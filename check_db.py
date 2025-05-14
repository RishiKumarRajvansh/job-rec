import sqlite3
import os

DB_PATH = 'instance/job_recommender.db'

def check_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("=== Database Tables ===")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    for table in tables:
        print(f"\nTable: {table[0]}")
        cursor.execute(f"PRAGMA table_info({table[0]})")
        columns = cursor.fetchall()
        print("Columns:", [col[1] for col in columns])
        
        cursor.execute(f"SELECT * FROM {table[0]}")
        rows = cursor.fetchall()
        print(f"Row count: {len(rows)}")
        if table[0] == 'user':
            print("\nUsers in database:")
            for row in rows:
                print(row)
    
    conn.close()

if __name__ == "__main__":
    check_db()
