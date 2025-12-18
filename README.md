# Face Recognition Batch Processor

An automated Python pipeline designed to organize large photo backups (specifically Google Photos Takeout archives). It iterates through ZIP files stored on a network drive (NAS), identifies specific faces using biometric recognition, extracts matching photos to a local drive, and re-uploads the remaining non-matching photos back to the network.

## 🚀 Features

- **Batch ZIP Processing:** Automatically handles multiple `.zip` archives from a network source (SMB/TrueNAS).
- **Biometric Recognition:** Uses `dlib` and `face_recognition` for high-accuracy detection.
- **Multi-Reference Support:** Accepts a folder of reference images (e.g., with/without glasses, different angles) to improve detection accuracy.
- **Smart Resume:** Automatically skips ZIP files that have already been processed to avoid redundancy.
- **Network Resilience:** Includes retry logic and robust file handling (`shutil.copyfile`) to prevent timeouts and metadata errors on SMB shares.
- **Privacy First:** All processing happens locally. No data is sent to external cloud APIs.

## 🛠️ Prerequisites

- **Python 3.9+**
- **CMake** (Required to compile `dlib`)
  - *macOS:* `brew install cmake`
  - *Windows:* Install via [cmake.org](https://cmake.org) (Add to PATH)
  - *Linux:* `sudo apt-get install cmake`

## 📦 Installation

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/YOUR_USERNAME/face-recognition-sorter.git](https://github.com/YOUR_USERNAME/face-recognition-sorter.git)
   cd face-recognition-sorter

2. **Set up the Virtual Environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate

3. **Install Dependencies:** Note: Installing `dlib` may take a few minutes as it compiles C++ code.
   ```bash
   pip install cmake dlib face_recognition opencv-python

## ⚙️ Configuration
To ensure security and privacy, this project separates configuration from code. Do not commit your real paths to GitHub.

1. **Create your configuration file:** Duplicate the example file to create your local config.
   ```bash
   cp config_example.py config.py

2. **Edit config.py:** Open the file and update the variables with your local and network paths:
   ```python
   # config.py
    NETWORK_SOURCE_DIR = "/Volumes/server/backups/google_photos" # Where the original ZIPs are
    NAS_OUTPUT_DIR = "/Volumes/server/backups/processed"         # Where to save photos WITHOUT the target face
    FINAL_DESTINATION = "found_photos_local"                     # Where to save photos WITH the target face
    REFERENCE_DIR = "my_reference_faces"                         # Folder containing your reference photos

3. **Add Reference Photos:** Create the folder defined in `REFERENCE_DIR` (e.g., `my_reference_faces`) and add 3-5 photos of the person you want to find.
- Tip: Use photos with different lighting and angles for better results.

## ▶️ Usage
Once configured, simply run the main script:
   ```bash
   python3 batch_processor.py

### Workflow:
1. The script copies a ZIP file from the NAS to the local machine (for performance).
2. Extracts contents to a temporary workspace.
3. Scans all images for matches against your reference faces.
4. Moves matching photos to your local FINAL_DESTINATION.
5. Zips the remaining photos into a new archive (e.g., remainder_001.zip).
6. Uploads the new ZIP back to the NAS_OUTPUT_DIR.
7. Cleans up temporary files and proceeds to the next batch.

## 🛡️ Privacy & Security
This repository includes a strict `.gitignore` file to prevent accidental upload of sensitive data.
- Ignored: All image formats (`.jpg`, `.png`, etc.), ZIP files, config files containing passwords/paths, and system files.
- Safe to Commit: Python scripts (`.py`), documentation (`.md`), and example configs.

## 📄 License
MIT License