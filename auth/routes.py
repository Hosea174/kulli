from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from extensions import db, mail
from models import User, TruckOwner
import uuid
from flask_mail import Message

auth = Blueprint('auth', __name__)

@auth.route('/register/user', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        phone = request.form.get('phone')
        password = request.form.get('password')
        
        print(f"Registration attempt - Email: {email}, Name: {name}")  # Debug log
        
        user = User.query.filter_by(email=email).first()
        if user:
            print(f"User already exists: {email}")  # Debug log
            flash('Email already exists')
            return redirect(url_for('auth.register_user'))
        
        verification_token = str(uuid.uuid4()) if current_app.config['EMAIL_VERIFICATION_REQUIRED'] else None
        new_user = User(
            email=email,
            name=name,
            phone=phone,
            password=generate_password_hash(password, method='pbkdf2:sha256'),
            email_verified=not current_app.config['EMAIL_VERIFICATION_REQUIRED'],
            verification_token=verification_token
        )
        
        db.session.add(new_user)
        db.session.commit()
        print(f"New user created: {new_user.id}")  # Debug log
        
        flash('Registration successful! Please login.')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register_user.html')

@auth.route('/register/truck-owner', methods=['GET', 'POST'])
def register_truck_owner():
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        phone = request.form.get('phone')
        password = request.form.get('password')
        license_plate = request.form.get('license_plate')
        truck_type = request.form.get('truck_type')
        
        owner = TruckOwner.query.filter_by(email=email).first()
        if owner:
            flash('Email already exists')
            return redirect(url_for('auth.register_truck_owner'))
        
        verification_token = str(uuid.uuid4()) if current_app.config['EMAIL_VERIFICATION_REQUIRED'] else None
        new_owner = TruckOwner(
            email=email,
            name=name,
            phone=phone,
            password=generate_password_hash(password, method='pbkdf2:sha256'),
            license_plate=license_plate,
            truck_type=truck_type,
            email_verified=not current_app.config['EMAIL_VERIFICATION_REQUIRED'],
            verification_token=verification_token
        )
        
        db.session.add(new_owner)
        db.session.commit()
        
        flash('Registration successful! Please login.')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register_truck_owner.html')

def send_verification_email(email, token):
    try:
        print(f"Attempting to send verification email to {email}")
        print(f"Mail server config: {current_app.config['MAIL_SERVER']}:{current_app.config['MAIL_PORT']}")
        print(f"Mail username: {current_app.config['MAIL_USERNAME']}")
        
        msg = Message('Verify your email',
                    sender='l.mateev@scm.bg',
                    recipients=[email])
        verification_url = url_for('auth.verify_email', token=token, _external=True)
        msg.body = f'Click the following link to verify your email: {verification_url}'
        
        print(f"Message created, attempting to connect to SMTP server...")
        
        # Test SMTP connection
        with mail.connect() as conn:
            print("SMTP connection successful!")
            print(f"Sending email to {email}...")
            conn.send(msg)
            print(f"Verification email sent to {email} with token: {token}")
            return True
            
    except Exception as e:
        print(f"Failed to send verification email: {str(e)}")
        import traceback
        traceback.print_exc()
        flash('We encountered an issue sending the verification email. Please try again later.')
        return False

@auth.route('/verify-email/<token>')
def verify_email(token):
    print(f"Verification attempt with token: {token}")  # Debug log
    
    user = User.query.filter_by(verification_token=token).first()
    owner = TruckOwner.query.filter_by(verification_token=token).first()
    
    if user:
        print(f"Found user to verify: {user.email}")  # Debug log
        user.email_verified = True
        user.verification_token = None
        db.session.commit()
        flash('Your email has been verified!')
        return redirect(url_for('auth.login'))
    elif owner:
        print(f"Found truck owner to verify: {owner.email}")  # Debug log
        owner.email_verified = True
        owner.verification_token = None
        db.session.commit()
        flash('Your email has been verified!')
        return redirect(url_for('auth.login'))
    else:
        print("Invalid verification token")  # Debug log
        flash('Invalid verification token')
        return redirect(url_for('auth.login'))

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user_type = request.form.get('user_type')
        
        print(f"Login attempt - Email: {email}, Type: {user_type}")  # Debug log

        user = None
        if user_type == 'user':
            user = User.query.filter_by(email=email).first()
            print(f"Found user: {user}")  # Debug log
        elif user_type == 'truck_owner':
            user = TruckOwner.query.filter_by(email=email).first()
            print(f"Found truck owner: {user}")  # Debug log
            
        if user:
            print(f"Password check: {check_password_hash(user.password, password)}")  # Debug log
            print(f"Email verified: {user.email_verified}")  # Debug log
            
        # Check if password verification is required
        password_valid = True
        if current_app.config['PASSWORD_CHECK_REQUIRED']:
            password_valid = check_password_hash(user.password, password)
            print(f"Password check required. Result: {password_valid}")  # Debug log

        # Check if user type verification is required
        user_type_valid = True
        if current_app.config['USER_TYPE_CHECK_REQUIRED']:
            user_type_valid = (user_type == 'user' and isinstance(user, User)) or \
                            (user_type == 'truck_owner' and isinstance(user, TruckOwner))
            print(f"User type check required. Result: {user_type_valid}")  # Debug log

        # Check email verification if required
        email_verified = True
        if current_app.config['EMAIL_VERIFICATION_REQUIRED']:
            email_verified = user.email_verified
            print(f"Email verification required. Result: {email_verified}")  # Debug log

        if user and password_valid and user_type_valid and email_verified:
            login_user(user)
            print(f"Login successful for: {email}")  # Debug log
            if user_type == 'user':
                return redirect(url_for('user_dashboard'))
            elif user_type == 'truck_owner':
                return redirect(url_for('truck_owner_dashboard'))
                
        flash('Please check your login details and try again.')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@auth.route('/test-smtp')
def test_smtp():
    try:
        with mail.connect() as conn:
            print("SMTP connection successful!")
            return "SMTP connection successful!", 200
    except Exception as e:
        print(f"SMTP connection failed: {str(e)}")
        return f"SMTP connection failed: {str(e)}", 500
