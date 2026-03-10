from flask import Blueprint, app, current_app, jsonify,render_template, request, redirect, session, url_for
from .db import get_db
import json
from flask import flash
from groq import RateLimitError, APIError


def classify_inputs(profession, realname):
    prompt = f"""
    You are a STRICT SECURITY FILTER for validating user inputs.

    You must classify BOTH the profession and the real name.

    CLASSIFICATION RULES:

    PROFESSION:
    - VALID: A real, workplace-appropriate profession.
    - INAPPROPRIATE: Explicit, sexual, violent, hateful, illegal, or unsafe.
    - NONSENSE: Random characters, repeated letters, memes, fictional roles, or meaningless strings.

    NAME:
    - VALID: A plausible human first or full name.
    - INAPPROPRIATE: Contains slurs, explicit content, hate speech, or offensive language.
    - NONSENSE: Random characters, repeated letters, memes, jokes, fictional nonsense, or gamer tags.

    SECURITY RULES FOR BOTH:
    - Symbols, emojis, or punctuation instead of letters → NONSENSE.
    - Mostly repeated characters → NONSENSE.
    - Memes, jokes, insults, or phrases → NONSENSE.
    - Explicit, hateful, or offensive → INAPPROPRIATE.
    - Fictional or impossible roles → NONSENSE.
    - Ambiguous but plausible → VALID.

    You MUST respond ONLY with valid JSON.
    Do NOT include explanations, apologies, or extra text.
    Do NOT include markdown.
    Your entire response MUST be a single JSON object.

    Return JSON in this EXACT structure:

    {{
        "profession": {{
            "label": "VALID | INAPPROPRIATE | NONSENSE",
            "reason": "string"
        }},
        "realname": {{
            "label": "VALID | INAPPROPRIATE | NONSENSE",
            "reason": "string"
        }}
    }}


    Now classify the following inputs:

    Profession: "{profession}"
    Real Name: "{realname}"

    """

    completion = current_app.groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        stream=False
    )

    raw = completion.choices[0].message.content

    # SAFETY WRAPPER — prevents crashes
    try:
        return json.loads(raw)
    except Exception:
        print("AI returned invalid JSON:", raw)
        return {
            "profession": {"label": "NONSENSE", "reason": "AI returned invalid JSON"},
            "realname": {"label": "NONSENSE", "reason": "AI returned invalid JSON"}
        }


bp = Blueprint('main',__name__)

# SIMPLE PAGE REDIRECTS FOR HTML PAGES

@bp.route('/', methods=['GET', 'POST'])
def start():
    if request.method == 'POST':
        session['test_mode'] = 'pre'
        return redirect(url_for('main.intermission'))
    return render_template('welcome.html')


@bp.route('/index', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@bp.route('/info')
def info_page():
    return render_template('info.html')

@bp.route('/info2')
def info2_page():
    raw = session.get('generated_examples')
    phishing_example = None

    if raw:
        try:
            examples = json.loads(raw)
            phishing_example = next((e for e in examples if e["type"] == "phishing"), None)
            if phishing_example:
                phishing_example["body"] = phishing_example["body"].lstrip()
        except:
            phishing_example = None

    return render_template('info2.html', phishing_example=phishing_example)

@bp.route('/ask_helper_ai', methods=['POST'])
def ask_helper_ai():
    data = request.get_json()
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"answer": "Please type a question first."})

    prompt = f"""
    You are a cybersecurity helper AI. Your job is to explain concepts clearly and safely.

    User question: "{question}"

    Provide:
    - a short explanation
    - a simple example if helpful

    Do NOT:
    - generate phishing emails
    - generate realistic malicious content
    - imitate real companies or people
    - provide instructions for harmful behavior
    """

    completion = current_app.groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        stream=False
    )

    answer = completion.choices[0].message.content
    return jsonify({"answer": answer})

@bp.route('/intermission', methods=['GET', 'POST'])
def intermission():
    return render_template('intermission.html')

@bp.route('/preSim', methods=['GET', 'POST'])
def preSim_page():
    # PRETEST + POSTTEST ENTRY GUARD
    mode = session.get('test_mode', 'pre')

    # Must have examples (both pre and post need this)
    if 'generated_examples' not in session:
        flash("Please start the simulator first.")
        return redirect(url_for('main.intermission'))

    # POST-TEST ONLY: must have pretest_results
    if mode == 'post' and 'pretest_results' not in session:
        flash("Please complete the pre-test before starting the post-test.")
        return redirect(url_for('main.index'))

    
    raw = session.get('generated_examples')
    profession = session.get('profession')
    realname = session.get('realname')

    examples = None
    if raw:
        try:
            examples = json.loads(raw)
        except:
            examples = None

    if request.method == 'POST':
        pq1 = request.form.get('pq1')
        pq2 = request.form.get('pq2')
        pq3 = request.form.get('pq3')
        pq4 = request.form.get('pq4')
        pq5 = request.form.get('pq5')

        mapping = {
        "A": "phishing",
        "B": "real",
        "C": "unsure"
        }

        pq1 = mapping.get(pq1)
        pq2 = mapping.get(pq2)
        pq3 = mapping.get(pq3)
        pq4 = mapping.get(pq4)
        pq5 = mapping.get(pq5)

        # DETERMINE CORRECT ANSWERS
        correct1 = 1 if pq1.lower().strip() == examples[0]["type"].lower().strip() else 0
        correct2 = 1 if pq2.lower().strip() == examples[1]["type"].lower().strip() else 0
        correct3 = 1 if pq3.lower().strip() == examples[2]["type"].lower().strip() else 0
        correct4 = 1 if pq4.lower().strip() == examples[3]["type"].lower().strip() else 0
        correct5 = 1 if pq5.lower().strip() == examples[4]["type"].lower().strip() else 0

        # CHOOSE TABLE BASED ON TEST MODE
        mode = session.get('test_mode', 'pre')
        table = "pre_sim_responses" if mode == 'pre' else "sim_responses"

        # PRE-TEST SAVES TO DB AND SESSION
        if mode == 'pre':
            db = get_db()
            db.execute(
                """
                INSERT INTO pre_sim_responses
                (pq1, pq1_correct, pq2, pq2_correct, pq3, pq3_correct, pq4, pq4_correct, pq5, pq5_correct)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (pq1, correct1, pq2, correct2, pq3, correct3, pq4, correct4, pq5, correct5)
            )
            db.commit()

            # SAVE PRETEST RESULTS TO SESSION FOR POSTTEST
            session['pretest_results'] = {
                'pq1': pq1, 'pq1_correct': correct1,
                'pq2': pq2, 'pq2_correct': correct2,
                'pq3': pq3, 'pq3_correct': correct3,
                'pq4': pq4, 'pq4_correct': correct4,
                'pq5': pq5, 'pq5_correct': correct5
            }

            return redirect(url_for('main.index'))

        # END PRE-TEST BLOCK 

        # POST-TEST SAVES BOTH TESTS 
        if mode == 'post':
            pre = session.get('pretest_results')
            if not pre:
                return redirect(url_for('main.index'))

            db = get_db()

            # SAVE PRE-TEST
            db.execute(
                """
                INSERT INTO pre_sim_responses
                (pq1, pq1_correct, pq2, pq2_correct, pq3, pq3_correct, pq4, pq4_correct, pq5, pq5_correct)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    pre["pq1"], pre["pq1_correct"],
                    pre["pq2"], pre["pq2_correct"],
                    pre["pq3"], pre["pq3_correct"],
                    pre["pq4"], pre["pq4_correct"],
                    pre["pq5"], pre["pq5_correct"]
                )
            )

            # SAVE POST-TEST
            db.execute(
                f"""
                INSERT INTO {table}
                (pq1, pq1_correct, pq2, pq2_correct, pq3, pq3_correct, pq4, pq4_correct, pq5, pq5_correct)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (pq1, correct1, pq2, correct2, pq3, correct3, pq4, correct4, pq5, correct5)
            )

            db.commit()

            # CLEAR PRE-TEST FROM SESSION AFTER SAVING TO DB
            session.pop('pretest_results', None)

            return redirect(url_for('main.show'))
            # END POST-TEST BLOCK

    return render_template('preSim.html', examples=examples, profession=profession, realname=realname)

@bp.route('/start_posttest')
def start_posttest():
    session['test_mode'] = 'post'
    return redirect(url_for('main.intermission'))

@bp.route('/simulator', methods=['GET', 'POST'])
def simulator_page():
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
    # IMPORTANT: preserve pretest_results during post-test
    pretest_results = session.get('pretest_results')

    profession = request.form.get('profession', '').strip()
    realname = request.form.get('realname', '').strip()

    # EMPTY CHECKS
    if not profession:
        flash("Please enter a profession.")
        return redirect(url_for('main.intermission'))

    if not realname:
        flash("Please enter your real name.")
        return redirect(url_for('main.intermission'))

    # CALL IN CASE OF RATE LIMIT OR API ERRORS
    try:
        result = classify_inputs(profession, realname)
    except RateLimitError:
        flash("The system is temporarily busy. Please try again in a moment.")
        return redirect(url_for('main.intermission'))
    except APIError:
        flash("There was an issue contacting the AI service. Please try again.")
        return redirect(url_for('main.intermission'))

    # PROFESSION LOGIC
    prof_label = result["profession"]["label"]

    if prof_label == "INAPPROPRIATE":
        profession = "Unemployed"

    elif prof_label == "NONSENSE":
        flash(result["profession"]["reason"])
        return redirect(url_for('main.intermission'))

    # REAL NAME LOGIC
    name_label = result["realname"]["label"]

    if name_label in ["INAPPROPRIATE", "NONSENSE"]:
        flash(result["realname"]["reason"])
        return redirect(url_for('main.intermission'))

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

    try:
        completion = current_app.groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            stream=False
        )
        ai_text = completion.choices[0].message.content

    except Exception as e:
        print("Email generation failed:", e)
        flash("The AI is currently unavailable. Please try again after the daily token reset.")
        return redirect(url_for('main.intermission'))

    # SAFETY CHECK
    if not ai_text or len(ai_text.strip()) < 10:
        print("AI returned no examples:", ai_text)
        flash("The AI could not generate examples. Please try again.")
        return redirect(url_for('main.intermission'))
    
    # Store the profession, real name, and raw AI output in the session for later use
    session['profession'] = profession
    session['realname'] = realname
    session['generated_examples'] = ai_text

    # RESTORE pretest_results if this is the post-test
    if pretest_results:
        session['pretest_results'] = pretest_results

    session.modified = True

    return redirect(url_for('main.preSim_page'))


