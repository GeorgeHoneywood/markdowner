import os
import markdown

from flask import escape

from pymongo import MongoClient

client = MongoClient(os.environ["MONGODB_URI"])
db = client["heroku_n4snplp7"]
pastes = db.pastes
users = db.users

def addLengths():
    user_pastes = pastes.find({})

    for paste in user_pastes:
        if not paste.get("length"):
            pastes.update_one(paste, { "$set": { "length": len(paste["markdown"]) } } )

def regenMarkdown():
    user_pastes = pastes.find({})

    for paste in user_pastes:
        if paste.get("markdown"):
            pastes.update_one(paste, { "$set": { "html": markdown.markdown(escape(paste["markdown"]), extensions=['mdx_truly_sane_lists', 'pymdownx.superfences', 'extra']) } })
 
if __name__ == "__main__":
    print("1 to add lengths:")
    print("2 to regenerate html:")
    choice = int(input())

    if choice == 1:
        addLengths()
    elif choice == 2:
        regenMarkdown()