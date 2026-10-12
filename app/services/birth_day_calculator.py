"""
Authoritative, deterministic Birth Day Number calculation engine.
Convention: Preserves the exact calendar day from 1 to 31 as the primary Birth Day Number.
Optionally calculates the secondary Pythagorean reduced root (with Master Numbers 11 & 22 preserved).
"""
from datetime import datetime
from typing import Dict, Any, Tuple, List

class BirthDayNumberCalculator:
    MASTER_NUMBERS = {11, 22}

    @classmethod
    def reduce_to_root(cls, day: int, preserve_masters: bool = True) -> Tuple[int, List[str]]:
        """
        Calculates the secondary reduced root number of a calendar day.
        Returns (reduced_root, reduction_steps).
        """
        steps = []
        val = day
        if preserve_masters and val in cls.MASTER_NUMBERS:
            steps.append(f"{val} is preserved as Master Number {val}")
            return val, steps

        while val > 9:
            digits = [int(c) for c in str(val)]
            summed = sum(digits)
            steps.append(f"{val} -> {' + '.join(str(c) for c in digits)} = {summed}")
            val = summed
            if preserve_masters and val in cls.MASTER_NUMBERS:
                steps.append(f"{val} is preserved as Master Number {val}")
                break

        return val, steps

    @classmethod
    def calculate(cls, dob_str: str, system: str = "pythagorean") -> Dict[str, Any]:
        """
        Validates date of birth strictly (YYYY-MM-DD) and performs Birth Day Number calculation.
        Primary number is strictly the calendar day (1-31).
        """
        if not dob_str or not isinstance(dob_str, str):
            raise ValueError("Date of birth is required.")

        dob_clean = dob_str.strip()
        try:
            dob_dt = datetime.strptime(dob_clean, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid date format '{dob_clean}'. Date of birth must be in YYYY-MM-DD format.")

        if dob_dt.year < 1800 or dob_dt.year > 2200:
            raise ValueError("Birth year must be between 1800 and 2200.")

        primary_day = dob_dt.day
        reduced_root, root_steps = cls.reduce_to_root(primary_day, preserve_masters=True)

        return {
            "birth_day_number": primary_day,
            "reduced_root": reduced_root,
            "is_master_day": primary_day in cls.MASTER_NUMBERS,
            "calculation_method": "Calendar Day (1-31) Preservation",
            "method_version": "1.0.0",
            "calculation_trace": {
                "date_of_birth": dob_clean,
                "calendar_day": primary_day,
                "calendar_month": dob_dt.month,
                "calendar_year": dob_dt.year,
                "primary_rule": f"Calendar day extracted as authoritative primary Birth Day Number: {primary_day}",
                "secondary_reduced_root": reduced_root,
                "root_reduction_steps": root_steps
            }
        }
