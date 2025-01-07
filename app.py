from flask import Flask, current_app, flash, jsonify, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, login_required
from flask_mail import Mail
from flask_migrate import Migrate
import os
from dotenv import load_dotenv
from flask_login import LoginManager
import requests
from crud import create_trip, get_user_trips, get_truck_owner_trips, update_trip_status_in_db
from models import Trip
from extensions import db, mail
from models import User, TruckOwner

# Load environment variables
load_dotenv()


def calculate_price(distance, truck_type):
    """Calculate trip price in EURO based on distance and truck type.
    Uses per km rates: 1.32€/km (large), 1.2€/km (medium), 0.95€/km (small)"""
    # Per km rates in EURO
    rates = {
        'small_pickup': 0.95,
        'mid_sized': 1.2,
        'large': 1.32
    }
    
    # Calculate total price in EURO
    price = distance * rates[truck_type]
    
    # Round to 2 decimal places
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
    trips = get_user_trips(current_user.id)
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
            'additional_data': trip.additional_data
        }
        return jsonify(trip_data)
    return jsonify({'error': 'Trip not found'}), 404

@app.route('/update-trip-status', methods=['POST'])
@login_required
def update_trip_status_route():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
            
        trip_id = data.get('trip_id')
        new_status = data.get('status')
        
        if not trip_id or not new_status:
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
            
        trip = Trip.query.get(trip_id)
        if not trip or (trip.user_id != current_user.id and trip.truck_owner_id != current_user.id):
            return jsonify({'success': False, 'message': 'Invalid trip update request'}), 403
            
        # Validate status transitions
        valid_transitions = {
            'waiting': ['waiting', 'truck_assigned', 'canceled'],
            'truck_assigned': ['truck_assigned', 'in_progress', 'canceled'],
            'in_progress': ['in_progress', 'completed', 'canceled'],
            'completed': ['completed'],
            'canceled': ['canceled']
        }
        
        if new_status not in valid_transitions.get(trip.status, []):
            return jsonify({
                'success': False,
                'message': f'Invalid status transition from {trip.status} to {new_status}'
            }), 400
            
        # Update trip fields
        trip.status = new_status
        trip.actual_distance = data.get('actual_distance')
        trip.actual_duration = data.get('actual_duration')
        trip.actual_price = data.get('actual_price')
        trip.fuel_cost = data.get('fuel_cost')
        trip.toll_cost = data.get('toll_cost')
        trip.notes = data.get('notes')
        trip.ecmr_link = data.get('ecmr_link')
        trip.gps_tracking_link = data.get('gps_tracking_link')
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Trip updated successfully',
            'new_status': new_status,
            'updated_fields': {
                'actual_distance': trip.actual_distance,
                'actual_duration': trip.actual_duration,
                'actual_price': trip.actual_price
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error updating trip: {str(e)}'
        }), 500

@app.route('/truck-owner/dashboard', methods=['GET', 'POST'])
@login_required
def truck_owner_dashboard():
    if request.method == 'POST':
        trip_id = request.form.get('trip_id')
        if trip_id:
            trip = update_trip_status_in_db(trip_id, 'truck_assigned')
            if trip:
                trip.truck_owner_id = current_user.id
                db.session.commit()
                flash('Trip accepted successfully!')
            else:
                flash('Could not find trip')
        else:
            flash('No trip selected')
        return redirect(url_for('truck_owner_dashboard'))
        
    print("Logged-in user:", current_user.name, current_user.email, current_user.id)
    trips = get_truck_owner_trips(current_user.id)
    return render_template('truck_owner_dashboard.html', 
                         trips=trips,
                         current_user=current_user)

@app.route('/create_trip', methods=['POST'])
@login_required
def create_trip_route():
    pickup_location = request.form['pickup_location']
    destination = request.form['destination']
    truck_type = request.form['truck_type']

    mapbox_token = 'sk.eyJ1IjoiY2hyaXN0ZWRsYSIsImEiOiJjbTVoc2pxcTUwbjM4MmtzZ25nZDllN2k1In0._pobdd2JUaLTehWOMZQG7w'

    batch_request = {
        "requests": [
            {
                "q": pickup_location,
                "proximity": "ip"
            },
            {
                "q": destination,
                "proximity": "ip"
            }
        ]
    }

    # Use Mapbox API to estimate distance and duration
    url1 = f"https://api.mapbox.com/search/geocode/v6/forward?q={pickup_location}&proximity=ip&access_token={mapbox_token}"
    url2 = f"https://api.mapbox.com/search/geocode/v6/forward?q={destination}&proximity=ip&access_token={mapbox_token}"
    
    response1 = requests.get(url1)
    response2 = requests.get(url2)

    if response1.status_code != 200 or response2.status_code != 200:
        print(f"Geocoding API error - Pickup status: {response1.status_code}, Destination status: {response2.status_code}")
        flash("Could not find the locations. Please check the addresses and try again.")
        return redirect(url_for('user_dashboard'))

    try:
        pickup_data = response1.json()
        destination_data = response2.json()
    except ValueError as e:
        print(f"JSON parsing error: {str(e)}")
        flash("Error processing location data. Please try again.")
        return redirect(url_for('user_dashboard'))

    if not pickup_data['features'] or not destination_data['features']:
        print(f"No features found - Pickup: {pickup_data}, Destination: {destination_data}")
        flash("Could not find coordinates for the locations. Please try different addresses.")
        return redirect(url_for('user_dashboard'))
        
    pickup_coords = pickup_data['features'][0]['geometry']['coordinates']
    dest_coords = destination_data['features'][0]['geometry']['coordinates']
    
    pickup_coordinates = {
        'longitude': pickup_coords[0],
        'latitude': pickup_coords[1]
    }
    destination_coordinates = {
        'longitude': dest_coords[0],
        'latitude': dest_coords[1]
    }
    
    pickup_location = pickup_data['features'][0].get('properties', {}).get('full_address', 
        pickup_data['features'][0].get('properties', {}).get('name', 'Unknown location'))
    destination = destination_data['features'][0].get('properties', {}).get('full_address', 
        destination_data['features'][0].get('properties', {}).get('name', 'Unknown location'))
        
    print(f"Geocoding successful - Pickup: {pickup_location}, Destination: {destination}")

    # Check if coordinates are valid
    if not all(isinstance(coord, (int, float)) for coord in pickup_coordinates.values()) or \
       not all(isinstance(coord, (int, float)) for coord in destination_coordinates.values()):
        print(f"Invalid coordinates - Pickup: {pickup_coordinates}, Destination: {destination_coordinates}")
        flash("Invalid location coordinates. Please try different addresses.")
        return redirect(url_for('user_dashboard'))

    mapbox_url = f"https://api.mapbox.com/directions/v5/mapbox/driving/{pickup_coordinates['longitude']},{pickup_coordinates['latitude']};{destination_coordinates['longitude']},{destination_coordinates['latitude']}?access_token={mapbox_token}"
    print(f"Mapbox Directions API URL: {mapbox_url}")
    
    try:
        response = requests.get(mapbox_url)
        trip_data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Mapbox Directions API request failed: {str(e)}")
        flash("Error connecting to Mapbox. Please try again.")
        return redirect(url_for('user_dashboard'))
    except ValueError as e:
        print(f"JSON parsing error: {str(e)}")
        flash("Error processing route data. Please try again.")
        return redirect(url_for('user_dashboard'))
        
    print(f"Mapbox Directions API response: {trip_data}")  # Debug log

    if response.status_code != 200:
        print(f"Mapbox Directions API error - Status: {response.status_code}, Response: {trip_data}")
        error_msg = "Could not calculate route. Please check the locations and try again."
        if trip_data.get('code') == 'InvalidInput' and 'maximum distance' in trip_data.get('message', ''):
            error_msg = "The distance between locations is too large for our current service. Please try locations closer together."
        flash(error_msg)
        return redirect(url_for('user_dashboard'))
        
    if 'routes' not in trip_data or len(trip_data['routes']) == 0:
        print(f"No routes found in response: {trip_data}")
        error_msg = "No route found between these locations. Please try different addresses."
        if trip_data.get('code') == 'InvalidInput' and 'maximum distance' in trip_data.get('message', ''):
            error_msg = "The distance between locations is too large for our current service. Please try locations closer together."
        flash(error_msg)
        return redirect(url_for('user_dashboard'))
    
    try:
        est_distance = round(trip_data['routes'][0]['distance'] / 1000, 2) # in km
        est_duration = round(trip_data['routes'][0]['duration'] / 60, 2) # in mins
        est_price = calculate_price(est_distance, truck_type)
    except KeyError as e:
        print(f"Error parsing Mapbox response: {str(e)}")
        flash("Error calculating trip details")
        return redirect(url_for('user_dashboard'))
    except Exception as e:
        print(f"Unexpected error calculating trip details: {str(e)}")
        flash("Error processing trip details")
        return redirect(url_for('user_dashboard'))

    # store trip details in session to be used in the confirmation page...
    session['trip_data'] = {
        'pickup_location': pickup_location,
        'destination': destination,
        'pickup_coordinates': [pickup_coordinates['longitude'], pickup_coordinates['latitude']],
        'destination_coordinates': [destination_coordinates['longitude'] , destination_coordinates['latitude']],
        'truck_type': truck_type,
        'est_distance': est_distance,
        'est_duration': est_duration,
        'est_price': est_price,
        'route_geometry': {
            'type': 'LineString',
            'coordinates': [
                [pickup_coordinates['longitude'], pickup_coordinates['latitude']],
                [destination_coordinates['longitude'], destination_coordinates['latitude']]
            ]
        }
    }

    return redirect(url_for('confirm_trip_page'))

@app.route('/confirm_trip_page')
@login_required
def confirm_trip_page():
    trip_data = session.get('trip_data', {})
    return render_template('confirm_trip.html', trip_data=trip_data)

@app.route('/confirm_trip', methods=['POST'])
@login_required
def confirm_trip():
    trip_data = request.form
    create_trip(
        user_id=current_user.id,
        pickup_location=trip_data['pickup_location'],
        destination=trip_data['destination'],
        est_duration=float(trip_data['est_duration']),
        est_distance=float(trip_data['est_distance']),
        est_price=float(trip_data['est_price']),
    )
    return redirect(url_for('user_dashboard'))

@app.route('/api/autocomplete', methods=['GET'])
@login_required
def autocomplete():
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400
    mapbox_token = 'sk.eyJ1IjoiY2hyaXN0ZWRsYSIsImEiOiJjbTVoMDltbzMwZjI4MmhzZDd0aGZpc241In0.Oticj4dmkI08J8zt5AKRqg'
    
    bbox = "-17.625, -34.833, 51.208, 37.349"
    mapbox_url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{query}.json?access_token={mapbox_token}&bbox={bbox}"
    response = requests.get(mapbox_url)

    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch suggestions"}), response.status_code

    return jsonify(response.json())

if __name__ == '__main__':
    with app.app_context():
        # Create instance directory if it doesn't exist
        instance_path = os.path.join(os.path.dirname(__file__), 'instance')
        if not os.path.exists(instance_path):
            os.makedirs(instance_path)
        db.create_all()
    app.run(debug=True)
