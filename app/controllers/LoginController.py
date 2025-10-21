from flask import render_template
from app import app

@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('Login/login.html')
