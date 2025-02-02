from flask import Flask, request

import os
from func import *

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def cmd_hello_ai():
    return hello_ai(request)

@app.route('/create_resume', methods=['GET', 'POST'])
def cmd_create_resume():
    return create_resume(request)

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=3001)
