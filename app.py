#app.py
from mongo_interface import db, list1
from flask import flash, request, Flask, render_template, url_for, redirect, session, request
import secure, random
correct_definition=''
correct_word=""
list_of_words = []
list_of_definitions = []
word_index= 0
wrong_one=""
wrong_two=""
wrong_three=""

app = Flask(__name__)
app.secret_key = secure.APP_SECRET_KEY
def make_lists(list_of_words, list_of_definitions):
    name_of_collection = str(session["current_list"]).lower()
    for item in db[name_of_collection].find():
        list_of_words.append(item["word"])
        list_of_definitions.append(item["definition"])     
    return list_of_words, list_of_definitions 

    correct_word= list_of_words[0]
    correct_definition= list_of_definitions[0]
    not_the_same = False
    while not not_the_same:
        wrong_one = random.choice(list_of_definitions)
        if correct_definition != wrong_one:
            not_the_same = True
        else:
            continue
    not_the_same = False
    while not not_the_same:
        wrong_two = random.choice(list_of_definitions)
        if correct_definition != wrong_two:
            if wrong_one != wrong_two:
                not_the_same = True
            else:
                continue
        else:
            continue
    not_the_same = False
    while not not_the_same:
        wrong_three = random.choice(list_of_definitions)
        if correct_definition != wrong_three:
            if wrong_one != wrong_three:
                if wrong_two != wrong_three:
                    not_the_same = True
                else:
                    continue
            else:
                continue
        else:
            continue
    list_of_options = [correct_definition, wrong_one, wrong_two, wrong_three]
    random.shuffle(list_of_options)
    
          
@app.route("/",methods=["GET"])
def main():
    if request.method == "GET":
        return render_template("homepage.html" )     
 
@app.route("/setsession", methods=["GET", "POST"])
def set_session():
    global list_of_words, list_of_definitions
    if request.method =="GET":
        return render_template("set_session.html")
    else:
        session["current_list"] = request.form.get("current_list")
        list_of_words = []
        list_of_definitions = []
        make_lists(list_of_words, list_of_definitions)
        return redirect("/quiz", 303)
        
@app.route("/quiz", methods=["GET","POST"])
def quiz():
    global correct_definition, list_of_words, list_of_definitions, correct_word, wrong_one, wrong_two, wrong_three, word_index
    print(correct_definition)
    if request.form.get("options") == correct_definition:
        list_of_words.pop(word_index)
        return "CORRECT"          
    elif request.form.get("options") == None:
        word_index= random.randint(0, len(list_of_words)-1)
        correct_word= list_of_words[word_index]
        correct_definition= list_of_definitions[word_index]
        not_the_same = False
        while not not_the_same:
            wrong_one = random.choice(list_of_definitions)
            if correct_definition != wrong_one:
                not_the_same = True
            else:
                continue
        not_the_same = False
        while not not_the_same:
            wrong_two = random.choice(list_of_definitions)
            if correct_definition != wrong_two:
                if wrong_one != wrong_two:
                    not_the_same = True
                else:
                    continue
            else:
                continue
        not_the_same = False
        while not not_the_same:
            wrong_three = random.choice(list_of_definitions)
            if correct_definition != wrong_three:
                if wrong_one != wrong_three:
                    if wrong_two != wrong_three:
                        not_the_same = True
                    else:
                        continue
                else:
                    continue
            else:
                continue
        list_of_options = [correct_definition, wrong_one, wrong_two, wrong_three]
        random.shuffle(list_of_options)
        return render_template("question.html", correct_word = correct_word, list_of_options = list_of_options)
    else: 
        return "NOPE"         
'''
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
'''
if __name__ == "__main__":
    #turn off this debugging stuff before production
    app.config['PROPAGATE_EXCEPTIONS'] = True
    app.config['DEBUG'] = True
    # next line: cause KeyErrors to bubble up to top level 
	#so we can see the traceback & debugger 
    app.config['TRAP_BAD_REQUEST_ERRORS'] = True

    app.run()