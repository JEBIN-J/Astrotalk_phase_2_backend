"""
Database-driven Numerology Repository.
Handles querying published interpretations, checking content integrity,
and caching deterministic calculation and interpretation results.
"""
import json
import sqlite3
from typing import Dict, Any, Optional, List
from app.core.database import get_db_connection

class NumerologyRepository:
    _cache: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def get_cache_key(cls, user_id: Optional[str], dob: str, system: str, content_version: str = "1.0.0") -> str:
        u_prefix = f"user_{user_id}:" if user_id else "guest:"
        return f"{u_prefix}{dob}_{system}_{content_version}"

    @classmethod
    def get_cached_result(cls, cache_key: str) -> Optional[Dict[str, Any]]:
        return cls._cache.get(cache_key)

    @classmethod
    def set_cached_result(cls, cache_key: str, data: Dict[str, Any]) -> None:
        cls._cache[cache_key] = data

    @classmethod
    def clear_cache(cls) -> None:
        cls._cache.clear()

    @staticmethod
    def get_published_interpretation(system_code: str, life_path_number: int) -> Optional[Dict[str, Any]]:
        """
        Retrieves published interpretation and its structured sections from SQLite.
        """
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    lpi.id,
                    lpi.life_path_number,
                    lpi.number_title,
                    lpi.core_theme,
                    lpi.overview,
                    lpi.strengths,
                    lpi.challenges,
                    lpi.relationship_interpretation,
                    lpi.career_interpretation,
                    lpi.personal_growth_guidance,
                    lpi.content_version,
                    lpi.publication_status,
                    ns.system_code,
                    ns.system_name,
                    ns.version as system_version
                FROM life_path_interpretations lpi
                JOIN numerology_systems ns ON lpi.numerology_system_id = ns.id
                WHERE ns.system_code = ? 
                  AND lpi.life_path_number = ? 
                  AND lpi.publication_status = 'published'
                  AND ns.is_active = 1
                LIMIT 1
            """, (system_code, life_path_number))
            row = cursor.fetchone()
            if not row:
                return None

            interp_id = row["id"]
            cursor.execute("""
                SELECT section_type, heading, content, display_order
                FROM life_path_interpretation_sections
                WHERE interpretation_id = ? AND publication_status = 'published'
                ORDER BY display_order ASC
            """, (interp_id,))
            section_rows = cursor.fetchall()

            sections = [
                {
                    "section_type": s["section_type"],
                    "heading": s["heading"],
                    "content": s["content"],
                    "display_order": s["display_order"]
                }
                for s in section_rows
            ]

            strengths = json.loads(row["strengths"]) if row["strengths"] else []
            challenges = json.loads(row["challenges"]) if row["challenges"] else []

            return {
                "id": row["id"],
                "life_path_number": row["life_path_number"],
                "number_title": row["number_title"],
                "core_theme": row["core_theme"],
                "overview": row["overview"],
                "strengths": strengths,
                "challenges": challenges,
                "relationship_interpretation": row["relationship_interpretation"],
                "career_interpretation": row["career_interpretation"],
                "personal_growth_guidance": row["personal_growth_guidance"],
                "content_version": row["content_version"],
                "system_code": row["system_code"],
                "system_name": row["system_name"],
                "system_version": row["system_version"],
                "sections": sections
            }
        finally:
            conn.close()

    @staticmethod
    def check_content_completeness(system_code: str = "pythagorean") -> Dict[str, Any]:
        """
        Verifies that all standard numbers (1-9, 11, 22, 33) have published records.
        """
        required_numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 22, 33]
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT lpi.life_path_number
                FROM life_path_interpretations lpi
                JOIN numerology_systems ns ON lpi.numerology_system_id = ns.id
                WHERE ns.system_code = ? AND lpi.publication_status = 'published'
            """, (system_code,))
            rows = cursor.fetchall()
            found = {r["life_path_number"] for r in rows}
            missing = [num for num in required_numbers if num not in found]
            return {
                "is_complete": len(missing) == 0,
                "total_required": len(required_numbers),
                "total_available": len(found),
                "available_numbers": sorted(list(found)),
                "missing_numbers": missing
            }
        finally:
            conn.close()

    @staticmethod
    def get_birth_day_interpretation(system_code: str, day: int) -> Optional[Dict[str, Any]]:
        """
        Retrieves published interpretation and its structured sections for a Birth Day Number (1-31).
        """
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    bdi.id,
                    bdi.birth_day_number,
                    bdi.number_title,
                    bdi.core_theme,
                    bdi.overview,
                    bdi.strengths,
                    bdi.challenges,
                    bdi.personality_interpretation,
                    bdi.relationship_interpretation,
                    bdi.career_interpretation,
                    bdi.personal_growth_guidance,
                    bdi.quick_summary,
                    bdi.reduced_root,
                    bdi.content_version,
                    bdi.publication_status,
                    ns.system_code,
                    ns.system_name,
                    ns.version as system_version
                FROM birth_day_interpretations bdi
                JOIN numerology_systems ns ON bdi.numerology_system_id = ns.id
                WHERE ns.system_code = ? 
                  AND bdi.birth_day_number = ? 
                  AND bdi.publication_status = 'published'
                  AND ns.is_active = 1
                LIMIT 1
            """, (system_code, day))
            row = cursor.fetchone()
            if not row:
                return None

            interp_id = row["id"]
            cursor.execute("""
                SELECT section_type, heading, content, display_order
                FROM birth_day_interpretation_sections
                WHERE interpretation_id = ? AND publication_status = 'published'
                ORDER BY display_order ASC
            """, (interp_id,))
            section_rows = cursor.fetchall()

            sections = [
                {
                    "section_type": s["section_type"],
                    "heading": s["heading"],
                    "content": s["content"],
                    "display_order": s["display_order"]
                }
                for s in section_rows
            ]

            strengths = json.loads(row["strengths"]) if row["strengths"] else []
            challenges = json.loads(row["challenges"]) if row["challenges"] else []
            quick_summary = json.loads(row["quick_summary"]) if row["quick_summary"] else {}

            return {
                "id": row["id"],
                "birth_day_number": row["birth_day_number"],
                "number_title": row["number_title"],
                "core_theme": row["core_theme"],
                "overview": row["overview"],
                "strengths": strengths,
                "challenges": challenges,
                "personality_interpretation": row["personality_interpretation"],
                "relationship_interpretation": row["relationship_interpretation"],
                "career_interpretation": row["career_interpretation"],
                "personal_growth_guidance": row["personal_growth_guidance"],
                "quick_summary": quick_summary,
                "reduced_root": row["reduced_root"],
                "content_version": row["content_version"],
                "system_code": row["system_code"],
                "system_name": row["system_name"],
                "system_version": row["system_version"],
                "sections": sections
            }
        finally:
            conn.close()

    @staticmethod
    def check_birth_day_completeness(system_code: str = "pythagorean") -> Dict[str, Any]:
        """
        Verifies that all 31 days have published records.
        """
        required_days = list(range(1, 32))
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT bdi.birth_day_number
                FROM birth_day_interpretations bdi
                JOIN numerology_systems ns ON bdi.numerology_system_id = ns.id
                WHERE ns.system_code = ? AND bdi.publication_status = 'published'
            """, (system_code,))
            rows = cursor.fetchall()
            found = {r["birth_day_number"] for r in rows}
            missing = [d for d in required_days if d not in found]
            return {
                "is_complete": len(missing) == 0,
                "total_required": len(required_days),
                "total_available": len(found),
                "available_days": sorted(list(found)),
                "missing_days": missing
            }
        finally:
            conn.close()

    @staticmethod
    def get_personal_year_interpretation(system_code: str, personal_year: int) -> Optional[Dict[str, Any]]:
        """
        Retrieves published Personal Year interpretation and its ordered sections.
        """
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    pyi.id,
                    pyi.personal_year_number,
                    pyi.title,
                    pyi.core_theme,
                    pyi.overview,
                    pyi.opportunities,
                    pyi.challenges,
                    pyi.career_and_work,
                    pyi.relationships,
                    pyi.personal_growth,
                    pyi.practical_guidance,
                    pyi.reflection_questions,
                    pyi.content_version,
                    pyi.publication_status,
                    ns.system_code,
                    ns.system_name,
                    ns.version as system_version
                FROM personal_year_interpretations pyi
                JOIN numerology_systems ns ON pyi.numerology_system_id = ns.id
                WHERE ns.system_code = ? 
                  AND pyi.personal_year_number = ? 
                  AND pyi.publication_status = 'published'
                  AND ns.is_active = 1
                LIMIT 1
            """, (system_code, personal_year))
            row = cursor.fetchone()
            if not row:
                return None

            interp_id = row["id"]
            cursor.execute("""
                SELECT section_type, heading, content, display_order
                FROM personal_year_interpretation_sections
                WHERE interpretation_id = ? AND publication_status = 'published'
                ORDER BY display_order ASC
            """, (interp_id,))
            section_rows = cursor.fetchall()

            sections = [
                {
                    "section_type": s["section_type"],
                    "heading": s["heading"],
                    "content": s["content"],
                    "display_order": s["display_order"]
                }
                for s in section_rows
            ]

            opportunities = json.loads(row["opportunities"]) if row["opportunities"] else []
            challenges = json.loads(row["challenges"]) if row["challenges"] else []
            reflection_questions = json.loads(row["reflection_questions"]) if row["reflection_questions"] else []

            return {
                "id": row["id"],
                "personal_year_number": row["personal_year_number"],
                "title": row["title"],
                "core_theme": row["core_theme"],
                "overview": row["overview"],
                "opportunities": opportunities,
                "challenges": challenges,
                "career_and_work": row["career_and_work"],
                "relationships": row["relationships"],
                "personal_growth": row["personal_growth"],
                "practical_guidance": row["practical_guidance"],
                "reflection_questions": reflection_questions,
                "content_version": row["content_version"],
                "system_code": row["system_code"],
                "system_name": row["system_name"],
                "system_version": row["system_version"],
                "sections": sections
            }
        finally:
            conn.close()

    @staticmethod
    def check_personal_year_completeness(system_code: str = "pythagorean") -> Dict[str, Any]:
        """
        Verifies that all 9 Personal Year numbers have published records.
        """
        required_years = list(range(1, 10))
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT pyi.personal_year_number
                FROM personal_year_interpretations pyi
                JOIN numerology_systems ns ON pyi.numerology_system_id = ns.id
                WHERE ns.system_code = ? AND pyi.publication_status = 'published'
            """, (system_code,))
            rows = cursor.fetchall()
            found = {r["personal_year_number"] for r in rows}
            missing = [y for y in required_years if y not in found]
            return {
                "is_complete": len(missing) == 0,
                "total_required": len(required_years),
                "total_available": len(found),
                "available_years": sorted(list(found)),
                "missing_years": missing
            }
        finally:
            conn.close()

    @staticmethod
    def get_name_interpretation(system_code: str, number_type: str, number_value: int) -> Optional[Dict[str, Any]]:
        """
        Retrieves published Name Analysis interpretation for specific system, number type and value.
        """
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    id, system_code, number_type, number_value, title, core_theme, overview,
                    strengths, challenges, relationships, career, guidance, content_version
                FROM name_number_interpretations
                WHERE system_code = ? AND number_type = ? AND number_value = ? AND publication_status = 'published'
                LIMIT 1
            """, (system_code, number_type, number_value))
            row = cursor.fetchone()
            if not row:
                return None

            strengths = json.loads(row["strengths"]) if row["strengths"] else []
            challenges = json.loads(row["challenges"]) if row["challenges"] else []

            return {
                "id": row["id"],
                "system_code": row["system_code"],
                "number_type": row["number_type"],
                "number_value": row["number_value"],
                "title": row["title"],
                "core_theme": row["core_theme"],
                "overview": row["overview"],
                "strengths": strengths,
                "challenges": challenges,
                "relationships": row["relationships"],
                "career": row["career"],
                "guidance": row["guidance"],
                "content_version": row["content_version"]
            }
        finally:
            conn.close()

    @staticmethod
    def get_missing_number_interpretation(missing_number: int, system_code: str = "pythagorean"):
        """
        Retrieves published Missing Number (Karmic Lesson) interpretation for a specific number.
        """
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    m.id, m.missing_number, m.number_title, m.core_theme, m.overview,
                    m.potential_challenges, m.learning_themes, m.practical_guidance,
                    m.relationships_communication, m.work_daily_life, m.reflection_questions,
                    m.content_version, m.publication_status, s.system_code, s.system_name
                FROM missing_number_interpretations m
                JOIN numerology_systems s ON m.numerology_system_id = s.id
                WHERE s.system_code = ? AND m.missing_number = ? AND m.publication_status = 'published'
                LIMIT 1
            """, (system_code, missing_number))
            row = cursor.fetchone()
            if not row:
                return None

            challenges = json.loads(row["potential_challenges"]) if row["potential_challenges"] else []
            learning_themes = json.loads(row["learning_themes"]) if row["learning_themes"] else []
            reflection_questions = json.loads(row["reflection_questions"]) if row["reflection_questions"] else []

            # Retrieve associated sections
            cursor.execute("""
                SELECT section_type, heading, content, display_order
                FROM missing_number_interpretation_sections
                WHERE interpretation_id = ? AND publication_status = 'published'
                ORDER BY display_order ASC
            """, (row["id"],))
            sections = [
                {
                    "section_type": sec["section_type"],
                    "heading": sec["heading"],
                    "content": sec["content"],
                    "display_order": sec["display_order"]
                }
                for sec in cursor.fetchall()
            ]

            return {
                "id": row["id"],
                "missing_number": row["missing_number"],
                "number_title": row["number_title"],
                "core_theme": row["core_theme"],
                "overview": row["overview"],
                "potential_challenges": challenges,
                "learning_themes": learning_themes,
                "practical_guidance": row["practical_guidance"],
                "relationships_communication": row["relationships_communication"],
                "work_daily_life": row["work_daily_life"],
                "reflection_questions": reflection_questions,
                "sections": sections,
                "content_version": row["content_version"],
                "publication_status": row["publication_status"]
            }
        finally:
            conn.close()

    @staticmethod
    def get_all_missing_number_interpretations(system_code: str = "pythagorean"):
        """
        Retrieves all published Missing Number interpretations for the system.
        """
        results = {}
        for num in range(1, 10):
            interp = NumerologyRepository.get_missing_number_interpretation(num, system_code)
            if interp:
                results[num] = interp
        return results

    @staticmethod
    def get_remedy_by_code(remedy_code: str):
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, remedy_code, title, category, focus_area, traditional_association,
                       explanation, instructions, precautions, affirmation, symbolic_color,
                       symbolic_day, estimated_cost_category, is_optional, content_version,
                       publication_status
                FROM numerology_remedies
                WHERE remedy_code = ? AND publication_status = 'published'
                LIMIT 1
            ''', (remedy_code,))
            row = cursor.fetchone()
            if not row:
                return None
            instructions = []
            try:
                instructions = json.loads(row['instructions'])
            except Exception:
                instructions = [row['instructions']]
            return {
                'id': row['id'],
                'remedy_code': row['remedy_code'],
                'title': row['title'],
                'category': row['category'],
                'focus_area': row['focus_area'],
                'traditional_association': row['traditional_association'],
                'explanation': row['explanation'],
                'instructions': instructions,
                'precautions': row['precautions'],
                'affirmation': row['affirmation'],
                'symbolic_color': row['symbolic_color'],
                'symbolic_day': row['symbolic_day'],
                'estimated_cost_category': row['estimated_cost_category'],
                'is_optional': bool(row['is_optional']),
                'content_version': row['content_version']
            }
        finally:
            conn.close()

    @staticmethod
    def check_remedies_completeness(system_code: str = "pythagorean"):
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) as remedy_count
                FROM numerology_remedies rem
                JOIN numerology_remedy_systems s ON rem.system_id = s.id
                WHERE s.system_code = ? AND rem.publication_status = 'published'
            ''', (system_code,))
            rem_count = cursor.fetchone()['remedy_count']

            cursor.execute('''
                SELECT COUNT(*) as rule_count
                FROM numerology_remedy_rules r
                JOIN numerology_remedy_systems s ON r.system_id = s.id
                WHERE s.system_code = ? AND r.publication_status = 'published'
            ''', (system_code,))
            rule_count = cursor.fetchone()['rule_count']

            return {
                'system': system_code,
                'published_remedies': rem_count,
                'published_rules': rule_count,
                'is_complete': rem_count >= 18 and rule_count >= 15
            }
        finally:
            conn.close()

