import os
from dotenv import load_dotenv
from flask import Flask



load_dotenv()


app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')

from app.controllers import (
    IndexController,
    RegisterController,
    LoginController
)