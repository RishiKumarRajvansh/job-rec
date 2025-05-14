import os
import logging
from database_manager import initialize_database, create_test_user, DB_PATH

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def main():
    """Initialize the database and create test user."""
    try:
        # Ensure the instance directory exists
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        
        # Remove existing database if it exists
        if os.path.exists(DB_PATH):
            logger.info(f"Removing existing database at {DB_PATH}")
            os.remove(DB_PATH)
            
        # Initialize database with all tables
        logger.info("Initializing database...")
        if not initialize_database():
            logger.error("Failed to initialize database")
            return False
            
        # Create test user
        logger.info("Creating test user...")
        user_id = create_test_user()
        if not user_id:
            logger.error("Failed to create test user")
            return False
            
        logger.info(f"Database initialized successfully with test user (ID: {user_id})")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return False

if __name__ == "__main__":
    main()
