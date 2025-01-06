import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(os.path.dirname(__file__), 'instance/truck_delivery.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Mail settings
    MAIL_SERVER = 'mail.scm.bg'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = 'l.mateev@scm.bg'
    MAIL_PASSWORD = 'Screws33'
    
    # Mapbox settings
    MAPBOX_TOKEN = os.getenv('MAPBOX_TOKEN')
    
    # Security settings
    EMAIL_VERIFICATION_REQUIRED = os.getenv('EMAIL_VERIFICATION_REQUIRED', 'FALSE').lower() == 'true'
    PASSWORD_CHECK_REQUIRED = os.getenv('PASSWORD_CHECK_REQUIRED', 'TRUE').lower() == 'true'
    USER_TYPE_CHECK_REQUIRED = os.getenv('USER_TYPE_CHECK_REQUIRED', 'TRUE').lower() == 'true'
    DEBUG_MODE = os.getenv('DEBUG_MODE', 'FALSE').lower() == 'true'
