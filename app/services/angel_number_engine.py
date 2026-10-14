"""
Angel Numbers Calculation and Pattern Detection Engine.
Deterministic pattern recognition, numerology digit-sum reduction,
and personal angel number derivation.
"""
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

PYTHAGOREAN_MAP = {
    'A': 1, 'J': 1, 'S': 1,
    'B': 2, 'K': 2, 'T': 2,
    'C': 3, 'L': 3, 'U': 3,
    'D': 4, 'M': 4, 'V': 4,
    'E': 5, 'N': 5, 'W': 5,
    'F': 6, 'O': 6, 'X': 6,
    'G': 7, 'P': 7, 'Y': 7,
    'H': 8, 'Q': 8, 'Z': 8,
    'I': 9, 'R': 9
}

class AngelNumberEngine:
    VERSION = "1.0.0"

    @classmethod
    def normalize_input(cls, raw_input: str) -> str:
        """
        Normalizes input while preserving leading zeros and clock separators.
        Rejects invalid characters or lengths.
        """
        if not raw_input:
            raise ValueError("Input sequence cannot be empty.")

        s = str(raw_input).strip()
        # Check length
        if len(s) < 1 or len(s) > 8:
            raise ValueError(f"Sequence length must be between 1 and 8 characters, received {len(s)}.")

        # If it's a clock time like 11:11 or 11.11
        if re.match(r'^\d{1,2}[:.]\d{2}$', s):
            s = s.replace('.', ':')
            parts = s.split(':')
            h = int(parts[0])
            m = int(parts[1])
            if not (0 <= h <= 23 and 0 <= m <= 59):
                raise ValueError(f"Clock input '{s}' contains invalid hour or minute ranges (00-23:00-59).")
            # Format as HH:MM with leading zero if single digit hour
            s = f"{h:02d}:{m:02d}"
            return s

        # Digits only check
        if not re.match(r'^\d+$', s):
            raise ValueError(f"Invalid sequence '{s}'. Only numeric digits (0-9) or 24-hour time (HH:MM) are accepted.")

        return s

    @classmethod
    def detect_patterns(cls, seq: str) -> Dict[str, Any]:
        """
        Algorithmic pattern detection across repeating digits, sequences, palindromes,
        repeated blocks, and mirror clock hours.
        """
        detected = []
        is_clock = ':' in seq
        digits_only = seq.replace(':', '')

        # 1. Clock Mirror Hour Patterns
        if is_clock:
            parts = seq.split(':')
            hh, mm = parts[0], parts[1]
            if hh == mm:
                detected.append({
                    "code": "mirror_hour",
                    "name": "Mirror Hour (Synchronous)",
                    "description": f"Hour and minute digits match identically ({seq})."
                })
            elif hh == mm[::-1]:
                detected.append({
                    "code": "mirror_hour",
                    "name": "Reversed Mirror Hour",
                    "description": f"Minutes reflect the reverse of the hours ({seq})."
                })

        # 2. All Identical Digits (e.g. 111, 7777)
        if len(digits_only) > 1 and len(set(digits_only)) == 1:
            detected.append({
                "code": "all_identical",
                "name": "Repeating Digits (Intensified Resonance)",
                "description": f"All {len(digits_only)} digits are identical ({digits_only[0]}), amplifying the base vibration."
            })

        # 3. Ascending Consecutive (e.g. 123, 1234, 2345)
        if len(digits_only) >= 3:
            is_asc = all(int(digits_only[i]) + 1 == int(digits_only[i+1]) for i in range(len(digits_only) - 1))
            if is_asc:
                detected.append({
                    "code": "ascending_consecutive",
                    "name": "Ascending Progression",
                    "description": "Digits increase consecutively by 1, symbolizing upward momentum and forward progress."
                })

        # 4. Descending Consecutive (e.g. 4321, 321)
        if len(digits_only) >= 3:
            is_desc = all(int(digits_only[i]) - 1 == int(digits_only[i+1]) for i in range(len(digits_only) - 1))
            if is_desc:
                detected.append({
                    "code": "descending_consecutive",
                    "name": "Descending Progression",
                    "description": "Digits decrease consecutively by 1, symbolizing release, decluttering, or inward grounding."
                })

        # 5. Repeated Blocks (e.g. 1212, 3434, 1010)
        n = len(digits_only)
        if n >= 4 and n % 2 == 0:
            half = n // 2
            if digits_only[:half] == digits_only[half:] and len(set(digits_only)) > 1:
                detected.append({
                    "code": "repeated_blocks",
                    "name": "Repeated Double Block",
                    "description": f"The multi-digit pattern '{digits_only[:half]}' repeats twice, creating rhythmic resonance."
                })

        # 6. Palindrome (e.g. 1221, 1331)
        if len(digits_only) >= 3 and digits_only == digits_only[::-1] and len(set(digits_only)) > 1:
            detected.append({
                "code": "palindrome",
                "name": "Palindromic Balance",
                "description": "The sequence reads the same backwards and forwards, symbolizing symmetry and reflection."
            })

        # 7. Repeated Adjacent Pair (e.g. 0011, 1123)
        if len(digits_only) >= 4:
            has_pair = any(digits_only[i] == digits_only[i+1] for i in range(len(digits_only) - 1))
            if has_pair and not any(p["code"] in ("all_identical", "repeated_blocks") for p in detected):
                detected.append({
                    "code": "has_repeated_pair",
                    "name": "Harmonic Doublet",
                    "description": "Contains clustered adjacent identical digits."
                })

        # Determine Primary Category based on precedence
        priority_order = [
            "all_identical",
            "mirror_hour",
            "ascending_consecutive",
            "descending_consecutive",
            "repeated_blocks",
            "palindrome",
            "has_repeated_pair"
        ]

        primary = "general_sequence"
        for p_code in priority_order:
            if any(p["code"] == p_code for p in detected):
                primary = p_code
                break

        return {
            "primary_pattern": primary,
            "detected_patterns": detected,
            "patterns_count": len(detected)
        }

    @classmethod
    def reduce_sequence(cls, seq: str) -> Dict[str, Any]:
        """
        Reduces a numeric sequence step-by-step to its single-digit root (1-9).
        Preserves leading zero representation in display strings.
        """
        digits_str = seq.replace(':', '')
        digits = [int(c) for c in digits_str]
        
        steps = []
        first_sum = sum(digits)
        step_1 = f"{' + '.join(str(d) for d in digits)} = {first_sum}"
        steps.append(step_1)

        current = first_sum
        while current > 9:
            d_list = [int(c) for c in str(current)]
            s = sum(d_list)
            steps.append(f"{current} -> {' + '.join(str(c) for c in d_list)} = {s}")
            current = s

        return {
            "compound_total": first_sum,
            "root_number": current,
            "calculation_steps": steps
        }

    @classmethod
    def calculate_personal_angel_number(cls, dob_str: Optional[str] = None, name: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculates personal angel number via:
        Method A: Birth-Date Reduction (DOB) -> Root -> Triple repetition (e.g. 7 -> 777)
        Method B: Name Reduction (Pythagorean) -> Root -> Triple repetition
        """
        if dob_str:
            dt = None
            for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
                try:
                    dt = datetime.strptime(dob_str.strip(), fmt)
                    break
                except ValueError:
                    continue

            if not dt:
                raise ValueError(f"Invalid date of birth format: '{dob_str}'. Expected YYYY-MM-DD.")

            date_digits = [int(c) for c in f"{dt.day:02d}{dt.month:02d}{dt.year:04d}"]
            comp_sum = sum(date_digits)
            steps = [f"Sum of birth date digits ({dt.strftime('%d-%m-%Y')}): {' + '.join(str(d) for d in date_digits)} = {comp_sum}"]

            curr = comp_sum
            while curr > 9:
                s_digits = [int(c) for c in str(curr)]
                s = sum(s_digits)
                steps.append(f"{curr} -> {' + '.join(str(c) for c in s_digits)} = {s}")
                curr = s

            root = curr
            angel_seq = f"{root}{root}{root}"

            return {
                "method": "birth_date",
                "method_name": "Birth-Date Root Resonance Method",
                "input_dob": dt.strftime("%Y-%m-%d"),
                "compound_total": comp_sum,
                "root_number": root,
                "personal_angel_number": angel_seq,
                "calculation_steps": steps,
                "explanation": (
                    f"Under the classical birth-date methodology, your birth date digits reduce to Root {root}. "
                    f"In angel numerology, the triple manifestation '{angel_seq}' serves as your foundational vibrational signature."
                )
            }

        elif name:
            cleaned = re.sub(r'[^A-Z]', '', name.upper().strip())
            if not cleaned:
                raise ValueError("Name must contain alphabetic characters.")

            letter_breakdown = []
            values = []
            for ch in cleaned:
                val = PYTHAGOREAN_MAP.get(ch, 0)
                values.append(val)
                letter_breakdown.append(f"{ch}({val})")

            comp_sum = sum(values)
            steps = [f"Letter values: {' + '.join(letter_breakdown)} = {comp_sum}"]

            curr = comp_sum
            while curr > 9:
                s_digits = [int(c) for c in str(curr)]
                s = sum(s_digits)
                steps.append(f"{curr} -> {' + '.join(str(c) for c in s_digits)} = {s}")
                curr = s

            root = curr
            angel_seq = f"{root}{root}{root}"

            return {
                "method": "name_pythagorean",
                "method_name": "Pythagorean Name Vibrational Method",
                "input_name": cleaned,
                "compound_total": comp_sum,
                "root_number": root,
                "personal_angel_number": angel_seq,
                "calculation_steps": steps,
                "explanation": (
                    f"Under the Pythagorean alphabetical mapping, '{cleaned}' reduces to root number {root}. "
                    f"Your personal name angel number is '{angel_seq}'."
                )
            }
        else:
            raise ValueError("Either 'dob' or 'name' must be provided for personal angel number calculation.")
