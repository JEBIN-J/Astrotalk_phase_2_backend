import swisseph as swe
from datetime import datetime, timedelta
import math

class MuhuratEngine:
    def __init__(self, lat=28.6139, lon=77.2090, tz=5.5):
        self.lat = lat
        self.lon = lon
        self.tz = tz
        self.geopos = (lon, lat, 0.0)
        
        # Astrological Constants
        self.PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
        self.VARA_LORDS = [1, 2, 3, 4, 5, 6, 0] # Monday=1 (Moon), Tuesday=2 (Mars)... Sunday=0 (Sun) - using 0=Sun, 1=Moon for Hora math
        # Actually standard mapping for weekday(): 0=Monday(Moon), 1=Tuesday(Mars), 2=Wednesday(Mercury), 3=Thursday(Jupiter), 4=Friday(Venus), 5=Saturday(Saturn), 6=Sunday(Sun)
        self.WEEKDAY_TO_HORA_PLANET = {
            0: "Moon", 1: "Mars", 2: "Mercury", 3: "Jupiter", 4: "Venus", 5: "Saturn", 6: "Sun"
        }
        
        self.NAKSHATRAS = [
            "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
            "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
            "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
            "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
            "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
        ]
        
        self.YOGAS = [
            "Vishkumbha", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda",
            "Sukarma", "Dhriti", "Shula", "Ganda", "Vriddhi", "Dhruva", "Vyaghata",
            "Harshana", "Vajra", "Siddhi", "Vyatipata", "Variyana", "Parigha",
            "Shiva", "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma", "Indra", "Vaidhriti"
        ]
        
        self.KARANAS = [
            "Bava", "Balava", "Kaulava", "Taitila", "Garaja", "Vanija", "Vishti",
            "Shakuni", "Chatushpada", "Naga", "Kimstughna"
        ]
        
        self.CHOGHADIYA_NAMES = ["Udveg", "Chal", "Labh", "Amrit", "Kaal", "Shubh", "Rog"]
        # Day Choghadiya starting sequence based on weekday (0=Mon, 6=Sun)
        self.DAY_CHOGHADIYA_START = {
            6: 0, # Sunday: Udveg
            0: 3, # Monday: Amrit
            1: 6, # Tuesday: Rog
            2: 2, # Wednesday: Labh
            3: 5, # Thursday: Shubh
            4: 1, # Friday: Chal
            5: 4  # Saturday: Kaal
        }
        self.NIGHT_CHOGHADIYA_START = {
            6: 5, # Sunday night starts with Shubh
            0: 1, # Monday night starts with Chal
            1: 4, # Tuesday night starts with Kaal
            2: 0, # Wednesday night starts with Udveg
            3: 3, # Thursday night starts with Amrit
            4: 6, # Friday night starts with Rog
            5: 2  # Saturday night starts with Labh
        }
        
    def _jd_to_time_str(self, jd):
        """Convert Julian Day to localized 12-hour AM/PM string"""
        y, m, d, h = swe.revjul(jd + (self.tz / 24.0), swe.GREG_CAL)
        hours = int(h)
        minutes = int(round((h - hours) * 60))
        if minutes == 60:
            minutes = 0
            hours += 1
        if hours >= 24:
            hours -= 24
        ampm = "AM" if hours < 12 else "PM"
        h12 = hours if 0 < hours <= 12 else (12 if hours == 0 else hours - 12)
        return f"{h12:02d}:{minutes:02d} {ampm}"
        
    def get_full_muhurat(self, date_str):
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        jd_ut = swe.julday(dt.year, dt.month, dt.day, 0.0)
        
        # 1. Sunrise and Sunset
        res_rise = swe.rise_trans(jd_ut, swe.SUN, swe.CALC_RISE, self.geopos)
        res_set = swe.rise_trans(jd_ut, swe.SUN, swe.CALC_SET, self.geopos)
        next_rise = swe.rise_trans(jd_ut + 1, swe.SUN, swe.CALC_RISE, self.geopos)
        
        rise_jd = res_rise[1][0]
        set_jd = res_set[1][0]
        next_rise_jd = next_rise[1][0]
        
        sunrise_str = self._jd_to_time_str(rise_jd)
        sunset_str = self._jd_to_time_str(set_jd)
        
        # 2. Panchanga Calculation (at Sunrise)
        sun_lon = swe.calc_ut(rise_jd, swe.SUN)[0][0]
        moon_lon = swe.calc_ut(rise_jd, swe.MOON)[0][0]
        
        # Tithi
        tithi_val = (moon_lon - sun_lon) % 360
        tithi_index = int(tithi_val / 12.0)
        tithi_paksha = "Shukla" if tithi_index < 15 else "Krishna"
        tithi_num = tithi_index % 15 + 1
        tithi_name = f"{tithi_paksha} {tithi_num}"
        if tithi_index == 14: tithi_name = "Purnima"
        if tithi_index == 29: tithi_name = "Amavasya"
        
        # Nakshatra
        nak_index = int((moon_lon % 360) / (360.0 / 27.0))
        nak_name = self.NAKSHATRAS[nak_index]
        
        # Yoga
        yoga_val = (sun_lon + moon_lon) % 360
        yoga_index = int(yoga_val / (360.0 / 27.0))
        yoga_name = self.YOGAS[yoga_index]
        
        # Karana
        karana_index = int(tithi_val / 6.0)
        karana_name = self.KARANAS[(karana_index % 7) + 1] if karana_index != 0 and karana_index != 57 and karana_index != 58 and karana_index != 59 else "Vishti"
        # simplified karana for now
        
        # Vara
        weekday = dt.weekday()
        vara_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        vara_name = vara_names[weekday]
        
        panchanga = {
            "vara": vara_name,
            "tithi": tithi_name,
            "nakshatra": nak_name,
            "yoga": yoga_name,
            "karana": karana_name
        }
        
        # 3. Inauspicious & Auspicious Periods (Rahu, Yama, Gulika, Abhijit)
        daylight = set_jd - rise_jd
        part_8 = daylight / 8.0
        part_15 = daylight / 15.0
        
        abhijit_start = rise_jd + 7 * part_15
        abhijit_end = rise_jd + 8 * part_15
        
        rahu_parts = {0: 2, 1: 7, 2: 5, 3: 6, 4: 4, 5: 3, 6: 8}
        yama_parts = {0: 4, 1: 3, 2: 2, 3: 1, 4: 7, 5: 6, 6: 5}
        guli_parts = {0: 6, 1: 5, 2: 4, 3: 3, 4: 2, 5: 1, 6: 7}
        
        def get_slot(part_num):
            s = rise_jd + (part_num - 1) * part_8
            e = rise_jd + part_num * part_8
            return {"start": self._jd_to_time_str(s), "end": self._jd_to_time_str(e)}
            
        general_timings = {
            "abhijit": {"start": self._jd_to_time_str(abhijit_start), "end": self._jd_to_time_str(abhijit_end)},
            "rahu": get_slot(rahu_parts[weekday]),
            "yama": get_slot(yama_parts[weekday]),
            "gulika": get_slot(guli_parts[weekday])
        }
        
        # 4. Choghadiya
        choghadiya_list = []
        day_chog_len = daylight / 8.0
        night_len = next_rise_jd - set_jd
        night_chog_len = night_len / 8.0
        
        start_idx_day = self.DAY_CHOGHADIYA_START[weekday]
        for i in range(8):
            chog_name = self.CHOGHADIYA_NAMES[(start_idx_day + i) % 7]
            t_start = rise_jd + i * day_chog_len
            t_end = rise_jd + (i + 1) * day_chog_len
            is_auspicious = chog_name in ["Amrit", "Shubh", "Labh"]
            choghadiya_list.append({
                "time": f"{self._jd_to_time_str(t_start)} - {self._jd_to_time_str(t_end)}",
                "name": chog_name,
                "type": "Day",
                "is_auspicious": is_auspicious
            })
            
        start_idx_night = self.NIGHT_CHOGHADIYA_START[weekday]
        for i in range(8):
            chog_name = self.CHOGHADIYA_NAMES[(start_idx_night + i) % 7]
            t_start = set_jd + i * night_chog_len
            t_end = set_jd + (i + 1) * night_chog_len
            is_auspicious = chog_name in ["Amrit", "Shubh", "Labh"]
            choghadiya_list.append({
                "time": f"{self._jd_to_time_str(t_start)} - {self._jd_to_time_str(t_end)}",
                "name": chog_name,
                "type": "Night",
                "is_auspicious": is_auspicious
            })
            
        # 5. Hora
        hora_list = []
        hora_order = ["Sun", "Venus", "Mercury", "Moon", "Saturn", "Jupiter", "Mars"]
        day_hora_len = daylight / 12.0
        night_hora_len = night_len / 12.0
        
        start_planet = self.WEEKDAY_TO_HORA_PLANET[weekday]
        start_idx = hora_order.index(start_planet)
        
        for i in range(12):
            p = hora_order[(start_idx + i) % 7]
            t_start = rise_jd + i * day_hora_len
            t_end = rise_jd + (i + 1) * day_hora_len
            hora_list.append({"time": f"{self._jd_to_time_str(t_start)} - {self._jd_to_time_str(t_end)}", "planet": p, "type": "Day"})
            
        start_idx_night = (start_idx + 12) % 7
        for i in range(12):
            p = hora_order[(start_idx_night + i) % 7]
            t_start = set_jd + i * night_hora_len
            t_end = set_jd + (i + 1) * night_hora_len
            hora_list.append({"time": f"{self._jd_to_time_str(t_start)} - {self._jd_to_time_str(t_end)}", "planet": p, "type": "Night"})

        # 6. Specific Categories
        categories = self._calculate_specific_categories(tithi_index, nak_index, yoga_index, rise_jd, day_chog_len)
        
        # Is Auspicious Overall
        overall = tithi_index not in [3, 8, 13, 14, 29] and nak_index not in [8, 9, 10]
        
        return {
            "date": date_str,
            "is_today": date_str == datetime.now().strftime("%Y-%m-%d"),
            "sunrise": sunrise_str,
            "sunset": sunset_str,
            "is_auspicious": overall,
            "panchanga": panchanga,
            "general_timings": general_timings,
            "choghadiya": choghadiya_list,
            "hora": hora_list,
            "categories": categories
        }
        
    def _calculate_specific_categories(self, tithi_index, nak_index, yoga_index, rise_jd, day_chog_len):
        categories = [
            {"name": "Financial Investment", "tithi_avoid": [3, 8, 13], "nak_good": [3, 4, 7, 13, 21, 22]},
            {"name": "Marriage", "tithi_avoid": [3, 8, 13, 14, 29], "nak_good": [3, 4, 10, 11, 14, 20]},
            {"name": "House Construction", "tithi_avoid": [3, 8, 13, 29], "nak_good": [3, 4, 7, 11, 13, 22]},
            {"name": "Starting Education", "tithi_avoid": [3, 8, 13, 14, 29], "nak_good": [0, 4, 5, 7, 12, 13, 14]},
            {"name": "Travel", "tithi_avoid": [5, 10, 15], "nak_good": [0, 4, 6, 7, 12, 13, 14, 16]},
            {"name": "Starting Business", "tithi_avoid": [3, 8, 13, 29], "nak_good": [0, 3, 4, 7, 13, 14, 21]}
        ]
        
        results = []
        for cat in categories:
            score = 3 # base Average
            reason = "A moderate day for this activity."
            
            if tithi_index in cat["tithi_avoid"]:
                score -= 2
                reason = "Inauspicious Tithi (Rikta/Amavasya) for this specific activity."
            elif tithi_index < 15:
                score += 1 # Shukla Paksha
                reason = "Shukla Paksha is generally favorable."
                
            if nak_index in cat["nak_good"]:
                score += 1
                reason = f"The current Nakshatra ({self.NAKSHATRAS[nak_index]}) is highly auspicious for {cat['name']}."
            elif nak_index in [8, 9, 10]:
                score -= 1
                reason = "Harsh Nakshatra active today, use caution."
                
            # Clamp score
            score = max(1, min(5, score))
            
            status = "AVERAGE"
            if score >= 4: status = "GOOD"
            if score <= 2: status = "AVOID"
            
            # Select a favorable/unfavorable time slot deterministically
            slot_idx = (len(cat['name']) + tithi_index + nak_index) % 6 + 1
            t_s = rise_jd + slot_idx * day_chog_len
            t_e = rise_jd + (slot_idx + 1) * day_chog_len
            
            results.append({
                "category": cat["name"],
                "status": status,
                "rating": score,
                "time": f"{self._jd_to_time_str(t_s)} - {self._jd_to_time_str(t_e)}",
                "reason": reason
            })
            
        return results
