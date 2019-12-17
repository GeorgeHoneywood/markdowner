from flask import Flask, request, url_for
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

@app.route("/upload", methods=["POST"])
def upload():
    if not request.content_type == 'text/markdown':
        response["code"] = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
        response["status"] = "Markdown only please ('Content-Type: text/markdown', not '{}')".format(request.content_type)
        return json.dumps(response), status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, {'Content-Type':'application/json'}
    
    try:
        md = request.data.decode("utf-8")
    except UnicodeDecodeError as e:
        response["code"] = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
        response["status"] = "Markdown only please ('{}')".format(e)
        return json.dumps(response), status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, {'Content-Type':'application/json'}

    #if the newlines are escaped
    md = md.replace("\\n", "\n")

    html = markdown.markdown(md)

    response["id"] = genID()

    with open(prefix + response["id"], "w") as f:
        f.write(html)

    response["code"] = status.HTTP_201_CREATED
    response["status"] = "Created file, everything worked, visit {}fetch/{} to access your data".format(request.host_url, response["id"])
    response["url"] = "{}fetch/{}".format(request.host_url, response["id"])

    return json.dumps(response), status.HTTP_201_CREATED, {'Content-Type':'application/json'}

def genID():
    return "".join([choice(string.ascii_letters + string.digits) for char in range(8)])

@app.route('/fetch/<id>')
def retrieve(id):
    try:
        with open(prefix + id, "r") as f:
            return f.read(), status.HTTP_200_OK, {'Content-Type':'text/html'}
    except FileNotFoundError as e:
        response["code"] = status.HTTP_404_NOT_FOUND
        response["status"] = "ID '{}' not found".format(id)
        return json.dumps(response), status.HTTP_404_NOT_FOUND, {'Content-Type':'application/json'}

if __name__ == "__main__":
    app.run(debug=True)