from flask import Flask, request, url_for, render_template, redirect, abort
from flask_cors import CORS
from flask_api import status

from random import choice

import json
import requests
import string
import markdown

app = Flask(__name__)
CORS(app)

response = {}
prefix = "html/"

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
    html = markdown.markdown(md, extensions=['mdx_truly_sane_lists', 'pymdownx.superfences'])

    response["id"] = genID()

    with open(prefix + response["id"], "w") as f:
        f.write(html)

    if request.content_type == 'application/x-www-form-urlencoded':
        return redirect("{}fetch/{}".format(request.host_url, response["id"]))
    else:
        response["code"] = status.HTTP_201_CREATED
        response["status"] = "Created file, everything worked, visit {}fetch/{} to access your data".format(request.host_url, response["id"])
        response["url"] = "{}fetch/{}".format(request.host_url, response["id"])

        return json.dumps(response), status.HTTP_201_CREATED, {'Content-Type':'application/json'}

def genID():
    return "".join([choice(string.ascii_letters + string.digits) for char in range(8)])

def inputMarkdown(request):
    return render_template("upload.html", url=url_for("upload", _external=True))

@app.route("/fetch/<string:id>/raw", methods=['GET'])
def rawFetch(id):
    return retrieve(id), status.HTTP_200_OK, {'Content-Type':'text/html'}

@app.route("/fetch/<string:id>", methods=['GET'])
def fetch(id):
    body = retrieve(id)

    return render_template("display.html", body = body, title = "fetch", display = True, id = id)

def retrieve(id):
    try:
        with open(prefix + id, "r") as f:
            return f.read()
    except FileNotFoundError as e:
        # response["code"] = status.HTTP_404_NOT_FOUND
        # response["status"] = "ID '{}' not found".format(id)
        # return json.dumps(response), status.HTTP_404_NOT_FOUND, {'Content-Type':'application/json'}
        abort(404)

if __name__ == "__main__":
    app.run(debug=True)