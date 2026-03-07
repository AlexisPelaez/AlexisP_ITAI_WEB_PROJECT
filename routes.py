from flask import Blueprint, app, current_app,render_template, request, redirect, session, url_for
from .db import get_db
import re
import json
from flask import flash
from groq import RateLimitError, APIError


def classify_profession(profession):
    prompt = f"""
    You are a STRICT SECURITY FILTER for a profession-based email simulator.

    Your ONLY job is to classify the user-provided profession into one of three categories:

    - VALID: A real, workplace-appropriate profession or job title.
    - INAPPROPRIATE: Explicit, sexual, violent, hateful, illegal, or otherwise unsafe for a workplace simulator.
    - NONSENSE: Not a real profession. This includes random characters, repeated letters, jokes, memes, fictional roles, or meaningless strings.

    SECURITY RULES:
    - If the input contains symbols, emojis, or punctuation instead of letters (e.g., "###", "@@@", "!!!"), classify it as NONSENSE.
    - If the input is fewer than 3 characters, classify it as NONSENSE.
    - If the input is mostly repeated characters (e.g., "aaaaaa", "lololol", "zzzzzz"), classify it as NONSENSE.
    - If the input is a joke, meme, insult, or non-job phrase (e.g., "your mom", "poop eater", "sigma grinder"), classify it as NONSENSE.
    - If the input is fictional or impossible as a real-world job (e.g., "dragon slayer", "wizard king", "demon hunter"), classify it as NONSENSE.
    - If the input refers to sexual content, adult entertainment, pornography, or explicit work, classify it as INAPPROPRIATE.
    - If the input refers to violence, killing, weapons, terrorism, extremism, or organized crime, classify it as INAPPROPRIATE.
    - If the input refers to clearly illegal activity (e.g., "drug dealer", "cartel boss", "hitman"), classify it as INAPPROPRIATE.
    - If the input is ambiguous but could reasonably be a real job title, prefer VALID.

    Respond ONLY in this exact JSON format:

    {{
      "label": "VALID or INAPPROPRIATE or NONSENSE",
      "reason": "A short explanation of why you chose this label."
    }}

    User input: "{profession}"
    """

    completion = current_app.groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        stream=False
    )

    return json.loads(completion.choices[0].message.content)

def classify_realname(realname):
    prompt = f"""
    You are a STRICT SECURITY FILTER for validating human names.

    Classify the input into one of three categories:

    - VALID: A plausible human first or full name.
    - INAPPROPRIATE: Contains slurs, explicit content, hate speech, or offensive language.
    - NONSENSE: Random characters, repeated letters, memes, jokes, fictional nonsense, or anything not resembling a real name.

    SECURITY RULES:
    - If the input contains symbols, emojis, or punctuation instead of letters (e.g., "###", "@@@", "!!!"), classify as NONSENSE.
    - If the input is fewer than 2 characters, classify as NONSENSE.
    - If the input is mostly repeated characters (e.g., "aaaaaa", "zzzzzz"), classify as NONSENSE.
    - If the input is a meme, joke, insult, or phrase (e.g., "your mom", "poop", "sigma grinder"), classify as NONSENSE.
    - If the input contains explicit, hateful, or offensive language, classify as INAPPROPRIATE.
    - If the input resembles a gamer tag or handle (e.g., "xXx_killer_xXx"), classify as NONSENSE.
    - If the input is ambiguous but could be a real name, prefer VALID.

    Respond ONLY in this JSON format:

    {{
      "label": "VALID or INAPPROPRIATE or NONSENSE",
      "reason": "A short explanation of why you chose this label."
    }}

    User input: "{realname}"
    """

    completion = current_app.groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        stream=False
    )

    return json.loads(completion.choices[0].message.content)


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

@bp.route('/intermission', methods=['GET', 'POST'])
def intermission():
    return render_template('intermission.html')

@bp.route('/preSim', methods=['GET', 'POST'])
def preSim_page():
    # 1. Retrieve raw AI output from session
    raw = session.get('generated_examples')
    profession = session.get('profession')
    realname = session.get('realname')

    # 2. Parse JSON into Python list
    examples = None
    if raw:
        try:
            examples = json.loads(raw)
            print("RAW AI OUTPUT:", raw)
        except:
            examples = None
            print("RAW AI OUTPUT:", raw)
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
    return render_template('preSim.html', examples=examples, profession=profession, realname=realname)

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
    profession = request.form.get('profession', '').strip()
    realname = request.form.get('realname', '').strip()

    # EMPTY CHECKS FOR PROFESSION AND REAL NAME
    if not profession or len(profession.strip()) == 0:
        flash("Please enter a profession.")
        return redirect(url_for('main.intermission'))

    if not realname or len(realname.strip()) == 0:
        flash("Please enter your real name.")
        return redirect(url_for('main.intermission'))

    # DEFENSE AGAINST INAPPROPRIATE OR UNSAFE PROFESSIONS OR NAMES

    try:
        classification = classify_profession(profession)
    except RateLimitError:
        flash("The system is temporarily busy. Please try again in a moment.")
        return redirect(url_for('main.intermission'))
    except APIError:
        flash("There was an issue contacting the AI service. Please try again.")
        return redirect(url_for('main.intermission'))

    if classification["label"] == "INAPPROPRIATE":
        profession = "Unemployed"

    elif classification["label"] == "NONSENSE":
        flash(classification["reason"])
        return redirect(url_for('main.intermission'))

    # DEFENSE AGAINST INAPPROPRIATE OR UNSAFE REAL NAMES
    name_classification = classify_realname(realname)

    if name_classification["label"] == "INAPPROPRIATE":
        flash(name_classification["reason"])
        return redirect(url_for('main.intermission'))

    elif name_classification["label"] == "NONSENSE":
        flash(name_classification["reason"])
        return redirect(url_for('main.intermission'))

    if not profession:
        return "No profession provided", 400
    if not realname:
        return "No name provided", 400

    # Build prompt for Groq
    prompt = f"""
    Generate ONLY 5 full-length workplace emails for someone working as a {profession}.
    Use the recipient's real name: {realname}.
    They must be a realistic mix:
    - 3 phishing emails
    - 2 legitimate emails
    
    SAFETY RULES FOR PROFESSION INPUT:
    - If the provided profession is violent, illegal, hateful, explicit, or otherwise inappropriate for workplace email simulation, you MUST NOT generate emails for that profession. Instead, reinterpret the profession as a neutral, safe, workplace-appropriate role that is adjacent or analogous. You MUST NOT mention that you reinterpreted the profession. Simply generate the emails using the safe replacement profession.

    PHISHING & LEGITIMATE EMAIL REQUIREMENTS
    - Phishing emails MUST each differ in their red flags. Do NOT make all phishing emails have the same red flag. Make one of the phishing emails incredibly easy to identify as a phishing email, with multiple red flags. Make another phishing email more subtle, with only one red flag that is not super obvious. Make the third phishing email somewhere in between, with 2-3 red flags that are somewhat obvious but could potentially be missed by someone who is not paying close attention.
    - Each email MUST have a professiomal tone appropriate for the workplace, even the phishing ones. Do NOT make the phishing emails sound overly dramatic or unrealistic.
    - Each email MUST include profession-specific terminology, tools, workflows, or realistic scenarios that someone in the {profession} field would encounter.
    - Do NOT repeat sentences or ideas. All content must be unique and meaningful.
    - All five subject lines MUST be unique and must not reuse the same structure or phrasing. For example, do NOT make all the subject lines follow the same format of "Action Required: [Task]". Instead, create a variety of subject line styles that are appropriate for workplace emails in the {profession} field.
    - Each email MUST describe a different scenario, workflow, or situation. Do NOT reuse the same storyline or context across multiple emails. Each email should present a distinct situation that someone in the {profession} field might realistically encounter.
    - Phishing emails MUST NOT all rely on password resets, account lockouts, or credential updates. Only one phishing email may use this theme. The other phishing emails should use different themes, such as invoice/payment fraud, fake meeting invites, impersonation of colleagues or supervisors, or requests for sensitive information.

    FORMATTING & STRUCTURE RULES
    - Return ONLY valid JSON.
    - No markdown.
    - No HTML tags of any kind.
    - All links must be plain text only (example: http://example.com). BUT MAKE THE LINKS REALISTIC AND RELEVANT TO THE PROFESSION. For example, if the profession is a teacher, a phishing email might include a link that looks like it's from an educational software company.
    - Do NOT reuse the same domain name for links across multiple emails. Each email must use a different realistic domain relevant to the {profession}.
    - Do not wrap links in <a> tags or any HTML formatting.
    - You MUST use the last name of "{realname}" naturally in greetings, sign-offs, or references.
    - Create a new line for each paragraph, but do not use <p> tags or any HTML formatting.
    - Each paragraph MUST be separated by \\n\\n.
    - You MUST escape all newline characters as \\n.

    - LENGTH & SENTENCE REQUIREMENTS:
    - Each paragraph MUST contain 4–6 full sentences.
    - Each email MUST contain exactly 4 paragraphs, plus a greeting line and a closing line.
    - Each email MUST be between 280 and 320 words. Do NOT produce fewer than 280 words under any circumstances.
    - Avoid short or vague sentences. Each sentence should contain meaningful detail and be at least 12–18 words long.

    NAME/SENDER RULES: 
    - Sender names MUST be diverse and varied across all five emails. Do NOT reuse the same first or last name more than once.
    - Sender names MUST reflect realistic workplace diversity. Use a mix of genders, ethnic backgrounds, and name styles (e.g., traditional, modern, international) that are appropriate for a professional setting. Avoid using names that are overly common or generic (e.g., John Smith) as well as names that are too unusual or unrealistic.
    - Sender names MUST sound professional and appropriate for workplace communication.
    - Sender names MUST be appropriate for the {profession} field. For example, if the profession is storm chasing, names may belong to meteorologists, field coordinators, emergency managers, data analysts, or equipment specialists.
    - Each sender MUST include a realistic job role or implied position based on the email content (e.g., “Field Operations Coordinator,” “Data Analysis Lead,” “Equipment Logistics Manager,” “Safety Compliance Officer”). Add their job titles at the end of their names. Do NOT repeat job roles across emails.

    DIFFICULTY LABEL RULES (IMPORTANT):
    - "least-difficult" = The phishing email that is extremely obvious, with multiple red flags.
    - "semi-difficult" = The phishing email that has 2–3 red flags that are noticeable but not extremely obvious.
    - "most-difficult" = The phishing email that is subtle, with only one red flag that could be easily missed.
    - "n/a" = Used ONLY for legitimate emails.
    
    REAL-WORLD NEWS EVENT RULES (IMPORTANT):
    Exactly ONE email must reference a real-world news-related event that is relevant to the {profession}. This event MUST be:
    - realistic,
    - widely reported in general news,
    - and something a professional in the field would recognize.

    You MAY describe the event in a specific and detailed way, BUT:
    - you MUST NOT quote or reproduce copyrighted news articles,
    - you MUST NOT use real people's names,
    - you MUST NOT claim the event is a specific historical incident. Instead, you should create a fictionalized version of a real news pattern that sounds like it could be real news coverage, without referencing any specific copyrighted content. For example, if the profession is related to cybersecurity, you might create a fictionalized email about "a widespread data breach affecting multiple organizations last month" that includes realistic details about the breach and its impact, without referencing any specific real-world incident or using any real names.
    You ARE allowed to create fictionalized versions of real news patterns (e.g., “a multi-state tornado outbreak last month,” “a major financial depression affecting several counties,” “a widespread data breach affecting multiple organizations”). These fictionalized events MUST sound like real news coverage without referencing copyrighted content.
    The email with the event MUST include a short explanation in "real_world_event_description" describing the event in 1–2 sentences.

    UNEMPLOYED OVERRIDE RULE:
    If the profession has been set to “Unemployed,” you MUST override the normal email content rules. 
    Instead of workplace emails, generate emails that are appropriate for someone who is currently unemployed. 
    These emails MUST still follow all formatting, length, JSON, paragraph, and difficulty rules, but the content MUST be related to:
    - job applications,
    - interview scheduling,
    - unemployment benefits,
    - job training programs,
    - networking opportunities,
    - community resources,
    - or general professional communication.

    Do NOT reference workplace tools, workflows, or internal systems, since an unemployed person would not have access to them. 
    Do NOT mention that the profession was changed or reinterpreted.


    Use this format:
    [
    {{
        "subject": "A realistic subject line",
        "body": "Dear {realname},\\n\\nParagraph 1 with 4–6 detailed sentences that introduce the purpose of the email and provide meaningful context.\\n\\nParagraph 2 with 4–6 sentences that expand on the situation, include specific details, and reference realistic workplace processes.\\n\\nParagraph 3 with 4–6 sentences that add additional information, follow-up actions, or clarifications.\\n\\nParagraph 4 with 4–6 sentences that conclude the message, reinforce next steps, and maintain a professional tone.\\n\\nSincerely,\\nSender Name",
        "type": "phishing | real",
        "difficulty": "most-difficult | semi-difficult | least-difficult | n/a",
        "real_world_event": "yes | no",
        "real_world_event_description": "If real_world_event is 'yes', briefly describe the real-world news-related event being referenced. If 'no', write 'n/a'.",
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
    session['realname'] = realname
    session['generated_examples'] = ai_text

    # Mark the session as modified to ensure it gets saved
    session.modified = True

    # Redirect to your existing PreSim page
    return redirect(url_for('main.preSim_page'))


