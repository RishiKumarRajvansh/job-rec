from app import app, db
from models import Job

def test_db():
    with app.app_context():
        count = Job.query.count()
        print('Number of jobs:', count)

if __name__ == '__main__':
    test_db()
