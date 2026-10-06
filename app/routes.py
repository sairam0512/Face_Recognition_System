import io
import base64
import warnings
warnings.filterwarnings("ignore", category=UserWarning)
from pathlib import Path

from flask import Blueprint, render_template, request, redirect, url_for, send_from_directory, flash, jsonify, current_app
from werkzeug.utils import secure_filename
from PIL import Image
import numpy as np
import cv2

from app.utils import (
    encode_all_faces,
    recognize_image_file,
    recognize_frame,
    add_face_from_file,
    delete_face,
    ENC_PATH,
    FACES_DIR,
    UPLOADS_DIR
)

main = Blueprint('main', __name__)

@main.route("/")
def index():
    return render_template("index.html")

# Upload + Recognize (image file)
@main.route("/upload", methods=["GET", "POST"])
def upload_page():
    if request.method == "POST":
        if "image" not in request.files:
            flash("No image part")
            return redirect(request.url)
        file = request.files["image"]
        if file.filename == "":
            flash("No selected file")
            return redirect(request.url)
        filename = secure_filename(file.filename)
        save_path = UPLOADS_DIR / filename
        file.save(save_path)
        result = recognize_image_file(str(save_path), str(ENC_PATH))
        return render_template("result.html", result=result, filename=filename, source="upload")
    return render_template("upload.html")

@main.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)

# Webcam page (client captures frames & sends as base64)
@main.route("/webcam")
def webcam_page():
    return render_template("webcam.html")

@main.route("/recognize_webcam", methods=["POST"])
def recognize_webcam():
    data = request.json
    if not data or "image" not in data:
        return jsonify({"error": "no image provided"}), 400
    header, b64 = data["image"].split(",", 1)
    img_bytes = base64.b64decode(b64)
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    result = recognize_frame(frame, str(ENC_PATH))
    return jsonify(result)

# Manage known faces
@main.route("/manage", methods=["GET"])
def manage_page():
    persons = []
    for entry in sorted(FACES_DIR.iterdir()):
        thumbnail = None
        if entry.is_dir():
            name = entry.name
            for img_file in entry.iterdir():
                if img_file.suffix.lower() in [".jpg", ".jpeg", ".png"]:
                    thumbnail = f"faces/{entry.name}/{img_file.name}"
                    break
        else:
            if entry.suffix.lower() in [".jpg", ".jpeg", ".png"]:
                name = entry.stem
                thumbnail = f"faces/{entry.name}"
            else:
                continue
        persons.append({
            "name": name,
            "thumbnail": thumbnail
        })
    return render_template("manage.html", persons=persons)

@main.route("/add_face", methods=["POST"])
def add_face():
    if "image" not in request.files or "name" not in request.form:
        flash("Missing data")
        return redirect(url_for("main.manage_page"))
    file = request.files["image"]
    name = request.form["name"].strip()
    if name == "":
        flash("Provide a name")
        return redirect(url_for("main.manage_page"))
    filename = secure_filename(file.filename)
    save_path = UPLOADS_DIR / filename
    file.save(save_path)
    ok, msg = add_face_from_file(str(save_path), name, FACES_DIR, ENC_PATH)
    flash(msg)
    return redirect(url_for("main.manage_page"))

@main.route("/delete_face", methods=["POST"])
def delete_face_route():
    name = request.form.get("name")
    if not name:
        flash("No name provided")
        return redirect(url_for("main.manage_page"))
    ok, msg = delete_face(name, FACES_DIR, ENC_PATH)
    flash(msg)
    return redirect(url_for("main.manage_page"))

@main.route("/retrain", methods=["POST"])
def retrain():
    encode_all_faces(FACES_DIR, ENC_PATH)
    flash("Retrained encodings from faces/ directory.")
    return redirect(url_for("main.manage_page"))
