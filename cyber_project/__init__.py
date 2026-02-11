from flask import Flask
import os

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # Make sure the instance folder exists BEFORE using it
    os.makedirs(app.instance_path, exist_ok=True)

    # Use a clean absolute path for the database
    app.config["DATABASE"] = os.path.join(
        os.path.abspath(app.instance_path),
        "flask.sqlite"
    )

    from . import db
    db.init_app(app)

    from . import routes
    app.register_blueprint(routes.bp)

    return app
