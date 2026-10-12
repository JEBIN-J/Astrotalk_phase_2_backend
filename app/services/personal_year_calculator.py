from datetime import datetime
from typing import Dict, Any, Tuple, List

class PersonalYearCalculator:
    MIN_SUPPORTED_YEAR = 1900
    MAX_SUPPORTED_YEAR = 2100

    @classmethod
    def reduce_to_single_digit(cls, n: int) -> Tuple[int, List[str]]:
        if n < 0:
            raise ValueError("Number must be a non-negative integer.")
        steps = []
        val = n
        while val > 9:
            digits = [int(c) for c in str(val)]
            summed = sum(digits)
            steps.append(f"{val} -> {' + '.join(str(c) for c in digits)} = {summed}")
            val = summed
        if not steps and val <= 9:
            steps.append(f"{val} (single digit)")
        return val, steps

    @classmethod
    def calculate(cls, dob_str: str, target_year: int) -> Dict[str, Any]:
        if not dob_str or not isinstance(dob_str, str):
            raise ValueError("Date of birth is required.")

        dob_clean = dob_str.strip()
        try:
            dob_dt = datetime.strptime(dob_clean, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid date format '{dob_clean}'. Date of birth must be in YYYY-MM-DD format.")

        if dob_dt.year < 1800 or dob_dt.year > 2200:
            raise ValueError("Birth year must be between 1800 and 2200.")

        try:
            target_year = int(target_year)
        except (ValueError, TypeError):
            raise ValueError("Target year must be a valid integer.")

        if target_year < cls.MIN_SUPPORTED_YEAR or target_year > cls.MAX_SUPPORTED_YEAR:
            raise ValueError(f"Target year must be between {cls.MIN_SUPPORTED_YEAR} and {cls.MAX_SUPPORTED_YEAR}.")

        birth_month = dob_dt.month
        birth_day = dob_dt.day

        month_val, month_steps = cls.reduce_to_single_digit(birth_month)
        day_val, day_steps = cls.reduce_to_single_digit(birth_day)
        year_val, year_steps = cls.reduce_to_single_digit(target_year)

        combined_sum = month_val + day_val + year_val
        personal_year, sum_steps = cls.reduce_to_single_digit(combined_sum)

        trace = {
            "date_of_birth": dob_clean,
            "target_year": target_year,
            "birth_month": birth_month,
            "birth_day": birth_day,
            "month_reduced": month_val,
            "month_reduction_step": f"Month {birth_month} -> {month_val}",
            "day_reduced": day_val,
            "day_reduction_step": f"Day {birth_day} -> {day_val}",
            "year_reduced": year_val,
            "year_reduction_step": f"Year {target_year} -> {year_val}",
            "sum_formula": f"{month_val} (month) + {day_val} (day) + {year_val} (year) = {combined_sum}",
            "final_reduction_steps": sum_steps,
            "personal_year_result": personal_year
        }

        return {
            "personal_year_number": personal_year,
            "target_year": target_year,
            "calculation_method": "Pythagorean Calendar-Year Cycle (1-9)",
            "method_version": "1.0.0",
            "calculation_trace": trace
        }
