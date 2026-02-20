import os
from flask import Flask

def create_app():
    app = Flask(
    __name__,
    instance_path=os.path.join(os.path.dirname(__file__), "instance"),
    instance_relative_config=True
    )


    # Ensure instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    # Database path inside app/instance/
    app.config["DATABASE"] = os.path.join(app.instance_path, "flask.sqlite")

    # Register database functions
    from . import db
    db.init_app(app)

    # Register routes
    from . import routes
    app.register_blueprint(routes.bp)

    return app


