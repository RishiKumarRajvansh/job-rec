# Hostinger Deployment Guide for Job Recommender System

## Prerequisites
- A Hostinger account with Python support (Premium or Business plan)
- SSH access enabled on your Hostinger account
- Basic knowledge of terminal commands

## Step 1: Purchase and Set Up Hosting

1. Log in to your Hostinger account
2. Purchase a hosting plan that supports Python applications (Premium or Business)
3. Set up your domain name and wait for DNS propagation

## Step 2: Prepare Your Local Files

1. Ensure you have the following files ready:
   - All application code
   - passenger_wsgi.py
   - .env.production (renamed to .env on the server)
   - requirements.txt
   - deploy.sh

2. Create a ZIP archive of your project:
   ```
   zip -r job_recommender.zip . -x "*.git*" -x "__pycache__/*" -x "*.pyc" -x "env/*" -x "venv/*"
   ```

## Step 3: Upload Files to Hostinger

### Option A: Using the Hostinger File Manager
1. Log in to your Hostinger control panel
2. Navigate to File Manager
3. Upload the ZIP file of your project
4. Extract the ZIP file to your public_html directory

### Option B: Using FTP
1. Use an FTP client like FileZilla
2. Connect to your Hostinger account using the FTP credentials from your Hostinger dashboard
3. Upload the ZIP file to your public_html directory
4. Extract the ZIP file

### Option C: Using SSH (Recommended for larger files)
1. Connect to your server via SSH:
   ```
   ssh u123456789@your-server-ip
   ```
2. Navigate to your public_html directory:
   ```
   cd public_html
   ```
3. Use SCP to upload your ZIP file from your local machine
4. Extract the ZIP file:
   ```
   unzip job_recommender.zip
   ```

## Step 4: Set Up the Python Environment

1. Connect to your server via SSH
2. Navigate to your application directory:
   ```
   cd public_html
   ```
3. Run the deployment script:
   ```
   bash deploy.sh
   ```

## Step 5: Configure Python Version

1. In the Hostinger control panel, navigate to "Advanced" > "Python"
2. Select Python version 3.10 or higher
3. Set the application path to your public_html directory
4. Set the application startup file to passenger_wsgi.py
5. Click "Save" to apply changes

## Step 6: Set Up a Custom Domain (Optional)

1. In the Hostinger control panel, navigate to "Domains"
2. Add your custom domain and follow the instructions to set it up

## Step 7: Test Your Application

1. Visit your domain in a web browser
2. Verify that all features work correctly
3. Check the error logs if you encounter any issues:
   ```
   tail -f ~/logs/error.log
   ```

## Step 8: Set Up SSL Certificate

1. In the Hostinger control panel, navigate to "SSL/TLS"
2. Enable the free Let's Encrypt SSL certificate
3. Follow the instructions to complete the process

## Troubleshooting

### Application Shows 500 Error
1. Check the error logs:
   ```
   tail -f ~/logs/error.log
   ```
2. Ensure all file permissions are set correctly:
   ```
   chmod 755 passenger_wsgi.py
   chmod -R 755 templates static
   chmod -R 700 instance uploads
   ```
3. Verify Python version compatibility

### Database Connection Issues
1. Check if SQLite database exists and has proper permissions
2. If using PostgreSQL, verify connection credentials in .env file

### Static Files Not Loading
1. Verify static file paths in Flask configuration
2. Ensure static directory has proper permissions

## Maintenance

### Updating Your Application
1. Make changes to your local repository
2. Create a new ZIP file excluding unnecessary files
3. Upload to server and extract, replacing existing files
4. Restart the application if needed

### Database Backups
1. Set up regular backups of your database:
   ```
   # For SQLite
   cp instance/job_recommender.db instance/job_recommender.db.backup
   ```
2. Download backups regularly to your local machine
