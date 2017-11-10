# helper.py
from mongo_interface import make_database
import random
db = make_database()


def CalculatePercentAccuracy(full_doc, name):
    right = full_doc[name]["correct"]
    wrong = full_doc[name]["wrong"]
    if right+wrong == 0:
        percent_accuracy = 0
        percent_inaccuracy = 0
    else:
        percent_accuracy = int((right/(right+wrong))*100)
        percent_inaccuracy = 100 - percent_accuracy
    return [percent_accuracy, percent_inaccuracy]


def CheckAnswers(request, flash, session, need_to_flash):
    errors = False
    stuff = {"username": request.form.get("user").split(" ")[0],
             "email": request.form.get("email").split(" ")[0],
             "c_user": request.form.get("c_user").split(" ")[0],
             "gender": request.form.get("gender").title(),
             "f_name": request.form.get("f_name").split(" ")[0],
             "l_name": request.form.get("l_name").split(" ")[0]}
    if request.form.get("user").strip() != request.form.get("c_user").strip():
        if need_to_flash:
            flash("Please ensure that username is validated correctly.")
        stuff["username"] = ""
        stuff["c_user"] = ""
        errors = True
    elif ((stuff["username"] != session["username"]) and
          db.users.find_one({"username": stuff["username"]}) is not None):
        if need_to_flash:
            flash("Username already taken")
        stuff["username"] = ""
        stuff["c_user"] = ""
        errors = True
    elif "@" not in list(request.form.get("email").strip()):
        if need_to_flash:
            flash("Please enter a valid email")
        stuff["email"] = ""
        errors = True
    elif "." not in request.form.get("email").strip().split("@")[1]:
        if need_to_flash:
            flash("Please enter a valid email")
        stuff["email"] = ""
        errors = True
    elif request.form.get("gender") is None:
        if need_to_flash:
            flash("Please select gender")
        errors = True
    return {"errors": errors, "new_stuff": stuff}


def CheckIfUserChoseList(session, arrow):
    if len(RetrieveUserInfo(session)["doc"]["list_of_words"]) > 0:
            template = "homepage_2.html"
    else:
        template = "homepage_3.html"
    full_name = RetrieveUserInfo(session)["full_name"]
    db.users.update({"username": session["username"]},
                    {"$set": {"last_accessed":
                              arrow.utcnow().format('YYYY-MM-DD')}})
    return {"full_name": full_name, "template": template}


def CreateListsFromDb(user_info, session, ObjectId):
    teacher = user_info["teacher"]
    teacher_docs = db[teacher].find()
    list_name = session["current_list"]
    list_ids = []
    for doc in teacher_docs:
        for item in doc:
            if item == "_id":
                continue
            elif item == list_name:
                for ids in doc[item]:
                    list_ids.append(ids)
            else:
                continue
    list_of_words = []
    list_of_definitions = []
    study = []
    for word_id in list_ids:
        word_doc = db.masterlist.find_one({"_id": ObjectId(word_id)})
        study.append(word_doc)
        list_of_words.append(word_doc["word"])
        list_of_definitions.append(word_doc["definition"])
    return({"list_of_words": tuple(list_of_words),
            "list_of_definitions": tuple(list_of_definitions),
            "study": study})


def CreateMongoList(session, name):
    db.users.update({"username": session["username"]},
                    {"$set": {name: {"correct": 0, "wrong": 0,
                                     "correct_words": [],
                                     "wrong_words": []}}})


def GetTeacherListNames(username):
    teacher_lists = []
    for item in db[username].find():
        for listname in item:
            if listname == "_id":
                continue
            else:
                teacher_lists.append(item)
    return teacher_lists


def LessThanFour(name, user_info, session, ObjectId,
                 list_of_words, list_of_definitions):
    list2 = []
    list_of_ops = []
    list_of_options = []
    list_of_defs = CreateListsFromDb(user_info,
                                     session,
                                     ObjectId)["list_of_definitions"]
    for item in list_of_defs:
        if item not in list_of_definitions:
            list2.append(item)
    not_nothing = True
    while not_nothing:
        word_index = random.randint(0, (len(list_of_words)-1))
        correct_word = list_of_words[word_index]
        if correct_word != "Nothing":
            not_nothing = False
    correct_def = list_of_definitions[word_index]
    for i in range(0, 3):
        wrong_index = random.randint(0, (len(list2)-1))
        list_of_ops.append(list2[wrong_index])
    list_of_ops.append(correct_def)
    random.shuffle(list_of_ops)
    list_of_options = tuple(list_of_ops)
    list_of_words.append("Nothing")
    return {"list_of_words": list_of_words,
            "list_of_definitions": list_of_definitions,
            "list_of_options": list_of_options,
            "correct_word": correct_word,
            "correct_def": correct_def, "word_index": word_index}


def MakeOptions(list_of_words, list_of_definitions, correct_def):
    not_the_same = False
    while not not_the_same:
        wrong_one = random.choice(list_of_definitions)
        if correct_def != wrong_one:
            not_the_same = True
        else:
            continue
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
    list_of_ops = [correct_def,
                   wrong_one, wrong_two, wrong_three]
    random.shuffle(list_of_ops)
    list_of_options = tuple(list_of_ops)
    return list_of_options


def MakeProgressReport(session, stats):
    progress = {}
    for lis in stats:
        num_questions = (stats[lis]["correct"]+stats[lis]["wrong"])
        if num_questions == 0:
            session["progress_report"] = {}
        else:
            percent_accuracy = int((stats[lis]["correct"] / num_questions)*100)
            percent_inaccuracy = 100 - percent_accuracy
            correct_words = stats[lis]["correct_words"]
            wrong_words = stats[lis]["wrong_words"]
            correct_words = tuple(correct_words)
            wrong_words = tuple(wrong_words)
            progress[lis] = {"percent_accuracy": percent_accuracy,
                             "percent_inaccuracy": percent_inaccuracy,
                             "total_questions": num_questions,
                             "correct_words": correct_words,
                             "wrong_words": wrong_words}
            # od is the numerically ordered version of progress
            session["progress_report"] = progress


def ResetSession(session):
    session["username"] = None
    session["email"] = None
    session["first_name"] = None
    session["last_name"] = None
    session["progress_report"] = None
    session["user_type"] = None


def RetrieveTeacherInfo(session):
    username = session["username"]
    doc = db.teachers.find_one({"username": username})
    email = doc["email"]
    f_name = doc["first_name"].title()
    l_name = doc["last_name"].title()
    gender = session["gender"].title()
    full_name = '{} {}'.format(f_name.split(" ")[0], l_name)
    return {"username": username, "doc": doc, "full_name": full_name,
            "gender": gender, "email": email, "f_name": f_name,
            "l_name": l_name}


def RetrieveUserInfo(session):
    username = session["username"]
    doc = db.users.find_one({"username": username})
    email = doc["email"]
    f_name = doc["first_name"].title()
    l_name = doc["last_name"].title()
    gender = session["gender"].title()
    teacher = doc["teacher"]
    full_name = '{} {}'.format(f_name.split(" ")[0], l_name)
    return {"username": username, "doc": doc, "full_name": full_name,
            "gender": gender, "email": email, "f_name": f_name,
            "l_name": l_name, "teacher": teacher}


def UpdateCorrect(correct_word, teachername, listname, username, word_index):
    list_doc = db.users.find_one({"username": username})[listname]
    list_doc["correct"] += 1
    list_doc["correct_words"].append(correct_word)
    db.users.update({"username": username},
                    {"$set": {listname: list_doc}})
    full_doc = db.masterlist.find_one({"word": correct_word})
    quote_ggs = full_doc["quote_ggs"]
    list_of_words = db.users.find_one({"username": username})["list_of_words"]
    list_of_words.pop(word_index)
    list_of_definitions = db.users.find_one(
                                            {"username": username}
                                           )["list_of_definitions"]
    list_of_definitions.pop(word_index)
    db.users.update({"username": username},
                    {"$set": {"list_of_words": list_of_words}})
    db.users.update({"username": username},
                    {"$set": {"list_of_definitions": list_of_definitions}})
    correct_translit = full_doc["transliteration"]
    return {"quote_ggs": quote_ggs, "correct_translit": correct_translit}


def UpdateSession(session, username, doc):
    session["username"] = username
    gender = doc["gender"]
    session["gender"] = gender
    email = doc["email"]
    session["first_name"] = doc["first_name"]
    session["last_name"] = doc["last_name"]
    session["email"] = email


def UpdateSession_Form(session, request):
    session["username"] = request.form.get("user").strip()
    session["email"] = request.form.get("email").strip()
    session["first_name"] = request.form.get("f_name").strip()
    session["last_name"] = request.form.get("l_name").strip()
    session["gender"] = request.form.get("gender")


def UpdateTeacherLastAccessed(session, arrow):
    db.teachers.update({"username": session["username"]},
                       {"$set": {"last_accessed":
                                 arrow.utcnow().format('YYYY-MM-DD')}})


def UpdateUserLastAccessed(session, arrow):
    db.users.update({"username": session["username"]},
                    {"$set": {"last_accessed":
                              arrow.utcnow().format('YYYY-MM-DD')}})


def UpdateWrong(correct_word, teachername, listname, username, word_index):
    list_doc = db.users.find_one({"username": username})[listname]
    list_doc["wrong"] += 1
    list_doc["wrong_words"].append(correct_word)
    db.users.update({"username": username},
                    {"$set": {listname: list_doc}})
    full_doc = db.masterlist.find_one({"word": correct_word})
    quote_ggs = full_doc["quote_ggs"]
    correct_translit = full_doc["transliteration"]
    return {"quote_ggs": quote_ggs, "correct_translit": correct_translit}
