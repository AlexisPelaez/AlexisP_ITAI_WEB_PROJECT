from flask import Blueprint,render_template, request 
from .db import get_db
bp = Blueprint('main',__name__)

# SIMPLE PAGE REDIRECTS FOR HTML PAGES

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/info')
def info_page():
    return render_template('info.html')

@bp.route('/simulator')
def simulator_page():
    return render_template('simulator.html')    

# SPECIAL PAGE REDIRECTS

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        db.execute("INSERT INTO user (username, password) VALUES (?, ?)",(username,password))
        db.commit()
        return f'Hello {username}! Your password is {password}.'
    return render_template('name.html')

@bp.route('/show')
def show():
    db = get_db()
    users = db.execute("SELECT * FROM user").fetchall()
    return "<br>".join([f"{u['id']}: {u['username']} - {u['password']}" for u in users])
