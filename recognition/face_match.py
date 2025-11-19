import os, sys, cv2, pymongo
import numpy as np
from dotenv import load_dotenv

from insightface.app import FaceAnalysis
from numpy.linalg import norm

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

DB_NAME = "face_recognition_db"
COLLECTION_NAME = "persons"

def cosine_similarity(a, b):
    return np.dot(a, b) / (norm(a) * norm(b))

def load_database_embeddings(collection):
    people = []
    for person in collection.find():
        if "embedding" not in person:
            continue
        people.append({
            "_id": person["_id"],
            "link": person["link"],
            "name": person["name"],
            "embedding": np.array(person["embedding"], dtype=np.float32),
        })
    return people

def main():
    if len(sys.argv) < 2:
        print("usage: python face_match.py <query_image_path>")
        return
    
    query_image_path = sys.argv[1]

    img = cv2.imread(query_image_path)
    if img is None:
        print(f"error, could not read image {query_image_path}")
        return

    print('loading face model')
    app = FaceAnalysis(name="buffalo_l")
    app.prepare(ctx_id=-1, det_size=(640, 640))

    faces = app.get(img)
    if len(faces) == 0:
        print("No faces found in the image.")
        return
    
    query_embedding = faces[0].normed_embedding.astype(np.float32)

    client = pymongo.MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    db_people = load_database_embeddings(collection)
    if len(db_people) == 0:
        print("no embeddings found in the database.")
        return
    
    best_match = None
    best_score = -1

    for person in db_people:
        score = cosine_similarity(query_embedding, person["embedding"])
        if score > best_score:
            best_score = score
            best_match = person

    print("best match")
    print("Name:", best_match["name"])
    print("Link:", best_match["link"])
    print("Similarity:", best_score)

if __name__ == "__main__":
    main()
