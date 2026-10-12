"""
Authoritative, deterministic Life Path Number calculation engine
implementing the Pythagorean Month-Day-Year separate reduction method
with Master Numbers (11, 22, 33) preserved at intermediate and final stages.
"""
from datetime import datetime
from typing import Dict, Any, List, Tuple

class LifePathCalculator:
    MASTER_NUMBERS = {11, 22, 33}

    @staticmethod
    def _reduce_digits(n: int, preserve_masters: bool = True) -> Tuple[int, List[str]]:
        """
        Reduces an integer to a single digit (1-9) or a Master Number (11, 22, 33).
        Returns (reduced_value, steps_trace).
        """
        steps = []
        val = n
        if preserve_masters and val in LifePathCalculator.MASTER_NUMBERS:
            steps.append(f"{val} is preserved as Master Number {val}")
            return val, steps

        while val > 9:
            digits = [int(c) for c in str(val)]
            summed = sum(digits)
            digit_str = " + ".join(str(c) for c in digits)
            steps.append(f"{val} -> {digit_str} = {summed}")
            val = summed
            if preserve_masters and val in LifePathCalculator.MASTER_NUMBERS:
                steps.append(f"{val} is preserved as Master Number {val}")
                break
        return val, steps

    @classmethod
    def calculate(cls, dob_str: str, system: str = "pythagorean") -> Dict[str, Any]:
        """
        Validates date of birth strictly (YYYY-MM-DD) and performs deterministic Life Path calculation.
        """
        if not dob_str or not isinstance(dob_str, str):
            raise ValueError("Date of birth is required.")

        dob_clean = dob_str.strip()
        try:
            dob_dt = datetime.strptime(dob_clean, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid date format '{dob_clean}'. Date of birth must be in YYYY-MM-DD format.")

        # Year boundary validation
        if dob_dt.year < 1800 or dob_dt.year > 2200:
            raise ValueError("Birth year must be between 1800 and 2200.")

        month_val = dob_dt.month
        day_val = dob_dt.day
        year_val = dob_dt.year

        # Step 1: Reduce Month
        reduced_month, month_steps = cls._reduce_digits(month_val, preserve_masters=True)

        # Step 2: Reduce Day
        reduced_day, day_steps = cls._reduce_digits(day_val, preserve_masters=True)

        # Step 3: Reduce Year
        year_digits = [int(c) for c in str(year_val)]
        year_first_sum = sum(year_digits)
        year_digit_str = " + ".join(str(c) for c in year_digits)
        year_initial_step = f"{year_val} -> {year_digit_str} = {year_first_sum}"
        
        reduced_year, year_reduction_steps = cls._reduce_digits(year_first_sum, preserve_masters=True)
        year_steps = [year_initial_step] + [s for s in year_reduction_steps if not s.startswith(str(year_val))]

        # Step 4: Combined Total
        combined_total = reduced_month + reduced_day + reduced_year
        combined_step = f"{reduced_month} (Month) + {reduced_day} (Day) + {reduced_year} (Year) = {combined_total}"

        # Step 5: Final Reduction
        final_number, final_reduction_steps = cls._reduce_digits(combined_total, preserve_masters=True)

        all_combined_steps = [combined_step] + final_reduction_steps

        # Number titles
        titles = {
            1: "The Innovative Pioneer & Leader",
            2: "The Harmonious Peacemaker & Diplomat",
            3: "The Expressive Creator & Communicator",
            4: "The Master Builder & Strategist",
            5: "The Free-Spirited Catalyst & Adventurer",
            6: "The Nurturing Guardian & Healer",
            7: "The Analytical Seeker & Mystic",
            8: "The Sovereign Achiever & Manifestor",
            9: "The Compassionate Humanitarian & Visionary",
            11: "The Illuminator (Master Intuitive)",
            22: "The Master Architect (Vision to Form)",
            33: "The Master Healer (Universal Compassion)"
        }

        core_themes = {
            1: "Independence, pioneering initiative, and trailblazing leadership.",
            2: "Cooperation, deep intuition, balance, and relational harmony.",
            3: "Creative self-expression, joyful vitality, enthusiasm, and optimism.",
            4: "Dedication, systematic order, reliability, and enduring foundations.",
            5: "Freedom, progressive change, versatility, and experiential learning.",
            6: "Unconditional care, domestic harmony, integrity, and healing service.",
            7: "Inner wisdom, analytical inquiry, discernment, and philosophical depth.",
            8: "Material mastery, executive authority, abundance, and karmic balance.",
            9: "Universal empathy, philanthropy, selfless vision, and completion.",
            11: "Spiritual insight, heightened intuition, and inspiring divine illumination.",
            22: "Monumental achievements, practical idealism, and global structural impact.",
            33: "Uplifting collective consciousness, compassionate wisdom, and healing service."
        }

        return {
            "life_path_number": final_number,
            "number_title": titles.get(final_number, f"Life Path {final_number}"),
            "core_theme": core_themes.get(final_number, "Personal destiny and core vibration."),
            "is_master_number": final_number in cls.MASTER_NUMBERS,
            "system": system,
            "calculation_trace": {
                "date_of_birth": dob_clean,
                "month": {
                    "original": month_val,
                    "reduced": reduced_month,
                    "steps": month_steps
                },
                "day": {
                    "original": day_val,
                    "reduced": reduced_day,
                    "steps": day_steps
                },
                "year": {
                    "original": year_val,
                    "reduced": reduced_year,
                    "steps": year_steps
                },
                "combined_sum": combined_total,
                "reduction_steps": all_combined_steps,
                "final_number": final_number
            }
        }
