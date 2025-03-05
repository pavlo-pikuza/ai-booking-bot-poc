from flask import Flask, request, jsonify
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from datetime import datetime
import os

app = Flask(__name__, template_folder='templates', static_folder='static')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)