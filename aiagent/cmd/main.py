from flask import Flask, request
from flask_cors import CORS

import os
import func
import aichatbot
import analysis
import debug
import hashlib

app = Flask(__name__)
CORS(app)

@app.route('/', methods=['GET'])
def cmd_hello_ai():
    handle_request(request)
    return aichatbot.hello_ai(request)

@app.route('/chats_as_student', methods=['POST'])
def cmd_chats_as_student():
    handle_request(request)
    return aichatbot.chats_as_student(request)

@app.route('/chats_as_teacher', methods=['POST'])
def cmd_chats_as_teacher():
    handle_request(request)
    return aichatbot.chats_as_teacher(request)

@app.route('/create_agenda', methods=['POST'])
def cmd_create_agenda():
    handle_request(request)
    return func.create_agenda(request)

@app.route('/create_questions', methods=['POST'])
def cmd_create_questions():
    handle_request(request)
    return func.create_questions(request)

@app.route('/answered_questions', methods=['POST'])
def cmd_answered_questions():
    handle_request(request)
    return func.answered_questions(request)

@app.route('/submit_homework', methods=['POST'])
def cmd_submit_homework():
    handle_request(request)
    return func.submit_homework(request)

@app.route('/create_summary', methods=['POST'])
def cmd_create_summary():
    handle_request(request)
    return analysis.create_summary(request)

@app.route('/test_firebase', methods=['GET'])
def cmd_test_firebase():
    return debug.test_firebase(request)

@app.route('/test_zip', methods=['GET'])
def cmd_test_zip():
    return debug.test_zip(request)

@app.route('/set_store_value', methods=['POST'])
def cmd_test_store_value():
    return debug.set_store_value(request) if handle_debug(request) else ("NG", 401)

@app.route('/copy_store_field', methods=['POST'])
def cmd_test_copy_field():
    return debug.copy_store_field(request) if handle_debug(request) else ("NG", 401)

@app.route('/show_store_field', methods=['POST'])
def cmd_test_show_field():
    return debug.show_store_field(request) if handle_debug(request) else ("NG", 401)

def handle_request(request):
    print(f"{request.method} [{request.path}] Start.", flush=True)

def handle_debug(request):
    value = request.headers.get('X-DEBUG', 'None')
    hash = hashlib.md5(value.encode()).hexdigest()
    return  hash == 'c6adf464cda7586754994b5ce0fadb3d'

if __name__ == '__main__':
    app.debug = False
    app.threaded = True
    app.run(host='0.0.0.0', port=os.getenv("SERVICE_PORT"))

