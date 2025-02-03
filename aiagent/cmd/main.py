from flask import Flask, request

import os
from func import *

app = Flask(__name__)

@app.route('/', methods=['GET'])
def cmd_hello_ai():
    return hello_ai(request)

@app.route('/create_agenda', methods=['POST'])
def cmd_create_agenda():
    return create_agenda(request)

@app.route('/create_questions', methods=['POST'])
def cmd_create_questions():
    return create_questions(request)

@app.route('/test_firebase', methods=['GET'])
def cmd_test_firebase():
    return test_firebase(request)

@app.route('/test_zip', methods=['GET'])
def cmd_test_zip():
    return test_zip(request)

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=3001)
