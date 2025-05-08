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
        skills TEXT,
        salary TEXT,
        job_type TEXT,
        source_url TEXT,
        platform TEXT
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
        education_summary TEXT
    )
    ''')
    
    conn.commit()
    conn.close()
    
    print(f"Database '{DB_PATH}' initialized and tables ensured.")

def save_job_to_db(job_data):
    """Save a job to the database (alias for add_job for compatibility)."""
    # Check if job with same title and company already exists to avoid duplicates
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Convert skills list to JSON string if it's a list
    job_data_copy = job_data.copy()
    if 'skills' in job_data_copy and isinstance(job_data_copy['skills'], list):
        job_data_copy['skills'] = json.dumps(job_data_copy['skills'])
    
    # Check for duplicates
    if 'title' in job_data_copy and 'company' in job_data_copy:
        cursor.execute(
            "SELECT id FROM jobs WHERE title = ? AND company = ?", 
            (job_data_copy['title'], job_data_copy['company'])
        )
        existing_job = cursor.fetchone()
        
        if existing_job:
            conn.close()
            print(f"Job already exists: {job_data_copy['title']} at {job_data_copy['company']}")
            return existing_job[0]  # Return existing job ID
    
    conn.close()
    return add_job(job_data_copy)

def add_job(job_data):
    """Add a job to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
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
    
    # Only get jobs from scraper (exclude sample jobs)
    cursor.execute("""
    SELECT * FROM jobs 
    WHERE source_url IS NOT NULL
    """)
    
    jobs = cursor.fetchall()
    
    # Convert Row objects to dictionaries
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
    
    conn.close()
    return jobs_list

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
    query_terms = f"%{query}%" if query and query.lower() != 'all' else "%"
    location_terms = f"%{location}%" if location and location.lower() != 'all' else "%"
    
    # Basic search query - only include scraped jobs
    cursor.execute("""
    SELECT * FROM jobs 
    WHERE (title LIKE ? OR description LIKE ? OR company LIKE ?)
    AND (location LIKE ?)
    AND source_url IS NOT NULL
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
    
    if job:
        job_dict = dict(job)
        
        # Parse skills from JSON string if needed
        if 'skills' in job_dict and isinstance(job_dict['skills'], str):
            try:
                job_dict['skills'] = json.loads(job_dict['skills'])
            except json.JSONDecodeError:
                # If not valid JSON, try splitting by comma
                job_dict['skills'] = job_dict['skills'].split(',') if job_dict['skills'] else []
        
        conn.close()
        return job_dict
    
    conn.close()
    return None

# If this file is run directly, initialize the database
if __name__ == "__main__":
    init_db()
    print("Database initialized. No sample jobs added.")
