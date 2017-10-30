# -*- coding: utf-8 -*-
# app.py
from mongo_interface import make_database
from bson.objectid import ObjectId  
from flask import flash, request, Flask, render_template, redirect, session
from helper import make_lists, retrieve_user_info, reset_sessions
from helper import make_options, check_answers, calculate_percent_accuracy
from helper import UpdateSession, UpdateSession_Form, UpdateCorrect
from helper import UpdateWrong, less_than_four, CreateMongoList
from helper import retrieve_teacher_info, make_progress_report
from helper import check_if_user_chose_list
from passlib.hash import pbkdf2_sha512
import collections
import arrow
import random
import secure
app = Flask(__name__)
app.secret_key = secure.APP_SECRET_KEY
db = make_database()


@app.route("/", methods=["GET"])
def main():
    try:
        session["email"]
        if session["email"] is None:
            return render_template("homepage.html")
    except KeyError:
        return render_template("homepage.html")
    try:
        if session["user_type"] == "Teacher":
            db.teachers.update({"username": session["username"]},
                               {"$set": {"last_accessed":
                                         arrow.utcnow().format('YYYY-MM-DD')}})
            full_name = retrieve_teacher_info(session)["full_name"]
            return render_template("homepage_teacher.html",
                                   full_name=full_name)
    except KeyError:
        full_name = check_if_user_chose_list(session, arrow)["full_name"]
        template = check_if_user_chose_list(session, arrow)["template"]
    full_name = check_if_user_chose_list(session, arrow)["full_name"]
    template = check_if_user_chose_list(session, arrow)["template"]
    return render_template(template, full_name=full_name)


@app.route("/setsession", methods=["GET", "POST"])
def set_session():
    if request.method == "GET":
        user_info = retrieve_user_info(session)
        db.users.update({"username": session["username"]},
                        {"$set": {"last_accessed":
                                  arrow.utcnow().format('YYYY-MM-DD')}})
        # if choosing list for the first time, don't show quiz/study in nav bar
        #       >> set_session2.html
        if len(user_info["doc"]["list_of_words"]) > 0:
            template = "set_session2.html"
        # else, go to set_session.html
        else:
            template = "set_session.html"
        full_name = user_info["full_name"]
        return render_template(template,
                               full_name=full_name)
    elif request.method == "POST":
        # once the user has selected a list, set session[current_list]s
        session["current_list"] = request.form.get("current_list").strip()
        # clear lists of words/defs (in case they had previously chosen a list)
        name_of_collection = str(session["current_list"]).lower()
        # make lists of words/defs according to current list
        make_lists(session, name_of_collection)
        # redirect user to confirmation page
        return redirect("/list_selected", 303)


@app.route("/study", methods=["GET"])
def study():
    name_of_collection = str(session["current_list"]).lower()
    user_info = retrieve_user_info(session)
    full_name = user_info["full_name"]
    all_words = []
    # if the list_of_words is empty, user hasn't chosen a list
    #         >> redirect to error page
    db.users.update({"username": session["username"]},
                    {"$set": {"last_accessed":
                              arrow.utcnow().format('YYYY-MM-DD')}})
    if len(user_info["doc"]["list_of_words"]) < 1:
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


@app.route("/list_info", methods=["GET"])
def list_info():
    lists = {}
    all_list_numbers = ["1", "2", "3", "4", "5", "6"]
    for item in all_list_numbers:
        list_name = "list" + item
        lists[item] = []
        for word in db[list_name].find():
            lists[item].append(word)
            print(word["definition"])
    full_name = retrieve_teacher_info(session)["full_name"]
    return render_template("list_info.html", lists=lists, full_name=full_name)


@app.route("/list_selected", methods=["GET"])
def list_selected():
    full_name = retrieve_user_info(session)["full_name"]
    name = session["current_list"].lower()
    doc = db.users.find_one({"username": session["username"]})
    # name is the name of the vocab list
    # if list does not exist in user_doc, the user has not accessed it before
    #           >> initialize list in user doc with values equal to 0
    if name not in doc:
        CreateMongoList(session, name)
        # reset name to just the list number
    name = name[-1]
    return render_template("list_selected.html",
                           name=name, full_name=full_name)


@app.route("/progress", methods=["GET"])
def progress():
    no_questions = False
    # doc is the user's document in the db
    user_info = retrieve_user_info(session)
    doc = user_info["doc"]
    current_list = session["current_list"].lower()
    db.users.update({"username": session["username"]},
                    {"$set": {"last_accessed":
                              arrow.utcnow().format('YYYY-MM-DD')}})
    # if the current list in doc, user has answered questions from the list
    if current_list in doc:
        correct_words = list(set(doc[current_list]["correct_words"]))
        wrong_words = list(set(doc[current_list]["wrong_words"]))
        # get the list of wrong words and list of correct words (minus repeats)
        # calculate percent accuracy and percent inaccuracy
        percent_accuracy = calculate_percent_accuracy(doc, current_list)[0]
        percent_inaccuracy = calculate_percent_accuracy(doc, current_list)[1]
        if percent_accuracy == 0 and percent_inaccuracy == 0:
            no_questions = True
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
                           username=session["username"],
                           full_name=user_info["full_name"],
                           percent_accuracy=percent_accuracy,
                           no_questions=no_questions, wrong_words=wrong_words,
                           current_list=current_list,
                           correct_words=correct_words,
                           percent_inaccuracy=percent_inaccuracy)


@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    global correct_def, correct_word, word_index
    user_info = retrieve_user_info(session)
    full_name = user_info["full_name"]
    doc = user_info["doc"]
    list_of_defs = doc["list_of_definitions"]
    list_of_words = doc["list_of_words"]
    if request.method == "GET":
        try:
            name = session["current_list"].lower()
        except KeyError:
            return render_template("error_choose_list.html",
                                   full_name=full_name)
        # list of defs is empty but list of words isn't, user has finished list
        if (len(list_of_defs) < 1 and len(list_of_words)) > 0:
            full_doc = db.users.find_one({"username": session["username"]})
            percent_accuracy = calculate_percent_accuracy(full_doc, name)[0]
            return render_template("finished.html", name=name[-1],
                                   full_name=full_name,
                                   percent_accuracy=percent_accuracy)
        # list of definitions has less than 4 items left
        elif len(list_of_defs) < 4:
            # less_than_four returns list_of_options
            #       >> also updates correct values/lists for later reference
            make_choices = less_than_four(name, list_of_words,
                                          list_of_defs)
            list_of_options = make_choices["list_of_options"]
            db.users.update({"username": session["username"]},
                            {'$set': {"list_of_words":
                                      make_choices["list_of_words"]}})
            correct_word = make_choices["correct_word"]
            correct_def = make_choices["correct_def"]
            word_index = make_choices["word_index"]
        else:
            # more than 4 values in list of defs and list of words
            word_index = random.randint(0,
                                        (len(user_info["doc"]["list_of_words"])
                                         - 1))
            correct_word = doc["list_of_words"][word_index]
            correct_def = doc["list_of_definitions"][word_index]
            list_of_options = make_options(user_info["doc"]["list_of_words"],
                                           doc["list_of_definitions"],
                                           correct_def)
        return render_template("question.html", correct_word=correct_word,
                               list_of_options=list_of_options,
                               name_of_lis=name[-1], full_name=full_name)
    elif request.method == "POST":
        name = session["current_list"].lower()
        username = session["username"]
        if request.form.get("options") == correct_def:
            # if user is correct, update mongo and lists of words/defs
            info = UpdateCorrect(correct_word, name, username, word_index)
            return render_template("correct.html", correct_word=correct_word,
                                   correct_def=correct_def, username=username,
                                   quote_ggs=info["quote_ggs"],
                                   name_of_lis=name[-1], full_name=full_name,
                                   correct_translit=info["correct_translit"])
        else:
            # if user is wrong, update mongo and lists of words/defs
            info = UpdateWrong(correct_word, name, username,
                               word_index, session)
            return render_template("incorrect.html", correct_word=correct_word,
                                   correct_def=correct_def,
                                   full_name=full_name, name_of_lis=name[-1],
                                   quote_ggs=info["quote_ggs"],
                                   correct_translit=info["correct_translit"])


@app.route("/my_classes", methods=["GET"])
def my_classes():
    username = session["username"]
    mongo_doc = db.teachers.find_one({"username": username})
    other_stuff_in_mongo_doc = ["_id", "username", "gender",
                                "password", "first_name",
                                "last_name", "security_word",
                                "email", "last_accessed"]
    classes = {}
    for item in mongo_doc:
        if item in other_stuff_in_mongo_doc:
            continue
        else:
            classes[item] = mongo_doc[item]
    students = {}
    for item in classes:
        students[item] = {}
        for student in db.users.find({"class_name": item}):
            f_name = student["first_name"]
            l_name = student["last_name"]
            student_name = '{} {}'.format(f_name.split(" ")[0], l_name)
            student_data = {}
            for thing in student:
                name_of_item = list(str(thing))
                if name_of_item[0:4] == list("list"):
                    try:
                        int(name_of_item[4])
                        percent_accuracy = int((student[thing]["correct"] /
                                               (student[thing]["correct"] +
                                                student[thing]["wrong"]))*100)
                        number_questions = (student[thing]["correct"] +
                                            student[thing]["wrong"])
                        list_name = name_of_item[4]
                        student_data[list_name] = (percent_accuracy,
                                                   number_questions)
                    except (IndexError, ValueError, ZeroDivisionError):
                        continue
            sorted_data = collections.OrderedDict(sorted(student_data.items()))
            students[item][student_name] = sorted_data
    full_name = retrieve_teacher_info(session)["full_name"]
    return render_template("my_classes.html",
                           classes=classes, students=students,
                           full_name=full_name)


@app.route("/delete_class", methods=["GET", "POST"])
def delete_class():
    full_name = retrieve_user_info(session)["full_name"]
    username = session["username"]
    mongo_doc = db.users.find_one({"username": username})
    class_name = mongo_doc["class_name"]
    if request.method == "GET":
        if len(mongo_doc["list_of_words"]) < 1:
            return render_template("delete_class2.html",
                                   full_name=full_name,
                                   class_name=class_name)
        else:
            return render_template("delete_class.html",
                                   full_name=full_name,
                                   class_name=class_name)
    else:
        if request.form.get("yes/no") == "Yes":
            db.users.update({"username": username}, {"$set":
                                                     {"class_name": None}})
            db.users.update({"username": username}, {"$set":
                                                     {"class_code": None}})
            flash("You have officially un-enrolled from ", class_name)
            return redirect("/profile", 303)
        else:
            return redirect("/profile", 303)


@app.route("/edit_info_teacher", methods=["GET", "POST"])
def edit_info_teacher():
    if request.method == "GET":
        other_genders = ["Male", "Female", "Other"]
        user_info = retrieve_teacher_info(session)
        other_genders.remove(user_info["gender"])
        return render_template("edit_info.html",
                               user=user_info["username"],
                               c_user=user_info["username"],
                               email=user_info["email"],
                               f_name=user_info["f_name"].split(" ")[0],
                               l_name=user_info["l_name"].split(" ")[0],
                               gender=user_info["gender"],
                               other_genders=other_genders)
    elif request.method == "POST":
        doc = {}
        for teacher in db.teachers.find():
            for item in teacher:
                doc[item] = teacher[item]
        new_stuff = check_answers(request, flash, session, False)["new_stuff"]
        if session["username"] != new_stuff["username"]:
            if session["username"] in doc.values():
                flash("Username taken")
                other_genders = ["Male", "Female", "Other"]
                other_genders.remove(new_stuff["gender"])
                return render_template("/edit_info.html",
                                       user="", c_user="",
                                       email=new_stuff["email"],
                                       f_name=new_stuff["f_name"],
                                       l_name=new_stuff["l_name"],
                                       gender=new_stuff["gender"],
                                       other_genders=other_genders)
        doc = {}
        for user in db.users.find():
            for item in user:
                doc[item] = user[item]
        if session["username"] != new_stuff["username"]:
            if session["username"] in doc.values():
                flash("Username taken")
                other_genders = ["Male", "Female", "Other"]
                other_genders.remove(new_stuff["gender"])
                return render_template("/edit_info.html",
                                       user="", c_user="",
                                       email=new_stuff["email"],
                                       f_name=new_stuff["f_name"],
                                       l_name=new_stuff["l_name"],
                                       gender=new_stuff["gender"],
                                       other_genders=other_genders)
        if not check_answers(request, flash, session, True)["errors"]:
            username_query = {"username": session["username"]}
            things_to_update = ["email", "username", "gender"]
            for i in things_to_update:
                db.teachers.update(username_query, {'$set':
                                                    {i: new_stuff[i]}})
            db.teachers.update(username_query, {'$set':
                                                {"first_name":
                                                 new_stuff["f_name"]}})
            db.teachers.update(username_query, {'$set':
                                                {"last_name":
                                                 new_stuff["l_name"]}})
            UpdateSession_Form(session, request)
            flash("Profile updated")
            return redirect("/profile_teacher", 303)
        # if check answers returns True, the user has made a mistake
        # reroute to edit_info so user can fix answer(s)
        else:
            other_genders = ["Male", "Female", "Other"]
            other_genders.remove(new_stuff["gender"])
            return render_template("edit_info_teacher.html",
                                   user=new_stuff["username"],
                                   email=new_stuff["email"],
                                   f_name=new_stuff["f_name"],
                                   l_name=new_stuff["l_name"],
                                   c_user=new_stuff["c_user"],
                                   gender=new_stuff["gender"],
                                   other_genders=other_genders)


@app.route("/add_class", methods=["GET", "POST"])
def add_class():
    if request.method == "GET":
        full_name = retrieve_teacher_info(session)["full_name"]
        return render_template("add_class.html", full_name=full_name)
    else:
        for teacher in db.teachers.find():
            for item in teacher:
                if item == request.form.get("class_name"):
                    flash("Class Name is taken")
                    class_name = ""
                    class_code = request.form.get("class_code")
                    full_name = retrieve_teacher_info(session)["full_name"]
                    return render_template("add_class2.html",
                                           class_name=class_name,
                                           class_code=class_code,
                                           full_name=full_name)
                elif teacher[item] == request.form.get("class_code"):
                    flash("Class Code already taken")
                    class_name = request.form.get("class_name")
                    class_code = ""
                    full_name = retrieve_teacher_info(session)["full_name"]
                    return render_template("add_class2.html",
                                           class_name=class_name,
                                           class_code=class_code,
                                           full_name=full_name)
                else:
                    continue
        db.teachers.update({"username": session["username"]
                            }, {'$set': {request.form.get("class_name"):
                                         request.form.get("class_code")}})
        flash("Class created")
        return redirect("/my_classes", 303)


@app.route("/profile_teacher", methods=["GET", "POST"])
def profile_teacher():
    full_name = retrieve_teacher_info(session)["full_name"]
    username = retrieve_teacher_info(session)["username"]
    email = retrieve_teacher_info(session)["email"]
    gender = retrieve_teacher_info(session)["gender"]
    db.teachers.update({"username": session["username"]},
                       {"$set": {"last_accessed":
                                 arrow.utcnow().format('YYYY-MM-DD')}})
    return render_template("profile_teacher.html",
                           full_name=full_name, gender=gender,
                           email=email, username=username)


'''
@app.route("/make_a_list", methods=["GET", "POST"])
def make_a_list():
    if request.method == "GET":
        masterlist = []
        doc = db.masterlist.find()
        for word in doc:
            masterlist.append(word)
        full_name = retrieve_teacher_info(session)["full_name"]
        return render_template("make_a_list.html",
                               masterlist=masterlist,
                               full_name=full_name)
    else:
        full_name = retrieve_teacher_info(session)["full_name"]
        list_ids = request.form.getlist('word')
        list_name = request.form.get("list_name")
        db[retrieve_teacher_info(session)["username"]].insert({list_name: list_ids})
        words = []
        for word_id in list_ids:
            list_of_words = db.masterlist.find({"_id": ObjectId(word_id)})
            for word in list_of_words:
                for item in word:
                    if item == "word":
                        words.append(word[item])
                    else:
                        continue
        return render_template("list_confirmation.html",
                               words=words,
                               list_name=list_name)
'''

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    elif request.method == "POST":
        submitted_username = request.form.get("user").lower().strip()
        doc = db.users.find_one({"username": submitted_username})
        teacher_doc = db.teachers.find_one({"username": submitted_username})
        username = request.form.get("user").strip()
        # if the document does not exist in db, wrong username
        if doc is None and teacher_doc is None:
            flash("Wrong Username")
            return render_template("login2.html",
                                   user="",
                                   password=request.form.get("pass").lower())
        # if username exists and password matches up, redirect to choose list
        elif teacher_doc is None:
            if pbkdf2_sha512.verify(request.form.get("pass").strip(),
                                    doc["password"]):
                UpdateSession(session, username, doc)
                flash("Successful login")
                db.users.update({"username": session["username"]},
                                {"$set":
                                 {"last_accessed":
                                  arrow.utcnow().format('YYYY-MM-DD')}})
                return redirect("/setsession", 303)
            else:
                flash("Wrong password")
                return render_template("login2.html",
                                       user=request.form.get("user").lower(),
                                       password="")
        else:
            if pbkdf2_sha512.verify(request.form.get("pass").strip(),
                                    teacher_doc["password"]):
                UpdateSession(session, username, teacher_doc)
                session["user_type"] = "Teacher"
                db.teachers.update({"username": session["username"]},
                                   {"$set":
                                    {"last_accessed":
                                     arrow.utcnow().format('YYYY-MM-DD')}})
                flash("Successful login")
                return redirect("/", 303)
            else:
                flash("Wrong password")
                return render_template("login2.html",
                                       user=request.form.get("user").lower(),
                                       password="")


@app.route("/choose_user_type", methods=["GET", "POST"])
def choose_user_type():
    if request.method == "GET":
        return render_template("choose_user_type.html")
    else:
        if request.form["user_type"] == "Student":
            session["user_type"] = "Student"
            return redirect("/signup", 303)
        else:
            session["user_type"] = "Teacher"
            return redirect("/sign_up_teacher", 303)


@app.route("/sign_up_teacher", methods=["GET", "POST"])
def sign_up_teacher():
    if request.method == "GET":
        return render_template("sign_up_teacher.html")
    elif request.method == "POST":
        UpdateSession_Form(session, request)
        new_stuff = check_answers(request, flash, session, False)["new_stuff"]
        pass_word = pbkdf2_sha512.hash(request.form.get("pass").strip())
        c_pass = request.form.get("c_pass").strip()
        security_word = request.form.get("security_word").strip()
        # if check_answers is False, user has not made any mistakes
        # insert document in db
        if not check_answers(request, flash, session, True)["errors"]:
            db.teachers.insert_one({"username": new_stuff["username"],
                                    "password": pass_word,
                                    "security_word": request.form.get
                                    ("security_word").strip(),
                                    "email": new_stuff["email"],
                                    "first_name": new_stuff["f_name"],
                                    "last_name": new_stuff["l_name"],
                                    "gender": new_stuff["gender"],
                                    "last_accessed":
                                    arrow.utcnow().format('YYYY-MM-DD')
                                    })
            # update the session with newly created db
            UpdateSession_Form(session, request)
            session["user_type"] = "Teacher"
            flash("Profile created")
            return redirect("/", 303)
        # if password doesnt match up, as user to retype them
        elif (request.form.get("pass").strip() !=
              request.form.get("c_pass").strip()):
            flash("Please retype the password/confirmed password")
            pass_word = ""
            c_pass = ""
        other_genders = ["Male", "Female", "Other"]
        other_genders.remove(new_stuff["gender"])
        return render_template("sign_up_teacher2.html",
                               user=new_stuff["username"],
                               pass_word=pass_word,
                               email=new_stuff["email"],
                               security_word=security_word,
                               f_name=new_stuff["f_name"],
                               l_name=new_stuff["l_name"],
                               c_pass=c_pass,
                               c_user=new_stuff["c_user"],
                               gender=new_stuff["gender"],
                               other_genders=other_genders)


@app.route("/edit_info", methods=["GET", "POST"])
def edit_info():
    if request.method == "GET":
        # if just accessing page, fill in values with existing information
        other_genders = ["Male", "Female", "Other"]
        user_info = retrieve_user_info(session)
        other_genders.remove(user_info["gender"])
        return render_template("edit_info.html",
                               user=user_info["username"],
                               c_user=user_info["username"],
                               email=user_info["email"],
                               f_name=user_info["f_name"].split(" ")[0],
                               l_name=user_info["l_name"].split(" ")[0],
                               gender=user_info["gender"],
                               other_genders=other_genders)
    elif request.method == "POST":
        # check answers makes incorrect value(s) blank > user knows what to fix
        # new stuff is equal to a dict of all variables
        #     (whether variables are blank or equal to user responses)
        new_stuff = check_answers(request, flash, session, False)["new_stuff"]
        doc = {}
        for user in db.users.find():
            for item in user:
                doc[item] = user[item]
        if session["username"] != new_stuff["username"]:
            if session["username"] in doc.values():
                flash("Username taken")
                other_genders = ["Male", "Female", "Other"]
                other_genders.remove(new_stuff["gender"])
                return render_template("/edit_info.html",
                                       user="", c_user="",
                                       email=new_stuff["email"],
                                       f_name=new_stuff["f_name"],
                                       l_name=new_stuff["l_name"],
                                       gender=new_stuff["gender"],
                                       other_genders=other_genders)
        doc = {}
        for teacher in db.teachers.find():
            for item in teacher:
                doc[item] = teacher[item]
        if session["username"] != new_stuff["username"]:
            if session["username"] in doc.values():
                flash("Username taken")
                other_genders = ["Male", "Female", "Other"]
                other_genders.remove(new_stuff["gender"])
                return render_template("/edit_info.html",
                                       user="", c_user="",
                                       email=new_stuff["email"],
                                       f_name=new_stuff["f_name"],
                                       l_name=new_stuff["l_name"],
                                       gender=new_stuff["gender"],
                                       other_genders=other_genders)
        # if check_answers[errors] is false, no user has not made any errors
        if not check_answers(request, flash, session, True)["errors"]:
            # username_query is the query for the first part of db.update
            username_query = {"username": session["username"]}
            # things to update is the list of things to update (for loop)
            things_to_update = ["email", "gender"]
            for i in things_to_update:
                db.users.update(username_query, {'$set':
                                                 {i: new_stuff[i]}})
            # first/last/user names have different variable/db names
            #         >> they are outside of loop
            db.users.update(username_query, {'$set':
                                             {"username":
                                              new_stuff["username"]}})
            db.users.update(username_query, {'$set':
                                             {"first_name":
                                              new_stuff["f_name"]}})
            db.users.update(username_query, {'$set':
                                             {"last_name":
                                              new_stuff["l_name"]}})
            UpdateSession_Form(session, request)
            flash("Profile updated")
            return redirect("/profile", 303)
        # if check answers returns True, the user has made a mistake
        # reroute to edit_info so user can fix answer(s)
        else:
            other_genders = ["Male", "Female", "Other"]
            other_genders.remove(new_stuff["gender"])
            return render_template("edit_info.html",
                                   user=new_stuff["user"],
                                   email=new_stuff["email"],
                                   f_name=new_stuff["f_name"],
                                   l_name=new_stuff["l_name"],
                                   c_user=new_stuff["c_user"],
                                   gender=new_stuff["gender"],
                                   other_genders=other_genders)


@app.route("/security", methods=["GET", "POST"])
def security():
    if request.method == "GET":
        return render_template("wrong_password.html")
    elif request.method == "POST":
        # let session["username"] and security_word equal to user responses
        session["username"] = request.form.get("user").strip()
        security_word = request.form.get("security_word").strip()
        doc = db.users.find_one({"username": session["username"]})
        if doc is None:
            doc = db.teachers.find_one({"username": session["username"]})
        # if there is no document with given username, wrong username entered
        if doc is None:
            flash("Wrong Username")
            return render_template("wrong_password.html")
        # if doc exists + security word matches up, redirect user to reset pass
        elif doc["security_word"].lower() == security_word.lower().strip():
            return redirect("/reset_password", 303)
        # doc exists but security word is wrong > security word is incorrect
        else:
            flash("Security word is incorrect. Try again")
            return render_template("wrong_password.html")


@app.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    username = session["username"]
    if request.method == "GET":
        return render_template("reset_password.html")
    elif request.method == "POST":
        # if confirmed password ≠ password, ask user to retype them
        if (request.form.get("pass").strip() !=
           request.form.get("c_pass").strip()):
            flash("Re-Type Password or Password Confirmation")
            return render_template("reset_password.html")
        # else, update database with new password
        else:
            db.users.update({"username": username},
                            {"$set": {"password":
                             pbkdf2_sha512.hash
                             (request.form.get("pass").strip())}})
            flash("Password reset")
            return redirect("/")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("sign_up.html")
    elif request.method == "POST":
        UpdateSession_Form(session, request)
        new_stuff = check_answers(request, flash, session, False)["new_stuff"]
        pass_word = pbkdf2_sha512.hash(request.form.get("pass").strip())
        c_pass = request.form.get("c_pass").strip()
        security_word = request.form.get("security_word").strip()
        # if check_answers is False, user has not made any mistakes
        # insert document in db
        if not check_answers(request, flash, session, True)["errors"]:
            db.users.insert_one({"username": new_stuff["username"],
                                 "password": pass_word,
                                 "security_word": request.form.get
                                 ("security_word").strip(),
                                 "email": new_stuff["email"],
                                 "first_name": new_stuff["f_name"],
                                 "last_name": new_stuff["l_name"],
                                 "gender": new_stuff["gender"],
                                 "list_of_words": [],
                                 "list_of_definitions": [],
                                 "class_name": None,
                                 "class_code": None,
                                 "teacher_username": None,
                                 "last_accessed":
                                 arrow.utcnow().format('YYYY-MM-DD')
                                 })
            # update the session with newly created db
            UpdateSession_Form(session, request)
            flash("Profile created")
            return redirect("/setsession", 303)
        # if password doesnt match up, as user to retype them
        elif (request.form.get("pass").strip() !=
              request.form.get("c_pass").strip()):
            flash("Please retype the password/confirmed password")
            pass_word = ""
            c_pass = ""
        other_genders = ["Male", "Female", "Other"]
        other_genders.remove(new_stuff["gender"])
        return render_template("sign_up2.html",
                               user=new_stuff["username"],
                               pass_word=pass_word,
                               email=new_stuff["email"],
                               security_word=security_word,
                               f_name=new_stuff["f_name"],
                               l_name=new_stuff["l_name"],
                               c_pass=c_pass,
                               c_user=new_stuff["c_user"],
                               gender=new_stuff["gender"],
                               other_genders=other_genders)


@app.route("/logged_out", methods=["GET", "POST"])
def logged_out():
    if request.method == "GET":
        return render_template("logoutconfirmation.html")
    else:
        if request.form.get("yesorno") == "Yes":
            reset_sessions(session)
            return render_template("logged_out.html")
        else:
            return redirect("/profile", 303)


@app.route("/design", methods=["GET"])
def design():
    return render_template("design.html")


@app.route("/profile", methods=["GET"])
def profile():
    doc = retrieve_user_info(session)["doc"]
    user_info = retrieve_user_info(session)
    db.users.update({"username": session["username"]},
                    {"$set":
                     {"last_accessed": arrow.utcnow().format('YYYY-MM-DD')}})
    # for each query in the document, if it is a list, add it to stats
    stats = {}
    for item in doc:
        name_of_item = list(str(item))
        if name_of_item[0:4] == list("list"):
            try:
                int(name_of_item[4])
                stats[item] = doc[item]
            except (IndexError, ValueError):
                continue
    class_code = doc["class_code"]
    class_name = doc["class_name"]
    if class_code is None:
        teacher_name = None
    else:
        for teacher_mongodoc in db.teachers.find():
            for item in teacher_mongodoc:
                if item == class_name and teacher_mongodoc[item] == class_code:
                    teacher_fname = teacher_mongodoc["first_name"]
                    teacher_lname = teacher_mongodoc["last_name"]
                else:
                    continue
        teacher_name = '{} {}'.format(teacher_fname.split(" ")[0],
                                      teacher_lname)
    # for each list in stats:
    #   calculate num_questions, percent_accuracy, percent_inaccuracy
    #   get the correct_words and incorrect_words (minus repeats)
    #   set equal to progress[list_numbxer]
    if len(stats) == 0:
        session["od"] = {}
    else:
        make_progress_report(session, stats, collections)
    if len(doc["list_of_words"]) < 1:
        template = "profile_2.html"
    else:
        template = "profile.html"
    return render_template(template,
                           email=user_info["email"],
                           username=user_info["username"],
                           full_name=user_info["full_name"],
                           gender=user_info["gender"],
                           od=session["od"], class_code=class_code,
                           class_name=class_name, teacher_name=teacher_name)


@app.route("/enroll_in_class", methods=["GET", "POST"])
def enroll_in_class():
    if request.method == "GET":
        db.users.update({"username": session["username"]},
                        {"$set": {"last_accessed":
                                  arrow.utcnow().format('YYYY-MM-DD')}})
        full_name = retrieve_user_info(session)["full_name"]
        return render_template("enroll_in_class.html", full_name=full_name)
    else:
        class_code = request.form.get("class_code")
        for teacher in db.teachers.find():
            for attribute in teacher:
                if teacher[attribute] == class_code:
                    flash("You have enrolled in '"+attribute+"'")
                    db.users.update({"username": session["username"]},
                                    {'$set': {"class_code": class_code}})
                    db.users.update({"username": session["username"]},
                                    {'$set': {"class_name": attribute}})
                    db.users.update({"username": session["username"]},
                                    {'$set': {"teacher_username": teacher["username"]}})
                    return redirect("/profile", 303)
                else:
                    continue
        flash("Class Doesn't Exist. Please Try Again")
        return redirect("/enroll_in_class", 303)


@app.route("/MyProgressReport", methods=["GET"])
def print_from_profile():
    full_name = retrieve_user_info(session)["full_name"]
    # FIX THIS IN FUTURE. DONT AUTOMATICALLY SET EASTERN STANDARD TIME
    current_time = arrow.utcnow().to("US/Eastern")
    current_time = current_time.format('MM/DD/YYYY; h:mm A')
    return render_template("print_from_profile.html", od=session["od"],
                           full_name=full_name, current_time=current_time)


if __name__ == "__main__":
    app.config['PROPAGATE_EXCEPTIONS'] = True
    app.run()
