from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User, AuditLog
from app import db, login_manager
from app import LoginForm, RegistrationForm
from datetime import datetime
import pytz

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('Your account has been deactivated.', 'danger')
                return redirect(url_for('auth.login'))
            
            login_user(user, remember=form.remember.data)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Log the login event
            audit_log = AuditLog(
                user_id=user.user_id,
                action='login',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit_log)
            db.session.commit()
            
            next_page = request.args.get('next')
            flash('You have been logged in!', 'success')
            return redirect(next_page or url_for('main.index'))
        else:
            # Log failed login attempt
            audit_log = AuditLog(
                action='failed_login',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                message=f'Failed login attempt for username: {form.username.data}'
            )
            db.session.add(audit_log)
            db.session.commit()
            
            flash('Login unsuccessful. Please check username and password.', 'danger')
    
    return render_template('auth/login.html', title='Login', form=form)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter((User.username == form.username.data) | 
                                         (User.email == form.email.data)).first()
        if existing_user:
            flash('Username or email already exists.', 'danger')
            return redirect(url_for('auth.register'))

        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            role='student'
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()

        audit_log = AuditLog(
            user_id=user.user_id,
            action='register',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit_log)
        db.session.commit()
        
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', title='Register', form=form)

@auth.route('/logout')
@login_required
def logout():

    audit_log = AuditLog(
        user_id=current_user.user_id,
        action='logout',
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )
    db.session.add(audit_log)
    db.session.commit()
    
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))