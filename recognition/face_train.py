import cv2
import numpy as np
import os
import pymongo
import gridfs
import pickle
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

def get_db_collection(mongo_uri, db_name, collection_name):
    client = pymongo.MongoClient(mongo_uri)
    db = client[db_name]
    collection = db[collection_name]
    return db, collection

def load_faces(db, collection, fs, face_cascade):
    faces = []
    labels = []
    label_to_info = {}
    label = 0

    for doc in collection.find():
        name = doc.get("name")
        link = doc.get("link")
        image_id = doc.get("image_id")
        if image_id is None:
            continue
        try:
            image_data = fs.get(image_id).read()
        except Exception as e:
            print("error retrieving image for {name}: {e}")
            continue

        if not image_data:
            print(f"Image data for {name} is empty, skipping.")
            continue

        np_arr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if img is None:
            print("couldn't decode image")
            continue

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces_detected = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
        if len(faces_detected) == 0:
            print(f"no face detected for {name}")
            continue

        (x, y, w, h) = faces_detected[0]
        face_roi = gray[y:y+h, x:x+w]
        faces.append(face_roi)
        labels.append(label)
        label_to_info[label] = {"name": name, "link": link}
        label += 1

    print(label)
    return faces, labels, label_to_info

def main():
    DB_NAME = "face_recognition_db"
    COLLECTION_NAME = "persons"

    cascade_path = os.path.join(os.getcwd(), "haarcascade_frontalface_default.xml")
    if not os.path.exists(cascade_path):
        raise ValueError("Haar cascade file not found at " + cascade_path)
    face_cascade = cv2.CascadeClassifier(cascade_path)

    db, collection = get_db_collection(MONGO_URI, DB_NAME, COLLECTION_NAME)
    fs = gridfs.GridFS(db)

    faces, labels, label_to_info = load_faces(db, collection, fs, face_cascade)
    if len(faces) == 0:
        print("no faces found in the database")
        return

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(faces, np.array(labels))

    recognizer.save("recognizer.yml")
    with open("label_mapping.pkl", "wb") as f:
        pickle.dump(label_to_info, f)
    print("Training complete. Model saved as recognizer.yml and mapping saved as label_mapping.pkl.")

if __name__ == "__main__":
    main()