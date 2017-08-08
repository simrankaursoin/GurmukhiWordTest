# -*- coding: utf-8 -*-
# app.py
from mongo_interface import make_database
from flask import flash, request, Flask, render_template, redirect, session
from helper import make_lists, retrieve_user_info, reset_sessions
from helper import make_options, check_answers, calculate_percent_accuracy
from helper import UpdateSession, UpdateSession_Form, UpdateCorrect
from helper import UpdateWrong, less_than_four
import collections
import random
import secure

# global variables
list_of_definitions = []
list_of_words = []
user_doc = {}
list_of_options = []
db = make_database()


app = Flask(__name__)
app.secret_key = secure.APP_SECRET_KEY


@app.route("/", methods=["GET"])
def main():
    try:
        global list_of_words, list_of_definitions
        # retrieve_user_info uses user info from session to create full_name
        full_name = retrieve_user_info(session)["full_name"]
    except:
        # if error, the user hasn't signed in yet >> homepage.html
        return render_template("homepage.html")
    # if len(list_of_words) > 0, user hasn't chosen a list >> homepage_2.html
    if len(list_of_words) > 0:
        template = "homepage_2.html"
    # else, user has chosen a list >> homepage_3.html
    else:
        template = "homepage_3.html"
    return render_template(template, full_name=full_name)


@app.route("/setsession", methods=["GET", "POST"])
def set_session():
    global list_of_words, list_of_definitions
    if request.method == "GET":
        # if choosing list for the first time, don't show quiz/study in nav bar
        #       >> set_session2.html
        if len(list_of_words) > 0:
            template = "set_session2.html"
        # else, go to set_session.html
        else:
            template = "set_session.html"
        full_name = retrieve_user_info(session)["full_name"]
        return render_template(template,
                               full_name=full_name)
    elif request.method == "POST":
        # once the user has selected a list, set session[current_list]
        session["current_list"] = request.form.get("current_list").strip()
        # clear lists of words/defs (in case they had previously chosen a list)
        list_of_words = []
        list_of_definitions = []
        name_of_collection = str(session["current_list"]).lower()
        # make lists of words/defs according to current list
        make_lists(list_of_words, list_of_definitions, name_of_collection)
        # redirect user to confirmation page
        return redirect("/list_selected", 303)


@app.route("/study", methods=["GET"])
def study():
    name_of_collection = str(session["current_list"]).lower()
    full_name = retrieve_user_info(session)["full_name"]
    all_words = []
    # if the list_of_words is empty, user hasn't chosen a list
    #         >> redirect to error page
    if len(list_of_words) < 1:
            return render_template("error_choose_list.html",
                                   full_name=full_name)
    # if user has chosen a list, create all_words based on vocab list in db
    for item in db[name_of_collection].find():
        all_words.append(item)
    # name is the list number
    name = session["current_list"]
    name = name[-1]
    return render_template("study.html", name=name,
                           full_name=full_name, all_words=all_words)


@app.route("/list_selected", methods=["GET"])
def list_selected():
    global user_doc
    full_name = retrieve_user_info(session)["full_name"]
    name = session["current_list"].lower()
    # name is the name of the vocab list
    # if list does not exist in user_doc, the user has not accessed it before
    #           >> initialize list in user doc with values equal to 0
    if name not in user_doc:
        user_doc[name] = {"correct": 0, "wrong": 0, "correct_words": [],
                          "wrong_words": []}
    # reset name to just the list number
    name = name[-1]
    return render_template("list_selected.html",
                           name=name, full_name=full_name)


@app.route("/progress", methods=["GET"])
def progress():
    no_questions = False
    # doc is the user's document in the db
    doc = retrieve_user_info(session)["doc"]
    current_list = session["current_list"].lower()
    # if the current list in doc, user has answered questions from the list
    if current_list in doc:
        correct_words = list(set(doc[current_list]["correct_words"]))
        wrong_words = list(set(doc[current_list]["wrong_words"]))
        # get the list of wrong words and list of correct words (minus repeats)
        # calculate percent accuracy and percent inaccuracy
        percent_accuracy = calculate_percent_accuracy(doc, current_list)[0]
        percent_inaccuracy = calculate_percent_accuracy(doc, current_list)[1]
    # if list is not in doc, user hasn't answered any questions yet
    else:
        # set no_questions = True so the browser can handle accordingly
        no_questions = True
        # set all values to blanks (so that the return statement doesn't crash)
        correct_words = ""
        wrong_words = ""
        percent_accuracy = ""
        percent_inaccuracy = ""
    # reset current_list to just the list number
    current_list = session["current_list"][-1]
    return render_template("progress.html",
                           username=retrieve_user_info(session)["username"],
                           full_name=retrieve_user_info(session)["full_name"],
                           percent_accuracy=percent_accuracy,
                           no_questions=no_questions,
                           current_list=current_list,
                           correct_words=correct_words,
                           wrong_words=wrong_words,
                           percent_inaccuracy=percent_inaccuracy)


@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    global list_of_words, list_of_definitions, user_doc, correct_def
    global correct_word, word_index, list_of_options
    full_name = retrieve_user_info(session)["full_name"]
    name = session["current_list"].lower()
    if request.method == "GET":
        if len(list_of_definitions) < 1 and len(list_of_words) > 0:
            full_doc = db.users.find_one({"username": session["username"]})
            percent_accuracy = calculate_percent_accuracy(full_doc, name)[0]
            return render_template("finished.html", name=name[-1],
                                   full_name=full_name,
                                   percent_accuracy=percent_accuracy)
        elif len(list_of_definitions) < 1:
            return render_template("error_choose_list.html",
                                   full_name=full_name)
        elif len(list_of_definitions) < 4:
            make_choices = less_than_four(name, list_of_words,
                                          list_of_definitions, list_of_options)
            list_of_options = make_choices["list_of_options"]
            list_of_words = make_choices["list_of_words"]
            list_of_definitions = make_choices["list_of_definitions"]
            correct_word = make_choices["correct_word"]
            correct_def = make_choices["correct_def"]
            word_index = make_choices["word_index"]
        else:
            word_index = random.randint(0, (len(list_of_words)-1))
            correct_word = list_of_words[word_index]
            correct_def = list_of_definitions[word_index]
            list_of_options = make_options(list_of_words, list_of_definitions,
                                           correct_def)
        return render_template("question.html", correct_word=correct_word,
                               list_of_options=list_of_options,
                               name_of_lis=name[-1], full_name=full_name)
    elif request.method == "POST":
        username = retrieve_user_info(session)["username"]
        if request.form.get("options") == correct_def:
            info = UpdateCorrect(user_doc, correct_word, name, username,
                                 word_index, list_of_words,
                                 list_of_definitions)
            return render_template("correct.html", correct_word=correct_word,
                                   correct_def=correct_def, username=username,
                                   quote_ggs=info["quote_ggs"],
                                   name_of_lis=name[-1], full_name=full_name,
                                   correct_translit=info["correct_translit"])
        else:
            info = UpdateWrong(user_doc, correct_word, name, username, session,
                               word_index, list_of_words, list_of_definitions)
            return render_template("incorrect.html", correct_word=correct_word,
                                   correct_def=correct_def,
                                   full_name=full_name, name_of_lis=name[-1],
                                   quote_ggs=info["quote_ggs"],
                                   correct_translit=info["correct_translit"])


@app.route("/login", methods=["GET", "POST"])
def login():
    global user_doc
    if request.method == "GET":
        return render_template("login.html")
    elif request.method == "POST":
        doc = db.users.find_one({"username":
                                 request.form.get("user").lower().strip()})
        username = request.form.get("user").strip()
        if doc is None:
            flash("Wrong Username")
            return render_template("login.html")
        elif doc["password"] == request.form.get("pass").strip():
            user_doc = {}
            UpdateSession(session, username, doc)
            flash("Successful login")
            return redirect("/setsession", 303)
        else:
            UpdateSession(session, username, doc)
            f_name = doc["first_name"]
            l_name = doc["last_name"]
            session["first_name"] = f_name
            session["last_name"] = l_name
            flash("Wrong password")
            return render_template("login.html")


@app.route("/edit_info", methods=["GET", "POST"])
def edit_info():
    if request.method == "GET":
        return render_template("edit_info.html",
                               user=retrieve_user_info(session)["username"],
                               c_user=retrieve_user_info(session)["username"],
                               email=retrieve_user_info(session)["email"],
                               f_name=retrieve_user_info(session)
                               ["f_name"].split(" ")[0],
                               l_name=retrieve_user_info(session)
                               ["l_name"].split(" ")[0])
    elif request.method == "POST":
        new_stuff = check_answers(request, flash, session, False)["new_stuff"]
        if not check_answers(request, flash, session, True)["errors"]:
            username_query = {"username": session["username"]}
            things_to_update = ["email", "user", "gender"]
            for i in things_to_update:
                db.users.update(username_query, {'$set':
                                                 {i: new_stuff[i]}})
            db.users.update(username_query, {'$set':
                                             {"first_name":
                                              new_stuff["f_name"]}})
            db.users.update(username_query, {'$set':
                                             {"last_name":
                                              new_stuff["l_name"]}})
            UpdateSession_Form(session, request)
            flash("Profile updated")
            return redirect("/profile", 303)
        else:
            return render_template("edit_info.html",
                                   user=new_stuff["user"],
                                   email=new_stuff["email"],
                                   f_name=new_stuff["f_name"],
                                   l_name=new_stuff["l_name"],
                                   c_user=new_stuff["c_user"])


@app.route("/security", methods=["GET", "POST"])
def security():
    if request.method == "GET":
        return render_template("wrong_password.html")
    elif request.method == "POST":
        session["username"] = request.form.get("user").strip()
        security_word = request.form.get("security_word").strip()
        doc = db.users.find_one({"username": session["username"]})
        if doc is None:
            flash("Wrong Username")
            return render_template("wrong_password.html")
        elif doc["security_word"].lower() == security_word.lower().strip():
            return redirect("/reset_password", 303)
        else:
            flash("Security word is incorrect. Try again")
            return render_template("wrong_password.html")


@app.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    username = session["username"]
    if request.method == "GET":
        return render_template("reset_password.html")
    elif request.method == "POST":
        if (request.form.get("pass").strip() !=
           request.form.get("c_pass").strip()):
            flash("Re-Type Password or Password Confirmation")
            return render_template("reset_password.html")
        else:
            db.users.update({"username": username},
                            {"$set": {"password":
                             request.form.get("pass").strip()}})
            flash("Password reset")
            return redirect("/")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    new_stuff = check_answers(request, flash, session, False)["new_stuff"]
    if request.method == "GET":
        return render_template("sign_up.html")
    elif request.method == "POST":
        pass_word = request.form.get("pass").strip()
        c_pass = request.form.get("c_pass").strip()
        security_word = request.form.get("security_word").strip()
        if not check_answers(request, flash, session, True)["errors"]:
            db.users.insert_one({"username": new_stuff["user"],
                                 "password": request.form.get("pass").strip(),
                                 "security_word": request.form.get
                                 ("security_word").strip(),
                                 "email": new_stuff["email"],
                                 "first_name": new_stuff["f_name"],
                                 "last_name": new_stuff["l_name"],
                                 "gender": new_stuff["gender"]})
            UpdateSession_Form(session, request)
            flash("Profile created")
            return redirect("/setsession", 303)
        elif (request.form.get("pass").strip() !=
              request.form.get("c_pass").strip()):
            flash("Please retype the password/confirmed password")
            pass_word = ""
            c_pass = ""
        return render_template("sign_up2.html",
                               user=new_stuff["user"],
                               pass_word=pass_word,
                               email=new_stuff["email"],
                               security_word=security_word,
                               f_name=new_stuff["f_name"],
                               l_name=new_stuff["l_name"],
                               c_pass=c_pass,
                               c_user=new_stuff["c_user"])


@app.route("/logged_out", methods=["GET"])
def logged_out():
    global user_doc
    reset_sessions(session, user_doc)
    return render_template("logged_out.html")


@app.route("/profile", methods=["GET"])
def profile():
    retrieve_user_info(session)
    doc = retrieve_user_info(session)["doc"]
    stats = {}
    progress = {}
    for item in doc:
        name_of_item = list(str(item))
        if name_of_item[0:4] == list("list"):
            stats[item] = doc[item]
    for lis in stats:
        num_questions = (stats[lis]["correct"]+stats[lis]["wrong"])
        percent_accuracy = int((stats[lis]["correct"] / num_questions)*100)
        percent_inaccuracy = 100 - percent_accuracy
        correct_words = list(set(stats[lis]["correct_words"]))
        wrong_words = list(set(stats[lis]["wrong_words"]))
        progress[list(lis)[-1]] = {"percent_accuracy": percent_accuracy,
                                   "percent_inaccuracy": percent_inaccuracy,
                                   "total_questions": num_questions,
                                   "correct_words": correct_words,
                                   "wrong_words": wrong_words}
    od = collections.OrderedDict(sorted(progress.items()))
    if len(list_of_words) < 1:
        template = "profile_2.html"
    else:
        template = "profile.html"
    return render_template(template,
                           email=retrieve_user_info(session)["email"],
                           username=retrieve_user_info(session)["username"],
                           full_name=retrieve_user_info(session)["full_name"],
                           gender=retrieve_user_info(session)["gender"], od=od)


if __name__ == "__main__":
    app.config['PROPAGATE_EXCEPTIONS'] = True
    app.config['DEBUG'] = True
    app.config['TRAP_BAD_REQUEST_ERRORS'] = True
    app.run()
