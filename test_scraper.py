"""Script to test the job scraping functionality"""
import sys
import logging
from datetime import datetime
from database_manager import init_db, get_all_jobs
from scraper import scrape_jobs

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_scraper():
    """Test the job scraping functionality"""
    try:
        # Initialize database
        init_db()
        
        # Test user ID
        test_user_id = 1
        
        # Test scraping jobs
        print("Starting test scrape...")
        jobs = scrape_jobs(
            query="Python",
            location="India",
            user_skills=["Python", "SQL", "JavaScript"],
            pages=1,
            force_clear=True,
            user_id=test_user_id
        )
        
        # Check results
        if jobs:
            print(f"Successfully scraped {len(jobs)} jobs!")
            # Print details of first job
            if len(jobs) > 0:
                first_job = jobs[0]
                print("\nFirst job details:")
                print(f"Title: {first_job.get('title')}")
                print(f"Company: {first_job.get('company')}")
                print(f"Skills: {first_job.get('skills')}")
        else:
            print("No jobs found in the scrape")
            
        # Verify jobs in database
        all_jobs = get_all_jobs()
        print(f"\nTotal jobs in database: {len(all_jobs)}")
        
    except Exception as e:
        print(f"Error during test: {e}", file=sys.stderr)
        raise

if __name__ == "__main__":
    test_scraper()
