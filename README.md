#README.md
##Notes for the Gurmukhi Quiz App

Project Description:
This project was created for teachers in Sikh Khalsa Schools around the country who struggle to find tools that support the Gurmukhi dialect. This quiz app should help students learn and practice some of the most common words in Gurbani. 

In order to run the code:
	•	clone the repo
	•	create and activate a virtual environment that uses python3
        ⁃   virtualenv -p python3 virtualenv_name
	•	install the required packages from requirements.txt using ‘pip install’
        ⁃	pip install -r requirements.txt
	•	open a mongo instance in one tab (mongod) and import the example data (the .csv files) in another tab
        ⁃	mongoimport --db words --collection NAME --type csv --headerline --file FILEPATH_TO_.csv
        ⁃	python app.py
	•	go to the following address in your browser
        ⁃	 http://127.0.0.1:500/ 


----------


> Written with [StackEdit](https://stackedit.io/).
