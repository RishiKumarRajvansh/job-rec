import sys
import os
import logging

# Configure logging for troubleshooting deployment issues
logging.basicConfig(
    filename='passenger_error.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    # Hostinger basic plan typically uses Python 3.8
    INTERP = os.path.expanduser("/usr/bin/python3.8")
    if sys.executable != INTERP:
        os.execl(INTERP, INTERP, *sys.argv)
    
    # Add current directory to path
    sys.path.append(os.getcwd())
    
    # Log current environment
    logger.info(f"Current directory: {os.getcwd()}")
    logger.info(f"Python version: {sys.version}")
    
    # Load environment variables from .env file
    from dotenv import load_dotenv
    load_dotenv('.env')
    
    # Import Flask app - this is what Passenger will use
    from app import app as application
    
    logger.info("Passenger WSGI loaded successfully")
except Exception as e:
    logger.error(f"Error in passenger_wsgi.py: {str(e)}")
    import traceback
    logger.error(traceback.format_exc())
