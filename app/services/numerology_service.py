from datetime import datetime
from typing import Dict, Any, List

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

    VEDIC_PLANETS = {
        1: "Sun", 2: "Moon", 3: "Jupiter", 4: "Rahu", 
        5: "Mercury", 6: "Venus", 7: "Ketu", 8: "Saturn", 9: "Mars"
    }

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
            "total_sum": total_sum,
            "vowel_sum": vowel_sum,
            "consonant_sum": consonant_sum,
            "breakdown": breakdown
        }
        
    @staticmethod
    def _calculate_lo_shu_grid(dob_str: str) -> dict:
        digits = [int(d) for d in dob_str.replace("-", "")]
        grid_counts = {i: 0 for i in range(1, 10)}
        for d in digits:
            if d != 0:
                grid_counts[d] += 1
                
        # Basic pattern detection
        planes = {
            "Thought (4-3-8)": all(grid_counts[x] > 0 for x in [4,3,8]),
            "Will (9-5-1)": all(grid_counts[x] > 0 for x in [9,5,1]),
            "Action (2-7-6)": all(grid_counts[x] > 0 for x in [2,7,6]),
        }
        
        return {
            "counts": grid_counts,
            "planes": planes,
            "missing": [k for k, v in grid_counts.items() if v == 0]
        }

    # ==========================================
    # VEDIC NUMEROLOGY
    # ==========================================
    @staticmethod
    def calculate_vedic(name: str, dob_str: str) -> Dict[str, Any]:
        try:
            dt = datetime.strptime(dob_str, "%Y-%m-%d")
        except ValueError:
            return {"error": "Invalid date format. Use YYYY-MM-DD"}
            
        # A. Mulank / Driver Number
        day = dt.day
        mulank = NumerologyService.reduce_number(day, keep_master=False)
        
        # B. Bhagyank / Destiny Number
        date_sum = sum(int(digit) for digit in dob_str.replace("-", ""))
        bhagyank = NumerologyService.reduce_number(date_sum, keep_master=False)
        
        # C. Namank (Using Chaldean for Vedic typically)
        name_details = NumerologyService._calculate_name_details(name, NumerologyService.CHALDEAN_MAP)
        namank = NumerologyService.reduce_number(name_details["total_sum"], keep_master=False)
        
        # D. Driver-Destiny Rel
        relation = f"{NumerologyService.VEDIC_PLANETS.get(mulank)} & {NumerologyService.VEDIC_PLANETS.get(bhagyank)}"
        
        return {
            "system": "vedic",
            "mulank": {
                "original_day": day,
                "reduced": mulank,
                "planet": NumerologyService.VEDIC_PLANETS.get(mulank)
            },
            "bhagyank": {
                "compound_total": date_sum,
                "reduced": bhagyank,
                "planet": NumerologyService.VEDIC_PLANETS.get(bhagyank)
            },
            "namank": {
                "compound_total": name_details["total_sum"],
                "reduced": namank,
                "breakdown": name_details["breakdown"]
            },
            "relationship": {
                "title": "Driver-Destiny Sync",
                "value": relation
            },
            "lo_shu_grid": NumerologyService._calculate_lo_shu_grid(dob_str)
        }

    # ==========================================
    # PYTHAGOREAN NUMEROLOGY
    # ==========================================
    @staticmethod
    def calculate_pythagorean(name: str, dob_str: str) -> Dict[str, Any]:
        try:
            dt = datetime.strptime(dob_str, "%Y-%m-%d")
        except ValueError:
            return {"error": "Invalid date format. Use YYYY-MM-DD"}
            
        # A. Life Path Number
        m = NumerologyService.reduce_number(dt.month, keep_master=True)
        d = NumerologyService.reduce_number(dt.day, keep_master=True)
        y_sum = sum(int(digit) for digit in str(dt.year))
        y = NumerologyService.reduce_number(y_sum, keep_master=True)
        lp_total = m + d + y
        life_path = NumerologyService.reduce_number(lp_total, keep_master=True)
        
        # B. Birthday Number
        birthday = NumerologyService.reduce_number(dt.day, keep_master=True)
        
        # Name Numbers
        name_details = NumerologyService._calculate_name_details(name, NumerologyService.PYTHAGOREAN_MAP)
        
        # C. Expression Number
        expression = NumerologyService.reduce_number(name_details["total_sum"], keep_master=True)
        
        # D. Soul Urge Number
        soul_urge = NumerologyService.reduce_number(name_details["vowel_sum"], keep_master=True)
        
        # E. Personality Number
        personality = NumerologyService.reduce_number(name_details["consonant_sum"], keep_master=True)
        
        # F. Maturity Number
        maturity_total = life_path + expression
        maturity = NumerologyService.reduce_number(maturity_total, keep_master=True)
        
        # G. Personal Year
        current_year = datetime.now().year
        py_total = dt.month + dt.day + current_year
        personal_year = NumerologyService.reduce_number(py_total, keep_master=False)
        
        return {
            "system": "pythagorean",
            "life_path": {
                "calculation": f"{m} + {d} + {y} = {lp_total}",
                "reduced": life_path
            },
            "birthday": {
                "original": dt.day,
                "reduced": birthday
            },
            "expression": {
                "compound_total": name_details["total_sum"],
                "reduced": expression,
                "breakdown": name_details["breakdown"]
            },
            "soul_urge": {
                "compound_total": name_details["vowel_sum"],
                "reduced": soul_urge
            },
            "personality": {
                "compound_total": name_details["consonant_sum"],
                "reduced": personality
            },
            "maturity": {
                "compound_total": maturity_total,
                "reduced": maturity
            },
            "personal_year": {
                "year": current_year,
                "reduced": personal_year
            }
        }
