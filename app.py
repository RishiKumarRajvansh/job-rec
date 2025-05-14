import os
import sys
import re
import traceback
from datetime import datetime
from flask import Flask, request, jsonify, render_template, flash, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required
from werkzeug.utils import secure_filename
from database_manager import search_jobs_db, initialize_database as init_db, clear_jobs_table
from courses import fetch_courses_by_skills
from scraper import scrape_jobs
import json
import subprocess
import time
import spacy
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
from werkzeug.exceptions import BadRequest
from nlp_utils import extract_skills_from_text, extract_location_from_text
from database_manager import (
    get_all_jobs,
    add_work_experience, update_work_experience, delete_work_experience, get_user_work_experience,
    add_education, update_education, delete_education, get_user_education,
    update_user_profile, jobs_need_refresh
)
from resume_parser import parse_resume, extract_text_from_pdf, extract_text_from_docx, extract_text_from_txt
from flask_wtf.csrf import CSRFProtect
from forms import (
    LoginForm, RegistrationForm, JobSearchForm, ProfileForm,
    WorkExperienceForm, EducationForm, ResumeUploadForm
)

# Define constants
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx'}

# Ensure spaCy and its model are available
try:
    import spacy
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "spacy"])
    import spacy

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Change this to a random secret key
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Configure database
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance/job_recommender.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
from models import db, User  # Import db and User from models.py
db.init_app(app)

# Initialize Flask-Migrate
migrate = Migrate(app, db)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize Flask-Bcrypt
bcrypt = Bcrypt(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def ensure_spacy_installed():
    """Ensure spaCy is installed."""
    try:
        import spacy
        print("spaCy is already installed.")
        return True
    except ImportError:
        print("spaCy not found. Installing...")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "spacy"],
                capture_output=True, 
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                print(f"Error installing spaCy: {result.stderr}")
                return False
            
            # Verify installation worked
            try:
                import spacy
                return True
            except ImportError:
                print("spaCy still not available after installation.")
                return False
        except Exception as e:
            print(f"Failed to install spaCy: {e}")
            return False


def ensure_model_downloaded(model_name='en_core_web_sm'):
    """Ensure the spaCy model is downloaded."""
    try:
        import spacy
        try:
            spacy.load(model_name)
            print(f"spaCy model '{model_name}' is already downloaded.")
            return True
        except OSError:
            print(f"spaCy model '{model_name}' not found. Downloading...")
            try:
                # Use a more robust download command with full output capture
                result = subprocess.run(
                    [sys.executable, "-m", "spacy", "download", model_name],
                    capture_output=True,
                    text=True,
                    check=False  # Don't raise exception on non-zero exit
                )
                
                if result.returncode != 0:
                    print(f"Error downloading spaCy model: {result.stderr}")
                    return False
                    
                print("Model download output:", result.stdout)
                print(f"Model '{model_name}' downloaded successfully.")
                
                # Verify model was downloaded by trying to load it
                try:
                    spacy.load(model_name)
                    return True
                except OSError:
                    print(f"Model '{model_name}' still not available after download.")
                    return False
            except Exception as e:
                print(f"Failed to download model: {e}")
                return False
    except ImportError:
        print("Cannot download model because spaCy is not installed.")
        return False


def run_scraper(query="All", location="All"):
    """
    Run the job scraper with the specified query and location.
    
    Args:
        query (str): Job search query
        location (str): Location to search in
        
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"Starting job scraper with query='{query}', location='{location}'")
    try:
        print(f"Running scraper with query='{query}', location='{location}'")
        
        # Initialize database and ensure tables exist
        init_db()
        clear_jobs_table()
        
        # Ensure spaCy is installed and model is downloaded
        ensure_spacy_installed()
        
        # Prepare and run the scraper process
        scraper_command = [sys.executable, "scraper.py", "--query", query, "--location", location]
        print(f"Running scraper with command: {' '.join(scraper_command)}")
        
        result = subprocess.run(scraper_command, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Scraper failed with error: {result.stderr}")
            return False
        
        print(f"Scraper output: {result.stdout}")
        print("Scraper completed successfully")
        
        return True
    except Exception as e:
        print(f"Error running scraper: {str(e)}")
        traceback.print_exc()
        return False


def jobs_need_refresh():
    """Check if jobs need to be refreshed based on time elapsed."""
    # Get the last scrape time from the session
    last_scrape = session.get('last_scrape_time')
    if not last_scrape:
        return True
    
    try:
        elapsed = (datetime.utcnow() - datetime.fromisoformat(last_scrape)).total_seconds()
        # Only refresh if it's been more than 6 hours
        return elapsed > 21600  # 6 hours
    except:
        return True


# Add template filters
@app.template_filter('from_json')
def from_json_filter(value):
    """Convert a JSON string to Python object."""
    if not value:
        return []
    try:
        if isinstance(value, str):
            # If it looks like a JSON array or object
            if value.startswith('[') or value.startswith('{'):
                return json.loads(value)
            # If it's just a comma-separated string
            return [s.strip() for s in value.split(',') if s.strip()]
        return value if isinstance(value, (list, tuple)) else []
    except (json.JSONDecodeError, AttributeError):
        # If it's not JSON and not a string, return empty list
        return []


@app.template_filter('nl2br')
def nl2br(value):
    """Convert newlines to HTML line breaks."""
    if not value:
        return value
    return value.replace('\n', '<br>')


@app.route('/')
def index():
    resume_skills = session.get('resume_skills', [])
    return render_template('index.html', resume_skills=resume_skills)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form, current_year=datetime.now().year)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form, current_year=datetime.now().year)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route("/profile", methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    
    if form.validate_on_submit():
        # Check for changes and only update fields that have changed
        updates = {}
        if form.username.data != current_user.username:
            # Check if new username is already taken
            existing_user = User.query.filter_by(username=form.username.data).first()
            if existing_user and existing_user.id != current_user.id:
                flash('Username already taken.', 'danger')
                return redirect(url_for('profile'))
            updates['username'] = form.username.data

        if form.email.data != current_user.email:
            # Check if new email is already taken
            existing_user = User.query.filter_by(email=form.email.data).first()
            if existing_user and existing_user.id != current_user.id:
                flash('Email already registered.', 'danger')
                return redirect(url_for('profile'))
            updates['email'] = form.email.data

        # For non-unique fields, update if they've changed
        if form.skills.data != current_user.skills:
            updates['skills'] = form.skills.data
        if form.location.data != current_user.location:
            updates['location'] = form.location.data
        if form.certifications.data != current_user.certifications:
            updates['certifications'] = form.certifications.data
        if form.summary.data != current_user.summary:
            updates['summary'] = form.summary.data

        # Track if we need to trigger a scrape
        need_scrape = False

        # Only update if there are actual changes
        if updates:
            try:
                # Update SQLAlchemy model
                if 'username' in updates:
                    current_user.username = updates['username']
                if 'email' in updates:
                    current_user.email = updates['email']
                if 'skills' in updates:
                    current_user.skills = updates['skills']
                    need_scrape = True  # Skills changed, need to refresh jobs
                if 'location' in updates:
                    current_user.location = updates['location']
                    need_scrape = True  # Location changed, need to refresh jobs
                if 'certifications' in updates:
                    current_user.certifications = updates['certifications']
                if 'summary' in updates:
                    current_user.summary = updates['summary']
                
                # Commit SQLAlchemy changes
                db.session.commit()
                
                flash('Your profile has been updated!', 'success')
                if need_scrape:
                    # Trigger a scrape with the new skills/location
                    user_skills = [s.strip() for s in current_user.skills.split(',')] if current_user.skills else []
                    session['resume_skills'] = user_skills
                    session.pop('last_scrape_time', None)  # Force a fresh scrape
                    return redirect(url_for('list_all_jobs', run_scraper='true'))
                
                return redirect(url_for('profile'))
                
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating profile: {str(e)}', 'danger')
                return redirect(url_for('profile'))
        return redirect(url_for('profile'))
        
    elif request.method == 'GET':
        # Populate form with current user data
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.location.data = current_user.location
        form.skills.data = current_user.skills
        form.certifications.data = current_user.certifications
        form.summary.data = current_user.summary

    # Get resume skills if they exist
    resume_skills = session.get('resume_skills', [])
    
    return render_template('profile.html',
                         form=form,
                         resume_skills=resume_skills)


@app.route("/add_experience", methods=['POST'])
@login_required
def add_experience():
    form = WorkExperienceForm()
    if form.validate_on_submit():
        start_date = datetime.strptime(form.start_date.data, '%m/%Y')
        end_date = None if form.current_job.data else datetime.strptime(form.end_date.data, '%m/%Y')
        
        exp_id = add_work_experience(
            user_id=current_user.id,
            company=form.company.data,
            title=form.title.data,
            start_date=start_date,
            end_date=end_date,
            description=form.description.data,
            current_job=form.current_job.data
        )
        
        if exp_id:
            flash('Work experience added successfully!', 'success')
        else:
            flash('Error adding work experience.', 'danger')
    return redirect(url_for('profile'))


@app.route("/edit_experience/<int:id>", methods=['POST'])
@login_required
def edit_experience(id):
    form = WorkExperienceForm()
    if form.validate_on_submit():
        start_date = datetime.strptime(form.start_date.data, '%m/%Y')
        end_date = None if form.current_job.data else datetime.strptime(form.end_date.data, '%m/%Y')
        
        success = update_work_experience(
            exp_id=id,
            user_id=current_user.id,
            company=form.company.data,
            title=form.title.data,
            start_date=start_date,
            end_date=end_date,
            description=form.description.data,
            current_job=form.current_job.data
        )
        
        return jsonify({'success': success})
    return jsonify({'success': False, 'errors': form.errors}), 400


@app.route("/delete_experience/<int:id>", methods=['POST'])
@login_required
def delete_experience(id):
    success = delete_work_experience(id, current_user.id)
    return jsonify({'success': success})


@app.route("/add_education", methods=['POST'])
@login_required
def add_education_route():
    form = EducationForm()
    if form.validate_on_submit():
        start_date = datetime.strptime(form.start_date.data, '%m/%Y') if form.start_date.data else None
        end_date = datetime.strptime(form.end_date.data, '%m/%Y') if form.end_date.data else None
        gpa = float(form.gpa.data) if form.gpa.data else None
        
        edu_id = add_education(
            user_id=current_user.id,
            institution=form.institution.data,
            degree=form.degree.data,
            field_of_study=form.field_of_study.data,
            start_date=start_date,
            end_date=end_date,
            gpa=gpa,
            description=form.description.data
        )
        
        if edu_id:
            flash('Education entry added successfully!', 'success')
        else:
            flash('Error adding education entry.', 'danger')
    return redirect(url_for('profile'))


@app.route("/edit_education/<int:id>", methods=['POST'])
@login_required
def edit_education(id):
    form = EducationForm()
    if form.validate_on_submit():
        start_date = datetime.strptime(form.start_date.data, '%m/%Y') if form.start_date.data else None
        end_date = datetime.strptime(form.end_date.data, '%m/%Y') if form.end_date.data else None
        gpa = float(form.gpa.data) if form.gpa.data else None
        
        success = update_education(
            edu_id=id,
            user_id=current_user.id,
            institution=form.institution.data,
            degree=form.degree.data,
            field_of_study=form.field_of_study.data,
            start_date=start_date,
            end_date=end_date,
            gpa=gpa,
            description=form.description.data
        )
        
        return jsonify({'success': success})
    return jsonify({'success': False, 'errors': form.errors}), 400


@app.route("/delete_education/<int:id>", methods=['POST'])
@login_required
def delete_education_route(id):
    success = delete_education(id, current_user.id)
    return jsonify({'success': success})


@app.route('/jobs')
@app.route('/list_all_jobs')
@login_required
def list_all_jobs():
    """Display the list of jobs."""
    query = request.args.get('query', 'All')
    location = request.args.get('location', 'All')
    run_scraper = request.args.get('run_scraper', 'false').lower() == 'true'
    force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
      # Get user's skills from session and profile
    resume_skills = []
    
    # Get skills from user-specific session key
    session_skills = session.get(f'user_{current_user.id}_resume_skills', [])
    if session_skills:
        if isinstance(session_skills, str):
            resume_skills.extend(s.strip() for s in session_skills.split(',') if s.strip())
        elif isinstance(session_skills, list):
            resume_skills.extend(s.strip() for s in session_skills if s.strip())
            
    # Get skills from user profile if available
    if current_user and current_user.resume_skills:
        profile_skills = current_user.resume_skills
        if isinstance(profile_skills, str):
            profile_skills = [s.strip() for s in profile_skills.split(',') if s.strip()]
            resume_skills.extend(profile_skills)
    
    # Remove duplicates and empty strings
    resume_skills = list(set(s for s in resume_skills if s))
    
    # Get the last scrape time from session
    last_scrape_time = session.get('last_scrape_time')
    
    # Check if we need to scrape
    need_scrape = (
        force_refresh or  # Manual refresh requested
        run_scraper or   # Search with new query
        jobs_need_refresh()  # Time-based refresh check
    )

    # Get jobs either by scraping or from database
    if need_scrape:
        try:
            # Show loading state
            session['is_loading'] = True
            
            # Use scrape_jobs to get fresh data
            jobs = scrape_jobs(
                query=query,
                location=location,
                user_skills=resume_skills,
                pages=3,  # Scrape 3 pages by default
                force_clear=force_refresh,
                user_id=current_user.id
            )
            
            # Update last scrape time
            session['last_scrape_time'] = datetime.utcnow().isoformat()
            
            if not jobs:
                flash('No jobs found. Try adjusting your search criteria.', 'info')
                jobs = []
            else:
                flash(f'Successfully found {len(jobs)} jobs!', 'success')
        
        except Exception as e:
            flash(f'Error while scraping jobs: {str(e)}', 'error')
            jobs = []
        finally:
            # Clear loading state
            session.pop('is_loading', None)
    else:
        # Get existing jobs from database
        jobs = search_jobs_db(query, location, resume_skills, user_id=current_user.id)

    # Process jobs to ensure proper skill formatting and matching
    missing_skills_set = set()
    
    for job in jobs:
        # Handle required skills
        if isinstance(job.get('required_skills'), str):
            try:
                job['required_skills'] = json.loads(job['required_skills'])
            except (json.JSONDecodeError, TypeError):
                job['required_skills'] = []
        elif job.get('required_skills') is None:
            job['required_skills'] = []

        # Handle nice to have skills
        if isinstance(job.get('nice_to_have_skills'), str):
            try:
                job['nice_to_have_skills'] = json.loads(job['nice_to_have_skills'])
            except (json.JSONDecodeError, TypeError):
                job['nice_to_have_skills'] = []
        elif job.get('nice_to_have_skills') is None:
            job['nice_to_have_skills'] = []

        # Handle all skills
        if isinstance(job.get('skills'), str):
            try:
                job['skills'] = json.loads(job['skills'])
            except (json.JSONDecodeError, TypeError):
                job['skills'] = []
        elif job.get('skills') is None:
            job['skills'] = []

        # Calculate matching skills for required and nice-to-have if resume skills exist
        if resume_skills:
            # Normalize all skills to lowercase for matching
            resume_skills_set = set(s.lower().strip() for s in resume_skills if s)
            required_skills_set = set(s.lower().strip() for s in job.get('required_skills', []) if s)
            nice_to_have_set = set(s.lower().strip() for s in job.get('nice_to_have_skills', []) if s)
            all_skills_set = required_skills_set | nice_to_have_set
            
            # Find matching and missing skills while preserving original case
            job['matching_required_skills'] = [s for s in job['required_skills'] if s and s.lower().strip() in resume_skills_set]
            job['matching_nice_to_have_skills'] = [s for s in job['nice_to_have_skills'] if s and s.lower().strip() in resume_skills_set]
            job['missing_skills'] = [s for s in job['required_skills'] if s and s.lower().strip() not in resume_skills_set]
            
            # Only count it as a skill gap if the skill appears frequently in job requirements
            if len(job['missing_skills']) > 0:
                missing_skills_set.update(s for s in job['missing_skills'] if s)
            
            # Calculate match percentages
            if required_skills_set or nice_to_have_set:
                required_weight = 0.7  # 70% weight for required skills
                nice_to_have_weight = 0.3  # 30% weight for nice-to-have skills
                
                required_match = (len([s for s in job['matching_required_skills']]) / len(required_skills_set) * 100 * required_weight
                                if required_skills_set else 0)
                nice_to_have_match = (len([s for s in job['matching_nice_to_have_skills']]) / len(nice_to_have_set) * 100 * nice_to_have_weight
                                    if nice_to_have_set else 0)
                                    
                job['match_percentage'] = int(required_match + nice_to_have_match)
    
    # Sort jobs by match percentage and other criteria
    if resume_skills:
        jobs.sort(key=lambda x: (
            x.get('match_percentage', 0),
            x.get('is_new', False),
            x.get('is_urgent', False),
            x.get('date_scraped', '')
        ), reverse=True)
    else:
        jobs.sort(key=lambda x: (
            x.get('is_new', False),
            x.get('is_urgent', False),
            x.get('date_scraped', '')
        ), reverse=True)

    # Convert missing_skills_set back to a sorted list for template
    missing_skills = sorted(list(missing_skills_set))
      # Store missing skills in session for use in course recommendations, using user-specific key
    session[f'user_{current_user.id}_missing_skills'] = missing_skills# If we have missing skills, fetch course recommendations
    course_recommendations = {}
    if missing_skills:
        try:
            course_recommendations = fetch_courses_by_skills(missing_skills)
        except Exception as e:
            print(f"Error fetching course recommendations: {e}")
            course_recommendations = {}

    return render_template(
        'jobs_list.html',
        jobs=jobs,
        course_recommendations=course_recommendations,
        query=query,
        location=location,
        run_scraper=need_scrape,
        resume_skills=resume_skills,
        missing_skills=missing_skills,
        is_loading=session.get('is_loading', False)
    )


@app.route("/upload_resume", methods=['GET', 'POST'])
@login_required
def upload_resume():
    form = ResumeUploadForm()
    if form.validate_on_submit():
        if not form.resume.data:
            flash('Please select a resume file to upload.', 'warning')
            return redirect(url_for('upload_resume'))
            
        temp_file = None
        try:
            # Get file and create safe filename
            uploaded_file = form.resume.data
            filename = secure_filename(uploaded_file.filename)
            
            # Create path in upload folder
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Save the file
            uploaded_file.save(file_path)
            temp_file = file_path  # Keep track for cleanup
            
            # Parse resume using global nlp model
            resume_data = parse_resume(file_path, nlp)
            
            if resume_data and 'skills' in resume_data:
                # Clear old skills data
                if 'resume_skills' in session:
                    session.pop('resume_skills')
                if 'missing_skills' in session:
                    session.pop('missing_skills')
                  # Clean and validate skills
                cleaned_skills = [skill.strip() for skill in resume_data['skills'] if skill.strip()]
                  # Update session with fresh skills using user-specific keys
                session[f'user_{current_user.id}_resume_skills'] = cleaned_skills
                session[f'user_{current_user.id}_last_resume_update'] = datetime.utcnow().isoformat()
                
                # Update user profile with all resume data
                current_user.resume_skills = ','.join(cleaned_skills)  # Store as comma-separated string
                current_user.skills = ','.join(cleaned_skills)  # Also update regular skills
                current_user.last_resume_update = datetime.utcnow()
                
                # Update location if found
                if resume_data.get('location'):
                    current_user.location = resume_data['location']
                
                # Update summary if found
                if resume_data.get('summary'):
                    current_user.summary = resume_data['summary']
                
                # Update work experience
                if resume_data.get('work_experience'):
                    # Clear existing work experience if any was parsed
                    # Get existing experience IDs
                    existing_experience = get_user_work_experience(current_user.id)
                    for exp in existing_experience:
                        delete_work_experience(exp['id'], current_user.id)
                    
                    # Add new experience entries
                    for exp in resume_data['work_experience']:
                        start_date = datetime.strptime(exp['start_date'], '%m/%Y')            if exp.get('start_date') else None
                        
                        # Handle current job and end date
                        is_current = exp.get('current_job', False) or 'present' in str(exp.get('end_date', '')).lower()
                        end_date = None if is_current else (
                            datetime.strptime(exp['end_date'], '%m/%Y') if exp.get('end_date') else None
                        )
                        
                        add_work_experience(
                            user_id=current_user.id,
                            company=exp['company'],
                            title=exp['title'],
                            start_date=start_date,
                            end_date=end_date,
                            description=exp.get('description'),
                            current_job=is_current
                        )
                
                # Update education
                if resume_data.get('education'):
                    # Clear existing education if any was parsed
                    existing_education = get_user_education(current_user.id)
                    for edu in existing_education:
                        delete_education(edu['id'], current_user.id)
                    
                    # Add new education entries
                    for edu in resume_data['education']:
                        start_date = datetime.strptime(edu['start_date'], '%m/%Y') if edu.get('start_date') else None
                        end_date = datetime.strptime(edu['end_date'], '%m/%Y') if edu.get('end_date') else None
                        
                        add_education(
                            user_id=current_user.id,
                            institution=edu['institution'],
                            degree=edu['degree'],
                            field_of_study=edu.get('field_of_study'),
                            start_date=start_date,
                            end_date=end_date,
                            gpa=edu.get('gpa'),
                            description=edu.get('description')
                        )
                
                db.session.commit()
                
                flash('Resume uploaded and all information updated successfully!', 'success')
                return redirect(url_for('list_all_jobs'))
            else:
                flash('No skills found in resume. Please update your profile manually.', 'warning')
                return redirect(url_for('profile'))
                
        except Exception as e:
            flash(f'Error analyzing resume: {str(e)}', 'danger')
            return redirect(url_for('upload_resume'))
            
        finally:
            # Clean up the temporary file
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception as e:
                    print(f"Warning: Could not remove temporary file {temp_file}: {e}")
                    
    return render_template('upload_resume.html', form=form)


@app.route("/course_recommendations")
@login_required
def course_recommendations():
    # Get the user's skills
    user_skills = []
    if current_user.skills:
        user_skills = [skill.strip() for skill in current_user.skills.split(',')]
    
    # Get skills from user-specific session key
    session_skills = session.get(f'user_{current_user.id}_resume_skills', [])
    if session_skills:
        if isinstance(session_skills, str):
            resume_skills = [s.strip() for s in session_skills.split(',')]
        else:
            resume_skills = session_skills
    else:
        resume_skills = []
    
    # Combine user's profile skills and resume skills
    all_skills = list(set(user_skills + resume_skills))
    
    # Get missing skills from user-specific session key
    missing_skills = session.get(f'user_{current_user.id}_missing_skills', [])
    
    # Initialize course recommendations dictionary
    course_recommendations = {}
    
    # First, get recommendations for missing skills
    if missing_skills:
        try:
            course_recommendations = fetch_courses_by_skills(missing_skills)
        except Exception as e:
            print(f"Error fetching course recommendations for missing skills: {e}")
    
    # If we have space for more recommendations or no missing skills,
    # add courses for existing skills as well
    if not missing_skills or len(course_recommendations) < len(all_skills) * 3:
        existing_skills = [s for s in all_skills if s not in missing_skills]
        if existing_skills:
            try:
                additional_courses = fetch_courses_by_skills(existing_skills)
                # Add non-duplicate courses
                for skill, courses in additional_courses.items():
                    if skill not in course_recommendations:
                        course_recommendations[skill] = courses
            except Exception as e:
                print(f"Error fetching additional course recommendations: {e}")
    
    return render_template(
        'course_recommendations.html',
        course_recommendations=course_recommendations,
        user_skills=all_skills,
        missing_skills=missing_skills
    )


@app.route('/reset_skills')
@login_required
def reset_skills():
    # Clear skills from session
    if 'resume_skills' in session:
        session.pop('resume_skills')
    
    # Clear skills from user profile
    if current_user.is_authenticated:
        update_user_profile(current_user.id, skills=None)
        flash('Skills have been reset', 'info')
    
    return redirect(url_for('list_all_jobs'))


@app.route('/refresh_jobs')
@login_required
def refresh_jobs():
    """Force refresh of job listings"""
    try:
        # Set loading state
        session['is_loading'] = True
        
        # Get existing query and location
        query = request.args.get('query', 'All')
        location = request.args.get('location', 'All')
        
        # Get user's skills from session and profile
        resume_skills = []
        session_skills = session.get('resume_skills', [])
        if session_skills:
            if isinstance(session_skills, str):
                resume_skills.extend(s.strip() for s in session_skills.split(',') if s.strip())
            elif isinstance(session_skills, list):
                resume_skills.extend(s.strip() for s in session_skills if s.strip())
        
        # Get skills from user profile if available
        if current_user and current_user.resume_skills:
            profile_skills = current_user.resume_skills
            if isinstance(profile_skills, str):
                profile_skills = [s.strip() for s in profile_skills.split(',') if s.strip()]
                resume_skills.extend(profile_skills)
        
        # Remove duplicates and empty strings
        resume_skills = list(set(s for s in resume_skills if s))
          # Run the scraper with force_clear=True to get fresh data
        jobs = scrape_jobs(
            query=query,
            location=location,
            user_skills=resume_skills,
            pages=3,
            force_clear=True,
            user_id=current_user.id
        )
        
        if jobs:
            flash(f'Successfully found {len(jobs)} jobs!', 'success')
        else:
            flash('No jobs found. Try adjusting your search criteria.', 'info')
            
        # Update last scrape time
        session['last_scrape_time'] = datetime.utcnow().isoformat()
        
    except Exception as e:
        flash(f'Error refreshing jobs: {str(e)}', 'danger')
    finally:
        # Clear loading state
        session.pop('is_loading', None)
        
    return redirect(request.referrer or url_for('index'))


@app.route('/scrape_jobs_with_profile', methods=['GET'])
@login_required
def scrape_jobs_with_profile():
    """Scrape jobs using the user's profile information."""
    try:
        if not current_user.is_authenticated:
            flash('Please login to search jobs.', 'warning')
            return redirect(url_for('login'))

        # Get user profile information
        user = User.query.get(current_user.id)
        if not user:
            flash('User profile not found.', 'error')
            return redirect(url_for('profile'))
        
        # Extract skills and location from user profile
        user_skills = user.skills.split(',') if user.skills else []
        user_location = user.location if user.location else "All"
        
        # Run the job scraper with the user's profile data
        jobs = scrape_jobs(
            query="All",  # Use "All" since we're using skills directly
            location=user_location,
            user_skills=user_skills,
            pages=3,  # Scrape 3 pages by default
            force_clear=True,  # Clear existing jobs to get fresh results
            user_id=user.id  # Explicitly pass user.id
        )
        
        if jobs:
            flash(f'Successfully scraped {len(jobs)} jobs matching your profile!', 'success')
        else:
            flash('No jobs found matching your profile. Try adjusting your skills or location.', 'info')
        
        return redirect(url_for('list_all_jobs'))
        
    except Exception as e:
        flash(f'Error scraping jobs: {str(e)}', 'error')
        return redirect(url_for('list_all_jobs'))


@app.route('/check_refresh_status', methods=['GET'])
@login_required
def check_refresh_status():
    """Check if jobs need to be refreshed."""
    needs_refresh = jobs_need_refresh()
    last_scrape = session.get('last_scrape_time')
    return jsonify({
        'needs_refresh': needs_refresh,
        'last_scrape': last_scrape,
        'loading': session.get('is_loading', False)
    })


if __name__ == '__main__':
    try:
        with app.app_context():
            db.create_all()
            init_db()  # Initialize database tables
        app.run(debug=True)
    except Exception as e:
        print(f"Error starting application: {e}")
        traceback.print_exc()
