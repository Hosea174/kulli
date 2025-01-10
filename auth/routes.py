from flask import Blueprint, render_template, redirect, session, url_for, flash, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from app import db, mail
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
        
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists')
            return redirect(url_for('auth.register_user'))
        
        verification_token = str(uuid.uuid4())
        new_user = User(
            email=email,
            name=name,
            phone=phone,
            password=generate_password_hash(password, method='pbkdf2:sha256'),
            verification_token=verification_token
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # Send verification email
        send_verification_email(email, verification_token)
        
        flash('Please check your email to verify your account')
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
        
        verification_token = str(uuid.uuid4())
        new_owner = TruckOwner(
            email=email,
            name=name,
            phone=phone,
            password=generate_password_hash(password, method='pbkdf2:sha256'),
            license_plate=license_plate,
            truck_type=truck_type,
            verification_token=verification_token
        )
        
        db.session.add(new_owner)
        db.session.commit()
        
        # Send verification email
        send_verification_email(email, verification_token)
        
        flash('Please check your email to verify your account')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register_truck_owner.html')

def send_verification_email(email, token):
    msg = Message('Verify your email',
                  sender='hossaena2018@gmail.com',
                  recipients=[email])
    verification_url = url_for('auth.verify_email', token=token, _external=True)
    msg.body = f'Click the following link to verify your email: {verification_url}'
    mail.send(msg)
    print("your verification_url: ")
    print(verification_url)

@auth.route('/verify-email/<token>')
def verify_email(token):
    user = User.query.filter_by(verification_token=token).first()
    owner = TruckOwner.query.filter_by(verification_token=token).first()
    
    if user:
        user.email_verified = True
        user.verification_token = None
        db.session.commit()
        flash('Your email has been verified!')
        return redirect(url_for('auth.login'))
    elif owner:
        owner.email_verified = True
        owner.verification_token = None
        db.session.commit()
        flash('Your email has been verified!')
        return redirect(url_for('auth.login'))
    else:
        flash('Invalid verification token')
        return redirect(url_for('auth.login'))

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user_type = request.form.get('user_type')

        user = None
        if user_type == 'user':
            user = User.query.filter_by(email=email).first()
        elif user_type == 'truck_owner':
            user = TruckOwner.query.filter_by(email=email).first()
            
        if user and check_password_hash(user.password, password):
            if not user.email_verified:
                flash('Please verify your email first.')
                return redirect(url_for('auth.login'))
            
            login_user(user)
            session['user_type'] = user_type
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