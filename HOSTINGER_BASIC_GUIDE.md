# Hostinger Basic Plan Deployment Guide

## Initial Setup

1. **Log into your Hostinger account**
   - Go to hPanel (Hostinger's control panel)

2. **Set up Python Application**
   - Navigate to "Advanced" > "Python"
   - Enable Python support
   - Set application path to your public_html directory
   - Set Python version to 3.8 (or the highest available version)
   - Save changes

## File Upload

1. **Upload your files**
   - Access File Manager in hPanel
   - Navigate to public_html folder
   - Upload the ZIP file you created
   - Extract the ZIP file in the public_html directory

2. **Set up file permissions**
   - Connect via SSH or use File Manager
   - Make the deploy.sh executable:
     ```
     chmod +x deploy.sh
     ```

## Database Setup

1. **Execute the deployment script**
   - Connect via SSH:
     ```
     ssh u123456789@your-server-name.com
     ```
   - Navigate to your public_html directory:
     ```
     cd public_html
     ```
   - Run the deployment script:
     ```
     ./deploy.sh
     ```

## Configuration

1. **Check Python configuration**
   - Ensure Python application is enabled in hPanel
   - Verify Python version is set correctly
   - Make sure the passenger_wsgi.py file is set as the entry point

2. **Set up domain**
   - In hPanel, go to "Domains"
   - Assign your domain to the hosting account
   - Set up DNS records if needed

3. **Enable SSL**
   - In hPanel, go to "SSL"
   - Enable Let's Encrypt SSL
   - Follow the prompts to complete SSL setup

## Testing Your Deployment

1. **Access your site**
   - Visit your domain in a web browser

2. **Check the health endpoint**
   - Visit yourdomain.com/health
   - Should show status "online"

3. **Check error logs if needed**
   - SSH into your server
   - Check error logs:
     ```
     tail -f ~/logs/error.log
     ```

## Troubleshooting

1. **Application shows 500 error**
   - Check if Python is enabled in hPanel
   - Verify file permissions
   - Check error logs for specific issues

2. **Static files are not loading**
   - Check .htaccess configuration
   - Verify file permissions on static directory

3. **Database errors**
   - Ensure instance directory has correct permissions
   - Try reinitializing database with:
     ```
     python3 init_database.py
     ```

## Regular Maintenance

1. **Backup your database regularly**
   - SSH into your server
   - Create a backup:
     ```
     cp instance/job_recommender.db instance/job_recommender.db.backup
     ```

2. **Check application logs**
   - Monitor logs for errors:
     ```
     tail -f logs/app.log
     ```
