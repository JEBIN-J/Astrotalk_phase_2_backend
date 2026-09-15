import json
import uuid
from datetime import datetime
from app.core.database import get_db_connection

class TarotHistoryService:
    @staticmethod
    def save_daily_reading(user_id: str, card_id: str, orientation: str, seed: str, date_str: str, timezone: float):
        conn = get_db_connection()
        try:
            record_id = str(uuid.uuid4())
            created_at = datetime.utcnow().isoformat()
            
            # Using INSERT OR REPLACE or handle the unique constraint
            conn.execute('''
                INSERT INTO tarot_daily_readings (id, user_id, card_id, orientation, seed, date, timezone, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, date) DO NOTHING
            ''', (record_id, user_id, card_id, orientation, seed, date_str, timezone, created_at))
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def get_daily_reading(user_id: str, date_str: str):
        conn = get_db_connection()
        try:
            cursor = conn.execute('''
                SELECT * FROM tarot_daily_readings WHERE user_id = ? AND date = ?
            ''', (user_id, date_str))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        finally:
            conn.close()

    @staticmethod
    def save_reading(user_id: str, reading_type: str, question: str, spread_data: dict, astro_snapshot: dict, seed: str):
        conn = get_db_connection()
        try:
            record_id = str(uuid.uuid4())
            created_at = datetime.utcnow().isoformat()
            
            conn.execute('''
                INSERT INTO tarot_readings_history (id, user_id, reading_type, question, spread_data, astrology_snapshot, seed, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                record_id, user_id, reading_type, question, 
                json.dumps(spread_data), 
                json.dumps(astro_snapshot) if astro_snapshot else None, 
                seed, created_at
            ))
            conn.commit()
            return record_id
        finally:
            conn.close()

    @staticmethod
    def get_user_history(user_id: str):
        conn = get_db_connection()
        try:
            cursor = conn.execute('''
                SELECT * FROM tarot_readings_history WHERE user_id = ? ORDER BY created_at DESC
            ''', (user_id,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
