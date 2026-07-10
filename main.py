import argparse
import logging
import os
import shutil
from pathlib import Path
from typing import List

import face_recognition
import numpy as np
from dotenv import load_dotenv

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

VALID_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff')

def get_unique_filename(directory: Path, filename: str) -> str:
    """
    Generate a unique filename to avoid overwriting existing files in the output directory.
    """
    base, extension = os.path.splitext(filename)
    counter = 1
    new_name = filename
    while (directory / new_name).exists():
        new_name = f"{base}_{counter}{extension}"
        counter += 1
    return new_name

def load_reference_encodings(reference_folder: Path) -> List[np.ndarray]:
    """
    Load face encodings from images in the reference folder.
    """
    known_encodings: List[np.ndarray] = []
    logger.info(f"Loading references from '{reference_folder}'...")
    
    if not reference_folder.exists() or not reference_folder.is_dir():
        logger.error(f"Reference folder '{reference_folder}' not found or is not a directory.")
        return known_encodings

    count = 0
    for file_path in reference_folder.iterdir():
        if not file_path.is_file() or not file_path.name.lower().endswith(VALID_EXTENSIONS):
            continue
            
        try:
            img = face_recognition.load_image_file(str(file_path))
            encs = face_recognition.face_encodings(img)
            
            if encs:
                known_encodings.append(encs[0])
                count += 1
            else:
                logger.warning(f"No faces found in reference image: {file_path.name}")
        except Exception as e:
            logger.warning(f"Failed to load or process reference image {file_path.name}: {e}")
            
    logger.info(f"Total valid reference faces loaded: {count}")
    return known_encodings

def scan_and_move(input_dir: Path, output_dir: Path, known_encodings: List[np.ndarray], tolerance: float) -> int:
    """
    Scan the input directory recursively for matching faces and move them to the output directory.
    """
    found_count = 0
    
    for file_path in input_dir.rglob("*"):
        if not file_path.is_file() or not file_path.name.lower().endswith(VALID_EXTENSIONS):
            continue
            
        try:
            image = face_recognition.load_image_file(str(file_path))
            unknown_encodings = face_recognition.face_encodings(image)
            
            if not unknown_encodings:
                logger.debug(f"No faces detected in {file_path.name}")
                continue 

            is_match = False
            for unknown_face in unknown_encodings:
                results = face_recognition.compare_faces(known_encodings, unknown_face, tolerance=tolerance)
                if True in results:
                    is_match = True
                    break
            
            if is_match:
                unique_name = get_unique_filename(output_dir, file_path.name)
                destination = output_dir / unique_name
                shutil.move(str(file_path), str(destination))
                logger.info(f"[MATCH] Found and moved: {file_path.name}")
                found_count += 1
                
        except Exception as e:
            logger.warning(f"Could not process file {file_path.name}: {e}")
            
    return found_count

def main() -> None:
    """
    Main entry point for the Face Recognition Sorter.
    """
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Face Recognition Image Sorter")
    parser.add_argument("--input", type=str, default=os.getenv("INPUT_DIR"),
                        help="Input directory containing images to scan")
    parser.add_argument("--output", type=str, default=os.getenv("OUTPUT_DIR"),
                        help="Output directory where matching photos will be moved")
    parser.add_argument("--reference", type=str, default=os.getenv("REFERENCE_DIR", "my_reference_faces"),
                        help="Directory containing reference face images")
    parser.add_argument("--tolerance", type=float, default=float(os.getenv("TOLERANCE", "0.6")),
                        help="Tolerance for face matching (lower is stricter, default 0.6)")
    
    args = parser.parse_args()
    
    if not args.input or not args.output:
        logger.error("Both --input and --output directories must be provided via arguments or .env variables.")
        return
        
    input_dir = Path(args.input)
    output_dir = Path(args.output)
    reference_dir = Path(args.reference)
    
    if not input_dir.exists():
        logger.error(f"Input directory '{input_dir}' does not exist.")
        return
        
    output_dir.mkdir(parents=True, exist_ok=True)
    
    target_encodings = load_reference_encodings(reference_dir)
    if not target_encodings:
        logger.error("No valid reference faces loaded. Aborting process.")
        return

    logger.info(f"Starting face recognition scan on '{input_dir}'...")
    found = scan_and_move(input_dir, output_dir, target_encodings, args.tolerance)
    logger.info(f"Scan complete. Total matching photos found and moved: {found}")

if __name__ == "__main__":
    main()
