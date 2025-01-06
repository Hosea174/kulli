import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(os.path.dirname(__file__), 'instance/truck_delivery.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Mail settings
    MAIL_SERVER = 'smtp.zoho.eu'  # Try EU server if you're in Europe
    MAIL_PORT = 465  # Try port 465 with SSL
    MAIL_USE_SSL = True  # Changed from TLS to SSL
    MAIL_USE_TLS = False
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    
    # Mapbox settings
    MAPBOX_TOKEN = os.getenv('MAPBOX_TOKEN')
