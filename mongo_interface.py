# mongo_interface.py

from pymongo import MongoClient
from secure import MONGO_USERNAME, MONGO_PASSWORD

def make_database():
    client = MongoClient("localhost", 27017)
    db = client["words"]
    db.authenticate(MONGO_USERNAME, MONGO_PASSWORD, mechanism='SCRAM-SHA-1')
    for item in db.list1.find():
        print(item)
    return db

# db name is words
# collection names are list1, list2, userlists