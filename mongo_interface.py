# mongo_interface.py

from pymongo import MongoClient


def make_database():
    client = MongoClient("localhost", 27017)
    db = client["words"]
    return db

# db name is words
# collection names are list1, list2, userlists
