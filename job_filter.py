from typing import List, Dict, Set, Any
import json

def normalize_skills(skills: List[str]) -> Set[str]:
    """Normalize skills by converting to lowercase and removing duplicates."""
    return {s.strip().lower() for s in skills if s and s.strip()}

def filter_jobs_by_location_and_skills(jobs: List[Dict[str, Any]], location: str, resume_skills: List[str]) -> List[Dict[str, Any]]:
    """
    Filter and rank jobs based on location and skill matching.
    
    Args:
        jobs: List of job dictionaries
        location: Location to filter by
        resume_skills: List of user's skills from resume and profile
    
    Returns:
        list: Filtered and ranked list of jobs with match details
    """
    filtered_jobs = []
    resume_skills_set = normalize_skills(resume_skills) if resume_skills else set()
    
    for job in jobs:
        # Location filtering with improved remote handling
        job_location = job.get('location', '').lower()
        is_remote = job.get('is_remote', False)
        
        location_match = (
            not location or 
            location.lower() == 'all' or
            ('remote' in location.lower() and is_remote) or
            any(loc.strip() in job_location for loc in location.lower().split(',')) or
            any(loc.strip() in location.lower() for loc in job_location.split(','))
        )
        
        if not location_match:
            continue
        
        # Extract and normalize job skills
        job_skills = set()
        required_skills = set()
        nice_to_have_skills = set()

        # Process skills from various fields
        if job.get('skills'):
            if isinstance(job['skills'], str):
                try:
                    skills_data = json.loads(job['skills'])
                    if isinstance(skills_data, dict):
                        required_skills.update(normalize_skills(skills_data.get('required', [])))
                        nice_to_have_skills.update(normalize_skills(skills_data.get('nice_to_have', [])))
                    elif isinstance(skills_data, list):
                        job_skills.update(normalize_skills(skills_data))
                except json.JSONDecodeError:
                    # Handle plain text skills
                    job_skills.update(normalize_skills(job['skills'].split(',')))
            elif isinstance(job['skills'], (list, tuple)):
                job_skills.update(normalize_skills(job['skills']))
            elif isinstance(job['skills'], dict):
                required_skills.update(normalize_skills(job['skills'].get('required', [])))
                nice_to_have_skills.update(normalize_skills(job['skills'].get('nice_to_have', [])))

        # Add skills from other fields if present
        for key in ['required_skills', 'nice_to_have_skills', 'skill_list']:
            if key in job:
                skill_value = job[key]
                if isinstance(skill_value, str):
                    try:
                        skill_list = json.loads(skill_value)
                    except json.JSONDecodeError:
                        skill_list = skill_value.split(',')
                else:
                    skill_list = skill_value

                if skill_list:
                    skills = normalize_skills(skill_list)
                    if 'required' in key:
                        required_skills.update(skills)
                    elif 'nice_to_have' in key:
                        nice_to_have_skills.update(skills)
                    else:
                        job_skills.update(skills)

        # Combine all skills, ensuring required skills take precedence
        all_job_skills = job_skills.union(required_skills).union(nice_to_have_skills)

        # If no resume skills provided, include job with basic info
        if not resume_skills_set:
            job.update({
                'skills': sorted(list(all_job_skills)),
                'required_skills': sorted(list(required_skills)),
                'nice_to_have_skills': sorted(list(nice_to_have_skills))
            })
            filtered_jobs.append(job)
            continue

        # Calculate skill matches
        matching_skills = all_job_skills.intersection(resume_skills_set)
        missing_skills = all_job_skills - resume_skills_set
        required_matched = required_skills.intersection(resume_skills_set)
        nice_to_have_matched = nice_to_have_skills.intersection(resume_skills_set)

        # Calculate match percentages with improved weighting
        total_required = len(required_skills) if required_skills else len(all_job_skills)
        total_nice_to_have = len(nice_to_have_skills)
        
        # Required skills match (60% weight)
        required_match = (len(required_matched) / total_required * 100) if total_required > 0 else 0
        
        # Nice to have skills match (20% weight)
        nice_to_have_match = (len(nice_to_have_matched) / total_nice_to_have * 100) if total_nice_to_have > 0 else 0
        
        # Overall skills match (20% weight)
        overall_match = (len(matching_skills) / len(all_job_skills) * 100) if all_job_skills else 0

        # Calculate final weighted score
        match_percentage = (
            (required_match * 0.6) + 
            (nice_to_have_match * 0.2) + 
            (overall_match * 0.2)
        )

        # Only include jobs with significant matches (>10%)
        if match_percentage >= 10:
            job.update({
                'match_percentage': round(match_percentage),
                'matching_skills': sorted(list(matching_skills)),
                'missing_skills': sorted(list(missing_skills)),
                'matching_required_skills': sorted(list(required_matched)),
                'matching_nice_to_have_skills': sorted(list(nice_to_have_matched)),
                'required_skills': sorted(list(required_skills)),
                'nice_to_have_skills': sorted(list(nice_to_have_skills)),
                'total_required_skills': total_required,
                'total_nice_to_have_skills': total_nice_to_have
            })
            filtered_jobs.append(job)

    # Sort jobs by match quality
    if resume_skills:
        filtered_jobs.sort(
            key=lambda x: (
                x.get('match_percentage', 0),
                len(x.get('matching_required_skills', [])),
                len(x.get('matching_nice_to_have_skills', [])),
                x.get('date_scraped', ''),
                x.get('title', '')
            ),
            reverse=True
        )
    else:
        # Sort by date if no skills provided
        filtered_jobs.sort(key=lambda x: x.get('date_scraped', ''), reverse=True)

    return filtered_jobs
