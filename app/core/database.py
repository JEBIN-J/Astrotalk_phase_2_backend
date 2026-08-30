import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dataset.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    try:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS palm_annotations (
                id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')
        
        # Add new columns if they don't exist
        cursor = conn.execute("PRAGMA table_info(palm_annotations)")
        columns = [row['name'] for row in cursor.fetchall()]
        if 'original_image' not in columns:
            conn.execute("ALTER TABLE palm_annotations ADD COLUMN original_image TEXT")
        if 'annotated_image' not in columns:
            conn.execute("ALTER TABLE palm_annotations ADD COLUMN annotated_image TEXT")
            
        conn.commit()
    finally:
        conn.close()

# Initialize tables on import
init_db()

def save_palm_annotation(record_id: str, data: dict, created_at: str, original_image: str = None, annotated_image: str = None):
    conn = get_db_connection()
    try:
        conn.execute(
            'INSERT INTO palm_annotations (id, data, created_at, original_image, annotated_image) VALUES (?, ?, ?, ?, ?)',
            (record_id, json.dumps(data), created_at, original_image, annotated_image)
        )
        conn.commit()
    finally:
        conn.close()
