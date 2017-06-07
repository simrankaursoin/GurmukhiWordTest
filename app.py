#app.py

from mongo_interface import db, list1
from flask import flash, request, Flask, render_template, url_for, redirect, session, request
from multiple_choice import list_of_words, list_of_definitions
import secure, random
app = Flask(__name__)
app.secret_key = secure.APP_SECRET_KEY


#######TODO ITEM: make it so that the user can only click one multiple choice option
#######TODO ITEM: (for way in the future) is it possible to have the user login through google or something so that I don't have to store all of the usernames and passwords?

@app.route("/",methods=["GET","POST"])
def main():
    if request.method == "GET":
        return render_template("homepage.html" )        
    if request.method == "POST":
        if request.form["list1"] == "enter":
            return redirect("/list1", code=303)
 
 
 
@app.route("/list1",methods=["GET","POST"])
def list1():
    if request.method == "GET":
        correct_word= list_of_words[0]
        correct_definition= list_of_definitions[0]
        not_the_same = False
        while not not_the_same:
            wrong_one = random.choice(list_of_definitions)
            if correct_definition != wrong_one:
                not_the_same = True
            else:
                continue
        #set session["current_list"] equal to list1
        return render_template("question.html", correct_word = correct_word, correct_definition=correct_definition, wrong_one = wrong_one)
    
    if request.method == "POST":
        if request.form.get("correct") == "yes":
            was_correct = True
        else:
            was_correct = False
        return "HEYO"
     
@app.route("/progress",methods=["GET"])
def progress():
    #check what list they're on using session
    #if the user has answered less than one word from the list (in userdata), print("Not enough data to provide progress summary)
    #else: provide percent accuracy for each word in the list
    #alternatively, list the 3 words theyre doing worst on
    return "Get request made" 
    
@app.route("/login",methods=["GET","POST"])
def login():
    #some_uuid = ____
    #session["uuid/username]= some_uuid
    #session["session_start"] = arrow.utcnow().timestamp
    #for item in db.collection_names(include_system_collections = False):
        #new_doc[item] = {}
    #new_doc["uuid/username"] = session["uuid/username"]
    #new_doc["session_start"] = session["session_start"]
    #db.userdata.insert_one(new_doc)
    #return render_template("homepage.html")
    return "Get request"        

if __name__ == "__main__":
    #turn off this debugging stuff before production
    app.config['PROPAGATE_EXCEPTIONS'] = True
    app.config['DEBUG'] = True
    # next line: cause KeyErrors to bubble up to top level 
	#so we can see the traceback & debugger 
    app.config['TRAP_BAD_REQUEST_ERRORS'] = True

    app.run()