from flask import Flask, render_template, url_for, flash, redirect, request, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required
from datetime import datetime
import os
import json
import subprocess
import sys  # Make sure to import sys
import time
from werkzeug.utils import secure_filename

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Change this to a random secret key
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'job_recommender.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Set up upload folder for resumes
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Ensure upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Import forms
from forms import RegistrationForm, LoginForm, ProfileForm, JobSearchForm

# User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    skills = db.Column(db.Text, nullable=True)
    experience_summary = db.Column(db.Text, nullable=True)
    education_summary = db.Column(db.Text, nullable=True)
    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Import database functions
from database_manager import get_all_jobs, search_jobs_db, get_job_by_id, clear_jobs_table

# Functions to ensure spaCy is installed and model is downloaded
def ensure_spacy_installed():
    """Ensure spaCy is installed."""
    try:
        import spacy
        print("spaCy is already installed.")
        return True
    except ImportError:
        print("spaCy not found. Installing...")
        try:
            # Use a more robust installation command with full output capture
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "spacy"],
                capture_output=True,
                text=True,
                check=False  # Don't raise exception on non-zero exit
            )
            
            if result.returncode != 0:
                print(f"Error installing spaCy: {result.stderr}")
                return False
                
            print("spaCy installation output:", result.stdout)
            print("spaCy installed successfully.")
            
            # Verify installation worked by trying to import again
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

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def run_scraper(query=None, location=None):
    """Run the scraper.py script with optional query and location parameters"""
    try:
        # Ensure spaCy is installed before running the scraper
        print("Checking if spaCy is installed...")
        if not ensure_spacy_installed():
            print("Failed to install spaCy. Aborting scraper.")
            return False
        
        print("Checking if spaCy model is downloaded...")
        if not ensure_model_downloaded():
            print("Failed to download spaCy model. Aborting scraper.")
            return False
        
        # Create a modified environment with the current Python path
        env = os.environ.copy()
        
        # Clear existing jobs before scraping new ones
        clear_jobs_table()
        
        # Build command with parameters if provided
        cmd = [sys.executable, "scraper.py"]  # Use sys.executable to ensure same Python interpreter
        if query and query.lower() != 'all':
            cmd.extend(["--query", query])
        if location and location.lower() != 'all':
            cmd.extend(["--location", location])
        
        print("Running scraper with command:", " ".join(cmd))
        
        # Run the scraper process with the modified environment
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            env=env,
            text=True
        )
        
        stdout, stderr = process.communicate(timeout=60)  # 60 second timeout
        
        if process.returncode != 0:
            print(f"Scraper error: {stderr}")
            return False
        
        print("Scraper output:", stdout)
        print("Scraper completed successfully")
        return True
    except Exception as e:
        print(f"Error running scraper: {str(e)}")
        return False

@app.route('/')
def index():
    form = JobSearchForm()
    resume_skills = session.get('resume_skills', [])
    current_year = datetime.now().year
    return render_template('index.html', form=form, resume_skills=resume_skills, current_year=current_year)

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

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.skills = form.skills.data
        current_user.experience_summary = form.experience_summary.data
        current_user.education_summary = form.education_summary.data
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.skills.data = current_user.skills
        form.experience_summary.data = current_user.experience_summary
        form.education_summary.data = current_user.education_summary
    return render_template('profile.html', title='Profile', form=form, current_year=datetime.now().year)

@app.route('/jobs')
@login_required
def list_all_jobs():
    # Don't show any flash messages here - we'll handle them in the template
    resume_skills = session.get('resume_skills', [])
    
    # Render the template with a flag to indicate we need to run the scraper
    return render_template('jobs_list.html',
                           jobs=[],
                           query="All",
                           location="All",
                          resume_skills=resume_skills,
                           current_year=datetime.now().year,
                          run_scraper=True)  # Flag to trigger scraping in the template

@app.route('/run_scraper_api', methods=['POST'])
@login_required
def run_scraper_api():
    """API endpoint to run the scraper and return results"""
    query = request.form.get('query', 'all')
    location = request.form.get('location', 'all')
    
    # Run the scraper
    success = run_scraper(query, location)
    
    if not success:
        return jsonify({
            'status': 'error',
            'message': 'Failed to run scraper. Please try again.'
        }), 500
    
    # Get the jobs from the database
    if query.lower() == 'all' and location.lower() == 'all':
        jobs = get_all_jobs()
    else:
        jobs = search_jobs_db(query, location, session.get('resume_skills', []))
    
    # Process jobs for JSON serialization
    processed_jobs = []
    for job in jobs:
        job_dict = dict(job)
        
        # Ensure skills is a list
        if isinstance(job_dict.get('skills'), str):
            try:
                job_dict['skills'] = json.loads(job_dict['skills'])
            except json.JSONDecodeError:
                job_dict['skills'] = job_dict['skills'].split(',') if job_dict['skills'] else []
        
        processed_jobs.append(job_dict)
    
    return jsonify({
        'status': 'success',
        'jobs': processed_jobs,
        'count': len(processed_jobs)
    })

@app.route('/search', methods=['POST'])
@login_required
def search():
    form = JobSearchForm()
    if form.validate_on_submit():
        query = form.query.data
        location = form.location.data
        resume_skills = session.get('resume_skills', [])
        
        # Render the template with a flag to indicate we need to run the scraper
        return render_template('jobs_list.html',
                               jobs=[],
                               query=query,
                               location=location,
                              resume_skills=resume_skills,
                               current_year=datetime.now().year,
                              run_scraper=True)  # Flag to trigger scraping in the template
    
    return redirect(url_for('index'))

@app.route('/upload_resume', methods=['GET', 'POST'])
@login_required
def upload_resume():
    if request.method == 'POST':
        if 'resume' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        file = request.files['resume']
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            # For now, just use some mock skills instead of parsing the resume
            mock_skills = ["Python", "JavaScript", "SQL", "Git", "HTML", "CSS"]
            session['resume_skills'] = mock_skills
            flash(f"Resume processed! Found skills: {', '.join(mock_skills)}", 'success')
            return redirect(url_for('index'))
        else:
            flash('File type not allowed. Please upload TXT, PDF, or DOCX.', 'warning')
            return redirect(request.url)
    return render_template('upload_resume.html', current_year=datetime.now().year)

@app.route('/reset_skills')
@login_required
def reset_skills():
    if 'resume_skills' in session:
        session.pop('resume_skills')
        flash('Resume skills have been cleared.', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables
    app.run(debug=True)
