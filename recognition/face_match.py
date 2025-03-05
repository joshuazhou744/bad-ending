import cv2
import numpy as np
import os
import sys
from dotenv import load_dotenv
import pickle

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

def load_recognizer():
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read("recognizer.yml")
    with open("label_mapping.pkl", "rb") as f:
        label_to_info = pickle.load(f)
    return recognizer, label_to_info

def detect_face(query_image_path, face_cascade):
    img = cv2.imread(query_image_path)
    if img is None:
        print("Error: could not load query image.")
        return None
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces_detected = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
    if len(faces_detected) == 0:
        print(f"no face detected for")
        return None
    
    (x, y, w, h) = faces_detected[0]
    query_face = gray[y:y+h, x:x+w]
    return query_face

def main():
    if len(sys.argv) < 2:
        print("Usage: python face_match.py <query_image_path>")
        return
    
    query_image_path = sys.argv[1]

    cascade_path = os.path.join(os.getcwd(), "haarcascade_frontalface_default.xml")
    if not os.path.exists(cascade_path):
        print("Haar cascade file not found at:", cascade_path)
        sys.exit(1)
    face_cascade = cv2.CascadeClassifier(cascade_path)

    recognizer, label_to_info = load_recognizer()
    query_face = detect_face(query_image_path, face_cascade)
    if query_face is None:
        sys.exit(1)

    label, confidence = recognizer.predict(query_face)
    print(f"Prediction: Label {label}, Confidence {confidence}")

    if label in label_to_info:
        info = label_to_info[label]
        print("Matched Person:")
        print("Name:", info["name"])
        print("Link:", info["link"])
    else:
        print("No matching person found.")

if __name__ == "__main__":
    main()