# helper.py
from mongo_interface import make_database
import random
db = make_database()


def make_lists(list_of_words, list_of_definitions, name_of_collection):
    # name_of_collection is a variable based on the session[current_list]
    # corresponds to the name of the collection in the mongo db
    for item in db[name_of_collection].find():
        list_of_words.append(item["word"])
        list_of_definitions.append(item["definition"])
    # create a list called list_of_words based on db words from list
    # create a list called list_of_definitions based on db defs from list
    # allows appending/deleting/easy-access (unlike the db)
    return list_of_words, list_of_definitions


def update_session_from_form(session, request):
    session["username"] = request.form.get("user").strip()
    session["email"] = request.form.get("email").strip()
    session["first_name"] = request.form.get("f_name").strip()
    session["last_name"] = request.form.get("l_name").strip()
    session["gender"] = request.form.get("gender")


def get_stuff_from_form(request, session):
    user = request.form.get("user").strip()
    c_user = request.form.get("c_user").strip()
    f_name = request.form.get("f_name")
    l_name = request.form.get("l_name")
    email = request.form.get("email")
    username = session["username"]
    return {"user": user, "username": username,
            "email": email, "f_name": f_name,
            "l_name": l_name, "c_user": c_user}


def update_session(session, username, doc):
    session["username"] = username
    gender = doc["gender"]
    session["gender"] = gender
    email = doc["email"]
    session["email"] = email


def get_form(request, x):
    return request.form.get(x).strip()


def retrieve_user_info(session):
    username = session["username"]
    doc = db.users.find_one({"username": username})
    email = doc["email"]
    f_name = session["first_name"].title()
    l_name = session["last_name"].title()
    gender = session["gender"].title()
    full_name = '{} {}'.format(f_name, l_name)
    return {"username": username, "doc": doc, "full_name": full_name,
            "gender": gender, "email": email, "f_name": f_name,
            "l_name": l_name}


def reset_sessions(session, user_doc):
    session["username"] = None
    session["email"] = None
    session["first_name"] = None
    session["last_name"] = None
    user_doc = {}
    return user_doc


def check_answers(request, flash, username, user):
    print(request.form.get("gender"))
    errors = False
    if request.form.get("user").strip() != request.form.get("c_user").strip():
        flash("Please ensure that username is validated correctly.")
        user = ""
        c_user = ""
        errors = True
    elif db.users.find_one({"username":
                            user}) is not None and user != username:
        flash("Username already taken")
        user = ""
        c_user = ""
        errors = True
        return c_user
    elif "@" not in list(request.form.get("email").strip()):
        flash("Please enter a valid email")
        email = ""
        errors = True
        return email
    elif len(request.form.get("f_name").split()) > 1:
        flash("Please enter a valid first name (one word)")
        f_name = ""
        errors = True
        return f_name
    elif len(request.form.get("l_name").split()) > 1:
        flash("Please enter a valid last name (one word)")
        l_name = ""
        errors = True
        return l_name
    elif request.form.get("gender") is None:
        print("NOPE")
        flash("Please select gender")
        errors = True
    if errors is True:
        return True
    else:
        return False


def calculate_percent_accuracy(full_doc, name):
    right = full_doc[name]["correct"]
    wrong = full_doc[name]["wrong"]
    percent_accuracy = int((right/(right+wrong))*100)
    return percent_accuracy


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
    list_of_options = [correct_def,
                       wrong_one, wrong_two, wrong_three]
    random.shuffle(list_of_options)
    return list_of_options
