from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from flask_login import LoginManager, current_user, login_required
import os
from dotenv import load_dotenv
from flask_login import LoginManager
import requests
from crud import create_trip, get_user_trips, get_waiting_trips, update_trip_status
from extensions import db, mail, socketio
from models import User, TruckOwner

# Load environment variables
load_dotenv()


# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(BASE_DIR, "instance/truck_delivery.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAPBOX_TOKEN'] = os.getenv('MAPBOX_TOKEN')
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.globals.update(format=format)

# Initialize extensions
db.init_app(app)
mail.init_app(app)
socketio.init_app(app)

# login_manager = LoginManager(app)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    user_type = session.get('user_type')
    if user_type == 'user':
        return User.query.get(int(user_id))
    elif user_type == 'truck_owner':
        return TruckOwner.query.get(int(user_id))
    return None



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
        
    print("Logged-in user:", current_user.name, current_user.email, current_user.id)
    trips = get_waiting_trips()
    return render_template('truck_owner_dashboard.html', trips=trips)

@app.route('/create_trip', methods=['POST'])
@login_required
def create_trip_route():
    pickup_location = request.form['pickup_location']
    destination = request.form['destination']
    truck_type = request.form['truck_type']

    mapbox_token = 'sk.eyJ1IjoiY2hyaXN0ZWRsYSIsImEiOiJjbTVoc2pxcTUwbjM4MmtzZ25nZDllN2k1In0._pobdd2JUaLTehWOMZQG7w'

    # Use Mapbox API to estimate distance and duration
    url1 = f"https://api.mapbox.com/search/geocode/v6/forward?q={pickup_location}&proximity=ip&access_token={mapbox_token}"
    url2 = f"https://api.mapbox.com/search/geocode/v6/forward?q={destination}&proximity=ip&access_token={mapbox_token}"
    
    response1 = requests.get(url1)
    response2 = requests.get(url2)

    if response1.status_code == 200 and response2.status_code == 200:
        pickup_coordinates = response1.json()['features'][0]['properties']['coordinates']
        destination_coordinates = response2.json()['features'][0]['properties']['coordinates']

        pickup_location = response1.json()['features'][0]['properties']['full_address']
        destination = response2.json()['features'][0]['properties']['full_address']
    else:
        flash("Error in geocoding request")
        return redirect(url_for('user_dashboard'))
    
    mapbox_url = f"https://api.mapbox.com/directions/v5/mapbox/driving/{pickup_coordinates['longitude']},{pickup_coordinates['latitude']};{destination_coordinates['longitude']},{destination_coordinates['latitude']}?access_token={mapbox_token}"
    response = requests.get(mapbox_url)
    trip_data = response.json()

    est_distance = round(trip_data['routes'][0]['distance'] / 1000, 2) # in km
    est_duration = round(trip_data['routes'][0]['duration'] / 60, 2) # in mins
    est_price = calculate_price(est_distance, truck_type)

    # store trip details in session to be used in the confirmation page...
    session['trip_data'] = {
        'pickup_location': pickup_location,
        'destination': destination,
        'pickup_coordinates': [pickup_coordinates['longitude'], pickup_coordinates['latitude']],
        'destination_coordinates': [destination_coordinates['longitude'] , destination_coordinates['latitude']],
        'truck_type': truck_type,
        'est_distance': est_distance,
        'est_duration': est_duration,
        'est_price': est_price
    }

    return redirect(url_for('confirm_trip_page'))

def calculate_price(distance, truck_type):
    start_prices = {'small_pickup': 500, 'mid_sized': 1500, 'large': 3000}
    base_rates = {'small_pickup': 10.5, 'mid_sized': 20.5, 'large': 40.0}
    return start_prices[truck_type] + round(distance * base_rates[truck_type], 2)

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

@app.route('/api/update_trip_status', methods=['POST'])
@login_required
def update_trip_status_api():
    trip_id = request.json.get('trip_id')
    new_status = request.json.get('new_status')

    trip = update_trip_status(trip_id, new_status)
    if not trip:
        return jsonify({"error": "Trip not found"}), 404

    socketio.emit('trip_status_update', {
        'trip_id': trip.id,
        'new_status': new_status
    }) 

    return jsonify({
        "message": "Trip status updated successfully",
        "trip_id": trip.id,
        "new_status": trip.status
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    from auth.routes import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    socketio.run(app, debug=True)