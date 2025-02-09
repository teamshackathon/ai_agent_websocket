from flask import Flask, request, jsonify
from flask_cors import CORS

import os
from func import *

app = Flask(__name__)
CORS(app)

@app.route('/', methods=['GET'])
def cmd_hello_ai():
    handle_request(request)
    return hello_ai(request)

@app.route('/chats_as_student', methods=['POST'])
def cmd_chats_as_student():
    handle_request(request)
    return chats_as_student(request)

@app.route('/chats_as_teacher', methods=['POST'])
def cmd_chats_as_teacher():
    handle_request(request)
    return chats_as_teacher(request)

@app.route('/create_agenda', methods=['POST'])
def cmd_create_agenda():
    handle_request(request)
    return create_agenda(request)

@app.route('/create_questions', methods=['POST'])
def cmd_create_questions():
    handle_request(request)
    return create_questions(request)

@app.route('/answered_questions', methods=['POST'])
def cmd_answered_questions():
    handle_request(request)
    return answered_questions(request)

@app.route('/submit_homework', methods=['POST'])
def cmd_submit_homework():
    handle_request(request)
    return submit_homework(request)

@app.route('/test_firebase', methods=['GET'])
def cmd_test_firebase():
    return test_firebase(request)

@app.route('/test_zip', methods=['GET'])
def cmd_test_zip():
    return test_zip(request)

@app.route('/test_store_value', methods=['POST'])
def cmd_test_store_value():
    return test_store_value(request)

@app.route('/test_copy_field', methods=['POST'])
def cmd_test_copy_field():
    return test_copy_field(request)

@app.route('/test_show_field', methods=['POST'])
def cmd_test_show_field():
    return test_show_field(request)

def handle_request(request):
    print(f"{request.method} [{request.path}] Start.", flush=True)

if __name__ == '__main__':
    app.debug = False
    app.run(host='0.0.0.0', port=os.getenv("SERVICE_PORT"))

