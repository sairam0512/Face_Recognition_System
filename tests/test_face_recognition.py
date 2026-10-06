import warnings
warnings.filterwarnings("ignore", category=UserWarning)
import unittest
import os
from pathlib import Path
from app.utils import recognize_image_file, encode_all_faces, FACES_DIR, ENC_PATH, UPLOADS_DIR

class TestFaceRecognition(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        print("Re-encoding faces for testing...")
        people, total = encode_all_faces(FACES_DIR, ENC_PATH)
        print(f"Encoded {total} faces for {people} people.")
        
    def test_integration_recognition(self):
        # Find a person in static/faces with at least one image
        test_person_dir = None
        for child in FACES_DIR.iterdir():
            if child.is_dir() and any(child.glob("*")):
                test_person_dir = child
                break
                
        self.assertIsNotNone(test_person_dir, "No registered face folders found with images for testing.")
        
        test_name = test_person_dir.name
        test_image_path = next(test_person_dir.glob("*"))
        print(f"Running integration test using person: '{test_name}', image: '{test_image_path.name}'")
        
        # Run recognition on the image
        result = recognize_image_file(str(test_image_path), str(ENC_PATH))
        
        print("Test recognition result:", result)
        
        # Verify result status
        self.assertEqual(result["status"], "ok", f"Recognition failed: {result.get('message')}")
        self.assertTrue(len(result["results"]) > 0, "No faces detected in the test registered image.")
        
        # Verify that the correct name is recognized
        names = [r["name"].lower() for r in result["results"]]
        print(f"Detected names in image: {names}")
        self.assertIn(test_name.lower(), names, f"Did not recognize '{test_name}' in their own image.")
        
        # Verify box coordinates are returned
        for r in result["results"]:
            self.assertIn("box", r)
            box = r["box"]
            self.assertIn("top", box)
            self.assertIn("right", box)
            self.assertIn("bottom", box)
            self.assertIn("left", box)
            self.assertIsInstance(box["top"], int)
            
        # Verify annotated file is generated
        self.assertIn("annotated_filename", result)
        annotated_path = UPLOADS_DIR / result["annotated_filename"]
        self.assertTrue(annotated_path.exists(), f"Annotated image file not found at: {annotated_path}")
        print("Success! Annotated file created at:", annotated_path)

if __name__ == "__main__":
    unittest.main()
