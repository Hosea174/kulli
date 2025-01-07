# Lazzar - Truck Delivery Platform

Lazzar is a Flask-based web application that connects truck owners with users who need load transportation services. It provides a platform for users to request trips and truck owners to accept them, with integrated mapping and pricing functionality.

## Features

### User Features
- User registration and authentication
- Create new trips with pickup/destination locations
- View trip details including estimated distance, duration and price
- View trip history and status
- Interactive map visualization for trips

### Truck Owner Features
- Truck owner registration and authentication
- View available trips
- Accept trips
- Update trip status

### Technical Features
- Flask web framework with SQLAlchemy ORM
- Mapbox integration for geocoding and routing
- Email verification system
- RESTful API for location autocomplete
- Secure password hashing
- Role-based authentication (User/Truck Owner)

## System Architecture

### Models
- **User**: Represents regular users who can request trips
- **TruckOwner**: Represents truck owners who can accept trips
- **Trip**: Represents transportation requests with status tracking

### Routes
- Auth routes for login/logout and registration
- User dashboard for trip management
- Truck owner dashboard for trip acceptance
- API endpoint for location autocomplete

### Templates
- Base template with navigation and layout
- User-specific dashboards
- Trip confirmation page with interactive map
- Authentication pages (login/register)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/lazzar.git
cd lazzar
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Initialize the database:
```bash
flask shell
>>> from app import db
>>> db.create_all()
```

6. Run the development server:
```bash
flask run
```

## Configuration

The application is configured through environment variables and the `config.py` file. Key configuration options include:

- Database connection
- Mapbox API token
- Email server settings
- Security settings (password requirements, email verification)

## API Documentation

### Autocomplete Endpoint
`GET /api/autocomplete?query=<location>`

Returns location suggestions for address input fields. Used by the frontend for location autocomplete.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Roadmap

- [ ] Add payment integration
- [ ] Implement trip tracking
- [ ] Add user ratings system
- [ ] Develop mobile app interface
