from flask import render_template
from app import app


@app.route('/register',  methods=['GET', 'POST'])
def register():
    return render_template('Register/register.html')