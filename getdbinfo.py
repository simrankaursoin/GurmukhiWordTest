#getdbinfo.py
# (this gets info from the db)

from mongo_interface import make_database

db = make_database()
number_teachers = 0
teacher_info = []

for teacher in db.teachers.find():
    number_teachers += 1
    teacher_info.append({teacher["username"]: teacher["last_accessed"]})

print("Number of teachers currently in the db:", number_teachers)
print("Here are a list of the times teachers last accessed the website: ")
for item in teacher_info:
    print(item)

number_users = 0
user_info = []

for user in db.users.find():
    number_users += 1
    user_info.append({user["username"]: user["last_accessed"]})

print("Number of users currently in the db:", number_users)
print("Here are a list of the times users last accessed the website: ")
for item in user_info:
    print(item)
