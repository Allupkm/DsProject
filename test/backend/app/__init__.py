from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import JWTManager
import pyodbc
import os

db = SQLAlchemy()
login_manager = LoginManager()
limiter = Limiter(key_func=get_remote_address)
jwt = JWTManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    

    db.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)
    jwt.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    

    from app.auth import auth as auth_blueprint
    from app.courses import courses as courses_blueprint
    from app.exams import exams as exams_blueprint
    from app.grading import grading as grading_blueprint
    from app.heartbeat import heartbeat as heartbeat_blueprint
    
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(courses_blueprint)
    app.register_blueprint(exams_blueprint)
    app.register_blueprint(grading_blueprint)
    app.register_blueprint(heartbeat_blueprint)
    
    # Create database tables
    with app.app_context():
        db.create_all()
        
        # Schedule periodic tasks
        from app.utils import scheduler
        scheduler.init_app(app)
        scheduler.start()
    
    return app