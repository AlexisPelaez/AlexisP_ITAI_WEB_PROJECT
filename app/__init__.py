import os
from flask import Flask
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from groq import Groq

db = SQLAlchemy()

def create_app():
    app = Flask(
        __name__,
        static_folder="../static",
        template_folder="../templates",
        instance_path=os.path.join(os.path.dirname(__file__), "instance"),
        instance_relative_config=True
    )

    # Secret key
    app.secret_key = os.getenv("SECRET_KEY", "dev-key")

    # Ensure instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    # POSTGRES DATABASE CONFIG
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    # Session config
    app.config["SESSION_TYPE"] = "filesystem"
    app.config["SESSION_FILE_DIR"] = os.path.join(app.instance_path, "flask_session")
    app.config["SESSION_PERMANENT"] = False
    Session(app)

    # Groq client
    app.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    # Import models so SQLAlchemy knows them
    from .models import PreSimResponse, SimResponse

    # Create tables if they don't exist
    with app.app_context():
        db.create_all()

    # Register routes
    from . import routes
    app.register_blueprint(routes.bp)

    return app