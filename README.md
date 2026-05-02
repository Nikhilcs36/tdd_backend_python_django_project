# TDD Backend Python Django Project - Login Tracking Dashboard

## Description

This repository contains the backend code for a comprehensive **Login Tracking Dashboard** built using Django and Django Rest Framework. The project is developed using Test-Driven Development (TDD) methodology and provides advanced user authentication, detailed login analytics, and comprehensive dashboard functionality. This backend serves as the foundation for monitoring user login activities, tracking authentication patterns, and providing valuable insights through a powerful REST API.

The primary focus of this project is the **Login Tracking Dashboard**, which offers real-time analytics and statistics about user login behavior, trends, and patterns. The system includes secure authentication mechanisms, user management, and role-based dashboard access to ensure data security and proper access control.

## Development Methodology: Test-Driven Development (TDD)

This project was built using **Test-Driven Development (TDD)**, a software development approach where tests are written before the actual implementation code. The TDD process follows a simple cycle:

1. **Write a failing test** that defines the desired functionality
2. **Write the minimum code** necessary to make the test pass
3. **Refactor the code** to improve design while keeping tests passing

### TDD Benefits in This Project:
- **High Code Quality**: Comprehensive test coverage ensures reliable functionality
- **Better Design**: Tests drive clean, modular architecture
- **Regression Prevention**: Changes can be made confidently without breaking existing features
- **Documentation**: Tests serve as living documentation of system behavior

The TDD approach was particularly valuable for building the Login Tracking Dashboard, ensuring that all analytics features work correctly and can be extended safely.

## Primary Feature: Login Tracking Dashboard

The **Login Tracking Dashboard** is the core feature of this application, providing:

- **Real-time Login Statistics**: Track user login counts, patterns, and trends
- **Advanced Analytics**: Weekly and monthly login distribution analysis
- **User-specific Dashboard**: Individual user login activity and statistics
- **Admin Dashboard**: Comprehensive admin interface with user management
- **Login Trends**: Visual representation of login patterns over time
- **Comparison Tools**: Compare login activities across different time periods
- **Security Monitoring**: Track login attempts and security events

## Features

### Login Tracking & Analytics
- **Real-time Login Statistics**: Track total logins, login frequency, success and failed attempts
- **Weekly/Monthly Analytics**: Detailed breakdown of login patterns by week and month
- **Login Trends**: Visual charts showing login trends over time including success rates
- **User-specific Dashboard**: Individual users can view their own login activity including success/failure rates
- **Admin Dashboard**: Comprehensive admin interface with user management capabilities
- **Login Comparison**: Compare login activities across different time periods
- **Distribution Analysis**: Analyze login distribution by time of day, day of week, etc.
- **Login Attempt Analytics**: Monitor login success and failure rates, including attempt patterns
- **Custom Date Range Filters**: Filter dashboard data by specific date ranges for flexible analysis

### User Management
- **Custom User Model**: Advanced user management with username, email, and profile images
- **User Registration & Authentication**: Secure user registration and login system
- **Profile Management**: Users can manage their profiles and view personal statistics
- **Role-based Access**: Different dashboard views for regular users and administrators

### User Access Levels Comparison

| Feature | Regular User | Admin User |
|---------|-------------|------------|
| View own login statistics | ✅ | ✅ |
| View own login activity | ✅ | ✅ |
| Access personal dashboard | ✅ | ✅ |
| Edit own profile | ✅ | ✅ |
| View all users' statistics | ❌ | ✅ |
| View all login activities | ❌ | ✅ |
| Access admin dashboard | ❌ | ✅ |
| View user-specific analytics | ❌ | ✅ |
| View other user profiles | ❌ | ✅ |
| View own login patterns (success/failed attempts) | ✅ | ✅ |
| Monitor system-wide security events | ❌ | ✅ |
| Access comprehensive charts | Limited | Full access |

### Authentication & Security
- **JWT Token Authentication**: Secure token-based authentication using DRF SimpleJWT
- **Email Verification**: Token-based email verification system for account activation
- **Password Reset**: Secure password reset functionality with token validation
- **Login Activity Tracking**: Detailed tracking of all login attempts including success/failed attempts and IP addresses
- **Security Monitoring**: Monitor suspicious login activities, failed login attempts, and security patterns

### API & Documentation
- **RESTful API**: Comprehensive REST API for all dashboard functionalities
- **Auto-generated Documentation**: API documentation using drf-spectacular
- **Swagger UI**: Interactive API documentation interface
- **Redoc**: Alternative API documentation format

### Deployment & Infrastructure
- **Docker Support**: Containerized deployment with Docker and Docker Compose
- **MySQL Database**: Robust database support for production environments
- **Media File Handling**: Secure handling of user profile images
- **Environment Configuration**: Flexible configuration using environment variables

## Authentication Methods

### JWT Token Authentication
Users can authenticate using JWT tokens for secure API access. The system provides:
- Token generation and refresh endpoints
- Secure token validation
- Automatic token expiration handling

### Email Verification
- Users receive verification emails with secure tokens
- Account activation through email links
- Resend verification email functionality

### Password Reset
- Secure password reset token generation
- Email-based password reset flow
- Token expiration for security

## Installation

### Recommended Approach: Docker Deployment

**Docker is the recommended approach** for running this application as it provides consistent environments and easier setup. Docker ensures that all dependencies are properly managed and the application runs reliably across different systems.

### Prerequisites
- Docker and Docker Compose
- MySQL database (included in Docker setup)

### Docker Deployment

#### Basic Docker Commands

**Build the Docker image**:
```bash
docker-compose build
```

**Run the application**:
```bash
docker-compose up
```

**Stop and remove containers**:
```bash
docker-compose down
```

**Delete volumes (including database data)**:
```bash
docker-compose down --v
```

#### Development Commands

**Run database migrations**:
```bash
docker-compose run --rm app sh -c "python manage.py wait_for_db && python manage.py migrate"
```

**Create a superuser**:
```bash
docker-compose run --rm app sh -c "python manage.py createsuperuser"
```

**Run tests**:
```bash
docker-compose run --rm app sh -c "python manage.py test"
```

**Run linting**:
```bash
docker-compose run --rm app flake8
```

**Run tests and linting together**:
```bash
docker-compose run --rm app sh -c "python manage.py test && flake8"
```

### Alternative: Local Development Setup

This setup is optional and can be used if you prefer running the application directly on your system.

**Prerequisites**
- Python 3.9+
- MySQL database

1. **Clone the repository**:
```bash
git clone https://github.com/Nikhilcs36/tdd_backend_python_django_project.git
cd tdd_backend_python_django_project
```

2. **Create and activate virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**:
Copy the `.env.example` file to `.env` and configure your database and email settings:
```bash
cp .env.example .env
```

5. **Run database migrations**:
```bash
cd app
python manage.py migrate
```

6. **Create superuser** (optional, for admin access):
```bash
python manage.py createsuperuser
```

7. **Start the development server**:
```bash
python manage.py runserver
```

## API Endpoints

### Authentication Endpoints
- `POST /api/user/token/` - Obtain JWT token
- `POST /api/user/token/refresh/` - Refresh JWT token
- `POST /api/user/create/` - User registration
- `GET /api/user/logout/` - User logout
- `POST /api/user/verify-email/` - Email verification
- `POST /api/user/resend-verification/` - Resend verification email
- `POST /api/user/password-reset/` - Request password reset
- `POST /api/user/reset-password/<token>/` - Reset password with token

### User Management Endpoints
- `GET /api/user/me/` - Get current user profile
- `GET /api/user/users/` - List all users (admin only)
- `GET /api/user/users/<id>/` - Get specific user details

### Dashboard Endpoints
- `GET /api/user/dashboard/stats/` - User dashboard statistics
- `GET /api/user/dashboard/login-activity/` - User login activity
- `GET /api/user/dashboard/charts/trends/` - Login trends chart data
- `GET /api/user/dashboard/charts/comparison/` - Login comparison data
- `GET /api/user/dashboard/charts/distribution/` - Login distribution data

### Admin Dashboard Endpoints
- `GET /api/user/admin/dashboard/` - Admin dashboard overview
- `GET /api/user/admin/charts/` - Admin charts data
- `GET /api/user/admin/dashboard/users/stats/` - Admin users statistics
- `GET /api/user/<user_id>/dashboard/stats/` - User-specific statistics (admin)
- `GET /api/user/<user_id>/dashboard/login-activity/` - User-specific login activity (admin)

### API Documentation
- `GET /api/schema/` - API schema
- `GET /api/docs/` - [Swagger UI documentation](http://localhost:8000/api/docs/)
- `GET /api/redoc/` - ReDoc documentation

## Usage

### Accessing the Application

1. **Development Server**: Access the application at `http://localhost:8000`
2. **API Documentation**: View interactive API docs at `http://localhost:8000/api/docs/`
3. **Admin Interface**: Access Django admin at `http://localhost:8000/admin/`

### Using the Login Tracking Dashboard

1. **User Registration**: Register a new user account
2. **Email Verification**: Verify your email address
3. **Login**: Authenticate using JWT tokens
4. **View Dashboard**: Access your personal dashboard with login statistics
5. **Admin Access**: Administrators can access comprehensive admin dashboard

### API Integration

Integrate with the API using JWT authentication:
```bash
# Get authentication token
curl -X POST http://localhost:8000/api/user/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'

# Use token to access protected endpoints
curl -H "Authorization: JWT YOUR_JWT_TOKEN" \
  http://localhost:8000/api/user/dashboard/stats/
```

## Customization

You can customize the application by modifying the following files:

### Core Application Files
- `app/core/models.py` - Database models for User and LoginActivity
- `app/core/views.py` - Core application views and logic
- `app/core/admin.py` - Admin interface configuration

### User Management Files
- `app/user/models.py` - User-related models (if any extensions)
- `app/user/views.py` - User authentication and management views
- `app/user/views_dashboard.py` - Dashboard views and analytics
- `app/user/serializers.py` - API serializers for user data
- `app/user/urls.py` - URL routing for user endpoints

### Configuration Files
- `app/app/settings.py` - Django project settings
- `app/app/urls.py` - Main URL configuration
- `.env` - Environment variables configuration

### Dashboard Customization
- Modify dashboard statistics in `app/user/views_dashboard.py`
- Customize charts and analytics endpoints
- Add new dashboard metrics and visualizations

## Admin Interface

The application provides a comprehensive admin interface for managing users and monitoring login activities.

### Accessing Admin Interface

1. **Create superuser account**:
```bash
python manage.py createsuperuser
```

2. **Start development server**:
```bash
python manage.py runserver
```

3. **Access admin interface**: Visit `http://localhost:8000/admin/`

### Admin Features
- **User Management**: View, edit, and manage user accounts
- **Login Activity Monitoring**: Monitor all user login activities
- **Dashboard Analytics**: Access comprehensive admin dashboard
- **Security Monitoring**: Track security events and suspicious activities

## License

This project is licensed under the MIT License - see the [MIT License](https://choosealicense.com/licenses/mit/) for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## Support

For support and questions, please contact nikhilcs36@gmail.com or open an issue in the GitHub repository.

## Acknowledgments

- Built with Django and Django REST Framework
- JWT authentication using djangorestframework-simplejwt
- API documentation with drf-spectacular
- Containerized deployment with Docker