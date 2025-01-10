from models import db, User, TruckOwner, Trip
from sqlalchemy import not_

# register a new user
def create_user(email, name, phone, password):
    user = User(email=email, name=name, phone=phone, password=password)
    db.session.add(user)
    db.session.commit()
    return user

# register a new truck owner
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
def update_trip_status(trip_id, status, truck_owner_id):
    trip = Trip.query.get(trip_id)
    if trip:
        trip.status = status
        if status == "truck_assigned":
            trip.truck_owner_id = truck_owner_id
        elif status == "waiting": #if trucker canceled the trip after accepting it
            trip.truck_owner_id = None

        db.session.commit()
    return trip

# Fetch all trips for a user
def get_user_trips(user_id):
    return Trip.query.filter_by(user_id=user_id).all()

# Fetch all waiting trips for truck owners
def get_waiting_trips():
    return Trip.query.filter(not_(Trip.status.in_(['rejected']))).all()