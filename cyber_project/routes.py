from flask import Blueprint,render_template, request 
from .db import get_db
bp = Blueprint('main',__name__)

# PAGE ROUTING

@bp.route('/')
def hello_world():
    return 'Hello World'

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        db.execute("INSERT INTO user (username, password) VALUES (?, ?)",(username,password))
        db.commit
        return f'Hello {username}! Your password is {password}.'
    return render_template('name.html')
