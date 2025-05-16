# Job Recommender System

## Recent Updates

### Job Count Standardization
- Implemented consistent job counting methodology across all pages
- Added a central `job_counter.py` utility to standardize job counts
- Fixed inconsistent job count displays between jobs list, dashboard, and insights pages
- Added different job count categories: total jobs, matching jobs, remote jobs, and onsite jobs
- Fixed duplicate job counting bug in database_manager.py that was causing inconsistent counts
- Updated templates to use consistent job count variables across all pages

### Job Scraping and Display
- Fixed the "Browse Jobs" feature to only scrape when necessary:
  - When no jobs are available for the user
  - When the user manually refreshes the job list
  - When the user updates their skills in their profile
- Fixed the "Refresh" button functionality to properly trigger job scraping
- Fixed the loading indicator to work consistently across all job-related actions
- Improved user experience by showing appropriate loading messages
- Added better error handling for failed job scraping operations

### User Skills Integration
- Improved skills synchronization between profile updates and job searches
- Fixed skill matching algorithm to properly handle case-insensitive matching
- Added proper memory of user skills using session storage with user-specific keys

### General Improvements
- Added utility functions to better manage job-related operations
- Fixed loading indicator functionality for better user feedback
- Ensured consistent behavior across all job-related actions

A comprehensive job search and recommendation platform that helps users find job opportunities matching their skills and experience.

## Features

### Job Search and Scraping
- Search for jobs across multiple platforms
- Filter jobs by location, skills, and other criteria
- Save and manage job listings

### Profile Management
- Upload and parse resumes (PDF, DOCX, TXT formats)
- Track education and work experience
- Maintain a skills inventory

### Course Recommendations
- Get course recommendations based on job market skills
- Bridge skill gaps with targeted learning resources

### Job Market Insights
- Interactive data visualizations of job market trends
- Analysis of in-demand skills, locations, and companies
- Salary distributions and comparisons
- Filter insights by specific skills

## Technical Implementation

### Insights Feature

The Insights feature provides data visualizations of job market trends:

- **In-Memory Graph Generation**: Uses Matplotlib and Seaborn to generate visualizations on-demand as base64-encoded images
- **Data Analysis**: Processes job data using Pandas for identifying trends and patterns
- **Interactive Filtering**: Allows users to filter visualizations by specific skills
- **Automatic Cleanup**: Removes old graph files to maintain clean storage

#### Visualizations include:

- Most in-demand skills
- Required vs nice-to-have skills comparison
- Jobs by location
- Companies with most openings
- Salary distribution and statistics
- Skills that command higher salaries
- Remote vs on-site job distribution
- Employment type breakdown
- Experience level distribution

#### Implementation Details

The Insights feature uses an in-memory approach for creating visualizations:
1. Data is fetched from the database and analyzed using Pandas
2. Matplotlib/Seaborn creates visualizations in memory using BytesIO buffers
3. Images are converted to base64 and embedded directly in the HTML
4. Old static graph files are automatically cleaned up to save storage space

## Setup and Installation

### Requirements

- Python 3.8+
- SQLite
- Required packages listed in requirements.txt

### Installation

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Linux/macOS: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Initialize the database: `python init_database.py`
6. Run the application: `python app.py`
7. Access the application at http://localhost:5000

## Maintenance

### Cleaning Up Old Graph Files

To manually clean up old visualization files:
```
python cleanup_graphs.py
```

The application automatically cleans files older than 3 days on startup.
