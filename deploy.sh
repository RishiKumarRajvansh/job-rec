#!/bin/bash
# Deployment script for Job Recommender System on Hostinger Basic Plan

echo "Starting deployment process for Job Recommender System..."

# Create necessary directories if they don't exist
echo "Creating required directories..."
mkdir -p instance
mkdir -p static/graphs
mkdir -p uploads
mkdir -p logs

# Set proper permissions for Hostinger environment
echo "Setting file and directory permissions..."
chmod 755 passenger_wsgi.py
chmod 755 wsgi.py
chmod -R 755 static
chmod -R 755 templates
chmod -R 700 instance
chmod -R 700 uploads
chmod -R 755 logs

# Install Python dependencies using pip3 with user flag for shared hosting
echo "Installing Python dependencies..."
pip3 install --user -r requirements.txt

# Check if the installation was successful
if [ $? -ne 0 ]; then
    echo "WARNING: Some dependencies may not have installed correctly."
    echo "You might need to install them manually or contact Hostinger support."
fi

# Initialize the database if it doesn't exist
if [ ! -f "instance/job_recommender.db" ]; then
    echo "Initializing database..."
    python3 init_database.py
fi

# Set environment to production
echo "Setting up environment configuration..."
cp .env.production .env

# Verify .htaccess exists, create if it doesn't
if [ ! -f ".htaccess" ]; then
    echo "Creating .htaccess file..."
    echo "RewriteEngine On
RewriteBase /
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^(.*)$ /passenger_wsgi.py/$1 [L]
SetEnv FLASK_APP wsgi.py
SetEnv FLASK_ENV production
SetEnv FLASK_DEBUG False" > .htaccess
fi

# Create a test file to verify the deployment
echo "<?php phpinfo(); ?>" > phpinfo.php

echo "Running pre-flight checks..."

# Check if Python is available
if command -v python3 &> /dev/null; then
    echo "✓ Python is installed"
    python3 --version
else
    echo "✗ Python not found - deployment may fail"
fi

echo "Deployment setup complete!"
echo "---------------------------------------"
echo "Next steps:"
echo "1. Visit your website domain to verify it's working"
echo "2. Check /health to verify the application status"
echo "3. If you encounter issues, check the logs folder"
echo "---------------------------------------"
