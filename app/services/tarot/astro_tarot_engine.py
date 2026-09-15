from datetime import datetime, timezone as dt_timezone, timedelta
from typing import Dict, Any, List
from .tarot_engine import TarotEngine
import app.services.vedic_engine as vedic_engine

class AstroTarotEngine:
    @staticmethod
    def get_astro_tarot_reading(
        birth_date: str, # YYYY-MM-DD
        birth_time: str, # HH:MM
        latitude: float,
        longitude: float,
        tz_offset: float,
        question: str = "",
        seed: str = None
    ) -> Dict[str, Any]:
        """
        Combines a real-time astrological transit calculation with a Tarot draw.
        """
        # Parse birth date
        dt_str = f"{birth_date} {birth_time}"
        birth_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")

        # 1. Calculate Natal Chart Data
        # Using exact same precision engine as the main astrology app
        hour_ut = birth_dt.hour - tz_offset + birth_dt.minute / 60.0
        jd_birth = vedic_engine.calculate_julian_day(birth_dt.year, birth_dt.month, birth_dt.day, hour_ut)
        ayanamsa_natal = vedic_engine.calculate_lahiri_ayanamsa(jd_birth)
        
        asc_deg, _, _ = vedic_engine.calculate_ascendant_and_mc(jd_birth, latitude, longitude, ayanamsa_natal)
        asc_sign_idx = int(asc_deg // 30) + 1
        
        natal_planets_raw = vedic_engine.get_planet_longitudes_precise(jd_birth, ayanamsa_natal)
        
        # Format natal chart snapshot
        natal_snapshot = []
        for name, (deg, speed, is_ret) in natal_planets_raw.items():
            s_idx, s_name, _, deg_in_sign = vedic_engine.degree_to_sign_and_dms(deg)
            house = ((s_idx - asc_sign_idx) % 12) + 1
            natal_snapshot.append({
                "planet": name,
                "sign": s_name,
                "house": house,
                "degree": deg_in_sign
            })

        # 2. Calculate Current Transits
        current_dt = datetime.now(dt_timezone.utc)
        jd_now = vedic_engine.calculate_julian_day(current_dt.year, current_dt.month, current_dt.day, current_dt.hour + current_dt.minute/60.0)
        ayanamsa_now = vedic_engine.calculate_lahiri_ayanamsa(jd_now)
        
        transit_planets_raw = vedic_engine.get_planet_longitudes_precise(jd_now, ayanamsa_now)
        
        transit_snapshot = []
        for name, (deg, speed, is_ret) in transit_planets_raw.items():
            s_idx, s_name, _, deg_in_sign = vedic_engine.degree_to_sign_and_dms(deg)
            transit_snapshot.append({
                "planet": name,
                "sign": s_name,
                "degree": deg_in_sign
            })
            
        # 3. Draw Tarot (e.g. 5 card spread for Astro-Tarot)
        tarot_spread = TarotEngine.create_spread("love_five_card" if "love" in question.lower() else "career_five_card", seed)

        # 4. Integrate correspondences
        # For each card in the spread, link its astrological correspondence with current transit data
        for pos in tarot_spread["positions"]:
            astro_corr = pos["card"].get("astrology_correspondence")
            if astro_corr:
                # Find transit position of this correspondence
                transit_match = next((t for t in transit_snapshot if t["planet"] == astro_corr or t["sign"] == astro_corr), None)
                natal_match = next((n for n in natal_snapshot if n["planet"] == astro_corr or n["sign"] == astro_corr), None)
                
                pos["astro_context"] = {
                    "correspondence": astro_corr,
                    "current_transit": transit_match,
                    "natal_placement": natal_match
                }

        return {
            "natal_snapshot": natal_snapshot,
            "transit_snapshot": transit_snapshot,
            "tarot_spread": tarot_spread
        }
