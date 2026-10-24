import unicodedata
import calendar
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

class NumerologyService:
    PYTHAGOREAN_MAP = {
        'a':1,'j':1,'s':1, 'b':2,'k':2,'t':2, 'c':3,'l':3,'u':3,
        'd':4,'m':4,'v':4, 'e':5,'n':5,'w':5, 'f':6,'o':6,'x':6,
        'g':7,'p':7,'y':7, 'h':8,'q':8,'z':8, 'i':9,'r':9
    }
    
    CHALDEAN_MAP = {
        'a':1,'i':1,'j':1,'q':1,'y':1, 'b':2,'k':2,'r':2,
        'c':3,'g':3,'l':3,'s':3, 'd':4,'m':4,'t':4,
        'e':5,'h':5,'n':5,'x':5, 'u':6,'v':6,'w':6,
        'o':7,'z':7, 'f':8,'p':8
    }

    CHALDEAN_CHART = {
        1: ['A', 'I', 'J', 'Q', 'Y'],
        2: ['B', 'K', 'R'],
        3: ['C', 'G', 'L', 'S'],
        4: ['D', 'M', 'T'],
        5: ['E', 'H', 'N', 'X'],
        6: ['U', 'V', 'W'],
        7: ['O', 'Z'],
        8: ['F', 'P']
    }

    PYTHAGOREAN_CHART = {
        1: ['A', 'J', 'S'],
        2: ['B', 'K', 'T'],
        3: ['C', 'L', 'U'],
        4: ['D', 'M', 'V'],
        5: ['E', 'N', 'W'],
        6: ['F', 'O', 'X'],
        7: ['G', 'P', 'Y'],
        8: ['H', 'Q', 'Z'],
        9: ['I', 'R']
    }

    VEDIC_PLANETS = {
        1: 'Sun', 2: 'Moon', 3: 'Jupiter', 4: 'Rahu', 
        5: 'Mercury', 6: 'Venus', 7: 'Ketu', 8: 'Saturn', 9: 'Mars'
    }

    @staticmethod
    def normalize_name(raw_name: str) -> str:
        """
        Normalizes spaces, capitalization, and strips non-Latin accent diacritics.
        e.g. '  René François  ' -> 'RENE FRANCOIS'
        """
        if not raw_name or not isinstance(raw_name, str):
            return ''
        normalized = unicodedata.normalize('NFKD', raw_name)
        ascii_chars = [c for c in normalized if not unicodedata.combining(c)]
        cleaned = ''.join(ascii_chars).upper()
        return ' '.join(cleaned.split())

    @staticmethod
    def reduce_number(num: int, keep_master: bool = False) -> int:
        if keep_master and num in [11, 22, 33]:
            return num
        while num > 9:
            num = sum(int(digit) for digit in str(num))
            if keep_master and num in [11, 22, 33]:
                return num
        return num

    @staticmethod
    def calculate_reduction_steps(num: int, keep_master: bool = False) -> Tuple[int, List[str]]:
        if num <= 0:
            return 0, []
        steps = []
        val = num
        if keep_master and val in [11, 22, 33]:
            steps.append(f"{val} is preserved as Master Number {val}")
            return val, steps
        while val > 9:
            digits = [int(c) for c in str(val)]
            summed = sum(digits)
            steps.append(f"{val} -> {' + '.join(str(c) for c in digits)} = {summed}")
            val = summed
            if keep_master and val in [11, 22, 33]:
                steps.append(f"{val} is preserved as Master Number {val}")
                return val, steps
        if not steps:
            steps.append(f"{val}")
        return val, steps

    @staticmethod
    def validate_date(year: int, month: int, day: int) -> Tuple[bool, Optional[str], Optional[datetime]]:
        current_year = datetime.now().year
        if year < 1900 or year > current_year:
            return False, f"Year must be between 1900 and {current_year}", None
        if month < 1 or month > 12:
            return False, "Month must be between 1 and 12", None
        
        days_in_month = calendar.monthrange(year, month)[1]
        if day < 1 or day > days_in_month:
            if month == 2:
                if calendar.isleap(year):
                    return False, f"February {year} has 29 days in a leap year.", None
                else:
                    return False, f"February {year} has only 28 days (not a leap year).", None
            month_name = calendar.month_name[month]
            return False, f"{month_name} has only {days_in_month} days.", None

        try:
            dt = datetime(year, month, day)
            return True, None, dt
        except ValueError as ve:
            return False, str(ve), None

    @staticmethod
    def _calculate_name_details(name: str, mapping: dict) -> dict:
        name_clean = ''.join(c.lower() for c in name if c.isalpha() or c.isspace())
        words = name_clean.split()
        
        breakdown = []
        total_sum = 0
        vowel_sum = 0
        consonant_sum = 0
        vowels = set('aeiou') 
        
        for word in words:
            word_val = 0
            word_vowels = 0
            word_cons = 0
            word_breakdown = []
            for char in word:
                val = mapping.get(char, 0)
                word_val += val
                if char in vowels:
                    word_vowels += val
                else:
                    word_cons += val
                word_breakdown.append({'char': char.upper(), 'value': val})
            total_sum += word_val
            vowel_sum += word_vowels
            consonant_sum += word_cons
            breakdown.append({'word': word, 'subtotal': word_val, 'letters': word_breakdown})
            
        return {
            'total_sum': total_sum,
            'vowel_sum': vowel_sum,
            'consonant_sum': consonant_sum,
            'breakdown': breakdown
        }
        
    @staticmethod
    def _calculate_lo_shu_grid(dob_str: str) -> dict:
        digits = [int(d) for d in dob_str.replace('-', '')]
        grid_counts = {i: 0 for i in range(1, 10)}
        for d in digits:
            if d != 0:
                grid_counts[d] += 1
                
        planes = {
            'Thought (4-3-8)': all(grid_counts[x] > 0 for x in [4,3,8]),
            'Will (9-5-1)': all(grid_counts[x] > 0 for x in [9,5,1]),
            'Action (2-7-6)': all(grid_counts[x] > 0 for x in [2,7,6]),
        }
        
        return {
            'counts': grid_counts,
            'planes': planes,
            'missing': [k for k, v in grid_counts.items() if v == 0]
        }

    # ==========================================
    # CHALDEAN NUMEROLOGY
    # ==========================================
    @staticmethod
    def calculate_chaldean(name: str, dob_str: str) -> Dict[str, Any]:
        try:
            dt = datetime.strptime(dob_str, '%Y-%m-%d')
        except ValueError:
            return {'error': 'Invalid date format. Use YYYY-MM-DD'}
            
        day = dt.day
        birth_day = NumerologyService.reduce_number(day, keep_master=False)
        
        date_sum = sum(int(digit) for digit in dob_str.replace('-', ''))
        destiny = NumerologyService.reduce_number(date_sum, keep_master=False)
        
        name_details = NumerologyService._calculate_name_details(name, NumerologyService.CHALDEAN_MAP)
        name_compound = name_details['total_sum']
        name_reduced = NumerologyService.reduce_number(name_compound, keep_master=False)
        
        soul_compound = name_details['vowel_sum']
        soul_reduced = NumerologyService.reduce_number(soul_compound, keep_master=False)
        
        personality_compound = name_details['consonant_sum']
        personality_reduced = NumerologyService.reduce_number(personality_compound, keep_master=False)
        
        return {
            'system': 'chaldean',
            'system_name': 'Chaldean Numerology (Ancient Vedic)',
            'birth_day': {
                'original': day,
                'reduced': birth_day
            },
            'life_path': {
                'compound_total': date_sum,
                'reduced': destiny
            },
            'expression': {
                'compound_total': name_compound,
                'reduced': name_reduced,
                'breakdown': name_details['breakdown']
            },
            'soul_urge': {
                'compound_total': soul_compound,
                'reduced': soul_reduced
            },
            'personality': {
                'compound_total': personality_compound,
                'reduced': personality_reduced
            },
            'lo_shu_grid': NumerologyService._calculate_lo_shu_grid(dob_str)
        }

    # ==========================================
    # VEDIC NUMEROLOGY
    # ==========================================
    @staticmethod
    def calculate_vedic(name: str, dob_str: str) -> Dict[str, Any]:
        try:
            dt = datetime.strptime(dob_str, '%Y-%m-%d')
        except ValueError:
            return {'error': 'Invalid date format. Use YYYY-MM-DD'}
            
        day = dt.day
        mulank = NumerologyService.reduce_number(day, keep_master=False)
        
        date_sum = sum(int(digit) for digit in dob_str.replace('-', ''))
        bhagyank = NumerologyService.reduce_number(date_sum, keep_master=False)
        
        name_details = NumerologyService._calculate_name_details(name, NumerologyService.CHALDEAN_MAP)
        namank = NumerologyService.reduce_number(name_details['total_sum'], keep_master=False)
        
        relation = f"{NumerologyService.VEDIC_PLANETS.get(mulank)} & {NumerologyService.VEDIC_PLANETS.get(bhagyank)}"
        
        return {
            'system': 'vedic',
            'mulank': {
                'original_day': day,
                'reduced': mulank,
                'planet': NumerologyService.VEDIC_PLANETS.get(mulank)
            },
            'bhagyank': {
                'compound_total': date_sum,
                'reduced': bhagyank,
                'planet': NumerologyService.VEDIC_PLANETS.get(bhagyank)
            },
            'namank': {
                'compound_total': name_details['total_sum'],
                'reduced': namank,
                'breakdown': name_details['breakdown']
            },
            'relationship': {
                'title': 'Driver-Destiny Sync',
                'value': relation
            },
            'lo_shu_grid': NumerologyService._calculate_lo_shu_grid(dob_str)
        }

    # ==========================================
    # PYTHAGOREAN NUMEROLOGY
    # ==========================================
    @staticmethod
    def calculate_pythagorean(name: str, dob_str: str) -> Dict[str, Any]:
        try:
            dt = datetime.strptime(dob_str, '%Y-%m-%d')
        except ValueError:
            return {'error': 'Invalid date format. Use YYYY-MM-DD'}
            
        m = NumerologyService.reduce_number(dt.month, keep_master=True)
        d = NumerologyService.reduce_number(dt.day, keep_master=True)
        y_sum = sum(int(digit) for digit in str(dt.year))
        y = NumerologyService.reduce_number(y_sum, keep_master=True)
        lp_total = m + d + y
        life_path = NumerologyService.reduce_number(lp_total, keep_master=True)
        
        birthday = NumerologyService.reduce_number(dt.day, keep_master=True)
        
        name_details = NumerologyService._calculate_name_details(name, NumerologyService.PYTHAGOREAN_MAP)
        expression = NumerologyService.reduce_number(name_details['total_sum'], keep_master=True)
        soul_urge = NumerologyService.reduce_number(name_details['vowel_sum'], keep_master=True)
        personality = NumerologyService.reduce_number(name_details['consonant_sum'], keep_master=True)
        
        maturity_total = life_path + expression
        maturity = NumerologyService.reduce_number(maturity_total, keep_master=True)
        
        current_year = datetime.now().year
        py_total = dt.month + dt.day + current_year
        personal_year = NumerologyService.reduce_number(py_total, keep_master=False)
        
        return {
            'system': 'pythagorean',
            'system_name': 'Pythagorean Numerology (Modern)',
            'life_path': {
                'calculation': f"{m} + {d} + {y} = {lp_total}",
                'reduced': life_path
            },
            'birthday': {
                'original': dt.day,
                'reduced': birthday
            },
            'expression': {
                'compound_total': name_details['total_sum'],
                'reduced': expression,
                'breakdown': name_details['breakdown']
            },
            'soul_urge': {
                'compound_total': name_details['vowel_sum'],
                'reduced': soul_urge
            },
            'personality': {
                'compound_total': name_details['consonant_sum'],
                'reduced': personality
            },
            'maturity': {
                'compound_total': maturity_total,
                'reduced': maturity
            },
            'personal_year': {
                'year': current_year,
                'reduced': personal_year
            }
        }

    # ==========================================
    # LIVE PREVIEW & AUTHORITATIVE CALCULATOR
    # ==========================================
    @classmethod
    def calculate_preview(
        cls,
        name: str,
        dob_str: Optional[str] = None,
        day: Optional[int] = None,
        month: Optional[int] = None,
        year: Optional[int] = None,
        system: str = 'chaldean',
        gender: Optional[str] = None
    ) -> Dict[str, Any]:
        system_clean = (system or 'chaldean').lower().strip()
        if system_clean not in ['chaldean', 'pythagorean']:
            system_clean = 'chaldean'

        is_chaldean = (system_clean == 'chaldean')
        mapping = cls.CHALDEAN_MAP if is_chaldean else cls.PYTHAGOREAN_MAP
        chart = cls.CHALDEAN_CHART if is_chaldean else cls.PYTHAGOREAN_CHART
        preserve_master = not is_chaldean

        # 1. Normalize and Calculate Name
        norm_name = cls.normalize_name(name)
        letters_list = []
        letter_counts: Dict[str, int] = {}
        active_letters = []
        active_numbers = set()
        compound_total = 0

        for ch in norm_name:
            if ch.isalpha():
                lower_ch = ch.lower()
                val = mapping.get(lower_ch, 0)
                letters_list.append({'char': ch, 'value': val})
                letter_counts[ch] = letter_counts.get(ch, 0) + 1
                compound_total += val
                if ch not in active_letters:
                    active_letters.append(ch)
                if val > 0:
                    active_numbers.add(val)

        is_name_empty = len(letters_list) == 0
        if is_name_empty:
            reduced_number = None
            display_total = None
            reduction_steps = []
        else:
            display_total = compound_total
            reduced_number, reduction_steps = cls.calculate_reduction_steps(compound_total, keep_master=preserve_master)

        # 2. Date of Birth Validation and Derived Numbers
        dt: Optional[datetime] = None
        is_date_valid = False
        date_error: Optional[str] = None
        formatted_dob: Optional[str] = None
        birth_day_number: Optional[int] = None
        life_path_number: Optional[int] = None

        parsed_day = day
        parsed_month = month
        parsed_year = year

        if (parsed_day is None or parsed_month is None or parsed_year is None) and dob_str and str(dob_str).strip():
            parts = str(dob_str).strip().split('-')
            if len(parts) == 3:
                try:
                    parsed_year = int(parts[0])
                    parsed_month = int(parts[1])
                    parsed_day = int(parts[2])
                except ValueError:
                    pass

        has_date_input = (parsed_day is not None or parsed_month is not None or parsed_year is not None)
        if has_date_input:
            if parsed_day is None or parsed_month is None or parsed_year is None:
                is_date_valid = False
                date_error = 'Please provide complete Day, Month, and Year.'
            else:
                valid, err, valid_dt = cls.validate_date(parsed_year, parsed_month, parsed_day)
                if not valid:
                    is_date_valid = False
                    date_error = err
                else:
                    is_date_valid = True
                    dt = valid_dt
                    formatted_dob = dt.strftime('%Y-%m-%d')
                    
                    if is_chaldean:
                        birth_day_number = cls.reduce_number(dt.day, keep_master=False)
                        all_digits_sum = sum(int(c) for c in formatted_dob.replace('-', ''))
                        life_path_number = cls.reduce_number(all_digits_sum, keep_master=False)
                    else:
                        birth_day_number = cls.reduce_number(dt.day, keep_master=True)
                        m_red = cls.reduce_number(dt.month, keep_master=True)
                        d_red = cls.reduce_number(dt.day, keep_master=True)
                        y_sum = sum(int(c) for c in str(dt.year))
                        y_red = cls.reduce_number(y_sum, keep_master=True)
                        life_path_number = cls.reduce_number(m_red + d_red + y_red, keep_master=True)

        valid_gender = (gender or 'other').lower().strip()
        if valid_gender not in ['male', 'female', 'other']:
            valid_gender = 'other'

        return {
            'system': system_clean,
            'system_name': 'Chaldean Numerology (Ancient Vedic)' if is_chaldean else 'Pythagorean Numerology (Modern)',
            'version': '2.1.0',
            'name_input': name,
            'normalized_name': norm_name,
            'is_name_empty': is_name_empty,
            'compound_total': display_total,
            'reduced_number': reduced_number,
            'reduction_steps': reduction_steps,
            'letter_values': letters_list,
            'letter_counts': letter_counts,
            'active_letters': active_letters,
            'active_numbers': sorted(list(active_numbers)),
            'alphabet_chart': chart,
            'date_input': {
                'day': parsed_day,
                'month': parsed_month,
                'year': parsed_year,
                'formatted_dob': formatted_dob
            },
            'is_date_valid': is_date_valid,
            'date_error': date_error,
            'birth_day_number': birth_day_number,
            'life_path_number': life_path_number,
            'gender': valid_gender
        }
