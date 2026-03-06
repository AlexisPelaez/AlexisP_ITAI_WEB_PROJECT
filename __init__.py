import os
from flask import Flask
from groq import Groq

def create_app():
    app = Flask(
    __name__,
    instance_path=os.path.join(os.path.dirname(__file__), "instance"),
    instance_relative_config=True
    )
    
    # Secret key for sessions
    app.secret_key = os.getenv("SECRET_KEY", "dev-key")

    # Ensure instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    # Database path inside app/instance/
    app.config["DATABASE"] = os.path.join(app.instance_path, "flask.sqlite")

     # Configure Groq client
    app.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    # Register database functions
    from . import db
    db.init_app(app)

    # Register routes
    from . import routes
    app.register_blueprint(routes.bp)

    return app


