"""Fix job scraper functionality"""

import os
import logging
import sys
from database_manager import initialize_database, check_database

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_database():
    """Initialize and repair the database structure."""
    try:
        print("Initializing database fix...")
        
        # Initialize database and create tables
        if not initialize_database():
            raise Exception("Failed to initialize database")
            
        # Check database state
        if not check_database():
            raise Exception("Database check failed")
            
        # Run a test scrape
        from scraper import scrape_jobs
        jobs = scrape_jobs(
            query="Python",
            location="India", 
            user_skills=["Python", "SQL", "JavaScript"],
            pages=1,
            force_clear=True,
            user_id=1
        )
        
        print(f"Test scrape completed. Found {len(jobs)} jobs.")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    # Try to fix the database
    success = fix_database()
    if success:
        print("Fix completed successfully!")
    else:
        print("Fix failed. Please check the error messages above.")
