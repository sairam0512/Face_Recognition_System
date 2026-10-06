import os
from pathlib import Path
from flask import Flask

def create_app():
    # Setup directories
    BASE_DIR = Path(__file__).parent
    STATIC_DIR = BASE_DIR / "static"
    FACES_DIR = STATIC_DIR / "faces"
    UPLOADS_DIR = STATIC_DIR / "uploads"
    ENC_PATH = STATIC_DIR / "faces_encodings.pkl"

    FACES_DIR.mkdir(parents=True, exist_ok=True)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

    app = Flask(__name__)
    
    # Configuration
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "replace-this-with-a-secret-for-production")
    app.config["UPLOAD_FOLDER"] = str(UPLOADS_DIR)
    app.config["FACES_FOLDER"] = str(FACES_DIR)
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max upload

    # Import and Register Blueprint
    from app.routes import main
    app.register_blueprint(main)

    # Initial training check
    if not ENC_PATH.exists():
        from app.utils import encode_all_faces
        encode_all_faces(FACES_DIR, ENC_PATH)

    return app
