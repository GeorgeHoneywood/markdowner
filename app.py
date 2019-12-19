from flask import Flask, session, request, url_for, render_template, redirect, abort, escape, flash
from flask_cors import CORS
from flask_api import status
from flask_session import Session

#from werkzeug.security import generate_password_hash, check_password_hash
#from werkzeug.middleware.proxy_fix import ProxyFix

from pymongo import MongoClient
from datetime import datetime
from random import choice

import json
import requests
import string
import markdown
import os

app = Flask(__name__)
app.app_context().push()
CORS(app)

#app.secret_key = os.environ["SECRET_KEY"].encode("utf-8")
#app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

response = {}

client = MongoClient(os.environ["MONGODB_URI"])
db = client["heroku_n4snplp7"]
pastes = db.pastes
users = db.users

# SESSION_TYPE = "mongodb"
# SESSION_MONGODB = client
# app.config.from_object(__name__)
# Session(app)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", upload=url_for("upload"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html"), status.HTTP_200_OK
    else:
        user = users.find_one({"username": request.form['username']})
        if not user:
            error = "user doesn't exist"
            return redirect(url_for("login", error = error))
        else:
            if check_password_hash(escape(request.form['password']).encode("utf-8") + user["salt"]):
                print("yes")
            else:
                print("nop")

@app.route("/signup", methods=["POST"])
def signup():
    if users.find_one({"username": request.form['username']}):
        error = "user already exists"
        return redirect(url_for("login", error = error))
    else:
        message = "user '{}' created".format(request.form['username'])
        salt = os.urandom(16)

        users.insert_one({ 
                            "username": request.form['username'],
                            "password": generate_password_hash(escape(request.form['password']).encode("utf-8") + salt),
                            "salt": salt,
                            "timestamp": datetime.now(),
                            "ip": request.remote_addr
                          })
        return redirect(url_for("login", message = message))

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        return genHTML(request)
    else:
        return render_template("upload.html")

def genHTML(request):
    if request.content_type == 'application/x-www-form-urlencoded':
        md = request.form['data']
        md = md.replace("\r\n", "\n")
    elif request.content_type == 'text/markdown':
        try:
            md = request.data.decode("utf-8")

            md = md.replace("\\n", "\n")
        except UnicodeDecodeError:
            return badInputError(request)
    else:
        return badInputError(request)

    if len(md) > 50000:
        abort(status.HTTP_406_NOT_ACCEPTABLE)

    #render the markdown text into html text
    html = markdown.markdown(escape(md), extensions=['mdx_truly_sane_lists', 'pymdownx.superfences'])

    paste = { 
                "pasteID": genID(),
                "username": "guest",
                "timestamp": datetime.now(),
                "markdown": md,
                "html": html
            }

    pastes.insert_one(paste)

    if request.content_type == 'application/x-www-form-urlencoded':
        return redirect(url_for('fetch', pasteID = paste["pasteID"]))
    else:
        response["code"] = status.HTTP_201_CREATED
        response["status"] = "Created file, everything worked, visit {} to access your data".format(url_for('fetch', pasteID = paste["pasteID"]))
        response["url"] = url_for('fetch', pasteID = paste["pasteID"])

        return json.dumps(response), status.HTTP_201_CREATED, {'Content-Type':'application/json'}

def genID():
    return "".join([choice(string.ascii_letters + string.digits) for char in range(8)])

def badInputError(request):
    response["code"] = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    response["status"] = "Markdown only please ('Content-Type: text/markdown', not '{}')".format(request.content_type)
    return json.dumps(response), status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, {'Content-Type':'application/json'}

@app.route("/fetch/<string:pasteID>/raw", methods=['GET'])
def rawFetch(pasteID):
    return retrieve(pasteID)["html"], status.HTTP_200_OK, {'Content-Type':'text/html'}

@app.route("/fetch/<string:pasteID>", methods=['GET'])
def fetch(pasteID):
    paste = retrieve(pasteID)

    return render_template("display.html", paste = paste, title = "fetch", fetch = True)

def retrieve(pasteID):
    paste = pastes.find_one({"pasteID": pasteID})

    if not paste:
        abort(404)
    else:
        return paste

if __name__ == "__main__":
    app.run(debug=True, host = "0.0.0.0")