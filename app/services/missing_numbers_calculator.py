"""
Authoritative Missing Numbers / Karmic Lessons Calculator Engine.
Implements:
  1. Full birth name frequency analysis under Pythagorean Name Numerology (1-9 Mapping).
  2. Counts occurrences of every number 1 through 9.
  3. A number is marked missing IF AND ONLY IF its occurrence count is strictly ZERO.
  4. Preserves user name, tracks letter-by-letter mappings, word subtotals, and transparent calculation traces.
  5. NFKD Unicode normalization and diacritic stripping.
  6. Rejection of unsupported scripts and empty names.
  7. Secondary analysis: Hidden Passion numbers (highest frequency) and Planes of Expression.
"""
import unicodedata
from typing import Dict, Any, List, Tuple, Optional


class MissingNumbersCalculator:
    """
    Dedicated calculator for Missing Numbers (Karmic Lessons).
    Analyzes the frequency of numbers 1-9 across all supported letters in the full birth name.
    """

    PYTHAGOREAN_MAP: Dict[str, int] = {
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

    ALLOWED_PUNCTUATION = {"'", "-", "’", "•"}

    # Planes of Expression grouping (traditional Pythagorean)
    PLANES_OF_EXPRESSION = {
        "physical": [4, 5],
        "mental": [1, 8],
        "emotional": [2, 3, 6],
        "intuitive": [7, 9]
    }

    @classmethod
    def normalize_name(cls, raw_name: str) -> Tuple[str, List[str]]:
        """
        Normalizes birth name:
          - Strips leading/trailing spaces
          - Normalizes multiple spaces into a single space
          - Strips Unicode diacritics via NFKD (e.g., 'Renée' -> 'RENEE')
          - Detects unsupported non-Latin scripts (e.g. Cyrillic, Devanagari, Hanzi)
        Returns (clean_normalized_name, excluded_chars).
        Raises ValueError if name is empty or contains unsupported non-Latin scripts.
        """
        if not raw_name or not isinstance(raw_name, str):
            raise ValueError("Birth name must be a non-empty string.")

        trimmed = raw_name.strip()
        if not trimmed:
            raise ValueError("Birth name cannot be empty or blank whitespace.")

        normalized = unicodedata.normalize('NFKD', trimmed)
        ascii_chars = []
        excluded_chars = []

        for ch in normalized:
            # Skip combining diacritic marks
            if unicodedata.combining(ch):
                continue

            up = ch.upper()
            if up in cls.PYTHAGOREAN_MAP or up.isspace():
                ascii_chars.append(up)
            elif ch in cls.ALLOWED_PUNCTUATION:
                # Allowed punctuation is retained for word separation but excluded from letter counts
                ascii_chars.append(" ")
            else:
                excluded_chars.append(ch)

        # Check for unsupported non-Latin alphabets
        if excluded_chars:
            unsupported_sample = ", ".join(repr(c) for c in excluded_chars[:5])
            raise ValueError(
                f"Name contains unsupported non-Latin characters: {unsupported_sample}. "
                "Please provide a standard Latin transliteration for authoritative Pythagorean frequency analysis."
            )

        cleaned_str = "".join(ascii_chars)
        words = cleaned_str.split()
        if not words:
            raise ValueError("Birth name must contain at least one valid Latin letter (A-Z).")

        return " ".join(words), excluded_chars

    @classmethod
    def analyze(cls, raw_birth_name: str) -> Dict[str, Any]:
        """
        Performs full frequency analysis on the birth name.
        Counts occurrences of numbers 1-9.
        Returns complete frequency table, missing numbers, present numbers, and audit trace.
        """
        normalized_name, excluded_chars = cls.normalize_name(raw_birth_name)
        words = normalized_name.split()

        # Initialize frequency table for 1 through 9
        frequency_table: Dict[int, int] = {i: 0 for i in range(1, 10)}

        letter_trace: List[Dict[str, Any]] = []
        words_breakdown: List[Dict[str, Any]] = []
        letter_position = 1

        for w in words:
            word_letters = []
            word_freq: Dict[int, int] = {i: 0 for i in range(1, 10)}

            for ch in w:
                if ch in cls.PYTHAGOREAN_MAP:
                    num = cls.PYTHAGOREAN_MAP[ch]
                    frequency_table[num] += 1
                    word_freq[num] += 1

                    entry = {
                        "position": letter_position,
                        "letter": ch,
                        "mapped_number": num,
                        "word": w
                    }
                    letter_trace.append(entry)
                    word_letters.append(entry)
                    letter_position += 1

            words_breakdown.append({
                "word": w,
                "letters_count": len(word_letters),
                "letters": word_letters,
                "frequencies": word_freq
            })

        total_letters_evaluated = len(letter_trace)

        # Identify missing numbers: STRICTLY frequency == 0
        missing_numbers: List[int] = [n for n in range(1, 10) if frequency_table[n] == 0]

        # Identify present numbers: frequency > 0
        present_numbers: List[int] = [n for n in range(1, 10) if frequency_table[n] > 0]

        # Identify Hidden Passion Number(s): numbers with highest occurrence > 0
        max_freq = max(frequency_table.values()) if total_letters_evaluated > 0 else 0
        hidden_passion_numbers = [n for n in range(1, 10) if frequency_table[n] == max_freq and max_freq > 0]

        # Calculate Planes of Expression
        planes_analysis = {}
        for plane_name, plane_nums in cls.PLANES_OF_EXPRESSION.items():
            plane_total = sum(frequency_table[num] for num in plane_nums)
            plane_pct = round((plane_total / total_letters_evaluated * 100), 1) if total_letters_evaluated > 0 else 0.0
            planes_analysis[plane_name] = {
                "numbers": plane_nums,
                "occurrences": plane_total,
                "percentage": plane_pct
            }

        return {
            "calculation_status": "completed",
            "system": "pythagorean",
            "system_name": "Pythagorean Name Numerology",
            "algorithm_version": "1.0.0",
            "birth_name": raw_birth_name.strip(),
            "normalized_name": normalized_name,
            "total_letters_evaluated": total_letters_evaluated,
            "frequency_table": frequency_table,
            "missing_numbers": missing_numbers,
            "missing_count": len(missing_numbers),
            "present_numbers": present_numbers,
            "present_count": len(present_numbers),
            "has_no_missing_numbers": len(missing_numbers) == 0,
            "hidden_passion": {
                "numbers": hidden_passion_numbers,
                "max_frequency": max_freq
            },
            "planes_of_expression": planes_analysis,
            "audit_trace": {
                "normalization_policy": "NFKD Unicode normalization, Latin uppercase mapping (A-Z -> 1-9)",
                "words_evaluated": words_breakdown,
                "letter_mapping_trace": letter_trace,
                "formula_summary": ", ".join(f"{n}: {frequency_table[n]}" for n in range(1, 10))
            }
        }
