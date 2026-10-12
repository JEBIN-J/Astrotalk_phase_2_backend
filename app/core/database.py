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
            
        # Tarot tables
        conn.execute('''
            CREATE TABLE IF NOT EXISTS tarot_daily_readings (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                card_id TEXT NOT NULL,
                orientation TEXT NOT NULL,
                seed TEXT NOT NULL,
                date TEXT NOT NULL,
                timezone REAL NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(user_id, date)
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS tarot_readings_history (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                reading_type TEXT NOT NULL,
                question TEXT,
                spread_data TEXT NOT NULL,
                astrology_snapshot TEXT,
                seed TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')
        
        
        # Numerology tables
        conn.execute('''
            CREATE TABLE IF NOT EXISTS numerology_systems (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                system_code TEXT UNIQUE NOT NULL,
                system_name TEXT NOT NULL,
                calculation_method TEXT NOT NULL,
                master_number_policy TEXT NOT NULL,
                version TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS life_path_interpretations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numerology_system_id INTEGER NOT NULL,
                life_path_number INTEGER NOT NULL,
                number_title TEXT NOT NULL,
                core_theme TEXT NOT NULL,
                overview TEXT NOT NULL,
                strengths TEXT NOT NULL,
                challenges TEXT NOT NULL,
                relationship_interpretation TEXT NOT NULL,
                career_interpretation TEXT NOT NULL,
                personal_growth_guidance TEXT NOT NULL,
                content_version TEXT NOT NULL DEFAULT '1.0.0',
                publication_status TEXT NOT NULL DEFAULT 'published',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (numerology_system_id) REFERENCES numerology_systems(id),
                UNIQUE(numerology_system_id, life_path_number, content_version)
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS life_path_interpretation_sections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                interpretation_id INTEGER NOT NULL,
                section_type TEXT NOT NULL,
                heading TEXT NOT NULL,
                content TEXT NOT NULL,
                display_order INTEGER NOT NULL,
                publication_status TEXT NOT NULL DEFAULT 'published',
                FOREIGN KEY (interpretation_id) REFERENCES life_path_interpretations(id)
            )
        ''')

        
        # Birth Day Tables
        conn.execute('''
            CREATE TABLE IF NOT EXISTS birth_day_interpretations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numerology_system_id INTEGER NOT NULL,
                birth_day_number INTEGER NOT NULL,
                number_title TEXT NOT NULL,
                core_theme TEXT NOT NULL,
                overview TEXT NOT NULL,
                strengths TEXT NOT NULL,
                challenges TEXT NOT NULL,
                personality_interpretation TEXT NOT NULL,
                relationship_interpretation TEXT NOT NULL,
                career_interpretation TEXT NOT NULL,
                personal_growth_guidance TEXT NOT NULL,
                quick_summary TEXT NOT NULL,
                reduced_root INTEGER NOT NULL,
                content_version TEXT NOT NULL DEFAULT '1.0.0',
                publication_status TEXT NOT NULL DEFAULT 'published',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (numerology_system_id) REFERENCES numerology_systems(id),
                UNIQUE(numerology_system_id, birth_day_number, content_version)
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS birth_day_interpretation_sections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                interpretation_id INTEGER NOT NULL,
                section_type TEXT NOT NULL,
                heading TEXT NOT NULL,
                content TEXT NOT NULL,
                display_order INTEGER NOT NULL,
                publication_status TEXT NOT NULL DEFAULT 'published',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (interpretation_id) REFERENCES birth_day_interpretations(id)
            )
        ''')

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
