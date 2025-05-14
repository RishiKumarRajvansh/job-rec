from database_manager import get_db_connection
import json

def debug_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check job count
    cursor.execute("SELECT COUNT(*) FROM jobs")
    job_count = cursor.fetchone()[0]
    print(f"\nTotal jobs in database: {job_count}")
    
    if job_count > 0:
        # Get sample jobs
        cursor.execute("""
            SELECT j.*, GROUP_CONCAT(js.skill) as skills_list 
            FROM jobs j 
            LEFT JOIN job_skills js ON j.id = js.job_id 
            GROUP BY j.id 
            LIMIT 5
        """)
        jobs = cursor.fetchall()
        
        print("\nSample jobs:")
        for job in jobs:
            job_dict = dict(job)
            print("\nJob:", job_dict['title'])
            print("Company:", job_dict['company'])
            print("Location:", job_dict['location'])
            
            # Print skills both from jobs table and job_skills table
            if 'skills' in job_dict and job_dict['skills']:
                try:
                    skills_from_json = json.loads(job_dict['skills'])
                    print("Skills from jobs table:", skills_from_json)
                except json.JSONDecodeError:
                    print("Skills from jobs table (raw):", job_dict['skills'])
            
            if 'skills_list' in job_dict and job_dict['skills_list']:
                print("Skills from job_skills table:", job_dict['skills_list'].split(','))
    
    cursor.execute("SELECT COUNT(*) FROM job_skills")
    skill_count = cursor.fetchone()[0]
    print(f"\nTotal job skills entries: {skill_count}")
    
    if skill_count > 0:
        cursor.execute("SELECT DISTINCT skill FROM job_skills LIMIT 10")
        skills = cursor.fetchall()
        print("\nSample unique skills:")
        for skill in skills:
            print(skill[0])

    conn.close()

if __name__ == "__main__":
    debug_database()
