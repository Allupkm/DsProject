from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models import Course, CourseEnrollment, User, AuditLog
from app import db
from app import CourseForm, EnrollmentForm
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from app.utils import role_required

courses = Blueprint('courses', __name__)

@courses.route('/courses')
@login_required
def list_courses():
    if current_user.role == 'admin':
        courses = Course.query.filter_by(is_active=True).all()
    elif current_user.role == 'professor':
        courses = Course.query.join(CourseEnrollment).filter(
            CourseEnrollment.user_id == current_user.user_id,
            CourseEnrollment.role == 'professor',
            Course.is_active == True
        ).all()
    else:
        courses = Course.query.join(CourseEnrollment).filter(
            CourseEnrollment.user_id == current_user.user_id,
            Course.is_active == True
        ).all()
    
    return render_template('courses/list.html', courses=courses)

@courses.route('/courses/create', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'professor'])
def create_course():
    form = CourseForm()
    
    if form.validate_on_submit():
        try:
            course = Course(
                course_code=form.course_code.data,
                course_name=form.course_name.data,
                description=form.description.data,
                created_by=current_user.user_id
            )
            db.session.add(course)
            db.session.commit()
            
            enrollment = CourseEnrollment(
                course_id=course.course_id,
                user_id=current_user.user_id,
                role='professor'
            )
            db.session.add(enrollment)
            db.session.commit()
            audit_log = AuditLog(
                user_id=current_user.user_id,
                action='create_course',
                entity_type='course',
                entity_id=course.course_id,
                new_values=str({
                    'course_code': course.course_code,
                    'course_name': course.course_name
                }),
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit_log)
            db.session.commit()
            
            flash('Course created successfully!', 'success')
            return redirect(url_for('courses.list_courses'))
        except IntegrityError:
            db.session.rollback()
            flash('Course code already exists.', 'danger')
    
    return render_template('courses/create.html', form=form)

@courses.route('/courses/<int:course_id>/enroll', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'professor'])
def enroll_student(course_id):
    course = Course.query.get_or_404(course_id)
    
    if current_user.role != 'admin':
        enrollment = CourseEnrollment.query.filter_by(
            course_id=course_id,
            user_id=current_user.user_id,
            role='professor'
        ).first()
        if not enrollment:
            flash('You are not authorized to enroll students in this course.', 'danger')
            return redirect(url_for('courses.list_courses'))
    
    form = EnrollmentForm()

    form.user_id.choices = [(u.user_id, f"{u.first_name} {u.last_name} ({u.username})") 
                           for u in User.query.filter_by(role='student', is_active=True).all()]
    
    if form.validate_on_submit():
        try:
            existing = CourseEnrollment.query.filter_by(
                course_id=course_id,
                user_id=form.user_id.data
            ).first()
            
            if existing:
                flash('This student is already enrolled in the course.', 'warning')
            else:
                enrollment = CourseEnrollment(
                    course_id=course_id,
                    user_id=form.user_id.data,
                    role='student'
                )
                db.session.add(enrollment)
                db.session.commit()
                
                audit_log = AuditLog(
                    user_id=current_user.user_id,
                    action='enroll_student',
                    entity_type='enrollment',
                    entity_id=enrollment.enrollment_id,
                    new_values=str({
                        'course_id': course_id,
                        'user_id': form.user_id.data,
                        'role': 'student'
                    }),
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent')
                )
                db.session.add(audit_log)
                db.session.commit()
                
                flash('Student enrolled successfully!', 'success')
                return redirect(url_for('courses.view_course', course_id=course_id))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while enrolling the student.', 'danger')
    
    return render_template('courses/enroll.html', form=form, course=course)

@courses.route('/courses/<int:course_id>')
@login_required
def view_course(course_id):
    course = Course.query.get_or_404(course_id)
    
    if current_user.role == 'admin':
        pass
    else:
        enrollment = CourseEnrollment.query.filter_by(
            course_id=course_id,
            user_id=current_user.user_id
        ).first()
        if not enrollment:
            flash('You are not enrolled in this course.', 'danger')
            return redirect(url_for('courses.list_courses'))
    
    enrollments = CourseEnrollment.query.filter_by(course_id=course_id).all()

    if current_user.role == 'admin':
        exams = course.exams
    elif current_user.role == 'professor':
        professor_enrollment = CourseEnrollment.query.filter_by(
            course_id=course_id,
            user_id=current_user.user_id,
            role='professor'
        ).first()
        if professor_enrollment:
            exams = course.exams
        else:
            exams = []
    else:
        exams = [exam for exam in course.exams if exam.is_published]
    
    return render_template('courses/view.html', 
                         course=course, 
                         enrollments=enrollments, 
                         exams=exams)