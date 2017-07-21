# -*- coding: utf-8 -*-
# app.py
from mongo_interface import make_database
from flask import flash, request, Flask, render_template, redirect, session
import secure
import random
import collections
db = make_database()
correct_def = ''
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
user_doc = {}


@app.route("/", methods=["GET"])
def main():
    if request.method == "GET":
        try:
            username = session["username"]
            email = db.users.find_one({"username": username})["email"]
            session["email"] = email
            return render_template("homepage_2.html", username=username)
        except:
            return render_template("homepage.html")


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
    username = session["username"]
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
    username = session["username"]
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
    global user_doc
    username = session["username"]
    name = session["current_list"]
    try:
        user_doc[name.lower()]
    except:
        # if the user has never accessed this list before, set everything to 0
        user_doc[name.lower()] = {"correct": 0, "wrong": 0}
    name.split()
    name = name[-1]
    return render_template("list_selected.html", name=name, username=username)


@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    global correct_def, name_of_collection, list_of_words
    global list_of_definitions, correct_word, wrong_one, wrong_two
    global wrong_three, word_index, user_doc
    username = session["username"]
    name_of_lis = session["current_list"]
    if request.method == "GET":
        if len(list_of_words) < 1:
            return render_template("error_choose_list.html", username=username)
        else:
            # a word_index generated to make the word choice random
            word_index = random.randint(0, (len(list_of_words)-1))
            # the correct_word is set
            correct_word = list_of_words[word_index]
            # the correct_definiton is set
            correct_def = list_of_definitions[word_index]
            # a variable called not_the_same is created
            # loop to ensure that wrong_one≠correct_def
            not_the_same = False
            while not not_the_same:
                wrong_one = random.choice(list_of_definitions)
                if correct_def != wrong_one:
                    not_the_same = True
                else:
                    continue
            # wrong_two≠correct_def≠wrong_one
            not_the_same = False
            while not not_the_same:
                wrong_two = random.choice(list_of_definitions)
                if correct_def != wrong_two:
                    if wrong_one != wrong_two:
                        not_the_same = True
                    else:
                        continue
                else:
                    continue
            # wrong_three≠correct_def≠wrong_one≠wrong_two
            not_the_same = False
            while not not_the_same:
                wrong_three = random.choice(list_of_definitions)
                if correct_def != wrong_three:
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
            list_of_options = [correct_def,
                               wrong_one, wrong_two, wrong_three]
            random.shuffle(list_of_options)
            return render_template("question.html", correct_word=correct_word,
                                   list_of_options=list_of_options,
                                   name_of_lis=name_of_lis, username=username)
    else:
        name_of_lis = session["current_list"]
        if request.form.get("options") == correct_def:
            # update dictionary
            user_doc[session["current_list"].lower()]["correct"] += 1
            # update mongo
            db.users.update({"username": username},
                            {"$set": {session["current_list"].lower():
                             user_doc[session["current_list"].lower()]}})
            full_doc = db[name_of_collection].find_one({"word": correct_word})
            quote_ggs = full_doc["quote_ggs"]
            correct_translit = full_doc["transliteration"]
            # go to correct.html and print details about the correct word
            return render_template("correct.html", correct_word=correct_word,
                                   correct_def=correct_def,
                                   quote_ggs=quote_ggs,
                                   name_of_lis=name_of_lis,
                                   correct_translit=correct_translit,
                                   username=username)
        elif request.form.get("options") is None:
            # if the user clicked submit without submitting a response
            flash("Please submit a response")
            list_of_options = [correct_def,
                               wrong_one, wrong_two, wrong_three]
            return render_template("question.html", correct_word=correct_word,
                                   list_of_options=list_of_options)
        else:
            # if the user was incorrect, go to incorrect.html
            # print details about the correct word
            # update dictionary
            user_doc[session["current_list"].lower()]["wrong"] += 1
            # update mongo
            db.users.update({"username": username},
                            {"$set": {session["current_list"].lower():
                             user_doc[session["current_list"].lower()]}})
            full_doc = db[name_of_collection].find_one({"word": correct_word})
            quote_ggs = full_doc["quote_ggs"]
            correct_translit = full_doc["transliteration"]
            return render_template("incorrect.html", correct_word=correct_word,
                                   correct_def=correct_def,
                                   quote_ggs=quote_ggs,
                                   name_of_lis=name_of_lis,
                                   correct_translit=correct_translit,
                                   username=username)


@app.route("/login", methods=["GET", "POST"])
def login():
    global user_doc
    if request.method == "GET":
        # if user is simply accessing the page
        return render_template("login.html")
    else:
        # if the user tried to login
        # 1. check if the user exists in database
        doc = db.users.find_one({"username":
                                 request.form.get("user").lower().strip()})
        username = request.form.get("user")
        if doc is None:
            # if not user in db, the username is wrong
            flash("Wrong Username")
            return render_template("login.html")
        elif doc["password"] == request.form.get("pass"):
            # the user is in db and the password is correct
            user_doc = {}
            session["username"] = username
            flash("Successful login")
            # successful login
            # direct the user to choose a list
            return redirect("/setsession", 303)
        else:
            session["username"] = username
            email = db.users.find_one({"username": username})["email"]
            session["email"] = email
            # just wrong password
            flash("Wrong password")
            return render_template("login.html")


@app.route("/security", methods=["GET", "POST"])
def security():
    if request.method == "GET":
        # directed here when user clicks "Forgot password" on login page
        return render_template("wrong_password.html")
    else:
        # check is user in database
        session["username"] = request.form.get("user")
        security_word = request.form.get("security_word")
        doc = db.users.find_one({"username": session["username"]})
        if doc is None:
            # if user not in db, wrong username
            flash("Wrong Username")
            return render_template("wrong_password.html")
        elif doc["security_word"].lower() == security_word.lower():
            # security word is correct, redirect to choose a list
            return redirect("/reset_password", 303)
        else:
            # security word is incorrect
            flash("Security word is incorrect. Try again")
            return render_template("wrong_password.html")


@app.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    username = session["username"]
    if request.method == "GET":
        return render_template("reset_password.html")
    else:
        if request.form.get("pass") != request.form.get("c_pass"):
            # password ≠ confirmed password
            flash("Re-Type Password or Password Confirmation")
            return render_template("reset_password.html")
        elif len(request.form.get("pass")) < 8:
            # password length is less than 8 characters
            flash("Password length is less than 8 characters")
            return render_template("reset_password.html")
        else:
            db.users.update({"username": username},
                            {"$set": {"password":request.form.get("pass")}})
            flash("Password reset")
            return redirect("/")
        

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        # user is signing up
        return render_template("sign_up.html")
    else:
        if request.form.get("user") != request.form.get("c_user"):
            # username ≠ confirmed username
            flash("Re-Type Username or Username Confirmation")
            return render_template("sign_up.html")
        if db.users.find_one({"username":
                              request.form.get("user")}) is not None:
            # username already exists in database
            flash("Username already taken")
            return render_template("sign_up.html")
        if request.form.get("pass") != request.form.get("c_pass"):
            # password ≠ confirmed password
            flash("Re-Type Password or Password Confirmation")
            return render_template("sign_up.html")
        if len(request.form.get("pass")) < 8:
            # password length is less than 8 characters
            flash("Password length is less than 8 characters")
            return render_template("sign_up.html")
        db.users.insert_one({"username": request.form.get("user"),
                             "password": request.form.get("pass"),
                             "security_word":
                             request.form.get("security_word"),
                             "email": request.form.get("email")})
        # add user to db and set session[username] and session[email]
        session["username"] = request.form.get("user")
        session["email"] = request.form.get("email")
        flash("Profile created")
        # redirect user to choose a list
        return redirect("/setsession", 303)


@app.route("/logged_out", methods=["GET"])
def logged_out():
    global user_doc
    # user has logged out
    # delete session[username] and session[email]
    session["username"] = None
    session["email"] = None
    user_doc = {}
    return render_template("logged_out.html")


@app.route("/profile", methods=["GET"])
def profile():
    username = session["username"]
    email = db.users.find_one({"username": username})["email"]
    doc = db.users.find_one({"username": username})
    stats = {}
    progress = {}
    for item in doc:
        name_of_item = list(str(item))
        if name_of_item[0:4] == list("list"):
            stats[item] = doc[item]
    for lis in stats:
        num_questions = (stats[lis]["correct"]+stats[lis]["wrong"])
        percent_accuracy = int((stats[lis]["correct"] / num_questions)*100)
        progress[list(lis)[-1]] = {"percent_accuracy": percent_accuracy,
                                   "total_questions": num_questions}
    od = collections.OrderedDict(sorted(progress.items()))
    # get information about user and print in profile.html
    return render_template("profile.html", email=email, username=username,
                           od=od)


if __name__ == "__main__":
    # turn off this debugging stuff before production
    app.config['PROPAGATE_EXCEPTIONS'] = True
    app.config['DEBUG'] = True
    # next line: cause KeyErrors to bubble up to top level
    # so we can see the traceback & debugger
    app.config['TRAP_BAD_REQUEST_ERRORS'] = True
    app.run()
