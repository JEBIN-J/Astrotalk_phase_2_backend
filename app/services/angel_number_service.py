"""
angel_number_service.py
Service handling Angel Numbers lookups, reductions, pattern detections,
personal angel number calculations, mirror hour queries, sightings journal,
and daily reflections.
Strictly deterministic, no fabrication or random generation.
"""

from datetime import datetime
import json
from typing import Dict, Any, List, Optional
from app.core.database import get_db_connection
from app.services.angel_number_engine import AngelNumberEngine

class AngelNumberService:

    @staticmethod
    def lookup_sequence(raw_input: str) -> Dict[str, Any]:
        """
        Processes a submitted number or clock pattern.
        Returns deterministic reduction steps, pattern analysis,
        and approved interpretation from dataset.db.
        """
        # 1. Normalize and validate
        try:
            canonical = AngelNumberEngine.normalize_input(raw_input)
        except ValueError as ve:
            return {
                "success": False,
                "error": str(ve),
                "raw_input": raw_input
            }
        
        is_clock = ':' in canonical

        # 2. Reduction calculation
        reduction = AngelNumberEngine.reduce_sequence(canonical)
        
        # 3. Pattern detection
        pattern_res = AngelNumberEngine.detect_patterns(canonical)
        patterns = pattern_res.get("detected_patterns", [])
        primary_pattern = pattern_res.get("primary_pattern")

        # 4. Fetch interpretation from database
        conn = get_db_connection()
        cursor = conn.cursor()

        # Query exact interpretation (supporting both clock and plain)
        cursor.execute(
            """
            SELECT * FROM angel_number_interpretations
            WHERE (canonical_sequence = ? OR canonical_sequence = ?) AND is_active = 1
            LIMIT 1
            """,
            (canonical, canonical.replace(':', ''))
        )
        row = cursor.fetchone()

        interpretation = None
        has_reviewed_interpretation = False

        if row:
            has_reviewed_interpretation = True
            interpretation = {
                "id": row["id"],
                "sequence": row["sequence"],
                "canonical_sequence": row["canonical_sequence"],
                "title": row["title"],
                "short_meaning": row["short_meaning"],
                "detailed_meaning": row["detailed_meaning"],
                "traditional_symbolic_themes": json.loads(row["traditional_symbolic_themes"] or "[]"),
                "reflection_questions": json.loads(row["reflection_questions"] or "[]"),
                "practical_guidance": row["practical_guidance"],
                "love_and_relationships": row["love_and_relationships"],
                "career_and_work": row["career_and_work"],
                "personal_growth": row["personal_growth"],
                "spiritual_reflection": row["spiritual_reflection"],
                "root_number": row["root_number"],
                "primary_pattern": row["primary_pattern"],
                "source_reference": row["source_reference"],
                "content_version": row["content_version"]
            }

        # 5. Fetch related numbers (other published records sharing pattern or root)
        related_sequences = []
        if has_reviewed_interpretation:
            cursor.execute(
                """
                SELECT canonical_sequence, title, short_meaning, root_number
                FROM angel_number_interpretations
                WHERE is_active = 1 AND canonical_sequence != ?
                ORDER BY 
                    CASE WHEN root_number = ? THEN 0 ELSE 1 END,
                    id ASC
                LIMIT 4
                """,
                (canonical, reduction["root_number"])
            )
            for r in cursor.fetchall():
                related_sequences.append({
                    "sequence": r["canonical_sequence"],
                    "title": r["title"],
                    "short_meaning": r["short_meaning"],
                    "root_number": r["root_number"]
                })

        # 6. Fetch root number interpretation snippet if distinct
        root_number_info = None
        root_num = reduction["root_number"]
        if canonical != str(root_num):
            cursor.execute(
                """
                SELECT canonical_sequence, title, short_meaning, personal_growth
                FROM angel_number_interpretations
                WHERE canonical_sequence = ? AND is_active = 1
                LIMIT 1
                """,
                (str(root_num),)
            )
            root_row = cursor.fetchone()
            if root_row:
                root_number_info = {
                    "number": root_num,
                    "title": root_row["title"],
                    "short_meaning": root_row["short_meaning"],
                    "growth_note": root_row["personal_growth"]
                }

        conn.close()

        return {
            "success": True,
            "raw_input": raw_input,
            "normalized_sequence": canonical,
            "is_clock_format": is_clock,
            "reduction": reduction,
            "detected_patterns": patterns,
            "primary_pattern": primary_pattern,
            "has_reviewed_interpretation": has_reviewed_interpretation,
            "interpretation": interpretation,
            "root_number_info": root_number_info,
            "related_sequences": related_sequences,
            "status_message": (
                "Approved interpretation loaded." if has_reviewed_interpretation
                else "No reviewed interpretation currently available for this sequence. Calculation steps and pattern detection are provided based on deterministic reduction rules."
            )
        }

    @staticmethod
    def get_published_patterns() -> List[Dict[str, Any]]:
        """Returns all approved pattern classifications."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, pattern_code, pattern_name, pattern_description, display_priority
            FROM angel_number_patterns
            WHERE is_active = 1
            ORDER BY display_priority ASC
            """
        )
        rows = cursor.fetchall()
        patterns = [dict(r) for r in rows]
        conn.close()
        return patterns

    @staticmethod
    def get_popular_sequences() -> List[Dict[str, Any]]:
        """Returns verified, reviewed entries for browsing."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT canonical_sequence, title, short_meaning, root_number
            FROM angel_number_interpretations
            WHERE is_active = 1
            ORDER BY id ASC
            LIMIT 20
            """
        )
        rows = cursor.fetchall()
        results = [dict(r) for r in rows]
        conn.close()
        return results

    @staticmethod
    def get_mirror_hours() -> List[Dict[str, Any]]:
        """Returns published clock-format sequences with time analysis."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT canonical_sequence, title, short_meaning, detailed_meaning, practical_guidance, root_number
            FROM angel_number_interpretations
            WHERE is_active = 1 AND (canonical_sequence LIKE '%:%' OR primary_pattern = 'mirror_hour')
            ORDER BY canonical_sequence ASC
            """
        )
        rows = cursor.fetchall()
        results = []
        for r in rows:
            seq = r["canonical_sequence"]
            pat_res = AngelNumberEngine.detect_patterns(seq)
            results.append({
                "time": seq,
                "title": r["title"],
                "short_meaning": r["short_meaning"],
                "detailed_meaning": r["detailed_meaning"],
                "practical_guidance": r["practical_guidance"],
                "root_number": r["root_number"],
                "patterns": pat_res.get("detected_patterns", [])
            })
        conn.close()
        return results

    @staticmethod
    def calculate_personal_number(method: str, dob: Optional[str] = None, name: Optional[str] = None) -> Dict[str, Any]:
        """Calculates personal angel number via DOB (Method A) or Name (Method B)."""
        try:
            if method == "name":
                calc_res = AngelNumberEngine.calculate_personal_angel_number(name=name)
            else:
                calc_res = AngelNumberEngine.calculate_personal_angel_number(dob_str=dob)
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
        
        # Look up interpretation for the resulting personal angel sequence or root
        seq_to_lookup = calc_res.get("personal_angel_number") or str(calc_res["root_number"])
        lookup_data = AngelNumberService.lookup_sequence(seq_to_lookup)

        return {
            "success": True,
            "method": method,
            "calculation": calc_res,
            "sequence_interpretation": lookup_data
        }

    @staticmethod
    def get_daily_reflection(date_str: Optional[str] = None, timezone: str = "UTC") -> Dict[str, Any]:
        """
        Deterministic daily reflection based on date.
        Never random.
        """
        if not date_str:
            date_str = datetime.utcnow().strftime("%Y-%m-%d")
        
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            doy = dt.timetuple().tm_yday
        except Exception:
            doy = 1

        conn = get_db_connection()
        cursor = conn.cursor()

        # Query explicit day of year record
        cursor.execute(
            """
            SELECT * FROM angel_number_daily_content
            WHERE day_of_year_index = ? AND is_active = 1
            LIMIT 1
            """,
            (doy,)
        )
        row = cursor.fetchone()

        if not row:
            cursor.execute("SELECT COUNT(*) as count FROM angel_number_daily_content WHERE is_active = 1")
            total = cursor.fetchone()["count"]
            if total > 0:
                offset = doy % total
                cursor.execute(
                    """
                    SELECT * FROM angel_number_daily_content
                    WHERE is_active = 1
                    ORDER BY id ASC
                    LIMIT 1 OFFSET ?
                    """,
                    (offset,)
                )
                row = cursor.fetchone()

        if not row:
            conn.close()
            return {
                "success": False,
                "error": "No daily reflections configured"
            }

        daily = {
            "sequence": row["sequence"],
            "date": date_str,
            "title": row["title"],
            "reflection": row["reflection"],
            "methodology_version": "1.0.0",
            "language": "en"
        }
        conn.close()
        return {
            "success": True,
            "daily": daily
        }

    # ==========================
    # Journal Operations
    # ==========================

    @staticmethod
    def add_sighting(
        user_id: str,
        observed_sequence: str,
        observed_at: Optional[str] = None,
        timezone: str = "UTC",
        context_category: Optional[str] = None,
        personal_note: Optional[str] = None,
        mood: Optional[str] = None
    ) -> Dict[str, Any]:
        """Saves a verified sighting to the user's journal."""
        try:
            canonical = AngelNumberEngine.normalize_input(observed_sequence)
        except ValueError as ve:
            return {"success": False, "error": str(ve)}

        if not observed_at:
            observed_at = datetime.utcnow().isoformat()
        
        now_ts = datetime.utcnow().isoformat()

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO angel_number_sightings (
                user_id, observed_sequence, observed_at, timezone,
                context_category, personal_note, mood, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id, canonical, observed_at, timezone,
                context_category, personal_note, mood, now_ts, now_ts
            )
        )
        sighting_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return {
            "success": True,
            "sighting_id": sighting_id,
            "observed_sequence": canonical,
            "observed_at": observed_at
        }

    @staticmethod
    def get_sightings(user_id: str, search: Optional[str] = None) -> Dict[str, Any]:
        """Returns all genuine sightings for the authenticated user only."""
        conn = get_db_connection()
        cursor = conn.cursor()

        if search:
            cursor.execute(
                """
                SELECT * FROM angel_number_sightings
                WHERE user_id = ? AND (observed_sequence LIKE ? OR personal_note LIKE ?)
                ORDER BY observed_at DESC
                """,
                (user_id, f"%{search}%", f"%{search}%")
            )
        else:
            cursor.execute(
                """
                SELECT * FROM angel_number_sightings
                WHERE user_id = ?
                ORDER BY observed_at DESC
                """,
                (user_id,)
            )
        rows = cursor.fetchall()
        sightings = [dict(r) for r in rows]

        # Calculate genuine counts from real sightings
        total_sightings = len(sightings)
        sequence_counts: Dict[str, int] = {}
        for s in sightings:
            seq = s["observed_sequence"]
            sequence_counts[seq] = sequence_counts.get(seq, 0) + 1
        
        most_frequent = None
        if sequence_counts:
            most_frequent = max(sequence_counts.items(), key=lambda x: x[1])[0]

        conn.close()
        return {
            "success": True,
            "sightings": sightings,
            "total_sightings": total_sightings,
            "unique_sequences_count": len(sequence_counts),
            "most_frequent_sequence": most_frequent,
            "frequency_breakdown": sequence_counts
        }

    @staticmethod
    def update_sighting(
        user_id: str,
        sighting_id: int,
        context_category: Optional[str] = None,
        personal_note: Optional[str] = None,
        mood: Optional[str] = None
    ) -> Dict[str, Any]:
        """Updates a user's sighting after verifying ownership."""
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id, user_id FROM angel_number_sightings WHERE id = ?", (sighting_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return {"success": False, "error": "Sighting not found"}
        
        if str(row["user_id"]) != str(user_id):
            conn.close()
            return {"success": False, "error": "Unauthorized: Cannot edit another user's sighting"}

        now_ts = datetime.utcnow().isoformat()
        cursor.execute(
            """
            UPDATE angel_number_sightings
            SET context_category = coalesce(?, context_category),
                personal_note = coalesce(?, personal_note),
                mood = coalesce(?, mood),
                updated_at = ?
            WHERE id = ? AND user_id = ?
            """,
            (context_category, personal_note, mood, now_ts, sighting_id, user_id)
        )
        conn.commit()
        conn.close()
        return {"success": True, "message": "Sighting updated"}

    @staticmethod
    def delete_sighting(user_id: str, sighting_id: int) -> Dict[str, Any]:
        """Deletes a sighting after verifying ownership."""
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id, user_id FROM angel_number_sightings WHERE id = ?", (sighting_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return {"success": False, "error": "Sighting not found"}
        
        if str(row["user_id"]) != str(user_id):
            conn.close()
            return {"success": False, "error": "Unauthorized: Cannot delete another user's sighting"}

        cursor.execute("DELETE FROM angel_number_sightings WHERE id = ? AND user_id = ?", (sighting_id, user_id))
        conn.commit()
        conn.close()
        return {"success": True, "message": "Sighting deleted"}
