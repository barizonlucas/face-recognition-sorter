import face_recognition
import os
import shutil
import time
import zipfile

# --- IMPORTAÇÃO SEGURA (OU CONFIGURAÇÃO DIRETA SE PREFERIR) ---
# Se você estiver usando o arquivo config.py, mantenha assim. 
# Se preferir colar os caminhos direto aqui, pode substituir as variáveis config.XXXX
try:
    import config
    # Mapeando variáveis do config para locais
    NETWORK_SOURCE_DIR = config.NETWORK_SOURCE_DIR
    NAS_OUTPUT_DIR = config.NAS_OUTPUT_DIR
    FINAL_DESTINATION = config.FINAL_DESTINATION
    REFERENCE_DIR = config.REFERENCE_DIR
    TEMP_WORK_DIR = config.TEMP_WORK_DIR
    VALID_EXTENSIONS = config.VALID_EXTENSIONS
    TOLERANCE = config.TOLERANCE
except ImportError:
    # CASO NÃO TENHA CONFIG.PY, USE ESTES VALORES PADRÃO (Edite aqui se necessário)
    NETWORK_SOURCE_DIR = "/Volumes/arquivos/lucas/google photos"
    NAS_OUTPUT_DIR = "/Volumes/arquivos/lucas/nuvem"
    FINAL_DESTINATION = "found_photos_final"
    REFERENCE_DIR = "my_reference_faces"
    TEMP_WORK_DIR = "temp_workspace"
    VALID_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff')
    TOLERANCE = 0.6

def generate_unique_name(directory, filename):
    base, extension = os.path.splitext(filename)
    counter = 1
    new_name = filename
    while os.path.exists(os.path.join(directory, new_name)):
        new_name = f"{base}_{counter}{extension}"
        counter += 1
    return new_name

def load_reference_encodings(reference_folder):
    known_encodings = []
    print(f">> Loading references from '{reference_folder}'...")
    
    if not os.path.exists(reference_folder):
        print(f"ERROR: Reference folder '{reference_folder}' not found.")
        return []

    files = os.listdir(reference_folder)
    count = 0
    
    for filename in files:
        if not filename.lower().endswith(VALID_EXTENSIONS):
            continue
            
        path = os.path.join(reference_folder, filename)
        try:
            img = face_recognition.load_image_file(path)
            encs = face_recognition.face_encodings(img)
            
            if len(encs) > 0:
                known_encodings.append(encs[0])
                count += 1
        except Exception:
            pass
            
    print(f">> Total valid reference faces loaded: {count}\n")
    return known_encodings

def scan_folder_recursive(source_folder, known_face_encodings):
    found_count = 0
    for root, dirs, files in os.walk(source_folder):
        for filename in files:
            if not filename.lower().endswith(VALID_EXTENSIONS): continue
            
            full_path = os.path.join(root, filename)
            try:
                image = face_recognition.load_image_file(full_path)
                unknown_encodings = face_recognition.face_encodings(image)
                
                if not unknown_encodings: continue 

                is_match = False
                for unknown_face in unknown_encodings:
                    results = face_recognition.compare_faces(known_face_encodings, unknown_face, tolerance=TOLERANCE)
                    if True in results:
                        is_match = True
                        break
                
                if is_match:
                    unique_name = generate_unique_name(FINAL_DESTINATION, filename)
                    shutil.move(full_path, os.path.join(FINAL_DESTINATION, unique_name))
                    print(f"      [MATCH] Found: {filename}")
                    found_count += 1
            except Exception:
                pass
    return found_count

def zip_folder(folder_path, output_path):
    shutil.make_archive(output_path, 'zip', folder_path)

def safe_upload_to_nas(local_file, nas_path, max_retries=3):
    """
    CORREÇÃO APLICADA: Usa copyfile em vez de move para evitar erro de metadados (Errno 22).
    """
    for attempt in range(1, max_retries + 1):
        try:
            print(f"   -> Uploading to NAS (Attempt {attempt}/{max_retries})...")
            
            # 1. Copia apenas os dados (ignora permissões/datas que o NAS rejeita)
            shutil.copyfile(local_file, nas_path)
            
            # 2. Verifica se chegou lá
            if os.path.exists(nas_path):
                # 3. Se deu certo, apaga o original local
                os.remove(local_file)
                return True
            else:
                raise Exception("File copied but not detected on destination.")

        except Exception as e:
            print(f"   [WARNING] Upload failed: {e}")
            # Se o arquivo corrompido ficou lá, tenta limpar
            try:
                if os.path.exists(nas_path): os.remove(nas_path)
            except: pass
            
            if attempt < max_retries:
                print("   Waiting 15 seconds before retrying...")
                time.sleep(15)
            else:
                print("   [ERROR] Max retries reached. Upload failed.")
                return False

def main():
    print("--- BATCH PROCESSOR V5 (SMB FIX) ---")

    if not os.path.exists(NETWORK_SOURCE_DIR):
        print(f"ERROR: Network Source '{NETWORK_SOURCE_DIR}' not found.")
        return

    if not os.path.exists(FINAL_DESTINATION): os.makedirs(FINAL_DESTINATION)
    if not os.path.exists(NAS_OUTPUT_DIR):
        try: os.makedirs(NAS_OUTPUT_DIR)
        except: pass

    target_encodings = load_reference_encodings(REFERENCE_DIR)
    if not target_encodings:
        print("CRITICAL ERROR: No valid reference faces loaded.")
        return

    all_files = os.listdir(NETWORK_SOURCE_DIR)
    zip_files = [f for f in all_files if f.lower().endswith('.zip') and 'takeout' in f.lower()]
    zip_files.sort()

    total_zips = len(zip_files)
    print(f">> Found {total_zips} zip files available.\n")

    for index, zip_name in enumerate(zip_files):
        zip_identifier = index + 1
        new_zip_name_base = f"remainder_{zip_identifier:03d}"
        nas_destination_path = os.path.join(NAS_OUTPUT_DIR, new_zip_name_base + ".zip")

        # RESUME CHECK
        if os.path.exists(nas_destination_path):
            # Verificação extra: se o arquivo tem 0 bytes, ele processa de novo
            if os.path.getsize(nas_destination_path) > 0:
                print(f"[SKIP] Batch {index + 1}/{total_zips} ({zip_name}) already processed.")
                continue
            else:
                print(f"[REDO] Batch {index + 1} found but empty. Reprocessing...")

        print("="*60)
        print(f"PROCESSING BATCH {index + 1}/{total_zips}: {zip_name}")
        print("="*60)
        
        network_zip_path = os.path.join(NETWORK_SOURCE_DIR, zip_name)
        local_zip_path = os.path.join(os.getcwd(), zip_name)
        
        # 1. Copy
        print("1. Copying from NAS...")
        try:
            shutil.copyfile(network_zip_path, local_zip_path) # Alterado para copyfile aqui também por segurança
        except Exception as e:
            print(f"Error copying from NAS: {e}")
            continue

        # 2. Unzip
        print("2. Unzipping locally...")
        if os.path.exists(TEMP_WORK_DIR): shutil.rmtree(TEMP_WORK_DIR)
        os.makedirs(TEMP_WORK_DIR)
        
        try:
            with zipfile.ZipFile(local_zip_path, 'r') as zip_ref:
                zip_ref.extractall(TEMP_WORK_DIR)
        except zipfile.BadZipFile:
            print(f"ERROR: Corrupted Zip. Skipping.")
            if os.path.exists(local_zip_path): os.remove(local_zip_path)
            continue

        # 3. Scan
        print("3. Scanning faces...")
        found = scan_folder_recursive(TEMP_WORK_DIR, target_encodings)
        print(f">> Extracted {found} matching photos.")

        # 4. Zip Remainder
        print("4. Zipping remainder...")
        local_new_zip = os.path.join(os.getcwd(), new_zip_name_base)
        zip_folder(TEMP_WORK_DIR, local_new_zip)
        
        # 5. Upload with Retry
        local_new_zip_file = local_new_zip + ".zip"
        
        success = safe_upload_to_nas(local_new_zip_file, nas_destination_path)

        if not success:
            print("CRITICAL: Failed to upload to NAS. Pausing.")
            break 

        # 6. Cleanup
        print("6. Cleanup...")
        shutil.rmtree(TEMP_WORK_DIR)
        if os.path.exists(local_zip_path): os.remove(local_zip_path)
        print(">> Batch Done.\n")

    print("\n" + "="*60)
    print("ALL DONE.")
    print("="*60)

if __name__ == "__main__":
    main()