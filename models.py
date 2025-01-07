from extensions import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(100), unique=True)
    trips = db.relationship('Trip', backref='user', lazy=True)

class TruckOwner(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email_verified = db.Column(db.Boolean, default=False)
    license_plate = db.Column(db.String(20), nullable=False)
    truck_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='offline')  # online, on_trip, offline
    verification_token = db.Column(db.String(100), unique=True)
    trips = db.relationship('Trip', backref='truck_owner', lazy=True)

class Trip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    truck_owner_id = db.Column(db.Integer, db.ForeignKey('truck_owner.id'), nullable=True)
    pickup_location = db.Column(db.String(200), nullable=False)
    destination = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default='waiting')  # waiting, truck_assigned, started, completed, canceled
    est_duration = db.Column(db.Float)  # In hours
    est_distance = db.Column(db.Float)  # In kilometers
    est_price = db.Column(db.Float)
    actual_duration = db.Column(db.Float, default=None)  # Initially NULL
    actual_distance = db.Column(db.Float, default=None)  # Initially NULL
    actual_price = db.Column(db.Float, default=None)  # Initially NULL
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
