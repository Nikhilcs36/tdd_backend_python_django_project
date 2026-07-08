# TDD Backend Python Django Project - Login Tracking Dashboard

## Description

This repository contains the backend code for a comprehensive **Login Tracking Dashboard** built using Django and Django Rest Framework. The project is developed using Test-Driven Development (TDD) methodology and provides advanced user authentication, detailed login analytics, and comprehensive dashboard functionality. This backend serves as the foundation for monitoring user login activities, tracking authentication patterns, and providing valuable insights through a powerful REST API.

The primary focus of this project is the **Login Tracking Dashboard**, which offers real-time analytics and statistics about user login behavior, trends, and patterns. The system includes secure authentication mechanisms, user management, role-based dashboard access, a circle drawing game backend, and downloadable Excel reports to ensure data security and proper access control.

---

## Frontend

This backend project is designed to pair with a React frontend application built with TypeScript, Vite, and Vitest.

- **Frontend Repository**: [tdd_react_typescript_vite_vitest_project](https://github.com/Nikhilcs36/tdd_react_typescript_vite_vitest_project)

The frontend and backend communicate over a shared Docker network (`tdd-network`). See the [Frontend Integration](#frontend-integration) section for details.

---

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
- **Combined Chart Data**: Admin can view combined login trends/comparison/distribution data for multiple users using `user_ids[]` parameter
- **Role-based Chart Filtering**: Filter charts and dashboard data by user role (`admin` / `regular`)
- **Batch User Statistics**: Admin can retrieve statistics for multiple users with optional active status filtering

### User Management
- **Custom User Model**: Extends Django's `AbstractBaseUser` with built-in login statistics tracking (`login_count`, `weekly_logins`, `monthly_logins`), email verification system (`email_verified`, verification tokens), password reset tokens, and automatic profile image cleanup on account deletion
- **User Registration & Authentication**: Secure user registration and login system with email verification requirement
- **Profile Management**: Users can manage their profiles, upload profile images (JPG/JPEG/PNG only, max 2MB), and view personal statistics
- **Role-based Access**: Different dashboard views for regular users and administrators
- **User Filtering**: List users with role-based filtering (`admin`/`regular`) and `me` parameter
- **Pagination**: Customizable pagination for user listings and login activity
- **Optional Name Field**: The `name` field on the user model is optional and excluded from the admin user creation form

### Game Section
- **Circle Drawing Game Backend**: Submit and track scores for a circle drawing game
- **Score Submission**: Authenticated users can submit their game scores
- **My Scores**: Users can view their own scores with best score tracking, paginated
- **Game Leaderboard**: Admin-only leaderboard showing the best score per user, ordered by score descending
- **Feature Flags**: The game section and leaderboard can be independently enabled/disabled via environment variables (`GAME_SECTION_ENABLED`, `GAME_LEADERBOARD_ENABLED`)
- **Role-based Access**: Score submission and personal score viewing are available to all authenticated users; leaderboard requires admin/staff privileges

### Login Tracking Summary Report Download
- **Excel Report Generation**: Download comprehensive login activity summary reports in professionally formatted Excel (.xlsx) format
- **Individual Mode**: Single user report — regular users can download their own report; admins can download for any user
- **Grouped Mode**: Combined report for multiple users (admin only)
- **Flexible Filtering**: Filter by date range, user role, user IDs, or predefined filters (`all`, `admin_only`, `regular_users`, `me`)
- **Feature Flag**: Report download can be enabled/disabled via `ENABLE_REPORT_DOWNLOAD` environment variable
- **Detailed Report Data**: Includes report metadata (user info, date period), recent login activities, top user agents, summary statistics (total/successful/failed logins, success rate), daily login trends, weekly/monthly comparison, success/failure distribution ratio, and grouped summary with combined totals for admin overview
- **Professional Formatting**: Styled Excel output with headers, borders, auto-adjusted column widths, and separate sheets for different data views

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
| View combined chart data (multiple users) | ❌ | ✅ |
| Filter data by user role | ❌ | ✅ |
| Access batch user statistics | ❌ | ✅ |
| View other users' login activity | ❌ | ✅ |
| Submit game scores | ✅ | ✅ |
| View own game scores | ✅ | ✅ |
| Access game leaderboard | ❌ | ✅ |
| Download own login report (individual mode) | ✅ | ✅ |
| Download any user's login report | ❌ | ✅ |
| Download grouped reports | ❌ | ✅ |
| View auto staff access countdown (`logins_remaining_for_staff`) | ✅ | ✅ |
| Switch active role | ❌ | ✅ |

### Authentication & Security
- **JWT Token Authentication**: Secure token-based authentication using DRF SimpleJWT
- **JWT Token Blacklisting**: Logout endpoint blacklists refresh tokens, preventing reuse
- **Email-based Login**: Users can log in using their email address instead of username (via custom `EmailBackend` authentication backend)
- **Custom JWT Exception Handler**: Standardized, user-friendly error messages for invalid or expired tokens
- **Email Verification**: Token-based email verification system for account activation (24-hour token expiration)
- **Welcome Email**: Automated welcome email sent after successful email verification
- **Password Reset**: Secure password reset functionality with token validation (1-hour token expiration)
- **RSA Encrypted Login Credentials**: Login passwords are encrypted using RSA-OAEP with SHA-256 before being sent over the network. The public key is served at `GET /api/user/public-key/`, and the private key never leaves the server. RSA keys are auto-generated on server startup — no manual setup required.
- **Auto Staff Access**: After 3 successful logins, users are automatically granted staff access (`is_staff=True`) via middleware. Login response includes `logins_remaining_for_staff` countdown (3, 2, 1, 0), `staff_access_granted` status, `active_role` ('regular'/'staff'/'superuser'), and `role_label` for frontend role-based UI control.
- **Role Switching**: Authenticated users with staff or superuser privileges can switch their active role via `POST /api/user/switch-role/`. Superusers can switch between 'regular', 'staff', and 'superuser'. Staff users can switch between 'regular' and 'staff'.
- **Automatic Token Cleanup**: Expired blacklisted JWT tokens are automatically cleaned every 24 hours via background scheduler. Tokens expired more than 1 day ago are deleted to prevent DB bloat.
- **Login Activity Tracking**: Detailed tracking of all login attempts via `LoginTrackingMiddleware`, including success/failed attempts, IP addresses, and user agents
- **Login Activity Model**: Persistent storage of login attempts with timestamp, IP address, user agent, and success status
- **Security Monitoring**: Monitor suspicious login activities, failed login attempts, and security patterns
- **Role-based Permissions**: Custom permission classes (`IsSuperUser`, `IsStaffOrSuperUser`) for fine-grained access control
- **Admin Bulk Email Verification**: Admin action to mark multiple users as email verified

### Email & SMTP Configuration
- **Gmail SMTP Integration**: Configured to send emails via Gmail SMTP server (`smtp.gmail.com`, port 587, TLS enabled)
- **HTML Email Templates**: Professionally designed HTML email templates for:
  - **Verification Email** — Account activation link with 24-hour expiry
  - **Password Reset Email** — Secure password reset link with 1-hour expiry
  - **Welcome Email** — Automated welcome message after successful verification
- **Frontend-friendly URLs**: Email links point to the React frontend application (not the backend API), configured via `FRONTEND_BASE_URL` environment variable
- **Environment Configuration**: Email credentials configured through `.env` file (`EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`)

### API & Documentation
- **RESTful API**: Comprehensive REST API for all dashboard functionalities
- **Auto-generated Documentation**: API documentation using drf-spectacular
- **Swagger UI**: Interactive API documentation interface
- **Redoc**: Alternative API documentation format

### Deployment & Infrastructure
- **Docker Support**: Containerized deployment with Docker and Docker Compose
- **MySQL Database**: Robust database support for production environments
- **Media File Handling**: Secure handling of user profile images with automatic cleanup on user deletion
- **Relative URL File Field**: Custom file field that returns relative media URLs (e.g., `/media/uploads/user/image.jpg`) — frontend-friendly
- **Environment Configuration**: Flexible configuration using environment variables
- **CORS Configuration**: Configured to allow requests from frontend development server (`http://localhost:5173`)
- **Timezone**: Configured to `Asia/Kolkata`
- **Max Upload Size**: 2MB limit for profile image uploads

### Feature Flags
- **GAME_SECTION_ENABLED**: Enable/disable the entire game section (default: `True`)
- **GAME_LEADERBOARD_ENABLED**: Enable/disable the game leaderboard (default: `True`)
- **ENABLE_REPORT_DOWNLOAD**: Enable/disable login report download (default: `True`)

---

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

---

## API Endpoints

### Authentication Endpoints
- `GET /api/user/public-key/` - Get RSA public key for login credential encryption
- `POST /api/user/token/` - Obtain JWT token (accepts `email` and `password`; also supports `encrypted_password`). Returns user details including `logins_remaining_for_staff` (countdown: 3, 2, 1, 0), `staff_access_granted`, `active_role` ('regular'/'staff'/'superuser'), and `role_label` for frontend role-based UI control
- `POST /api/user/token/refresh/` - Refresh JWT token
- `POST /api/user/switch-role/` - Switch active role (superusers: 'regular'/'staff'/'superuser'; staff users: 'regular'/'staff'). Requires `{"role": "..."}` in request body
- `POST /api/user/create/` - User registration
- `POST /api/user/logout/` - User logout (blacklists refresh token)
- `POST /api/user/verify-email/` - Email verification
- `POST /api/user/resend-verification/` - Resend verification email
- `POST /api/user/password-reset/` - Request password reset
- `POST /api/user/reset-password/<token>/` - Reset password with token

### User Management Endpoints
- `GET /api/user/me/` - Get current user profile
- `PUT /api/user/me/` - Update current user profile (supports image upload)
- `GET /api/user/users/` - List all users (admin only, supports `role` and `me` filters)
- `GET /api/user/users/<id>/` - Get specific user details (superuser only)
- `PUT /api/user/users/<id>/` - Update specific user (superuser only)
- `DELETE /api/user/users/<id>/` - Delete specific user (superuser only)

### Dashboard Endpoints
- `GET /api/user/dashboard/stats/` - User dashboard statistics (supports `start_date`, `end_date`)
- `GET /api/user/dashboard/login-activity/` - User login activity (supports `start_date`, `end_date`, pagination)
- `GET /api/user/dashboard/charts/trends/` - Login trends chart data (supports `user_ids[]`, `role`, `me`, date filters)
- `GET /api/user/dashboard/charts/comparison/` - Login comparison data (supports `user_ids[]`, `role`, `me`, date filters)
- `GET /api/user/dashboard/charts/distribution/` - Login distribution data (supports `user_ids[]`, `role`, `me`, date filters)

### Admin Dashboard Endpoints
- `GET /api/user/admin/dashboard/` - Admin dashboard overview (supports `user_ids[]`, `role`, `filter`, `me`, date filters)
- `GET /api/user/admin/charts/` - Admin charts data (user growth, daily login activity, success ratio)
- `GET /api/user/admin/dashboard/users/stats/` - Batch user statistics (admin only, supports `user_ids[]`, `is_active`)

### Role-Based Dashboard Endpoints
- `GET /api/user/<user_id>/dashboard/stats/` - User-specific statistics (role-based access)
- `GET /api/user/<user_id>/dashboard/login-activity/` - User-specific login activity (role-based access)

### Report Download Endpoint
- `GET /api/user/dashboard/report/download/?mode=<mode>` - Download login activity summary report in Excel format
  - **Parameters**: `mode` (required: `individual` or `grouped`), `user_ids[]`, `start_date`, `end_date`, `filter` (`all`/`admin_only`/`regular_users`/`me`), `role` (`admin`/`regular`), `selected_user_id`
  - **Permissions**: Regular users can download their own report in individual mode; admins can download for any user(s)

### Game Endpoints
- `POST /api/game/scores/` - Submit a game score (authenticated users)
- `GET /api/game/my-scores/` - List my game scores with best score (authenticated users, paginated)
- `GET /api/game/leaderboard/` - Game leaderboard — best score per user (admin/staff only, paginated)

### API Documentation
- `GET /api/schema/` - API schema
- `GET /api/docs/` - [Swagger UI documentation](http://localhost:8000/api/docs/)
- `GET /api/redoc/` - ReDoc documentation

---

## Usage

### Accessing the Application

1. **Development Server**: Access the application at `http://localhost:8000`
2. **API Documentation**: View interactive API docs at `http://localhost:8000/api/docs/`
3. **Admin Interface**: Access Django admin at `http://localhost:8000/admin/`

### Using the Login Tracking Dashboard

1. **User Registration**: Register a new user account
2. **Email Verification**: Verify your email address (check your email for the verification link)
3. **Login**: Authenticate using your email and password
4. **View Dashboard**: Access your personal dashboard with login statistics
5. **Admin Access**: Administrators can access comprehensive admin dashboard

### Using Game Features

1. **Submit a Score**: Authenticated users can submit a game score via `POST /api/game/scores/`
2. **View Scores**: Access your own scores via `GET /api/game/my-scores/` (includes best score)
3. **Leaderboard**: Admins can view the global leaderboard via `GET /api/game/leaderboard/`

### Downloading Login Reports

1. **Individual Report**: `GET /api/user/dashboard/report/download/?mode=individual` — downloads your own login report
2. **Grouped Report (Admin)**: `GET /api/user/dashboard/report/download/?mode=grouped` — downloads combined report for all users
3. **Custom Filtering**: Add `start_date`, `end_date`, `user_ids[]`, `role`, or `filter` parameters to customize the report

### API Integration

Integrate with the API using JWT authentication:
```bash
# Get authentication token
curl -X POST http://localhost:8000/api/user/token/ \
  -H "Content-Type: application/json" \
  -d '{"email": "your_email@example.com", "password": "your_password"}'

# Use token to access protected endpoints
curl -H "Authorization: JWT YOUR_JWT_TOKEN" \
  http://localhost:8000/api/user/dashboard/stats/
```

---

## Frontend Integration

### Docker Network Communication

This backend is designed to work with the frontend React application over a shared Docker network.

**Backend Container**: `backend` (port 8000)
**Frontend Container**: Connects to backend at `http://backend:8000`

### Setup Steps

1. **Create the shared Docker network** (one-time):
```bash
docker network create tdd-network
```

2. **Start the backend**:
```bash
docker-compose up -d
```

3. **Start the frontend** (separate project):
   The frontend `docker-compose.yml` should use the same `tdd-network` network.

> See `BACKEND_SETUP.md` and `FRONTEND_SETUP.md` for detailed setup guides.

### CORS Configuration

The backend is configured to accept requests from the frontend development server:
- Frontend URL: `http://localhost:5173`
- CORS credentials are enabled for authenticated requests

---

## Customization

You can customize the application by modifying the following files:

### Core Application Files
- `app/core/models.py` - Database models for User and LoginActivity
- `app/core/views.py` - Core application views and logic
- `app/core/admin.py` - Admin interface configuration (UserAdmin with role badges, LoginActivityAdmin with granular permissions)
- `app/core/apps.py` - App config that starts the daily token cleanup scheduler on Django startup
- `app/core/token_cleanup_scheduler.py` - Background scheduler that automatically cleans expired blacklisted JWT tokens every 24 hours
- `app/core/email_service.py` - Email sending logic and URL building
- `app/core/authentication.py` - Custom email-based authentication backend
- `app/core/exceptions.py` - Custom exception handler for JWT errors
- `app/core/middleware.py` - Login tracking middleware
- `app/core/templates/email/` - HTML email templates
- `app/core/templates/admin/base_site.html` - Custom admin template with role-based permission banner
- `app/templates/admin/base_site.html` - Custom admin template with role-based permission banner and responsive header styling
- `app/sites.py` - StaffOnlyAuthenticationForm that blocks regular users from logging into Django admin

### User Management Files
- `app/user/models.py` - User-related models (if any extensions)
- `app/user/views.py` - User authentication and management views
- `app/user/views_dashboard.py` - Dashboard views and analytics
- `app/user/views_report.py` - Report download views and logic
- `app/user/serializers.py` - API serializers for user data
- `app/user/serializers_dashboard.py` - Dashboard data serializers
- `app/user/urls.py` - URL routing for user endpoints
- `app/user/permissions.py` - Custom permission classes (`IsSuperUser`, `IsStaffOrSuperUser`)
- `app/user/validators.py` - Username, email, and password validators
- `app/user/pagination.py` - Custom pagination classes
- `app/user/fields.py` - Custom serializer fields (RelativeURLFileField)
- `app/user/mixins.py` - Shared mixins for date filtering and user filtering
- `app/user/reports/` - Report generation modules:
  - `data_collector.py` - Collects login data for reports
  - `excel_generator.py` - Generates formatted Excel reports

### Game Files
- `app/game/models.py` - GameScore model
- `app/game/views.py` - Game views (score submission, my scores, leaderboard) with feature flag support
- `app/game/serializers.py` - Game score serializers
- `app/game/urls.py` - URL routing for game endpoints

### Configuration Files
- `app/app/settings.py` - Django project settings
- `app/app/urls.py` - Main URL configuration
- `.env` - Environment variables configuration

### Dashboard Customization
- Modify dashboard statistics in `app/user/views_dashboard.py`
- Customize charts and analytics endpoints
- Add new dashboard metrics and visualizations

### Feature Flag Configuration
- **`GAME_SECTION_ENABLED`** (default: `True`): Set to `False` in `.env` to disable all game features
- **`GAME_LEADERBOARD_ENABLED`** (default: `True`): Set to `False` in `.env` to disable the leaderboard
- **`ENABLE_REPORT_DOWNLOAD`** (default: `True`): Set to `False` in `.env` to disable report downloads

---

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

The admin site features a custom header: **"Login Tracking Dashboard"** with a **"Dashboard"** index title.

### Admin Features
- **User Management**: View, edit, and manage user accounts
- **Email Verification**: View and manage email verification status
- **Bulk Email Verification**: Mark multiple users as email verified via admin action
- **Login Activity Monitoring**: Monitor all user login activities
- **Login Activity Records**: View-only admin interface for login activity records with search by username/IP, filter by success status and date range, sorted by most recent
- **Game Score Records**: View-only admin interface for game scores with search by username/email, sorted by highest score
- **Dashboard Analytics**: Access comprehensive admin dashboard
- **Security Monitoring**: Track security events and suspicious activities
- **Role-based Access Control**: Only superusers can add, edit, or delete users; staff users have view-only access

### Admin Authentication
- **Staff-Only Login**: Regular users are blocked from logging into the Django admin panel. Only users with `is_staff` or `is_superuser` privileges can access the admin login page. Non-staff users see a clear error message: *"Your account does not have admin access. Please log in again with a staff or superuser account."*

### Admin Navigation & UI
- **Frontend "View site" Link**: The "View site" link in the admin header redirects to the frontend application (configured via `FRONTEND_BASE_URL`) instead of the backend root URL
- **Role Badge Display**: The user list page shows a colour-coded role badge for each user:
  - **Superuser** (red) — Full administrative access: Create, Read, Update, and Delete any user record
  - **Staff** (yellow) — Read-only administrative access: View user list, view user details. Cannot add, edit, or delete users
  - **Regular** (green) — Own data only. Regular users cannot access the Django admin panel
- **Permission Info Banner**: A permission banner is displayed at the top of every admin page, showing the logged-in user's role and a description of their access level

### Granular Admin Permissions

| Model | Superuser | Staff |
|-------|-----------|-------|
| **User** | Full CRUD (add, change, view, delete) | View-only (can view user list & details) |
| **LoginActivity** | View & Delete (no add/edit) | View-only (no add/edit/delete) |
| **GameScore** | View & Delete (no add/edit) | View-only (no add/edit/delete) |

- **LoginActivityAdmin**: View-only for staff (search by username/email/IP, filter by success/date). Only superusers can delete records. No one can add or edit login activity records via admin.
- **GameScoreAdmin**: View-only for staff (search by username/email, filter by score/date). Only superusers can delete records. No one can add or edit game scores via admin.
- **Bulk Email Verification**: Admin action to mark multiple users as email verified

---

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