"""
Authoritative Personality Number & Soul Urge Number Calculator Engine.
Implements:
  1. Pythagorean Name Numerology (1-9 Mapping)
  2. Personality Number: Consonants strictly, vowels excluded.
  3. Soul Urge Number (Heart's Desire): Vowels strictly, consonants excluded.
  4. Configurable Y Policy:
     - 'always_consonant' (default): Y is consonant (value 7), contributing to Personality only.
     - 'always_vowel': Y is vowel (value 7), contributing to Soul Urge only.
     - 'manual_classification': configurable Y treatment.
  5. Reduction Rule & Master Numbers:
     - Preserves Master Numbers 11, 22, and 33 when reached.
     - Reduces other numbers to single digits 1-9.
  6. Audit Trace & Normalization:
     - Full letter-by-letter traces, word breakdowns, subtotals, reduction steps.
     - NFKD normalization and diacritic stripping.
     - Rejection/explanation of non-Latin unsupported characters.
"""
import unicodedata
from typing import Dict, Any, List, Tuple, Optional


class PersonalityNumberCalculator:
    """
    Dedicated calculator for Personality Number (The Outer Persona / Demeanor).
    Calculated strictly from consonants.
    """

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

    MASTER_NUMBERS = {11, 22, 33}

    @classmethod
    def calculate(
        cls,
        words_data: List[Dict[str, Any]],
        y_policy: str = "always_consonant"
    ) -> Dict[str, Any]:
        """
        Calculates Personality Number from pre-classified word breakdown data.
        """
        total_sum = 0
        all_consonants = []
        word_summaries = []

        for w_data in words_data:
            word = w_data["word"]
            w_cons_letters = [ch for ch in w_data["letters"] if ch["type"] == "consonant"]
            w_cons_sum = sum(ch["value"] for ch in w_cons_letters)
            total_sum += w_cons_sum

            w_reduced, _, w_steps = cls._reduce_number(w_cons_sum)
            word_summaries.append({
                "word": word,
                "consonants": w_cons_letters,
                "subtotal": w_cons_sum,
                "reduced": w_reduced,
                "formula": " + ".join(f"{c['letter']}({c['value']})" for c in w_cons_letters) + f" = {w_cons_sum}" if w_cons_letters else "0"
            })
            all_consonants.extend(w_cons_letters)

        final_num, root_num, reduction_steps = cls._reduce_number(total_sum)

        return {
            "number": final_num,
            "root_number": root_num,
            "is_master_number": final_num in cls.MASTER_NUMBERS,
            "unreduced_sum": total_sum,
            "included_letters_count": len(all_consonants),
            "included_letters": all_consonants,
            "words_breakdown": word_summaries,
            "reduction_steps": reduction_steps,
            "formula_summary": " + ".join(f"{w['subtotal']}" for w in word_summaries) + f" = {total_sum}" if word_summaries else str(total_sum),
            "label": "Personality Number",
            "calculation_basis": "Consonants only (Vowels excluded)",
            "y_policy_applied": y_policy
        }

    @classmethod
    def _reduce_number(cls, n: int) -> Tuple[int, int, List[str]]:
        if n <= 0:
            return 0, 0, ["0"]
        steps = []
        val = n
        if val in cls.MASTER_NUMBERS:
            root = sum(int(c) for c in str(val))
            steps.append(f"{val} (Preserved Master Number {val})")
            return val, root, steps

        while val > 9:
            digits = [int(c) for c in str(val)]
            summed = sum(digits)
            steps.append(f"{val} -> {' + '.join(str(c) for c in digits)} = {summed}")
            val = summed
            if val in cls.MASTER_NUMBERS:
                root = sum(int(c) for c in str(val))
                steps.append(f"{val} (Preserved Master Number {val})")
                return val, root, steps

        root = val
        if not steps:
            steps.append(f"{val} (Single digit)")
        return val, root, steps


class SoulUrgeNumberCalculator:
    """
    Dedicated calculator for Soul Urge Number (Heart's Desire / Core Motivations).
    Calculated strictly from vowels.
    """

    MASTER_NUMBERS = {11, 22, 33}

    @classmethod
    def calculate(
        cls,
        words_data: List[Dict[str, Any]],
        y_policy: str = "always_consonant"
    ) -> Dict[str, Any]:
        """
        Calculates Soul Urge Number from pre-classified word breakdown data.
        """
        total_sum = 0
        all_vowels = []
        word_summaries = []

        for w_data in words_data:
            word = w_data["word"]
            w_vow_letters = [ch for ch in w_data["letters"] if ch["type"] == "vowel"]
            w_vow_sum = sum(ch["value"] for ch in w_vow_letters)
            total_sum += w_vow_sum

            w_reduced, _, w_steps = cls._reduce_number(w_vow_sum)
            word_summaries.append({
                "word": word,
                "vowels": w_vow_letters,
                "subtotal": w_vow_sum,
                "reduced": w_reduced,
                "formula": " + ".join(f"{c['letter']}({c['value']})" for c in w_vow_letters) + f" = {w_vow_sum}" if w_vow_letters else "0"
            })
            all_vowels.extend(w_vow_letters)

        final_num, root_num, reduction_steps = cls._reduce_number(total_sum)

        return {
            "number": final_num,
            "root_number": root_num,
            "is_master_number": final_num in cls.MASTER_NUMBERS,
            "unreduced_sum": total_sum,
            "included_letters_count": len(all_vowels),
            "included_letters": all_vowels,
            "words_breakdown": word_summaries,
            "reduction_steps": reduction_steps,
            "formula_summary": " + ".join(f"{w['subtotal']}" for w in word_summaries) + f" = {total_sum}" if word_summaries else str(total_sum),
            "label": "Soul Urge / Heart's Desire Number",
            "calculation_basis": "Vowels only (Consonants excluded)",
            "y_policy_applied": y_policy
        }

    @classmethod
    def _reduce_number(cls, n: int) -> Tuple[int, int, List[str]]:
        if n <= 0:
            return 0, 0, ["0"]
        steps = []
        val = n
        if val in cls.MASTER_NUMBERS:
            root = sum(int(c) for c in str(val))
            steps.append(f"{val} (Preserved Master Number {val})")
            return val, root, steps

        while val > 9:
            digits = [int(c) for c in str(val)]
            summed = sum(digits)
            steps.append(f"{val} -> {' + '.join(str(c) for c in digits)} = {summed}")
            val = summed
            if val in cls.MASTER_NUMBERS:
                root = sum(int(c) for c in str(val))
                steps.append(f"{val} (Preserved Master Number {val})")
                return val, root, steps

        root = val
        if not steps:
            steps.append(f"{val} (Single digit)")
        return val, root, steps


class PersonalitySoulAnalyzer:
    """
    Master coordinator service for Personality & Soul Urge analysis.
    Normalizes input, separates vowels & consonants according to Y policy,
    invokes dedicated calculators, and builds an auditable transparency trace.
    """

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

    BASE_VOWELS = {'A', 'E', 'I', 'O', 'U'}

    @classmethod
    def normalize_name(cls, raw_name: str) -> Tuple[str, List[str]]:
        """
        Normalizes name: strips leading/trailing spaces, normalizes multiple spaces,
        strips Unicode diacritics via NFKD.
        Returns (clean_normalized_name, excluded_non_letters).
        """
        if not raw_name or not isinstance(raw_name, str):
            return "", []

        normalized = unicodedata.normalize('NFKD', raw_name)
        ascii_chars = []
        excluded_chars = []

        for ch in normalized:
            if unicodedata.combining(ch):
                continue
            up = ch.upper()
            if up in cls.PYTHAGOREAN_MAP or up.isspace():
                ascii_chars.append(up)
            else:
                excluded_chars.append(ch)

        cleaned_str = "".join(ascii_chars)
        words = cleaned_str.split()
        return " ".join(words), excluded_chars

    @classmethod
    def analyze(
        cls,
        raw_name: str,
        y_policy: str = "always_consonant"
    ) -> Dict[str, Any]:
        """
        Executes complete deterministic calculation with auditable trace.
        """
        if not raw_name or not str(raw_name).strip():
            raise ValueError("Full birth name is required for Personality & Soul Urge calculation.")

        raw_trimmed = str(raw_name).strip()
        if len(raw_trimmed) > 100:
            raise ValueError("Name exceeds maximum length of 100 characters. Please provide a standard birth name.")

        normalized_name, excluded_chars = cls.normalize_name(raw_trimmed)
        words = normalized_name.split()

        if not words:
            has_letters = any(c.isalpha() for c in raw_trimmed)
            if has_letters:
                raise ValueError(
                    f"Name '{raw_trimmed}' contains non-Latin scripts not supported by the Western Pythagorean system. "
                    "Please provide an English/Latin transliteration (e.g., 'Aarav' instead of 'आरव')."
                )
            raise ValueError("Name does not contain valid letters (A-Z).")

        valid_y_policies = {"always_consonant", "always_vowel", "manual"}
        if y_policy not in valid_y_policies:
            y_policy = "always_consonant"

        words_data = []
        all_vowels_list = []
        all_consonants_list = []

        for word in words:
            word_letters = []
            for ch in word:
                val = cls.PYTHAGOREAN_MAP[ch]
                is_vowel = False

                if ch in cls.BASE_VOWELS:
                    is_vowel = True
                elif ch == 'Y':
                    if y_policy == "always_vowel":
                        is_vowel = True
                    else:
                        is_vowel = False
                else:
                    is_vowel = False

                letter_entry = {
                    "letter": ch,
                    "value": val,
                    "type": "vowel" if is_vowel else "consonant"
                }
                word_letters.append(letter_entry)
                if is_vowel:
                    all_vowels_list.append(letter_entry)
                else:
                    all_consonants_list.append(letter_entry)

            words_data.append({
                "word": word,
                "letters": word_letters
            })

        personality_calc = PersonalityNumberCalculator.calculate(words_data, y_policy=y_policy)
        soul_urge_calc = SoulUrgeNumberCalculator.calculate(words_data, y_policy=y_policy)

        audit_trace = {
            "original_name": raw_trimmed,
            "normalized_name": normalized_name,
            "name_normalization_policy": "NFKD Unicode normalization, combining diacritics stripped, non-letter characters excluded.",
            "letter_classification_policy": (
                "Y treated as Consonant (Pythagorean default)" if y_policy == "always_consonant"
                else "Y treated as Vowel (Vocalic policy)"
            ),
            "master_number_policy": "Master Numbers 11, 22, 33 preserved when reached; other totals reduced to single digit 1-9.",
            "total_letters_evaluated": len(all_vowels_list) + len(all_consonants_list),
            "vowels_count": len(all_vowels_list),
            "consonants_count": len(all_consonants_list),
            "excluded_characters": excluded_chars,
            "words": words_data,
            "personality_trace": {
                "included_letters": [f"{c['letter']}={c['value']}" for c in all_consonants_list],
                "unreduced_sum": personality_calc["unreduced_sum"],
                "reduction_steps": personality_calc["reduction_steps"],
                "final_number": personality_calc["number"]
            },
            "soul_urge_trace": {
                "included_letters": [f"{v['letter']}={v['value']}" for v in all_vowels_list],
                "unreduced_sum": soul_urge_calc["unreduced_sum"],
                "reduction_steps": soul_urge_calc["reduction_steps"],
                "final_number": soul_urge_calc["number"]
            },
            "algorithm_version": "1.0.0"
        }

        return {
            "system": "pythagorean",
            "y_policy": y_policy,
            "original_name": raw_trimmed,
            "normalized_name": normalized_name,
            "personality": personality_calc,
            "soul_urge": soul_urge_calc,
            "audit_trace": audit_trace,
            "algorithm_version": "1.0.0"
        }
