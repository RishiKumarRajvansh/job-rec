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

def clear_jobs_table():
    """Clear all jobs from the database to prepare for fresh scraping."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM jobs")
        conn.commit()
        print("Jobs table cleared for fresh scraping.")
    except sqlite3.Error as e:
        print(f"Error clearing jobs table: {e}")
        conn.rollback()  # Rollback any changes in case of error
        raise  # Re-raise the exception to be handled upstream
    finally:
        conn.close()

def clear_jobs_database():
    """
    Clear all jobs from the database before a new scraping session
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM jobs")
        conn.commit()
        print("Jobs database cleared successfully")
    except Exception as e:
        print(f"Error clearing jobs database: {e}")
        conn.rollback()
    finally:
        conn.close()
        
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
    
    # Get all jobs
    cursor.execute("SELECT * FROM jobs")
    
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
        
        jobs_list.append(job_dict)  # This line is incorrectly indented in your code
    
    conn.close()
    return jobs_list


# def search_jobs_db(query, location, resume_skills=None):
#     """
#     Search for jobs in the database based on query and location.
    
#     Args:
#         query (str): Job title or keywords
#         location (str): Job location
#         resume_skills (list): List of skills from the user's resume
        
#     Returns:
#         list: List of matching jobs
#     """
#     conn = get_db_connection()
#     cursor = conn.cursor()
    
#     # Prepare search terms
#     query_terms = f"%{query}%" if query and query.lower() != 'all' else "%"
#     location_terms = f"%{location}%" if location and location.lower() != 'all' else "%"
    
#     # Basic search query
#     cursor.execute("""
#     SELECT * FROM jobs 
#     WHERE (title LIKE ? OR description LIKE ? OR company LIKE ?)
#     AND (location LIKE ?)
#     """, (query_terms, query_terms, query_terms, location_terms))
    
#     jobs = cursor.fetchall()
#     conn.close()
    
#     # Convert SQLite Row objects to dictionaries
#     jobs_list = []
#     for job in jobs:
#         job_dict = dict(job)
        
#         # Parse skills from JSON string if needed
#         if 'skills' in job_dict and isinstance(job_dict['skills'], str):
#             try:
#                 job_dict['skills'] = json.loads(job_dict['skills'])
#             except json.JSONDecodeError:
#                 # If not valid JSON, try splitting by comma
#                 job_dict['skills'] = job_dict['skills'].split(',') if job_dict['skills'] else []
        
#         jobs_list.append(job_dict)
    
#     # If resume skills are provided, calculate matching skills and sort by matches
#     if resume_skills:
#         for job in jobs_list:
#             job_skills = [s.lower() for s in job.get('skills', [])]
#             resume_skills_lower = [s.lower() for s in resume_skills]
            
#             # Count matching skills
#             matching_skills = sum(1 for s in resume_skills_lower if s in job_skills)
#             job['matching_resume_skills'] = matching_skills
        
#         # Sort by number of matching skills (descending)
#         jobs_list.sort(key=lambda x: x.get('matching_resume_skills', 0), reverse=True)
    
#     return jobs_list
def search_jobs_db(query, location, resume_skills=None, match_any=True):
    """
    Search for jobs in the database based on query and location.
    
    Args:
        query (str): Search query
        location (str): Location to search in
        resume_skills (list): List of skills from resume
        match_any (bool): If True, match any skill; if False, match all skills
        
    Returns:
        list: List of matching jobs
    """
    print(f"Searching jobs with query: '{query}', location: '{location}'")
    
    if resume_skills:
        print(f"Using resume skills: {resume_skills}")
    
    conn = get_db_connection()
    
    # Modify location search to handle NCR/Delhi equivalence
    location_search = location
    if location.lower() == 'delhi':
        # Search for either Delhi or NCR
        location_condition = "(location LIKE ? OR location LIKE ?)"
        location_params = [f"%{location}%", "%NCR%"]
    else:
        location_condition = "location LIKE ?"
        location_params = [f"%{location}%"]
    
    if query.lower() == 'all' and location.lower() == 'all':
        # Return all jobs
        jobs = conn.execute('SELECT * FROM jobs').fetchall()
    elif resume_skills and match_any:
        # Match any skill from resume
        # Create a SQL query with multiple LIKE conditions for skills
        sql_query = "SELECT * FROM jobs WHERE ("
        
        # Add conditions for each skill
        skill_conditions = []
        params = []
        for skill in resume_skills:
            skill_conditions.append(f"title LIKE ? OR description LIKE ? OR company LIKE ? OR snippet LIKE ?")
            params.extend([f"%{skill}%", f"%{skill}%", f"%{skill}%", f"%{skill}%"])
        
        sql_query += " OR ".join(skill_conditions)
        sql_query += ")"
        
        # Add location condition if specified
        if location.lower() != 'all':
            sql_query += f" AND {location_condition}"
            params.extend(location_params)
        
        print("SQL Query: ", sql_query)
        print("Params:", params)
        
        jobs = conn.execute(sql_query, params).fetchall()
    else:
        # Simple search with query and location
        if query.lower() == 'all':
            if location.lower() == 'all':
                sql_query = "SELECT * FROM jobs"
                params = []
            else:
                sql_query = f"SELECT * FROM jobs WHERE {location_condition}"
                params = location_params
        elif location.lower() == 'all':
            sql_query = "SELECT * FROM jobs WHERE title LIKE ? OR description LIKE ? OR company LIKE ? OR snippet LIKE ?"
            params = [f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%"]
        else:
            sql_query = f"SELECT * FROM jobs WHERE (title LIKE ? OR description LIKE ? OR company LIKE ? OR snippet LIKE ?) AND {location_condition}"
            params = [f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%"] + location_params
        
        print("SQL Query: ", sql_query)
        print("Params:", params)
        
        jobs = conn.execute(sql_query, params).fetchall()
    
    # Convert rows to dictionaries
    job_list = []
    for job in jobs:
        job_dict = dict(job)
        
        # Parse skills from JSON string if needed
        if 'skills' in job_dict and isinstance(job_dict['skills'], str):
            try:
                job_dict['skills'] = json.loads(job_dict['skills'])
            except json.JSONDecodeError:
                # If not valid JSON, try splitting by comma
                job_dict['skills'] = job_dict['skills'].split(',') if job_dict['skills'] else []
        
        # Calculate matching skills if resume_skills is provided
        if resume_skills:
            job_skills = job_dict.get('skills', [])
            if isinstance(job_skills, str):
                job_skills = job_skills.split(',')
            
            job_skills_lower = [s.lower() for s in job_skills]
            resume_skills_lower = [s.lower() for s in resume_skills]
            matching_skills = [skill for skill in resume_skills_lower if skill.lower() in job_skills_lower]
            job_dict['matching_skills'] = matching_skills
            job_dict['matching_resume_skills'] = len(matching_skills)
            job_dict['match_percentage'] = round((len(matching_skills) / len(resume_skills)) * 100) if resume_skills else 0
        
        job_list.append(job_dict)
    
    # Sort by match percentage if resume_skills is provided
    if resume_skills:
        job_list.sort(key=lambda x: x.get('match_percentage', 0), reverse=True)
    
    print(f"Found {len(job_list)} jobs matching the criteria")
    if job_list:
        print(f"First job: {job_list[0]['title']} at {job_list[0].get('company', 'Unknown')}")
    
    conn.close()
    return job_list






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
