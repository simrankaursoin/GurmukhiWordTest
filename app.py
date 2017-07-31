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
    try:
        username = session["username"]
        # get username from session (added when they logged/signed in)
        # get first/last name or email from mongo database
        # set first name/last name/email in session for accessing later
        f_name = db.users.find_one({"username": username})["first_name"]
        l_name = db.users.find_one({"username": username})["last_name"]
        session["first_name"] = f_name
        session["last_name"] = l_name
        email = db.users.find_one({"username": username})["email"]
        session["email"] = email
        # full_name is the first name + last name (to display in top R corner)
        full_name = f_name + " " + l_name
        if len(list_of_words) > 0:
            # number 1 is that they logged in and chose list 
            # > homepage_2.html
            return render_template("homepage_2.html", full_name=full_name)
        else:
            # number 2 is that they logged in but didnt choose list 
            # > homepage_3.html
            return render_template("homepage_3.html", full_name=full_name)
    except:
        # number 3 is that they are not yet logged in 
        # > homepage.html
        return render_template("homepage.html")



def make_lists(list_of_words, list_of_definitions):
    global name_of_collection
    # name_of_collection is a variable based on the session[current_list]
    # corresponds to the name of the collection in the mongo db
    name_of_collection = str(session["current_list"]).lower()
    for item in db[name_of_collection].find():
        list_of_words.append(item["word"])
        list_of_definitions.append(item["definition"])
    # create a list called list_of_words based on db words from list
    # create a list called list_of_definitions based on db defs from list
    # allows appending/deleting/easy-access (unlike the db)
    return list_of_words, list_of_definitions


@app.route("/setsession", methods=["GET", "POST"])
def set_session():
    # choose list
    global list_of_words, list_of_definitions
    if request.method == "GET":
        # username, f_name, l_name variables not actually necessary
        # just added for easier formatting/readability
        # all in order to create full_name (concatenation of first + last name)
        username = session["username"]
        f_name = db.users.find_one({"username": username})["first_name"]
        l_name = db.users.find_one({"username": username})["last_name"]
        session["first_name"] = f_name
        session["last_name"] = l_name
        full_name = f_name + " " + l_name
        if len(list_of_words) > 0:
            # if the user has chosen a list before 
            # directs user to a page to set the session["current_list"]
            # don't display quiz/study options in topnav until list selected
            return render_template("set_session2.html", full_name=full_name)
        else:
            # if the user is choosing a list for the first time
            # directs user to a page to set the session["current_list"]
            return render_template("set_session.html", full_name=full_name)
    else:
        # POST request for when user clicks "submit" (chooses list)
        # the session["current_list"] is set accordingly
        session["current_list"] = request.form.get("current_list").strip()
        list_of_words = []
        list_of_definitions = []
        # make lists function makes list_of_words and list_of_definitions
        make_lists(list_of_words, list_of_definitions)
        # directs user to "list selected" page
        return redirect("/list_selected", 303)


@app.route("/study", methods=["GET", "POST"])
def study():
    global name_of_collection
    # full_name created to display in top right corner
    full_name = session["first_name"].title()+" "+session["last_name"].title()
    all_words = []
    # if list_of_words has no words, means that user is yet to choose a list
    # direct to error page
    if len(list_of_words) < 1:
            return render_template("error_choose_list.html",
                                   full_name=full_name)
    # for each word in the db vocab list, add the entire document to all_words
    # all_words is a list of dictionaries with the word, definition, etc.
    for item in db[name_of_collection].find():
        all_words.append(item)
    name = session["current_list"]
    name.split()
    name = name[-1]
    # name is the number of the list (so the user can see what list they're on)
    # study.html makes a table for the user to study from.
    return render_template("study.html", name=name,
                           full_name=full_name, all_words=all_words)


@app.route("/list_selected", methods=["GET"])
def list_selected():
    global user_doc
    # list selected is a confirmation page for once the user has selected a list
    full_name = session["first_name"].title()+" "+session["last_name"].title()
    name = session["current_list"]
    # name is the name of the current list (for user confirmation)
    # full name is first+last names for display in top right corner
    try:
        # check if the user has accessed this list before by checking user_doc
        # user_doc is dict that contains lists the user has accessed in session
        # user_doc makes it easier to update mongo on user progress
        # if user has accessed list before, do nothing
        user_doc[name.lower()]
    except:
        # if the user has never accessed this list before, initialize
        user_doc[name.lower()] = {"correct": 0, "wrong": 0}
    # set name to just the number of the current list (for user display)
    name.split()
    name = name[-1]
    return render_template("list_selected.html",
                           name=name, full_name=full_name)


@app.route("/progress", methods=["GET"])
def progress():
        no_questions = False
        right = None
        wrong = None
        percent_accuracy = None
        current_list = session["current_list"]
        username = session["username"]
        full_name = session["first_name"].title()+" "+session["last_name"].title()
        full_doc = db.users.find_one({"username": username})
        for item in db.users.find_one({"username": username}):
            if item == session["current_list"].lower():
                if item in full_doc:
                    print("YES")
                    right = full_doc[item]["correct"]
                    wrong = full_doc[item]["wrong"]
                    percent_accuracy = (right/(right+wrong))*100
        if right is None and wrong is None:
            no_questions = True
        return render_template("progress.html", username=username,
                               full_name=full_name,
                               percent_accuracy=percent_accuracy,
                               no_questions = no_questions, right=right,
                               wrong=wrong, current_list=current_list)


@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    global correct_def, name_of_collection, list_of_words
    global list_of_definitions, correct_word, wrong_one, wrong_two
    global wrong_three, word_index, user_doc
    # full_name is first+last names
    full_name = session["first_name"].title()+" "+session["last_name"].title()
    # name_of_lis is the name of the current list based on session
    name_of_lis = session["current_list"]
    if request.method == "GET":
        # if the user has not yet chosen list, list_of_words is empty
        # redirect user to error page
        if len(list_of_definitions) == 0:
            try:
                list_of_words[0]
                name = session["current_list"]
                name.split()
                name = name[-1]
                return render_template("finished.html", name=name, full_name=full_name)
            except:
                return render_template("error_choose_list.html",
                                    full_name=full_name)
        elif len(list_of_definitions) < 4:
            # if the len of list_of_words <4, the user only has 4 words left
            # can't get wrong answers from current_list, so must get elsewhere
            x = False
            while not x:
                # check if correct_word set to "Nothing using loop
                # if so, try another word from the list
                word_index = random.randint(0, (len(list_of_words)-1))
                correct_word = list_of_words[word_index]
                if correct_word == "Nothing":
                    continue
                else:
                    x = True
            # the correct_definiton is set
            correct_def = list_of_definitions[word_index]
            list_of_words.append("Nothing")
            # lis2 made of other defs (that aren't in the list of defs left)
            lis2 = []
            for item in db[name_of_collection].find():
                if item in list_of_definitions:
                    continue
                else:
                    lis2.append(item["definition"])
            # wrong_one is a random word from lis2
            wrong_one = random.choice(lis2)
            not_the_same = False
            # wrong_two is any word from lis_2 that is not wrong_one 
            # check that wrong_two ≠ wrong_one using loop
            while not not_the_same:
                wrong_two = random.choice(lis2)
                if wrong_two != wrong_one:
                    not_the_same = True
                else:
                    continue
            not_the_same = False
            # wrong_three is any word from lis_2 that is not wrong_one/wrong_two 
            # check that wrong_three ≠ wrong_two ≠ wrong_one using loop
            while not not_the_same:
                wrong_three = random.choice(lis2)
                if wrong_three != wrong_one:
                    if wrong_three != wrong_two:
                        not_the_same = True
                    else:
                        continue
                else:
                    continue
            # create and shuffle the list of answers to ensure random order
            list_of_options = [correct_def,
                               wrong_one, wrong_two, wrong_three]
            random.shuffle(list_of_options)
            return render_template("question.html", correct_word=correct_word,
                                   list_of_options=list_of_options,
                                   name_of_lis=name_of_lis,
                                   full_name=full_name)

        else:
            # more than 4 words left to answer
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
                                   name_of_lis=name_of_lis,
                                   full_name=full_name)
    else:
        # user has submitted an answer
        username = session["username"]
        name_of_lis = session["current_list"]
        # set the username and the name of the current list for later access
        if request.form.get("options") == correct_def:
            # user was correct
            # update dictionary (user_doc)
            user_doc[session["current_list"].lower()]["correct"] += 1
            # update mongo according to user_doc
            db.users.update({"username": username},
                            {"$set": {session["current_list"].lower():
                             user_doc[session["current_list"].lower()]}})
            full_doc = db[name_of_collection].find_one({"word": correct_word})
            quote_ggs = full_doc["quote_ggs"].split()
            # since correct, take out of list so user doesn't answer again
            list_of_words.pop(word_index)
            list_of_definitions.pop(word_index)
            correct_translit = full_doc["transliteration"]
            # go to correct.html and print details about the correct word
            return render_template("correct.html", correct_word=correct_word,
                                   correct_def=correct_def,
                                   quote_ggs=quote_ggs,
                                   name_of_lis=name_of_lis,
                                   correct_translit=correct_translit,
                                   username=username, full_name=full_name)
        elif request.form.get("options") is None:
            # if no response, the user clicked submit without selecting option
            flash("Please submit a response")
            # render page again
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
            quote_ggs = full_doc["quote_ggs"].split()
            correct_translit = full_doc["transliteration"]
            return render_template("incorrect.html", correct_word=correct_word,
                                   correct_def=correct_def,
                                   quote_ggs=quote_ggs,
                                   name_of_lis=name_of_lis,
                                   correct_translit=correct_translit,
                                   full_name=full_name)


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
        username = request.form.get("user").strip()
        if doc is None:
            # if not user in db, the username is wrong
            flash("Wrong Username")
            return render_template("login.html")
        elif doc["password"] == request.form.get("pass").strip():
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
            f_name = db.users.find_one({"username": username})["first_name"]
            l_name = db.users.find_one({"username": username})["last_name"]
            session["first_name"] = f_name
            session["last_name"] = l_name
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
        session["username"] = request.form.get("user").strip()
        security_word = request.form.get("security_word").strip()
        doc = db.users.find_one({"username": session["username"]})
        if doc is None:
            # if user not in db, wrong username
            flash("Wrong Username")
            return render_template("wrong_password.html")
        elif doc["security_word"].lower() == security_word.lower().strip():
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
        if request.form.get("pass").strip() != request.form.get("c_pass").strip():
            # password ≠ confirmed password
            flash("Re-Type Password or Password Confirmation")
            return render_template("reset_password.html")
        elif len(request.form.get("pass").strip()) < 8:
            # password length is less than 8 characters
            flash("Password length is less than 8 characters")
            return render_template("reset_password.html")
        else:
            # everything is fine, so reset password in database
            # print confirmation message and redirect to homepage
            db.users.update({"username": username},
                            {"$set": {"password": request.form.get("pass").strip()}})
            flash("Password reset")
            return redirect("/")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        # user is signing up
        return render_template("sign_up.html")
    else:
        user = request.form.get("user").strip()
        c_user = request.form.get("c_user").strip()
        pass_word = request.form.get("pass").strip()
        c_pass = request.form.get("c_pass").strip()
        security_word = request.form.get("security_word").strip()
        email = request.form.get("email").strip()
        f_name = request.form.get("f_name").strip()
        l_name = request.form.get("l_name").strip()
        if request.form.get("user").strip() != request.form.get("c_user").strip():
            # username ≠ confirmed username
            flash("Please retype the username/confirmed username")
            user = ""
            c_user = ""
            return render_template("sign_up2.html", user=user,
                                   pass_word=pass_word, email=email,
                                   security_word=security_word,
                                   f_name=f_name, l_name=l_name,
                                   c_pass=c_pass, c_user=c_user)
        if db.users.find_one({"username":
                              request.form.get("user").strip()}) is not None:
            # username already exists in database
            flash("Username already taken")
            user = ""
            c_user = ""
            return render_template("sign_up2.html", user=user,
                                   pass_word=pass_word, email=email,
                                   security_word=security_word,
                                   f_name=f_name, l_name=l_name,
                                   c_pass=c_pass, c_user=c_user)
        if request.form.get("pass").strip() != request.form.get("c_pass").strip():
            # password ≠ confirmed password
            flash("Please retype the password/confirmed password")
            pass_word = ""
            c_pass = ""
            return render_template("sign_up2.html", user=user,
                                   pass_word=pass_word, email=email,
                                   security_word=security_word,
                                   f_name=f_name, l_name=l_name,
                                   c_pass=c_pass, c_user=c_user)
        if len(request.form.get("f_name").strip()) < 1:
            flash("Please enter a first name")
            f_name = ""
            return render_template("sign_up2.html", user=user,
                                   pass_word=pass_word, email=email,
                                   security_word=security_word,
                                   f_name=f_name, l_name=l_name,
                                   c_pass=c_pass, c_user=c_user)
        if len(request.form.get("l_name").strip()) < 1:
            flash("Please enter a last name")
            l_name = ""
            return render_template("sign_up2.html", user=user,
                                   pass_word=pass_word, email=email,
                                   security_word=security_word,
                                   f_name=f_name, l_name=l_name,
                                   c_pass=c_pass, c_user=c_user)
        if "@" not in list(request.form.get("email").strip()):
            flash("Please enter a valid email")
            email = ""
            return render_template("sign_up2.html", user=user,
                                   pass_word=pass_word, email=email,
                                   security_word=security_word,
                                   f_name=f_name, l_name=l_name,
                                   c_pass=c_pass, c_user=c_user)
        if len(request.form.get("pass").strip()) < 8:
            # password length is less than 8 characters
            flash("Please enter a valid password greater than 8 characters")
            pass_word = ""
            c_pass = ""
            return render_template("sign_up2.html", user=user,
                                   pass_word=pass_word, email=email,
                                   security_word=security_word,
                                   f_name=f_name, l_name=l_name,
                                   c_pass=c_pass, c_user=c_user)
        db.users.insert_one({"username": request.form.get("user").strip(),
                             "password": request.form.get("pass").strip(),
                             "security_word":
                             request.form.get("security_word").strip(),
                             "email": request.form.get("email").strip(),
                             "first_name": request.form.get("f_name").strip(),
                             "last_name": request.form.get("l_name").strip()})
        # add user to db and set session[username] and session[email]
        session["username"] = request.form.get("user").strip()
        session["email"] = request.form.get("email").strip()
        session["first_name"] = request.form.get("f_name").strip()
        session["last_name"] = request.form.get("l_name").strip()
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
    session["first_name"] = None
    session["last_name"] = None
    user_doc = {}
    return render_template("logged_out.html")


@app.route("/profile", methods=["GET"])
def profile():
    if len(list_of_words) < 1:
        # if the list_of_words is empty, the user has notchosen a list yet
        # do not display quiz/study options in topnav bar
        # profile.html
        username = session["username"]
        email = db.users.find_one({"username": username})["email"]
        doc = db.users.find_one({"username": username})
        full_name = session["first_name"].title()+" "+session["last_name"].title()
        # create full_name, email, username based on session and db
        stats = {}
        # stats contains  all the lists the user has & the corresponding data
        # stats = {"list_name: {"wrong":#, "correct":#}}
        progress = {}
        # progress contains list_nums with corresponding % accuracy and num ?'s
        # progress = {"list_number": {percent accuracy: %, num_questions: #}}
        for item in doc:
            name_of_item = list(str(item))
            if name_of_item[0:4] == list("list"):
                # if item in the db.users is data of a list (not username, etc)
                # add to stats
                stats[item] = doc[item]
        for lis in stats:
            # for item in stats, get the number of questions (wrong+correct)
            # for item in stats, get percent accuracy (correct/num_questions)
            num_questions = (stats[lis]["correct"]+stats[lis]["wrong"])
            percent_accuracy = int((stats[lis]["correct"] / num_questions)*100)
            progress[list(lis)[-1]] = {"percent_accuracy": percent_accuracy,
                                    "total_questions": num_questions}
        # od is the sorted version of progress (sorted by list number)
        od = collections.OrderedDict(sorted(progress.items()))
        return render_template("profile_2.html", email=email, username=username,
                            od=od, full_name=full_name)
    else:
        # user has chosen a list, quiz/study options displayed in topnav bar
        # profile.html
        username = session["username"]
        email = db.users.find_one({"username": username})["email"]
        doc = db.users.find_one({"username": username})
        full_name = session["first_name"].title()+" "+session["last_name"].title()
        # create full_name, email, username based on session and db
        stats = {}
        # stats contains  all the lists the user has & the corresponding data
        # stats = {"list_name: {"wrong":#, "correct":#}}
        progress = {}
        # progress contains list_nums with corresponding % accuracy and num ?'s
        # progress = {"list_number": {percent accuracy: %, num_questions: #}}
        for item in doc:
            name_of_item = list(str(item))
            if name_of_item[0:4] == list("list"):
                # if item in the db.users is data of a list (not username, etc)
                # add to stats
                stats[item] = doc[item]
        for lis in stats:
            # for item in stats, get the number of questions (wrong+correct)
            # for item in stats, get percent accuracy (correct/num_questions)
            num_questions = (stats[lis]["correct"]+stats[lis]["wrong"])
            percent_accuracy = int((stats[lis]["correct"] / num_questions)*100)
            progress[list(lis)[-1]] = {"percent_accuracy": percent_accuracy,
                                    "total_questions": num_questions}
        # od is the sorted version of progress (sorted by list number)
        od = collections.OrderedDict(sorted(progress.items()))
        return render_template("profile.html", email=email, username=username,
                            od=od, full_name=full_name)


if __name__ == "__main__":
    # turn off this debugging stuff before production
    app.config['PROPAGATE_EXCEPTIONS'] = True
    app.config['DEBUG'] = True
    # next line: cause KeyErrors to bubble up to top level
    # so we can see the traceback & debugger
    app.config['TRAP_BAD_REQUEST_ERRORS'] = True
    app.run()
