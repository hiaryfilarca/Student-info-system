from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

from database import db

def create_app():
    base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    frontend_dir = os.path.join(base_dir, 'frontend')
    app = Flask(__name__, template_folder=frontend_dir, static_folder=frontend_dir)

    app.config['SECRET_KEY'] = 'your_secret_key_here'
    # Assuming default XAMPP/WAMP MySQL with blank root password
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/attendance_db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    from backend.routes import main
    app.register_blueprint(main)

    return app