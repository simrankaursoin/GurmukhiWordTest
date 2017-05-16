#mongo_interface.py

from pymongo import MongoClient
client = MongoClient("localhost", 27017)
db = client["words"]
list1 = client["list1"]
lis1={}
#db name is words
#collection name is list1