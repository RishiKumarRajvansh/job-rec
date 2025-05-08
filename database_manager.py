import sqlite3
import os
import json
from datetime import datetime

# Database file path
DB_PATH = 'instance/job_recommender.db'

def get_db_connection():
    """Create a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    return conn

def init_db():
    """Initialize the database with required tables if they don't exist."""
    # Ensure the instance directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create jobs table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        company TEXT,
        location TEXT,
        url TEXT,
        description TEXT,
        snippet TEXT,
        source TEXT,
        date_posted TEXT,
        skills TEXT,
        salary TEXT,
        job_type TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create users table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        skills TEXT,
        experience_summary TEXT,
        education_summary TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()
    
    print(f"Database '{DB_PATH}' initialized and 'jobs' table ensured.")

def add_job(job_data):
    """Add a job to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Convert skills list to JSON string if it's a list
    if 'skills' in job_data and isinstance(job_data['skills'], list):
        job_data['skills'] = json.dumps(job_data['skills'])
    
    # Get column names from the job_data dictionary
    columns = ', '.join(job_data.keys())
    placeholders = ', '.join(['?' for _ in job_data])
    values = list(job_data.values())
    
    query = f"INSERT INTO jobs ({columns}) VALUES ({placeholders})"
    
    cursor.execute(query, values)
    conn.commit()
    job_id = cursor.lastrowid
    conn.close()
    
    return job_id

def get_all_jobs():
    """Get all jobs from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM jobs ORDER BY date_posted DESC")
    jobs = cursor.fetchall()
    
    conn.close()
    return jobs

def search_jobs_db(query, location, resume_skills=None):
    """
    Search for jobs in the database based on query and location.
    
    Args:
        query (str): Job title or keywords
        location (str): Job location
        resume_skills (list): List of skills from the user's resume
        
    Returns:
        list: List of matching jobs
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Prepare search terms
    query_terms = f"%{query}%" if query else "%"
    location_terms = f"%{location}%" if location else "%"
    
    # Basic search query
    cursor.execute("""
    SELECT * FROM jobs 
    WHERE (title LIKE ? OR description LIKE ? OR company LIKE ?) 
    AND (location LIKE ?)
    ORDER BY date_posted DESC
    """, (query_terms, query_terms, query_terms, location_terms))
    
    jobs = cursor.fetchall()
    conn.close()
    
    # Convert SQLite Row objects to dictionaries
    jobs_list = []
    for job in jobs:
        job_dict = dict(job)
        
        # Parse skills from JSON string if needed
        if 'skills' in job_dict and isinstance(job_dict['skills'], str):
            try:
                job_dict['skills'] = json.loads(job_dict['skills'])
            except json.JSONDecodeError:
                # If not valid JSON, try splitting by comma
                job_dict['skills'] = job_dict['skills'].split(',') if job_dict['skills'] else []
        
        jobs_list.append(job_dict)
    
    # If resume skills are provided, calculate matching skills and sort by matches
    if resume_skills:
        for job in jobs_list:
            job_skills = [s.lower() for s in job.get('skills', [])]
            resume_skills_lower = [s.lower() for s in resume_skills]
            
            # Count matching skills
            matching_skills = sum(1 for s in resume_skills_lower if s in job_skills)
            job['matching_resume_skills'] = matching_skills
        
        # Sort by number of matching skills (descending)
        jobs_list.sort(key=lambda x: x.get('matching_resume_skills', 0), reverse=True)
    
    return jobs_list

def get_job_by_id(job_id):
    """Get a job by its ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
    job = cursor.fetchone()
    
    conn.close()
    return dict(job) if job else None

def add_sample_jobs():
    """Add sample jobs to the database for testing."""
    sample_jobs = [
        {
            'title': 'Python Developer',
            'company': 'Tech Solutions Inc.',
            'location': 'London, UK',
            'url': 'https://example.com/jobs/1',
            'description': 'We are looking for a Python developer with experience in Flask and Django.',
            'snippet': 'Python developer needed for web application development using Flask and Django.',
            'source': 'Sample Data',
            'date_posted': datetime.now().strftime('%Y-%m-%d'),
            'skills': json.dumps(['Python', 'Flask', 'Django', 'SQL', 'Git']),
            'salary': '£50,000 - £65,000',
            'job_type': 'Full-time'
        },
        {
            'title': 'Data Scientist',
            'company': 'Data Insights Ltd.',
            'location': 'Remote',
            'url': 'https://example.com/jobs/2',
            'description': 'Join our team as a Data Scientist working on machine learning models.',
            'snippet': 'Data Scientist position available for someone with strong ML skills.',
            'source': 'Sample Data',
            'date_posted': datetime.now().strftime('%Y-%m-%d'),
            'skills': json.dumps(['Python', 'Machine Learning', 'TensorFlow', 'SQL', 'Statistics']),
            'salary': '£60,000 - £75,000',
            'job_type': 'Full-time'
        },
        {
            'title': 'Frontend Developer',
            'company': 'Web Creations',
            'location': 'Manchester, UK',
            'url': 'https://example.com/jobs/3',
            'description': 'Frontend developer needed to work on responsive web applications.',
            'snippet': 'Looking for a frontend developer with React experience.',
            'source': 'Sample Data',
            'date_posted': datetime.now().strftime('%Y-%m-%d'),
            'skills': json.dumps(['JavaScript', 'React', 'HTML', 'CSS', 'Git']),
            'salary': '£45,000 - £55,000',
            'job_type': 'Full-time'
        }
    ]
    
    for job in sample_jobs:
        add_job(job)
    
    print(f"Added {len(sample_jobs)} sample jobs to the database.")

# If this file is run directly, initialize the database and add sample jobs
if __name__ == "__main__":
    init_db()
    add_sample_jobs()
