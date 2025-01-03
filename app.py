from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, login_required
from flask_mail import Mail
import os
from dotenv import load_dotenv
from flask_login import LoginManager
from crud import get_user_trips, get_waiting_trips, update_trip_status
from extensions import db
from models import User, TruckOwner

# Load environment variables
load_dotenv()


# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(BASE_DIR, "instance/truck_delivery.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
login_manager = LoginManager(app)
mail = Mail(app)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    # Try to load user first, then truck owner
    user = User.query.get(int(user_id))
    if user:
        return user
    return TruckOwner.query.get(int(user_id))

# Register blueprint
from auth.routes import auth as auth_blueprint
app.register_blueprint(auth_blueprint)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/user/dashboard')
@login_required
def user_dashboard():
    trips = get_user_trips(current_user.id)
    return render_template('user_dashboard.html', trips=trips)

@app.route('/truck-owner/dashboard', methods=['GET', 'POST'])
@login_required
def truck_owner_dashboard():
    if request.method == 'POST':
        trip_id = request.form.get('trip_id')
        update_trip_status(trip_id, 'truck_assigned')
    trips = get_waiting_trips()
    return render_template('truck_owner_dashboard.html', trips=trips)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)