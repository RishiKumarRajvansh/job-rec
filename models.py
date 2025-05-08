from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))

    skills = db.Column(db.Text, nullable=True) # User's skills
    experience_summary = db.Column(db.Text, nullable=True)
    education_summary = db.Column(db.Text, nullable=True)
    
    # job_postings relationship was for manual entry, we can comment out or remove if not pursuing that path
    # job_postings = db.relationship('JobPosting', backref='author', lazy=True) 

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

# We are removing the previously discussed JobPosting model for manual entry
# and replacing it with a Job model for scraped jobs.

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    company = db.Column(db.String(255), nullable=True)
    location = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True) # Full description if available
    skills_raw_text = db.Column(db.Text, nullable=True) # Comma-separated or raw text of skills
    source_url = db.Column(db.String(512), nullable=False, unique=True) # URL of the job posting on Indeed
    date_scraped = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    source_site = db.Column(db.String(50), nullable=False, default='Indeed.com') # To track where it came from

    def __repr__(self):
        return f'<Job {self.title} at {self.company}>'

# If you had the JobPosting model from our previous incorrect discussion,
# ensure it's removed or commented out to avoid conflicts.
# class JobPosting(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     title = db.Column(db.String(150), nullable=False)
#     # ... other fields ...
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
