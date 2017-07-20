# -*- coding: utf-8 -*-
# app.py
from mongo_interface import make_database
from flask import flash, request, Flask, render_template, redirect, session
import secure
import random
db = make_database()
correct_definition = ''
correct_word = ""
list_of_words = []
list_of_definitions = []
word_index = 0
wrong_one = ""
wrong_two = ""
wrong_three = ""
name_of_collection = ''
app = Flask(__name__)
app.secret_key = secure.APP_SECRET_KEY


@app.route("/", methods=["GET"])
def main():
    if request.method == "GET":
        if session["username"] is None:
            return render_template("homepage.html")
        else:
            print(session["username"])
            username = session["username"]
            return render_template("homepage_2.html", username=username)
            

# make the list_of_words & list_of_definitions based on session["current_list"]


def make_lists(list_of_words, list_of_definitions):
    global name_of_collection
    # name_of_collection is a variable based on the session[current_list]
    name_of_collection = str(session["current_list"]).lower()
    for item in db[name_of_collection].find():
        list_of_words.append(item["word"])
        list_of_definitions.append(item["definition"])
    return list_of_words, list_of_definitions


@app.route("/setsession", methods=["GET", "POST"])
def set_session():
    global list_of_words, list_of_definitions
    username=session["username"]
    if request.method == "GET":
        # directs user to a page to set the session["current_list"]
        return render_template("set_session.html", username=username)
    else:
        # POST request for when user clicks "submit"
        # set_session page has a dropdown menu in which the user selects list
        # the session["current_list"] is set accordingly
        session["current_list"] = request.form.get("current_list")
        list_of_words = []
        list_of_definitions = []
        make_lists(list_of_words, list_of_definitions)
        # list_of_words & list_of_definitions according to list
        # lists allow for easier access and editing
        return redirect("/list_selected", 303)


@app.route("/study", methods=["GET", "POST"])
def study():
    global name_of_collection
    username=session["username"]
    all_words = []
    if len(list_of_words) < 1:
            return render_template("error_choose_list.html", username=username)
    # sets all_words equal to list containing each document
    for item in db[name_of_collection].find():
        all_words.append(item)
    name = session["current_list"]
    name.split()
    name = name[-1]
    # study.html makes a table for the user to study from.
    return render_template("study.html", name=name, 
                           username=username, all_words=all_words)


@app.route("/list_selected", methods=["GET"])
def list_selected():
    username= session["username"]
    name = session["current_list"]
    name.split()
    name = name[-1]
    return render_template("list_selected.html", name=name, username=username)


@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    global correct_definition, name_of_collection, list_of_words
    global list_of_definitions, correct_word, wrong_one, wrong_two
    global wrong_three, word_index
    username=session["username"]
    if request.method == "GET":
        if len(list_of_words) < 1:
            return render_template("error_choose_list.html", username=username)
        else:
            # a word_index generated to make the word choice random
            word_index = random.randint(0, (len(list_of_words)-1))
            # the correct_word is set
            correct_word = list_of_words[word_index]
            # the correct_definiton is set
            correct_definition = list_of_definitions[word_index]
            # a variable called not_the_same is created
            # loop to ensure that wrong_one≠correct_definition
            not_the_same = False
            while not not_the_same:
                wrong_one = random.choice(list_of_definitions)
                if correct_definition != wrong_one:
                    not_the_same = True
                else:
                    continue
            # wrong_two≠correct_definition≠wrong_one
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
            # wrong_three≠correct_definition≠wrong_one≠wrong_two
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
            # list_of_options made & shuffled so that responses in random order
            list_of_options = [correct_definition,
                               wrong_one, wrong_two, wrong_three]
            random.shuffle(list_of_options)
            return render_template("question.html", correct_word=correct_word,
                                   list_of_options=list_of_options,
                                   username=username)
    else:
        if request.form.get("options") == correct_definition:
            list_of_words.pop(word_index)
            list_of_definitions.pop(word_index)
            full_doc = db[name_of_collection].find_one({"word": correct_word})
            quote_ggs = full_doc["quote_ggs"]
            correct_translit = full_doc["transliteration"]
            return render_template("correct.html", correct_word=correct_word,
                                   correct_definition=correct_definition,
                                   quote_ggs=quote_ggs,
                                   correct_translit=correct_translit)
        elif request.form.get("options") is None:
            flash("Please submit a response")
            list_of_options = [correct_definition,
                               wrong_one, wrong_two, wrong_three]
            return render_template("question.html", correct_word=correct_word,
                                   list_of_options=list_of_options)
        else:
            full_doc = db[name_of_collection].find_one({"word": correct_word})
            quote_ggs = full_doc["quote_ggs"]
            correct_translit = full_doc["transliteration"]
            return render_template("incorrect.html", correct_word=correct_word,
                                   correct_definition=correct_definition,
                                   quote_ggs=quote_ggs,
                                   correct_translit=correct_translit,
                                   username=username)


'''
@app.route("/progress", methods = ["GET"])
def progress():
    #check what list they're on using session
    #if the user has answered < one word from the list, no summary
    #else: provide percent accuracy for each word in the list
    #alternatively, list the 3 words theyre doing worst on
    return "Get request made"
def login():
    # some_uuid = ____
    # session["uuid/username] = some_uuid
    # session["session_start"]  = arrow.utcnow().timestamp
    # for item in db.collection_names(include_system_collections = False):
        # new_doc[item] = {}
    # new_doc["uuid/username"] = session["uuid/username"]
    # new_doc["session_start"] = session["session_start"]
    # db.userdata.insert_one(new_doc)
    # return render_template("homepage.html")
    return "Get request"
'''


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    else:
        doc = db.users.find_one({"username":request.form.get("user").lower().strip()})
        username= request.form.get("user")
        if doc is None:
            flash("Wrong Username")
            return render_template("login.html")
        elif doc["password"] == request.form.get("pass"):
            session["username"]=username
            flash("Successful login")
            return redirect("/setsession", 303)
        else:
            session["username"]=username
            # just wrong password
            flash("Wrong password")
            return render_template("login.html")


@app.route("/security", methods=["GET", "POST"])
def security():
    if request.method == "GET":
        return render_template("wrong_password.html")
    else:
        session["username"] = request.form.get("user")
        security_word = request.form.get("security_word")
        doc = db.users.find_one({"username":session["username"]})
        if doc is None:
            flash("Wrong Username")
            return render_template("wrong_password.html")
        elif doc["security_word"].lower() == security_word.lower():
            return redirect("/", 303)
        else:
            flash("Incorrect. Try again")
            return render_template("wrong_password.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():  
    if request.method == "GET":
        return render_template("sign_up.html")
    else:
        if request.form.get("user") != request.form.get("c_user"):
            flash("Re-Type Username or Username Confirmation")
            return render_template("sign_up.html")
        if db.users.find_one({"username":request.form.get("user")}) != None:
            flash("Username already taken")
            return render_template("sign_up.html")
        if request.form.get("pass") != request.form.get("c_pass"):
            flash("Re-Type Password or Password Confirmation")
            return render_template("sign_up.html")
        if len(request.form.get("pass")) < 8:
            flash("Password length less than 8 characters")
            return render_template("sign_up.html")
        db.users.insert_one({"username":request.form.get("user"),
        "password":request.form.get("pass"), "security_word":request.form.get("security_word"),
        "email":request.form.get("email")})
        session["username"] = request.form.get("user")
        session["email"] = request.form.get("email")
        flash("Profile created")
        return render_template("homepage.html")
        

@app.route("/logged_out", methods=["GET"])
def logged_out():
    session["username"] = None
    session["email"] = None
    return render_template("logged_out.html")

@app.route("/profile", methods=["GET"])
def profile():
    username = session["username"]
    if session["email"] is None:
        session["email"] = db.users.find_one({"username":username})["email"]
        email= session["email"]
    else:
        email = session["email"]
    return render_template("profile.html", email=email, username=username)
        

if __name__ == "__main__":
    # turn off this debugging stuff before production
    app.config['PROPAGATE_EXCEPTIONS'] = True
    app.config['DEBUG'] = True
    # next line: cause KeyErrors to bubble up to top level
    # so we can see the traceback & debugger
    app.config['TRAP_BAD_REQUEST_ERRORS'] = True
    app.run()
