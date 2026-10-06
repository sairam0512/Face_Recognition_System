import warnings
warnings.filterwarnings("ignore", category=UserWarning)
from pathlib import Path
from app.utils import encode_all_faces, FACES_DIR, ENC_PATH

if __name__ == "__main__":
    people, total = encode_all_faces(FACES_DIR, ENC_PATH)
    print(f"Encoded {total} face images for {people} people. Encodings saved to {ENC_PATH}")
