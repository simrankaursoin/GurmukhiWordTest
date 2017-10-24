# ingest_file.py

from mongo_interface import make_database
import csv

db = make_database()
file_name = input("Enter file name here (including extension): ")
number_of_words = 0

with open(file_name, newline='') as csvfile:
    fieldnames = ["word", "transliteration", "definition", "quote_ggs"]
    filereader = csv.DictReader(csvfile)
    for row in filereader:
        doc = {}
        for word in db.masterlist.find():
            for attribute in word:
                doc[attribute] = word[attribute]
        if row['word'] in doc.values():
            print("Word already in masterlist")
            for item in db.masterlist.find({"word": row['word']}):
                print(item)
            print(row['word'] , row['transliteration'], row["definition"], row["quote_ggs"])
            choice = (input("Would you like to add your new word (a), discard it (d), or replace it (r)?")).lower()
            if choice == "a":
                number_of_words += 1
                db.masterlist.insert({"word":row['word'],
                                      "transliteration": row['transliteration'],
                                      "definition": row["definition"],
                                      "quote_ggs": row["quote_ggs"]})
            elif choice == "d":
                continue
            elif choice == "r":
                list_of_ids = []
                for item in db.masterlist.find({"word": row['word']}):
                    list_of_ids.append(str(item["_id"]))
                    print(item["_id"], item)
                target_id = input("Write the _id of the word you want to replace")
                if target_id in list_of_ids:
                    print("Valid id")
                    number_of_words += 1
                    db.masterlist.update({"_id": target_id}, {'$set':
                                                              {"word":row['word'],
                                                               "transliteration": row['transliteration'],
                                                               "definition": row["definition"],
                                                               "quote_ggs": row["quote_ggs"]}})
                else:
                    print("Invalid id")
            else:
                print("invalid option")
        else:
            db.masterlist.insert({"word":row['word'], 
                                  "transliteration": row['transliteration'],
                                  "definition": row["definition"],
                                  "quote_ggs": row["quote_ggs"]})
            number_of_words += 1
    print("Congratulations, " + str(number_of_words) + " words have been added to the masterlist")