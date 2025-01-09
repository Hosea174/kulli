from datetime import datetime
from models import db, User, TruckOwner, Trip

def create_user(email, name, phone, password):
    user = User(email=email, name=name, phone=phone, password=password)
    db.session.add(user)
    db.session.commit()
    return user

def create_truck_owner(email, name, phone, password, license_plate, truck_type):
    owner = TruckOwner(email=email, name=name, phone=phone, password=password,
                      license_plate=license_plate, truck_type=truck_type)
    db.session.add(owner)
    db.session.commit()
    return owner

def create_trip(user_id, pickup_location, destination, est_duration, est_distance, est_price, **kwargs):
    """
    Create a new trip with optional additional fields
    """
    trip = Trip(
        user_id=user_id,
        pickup_location=pickup_location,
        destination=destination,
        est_duration=est_duration,
        est_distance=est_distance,
        est_price=est_price
    )
    
    # Set any additional fields that were passed
    for key, value in kwargs.items():
        if hasattr(trip, key):
            setattr(trip, key, value)
    
    db.session.add(trip)
    db.session.commit()
    return trip

def update_trip_status(trip_id, status, **kwargs):
    """
    Update trip status with history tracking
    """
    trip = Trip.query.get(trip_id)
    if trip:
        # Update status history
        if not trip.status_history:
            trip.status_history = []
        trip.status_history.append({
            'status': status,
            'timestamp': datetime.utcnow().isoformat(),
            'changed_by': kwargs.get('changed_by', 'system')
        })
        
        trip.status = status
        trip.last_status_change = datetime.utcnow()
        
        # Update any additional fields
        for key, value in kwargs.items():
            if hasattr(trip, key):
                setattr(trip, key, value)
                
        db.session.commit()
    return trip

def get_user_trips(user_id):
    return Trip.query.filter_by(user_id=user_id).all()

def get_truck_owner_trips(truck_owner_id):
    # Get trips assigned to this truck owner (regardless of status)
    my_trips = Trip.query.filter(
        (Trip.truck_owner_id == truck_owner_id) &
        (Trip.status != 'waiting')
    ).order_by(Trip.created_at.desc()).all()
    
    # Get available trips (status = waiting and not assigned to any truck owner)
    available_trips = Trip.query.filter(
        (Trip.status == 'waiting') &
        (Trip.truck_owner_id.is_(None))
    ).order_by(Trip.created_at.desc()).all()
    
    return {
        'my_trips': my_trips,
        'available_trips': available_trips
    }
