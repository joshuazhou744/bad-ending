from insightface.app import FaceAnalysis
import numpy as np
import pymongo, gridfs, cv2
from dotenv import load_dotenv
import os

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

app = FaceAnalysis(name="buffalo_l")
app.prepare(ctx_id=0, det_size=(640, 640))

client = pymongo.MongoClient(MONGO_URI)
db = client["face_recognition_db"]
collection = db["persons"]
fs = gridfs.GridFS(db)

for person in collection.find():
    if "embedding" in person:
        continue
    
    image_id = person.get("image_id")
    if not image_id:
        print("no image, skipping")
        continue

    try:
        image_data = fs.get(image_id).read()
    except Exception as e:
        print(f"Error reading image for {person.get('name')}: {e}")
        continue

    np_arr = np.frombuffer(image_data, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if img is None:
        print("opencv could not decode image, skipping")
        continue

    faces = app.get(img)
    if len(faces) == 0:
        print(f"no face for {person['name']}, skipping")
        continue

    embedding = faces[0].normed_embedding.tolist()

    collection.update_one(
        {"_id": person["_id"]},
        {"$set": {"embedding": embedding}}
    )