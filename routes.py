from flask import Blueprint, app, current_app,render_template, request, redirect, session, url_for
from .db import get_db
import json

bp = Blueprint('main',__name__)

# SIMPLE PAGE REDIRECTS FOR HTML PAGES

@bp.route('/', methods=['GET', 'POST'])
def start():
    if request.method == 'POST':
        return redirect(url_for('main.preSim_page'))
    return render_template('welcome.html')

@bp.route('/index')
def index():
    return render_template('index.html')

@bp.route('/info')
def info_page():
    return render_template('info.html')

@bp.route('/intermission', methods=['POST'])
def intermission():
    return render_template('intermission.html')

@bp.route('/preSim', methods=['GET', 'POST'])
def preSim_page():
    # 1. Retrieve raw AI output from session
    raw = session.get('generated_examples')
    profession = session.get('profession')

    # 2. Parse JSON into Python list
    examples = None
    if raw:
        try:
            examples = json.loads(raw)
        except:
            examples = None
    # 3. Handle form submission
    if request.method == 'POST':
        pq1 = request.form.get('pq1')
        pq2 = request.form.get('pq2')
        pq3 = request.form.get('pq3')
        pq4 = request.form.get('pq4')
        pq5 = request.form.get('pq5')
        db = get_db()
        db.execute("INSERT INTO pre_sim_responses (pq1, pq2, pq3, pq4, pq5) VALUES (?,?,?,?,?) ", (pq1, pq2, pq3, pq4, pq5))
        db.commit()
        return redirect(url_for('main.index'))
    # 4. Render template with AI examples and profession
    return render_template('preSim.html', examples=examples, profession=profession)

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
    sim_responses = db.execute("SELECT * FROM sim_responses").fetchall()
    preSim_responses = db.execute("SELECT * FROM pre_sim_responses").fetchall()


    return render_template('data.html', sim_responses=sim_responses, preSim_responses=preSim_responses)

@bp.route('/handle-profession', methods=['POST'])
def handle_profession():
    profession = request.form.get('profession')

    if not profession:
        return "No profession provided", 400

    # Build prompt for Groq
    prompt = f"""
    Generate 5 full-length workplace emails for someone working as a {profession}.
    They must be a realistic mix:
    - 3 phishing emails
    - 2 legitimate emails

    IMPORTANT RULES:
    - Return ONLY valid JSON.
    - No markdown.
    - No HTML tags of any kind.
    - All links must be plain text only (example: http://example.com).
    - Do not wrap links in <a> tags or any HTML formatting.
    - Each email MUST be at least 2 paragraphs long to ensure realism.

    Use this format:
    [
    {{
        "subject": "A realistic subject line",
        "body": "A full-length email with paragraphs.",
        "type": "phishing | real",
        "red_flag": "Describe the suspicious element, or 'none' if the email is legitimate."
    }},
    ...
    ]
    """

    completion = current_app.groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        stream=False
    )

    ai_text = completion.choices[0].message.content

    # Store in session so PreSim can use it later
    session['profession'] = profession
    session['generated_examples'] = ai_text

    # Redirect to your existing PreSim page
    return redirect(url_for('main.preSim_page'))


