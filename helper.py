# helper.py
from mongo_interface import make_database
import random
db = make_database()


def make_lists(session, name_of_collection):
    # name_of_collection is a variable based on the session[current_list]
    # corresponds to the name of the collection in the mongo db
    list_of_words = []
    list_of_definitions = []
    for item in db[name_of_collection].find():
        list_of_words.append(item["word"])
        list_of_definitions.append(item["definition"])
    # create a list called list_of_words based on db words from list
    # create a list called list_of_definitions based on db defs from list
    # allows appending/deleting/easy-access (unlike the db)
    db.users.update({"username": session["username"]},
                    {'$set': {"list_of_words": list_of_words}})
    db.users.update({"username": session["username"]},
                    {'$set': {"list_of_definitions": list_of_definitions}})


def CreateMongoList(session, name):
    db.users.update({"username": session["username"]},
                    {"$set": {name: {"correct": 0, "wrong": 0,
                                     "correct_words": [],
                                     "wrong_words": []}}})


def UpdateSession_Form(session, request):
    session["username"] = request.form.get("user").strip()
    session["email"] = request.form.get("email").strip()
    session["first_name"] = request.form.get("f_name").strip()
    session["last_name"] = request.form.get("l_name").strip()
    session["gender"] = request.form.get("gender")


def less_than_four(name, list_of_words, list_of_definitions, list_of_options):
    list2 = []
    list_of_ops = []
    for item in db[name].find():
        if item["definition"] not in list_of_definitions:
            list2.append(item["definition"])
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
    list_of_options.append(correct_def)
    random.shuffle(list_of_ops)
    list_of_options = tuple(list_of_ops)
    list_of_words.append("Nothing")
    return {"list_of_words": list_of_words,
            "list_of_definitions": list_of_definitions,
            "list_of_options": list_of_options, "correct_word": correct_word,
            "correct_def": correct_def, "word_index": word_index}


def UpdateCorrect(correct_word, name, username, word_index):
    list_doc = db.users.find_one({"username": username})[name]
    list_doc["correct"] += 1
    list_doc["correct_words"].append(correct_word)
    db.users.update({"username": username},
                    {"$set": {name: list_doc}})
    full_doc = db[name].find_one({"word": correct_word})
    quote_ggs = full_doc["quote_ggs"].split()
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


def UpdateWrong(correct_word, name, username, word_index, session):
    list_doc = db.users.find_one({"username": username})[name]
    list_doc["wrong"] += 1
    list_doc["wrong_words"].append(correct_word)
    db.users.update({"username": username},
                    {"$set": {name: list_doc}})
    full_doc = db[name].find_one({"word": correct_word})
    quote_ggs = full_doc["quote_ggs"].split()
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


def retrieve_user_info(session):
    username = session["username"]
    doc = db.users.find_one({"username": username})
    email = doc["email"]
    f_name = doc["first_name"].title()
    l_name = doc["last_name"].title()
    gender = session["gender"].title()
    full_name = '{} {}'.format(f_name.split(" ")[0], l_name)
    return {"username": username, "doc": doc, "full_name": full_name,
            "gender": gender, "email": email, "f_name": f_name,
            "l_name": l_name}


def retrieve_teacher_info(session):
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

def check_if_user_chose_list(session, arrow):
    if len(retrieve_user_info(session)["doc"]["list_of_words"]) > 0:
            template = "homepage_2.html"
    else:
        template = "homepage_3.html"
    full_name = retrieve_user_info(session)["full_name"]
    db.users.update({"username": session["username"]},
                    {"$set": {"last_accessed":
                                arrow.utcnow().format('YYYY-MM-DD')}})
    return {"full_name": full_name, "template": template}


def make_progress_report(session, stats, collections):
    progress = {}
    for lis in stats:
        num_questions = (stats[lis]["correct"]+stats[lis]["wrong"])
        if num_questions == 0:
            session["od"] = {}
        else:
            percent_accuracy = int((stats[lis]["correct"] / num_questions)*100)
            percent_inaccuracy = 100 - percent_accuracy
            correct_words = list(set(stats[lis]["correct_words"]))
            wrong_words = list(set(stats[lis]["wrong_words"]))
            progress[list(lis)[-1]] = {"percent_accuracy": percent_accuracy,
                                       "percent_inaccuracy":
                                           percent_inaccuracy,
                                       "total_questions": num_questions,
                                       "correct_words": correct_words,
                                       "wrong_words": wrong_words}
            # od is the numerically ordered version of progress
            session["od"] = collections.OrderedDict(sorted(progress.items()))


def reset_sessions(session):
    session["username"] = None
    session["email"] = None
    session["first_name"] = None
    session["last_name"] = None
    session["od"] = None
    session["user_type"] = None


def check_answers(request, flash, session, need_to_flash):
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


def calculate_percent_accuracy(full_doc, name):
    right = full_doc[name]["correct"]
    wrong = full_doc[name]["wrong"]
    if right+wrong == 0:
        percent_accuracy = 0
        percent_inaccuracy = 0
    else:
        percent_accuracy = int((right/(right+wrong))*100)
        percent_inaccuracy = 100 - percent_accuracy
    return [percent_accuracy, percent_inaccuracy]


def make_options(list_of_words, list_of_definitions, correct_def):
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
