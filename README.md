# Face Recognition Sorter

![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## 🎯 Business Value & Use Case

Event photographers, media managers, and archivists often spend hours manually sifting through thousands of photos to find pictures of specific individuals (e.g., a bride at a wedding, a keynote speaker at a conference, or a VIP client). **Face Recognition Sorter** automates this tedious process. 

By leveraging state-of-the-art biometric detection, this tool scans vast directories of unstructured images and automatically extracts all photos containing a target person. What used to take days of manual labor can now be achieved in minutes with high accuracy.

## 🛠️ Technical Architecture

- **Core Engine:** Built on top of `dlib` and the `face_recognition` library, enabling deep-learning-based face encoding and high-accuracy biometric comparison.
- **Robust CLI & Config Management:** Utilizes Python's native `argparse` for flexible command-line execution. It elegantly falls back to environment variables loaded via `python-dotenv`, ensuring that automated deployments or repeated batch jobs can run seamlessly without verbose arguments.
- **Error Resiliency:** Implements standard Python `logging` and comprehensive `try/except` handlers. Corrupted files or images without detectable faces will emit warnings rather than crashing the entire batch process.

## 📦 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/face-recognition-sorter.git
   cd face-recognition-sorter
   ```

2. **Set up a Virtual Environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install Dependencies:**
   *Note: `dlib` requires CMake to compile C++ code. If it fails, install CMake via `brew install cmake` (Mac) or `sudo apt-get install cmake` (Linux).*
   ```bash
   pip install -r requirements.txt
   ```

## ⚙️ Configuration

To streamline repeated tasks, you can configure default paths using environment variables.

1. Create your environment file from the template:
   ```bash
   cp .env.example .env
   ```
2. Edit the `.env` file to set your default `INPUT_DIR`, `OUTPUT_DIR`, and matching `TOLERANCE`.

3. **Add Reference Photos:** Create a folder named `my_reference_faces` (or as defined in your arguments) and place 2-4 clear photos of the target individual inside.

## ▶️ Usage

You can run the script purely via Command Line Arguments, which will override any variables set in your `.env` file.

**Basic Usage:**
```bash
python main.py --input ./raw_photos --output ./sorted_matches
```

**Advanced Usage with Custom Reference and Tolerance:**
```bash
python main.py --input /Volumes/Drive/Event_Photos \
               --output ~/Desktop/VIP_Client \
               --reference ./vip_references \
               --tolerance 0.5
```
*(Note: A lower tolerance like 0.5 is stricter, reducing false positives. The default is 0.6.)*

## 🛡️ Privacy & Security
All processing happens 100% locally on your machine. No images or biometric data are ever transmitted to external cloud APIs. The repository includes a pre-configured `.gitignore` to strictly exclude sensitive image formats (`.jpg`, `.png`, etc.) and `.env` files from being accidentally committed.

## 🏗️ Origins & Scale (Real-World Engineering)
This project was born out of a demanding infrastructure challenge. The original architecture was engineered to process massive, multi-gigabyte `.zip` data dumps (such as Google Takeout archives) directly over a Network Attached Storage (NAS) via SMB protocols.

In its initial production environment, the pipeline successfully managed rigorous edge cases, including:
- Intermittent network instability and dropped SMB connections.
- Heavy sequential I/O operations across network drives without corrupting data.
- State-management to resume interrupted, long-running batch processes.

**Product Trade-off for Open Source:** For this public release, the codebase was intentionally refactored and simplified into a universal local directory scanner. This strategic pivot maximizes reproducibility, community adoption, and Developer Experience (DX), allowing engineers and recruiters to run and evaluate the core biometric engine without requiring a complex, specialized home-server setup.

## 📄 License
MIT License