#multiple_choice.py

from mongo_interface import db, list1
import random

#all_words is a dictionary that is comprised of everything in the database (word: transliteration, definition, quote_ggs)
all_words={}
for word in db.list1.find():
    all_words[word["word"]] = {"definition": word["definition"], "transliteration":word["transliteration"], "quote_ggs":word["quote_ggs"]}
  
option1 = ""
word = ""
unequal = True
#the variable "word" is a random word from the dictionary all_words
word = random.choice(list(all_words.keys()))

#x1 is a random other word
#unequal is a boolean to make sure that word and x1 are not the same word
while unequal:
    x1 = random.choice(list(all_words.keys()))
    if x1 == word:
        continue
#option1 is the definition of x1 (as another option for the multiple choice)
    else:
        option1 = all_words[x1]["definition"]
        #breaks loop
        unequal = False