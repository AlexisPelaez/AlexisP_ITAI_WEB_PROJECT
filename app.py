from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello World'
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        return f'Hello {username}! Your password is {password}.'
    return render_template('name.html')
if __name__ == '__main__':
    app.run(debug=True)
