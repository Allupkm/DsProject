from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import JWTManager
from app.config import Config
from app.utils import init_scheduled_tasks
import os

db = SQLAlchemy()
login_manager = LoginManager()
limiter = Limiter(key_func=get_remote_address)
jwt = JWTManager()

def create_app(config_class=Config):
    """Application factory function."""
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

    with app.app_context():
        db.create_all()
        init_scheduled_tasks(app)
    

    @app.errorhandler(403)
    def forbidden_error(error):
        return jsonify({
            "error": "Forbidden",
            "message": "You don't have permission to access this resource."
        }), 403
    
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({
            "error": "Not Found",
            "message": "The requested resource was not found."
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({
            "error": "Internal Server Error",
            "message": "An unexpected error occurred."
        }), 500
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(ssl_context='adhoc')