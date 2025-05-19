# Job Recommender System

A comprehensive job search and recommendation platform that helps users find job opportunities matching their skills and experience, provides personalized course recommendations to bridge skill gaps, and offers insightful job market analytics.

## Table of Contents

- [Recent Updates](#recent-updates)
- [Core Features](#core-features)
- [Technical Architecture](#technical-architecture)
- [Implementation Details](#implementation-details)
- [Setup and Installation](#setup-and-installation)
- [Deployment Guide](#deployment-guide)
  - [Development Environment](#development-environment)
  - [Production Environment](#production-environment)
  - [Switching Between Development and Production](#switching-between-development-and-production)
- [Security Configuration](#security-configuration)
- [Monitoring and Health Checks](#monitoring-and-health-checks)
- [Production Readiness](#production-readiness)
- [Rate Limiting](#rate-limiting)
- [Maintenance](#maintenance)

## Recent Updates

### Health Monitoring and Observability
- Implemented comprehensive `/health` endpoint for production monitoring
- Added detailed health checks for all system components (database, APIs, file system)
- Created external health monitoring script with alerting capabilities
- Added Slack and email alerting for system health issues
- Included detailed component status reporting for easier troubleshooting
- Implemented proper HTTP status codes based on system health (200, 503, 500)

### Security and Production Readiness
- Added Flask-Limiter for rate limiting on sensitive endpoints 
- Secured API keys by moving them to environment variables
- Made server host/port configurable via environment variables
- Implemented comprehensive security headers (CSP, HSTS, XSS protection)
- Enforced HTTPS in production environments
- Added proper database connection pooling and timeouts

### Project Organization Improvements
- Removed unnecessary utility scripts used only during development
- Consolidated duplicate dependencies
- Optimized the codebase for production
- Implemented complete error pages (404, 403, 429, 500)
- Updated Gunicorn configuration with security best practices
- Enhanced the wsgi.py file with production optimizations
- Consolidated documentation into a single comprehensive README.md file

### Job Count Standardization
- Implemented consistent job counting methodology across all pages
- Added a central `job_counter.py` utility to standardize job counts
- Fixed inconsistent job count displays between jobs list, dashboard, and insights pages
- Added different job count categories: total jobs, matching jobs, remote jobs, and onsite jobs
- Fixed duplicate job counting bug in database_manager.py that was causing inconsistent counts
- Updated templates to use consistent job count variables across all pages

### Job Scraping and Display
- Fixed the "Browse Jobs" feature to only scrape when necessary:
  - When no jobs are available for the user
  - When the user manually refreshes the job list
  - When the user updates their skills in their profile
- Fixed the "Refresh" button functionality to properly trigger job scraping
- Fixed the loading indicator to work consistently across all job-related actions
- Improved user experience by showing appropriate loading messages
- Added better error handling for failed job scraping operations

### User Skills Integration
- Improved skills synchronization between profile updates and job searches
- Fixed skill matching algorithm to properly handle case-insensitive matching
- Added proper memory of user skills using session storage with user-specific keys

### General Improvements
- Added utility functions to better manage job-related operations
- Fixed loading indicator functionality for better user feedback
- Ensured consistent behavior across all job-related actions

## Core Features

### Job Search and Scraping
- Search for jobs across multiple platforms with Adzuna integration
- Filter jobs by location, skills, and job type (remote/onsite)
- Smart job matching that ranks positions based on skill compatibility
- Automatic calculation of match percentages and identification of skill gaps
- Clear indication of required vs. nice-to-have skills for each job
- Automatic job refreshing based on configurable time thresholds

### Resume and Profile Management
- Intelligent resume parsing with support for PDF, DOCX, and TXT formats
- Automatic extraction of:
  - Professional skills using NLP and pattern matching
  - Work experience with company, title, and date detection
  - Education history with degree, institution, and GPA information
  - Location information for targeted job searches
  - Professional summary and certifications
- Comprehensive profile editor for maintaining skills, education, and work history
- Session-based skill storage with user-specific keys for privacy and personalization

### Course Recommendations
- Personalized course suggestions based on:
  - Identified skill gaps from job requirements
  - User's existing skill set for progressive learning
  - Current job market demand for specific skills
- Course information includes difficulty level, workload, and enrollment statistics
- Direct links to course providers for immediate enrollment

### Job Market Insights
- Interactive data visualizations of job market trends with real-time filtering
- In-depth analysis including:
  - Most in-demand skills with visual indication of user's skills
  - Required vs. nice-to-have skills comparison
  - Geographical job distribution
  - Companies with most job openings
  - Salary distribution and statistics
  - Skills that command higher salaries
  - Remote vs. on-site job distribution
  - Employment type breakdown (full-time, part-time, contract)
  - Experience level distribution across the job market

## Technical Architecture

### Database Structure
The application uses SQLite with the following main tables:
- `user`: Stores user accounts, profile information, and skills
- `work_experience`: Tracks professional history linked to users
- `education`: Manages educational background linked to users
- `jobs`: Stores comprehensive job listings with detailed attributes
- `job_skills`: Maintains skills associated with jobs, categorized as required or nice-to-have

### Core Components

#### Resume Parser (`resume_parser.py`)
- Uses natural language processing (spaCy) to extract structured data from resumes
- Implements sophisticated pattern matching to identify professional elements
- Handles various file formats with dedicated extraction methods
- Processes and normalizes extracted data for consistent database storage

#### Job Scraper (`scraper.py`)
- Connects to job listing APIs and websites to gather current opportunities
- Implements intelligent skill extraction from job descriptions
- Classifies skills as required or nice-to-have based on context analysis
- Handles pagination, error recovery, and duplicate prevention
- User-specific job collection to maintain personalized listings

#### Insights Generator (`insights.py`)
- Creates data visualizations using Matplotlib and Seaborn
- Processes job data using Pandas for identifying market trends
- Implements in-memory graph generation with base64 encoding for efficient delivery
- Provides interactive filtering capabilities for customized analysis
- Generates statistically meaningful representations of job market conditions

#### Standardized Job Counter (`job_counter.py`)
- Provides consistent job counting methodology across all app features
- Categorizes jobs by type: total, matching, remote, and onsite
- Ensures coherent data presentation throughout the user interface

#### Job Utilities (`job_utils.py`, `nlp_utils.py`)
- Centralizes common job-related operations for application-wide consistency
- Implements NLP-based skill extraction and matching algorithms
- Provides location detection and normalization functions
- Handles user skill management across sessions

### Frontend
- Responsive Bootstrap-based UI with custom CSS
- Interactive job filtering and sorting capabilities
- Real-time loading indicators for background operations
- Dynamic content updating with targeted AJAX requests
- Comprehensive error handling with user-friendly notifications

## Implementation Details

### Insights Feature
The Insights feature uses an in-memory approach for creating visualizations:
1. Data is fetched from the database and transformed into Pandas DataFrames
2. Visualization logic processes the data to extract meaningful patterns
3. Matplotlib/Seaborn creates visualizations in memory using BytesIO buffers
4. Images are converted to base64 and embedded directly in the HTML
5. Old static graph files are automatically cleaned up to save storage space

### Job Matching Algorithm
The system uses a sophisticated matching algorithm that:
1. Normalizes skills from both job descriptions and user profiles
2. Performs case-insensitive matching to avoid duplication
3. Weights required skills higher than nice-to-have skills
4. Calculates match percentages based on skill overlap
5. Identifies missing skills to guide user development

### Session Management
User data is maintained securely through:
1. User-specific session keys to prevent data leakage
2. Automatic session cleanup on logout
3. Persistent storage of critical data in the database
4. Temporary storage of sensitive information for active sessions only

## Setup and Installation

### Requirements
- Python 3.8+
- SQLite
- Required packages listed in requirements.txt

### Installation
1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Linux/macOS: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Initialize the database: `python init_database.py`
6. Run the application: `python app.py`
7. Access the application at http://localhost:5000

## Deployment Guide

### Development Environment

#### Setup

1. Create a virtual environment:
   ```
   python -m venv venv
   ```

2. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file from the template:
   ```
   copy .env.template .env
   ```

5. Run the application using the run.py script (recommended):
   
   ```
   python run.py
   ```
   
   This script will:
   - Create the instance directory if needed with proper permissions
   - Initialize the database if it doesn't exist or verify it if it does
   - Run the Flask application

The application will be available at: http://localhost:5000

### Production Environment

#### Production-Ready Setup

1. Clone the repository on your production server:
   ```bash
   git clone [your-repository-url]
   cd job_recommender_system
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. Install production dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create or update `.env` file with production settings:
   ```properties
   # Production environment variables
   FLASK_APP=app.py
   FLASK_ENV=production
   FLASK_DEBUG=False
   
   # Generate a secure random key
   # Python: import secrets; print(secrets.token_hex(32))
   SECRET_KEY=[your-secure-random-key]
   
   # Database configuration (PostgreSQL recommended)
   DATABASE_URL=postgresql://username:password@localhost/job_recommender
   
   # Performance settings
   SQLALCHEMY_ENGINE_OPTIONS_TIMEOUT=30
   SQLALCHEMY_ENGINE_OPTIONS_POOL_SIZE=10
   SQLALCHEMY_ENGINE_OPTIONS_MAX_OVERFLOW=20
   ```

5. Create necessary directories with proper permissions:
   ```bash
   mkdir -p instance logs
   chmod 750 instance logs
   ```

6. Initialize the database:
   ```bash
   # SQLite: Will create the database automatically
   python init_database.py
   
   # PostgreSQL: Run migrations
   flask db upgrade
   ```

#### Running with Gunicorn (Recommended for Production)

1. Install Gunicorn if not already included in requirements:
   ```bash
   pip install gunicorn
   ```

2. Run the application with Gunicorn (adjust workers based on your CPU cores):
   ```bash
   gunicorn --workers=4 --threads=2 --bind=0.0.0.0:8000 --log-level=info --access-logfile=logs/access.log --error-logfile=logs/error.log wsgi:app
   ```

   Parameters explained:
   - `--workers=4`: Number of worker processes (2-4 × CPU cores)
   - `--threads=2`: Threads per worker
   - `--bind=0.0.0.0:8000`: Listen on all interfaces, port 8000
   - `--log-level=info`: Logging level
   - `--access-logfile`: Access log file
   - `--error-logfile`: Error log file

3. For testing, you can access the application at http://your-server-ip:8000

#### Setting Up Nginx as a Reverse Proxy

1. Install Nginx:
   ```bash
   # Debian/Ubuntu
   sudo apt install nginx
   
   # CentOS/RHEL
   sudo yum install nginx
   ```

2. Create a configuration file (e.g., `/etc/nginx/sites-available/job_recommender`):
   ```nginx
   server {
       listen 80;
       server_name your-domain.com www.your-domain.com;
       
       access_log /var/log/nginx/job_recommender-access.log;
       error_log /var/log/nginx/job_recommender-error.log;
       
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
       
       location /static {
           alias /path/to/job_recommender_system/static;
           expires 30d;
       }
   }
   ```

3. Enable the site and restart Nginx:
   ```bash
   sudo ln -s /etc/nginx/sites-available/job_recommender /etc/nginx/sites-enabled/
   sudo nginx -t  # Test configuration
   sudo systemctl restart nginx
   ```

#### Setting Up a Process Manager (systemd)

1. Create a systemd service file `/etc/systemd/system/job_recommender.service`:
   ```ini
   [Unit]
   Description=Job Recommender Gunicorn Daemon
   After=network.target postgresql.service
   
   [Service]
   User=www-data
   Group=www-data
   WorkingDirectory=/path/to/job_recommender_system
   Environment="PATH=/path/to/job_recommender_system/venv/bin"
   ExecStart=/path/to/job_recommender_system/venv/bin/gunicorn \
             --workers 4 \
             --threads 2 \
             --bind 127.0.0.1:8000 \
             --log-level info \
             --access-logfile logs/access.log \
             --error-logfile logs/error.log \
             wsgi:app
   
   Restart=on-failure
   RestartSec=5s
   
   [Install]
   WantedBy=multi-user.target
   ```

2. Enable and start the service:
   ```bash
   sudo systemctl enable job_recommender
   sudo systemctl start job_recommender
   sudo systemctl status job_recommender  # Check service status
   ```

#### Configuring a Production Database (PostgreSQL)

For production, PostgreSQL is strongly recommended over SQLite:

1. Install PostgreSQL:
   ```bash
   # Debian/Ubuntu
   sudo apt install postgresql postgresql-contrib
   
   # CentOS/RHEL
   sudo yum install postgresql-server postgresql-contrib
   sudo postgresql-setup initdb
   sudo systemctl start postgresql
   ```

2. Create a database and user:
   ```bash
   sudo -u postgres psql
   
   postgres=# CREATE DATABASE job_recommender;
   postgres=# CREATE USER job_recommender_user WITH ENCRYPTED PASSWORD 'secure_password';
   postgres=# GRANT ALL PRIVILEGES ON DATABASE job_recommender TO job_recommender_user;
   postgres=# \q
   ```

3. Update your `.env` file with PostgreSQL connection details:
   ```
   DATABASE_URL=postgresql://job_recommender_user:secure_password@localhost/job_recommender
   ```

4. Install the PostgreSQL adapter in your virtual environment:
   ```bash
   pip install psycopg2-binary
   ```

5. Run migrations:
   ```bash
   flask db upgrade
   ```

### Switching Between Development and Production

To run in development mode locally:
```
export FLASK_ENV=development
export FLASK_DEBUG=True
python app.py
```

To run in production-like mode locally:
```
export FLASK_ENV=production
export FLASK_DEBUG=False
gunicorn --bind 0.0.0.0:8000 wsgi:app
```

## Security Configuration

### Security Features

The system includes the following security features:

1. **Rate Limiting**
   - Login and registration endpoints are protected from brute-force attacks
   - Default rate limiting for all endpoints: 200 requests per day, 50 per hour
   - Custom rate limits for sensitive routes

2. **Security Headers**
   - Content Security Policy (CSP) to prevent XSS attacks
   - X-Content-Type-Options to prevent MIME type sniffing
   - X-Frame-Options to prevent clickjacking
   - X-XSS-Protection to enable browser's XSS protection
   - Strict-Transport-Security (HSTS) for HTTPS enforcement
   - Referrer-Policy for controlling HTTP referer information
   - Permissions-Policy (formerly Feature-Policy) to control browser features

3. **HTTPS Enforcement**
   - Production environment enforces HTTPS connections
   - HTTP requests are redirected to HTTPS

4. **Credential Management**
   - API keys and credentials stored in environment variables
   - Database credentials configurable via environment variables
   - Secret key for session management configurable via environment variables

### Configuration Steps

#### Set Up HTTPS

For production deployment, HTTPS is essential. You can:

1. Use Let's Encrypt for free SSL certificates:
   ```bash
   sudo apt-get install certbot python3-certbot-nginx
   sudo certbot --nginx -d yourdomain.com
   ```

2. Update your Nginx configuration to include:
   ```nginx
   server {
       listen 443 ssl;
       server_name yourdomain.com;
       
       ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
       
       # Strong SSL settings
       ssl_protocols TLSv1.2 TLSv1.3;
       ssl_prefer_server_ciphers on;
       ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
       
       # HSTS (comment out if you face issues)
       add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
   }
   ```

#### Secure File Permissions

```bash
# Set proper ownership
sudo chown -R www-data:www-data /path/to/job_recommender_system

# Set proper permissions
find /path/to/job_recommender_system -type d -exec chmod 750 {} \;
find /path/to/job_recommender_system -type f -exec chmod 640 {} \;

# Make .env file accessible only to www-data
chmod 600 /path/to/job_recommender_system/.env

# Ensure instance folder is writable
chmod 770 /path/to/job_recommender_system/instance
```

#### Regular Security Checks

1. **Database Backup**:
   ```bash
   pg_dump -U postgres job_recommender > backup_$(date +%Y%m%d).sql
   ```

2. **Run Security Scan**:
   ```bash
   # Install safety
   pip install safety
   # Check for vulnerable dependencies
   safety check -r requirements.txt
   ```

3. **Regular Security Updates**:
   ```bash
   sudo apt-get update
   sudo apt-get upgrade
   ```

## Monitoring and Health Checks

### Health Check Endpoint

The system provides a comprehensive `/health` endpoint that returns detailed information about the health of all components.

#### Accessing the Health Check

```
GET /health
```

#### Response Format

```json
{
  "status": "healthy",  // or "degraded" or "unhealthy"
  "timestamp": "2025-05-18T00:45:12.345Z",
  "environment": "production",
  "database": {
    "status": "healthy",
    "message": "Database connection successful (query time: 0.002s)"
  },
  "api": {
    "coursera": {
      "status": "healthy",
      "response_time": "0.543s",
      "status_code": 200
    }
  },
  "file_system": {
    "status": "healthy",
    "details": {
      "instance": {
        "exists": true,
        "writable": true,
        "readable": true
      },
      "uploads": {
        "exists": true,
        "writable": true,
        "readable": true
      }
    }
  },
  "environment_vars": {
    "status": "healthy",
    "missing_vars": []
  }
}
```

#### Status Codes

- **200 OK**: All components are healthy
- **503 Service Unavailable**: Some components are degraded but system is operational
- **500 Internal Server Error**: Critical components (like database) are down

### Automated Monitoring

The system can be monitored using regular health checking scripts:

#### Setting up a Cron Job

```bash
# Run every 15 minutes
*/15 * * * * /path/to/venv/bin/python /path/to/monitor_health.py --url=https://yourdomain.com/health
```

### Log Monitoring

Set up log monitoring to track important events and errors:

1. Configure centralized logging:
   ```bash
   # Example using rsyslog
   sudo vim /etc/rsyslog.d/30-job-recommender.conf
   
   # Add these lines
   if $programname == 'job_recommender' then /var/log/job_recommender.log
   & stop
   ```

2. Set up log rotation:
   ```bash
   sudo vim /etc/logrotate.d/job_recommender
   
   # Add these lines
   /var/log/job_recommender.log {
       daily
       rotate 14
       compress
       delaycompress
       missingok
       notifempty
       create 0640 www-data adm
   }
   ```

## Production Readiness

The Job Recommender System is fully production-ready with the following features:

### Health Monitoring & Observability

✅ **Comprehensive Health Check System**
- Detailed `/health` endpoint with HTTP status codes (200/503/500) based on system state
- Component-level health checks for database, API services, file system, and environment variables
- Health_check.py module with thorough system component validation

### Security Features

✅ **Web Security**
- Content Security Policy (CSP) headers
- HSTS for secure connections
- XSS protections
- Clickjacking protection
- Security.py module with comprehensive security functions
- HTTPS enforcement for production environments

✅ **Rate Limiting**
- Flask-Limiter configuration with on_breach parameter
- Rate limiting for sensitive endpoints (login, registration)
- Proper error handling for rate limit breaches

✅ **Authentication & Authorization**
- Secure password hashing with bcrypt
- Proper session management
- Restricting sensitive routes with @login_required decorator
- User credential validation

### Error Handling

✅ **Comprehensive Error Pages**
- Custom error templates for 404, 403, 429, and 500 errors
- Detailed error logging with traceback
- User-friendly error messages
- Proper HTTP status codes for all error responses

### Database Optimizations

✅ **Connection Pooling**
- SQLAlchemy connection pool configuration
- Timeouts for database operations
- Proper pool_size and max_overflow parameters
- Database connection validation on startup

## Rate Limiting

### Implementation

Rate limiting is implemented using Flask-Limiter 3.5.0:

```python
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",  # Uses in-memory storage for development
    strategy="fixed-window",  # Uses a fixed window strategy for counting requests
    on_breach=limiter_handler  # Custom handler for rate limit breaches
)
```

### Route-Specific Rate Limits

Sensitive routes have stricter rate limits:

- Login: 10 requests per minute
- Registration: 10 requests per hour

Example:

```python
@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    # Login logic here
```

### Production Considerations

For production deployment:

1. Consider using a distributed storage backend like Redis for rate limiting:
   ```python
   limiter = Limiter(
       get_remote_address, 
       app=app,
       storage_uri="redis://localhost:6379"
   )
   ```
