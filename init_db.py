from app import app, db
from models import User, Job, WorkExperience, Education
from database_manager import init_db as init_sqlite_db
import sqlite3
import os

print("Initializing databases...")

# Create SQLAlchemy tables
with app.app_context():
    # Drop all tables and recreate them
    db.drop_all()
    db.create_all()
    print("SQLAlchemy tables created successfully!")

# Initialize SQLite tables for job scraper
init_sqlite_db()

print("Database initialization completed!")
