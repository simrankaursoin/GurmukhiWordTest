# -*- coding: utf-8 -*-
# app.py
from mongo_interface import make_database
from flask import flash, request, Flask, render_template, redirect, session
import secure
from helper import make_lists, retrieve_user_info, reset_sessions
from helper import make_options, check_answers, calculate_percent_accuracy
from helper import update_session, update_session_from_form, get_form
from helper import get_stuff_from_form
import random
import collections
db = make_database()
list_of_words = []
list_of_definitions = []
name_of_collection = ''
app = Flask(__name__)
app.secret_key = secure.APP_SECRET_KEY
user_doc = {}


@app.route("/", methods=["GET"])
def main():
    try:
        retrieve_user_info(session)
        full_name = retrieve_user_info(session)["full_name"]
        if len(list_of_words) > 0:
            template = "homepage_2.html"
        else:
            template = "homepage_3.html"
        return render_template(template, full_name=full_name)
    except:
        return render_template("homepage.html")


@app.route("/setsession", methods=["GET", "POST"])
def set_session():
    global list_of_words, list_of_definitions, name_of_collection
    if request.method == "GET":
        retrieve_user_info(session)
        if len(list_of_words) > 0:
            template = "set_session2.html"
        else:
            template = "set_session.html"
        full_name = retrieve_user_info(session)["full_name"]
        return render_template(template,
                               full_name=full_name)
    else:
        session["current_list"] = request.form.get("current_list").strip()
        list_of_words = []
        list_of_definitions = []
        name_of_collection = str(session["current_list"]).lower()
        make_lists(list_of_words, list_of_definitions, name_of_collection)
        return redirect("/list_selected", 303)


@app.route("/study", methods=["GET", "POST"])
def study():
    global name_of_collection
    retrieve_user_info(session)
    full_name = retrieve_user_info(session)["full_name"]
    all_words = []
    if len(list_of_words) < 1:
            return render_template("error_choose_list.html",
                                   full_name=full_name)
    for item in db[name_of_collection].find():
        all_words.append(item)
    name = session["current_list"]
    name = name[-1]
    return render_template("study.html", name=name,
                           full_name=full_name, all_words=all_words)


@app.route("/list_selected", methods=["GET"])
def list_selected():
    global user_doc
    retrieve_user_info(session)
    full_name = retrieve_user_info(session)["full_name"]
    name = session["current_list"]
    if name.lower() not in user_doc:
        user_doc[name.lower()] = {"correct": 0, "wrong": 0,
                                  "correct_words": [], "wrong_words": []}
    name = name[-1]
    return render_template("list_selected.html",
                           name=name, full_name=full_name)


@app.route("/progress", methods=["GET"])
def progress():
    retrieve_user_info(session)
    no_questions = False
    doc = retrieve_user_info(session)["doc"]
    current_list = session["current_list"].lower()
    if current_list in doc:
        correct_words = doc[current_list]["correct_words"]
        wrong_words = doc[current_list]["wrong_words"]
        percent_accuracy = calculate_percent_accuracy(doc, current_list)
        percent_inaccuracy = 100 - percent_accuracy
    else:
        no_questions = True
        correct_words = ""
        wrong_words = ""
        percent_accuracy = ""
        percent_inaccuracy = ""
    current_list = session["current_list"][-1]
    return render_template("progress.html",
                           username=retrieve_user_info(session)["username"],
                           full_name=retrieve_user_info(session)["full_name"],
                           percent_accuracy=percent_accuracy,
                           no_questions=no_questions, current_list=current_list,
                           correct_words=correct_words,
                           wrong_words=wrong_words,
                           percent_inaccuracy=percent_inaccuracy)
    

@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    global correct_def, name_of_collection, list_of_words, list_of_definitions
    global correct_word, list_of_options, word_index, user_doc
    full_name = retrieve_user_info(session)["full_name"]
    name_of_lis = list(session["current_list"])[-1]
    if request.method == "GET":
        if len(list_of_definitions) < 1:
            if len(list_of_words) > 0:
                name = session["current_list"].lower()
                full_doc = db.users.find_one({"username": session["username"]})
                percent_accuracy = calculate_percent_accuracy(full_doc, name)
                name = name[-1]
                return render_template("finished.html", name=name,
                                       full_name=full_name,
                                       percent_accuracy=percent_accuracy)
            else:
                return render_template("error_choose_list.html",
                                       full_name=full_name)
        elif len(list_of_definitions) < 4:
            list2 = []
            for item in db[name_of_collection].find():
                if item not in list_of_definitions:
                    list2.append(item["definition"])
            not_nothing = True
            while not_nothing:
                word_index = random.randint(0, (len(list_of_words)-1))
                correct_word = list_of_words[word_index]
                if correct_word != "Nothing":
                    not_nothing = False
            correct_def = list_of_definitions[word_index]
            list_of_options = []
            for i in range(0, 3):
                wrong_index = random.randint(0, (len(list2)-1))
                list_of_options.append(list2[wrong_index])
            list_of_options.append(correct_def)
            random.shuffle(list_of_options)
            list_of_words.append("Nothing")

        else:
            word_index = random.randint(0, (len(list_of_words)-1))
            correct_word = list_of_words[word_index]
            correct_def = list_of_definitions[word_index]
            list_of_options = make_options(list_of_words,
                                           list_of_definitions,
                                           correct_def)

        return render_template("question.html", correct_word=correct_word,
                               list_of_options=list_of_options,
                               name_of_lis=name_of_lis,
                               full_name=full_name)
    else:
        username = retrieve_user_info(session)["username"]
        name_of_lis = list(session["current_list"])[-1]
        current_list = session["current_list"].lower()
        if request.form.get("options") == correct_def:
            user_doc[current_list]["correct"] += 1
            user_doc[current_list]["correct_words"].append(correct_word)
            db.users.update({"username": username},
                            {"$set": {current_list:
                             user_doc[current_list]}})

            full_doc = db[name_of_collection].find_one({"word": correct_word})
            quote_ggs = full_doc["quote_ggs"].split()
            list_of_words.pop(word_index)
            list_of_definitions.pop(word_index)
            correct_translit = full_doc["transliteration"]
            return render_template("correct.html", correct_word=correct_word,
                                   correct_def=correct_def,
                                   quote_ggs=quote_ggs,
                                   name_of_lis=name_of_lis,
                                   correct_translit=correct_translit,
                                   username=username, full_name=full_name)
        elif request.form.get("options") is None:
            flash("Please submit a response")
            return render_template("question.html", correct_word=correct_word,
                                   list_of_options=list_of_options)
        else:
            user_doc[current_list]["wrong"] += 1
            user_doc[current_list]["wrong_words"].append(correct_word)
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
        return render_template("login.html")
    else:
        doc = db.users.find_one({"username":
                                 request.form.get("user").lower().strip()})
        username = request.form.get("user").strip()
        if doc is None:
            flash("Wrong Username")
            return render_template("login.html")
        elif doc["password"] == request.form.get("pass").strip():
            user_doc = {}
            update_session(session, username, doc)
            flash("Successful login")
            return redirect("/setsession", 303)
        else:
            update_session(session, username, doc)
            f_name = doc["first_name"]
            l_name = doc["last_name"]
            session["first_name"] = f_name
            session["last_name"] = l_name
            flash("Wrong password")
            return render_template("login.html")


@app.route("/edit_info", methods=["GET", "POST"])
def edit_info():
    if request.method == "GET":
        retrieve_user_info(session)
        return render_template("edit_info.html",
                               user=retrieve_user_info(session)["username"],
                               c_user=retrieve_user_info(session)["username"],
                               email=retrieve_user_info(session)["email"],
                               f_name=retrieve_user_info(session)["f_name"].split(" ")[0],
                               l_name=retrieve_user_info(session)["l_name"].split(" ")[0])              
    else:
        get_stuff_from_form(request, session)
        if not check_answers(request, flash, session["username"], session, True)["errors"]:
            username_query = {"username": session["username"]}
            db.users.update(username_query, {'$set':
                                             {"email":
                                              get_form(request, "email")}})
            db.users.update(username_query, {'$set':
                                             {"username":
                                              get_form(request, "user")}})
            db.users.update(username_query, {'$set':
                                             {"first_name":
                                              get_form(request, "f_name").split(" ")[0]}})
            db.users.update(username_query, {'$set':
                                             {"last_name":
                                              get_form(request, "l_name").split(" ")[0]}})
            db.users.update(username_query, {'$set':
                                             {"gender":
                                              get_form(request, "gender")}})
            update_session_from_form(session, request)
            flash("Profile updated")
            return redirect("/profile", 303)
        else:
            return render_template("edit_info.html", user=check_answers(request, flash, session["username"], session, False)["new_stuff"]["user"],
                                   email=check_answers(request, flash, session["username"], session, False)["new_stuff"]["email"],
                                   f_name=check_answers(request, flash, session["username"], session, False)["new_stuff"]["f_name"],
                                   l_name=check_answers(request, flash, session["username"], session, False)["new_stuff"]["l_name"],
                                   c_user=check_answers(request, flash, session["username"], session, False)["new_stuff"]["c_user"])


@app.route("/security", methods=["GET", "POST"])
def security():
    if request.method == "GET":
        return render_template("wrong_password.html")
    else:
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
    else:
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
    if request.method == "GET":
        return render_template("sign_up.html")
    else:
        pass_word = request.form.get("pass").strip()
        c_pass = request.form.get("c_pass").strip()
        security_word = request.form.get("security_word").strip()
        get_stuff_from_form(request, session)
        if not check_answers(request, flash, session["username"], session, True)["errors"]:
                          db.users.insert_one({"username": request.form.get("user").strip(),
                                            "password": request.form.get("pass").strip(),
                                            "security_word":
                                            request.form.get("security_word").strip(),
                                            "email": request.form.get("email").strip(),
                                            "first_name":
                                            request.form.get("f_name").split(" ")[0],
                                            "last_name":
                                            request.form.get("l_name").split(" ")[0],
                                            "gender":
                                            request.form.get("gender")})
                          update_session_from_form(session, request)
                          flash("Profile created")
                          return redirect("/setsession", 303)
                         
        elif (request.form.get("pass").strip() !=
              request.form.get("c_pass").strip()):
            flash("Please retype the password/confirmed password")
            pass_word = ""
            c_pass = ""
        print("NAH")
        return render_template("sign_up2.html",
                                   user=check_answers(request, flash, session["username"], session, False)["new_stuff"]["user"],
                                   pass_word=pass_word,
                                   email=check_answers(request, flash, session["username"], session, False)["new_stuff"]["email"],
                                   security_word=security_word,
                                   f_name=check_answers(request, flash, session["username"], session, False)["new_stuff"]["f_name"],
                                   l_name=check_answers(request, flash, session["username"], session, False)["new_stuff"]["l_name"],
                                   c_pass=c_pass,
                                   c_user=check_answers(request, flash, session["username"], session, False)["new_stuff"]["c_user"])


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
        correct_words = stats[lis]["correct_words"]
        wrong_words = stats[lis]["wrong_words"]
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
                           od=od,
                           full_name=retrieve_user_info(session)["full_name"],
                           gender=retrieve_user_info(session)["gender"])


if __name__ == "__main__":
    app.config['PROPAGATE_EXCEPTIONS'] = True
    app.config['DEBUG'] = True
    app.config['TRAP_BAD_REQUEST_ERRORS'] = True
    app.run()
