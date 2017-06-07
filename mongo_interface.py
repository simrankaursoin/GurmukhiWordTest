#mongo_interface.py

from pymongo import MongoClient
client = MongoClient("localhost", 27017)
db = client["words"]
list1 = client["list1"]
list2 = client["list2"]

#db name is words
#collection names are list1, list2, userlists