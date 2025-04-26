from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models import Exam, Course, Question, QuestionOption, ExamAttempt, Answer, AuditLog
from app import db
from app.forms import ExamForm, QuestionForm, OptionForm
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
from app.utils import role_required, archive_exam
import json

exams = Blueprint('exams', __name__)

@exams.route('/courses/<int:course_id>/exams/create', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'professor'])
def create_exam(course_id):
    course = Course.query.get_or_404(course_id)
    
    if current_user.role != 'admin':
        enrollment = CourseEnrollment.query.filter_by(
            course_id=course_id,
            user_id=current_user.user_id,
            role='professor'
        ).first()
        if not enrollment:
            flash('You are not authorized to create exams for this course.', 'danger')
            return redirect(url_for('courses.view_course', course_id=course_id))
    
    form = ExamForm()
    
    if form.validate_on_submit():
        try:
            exam = Exam(
                course_id=course_id,
                exam_name=form.exam_name.data,
                description=form.description.data,
                time_limit_minutes=form.time_limit_minutes.data,
                available_from=form.available_from.data,
                available_to=form.available_to.data,
                is_published=form.is_published.data,
                created_by=current_user.user_id,
                ip_restriction=form.ip_restriction.data,
                browser_lockdown=form.browser_lockdown.data,
                show_results_immediately=form.show_results_immediately.data,
                show_results_after=form.show_results_after.data
            )
            db.session.add(exam)
            db.session.commit()
            
            audit_log = AuditLog(
                user_id=current_user.user_id,
                action='create_exam',
                entity_type='exam',
                entity_id=exam.exam_id,
                new_values=str({
                    'course_id': course_id,
                    'exam_name': exam.exam_name
                }),
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit_log)
            db.session.commit()
            
            flash('Exam created successfully! Now add questions.', 'success')
            return redirect(url_for('exams.manage_questions', exam_id=exam.exam_id))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating the exam.', 'danger')
    
    return render_template('exams/create.html', form=form, course=course)

@exams.route('/exams/<int:exam_id>/questions', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'professor'])
def manage_questions(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    

    if current_user.role != 'admin':
        enrollment = CourseEnrollment.query.filter_by(
            course_id=exam.course_id,
            user_id=current_user.user_id,
            role='professor'
        ).first()
        if not enrollment:
            flash('You are not authorized to manage this exam.', 'danger')
            return redirect(url_for('courses.view_course', course_id=exam.course_id))
    
    questions = Question.query.filter_by(exam_id=exam_id).order_by(Question.display_order).all()
    
    question_form = QuestionForm()
    
    if question_form.validate_on_submit():
        try:
            question = Question(
                exam_id=exam_id,
                question_text=question_form.question_text.data,
                question_type=question_form.question_type.data,
                points=question_form.points.data,
                display_order=question_form.display_order.data,
                media_url=question_form.media_url.data
            )
            db.session.add(question)
            db.session.commit()
            
            audit_log = AuditLog(
                user_id=current_user.user_id,
                action='add_question',
                entity_type='question',
                entity_id=question.question_id,
                new_values=str({
                    'exam_id': exam_id,
                    'question_text': question.question_text[:50] + '...' if len(question.question_text) > 50 else question.question_text,
                    'question_type': question.question_type
                }),
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit_log)
            db.session.commit()
            
            flash('Question added successfully!', 'success')
            return redirect(url_for('exams.manage_questions', exam_id=exam_id))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while adding the question.', 'danger')
    
    return render_template('exams/manage_questions.html', 
                         exam=exam, 
                         questions=questions, 
                         question_form=question_form)

@exams.route('/questions/<int:question_id>/options', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'professor'])
def manage_options(question_id):
    question = Question.query.get_or_404(question_id)
    exam = question.exam

    if current_user.role != 'admin':
        enrollment = CourseEnrollment.query.filter_by(
            course_id=exam.course_id,
            user_id=current_user.user_id,
            role='professor'
        ).first()
        if not enrollment:
            flash('You are not authorized to manage this question.', 'danger')
            return redirect(url_for('courses.view_course', course_id=exam.course_id))
    
    options = QuestionOption.query.filter_by(question_id=question_id).order_by(QuestionOption.display_order).all()

    option_form = OptionForm()
    
    if option_form.validate_on_submit():
        try:
            option = QuestionOption(
                question_id=question_id,
                option_text=option_form.option_text.data,
                is_correct=option_form.is_correct.data,
                display_order=option_form.display_order.data
            )
            db.session.add(option)
            db.session.commit()

            audit_log = AuditLog(
                user_id=current_user.user_id,
                action='add_option',
                entity_type='option',
                entity_id=option.option_id,
                new_values=str({
                    'question_id': question_id,
                    'option_text': option.option_text[:50] + '...' if len(option.option_text) > 50 else option.option_text,
                    'is_correct': option.is_correct
                }),
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit_log)
            db.session.commit()
            
            flash('Option added successfully!', 'success')
            return redirect(url_for('exams.manage_options', question_id=question_id))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while adding the option.', 'danger')
    
    return render_template('exams/manage_options.html', 
                         question=question, 
                         exam=exam,
                         options=options, 
                         option_form=option_form)

@exams.route('/exams/<int:exam_id>/take', methods=['GET', 'POST'])
@login_required
@role_required(['student'])
def take_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)

    enrollment = CourseEnrollment.query.filter_by(
        course_id=exam.course_id,
        user_id=current_user.user_id
    ).first()
    if not enrollment:
        flash('You are not enrolled in this course.', 'danger')
        return redirect(url_for('courses.list_courses'))
  
    if not exam.is_published:
        flash('This exam is not yet published.', 'danger')
        return redirect(url_for('courses.view_course', course_id=exam.course_id))
    
    now = datetime.utcnow()
    if exam.available_from and now < exam.available_from:
        flash('This exam is not yet available.', 'danger')
        return redirect(url_for('courses.view_course', course_id=exam.course_id))
    
    if exam.available_to and now > exam.available_to:
        flash('This exam is no longer available.', 'danger')
        return redirect(url_for('courses.view_course', course_id=exam.course_id))
    

    if exam.ip_restriction and request.remote_addr not in exam.ip_restriction.split(','):
        flash('You cannot take this exam from your current location.', 'danger')
        return redirect(url_for('courses.view_course', course_id=exam.course_id))
    

    attempt = ExamAttempt.query.filter_by(
        exam_id=exam_id,
        user_id=current_user.user_id
    ).order_by(ExamAttempt.start_time.desc()).first()
    
    if not attempt or attempt.status == 'submitted' or attempt.status == 'graded':

        attempt = ExamAttempt(
            exam_id=exam_id,
            user_id=current_user.user_id,
            start_time=datetime.utcnow(),
            ip_address=request.remote_addr,
            status='in_progress'
        )
        db.session.add(attempt)
        db.session.commit()
        

        audit_log = AuditLog(
            user_id=current_user.user_id,
            action='start_exam',
            entity_type='exam_attempt',
            entity_id=attempt.attempt_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit_log)
        db.session.commit()
    elif attempt.status == 'in_progress':

        if exam.time_limit_minutes:
            time_elapsed = datetime.utcnow() - attempt.start_time
            if time_elapsed.total_seconds() > exam.time_limit_minutes * 60:
                attempt.status = 'submitted'
                attempt.submission_time = datetime.utcnow()
                attempt.is_auto_submitted = True
                db.session.commit()
                
                flash('Your time has expired and the exam was automatically submitted.', 'info')
                return redirect(url_for('exams.view_results', attempt_id=attempt.attempt_id))

    questions = Question.query.filter_by(exam_id=exam_id).order_by(Question.display_order).all()
    for question in questions:
        if question.question_type in ['multiple_choice', 'true_false']:
            question.options = QuestionOption.query.filter_by(
                question_id=question.question_id
            ).order_by(QuestionOption.display_order).all()
        question.existing_answer = Answer.query.filter_by(
            attempt_id=attempt.attempt_id,
            question_id=question.question_id
        ).first()
    remaining_time = None
    if exam.time_limit_minutes:
        time_elapsed = datetime.utcnow() - attempt.start_time
        remaining_seconds = exam.time_limit_minutes * 60 - time_elapsed.total_seconds()
        remaining_time = max(0, remaining_seconds)
    
    return render_template('exams/take.html', 
                         exam=exam, 
                         attempt=attempt,
                         questions=questions,
                         remaining_time=remaining_time)

@exams.route('/attempts/<int:attempt_id>/submit', methods=['POST'])
@login_required
def submit_exam(attempt_id):
    attempt = ExamAttempt.query.get_or_404(attempt_id)
    
    if attempt.user_id != current_user.user_id:
        flash('You are not authorized to submit this attempt.', 'danger')
        return redirect(url_for('courses.list_courses'))

    if attempt.status != 'in_progress':
        flash('This attempt has already been submitted.', 'info')
        return redirect(url_for('exams.view_results', attempt_id=attempt_id))

    exam = attempt.exam
    questions = exam.questions
    
    for question in questions:
        answer_key = f'question_{question.question_id}'
        
        if answer_key in request.form or answer_key in request.files:
            existing_answer = Answer.query.filter_by(
                attempt_id=attempt.attempt_id,
                question_id=question.question_id
            ).first()
            
            if not existing_answer:
                existing_answer = Answer(
                    attempt_id=attempt.attempt_id,
                    question_id=question.question_id
                )
                db.session.add(existing_answer)

            if question.question_type in ['multiple_choice', 'true_false']:
                selected_option_id = request.form.get(answer_key)
                if selected_option_id:
                    existing_answer.selected_option_id = int(selected_option_id)
            else:
                answer_text = request.form.get(answer_key)
                if answer_text:
                    existing_answer.answer_text = answer_text
            
            db.session.commit()

    attempt.status = 'submitted'
    attempt.submission_time = datetime.utcnow()
    db.session.commit()
    
    audit_log = AuditLog(
        user_id=current_user.user_id,
        action='submit_exam',
        entity_type='exam_attempt',
        entity_id=attempt.attempt_id,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )
    db.session.add(audit_log)
    db.session.commit()
    
    flash('Exam submitted successfully!', 'success')
    return redirect(url_for('exams.view_results', attempt_id=attempt_id))

@exams.route('/attempts/<int:attempt_id>/results')
@login_required
def view_results(attempt_id):
    attempt = ExamAttempt.query.get_or_404(attempt_id)
    exam = attempt.exam
    

    if attempt.user_id != current_user.user_id and current_user.role not in ['admin', 'professor']:
        flash('You are not authorized to view these results.', 'danger')
        return redirect(url_for('courses.list_courses'))
    

    if current_user.role in ['admin', 'professor'] and attempt.user_id != current_user.user_id:
        if current_user.role == 'professor':
            enrollment = CourseEnrollment.query.filter_by(
                course_id=exam.course_id,
                user_id=current_user.user_id,
                role='professor'
            ).first()
            if not enrollment:
                flash('You are not authorized to view these results.', 'danger')
                return redirect(url_for('courses.list_courses'))
    

    now = datetime.utcnow()
    show_results = False
    
    if current_user.role in ['admin', 'professor']:
        show_results = True
    elif exam.show_results_immediately:
        show_results = True
    elif exam.show_results_after and now >= exam.show_results_after:
        show_results = True
    elif attempt.status == 'graded':
        show_results = True
    
    if not show_results:
        flash('Results are not yet available for this exam.', 'info')
        return redirect(url_for('courses.view_course', course_id=exam.course_id))
    

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
            
            correct_options = [opt for opt in options if opt.is_correct]
        else:
            options = None
            correct_options = None
        
        questions.append({
            'question': question,
            'answer': answer,
            'options': options,
            'correct_options': correct_options
        })
    
    return render_template('exams/results.html', 
                         attempt=attempt,
                         exam=exam,
                         questions=questions,
                         now=now)

@exams.route('/exams/<int:exam_id>/archive', methods=['POST'])
@login_required
@role_required(['admin', 'professor'])
def archive_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    

    if current_user.role != 'admin':
        enrollment = CourseEnrollment.query.filter_by(
            course_id=exam.course_id,
            user_id=current_user.user_id,
            role='professor'
        ).first()
        if not enrollment:
            flash('You are not authorized to archive this exam.', 'danger')
            return redirect(url_for('courses.view_course', course_id=exam.course_id))
    

    success, message = archive_exam(exam_id, current_user.user_id, 'Manual archive by professor')
    
    if success:
        flash('Exam archived successfully!', 'success')
    else:
        flash(f'Error archiving exam: {message}', 'danger')
    
    return redirect(url_for('courses.view_course', course_id=exam.course_id))