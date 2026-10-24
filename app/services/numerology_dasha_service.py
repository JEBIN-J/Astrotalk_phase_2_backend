from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional

class NumerologyDashaService:
    PLANET_INFO = {
        1: {
            "planet": "Sun",
            "vedic_name": "Surya",
            "color": "Gold / Deep Orange",
            "gemstone": "Ruby (Manik)",
            "direction": "East",
            "element": "Fire",
            "favorable_days": ["Sunday"],
            "friendly_numbers": [1, 2, 3, 9],
            "neutral_numbers": [5],
            "enemy_numbers": [4, 6, 7, 8],
            "theme": "Leadership, vitality, executive decisions, government & fatherly guidance."
        },
        2: {
            "planet": "Moon",
            "vedic_name": "Chandra",
            "color": "Pearl White / Silver",
            "gemstone": "Pearl (Moti)",
            "direction": "North-West",
            "element": "Water",
            "favorable_days": ["Monday"],
            "friendly_numbers": [1, 2, 3, 4, 7],
            "neutral_numbers": [5, 6],
            "enemy_numbers": [8, 9],
            "theme": "Intuition, empathy, public diplomacy, artistic creativity & emotional balance."
        },
        3: {
            "planet": "Jupiter",
            "vedic_name": "Guru",
            "color": "Bright Yellow / Golden",
            "gemstone": "Yellow Sapphire (Pukhraj)",
            "direction": "North-East",
            "element": "Ether",
            "favorable_days": ["Thursday"],
            "friendly_numbers": [1, 2, 3, 9],
            "neutral_numbers": [5],
            "enemy_numbers": [4, 6, 7, 8],
            "theme": "Higher wisdom, mentorship, financial wealth, expansion & ethics."
        },
        4: {
            "planet": "Rahu",
            "vedic_name": "North Node",
            "color": "Electric Blue / Smoke Grey",
            "gemstone": "Hessonite (Gomed)",
            "direction": "South-West",
            "element": "Air",
            "favorable_days": ["Saturday", "Wednesday"],
            "friendly_numbers": [1, 4, 6, 8],
            "neutral_numbers": [5, 7],
            "enemy_numbers": [2, 9],
            "theme": "Technological innovation, sudden breakthroughs, unorthodox strategies & material ambition."
        },
        5: {
            "planet": "Mercury",
            "vedic_name": "Budha",
            "color": "Emerald Green",
            "gemstone": "Emerald (Panna)",
            "direction": "North",
            "element": "Earth",
            "favorable_days": ["Wednesday"],
            "friendly_numbers": [1, 5, 6],
            "neutral_numbers": [2, 3, 4, 7, 8],
            "enemy_numbers": [9],
            "theme": "Commercial commerce, intellectual dexterity, communication, speech & networking."
        },
        6: {
            "planet": "Venus",
            "vedic_name": "Shukra",
            "color": "Diamond White / Pastel Pink",
            "gemstone": "Diamond (Heera) / White Zircon",
            "direction": "South-East",
            "element": "Water",
            "favorable_days": ["Friday"],
            "friendly_numbers": [4, 5, 6, 8],
            "neutral_numbers": [2, 3, 7],
            "enemy_numbers": [1, 9],
            "theme": "Harmony, romantic allure, architectural beauty, diplomatic grace & luxuries."
        },
        7: {
            "planet": "Ketu",
            "vedic_name": "South Node",
            "color": "Smoky Grey / Light Brown",
            "gemstone": "Cat's Eye (Lehsuniya)",
            "direction": "North-East / South-West",
            "element": "Fire/Water",
            "favorable_days": ["Tuesday", "Thursday"],
            "friendly_numbers": [1, 2, 7],
            "neutral_numbers": [3, 5, 6],
            "enemy_numbers": [4, 8, 9],
            "theme": "Introspection, analytical discernment, spiritual liberation, esoteric insights & deep research."
        },
        8: {
            "planet": "Saturn",
            "vedic_name": "Shani",
            "color": "Deep Blue / Charcoal Black",
            "gemstone": "Blue Sapphire (Neelam)",
            "direction": "West",
            "element": "Air",
            "favorable_days": ["Saturday"],
            "friendly_numbers": [4, 5, 6, 8],
            "neutral_numbers": [3, 7],
            "enemy_numbers": [1, 2, 9],
            "theme": "Enduring perseverance, structural discipline, karmic justice, long-term mastery & caution."
        },
        9: {
            "planet": "Mars",
            "vedic_name": "Mangal",
            "color": "Crimson Red / Coral",
            "gemstone": "Red Coral (Moonga)",
            "direction": "South",
            "element": "Fire",
            "favorable_days": ["Tuesday"],
            "friendly_numbers": [1, 2, 3, 9],
            "neutral_numbers": [5, 6],
            "enemy_numbers": [4, 7, 8],
            "theme": "Courageous vigor, decisive execution, protective prowess, passion & mechanical engineering."
        }
    }

    # Python weekday (0=Monday, 6=Sunday) to Vedic weekday numerology number
    VEDIC_WEEKDAY_MAP = {
        6: 1,  # Sunday -> Sun (1)
        0: 2,  # Monday -> Moon (2)
        1: 9,  # Tuesday -> Mars (9)
        2: 5,  # Wednesday -> Mercury (5)
        3: 3,  # Thursday -> Jupiter (3)
        4: 6,  # Friday -> Venus (6)
        5: 8,  # Saturday -> Saturn (8)
    }

    WEEKDAY_NAMES = {
        6: "Sunday",
        0: "Monday",
        1: "Tuesday",
        2: "Wednesday",
        3: "Thursday",
        4: "Friday",
        5: "Saturday",
    }

    # Classical 365-day Pratantardasha distribution
    PD_DURATIONS = {
        1: 8,   # Sun
        2: 16,  # Moon
        3: 24,  # Jupiter
        4: 32,  # Rahu
        5: 41,  # Mercury
        6: 49,  # Venus
        7: 57,  # Ketu
        8: 65,  # Saturn
        9: 73   # Mars
    }

    @staticmethod
    def reduce_to_single_digit(num: int) -> tuple[int, List[int]]:
        steps = [num]
        val = abs(num)
        while val > 9:
            val = sum(int(ch) for ch in str(val))
            steps.append(val)
        return val, steps

    @staticmethod
    def parse_date(date_str: str) -> date:
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y"):
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except (ValueError, TypeError):
                continue
        raise ValueError(f"Invalid date format: {date_str}. Expected YYYY-MM-DD")

    @classmethod
    def calculate_basic_info(cls, name: str, dob_str: str, system: str = "pythagorean") -> Dict[str, Any]:
        dt = cls.parse_date(dob_str)
        day = dt.day
        month = dt.month
        year = dt.year

        # Basic Number (Mulank)
        basic_num, basic_steps = cls.reduce_to_single_digit(day)
        basic_planet = cls.PLANET_INFO.get(basic_num, {})

        # Supportive Number:
        # In Vedic/Indian numerology tradition, Supportive Number represents the Month reduction
        # (or the primary harmonious companion number to Mulank)
        supportive_num, supportive_steps = cls.reduce_to_single_digit(month)
        supportive_planet = cls.PLANET_INFO.get(supportive_num, {})

        # Destiny Number (Bhagyank / Life Path)
        # Sum of all digits of full DOB
        dob_digits_sum = sum(int(ch) for ch in f"{year:04d}{month:02d}{day:02d}")
        destiny_num, destiny_steps = cls.reduce_to_single_digit(dob_digits_sum)
        destiny_planet = cls.PLANET_INFO.get(destiny_num, {})

        # Name Number (Namank)
        system_lower = system.lower()
        if "chaldean" in system_lower:
            map_to_use = {
                'a':1,'i':1,'j':1,'q':1,'y':1, 'b':2,'k':2,'r':2,
                'c':3,'g':3,'l':3,'s':3, 'd':4,'m':4,'t':4,
                'e':5,'h':5,'n':5,'x':5, 'u':6,'v':6,'w':6,
                'o':7,'z':7, 'f':8,'p':8
            }
            method_label = "Chaldean Numerology (Ancient Vedic)"
        else:
            map_to_use = {
                'a':1,'j':1,'s':1, 'b':2,'k':2,'t':2, 'c':3,'l':3,'u':3,
                'd':4,'m':4,'v':4, 'e':5,'n':5,'w':5, 'f':6,'o':6,'x':6,
                'g':7,'p':7,'y':7, 'h':8,'q':8,'z':8, 'i':9,'r':9
            }
            method_label = "Pythagorean Numerology (Modern)"

        name_sum = 0
        name_breakdown = []
        for word in name.split():
            w_sum = 0
            chars = []
            for c in word.lower():
                if c in map_to_use:
                    v = map_to_use[c]
                    w_sum += v
                    chars.append({"char": c.upper(), "val": v})
            name_sum += w_sum
            name_breakdown.append({"word": word, "subtotal": w_sum, "letters": chars})

        name_num, name_steps = cls.reduce_to_single_digit(name_sum if name_sum > 0 else 1)

        # Transparency breakdown
        transparency = {
            "method_name": method_label,
            "inputs": {
                "name": name,
                "dob": dt.strftime("%Y-%m-%d"),
                "day": day,
                "month": month,
                "year": year
            },
            "basic_number_formula": f"Sum digits of birth day ({day}): {' -> '.join(str(s) for s in basic_steps)}",
            "supportive_number_formula": f"Sum digits of birth month ({month}): {' -> '.join(str(s) for s in supportive_steps)}",
            "destiny_number_formula": f"Sum all digits of {dt.strftime('%d-%m-%Y')} = {dob_digits_sum}: {' -> '.join(str(s) for s in destiny_steps)}",
            "name_number_formula": f"Sum of {method_label} letter values ({name_sum}): {' -> '.join(str(s) for s in name_steps)}"
        }

        return {
            "name": name,
            "dob": dt.strftime("%Y-%m-%d"),
            "system": system,
            "system_label": method_label,
            "basic_number": {
                "number": basic_num,
                "planet": basic_planet.get("planet"),
                "vedic_name": basic_planet.get("vedic_name"),
                "raw_day": day,
                "reduction_steps": basic_steps,
                "theme": basic_planet.get("theme")
            },
            "supportive_number": {
                "number": supportive_num,
                "planet": supportive_planet.get("planet"),
                "vedic_name": supportive_planet.get("vedic_name"),
                "raw_month": month,
                "reduction_steps": supportive_steps,
                "friendly_companions": basic_planet.get("friendly_numbers", []),
                "theme": supportive_planet.get("theme")
            },
            "destiny_number": {
                "number": destiny_num,
                "planet": destiny_planet.get("planet"),
                "vedic_name": destiny_planet.get("vedic_name"),
                "raw_sum": dob_digits_sum,
                "reduction_steps": destiny_steps,
                "theme": destiny_planet.get("theme")
            },
            "name_number": {
                "number": name_num,
                "planet": cls.PLANET_INFO.get(name_num, {}).get("planet"),
                "raw_sum": name_sum,
                "reduction_steps": name_steps,
                "breakdown": name_breakdown
            },
            "lucky_attributes": {
                "lucky_numbers": basic_planet.get("friendly_numbers", []),
                "neutral_numbers": basic_planet.get("neutral_numbers", []),
                "unfavorable_numbers": basic_planet.get("enemy_numbers", []),
                "lucky_color": basic_planet.get("color"),
                "lucky_gemstone": basic_planet.get("gemstone"),
                "lucky_direction": basic_planet.get("direction"),
                "lucky_element": basic_planet.get("element"),
                "favorable_days": basic_planet.get("favorable_days", [])
            },
            "transparency": transparency
        }

    @classmethod
    def calculate_mahadashas(cls, dob_str: str, ref_date_str: Optional[str] = None, max_years: int = 100) -> List[Dict[str, Any]]:
        dob = cls.parse_date(dob_str)
        ref_date = cls.parse_date(ref_date_str) if ref_date_str else date.today()

        basic_num, _ = cls.reduce_to_single_digit(dob.day)
        
        # Sequence cycles: basic_num, basic_num+1, ..., 9, 1, ..., with duration equal to number
        mahadashas = []
        cur_start = dob
        cur_num = basic_num
        period_idx = 1

        while (cur_start.year - dob.year) < max_years:
            dur_years = cur_num
            # Add dur_years keeping day/month
            try:
                cur_end = cur_start.replace(year=cur_start.year + dur_years)
            except ValueError:
                # Leap year edge case (Feb 29)
                cur_end = cur_start.replace(year=cur_start.year + dur_years, day=28)

            is_active = (cur_start <= ref_date < cur_end)
            status = "Active" if is_active else ("Completed" if ref_date >= cur_end else "Upcoming")

            p_info = cls.PLANET_INFO.get(cur_num, {})
            mahadashas.append({
                "period_index": period_idx,
                "dasha_number": cur_num,
                "lord": p_info.get("planet"),
                "vedic_name": p_info.get("vedic_name"),
                "duration_years": dur_years,
                "age_start": cur_start.year - dob.year,
                "age_end": cur_end.year - dob.year,
                "start_date": cur_start.strftime("%Y-%m-%d"),
                "end_date": cur_end.strftime("%Y-%m-%d"),
                "formatted_span": f"{cur_start.strftime('%d %b %Y')} - {cur_end.strftime('%d %b %Y')}",
                "is_active": is_active,
                "status": status,
                "theme": p_info.get("theme")
            })

            cur_start = cur_end
            cur_num = (cur_num % 9) + 1
            period_idx += 1

        return mahadashas

    @classmethod
    def calculate_antardashas(
        cls,
        dob_str: str,
        ref_date_str: Optional[str] = None,
        past_years: Optional[int] = None,
        future_years: Optional[int] = None,
        start_from_birth: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Calculates annual Antardashas from birthday to birthday.
        Starts from the user's birth year by default to align with the complete lifetime Mahadasha progression.
        Formula: (Reduced Day + Month + Reduced Year 2-digits + Birthday Weekday) mod 9 (or 9)
        """
        dob = cls.parse_date(dob_str)
        ref_date = cls.parse_date(ref_date_str) if ref_date_str else date.today()

        # Find native current age/year
        # Birthday in current reference year
        try:
            this_year_bday = dob.replace(year=ref_date.year)
        except ValueError:
            this_year_bday = dob.replace(year=ref_date.year, day=28)

        base_year = ref_date.year if ref_date >= this_year_bday else ref_date.year - 1

        if past_years is not None and not start_from_birth:
            start_year = max(dob.year, base_year - past_years)
        else:
            # Starts from user-entered birth values
            start_year = dob.year

        if future_years is not None and not start_from_birth:
            end_year = base_year + future_years
        else:
            # Complete 100-year lifetime progression matching Mahadasha
            end_year = dob.year + 100

        mahadashas = cls.calculate_mahadashas(dob_str, ref_date_str, max_years=120)
        reduced_day, _ = cls.reduce_to_single_digit(dob.day)

        antardashas = []
        for y in range(start_year, end_year + 1):
            try:
                bday_start = dob.replace(year=y)
                bday_end = dob.replace(year=y + 1)
            except ValueError:
                bday_start = dob.replace(year=y, day=28)
                bday_end = dob.replace(year=y + 1, day=28)

            weekday_idx = bday_start.weekday()
            weekday_val = cls.VEDIC_WEEKDAY_MAP[weekday_idx]
            weekday_name = cls.WEEKDAY_NAMES[weekday_idx]

            last2 = y % 100
            reduced_y2, _ = cls.reduce_to_single_digit(last2)

            sum_vals = reduced_day + dob.month + reduced_y2 + weekday_val
            ad_num = sum_vals % 9
            if ad_num == 0:
                ad_num = 9

            is_active = (bday_start <= ref_date < bday_end)
            status = "Active" if is_active else ("Completed" if ref_date >= bday_end else "Upcoming")

            # Find parent Mahadasha
            parent_md = next((m for m in mahadashas if cls.parse_date(m["start_date"]) <= bday_start < cls.parse_date(m["end_date"])), None)
            parent_num = parent_md["dasha_number"] if parent_md else 1
            parent_lord = parent_md["lord"] if parent_md else "Sun"

            ad_info = cls.PLANET_INFO.get(ad_num, {})
            antardashas.append({
                "cycle_year": y,
                "parent_dasha": parent_num,
                "parent_lord": parent_lord,
                "antardasha_number": ad_num,
                "lord": ad_info.get("planet"),
                "vedic_name": ad_info.get("vedic_name"),
                "start_date": bday_start.strftime("%Y-%m-%d"),
                "end_date": bday_end.strftime("%Y-%m-%d"),
                "formatted_span": f"{bday_start.strftime('%d %b %Y')} - {bday_end.strftime('%d %b %Y')}",
                "birthday_weekday": weekday_name,
                "weekday_value": weekday_val,
                "calculation_steps": f"{reduced_day} (Day) + {dob.month} (Month) + {reduced_y2} ('{last2:02d}) + {weekday_val} ({weekday_name}) = {sum_vals} -> {ad_num}",
                "is_active": is_active,
                "status": status,
                "theme": ad_info.get("theme")
            })

        return antardashas

    @classmethod
    def calculate_paryantardashas(cls, dob_str: str, antardasha_year: Optional[int] = None, ref_date_str: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Divides the selected (or active) annual Antardasha into 9 Pratantardashas (Paryantardashas)
        totaling 365 days according to the classical Vedic duration table.
        """
        dob = cls.parse_date(dob_str)
        ref_date = cls.parse_date(ref_date_str) if ref_date_str else date.today()

        req_past = 10
        req_future = 25
        if antardasha_year is not None:
            if antardasha_year < ref_date.year:
                req_past = max(req_past, ref_date.year - antardasha_year + 5)
            else:
                req_future = max(req_future, antardasha_year - ref_date.year + 5)

        all_ads = cls.calculate_antardashas(dob_str, ref_date_str, past_years=req_past, future_years=req_future)

        target_ad = None
        if antardasha_year is not None:
            target_ad = next((ad for ad in all_ads if ad["cycle_year"] == antardasha_year), None)
        
        if not target_ad:
            target_ad = next((ad for ad in all_ads if ad["is_active"]), all_ads[0] if all_ads else None)

        if not target_ad:
            return []

        ad_num = target_ad["antardasha_number"]
        ad_start = cls.parse_date(target_ad["start_date"])
        ad_end = cls.parse_date(target_ad["end_date"])
        total_span_days = (ad_end - ad_start).days  # 365 or 366 (leap year)

        paryantardashas = []
        cur_start = ad_start

        for step in range(9):
            pd_num = (ad_num - 1 + step) % 9 + 1
            dur = cls.PD_DURATIONS[pd_num]
            
            # If leap year, distribute the 1 extra day to the final period
            if step == 8 and total_span_days > 365:
                dur += (total_span_days - 365)

            cur_end = cur_start + timedelta(days=dur)
            # Ensure adjacent continuity
            if step == 8:
                cur_end = ad_end

            is_active = (cur_start <= ref_date < cur_end)
            status = "Active" if is_active else ("Completed" if ref_date >= cur_end else "Upcoming")

            p_info = cls.PLANET_INFO.get(pd_num, {})
            paryantardashas.append({
                "step_index": step + 1,
                "parent_dasha": target_ad["parent_dasha"],
                "parent_lord": target_ad["parent_lord"],
                "antardasha": ad_num,
                "antardasha_lord": target_ad["lord"],
                "paryantardasha_number": pd_num,
                "lord": p_info.get("planet"),
                "vedic_name": p_info.get("vedic_name"),
                "duration_days": (cur_end - cur_start).days,
                "start_date": cur_start.strftime("%Y-%m-%d"),
                "end_date": cur_end.strftime("%Y-%m-%d"),
                "formatted_span": f"{cur_start.strftime('%d %b %Y')} - {cur_end.strftime('%d %b %Y')}",
                "is_active": is_active,
                "status": status,
                "theme": p_info.get("theme")
            })

            cur_start = cur_end

        return paryantardashas

    @classmethod
    def calculate_daily_dashas(cls, dob_str: str, center_date_str: Optional[str] = None, days_span: int = 14) -> List[Dict[str, Any]]:
        """
        Calculates Daily Dasha for each date in a window around center_date (default +/- 7 days = 14 days).
        Formula: (Active Pratantardasha + Weekday Value) mod 9 (or 9)
        """
        dob = cls.parse_date(dob_str)
        center_date = cls.parse_date(center_date_str) if center_date_str else date.today()
        today = date.today()

        start_date = center_date - timedelta(days=days_span // 2)
        end_date = start_date + timedelta(days=days_span)

        daily_list = []
        cur_d = start_date

        while cur_d <= end_date:
            # Find active Pratantardasha for cur_d
            pds = cls.calculate_paryantardashas(dob_str, antardasha_year=None, ref_date_str=cur_d.strftime("%Y-%m-%d"))
            active_pd = next((p for p in pds if p["is_active"]), (pds[0] if pds else None))

            pd_num = active_pd["paryantardasha_number"] if active_pd else 1
            pd_lord = active_pd["lord"] if active_pd else "Sun"

            w_idx = cur_d.weekday()
            w_val = cls.VEDIC_WEEKDAY_MAP[w_idx]
            w_name = cls.WEEKDAY_NAMES[w_idx]
            w_lord = cls.PLANET_INFO[w_val]["planet"]

            dd_num = (pd_num + w_val) % 9
            if dd_num == 0:
                dd_num = 9

            dd_info = cls.PLANET_INFO.get(dd_num, {})
            is_today = (cur_d == today)
            is_selected = (cur_d == center_date)

            daily_list.append({
                "date": cur_d.strftime("%Y-%m-%d"),
                "formatted_date": cur_d.strftime("%d %b %Y"),
                "weekday": w_name,
                "weekday_value": w_val,
                "weekday_lord": w_lord,
                "active_dasha": active_pd["parent_dasha"] if active_pd else 1,
                "active_antardasha": active_pd["antardasha"] if active_pd else 1,
                "active_paryantardasha": pd_num,
                "active_paryantardasha_lord": pd_lord,
                "daily_dasha_number": dd_num,
                "lord": dd_info.get("planet"),
                "vedic_name": dd_info.get("vedic_name"),
                "calculation_formula": f"{pd_num} (PD {pd_lord}) + {w_val} ({w_name} / {w_lord}) = {pd_num + w_val} -> {dd_num}",
                "is_today": is_today,
                "is_selected": is_selected,
                "explanation": f"Combines {pd_lord} micro-period energy with {w_lord} weekday impulse. {dd_info.get('theme')}"
            })

            cur_d += timedelta(days=1)

        return daily_list

    @classmethod
    def get_full_workspace(cls, name: str, dob_str: str, system: str = "pythagorean", ref_date_str: Optional[str] = None) -> Dict[str, Any]:
        ref_date = cls.parse_date(ref_date_str) if ref_date_str else date.today()

        basic_info = cls.calculate_basic_info(name, dob_str, system)
        mahadashas = cls.calculate_mahadashas(dob_str, ref_date_str=ref_date.strftime("%Y-%m-%d"))
        antardashas = cls.calculate_antardashas(dob_str, ref_date_str=ref_date.strftime("%Y-%m-%d"))
        paryantardashas = cls.calculate_paryantardashas(dob_str, ref_date_str=ref_date.strftime("%Y-%m-%d"))
        daily_dashas = cls.calculate_daily_dashas(dob_str, center_date_str=ref_date.strftime("%Y-%m-%d"), days_span=14)

        active_md = next((m for m in mahadashas if m["is_active"]), None)
        active_ad = next((a for a in antardashas if a["is_active"]), None)
        active_pd = next((p for p in paryantardashas if p["is_active"]), None)
        active_dd = next((d for d in daily_dashas if d["is_selected"] or d["is_today"]), None)

        return {
            "status": "success",
            "reference_date": ref_date.strftime("%Y-%m-%d"),
            "basic_info": basic_info,
            "active_summary": {
                "mahadasha": active_md,
                "antardasha": active_ad,
                "paryantardasha": active_pd,
                "daily_dasha": active_dd
            },
            "mahadashas": mahadashas,
            "antardashas": antardashas,
            "paryantardashas": paryantardashas,
            "daily_dashas": daily_dashas,
            "methodology": {
                "version": "1.0.0",
                "authority": "Classical Vedic Ank Jyotish (Ank Dasha & Navagraha Progression)",
                "rules": {
                    "basic_number": "Single-digit digital root of day of birth (1..9)",
                    "supportive_number": "Single-digit digital root of month of birth (1..9) and friendly harmonic companions",
                    "destiny_number": "Single-digit digital root of full DOB digits (1..9)",
                    "mahadasha_progression": "Cyclic 45-year progression starting from Mulank, duration = planetary number in years",
                    "antardasha_annual": "(Reduced Day + Month + Reduced 2-digit Year + Birthday Weekday) mod 9",
                    "paryantardasha_subdivision": "9 sequential micro-periods starting with Antardasha ruler totaling 365 solar days",
                    "daily_dasha": "(Active Pratantardasha + Current Weekday) mod 9"
                }
            }
        }
