#app.py

from mongo_interface import db, list1
from flask import flash, request, Flask, render_template

app = Flask(__name__)

@app.route("/",methods=["GET","POST"])
def main():
    if request.method == "GET":
        return render_template("homepage.html", list1=list1,  db=db)
    
if __name__ == "__main__":
    #turn off this debugging stuff before production
    app.config['PROPAGATE_EXCEPTIONS'] = True
    app.config['DEBUG'] = True
    # next line: cause KeyErrors to bubble up to top level 
	#so we can see the traceback & debugger 
    app.config['TRAP_BAD_REQUEST_ERRORS'] = True
    app.run()