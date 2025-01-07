from models import db, User, TruckOwner, Trip

# Create a new user
def create_user(email, name, phone, password):
    user = User(email=email, name=name, phone=phone, password=password)
    db.session.add(user)
    db.session.commit()
    return user

# Create a new truck owner
def create_truck_owner(email, name, phone, password, license_plate, truck_type):
    owner = TruckOwner(email=email, name=name, phone=phone, password=password,
                       license_plate=license_plate, truck_type=truck_type)
    db.session.add(owner)
    db.session.commit()
    return owner

# Create a new trip
def create_trip(user_id, pickup_location, destination, est_duration, est_distance, est_price):
    trip = Trip(user_id=user_id, pickup_location=pickup_location, destination=destination,
                est_duration=est_duration, est_distance=est_distance, est_price=est_price)
    db.session.add(trip)
    db.session.commit()
    return trip

# Update trip status
def update_trip_status(trip_id, status):
    trip = Trip.query.get(trip_id)
    if trip:
        trip.status = status
        db.session.commit()
    return trip

# Fetch all trips for a user
def get_user_trips(user_id):
    return Trip.query.filter_by(user_id=user_id).all()

# Fetch trips for truck owners
def get_truck_owner_trips(truck_owner_id):
    return Trip.query.filter(
        (Trip.truck_owner_id == truck_owner_id) | 
        (Trip.status == 'waiting')
    ).order_by(Trip.status.desc(), Trip.created_at.desc()).all()
