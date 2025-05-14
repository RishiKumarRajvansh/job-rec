from app import app, db
import os
from database_manager import DB_PATH, get_db_connection, init_db as init_sqlite_db
from models import Job, JobSkill, User, WorkExperience, Education

def init_db():
    """Creates both SQLite and SQLAlchemy databases"""
    print("Initializing databases...")

    # Initialize SQLite tables first
    print("Initializing SQLite database...")
    init_sqlite_db()

    # Then initialize SQLAlchemy tables
    print("Initializing SQLAlchemy database...")
    with app.app_context():
        db.drop_all()  # This will clear existing tables
        db.create_all()
        print("SQLAlchemy tables created successfully!")

    print("Database initialization completed!")

if __name__ == "__main__":
    init_db()
