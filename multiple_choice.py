# -*- coding: utf-8 -*-
from mongo_interface import db, list1, list2

list_of_words=[]
list_of_definitions=[]
for item in db.list1.find():
    list_of_words.append(item["word"])
    list_of_definitions.append(item["definition"])