from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime
import bcrypt
import jwt
from time import time
from app.config import Config
from sqlalchemy import event
from sqlalchemy.orm import validates

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    salt = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    

    courses_created = db.relationship('Course', backref='creator', lazy=True)
    enrollments = db.relationship('CourseEnrollment', backref='user', lazy=True)
    exams_created = db.relationship('Exam', backref='creator', lazy=True)
    attempts = db.relationship('ExamAttempt', backref='user', lazy=True)
    answers_graded = db.relationship('Answer', backref='grader', lazy=True, foreign_keys='Answer.graded_by')
    logs = db.relationship('AuditLog', backref='user', lazy=True)
    
    def get_id(self):
        return str(self.user_id)
    
    def set_password(self, password):
        self.salt = bcrypt.gensalt().decode('utf-8')
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), self.salt.encode('utf-8')).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def get_reset_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.user_id, 'exp': time() + expires_in},
            Config.SECRET_KEY, algorithm='HS256')
    
    @staticmethod
    def verify_reset_token(token):
        try:
            user_id = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])['reset_password']
        except:
            return None
        return User.query.get(user_id)
    
    @validates('role')
    def validate_role(self, key, role):
        assert role in ['admin', 'professor', 'student']
        return role
    
    @validates('email')
    def validate_email(self, key, email):
        assert '@' in email
        return email

class Course(db.Model):
    __tablename__ = 'courses'
    
    course_id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(20), unique=True, nullable=False)
    course_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500))
    created_by = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    enrollments = db.relationship('CourseEnrollment', backref='course', lazy=True)
    exams = db.relationship('Exam', backref='course', lazy=True)

class CourseEnrollment(db.Model):
    __tablename__ = 'course_enrollments'
    
    enrollment_id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    enrollment_date = db.Column(db.DateTime, default=datetime.utcnow)
    role = db.Column(db.String(20), nullable=False)
    
    __table_args__ = (
        db.UniqueConstraint('course_id', 'user_id', name='_course_user_uc'),
    )
    
    @validates('role')
    def validate_role(self, key, role):
        assert role in ['professor', 'student', 'ta']
        return role

class Exam(db.Model):
    __tablename__ = 'exams'
    
    exam_id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id'), nullable=False)
    exam_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500))
    time_limit_minutes = db.Column(db.Integer)
    available_from = db.Column(db.DateTime)
    available_to = db.Column(db.DateTime)
    is_published = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    ip_restriction = db.Column(db.String(255))
    browser_lockdown = db.Column(db.Boolean, default=False)
    show_results_immediately = db.Column(db.Boolean, default=False)
    show_results_after = db.Column(db.DateTime)
    

    questions = db.relationship('Question', backref='exam', lazy=True)
    attempts = db.relationship('ExamAttempt', backref='exam', lazy=True)

class Question(db.Model):
    __tablename__ = 'questions'
    
    question_id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.exam_id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(20), nullable=False)
    points = db.Column(db.Numeric(5, 2), nullable=False)
    display_order = db.Column(db.Integer, nullable=False)
    media_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    

    options = db.relationship('QuestionOption', backref='question', lazy=True)
    answers = db.relationship('Answer', backref='question', lazy=True)
    
    @validates('question_type')
    def validate_question_type(self, key, question_type):
        assert question_type in ['multiple_choice', 'true_false', 'short_answer', 'essay']
        return question_type

class QuestionOption(db.Model):
    __tablename__ = 'question_options'
    
    option_id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.question_id'), nullable=False)
    option_text = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    display_order = db.Column(db.Integer, nullable=False)

class ExamAttempt(db.Model):
    __tablename__ = 'exam_attempts'
    
    attempt_id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.exam_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime)
    submission_time = db.Column(db.DateTime)
    ip_address = db.Column(db.String(50))
    status = db.Column(db.String(20), default='in_progress')
    total_score = db.Column(db.Numeric(5, 2))
    is_auto_submitted = db.Column(db.Boolean, default=False)
    

    answers = db.relationship('Answer', backref='attempt', lazy=True)
    
    @validates('status')
    def validate_status(self, key, status):
        assert status in ['in_progress', 'submitted', 'graded', 'archived']
        return status
    
    def calculate_score(self):
        total = 0
        for answer in self.answers:
            if answer.points_awarded is not None:
                total += answer.points_awarded
        self.total_score = total
        return total

class Answer(db.Model):
    __tablename__ = 'answers'
    
    answer_id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey('exam_attempts.attempt_id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.question_id'), nullable=False)
    answer_text = db.Column(db.Text)
    selected_option_id = db.Column(db.Integer, db.ForeignKey('question_options.option_id'))
    points_awarded = db.Column(db.Numeric(5, 2))
    feedback = db.Column(db.Text)
    graded_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    graded_at = db.Column(db.DateTime)

class ArchivedExam(db.Model):
    __tablename__ = 'archived_exams'
    
    archive_id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer)
    course_id = db.Column(db.Integer)
    exam_name = db.Column(db.String(100))
    exam_data = db.Column(db.Text)  
    archived_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    archived_at = db.Column(db.DateTime, default=datetime.utcnow)
    archive_reason = db.Column(db.String(100))

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    log_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(50))
    entity_id = db.Column(db.Integer)
    old_values = db.Column(db.Text)
    new_values = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Heartbeat(db.Model):
    __tablename__ = 'heartbeats'
    
    heartbeat_id = db.Column(db.Integer, primary_key=True)
    component = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    message = db.Column(db.String(255))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def track_changes(mapper, connection, target):
    if not target.user_id: 
        return
    

    from flask_login import current_user
    if current_user.is_authenticated:
        user_id = current_user.user_id
    else:
        user_id = target.user_id 
    

    old_values = {}
    for attr in db.inspect(target).attrs:
        if attr.history.has_changes():
            old_values[attr.key] = attr.history.deleted[0] if attr.history.deleted else None
    

    audit_log = AuditLog(
        user_id=user_id,
        action='update',
        entity_type=target.__tablename__,
        entity_id=target.id,
        old_values=str(old_values),
        new_values=str({k: getattr(target, k) for k in old_values.keys()}),
        ip_address=request.remote_addr if request else None,
        user_agent=request.headers.get('User-Agent') if request else None
    )
    db.session.add(audit_log)


models = [User, Course, CourseEnrollment, Exam, Question, QuestionOption, ExamAttempt, Answer, ArchivedExam]
for model in models:
    event.listen(model, 'after_update', track_changes)