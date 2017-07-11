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

app = Flask(__name__)
app.secret_key = secure.APP_SECRET_KEY

#function to make the list_of_words and list_of_definitions based on the session["current_list"]
def make_lists(list_of_words, list_of_definitions):
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
        return redirect("/quiz", 303)
        
@app.route("/quiz", methods=["GET"])
def quiz():
    #user is directed here to actually be asked questions
    global correct_definition, list_of_words, list_of_definitions, correct_word, wrong_one, wrong_two, wrong_three, word_index
    #there are 2 possible scenarios for why there is a GET request being made on this app route
    #scenario one is that the user has already answered the question and needs to get feedback
    #scenario two is that the user is accessing the page for the first time
    # 
    #if the user response == correct_definition, user got the question right
    #this word can now be removed, so the user is not asked it again
    #directs the user to a page saying "CORRECT
    if request.form.get("options") == correct_definition:
        list_of_words.pop(word_index)
        list_of_definitions.pop(word_index)
        return "CORRECT"        
    # 
    #if there is no user response, the user is simply accessing the page 
    elif request.form.get("options") == None:
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
        #this means that the user HAS responded to a question (is not just accessing the page) and is NOT correct. 
        #this means the user is incorrect
        #directs user to a page that simply says "NOPE"
        return "NOPE"      
        
           
                 
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