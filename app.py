#app.py

from mongo_interface import db, list1
from flask import flash, request, Flask, render_template
from multiple_choice import all_words, option1, word

app = Flask(__name__)

@app.route("/",methods=["GET","POST"])
def main():
    if request.method == "GET":
        #to ask the question
        return render_template("homepage.html", all_words=all_words, word=word, option1=option1)
    if request.method == "POST":
        #to submit the answer
        return render_template("correct_or_not.html", all_words=all_words, word=word, option1=option1)
    
if __name__ == "__main__":
    #turn off this debugging stuff before production
    app.config['PROPAGATE_EXCEPTIONS'] = True
    app.config['DEBUG'] = True
    # next line: cause KeyErrors to bubble up to top level 
	#so we can see the traceback & debugger 
    app.config['TRAP_BAD_REQUEST_ERRORS'] = True
    app.run()