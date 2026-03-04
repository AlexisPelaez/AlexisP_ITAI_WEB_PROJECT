from flask import Blueprint,render_template, request, redirect, url_for
from .db import get_db

bp = Blueprint('main',__name__)

# SIMPLE PAGE REDIRECTS FOR HTML PAGES

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/info')
def info_page():
    return render_template('info.html')

@bp.route('/simulator', methods=['GET', 'POST'])
def simulator_page():
    if request.method == 'POST':
        q1 = request.form.get('q1')
        q2 = request.form.get('q2')
        q3 = request.form.get('q3')
        q4 = request.form.get('q4')
        q5 = request.form.get('q5')
        db = get_db()
        db.execute("INSERT INTO sim_responses (q1, q2, q3, q4, q5) VALUES (?,?,?,?,?) ", (q1, q2, q3, q4, q5))
        db.commit()
        return redirect(url_for('main.simulator_page', submitted=1))
    return render_template('simulator.html')

@bp.route('/test')
def test_page():
    return render_template('test.html')

# SPECIAL PAGE REDIRECTS

@bp.route('/show')
def show():
    db = get_db()
    responses = db.execute("SELECT * FROM sim_responses").fetchall()

    return render_template('data.html', responses=responses)