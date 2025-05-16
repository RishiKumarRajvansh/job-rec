# Job Recommender System

A comprehensive job search and recommendation platform that helps users find job opportunities matching their skills and experience, provides personalized course recommendations to bridge skill gaps, and offers insightful job market analytics.

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

## Core Features

### Job Search and Scraping
- Search for jobs across multiple platforms with Adzuna integration
- Filter jobs by location, skills, and job type (remote/onsite)
- Smart job matching that ranks positions based on skill compatibility
- Automatic calculation of match percentages and identification of skill gaps
- Clear indication of required vs. nice-to-have skills for each job
- Automatic job refreshing based on configurable time thresholds

### Resume and Profile Management
- Intelligent resume parsing with support for PDF, DOCX, and TXT formats
- Automatic extraction of:
  - Professional skills using NLP and pattern matching
  - Work experience with company, title, and date detection
  - Education history with degree, institution, and GPA information
  - Location information for targeted job searches
  - Professional summary and certifications
- Comprehensive profile editor for maintaining skills, education, and work history
- Session-based skill storage with user-specific keys for privacy and personalization

### Course Recommendations
- Personalized course suggestions based on:
  - Identified skill gaps from job requirements
  - User's existing skill set for progressive learning
  - Current job market demand for specific skills
- Course information includes difficulty level, workload, and enrollment statistics
- Direct links to course providers for immediate enrollment

### Job Market Insights
- Interactive data visualizations of job market trends with real-time filtering
- In-depth analysis including:
  - Most in-demand skills with visual indication of user's skills
  - Required vs. nice-to-have skills comparison
  - Geographical job distribution
  - Companies with most job openings
  - Salary distribution and statistics
  - Skills that command higher salaries
  - Remote vs. on-site job distribution
  - Employment type breakdown (full-time, part-time, contract)
  - Experience level distribution across the job market

## Technical Architecture

### Database Structure
The application uses SQLite with the following main tables:
- `user`: Stores user accounts, profile information, and skills
- `work_experience`: Tracks professional history linked to users
- `education`: Manages educational background linked to users
- `jobs`: Stores comprehensive job listings with detailed attributes
- `job_skills`: Maintains skills associated with jobs, categorized as required or nice-to-have

### Core Components

#### Resume Parser (`resume_parser.py`)
- Uses natural language processing (spaCy) to extract structured data from resumes
- Implements sophisticated pattern matching to identify professional elements
- Handles various file formats with dedicated extraction methods
- Processes and normalizes extracted data for consistent database storage

#### Job Scraper (`scraper.py`)
- Connects to job listing APIs and websites to gather current opportunities
- Implements intelligent skill extraction from job descriptions
- Classifies skills as required or nice-to-have based on context analysis
- Handles pagination, error recovery, and duplicate prevention
- User-specific job collection to maintain personalized listings

#### Insights Generator (`insights.py`)
- Creates data visualizations using Matplotlib and Seaborn
- Processes job data using Pandas for identifying market trends
- Implements in-memory graph generation with base64 encoding for efficient delivery
- Provides interactive filtering capabilities for customized analysis
- Generates statistically meaningful representations of job market conditions

#### Standardized Job Counter (`job_counter.py`)
- Provides consistent job counting methodology across all app features
- Categorizes jobs by type: total, matching, remote, and onsite
- Ensures coherent data presentation throughout the user interface

#### Job Utilities (`job_utils.py`, `nlp_utils.py`)
- Centralizes common job-related operations for application-wide consistency
- Implements NLP-based skill extraction and matching algorithms
- Provides location detection and normalization functions
- Handles user skill management across sessions

### Frontend
- Responsive Bootstrap-based UI with custom CSS
- Interactive job filtering and sorting capabilities
- Real-time loading indicators for background operations
- Dynamic content updating with targeted AJAX requests
- Comprehensive error handling with user-friendly notifications

## Implementation Details

### Insights Feature
The Insights feature uses an in-memory approach for creating visualizations:
1. Data is fetched from the database and transformed into Pandas DataFrames
2. Visualization logic processes the data to extract meaningful patterns
3. Matplotlib/Seaborn creates visualizations in memory using BytesIO buffers
4. Images are converted to base64 and embedded directly in the HTML
5. Old static graph files are automatically cleaned up to save storage space

### Job Matching Algorithm
The system uses a sophisticated matching algorithm that:
1. Normalizes skills from both job descriptions and user profiles
2. Performs case-insensitive matching to avoid duplication
3. Weights required skills higher than nice-to-have skills
4. Calculates match percentages based on skill overlap
5. Identifies missing skills to guide user development

### Session Management
User data is maintained securely through:
1. User-specific session keys to prevent data leakage
2. Automatic session cleanup on logout
3. Persistent storage of critical data in the database
4. Temporary storage of sensitive information for active sessions only

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
