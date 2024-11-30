# mongodb+srv://llama:HhToi2XTKJrpgmjX@cluster0.rrb1f.mongodb.net

import pymongo
import os
import json
from lib.config import MONGODB_URL

def get_db():
    client = pymongo.MongoClient(MONGODB_URL)
    db = client["staging"]
    return db

mongo = get_db()

def get_collection(collection_name):
    db = get_db()
    collection = db[collection_name]

    return collection

def insert_dataset():
    for dirs in os.listdir('DATASET'):
        for files in os.listdir('DATASET/'+dirs):
            if files.endswith('.json') and "_infos" not in files:
                with open('DATASET/'+dirs+'/'+files) as f:
                    data = json.load(f)
                    mongo["products"].insert_many(data)
            elif "_infos" in files and files.endswith('.json'):
                with open('DATASET/'+dirs+'/'+files) as f:
                    data = json.load(f)
                    mongo["stores"].insert_many(data)
                
            else:
                for f in os.listdir('DATASET/'+dirs+'/'+files):
                    if f.endswith('.json') and "_infos" not in f:
                        with open('DATASET/'+dirs+'/'+files+'/'+f) as f:
                            data = json.load(f)
                            mongo["products"].insert_many(data)
                    elif "_infos" in f and f.endswith('.json'):
                        with open('DATASET/'+dirs+'/'+files+'/'+f) as f:
                            data = json.load(f)
                            mongo["stores"].insert_many(data)

    


def get_data():
    # data = mongo["products"].find()
    # VERMENTINO
    data = mongo["products"].find({"full_name":{"$regex":".*Vermentino.*"}})
    return data

if __name__ == '__main__':
    insert_dataset()
    print(list(get_data()))