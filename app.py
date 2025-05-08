from flask import Flask, render_template, url_for, flash, redirect, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required
from datetime import datetime
import os
import json

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

# User model - must be defined before importing other modules that use it
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

# Import forms
from forms import RegistrationForm, LoginForm, ProfileForm, JobSearchForm

# Simple mock data for jobs
MOCK_JOBS = [
    {
        "id": 1,
        "title": "Python Developer",
        "company": "Tech Solutions Inc.",
        "location": "Remote",
        "salary": "$80,000 - $100,000",
        "job_type": "Full-time",
        "snippet": "We are looking for a Python developer with experience in web frameworks like Flask or Django.",
        "skills": ["Python", "Flask", "Django", "SQL", "Git"],
        "date_posted": "2023-08-15",
        "url": "https://example.com/jobs/1"
    },
    {
        "id": 2,
        "title": "Frontend Developer",
        "company": "Web Creations",
        "location": "New York, NY",
        "salary": "$70,000 - $90,000",
        "job_type": "Full-time",
        "snippet": "Join our team to build responsive and interactive web applications using modern JavaScript frameworks.",
        "skills": ["JavaScript", "React", "HTML", "CSS", "Git"],
        "date_posted": "2023-08-14",
        "url": "https://example.com/jobs/2"
    },
    {
        "id": 3,
        "title": "Data Scientist",
        "company": "Data Insights",
        "location": "San Francisco, CA",
        "salary": "$100,000 - $130,000",
        "job_type": "Full-time",
        "snippet": "Looking for a data scientist to analyze large datasets and build predictive models.",
        "skills": ["Python", "R", "SQL", "Machine Learning", "Statistics"],
        "date_posted": "2023-08-13",
        "url": "https://example.com/jobs/3"
    }
]

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
def list_all_jobs():
    jobs = MOCK_JOBS  # Use mock data for now
    resume_skills = session.get('resume_skills', [])
    
    # If resume skills are active, add matching info to jobs
    if resume_skills:
        for job in jobs:
            job_skills = [s.lower() for s in job.get('skills', [])]
            resume_skills_lower = [s.lower() for s in resume_skills]
            
            # Count matching skills
            matching_skills = sum(1 for s in resume_skills_lower if s in job_skills)
            job['matching_resume_skills'] = matching_skills
        
        # Sort by number of matching skills (descending)
        jobs.sort(key=lambda x: x.get('matching_resume_skills', 0), reverse=True)
    
    return render_template('jobs_list.html', jobs=jobs, query="All", location="All", 
                          resume_skills=resume_skills, current_year=datetime.now().year)

@app.route('/search', methods=['POST'])
def search():
    form = JobSearchForm()
    if form.validate_on_submit():
        query = form.query.data.lower()
        location = form.location.data.lower()
        resume_skills = session.get('resume_skills', [])
        
        # Filter jobs based on query and location
        filtered_jobs = []
        for job in MOCK_JOBS:
            if (query in job['title'].lower() or query in job['company'].lower() or 
                query in job['snippet'].lower() or 
                any(query in skill.lower() for skill in job['skills'])):
                
                if location == 'all' or location in job['location'].lower():
                    filtered_jobs.append(job.copy())
        
        # If resume skills are active, add matching info to jobs
        if resume_skills:
            for job in filtered_jobs:
                job_skills = [s.lower() for s in job.get('skills', [])]
                resume_skills_lower = [s.lower() for s in resume_skills]
                
                # Count matching skills
                matching_skills = sum(1 for s in resume_skills_lower if s in job_skills)
                job['matching_resume_skills'] = matching_skills
            
            # Sort by number of matching skills (descending)
            filtered_jobs.sort(key=lambda x: x.get('matching_resume_skills', 0), reverse=True)
        
        return render_template('jobs_list.html', jobs=filtered_jobs, query=form.query.data, 
                              location=form.location.data, resume_skills=resume_skills, 
                              current_year=datetime.now().year)
    
    return redirect(url_for('index'))

@app.route('/upload_resume', methods=['GET', 'POST'])
@login_required  # Add this decorator to require login
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
def reset_skills():
    if 'resume_skills' in session:
        session.pop('resume_skills')
        flash('Resume skills have been cleared.', 'info')
    return redirect(url_for('index'))

# Add secure_filename import
from werkzeug.utils import secure_filename

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables
    app.run(debug=True)
