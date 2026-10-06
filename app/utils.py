import os
import pickle
import warnings
warnings.filterwarnings("ignore", category=UserWarning)
from pathlib import Path
from typing import Tuple, Dict, List, Any

import cv2
import numpy as np
from PIL import Image
import face_recognition

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
FACES_DIR = STATIC_DIR / "faces"
UPLOADS_DIR = STATIC_DIR / "uploads"
ENC_PATH = STATIC_DIR / "faces_encodings.pkl"

FACES_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

def load_encodings(enc_path: Path) -> Dict[str, List[np.ndarray]]:
    if not enc_path.exists():
        return {}
    with open(enc_path, "rb") as f:
        data = pickle.load(f)
    return data

def save_encodings(encodings: Dict[str, List[np.ndarray]], enc_path: Path):
    with open(enc_path, "wb") as f:
        pickle.dump(encodings, f)

def encode_all_faces(faces_dir: Path, enc_path: Path) -> Tuple[int, int]:
    """
    Walk faces_dir; expect structure:
    faces/<person_name>/*.jpg
    or faces/person_name_filename.jpg (single-level)
    Returns (num_people, total_encodings)
    """
    encodings = {}
    total = 0
    people = 0
    for child in faces_dir.iterdir():
        if child.is_dir():
            name = child.name
            person_imgs = list(child.glob("*"))
            enc_list = []
            for img_path in person_imgs:
                try:
                    image = face_recognition.load_image_file(str(img_path))
                    boxes = face_recognition.face_locations(image)
                    if not boxes:
                        continue
                    enc = face_recognition.face_encodings(image, boxes)[0]
                    enc_list.append(enc)
                    total += 1
                except Exception:
                    continue
            if enc_list:
                encodings[name] = enc_list
                people += 1
        else:
            # single image files directly under faces/
            if child.suffix.lower() in [".jpg", ".jpeg", ".png"]:
                name = child.stem
                try:
                    image = face_recognition.load_image_file(str(child))
                    boxes = face_recognition.face_locations(image)
                    if not boxes:
                        continue
                    enc = face_recognition.face_encodings(image, boxes)[0]
                    encodings[name] = [enc]
                    total += 1
                    people += 1
                except Exception:
                    continue
    save_encodings(encodings, enc_path)
    return people, total

def recognize_image_file(image_path: str, enc_path: str, tolerance=0.5) -> dict:
    encodings = load_encodings(Path(enc_path))
    if not encodings:
        return {"status": "no_encodings", "message": "No known faces. Add faces and retrain."}
    image = face_recognition.load_image_file(image_path)
    boxes = face_recognition.face_locations(image)
    if not boxes:
        return {"status": "no_faces", "message": "No faces detected in the image."}
    face_encs = face_recognition.face_encodings(image, boxes)
    results = []
    names = list(encodings.keys())
    known_encs = []
    for n in names:
        known_encs.append(encodings[n])
    # for easier comparison, flatten
    flat_known = []
    flat_names = []
    for i, name in enumerate(names):
        for enc in known_encs[i]:
            flat_known.append(enc)
            flat_names.append(name)
            
    # Load with OpenCV for annotation
    img_cv = cv2.imread(image_path)
    if img_cv is None:
        img_cv = cv2.cvtColor(np.array(Image.open(image_path)), cv2.COLOR_RGB2BGR)

    for i, fe in enumerate(face_encs):
        top, right, bottom, left = boxes[i]
        matches = face_recognition.compare_faces(flat_known, fe, tolerance=tolerance)
        face_distances = face_recognition.face_distance(flat_known, fe)
        best_match_idx = None
        
        distance = None
        name = "Unknown"
        if any(matches):
            best_match_idx = int(np.argmin(face_distances))
            name = flat_names[best_match_idx]
            distance = float(face_distances[best_match_idx])
            
        results.append({
            "face_index": i, 
            "name": name, 
            "distance": distance,
            "box": {
                "top": int(top),
                "right": int(right),
                "bottom": int(bottom),
                "left": int(left)
            }
        })
        
        # Draw bounding boxes and labels on image
        color = (0, 220, 0) if name != "Unknown" else (0, 0, 220)
        cv2.rectangle(img_cv, (left, top), (right, bottom), color, 3)
        
        label_text = name
        if distance is not None:
            confidence = (1.0 - distance) * 100
            label_text += f" ({confidence:.1f}%)"
            
        # Text size calculations
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        font_thickness = 1
        (text_w, text_h), baseline = cv2.getTextSize(label_text, font, font_scale, font_thickness)
        
        # Position label cleanly
        label_y = top - 10 if top - 10 > text_h + 10 else bottom + text_h + 10
        cv2.rectangle(
            img_cv,
            (left, label_y - text_h - 5),
            (left + text_w + 10, label_y + baseline),
            color,
            cv2.FILLED
        )
        cv2.putText(
            img_cv,
            label_text,
            (left + 5, label_y - 2),
            font,
            font_scale,
            (255, 255, 255),
            font_thickness,
            cv2.LINE_AA
        )

    annotated_filename = "annotated_" + Path(image_path).name
    annotated_path = UPLOADS_DIR / annotated_filename
    cv2.imwrite(str(annotated_path), img_cv)
    
    return {"status": "ok", "results": results, "annotated_filename": annotated_filename}

def recognize_frame(frame_bgr, enc_path: str, tolerance=0.5) -> dict:
    """
    frame_bgr: OpenCV BGR image (numpy array)
    """
    encodings = load_encodings(Path(enc_path))
    if not encodings:
        return {"status": "no_encodings", "message": "No known faces. Add faces and retrain."}
    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    boxes = face_recognition.face_locations(rgb)
    if not boxes:
        return {"status": "no_faces", "message": "No faces detected."}
    face_encs = face_recognition.face_encodings(rgb, boxes)
    results = []
    names = list(encodings.keys())
    known_encs = []
    for n in names:
        known_encs.append(encodings[n])
    flat_known = []
    flat_names = []
    for i, name in enumerate(names):
        for enc in known_encs[i]:
            flat_known.append(enc)
            flat_names.append(name)
    for i, fe in enumerate(face_encs):
        top, right, bottom, left = boxes[i]
        matches = face_recognition.compare_faces(flat_known, fe, tolerance=tolerance)
        face_distances = face_recognition.face_distance(flat_known, fe)
        
        distance = None
        name = "Unknown"
        if any(matches):
            best_match_idx = int(np.argmin(face_distances))
            name = flat_names[best_match_idx]
            distance = float(face_distances[best_match_idx])
            
        results.append({
            "face_index": i, 
            "name": name, 
            "distance": distance,
            "box": {
                "top": int(top),
                "right": int(right),
                "bottom": int(bottom),
                "left": int(left)
            }
        })
    return {"status": "ok", "results": results}


def add_face_from_file(image_path: str, name: str, faces_dir: Path, enc_path: Path) -> Tuple[bool, str]:
    """
    Adds the given image to faces/<name>/ and retrains encodings for that person (and saves enc file).
    """
    name_safe = "".join(c for c in name if c.isalnum() or c in (" ", "_", "-")).strip()
    person_dir = faces_dir / name_safe
    person_dir.mkdir(parents=True, exist_ok=True)
    try:
        im = face_recognition.load_image_file(image_path)
        boxes = face_recognition.face_locations(im)
        if not boxes:
            return False, "No face detected in provided image. Try another image."
        ext = Path(image_path).suffix or ".jpg"
        target = person_dir / (name_safe + "_" + Path(image_path).stem + ext)
        import cv2
        frame = cv2.imread(image_path)
        if frame is None:
            from PIL import Image
            pil = Image.open(image_path).convert("RGB")
            pil.save(str(target))
        else:
            cv2.imwrite(str(target), frame)
        encode_all_faces(faces_dir, enc_path)
        return True, f"Added face for '{name_safe}' and retrained encodings."
    except Exception as e:
        return False, f"Error adding face: {e}"

def delete_face(name: str, faces_dir: Path, enc_path: Path) -> Tuple[bool, str]:
    """
    Delete a person's folder (or files named with that person) and retrain encodings.
    """
    name_safe = name
    person_dir = faces_dir / name_safe
    removed = False
    try:
        if person_dir.exists() and person_dir.is_dir():
            import shutil
            shutil.rmtree(person_dir)
            removed = True
        else:
            for f in faces_dir.glob(f"{name_safe}*"):
                if f.is_file():
                    f.unlink()
                    removed = True
        if removed:
            encode_all_faces(faces_dir, enc_path)
            return True, f"Deleted data for '{name_safe}' and retrained encodings."
        else:
            return False, f"No data found for '{name_safe}'."
    except Exception as e:
        return False, f"Error deleting face data: {e}"
