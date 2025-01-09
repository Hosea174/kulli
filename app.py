from flask import Flask, current_app, flash, jsonify, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, login_required
from flask_mail import Mail
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
import os
from dotenv import load_dotenv
from flask_login import LoginManager
import requests
from crud import create_trip, get_user_trips, get_truck_owner_trips, update_trip_status
from models import Trip
from extensions import db, mail
from models import User, TruckOwner

# Load environment variables
load_dotenv()

def calculate_price(distance, truck_type):
    """Calculate trip price in EURO based on distance and truck type."""
    rates = {
        'small_pickup': 0.95,
        'mid_sized': 1.2,
        'large': 1.32
    }
    price = distance * rates[truck_type]
    return round(price, 2)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object('config.Config')
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(BASE_DIR, "instance/truck_delivery.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
mail.init_app(app)
login_manager = LoginManager(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    user = db.session.get(User, int(user_id))
    if user:
        return user
    truck_owner = db.session.get(TruckOwner, int(user_id))
    if truck_owner:
        return truck_owner
    return None

# Register blueprint
from auth.routes import auth as auth_blueprint
app.register_blueprint(auth_blueprint)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/user/dashboard')
@login_required
def user_dashboard():
    # Get trips in different status categories
    trips = {
        'active_requests': Trip.query.filter(
            (Trip.user_id == current_user.id) &
            (Trip.status.in_(['waiting', 'truck_assigned', 'in_progress']))
        ).order_by(Trip.created_at.desc()).all(),
        
        'completed_trips': Trip.query.filter(
            (Trip.user_id == current_user.id) &
            (Trip.status == 'completed')
        ).order_by(Trip.created_at.desc()).all(),
        
        'canceled_trips': Trip.query.filter(
            (Trip.user_id == current_user.id) &
            (Trip.status == 'canceled')
        ).order_by(Trip.created_at.desc()).all()
    }
    return render_template('user_dashboard.html', trips=trips)

@app.route('/api/trip/<int:trip_id>')
@login_required
def get_trip_details(trip_id):
    trip = Trip.query.get(trip_id)
    if trip and trip.user_id == current_user.id:
        trip_data = {
            'id': trip.id,
            'pickup_location': trip.pickup_location,
            'destination': trip.destination,
            'status': trip.status,
            'estimated': {
                'distance': trip.est_distance,
                'duration': trip.est_duration,
                'price': trip.est_price
            },
            'actual': {
                'distance': trip.actual_distance,
                'duration': trip.actual_duration,
                'price': trip.actual_price
            },
            'created_at': trip.created_at.isoformat(),
            'cargo': {
                'description': trip.cargo_description,
                'weight': trip.cargo_weight,
                'volume': trip.cargo_volume,
                'requirements': trip.special_requirements
            },
            'documents': trip.documents,
            'ecmr_link': trip.ecmr_link,
            'gps_tracking_link': trip.gps_tracking_link,
            'notes': trip.notes
        }
        return jsonify(trip_data)
    return jsonify({'error': 'Trip not found'}), 404

@app.route('/api/estimate_route', methods=['POST'])
@login_required 
def estimate_route():
    data = request.get_json()
    pickup = data['pickup_location']
    destination = data['destination']
    
    # Get route from Mapbox
    url = f"https://api.mapbox.com/directions/v5/mapbox/driving/{pickup};{destination}"
    params = {
        'access_token': app.config['MAPBOX_TOKEN'],
        'geometries': 'geojson',
        'steps': 'true'
    }
    
    response = requests.get(url, params=params)
    if response.status_code != 200:
        return jsonify({'error': 'Failed to get route data'}), 400
        
    route_data = response.json()
    
    # Calculate estimates
    distance = route_data['routes'][0]['distance'] / 1000  # Convert to km
    duration = route_data['routes'][0]['duration'] / 3600  # Convert to hours
    
    # Calculate price estimates for different truck types
    price_estimates = {
        'small_pickup': calculate_price(distance, 'small_pickup'),
        'mid_sized': calculate_price(distance, 'mid_sized'),
        'large': calculate_price(distance, 'large')
    }
    
    return jsonify({
        'distance': distance,
        'duration': duration,
        'price_estimates': price_estimates,
        'route_geometry': route_data['routes'][0]['geometry']
    })

@app.route('/create_trip', methods=['POST'])
@login_required
def create_trip_route():
    data = request.get_json()
    trip_data = {
        'user_id': current_user.id,
        'pickup_location': data['pickup_location'],
        'destination': data['destination'],
        'est_duration': data['duration'],
        'est_distance': data['distance'],
        'est_price': data['price'],
        'cargo_description': data.get('cargo_description'),
        'cargo_weight': float(data.get('cargo_weight', 0)),
        'cargo_volume': float(data.get('cargo_volume', 0)),
        'special_requirements': data.get('special_requirements'),
        'documents': data.get('documents')
    }
    
    trip = create_trip(**trip_data)
    return jsonify({
        'success': True,
        'trip': trip.to_dict()
    })

@app.route('/truck-owner/dashboard', methods=['GET', 'POST'])
@login_required
def truck_owner_dashboard():
    if not isinstance(current_user, TruckOwner):
        flash('Access denied. Truck owner account required.', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        trip_id = request.form.get('trip_id')
        truck_owner_id = request.form.get('truck_owner_id')
        
        if trip_id and truck_owner_id:
            trip = Trip.query.get(trip_id)
            if trip:
                trip.truck_owner_id = int(truck_owner_id)
                trip.status = 'truck_assigned'
                db.session.commit()
                flash('Trip successfully assigned!', 'success')
            else:
                flash('Trip not found.', 'error')

    # Get trips in two categories
    my_trips = Trip.query.filter_by(truck_owner_id=current_user.id).all()
    available_trips = Trip.query.filter_by(status='waiting').all()

    return render_template('truck_owner_dashboard.html', 
                         trips={'my_trips': my_trips, 'available_trips': available_trips})

@app.route('/update_trip_status', methods=['POST'])
@login_required
def update_trip_status_route():
    try:
        data = request.get_json()
        trip_id = data.get('trip_id')
        status = data.get('status')
        
        if not trip_id or not status:
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400

        trip = Trip.query.get(trip_id)
        if not trip:
            return jsonify({'success': False, 'message': 'Trip not found'}), 404

        # Verify user has permission to update this trip
        if trip.user_id != current_user.id and not current_user.__class__.__name__ == 'TruckOwner':
            return jsonify({'success': False, 'message': 'Unauthorized to update this trip'}), 403

        # Update trip status and additional fields
        update_data = {
            'status': status,
            'actual_distance': data.get('actual_distance'),
            'actual_duration': data.get('actual_duration'),
            'actual_price': data.get('actual_price'),
            'fuel_cost': data.get('fuel_cost'),
            'toll_cost': data.get('toll_cost'),
            'notes': data.get('notes'),
            'ecmr_link': data.get('ecmr_link'),
            'gps_tracking_link': data.get('gps_tracking_link')
        }

        trip = update_trip_status(trip_id, status, **update_data)
        
        return jsonify({
            'success': True,
            'message': 'Trip updated successfully',
            'trip': trip.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Failed to update trip: {str(e)}'}), 500

if __name__ == '__main__':
    with app.app_context():
        # Create instance directory if it doesn't exist
        instance_path = os.path.join(os.path.dirname(__file__), 'instance')
        if not os.path.exists(instance_path):
            os.makedirs(instance_path)
        db.create_all()
    app.run(debug=True)
