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
import traceback  # Import traceback to resolve the "traceback is not defined" error
from werkzeug.utils import secure_filename
import spacy  # Import spacy to resolve the "spacy is not defined" error
from nlp_utils import extract_skills_from_text
from database_manager import get_all_jobs, search_jobs_db, clear_jobs_table, init_db
from nlp_utils import extract_skills_from_text, extract_location_from_text
from resume_parser import parse_resume, extract_text_from_pdf, extract_text_from_docx, extract_text_from_txt

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

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def run_scraper(query="All", location="All"):
    """
    Run the job scraper with the specified query and location.
    
    Args:
        query (str): Job search query
        location (str): Location to search in
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print(f"Running scraper with query='{query}', location='{location}'")
        
        # Initialize database and ensure tables exist
        init_db()
        clear_jobs_table()
        
        # Ensure spaCy is installed and model is downloaded
        ensure_spacy_installed()
        
        # Prepare and run the scraper process
        scraper_command = [sys.executable, "scraper.py"]
        
        # Always pass the arguments, the scraper will handle "All" values internally
        scraper_command.extend(["--query", query])
        scraper_command.extend(["--location", location])
        
        print(f"Running scraper with command: {' '.join(scraper_command)}")
        
        result = subprocess.run(
            scraper_command,
            capture_output=True,
            text=True
        )
        
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
    try:
        query = request.form.get('query', 'all')
        location = request.form.get('location', 'all')
        
        # Get resume skills
        resume_skills = session.get('resume_skills', [])
        
        # If query is "All" and we have resume skills, use top skills for the query
        if (query.lower() == 'all' or not query) and resume_skills:
            # Use top 3 skills for the query
            query = " ".join(resume_skills[:3])
            print(f"Using resume skills for query: {query}")
        
        # Initialize database and ensure tables exist
        from database_manager import init_db, clear_jobs_table, get_all_jobs
        init_db()
        clear_jobs_table()
        
        # Run the scraper with the modified query
        if not run_scraper(query, location):
            return jsonify({
                'status': 'error',
                'message': 'Failed to run job scraper. Please try again.'
            }), 500
        
        # Get all jobs from the database
        jobs = get_all_jobs()
        
        # If no jobs found after scraping
        if not jobs:
            return jsonify({
                'status': 'success', 
                'message': 'No jobs found.',
                'jobs': []
            })
        
        # Compare job skills with resume skills
        for job in jobs:
            job_skills = job.get('skills', [])
            if job_skills and resume_skills:
                matching_skills = set(s.lower() for s in job_skills) & set(s.lower() for s in resume_skills)
                job['matching_skills'] = list(matching_skills)
                job['skill_match_percentage'] = int(len(matching_skills) / len(resume_skills) * 100) if resume_skills else 0
            else:
                job['matching_skills'] = []
                job['skill_match_percentage'] = 0
        
        # Sort jobs by skill match percentage
        jobs = sorted(jobs, key=lambda x: x.get('skill_match_percentage', 0), reverse=True)
        
        total_jobs = len(jobs)
        print(f"Found {total_jobs} jobs matching the criteria")
        if total_jobs > 0:
            print(f"First job: {jobs[0].get('title')} at {jobs[0].get('company')}")
        
        return jsonify({
            'status': 'success',
            'message': f'Found {total_jobs} jobs matching your criteria.',
            'jobs': jobs
        })
    
    except Exception as e:
        print(f"Error in run_scraper_api: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'An error occurred: {str(e)}'
        }), 500


# @app.route('/search', methods=['POST'])
# @login_required
# def search():
#     form = JobSearchForm()
#     if form.validate_on_submit():
#         query = form.query.data
#         location = form.location.data
#         resume_skills = session.get('resume_skills', [])
        
#         # Render the template with a flag to indicate we need to run the scraper
#         return render_template('jobs_list.html',
#                                jobs=[],
#                                query=query,
#                                location=location,
#                               resume_skills=resume_skills,
#                                current_year=datetime.now().year,
#                               run_scraper=True)  # Flag to trigger scraping in the template
    
#     return redirect(url_for('index'))
@app.route('/search', methods=['POST'])
@login_required
def search():
    form = JobSearchForm()
    if form.validate_on_submit():
        query = form.query.data
        location = form.location.data
        
        # Use resume location if available and no specific location is provided
        if location.lower() == 'all' and 'resume_location' in session and session['resume_location']:
            location = session['resume_location']
            flash(f"Using location from your resume: {location}", "info")
        
        # Use resume skills for the query if no specific query is provided
        resume_skills = session.get('resume_skills', [])
        if query.lower() == 'all' and resume_skills:
            # Use the first few skills as the query
            query = " ".join(resume_skills[:3])
            flash(f"Using skills from your resume for search: {query}", "info")
        
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
    """Upload and process a resume file"""
    if request.method == 'POST':
        if 'resume' not in request.files:
            flash('No file part', 'error')
            return redirect(request.referrer or url_for('index'))
            
        file = request.files['resume']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.referrer or url_for('index'))
            
        if file and allowed_file(file.filename):
            try:
                # Save the file temporarily
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                file.save(file_path)
                
                # Load NLP model
                nlp = spacy.load("en_core_web_sm")
                
                # Extract text based on file type
                file_extension = os.path.splitext(filename)[1].lower()
                if file_extension == '.pdf':
                    text = extract_text_from_pdf(file_path)
                elif file_extension == '.docx':
                    text = extract_text_from_docx(file_path)
                elif file_extension == '.txt':
                    text = extract_text_from_txt(file_path)
                else:
                    raise ValueError('Unsupported file format')
                
                # Process the text
                skills = extract_skills_from_text(text, nlp)
                location = extract_location_from_text(text, nlp)
                
                # Store in session
                session['resume_skills'] = skills
                session['resume_location'] = location
                
                flash('Resume processed successfully', 'success')
                return redirect(url_for('index'))
                
            except Exception as e:
                flash(f'Error processing resume: {str(e)}', 'error')
            finally:
                # Clean up temporary file
                if os.path.exists(file_path):
                    os.remove(file_path)
        else:
            flash('Invalid file format. Please upload a PDF, DOCX, or TXT file.', 'error')
    
    return render_template('upload_resume.html', current_year=datetime.now().year)



@app.route('/debug_resume_parser', methods=['GET', 'POST'])
@login_required
def debug_resume_parser():
    """Debug route to test resume parsing directly"""
    if request.method == 'GET':
        return render_template('debug_resume.html', current_year=datetime.now().year)
    
    if 'resume' not in request.files:
        return jsonify({'error': 'No file part'})
    
    file = request.files['resume']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    
    if file and allowed_file(file.filename):
        # Save the file temporarily
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        debug_info = {
            'file_path': file_path,
            'file_size': os.path.getsize(file_path),
            'file_exists': os.path.exists(file_path),
            'steps': []
        }
        
        try:
            # Step 1: Load NLP model
            debug_info['steps'].append({'step': 'Loading NLP model'})
            nlp_model = spacy.load("en_core_web_sm")
            debug_info['steps'].append({'step': 'NLP model loaded successfully'})
            
            # Step 2: Import functions
            debug_info['steps'].append({'step': 'Importing functions'})
            from nlp_utils import extract_skills_from_text
            from resume_parser import parse_resume, extract_text_from_pdf, extract_text_from_docx, extract_text_from_txt
            debug_info['steps'].append({'step': 'Functions imported successfully'})
            
            # Step 3: Extract text based on file extension
            debug_info['steps'].append({'step': 'Extracting text from file'})
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension == '.pdf':
                extracted_text = extract_text_from_pdf(file_path)
            elif file_extension == '.docx':
                extracted_text = extract_text_from_docx(file_path)
            elif file_extension == '.txt':
                extracted_text = extract_text_from_txt(file_path)
            else:
                extracted_text = "Unsupported file format"
            
            debug_info['text_length'] = len(extracted_text)
            debug_info['text_preview'] = extracted_text[:500] + '...' if len(extracted_text) > 500 else extracted_text
            debug_info['steps'].append({'step': f'Text extracted successfully, length: {len(extracted_text)}'})
            
            # Step 4: Extract skills
            debug_info['steps'].append({'step': 'Extracting skills'})
            extracted_skills = extract_skills_from_text(extracted_text, nlp_model)
            debug_info['skills'] = extracted_skills
            debug_info['steps'].append({'step': f'Skills extracted successfully, count: {len(extracted_skills)}'})
            
            # Step 5: Extract location
            debug_info['steps'].append({'step': 'Extracting location'})
            from resume_parser import extract_location_from_text
            extracted_location = extract_location_from_text(extracted_text, nlp_model)
            debug_info['location'] = extracted_location
            debug_info['steps'].append({'step': f'Location extracted: {extracted_location}'})
            
            # Clean up
            os.remove(file_path)
            debug_info['steps'].append({'step': 'Temporary file removed'})
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            debug_info['error'] = str(e)
            debug_info['error_details'] = error_details
            debug_info['steps'].append({'step': f'Error: {str(e)}'})
            
            # Try to remove the temporary file if it exists
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    debug_info['steps'].append({'step': 'Temporary file removed after error'})
            except:
                pass
        
        return jsonify(debug_info)
    
    return jsonify({'error': 'Invalid file type'})



@app.route('/reset_skills')
@login_required
def reset_skills():
    if 'resume_skills' in session:
        session.pop('resume_skills')
        flash('Resume skills have been cleared.', 'info')
    return redirect(url_for('index'))

@app.route('/enter_location', methods=['GET', 'POST'])
@login_required
def enter_location():
    """Page to manually enter location if not found in resume"""
    if request.method == 'POST':
        location = request.form.get('location', '')
        session['resume_location'] = location
        return redirect(url_for('jobs_list', query='all', location=location, run_scraper=True))
    
    return render_template('enter_location.html')
@app.route('/debug_skills', methods=['GET', 'POST'])
def debug_skills():
    """Debug route for testing skill extraction"""
    if request.method == 'POST':
        if 'resume' not in request.files:
            return jsonify({'error': 'No file part'})
        
        file = request.files['resume']
        
        if file.filename == '':
            return jsonify({'error': 'No selected file'})
        
        if file and allowed_file(file.filename):
            # Save the file temporarily
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Create the upload folder if it doesn't exist
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            
            file.save(file_path)
            print(f"Resume saved temporarily at: {file_path}")
            
            try:
                # Load spaCy model
                print("Loading spaCy model...")
                nlp = spacy.load("en_core_web_sm")
                
                # Extract text from the resume
                print("Extracting text from file...")
                file_extension = os.path.splitext(filename)[1].lower()
                
                if file_extension == '.pdf':
                    text = extract_text_from_pdf(file_path)
                elif file_extension == '.docx':
                    text = extract_text_from_docx(file_path)
                elif file_extension == '.txt':
                    text = extract_text_from_txt(file_path)
                else:
                    return jsonify({'error': 'Unsupported file format'})
                
                print(f"Extracted text length: {len(text)}")
                
                if not text:
                    return jsonify({'error': 'Could not extract text from the resume'})
                
                # Extract skills from the text
                print("Extracting skills...")
                skills = extract_skills_from_text(text, nlp)
                
                # Extract location from the text
                print("Extracting location...")
                location = extract_location_from_text(text, nlp)
                
                return jsonify({
                    'success': True,
                    'text_length': len(text),
                    'text_preview': text[:500] + '...' if len(text) > 500 else text,
                    'skills': skills,
                    'skills_count': len(skills),
                    'location': location
                })
            except Exception as e:
                return jsonify({'error': f'Error processing resume: {str(e)}'})
            finally:
                # Remove the temporary file
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"Temporary file removed: {file_path}")
        else:
            return jsonify({'error': 'Invalid file format. Please upload a PDF, DOCX, or TXT file.'})
    
    # If GET request, show the upload form
    return '''
    <!doctype html>
    <html>
    <head>
        <title>Debug Skills Extraction</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            h1 { color: #333; }
            form { margin-bottom: 20px; }
            #result { white-space: pre-wrap; background: #f5f5f5; padding: 15px; border-radius: 5px; }
            .skills-list { display: flex; flex-wrap: wrap; }
            .skill { background: #e0f7fa; padding: 5px 10px; margin: 5px; border-radius: 15px; }
        </style>
    </head>
    <body>
        <h1>Debug Skills Extraction</h1>
        <form id="upload-form" enctype="multipart/form-data">
            <input type="file" name="resume" accept=".pdf,.docx,.txt">
            <button type="submit">Upload and Extract Skills</button>
        </form>
        <div id="result"></div>
        
        <script>
            document.getElementById('upload-form').addEventListener('submit', function(e) {
                e.preventDefault();
                
                const form = new FormData(this);
                const resultDiv = document.getElementById('result');
                
                resultDiv.innerHTML = 'Processing...';
                
                fetch('/debug_skills', {
                    method: 'POST',
                    body: form
                })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        resultDiv.innerHTML = `<h2>Error</h2><p>${data.error}</p>`;
                    } else {
                        let skillsHtml = '';
                        if (data.skills && data.skills.length > 0) {
                            skillsHtml = '<div class="skills-list">';
                            data.skills.forEach(skill => {
                                skillsHtml += `<div class="skill">${skill}</div>`;
                            });
                            skillsHtml += '</div>';
                        } else {
                            skillsHtml = '<p>No skills extracted</p>';
                        }
                        
                        resultDiv.innerHTML = `
                            <h2>Results</h2>
                            <p><strong>Text Length:</strong> ${data.text_length} characters</p>
                            <p><strong>Text Preview:</strong></p>
                            <div style="max-height: 200px; overflow-y: auto; margin-bottom: 20px;">
                                ${data.text_preview}
                            </div>
                            <p><strong>Location:</strong> ${data.location || 'Not found'}</p>
                            <p><strong>Skills (${data.skills_count}):</strong></p>
                            ${skillsHtml}
                        `;
                    }
                })
                .catch(error => {
                    resultDiv.innerHTML = `<h2>Error</h2><p>${error.message}</p>`;
                });
            });
        </script>
    </body>
    </html>
    '''

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables
    app.run(debug=True)
