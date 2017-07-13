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
name_of_collection =''
app = Flask(__name__)
app.secret_key = secure.APP_SECRET_KEY

#function to make the list_of_words and list_of_definitions based on the session["current_list"]
def make_lists(list_of_words, list_of_definitions):
    global name_of_collection
    #name_of_collection is a variable based on the session[current_list]
    name_of_collection = str(session["current_list"]).lower()
    for item in db[name_of_collection].find():
        list_of_words.append(item["word"])
        list_of_definitions.append(item["definition"])     
    return list_of_words, list_of_definitions 

          
@app.route("/",methods=["GET"])
def main():
    if request.method == "GET":
        #initially directs user to the homepage which asks the user what they would like to do (quiz, etc). Redirects accordingly
        return render_template("homepage.html" )     
 
@app.route("/setsession", methods=["GET", "POST"])
def set_session():
    global list_of_words, list_of_definitions
    if request.method =="GET":
        #directs user to a page to set the session["current_list"]
        return render_template("set_session.html")
    else:
        #POST request for when user clicks "submit"
        #set_session page has a dropdown menu in which the user selects what list he/she would like to cover
        #the session["current_list"] is set accordingly
        session["current_list"] = request.form.get("current_list")
        list_of_words = []
        list_of_definitions = []
        make_lists(list_of_words, list_of_definitions)
        #makes list_of_words and list_of_definitions according to the list the user has selected
        #these lists allow for easier access and editing based on user progress
        return redirect(url_for("quiz"), 303)
        
@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    global correct_definition, name_of_collection, list_of_words, list_of_definitions, correct_word, wrong_one, wrong_two, wrong_three, word_index
    if request.method == "GET":
        #a word_index is generated to make the word choice random but also ensure that it corresponds to the same item in list_of_words and list_of_definitions
        word_index= random.randint(0, len(list_of_words)-1)
        #the correct_word is set
        correct_word= list_of_words[word_index]
        #the correct_definiton is set
        correct_definition= list_of_definitions[word_index]
        # a variable called not_the_same is created
        #a loop is made based on this variable to ensure that wrong_one (one of the incorrect responses) is not the same as correct_definition
        not_the_same = False
        while not not_the_same:
            wrong_one = random.choice(list_of_definitions)
            if correct_definition != wrong_one:
                not_the_same = True
            else:
                continue
        #this loop also ensures that wrong_two is not the same as wrong_one or correct_definition
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
        #another loop also ensures that wrong_three is not the same as wrong_two or wrong_one
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
        #list_of_options is created and shuffled to ensure that the responses are presented to the user in a random order
        list_of_options = [correct_definition, wrong_one, wrong_two, wrong_three]
        random.shuffle(list_of_options)
        return render_template("question.html", correct_word = correct_word, list_of_options = list_of_options)
    else: 
        if request.form.get("options") == correct_definition:
            print(request.form.get("options"))
            print(correct_definition)
            list_of_words.pop(word_index)
            list_of_definitions.pop(word_index)
            full_document = db[name_of_collection].find_one({"word":correct_word})
            quote_ggs= full_document["quote_ggs"]
            correct_transliteration= full_document["transliteration"]
            return render_template("correct.html", correct_word=correct_word, correct_definition = correct_definition, quote_ggs=quote_ggs, correct_transliteration = correct_transliteration)
        elif request.form.get("options") == None:
            flash("Please submit a response")
            list_of_options = [correct_definition, wrong_one, wrong_two, wrong_three]
            return render_template("question.html", correct_word = correct_word, list_of_options = list_of_options)
        else:
            print(request.form.get("options"))
            print(correct_definition)
            full_document = db[name_of_collection].find_one({"word":correct_word})
            quote_ggs= full_document["quote_ggs"]
            correct_transliteration= full_document["transliteration"]
            return render_template("incorrect.html", correct_word=correct_word, correct_definition = correct_definition, quote_ggs=quote_ggs, correct_transliteration = correct_transliteration)

          
                 
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