from functools import wraps
from flask import abort, request, current_app
from flask_login import current_user
from app.models import AuditLog, Heartbeat, db, Exam, ExamAttempt, Answer, ArchivedExam
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import pytz
import json
from azure.storage.blob import BlobServiceClient
import os
from app.config import Config
from sqlalchemy import and_


scheduler = BackgroundScheduler()

def role_required(roles):
    """Decorator to check if user has required role(s)."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                audit_log = AuditLog(
                    user_id=current_user.user_id if current_user.is_authenticated else None,
                    action='unauthorized_access',
                    entity_type='route',
                    entity_id=f.__name__,
                    message=f'Attempted access to {request.path} requiring roles: {roles}',
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent')
                )
                db.session.add(audit_log)
                db.session.commit()
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def archive_exam(exam_id, archived_by, reason):
    """Archive an exam and its results."""
    try:
        exam = Exam.query.get(exam_id)
        if not exam:
            return False, "Exam not found"
        

        attempts = ExamAttempt.query.filter_by(
            exam_id=exam_id,
            status='graded'
        ).all()
        

        exam_data = {
            'exam_info': {
                'exam_id': exam.exam_id,
                'exam_name': exam.exam_name,
                'course_id': exam.course_id,
                'created_at': exam.created_at.isoformat(),
            },
            'attempts': []
        }
        
        for attempt in attempts:
            attempt_data = {
                'attempt_id': attempt.attempt_id,
                'user_id': attempt.user_id,
                'start_time': attempt.start_time.isoformat(),
                'submission_time': attempt.submission_time.isoformat() if attempt.submission_time else None,
                'total_score': float(attempt.total_score) if attempt.total_score else None,
                'answers': []
            }
            
            answers = Answer.query.filter_by(attempt_id=attempt.attempt_id).all()
            for answer in answers:
                answer_data = {
                    'question_id': answer.question_id,
                    'answer_text': answer.answer_text,
                    'selected_option_id': answer.selected_option_id,
                    'points_awarded': float(answer.points_awarded) if answer.points_awarded else None,
                    'feedback': answer.feedback,
                    'graded_at': answer.graded_at.isoformat() if answer.graded_at else None
                }
                attempt_data['answers'].append(answer_data)
            
            exam_data['attempts'].append(attempt_data)

        archive = ArchivedExam(
            exam_id=exam.exam_id,
            course_id=exam.course_id,
            exam_name=exam.exam_name,
            exam_data=json.dumps(exam_data),
            archived_by=archived_by,
            archive_reason=reason
        )
        db.session.add(archive)
        

        exam.is_active = False
        db.session.commit()

        audit_log = AuditLog(
            user_id=archived_by,
            action='archive_exam',
            entity_type='exam',
            entity_id=exam.exam_id,
            new_values=str({
                'archive_id': archive.archive_id,
                'reason': reason
            }),
            ip_address=request.remote_addr if request else None,
            user_agent=request.headers.get('User-Agent') if request else None
        )
        db.session.add(audit_log)
        db.session.commit()
        
        return True, "Exam archived successfully"
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error archiving exam: {str(e)}")
        return False, str(e)

def auto_archive_old_exams():
    """Automatically archive exams older than configured days."""
    with scheduler.app.app_context():
        try:
            days = current_app.config.get('EXAM_ARCHIVE_DAYS', 30)
            archive_date = datetime.utcnow() - timedelta(days=days)
            
            exams_to_archive = Exam.query.filter(
                and_(
                    Exam.available_to < archive_date,
                    Exam.is_active == True
                )
            ).all()
            
            for exam in exams_to_archive:
                archive_exam(exam.exam_id, 1, f"Automatic archive after {days} days")
                
            current_app.logger.info(f"Auto-archived {len(exams_to_archive)} exams")
        except Exception as e:
            current_app.logger.error(f"Error in auto_archive_old_exams: {str(e)}")

def check_server_heartbeat():
    """Check server health status."""
    try:
        heartbeat = Heartbeat(
            component='server',
            status='up',
            message='Server is running'
        )
        db.session.add(heartbeat)
        db.session.commit()
        return True
    except Exception as e:
        heartbeat = Heartbeat(
            component='server',
            status='down',
            message=f'Server error: {str(e)}'
        )
        db.session.add(heartbeat)
        db.session.commit()
        return False

def check_database_heartbeat():
    """Check database health status."""
    try:
        result = db.session.execute('SELECT 1').fetchone()
        if result and result[0] == 1:
            heartbeat = Heartbeat(
                component='database',
                status='up',
                message='Database is responsive'
            )
            db.session.add(heartbeat)
            db.session.commit()
            return True
    except Exception as e:
        heartbeat = Heartbeat(
            component='database',
            status='down',
            message=f'Database error: {str(e)}'
        )
        db.session.add(heartbeat)
        db.session.commit()
        return False

def check_client_heartbeat(client_ip):
    """Check client health status."""
    try:
        heartbeat = Heartbeat(
            component='client',
            status='up',
            message=f'Client {client_ip} last seen'
        )
        db.session.add(heartbeat)
        db.session.commit()
        return True
    except Exception as e:
        heartbeat = Heartbeat(
            component='client',
            status='down',
            message=f'Client error: {str(e)}'
        )
        db.session.add(heartbeat)
        db.session.commit()
        return False

def init_scheduled_tasks(app):
    """Initialize all scheduled background tasks."""
    scheduler.app = app

    scheduler.add_job(
        func=check_server_heartbeat,
        trigger=IntervalTrigger(minutes=5),
        id='server_heartbeat',
        name='Check server status every 5 minutes',
        replace_existing=True
    )
    
    scheduler.add_job(
        func=check_database_heartbeat,
        trigger=IntervalTrigger(minutes=5),
        id='database_heartbeat',
        name='Check database status every 5 minutes',
        replace_existing=True
    )
    

    scheduler.add_job(
        func=auto_archive_old_exams,
        trigger='cron',
        hour=2,
        minute=0,
        id='auto_archive_exams',
        name='Auto-archive old exams daily at 2 AM',
        replace_existing=True
    )
    
    
    scheduler.start()

def upload_to_azure_blob(file_stream, filename, content_type):
    """Upload a file to Azure Blob Storage."""
    try:
        blob_service_client = BlobServiceClient.from_connection_string(
            current_app.config['AZURE_STORAGE_CONNECTION_STRING'])
        blob_client = blob_service_client.get_blob_client(
            container=current_app.config['AZURE_STORAGE_CONTAINER'],
            blob=filename)
        
        blob_client.upload_blob(file_stream, content_type=content_type)
        return blob_client.url
    except Exception as e:
        current_app.logger.error(f"Error uploading to Azure Blob: {str(e)}")
        return None