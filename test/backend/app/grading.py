from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models import Exam, ExamAttempt, Answer, Question, QuestionOption, AuditLog
from app import db
from app.forms import GradingForm
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from app.utils import role_required

grading = Blueprint('grading', __name__)

@grading.route('/exams/<int:exam_id>/attempts')
@login_required
@role_required(['admin', 'professor'])
def list_attempts(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    

    if current_user.role != 'admin':
        enrollment = CourseEnrollment.query.filter_by(
            course_id=exam.course_id,
            user_id=current_user.user_id,
            role='professor'
        ).first()
        if not enrollment:
            flash('You are not authorized to grade exams for this course.', 'danger')
            return redirect(url_for('courses.list_courses'))

    attempts = ExamAttempt.query.filter_by(exam_id=exam_id).order_by(ExamAttempt.submission_time.desc()).all()
    
    return render_template('grading/list_attempts.html', exam=exam, attempts=attempts)

@grading.route('/attempts/<int:attempt_id>/grade', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'professor'])
def grade_attempt(attempt_id):
    attempt = ExamAttempt.query.get_or_404(attempt_id)
    exam = attempt.exam
    

    if current_user.role != 'admin':
        enrollment = CourseEnrollment.query.filter_by(
            course_id=exam.course_id,
            user_id=current_user.user_id,
            role='professor'
        ).first()
        if not enrollment:
            flash('You are not authorized to grade this attempt.', 'danger')
            return redirect(url_for('courses.list_courses'))
    

    if attempt.status not in ['submitted', 'graded']:
        flash('This attempt is not ready for grading.', 'info')
        return redirect(url_for('grading.list_attempts', exam_id=exam.exam_id))
    

    questions = []
    for question in exam.questions:
        answer = Answer.query.filter_by(
            attempt_id=attempt.attempt_id,
            question_id=question.question_id
        ).first()
        
        if question.question_type in ['multiple_choice', 'true_false']:
            options = QuestionOption.query.filter_by(
                question_id=question.question_id
            ).order_by(QuestionOption.display_order).all()
        else:
            options = None
        
        questions.append({
            'question': question,
            'answer': answer,
            'options': options
        })
    
    if request.method == 'POST':
        try:
            total_score = 0
            
            for question in questions:
                answer = question['answer']
                points_key = f'points_{answer.answer_id}'
                feedback_key = f'feedback_{answer.answer_id}'
                
                if points_key in request.form:
                    points = float(request.form[points_key])
                    feedback = request.form.get(feedback_key, '')
                    
                    if points > question['question'].points:
                        flash(f'Points cannot exceed the maximum for each question.', 'danger')
                        return redirect(url_for('grading.grade_attempt', attempt_id=attempt_id))
                    
                    answer.points_awarded = points
                    answer.feedback = feedback
                    answer.graded_by = current_user.user_id
                    answer.graded_at = datetime.utcnow()
                    
                    total_score += points
            
            attempt.status = 'graded'
            attempt.total_score = total_score
            db.session.commit()
            
            audit_log = AuditLog(
                user_id=current_user.user_id,
                action='grade_exam',
                entity_type='exam_attempt',
                entity_id=attempt.attempt_id,
                new_values=str({
                    'total_score': total_score,
                    'status': 'graded'
                }),
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit_log)
            db.session.commit()
            
            flash('Exam graded successfully!', 'success')
            return redirect(url_for('grading.list_attempts', exam_id=exam.exam_id))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while grading: {str(e)}', 'danger')
    
    return render_template('grading/grade.html', 
                         attempt=attempt,
                         exam=exam,
                         questions=questions)

@grading.route('/attempts/<int:attempt_id>/auto-grade')
@login_required
@role_required(['admin', 'professor'])
def auto_grade_attempt(attempt_id):
    attempt = ExamAttempt.query.get_or_404(attempt_id)
    exam = attempt.exam
    
    if current_user.role != 'admin':
        enrollment = CourseEnrollment.query.filter_by(
            course_id=exam.course_id,
            user_id=current_user.user_id,
            role='professor'
        ).first()
        if not enrollment:
            flash('You are not authorized to grade this attempt.', 'danger')
            return redirect(url_for('courses.list_courses'))
    
    if attempt.status not in ['submitted', 'graded']:
        flash('This attempt is not ready for grading.', 'info')
        return redirect(url_for('grading.list_attempts', exam_id=exam.exam_id))
    
    try:
        total_score = 0
        

        for question in exam.questions:
            answer = Answer.query.filter_by(
                attempt_id=attempt.attempt_id,
                question_id=question.question_id
            ).first()
            
            if not answer:
                continue
            

            if question.question_type in ['multiple_choice', 'true_false']:
                if answer.selected_option_id:
                    selected_option = QuestionOption.query.get(answer.selected_option_id)
                    if selected_option and selected_option.is_correct:
                        answer.points_awarded = question.points
                    else:
                        answer.points_awarded = 0
                else:
                    answer.points_awarded = 0
                
                answer.graded_by = current_user.user_id
                answer.graded_at = datetime.utcnow()
                total_score += answer.points_awarded

        attempt.status = 'graded'
        attempt.total_score = total_score
        db.session.commit()

        audit_log = AuditLog(
            user_id=current_user.user_id,
            action='auto_grade_exam',
            entity_type='exam_attempt',
            entity_id=attempt.attempt_id,
            new_values=str({
                'total_score': total_score,
                'status': 'graded'
            }),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit_log)
        db.session.commit()
        
        flash('Auto-grading completed successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred during auto-grading: {str(e)}', 'danger')
    
    return redirect(url_for('grading.list_attempts', exam_id=exam.exam_id))