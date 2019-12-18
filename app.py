from flask import Flask, request, url_for, render_template, redirect, abort, escape
from flask_cors import CORS
from flask_api import status

from pymongo import MongoClient
from datetime import datetime
from random import choice

import json
import requests
import string
import markdown

app = Flask(__name__)
CORS(app)

response = {}

client = MongoClient("mongodb://markdowner:FC9BAuUt32wX@ds117960.mlab.com:17960/heroku_n4snplp7")
db = client["heroku_n4snplp7"]
pastes = db.pastes

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", upload=url_for("upload"))

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        return genHTML(request)
    else:
        return inputMarkdown(request)

def genHTML(request):
    if request.content_type == 'application/x-www-form-urlencoded':
        md = request.form['data']
        md = md.replace("\r\n", "\n")
    elif request.content_type == 'text/markdown':
        try:
            md = request.data.decode("utf-8")

            md = md.replace("\\n", "\n")
        except UnicodeDecodeError as e:
            response["code"] = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
            response["status"] = "Markdown only please ('{}')".format(e)
            return json.dumps(response), status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, {'Content-Type':'application/json'}
    else:
        response["code"] = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
        response["status"] = "Markdown only please ('Content-Type: text/markdown', not '{}')".format(request.content_type)
        return json.dumps(response), status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, {'Content-Type':'application/json'}

    #render the markdown text into html text
    html = markdown.markdown(escape(md), extensions=['mdx_truly_sane_lists', 'pymdownx.superfences'])

    paste = { 
            "pasteID": genID(),
            "userID": "guest",
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

def inputMarkdown(request):
    return render_template("upload.html", url=url_for("upload", _external=True))

@app.route("/fetch/<string:pasteID>/raw", methods=['GET'])
def rawFetch(pasteID):
    return retrieve(pasteID)["html"], status.HTTP_200_OK, {'Content-Type':'text/html'}

@app.route("/fetch/<string:pasteID>", methods=['GET'])
def fetch(pasteID):
    paste = retrieve(pasteID)

    return render_template("display.html", body = paste["html"], title = "fetch", fetch = True, pasteID = pasteID, user = paste["userID"], timestamp = paste["timestamp"])

def retrieve(pasteID):
    paste = pastes.find_one({"pasteID": pasteID})

    if not paste:
        abort(404)
    else:
        return paste

if __name__ == "__main__":
    app.run(debug=True, host = "0.0.0.0")