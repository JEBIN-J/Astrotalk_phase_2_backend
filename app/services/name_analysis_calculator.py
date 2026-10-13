"""
Authoritative Name Analysis Calculator Engine.
Supports:
  1. Pythagorean System (1-9 mapping, A,E,I,O,U as vowels, Y as consonant)
     - Expression Number (all letters, Master Numbers 11, 22, 33 preserved by default)
     - Soul Urge Number (vowels only, Master Numbers preserved)
     - Personality Number (consonants only, Master Numbers preserved)
     - Cornerstone (first letter of first name) with traditional meaning
     - Capstone (last letter of first name) with traditional meaning
     - First Vowel Number (first vowel found in name) with visceral reflex meaning
     - Individual component (word-by-word) totals and reductions
  2. Chaldean System (1-8 mapping, letter 9 omitted from standard letter values)
     - Compound Name Total
     - Reduced Root Number (1-9)
     - Letter-by-letter and word-by-word breakdowns
"""
import unicodedata
from typing import Dict, Any, List, Tuple, Optional

class NameAnalysisCalculator:
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

    CHALDEAN_MAP = {
        'A': 1, 'I': 1, 'J': 1, 'Q': 1, 'Y': 1,
        'B': 2, 'K': 2, 'R': 2,
        'C': 3, 'G': 3, 'L': 3, 'S': 3,
        'D': 4, 'M': 4, 'T': 4,
        'E': 5, 'H': 5, 'N': 5, 'X': 5,
        'U': 6, 'V': 6, 'W': 6,
        'O': 7, 'Z': 7,
        'P': 8, 'F': 8
    }

    VOWELS = {'A', 'E', 'I', 'O', 'U'}
    MASTER_NUMBERS = {11, 22, 33}

    CORNERSTONE_DATA = {
        'A': {"title": "The Bold Pioneer", "meaning": "You approach opportunities with fierce independence, courage, and original ambition."},
        'B': {"title": "The Sensitive Diplomat", "meaning": "You meet life's opportunities through cooperation, empathy, and intuitive peacemaking."},
        'C': {"title": "The Expressive Catalyst", "meaning": "You initiate projects with vibrant cheerfulness, social warmth, and spontaneous verbal wit."},
        'D': {"title": "The Methodical Pillar", "meaning": "You enter new ventures with steady discipline, practical orderliness, and unshakeable resolve."},
        'E': {"title": "The Dynamic Explorer", "meaning": "You greet change with insatiable curiosity, adaptability, and a craving for adventurous freedom."},
        'F': {"title": "The Caring Guardian", "meaning": "You embrace new responsibilities with warmth, compassionate loyalty, and protective domestic care."},
        'G': {"title": "The Analytical Truth-Seeker", "meaning": "You approach life with deep mental discernment, solitary contemplation, and strategic analysis."},
        'H': {"title": "The Executive Strategist", "meaning": "You initiate ventures with pragmatic vision, commercial discernment, and measured ambition."},
        'I': {"title": "The Idealistic Visionary", "meaning": "You meet beginnings with profound sensitivity, humanitarian values, and refined aesthetic ideals."},
        'J': {"title": "The Independent Trailblazer", "meaning": "You lead from the front with clever self-reliance, high determination, and inventive initiative."},
        'K': {"title": "The Intuitive Dynamic", "meaning": "You approach life with lightning spiritual intuition, creative intensity, and inspiring presence."},
        'L': {"title": "The Diplomatic Harmonizer", "meaning": "You examine beginnings intellectually, seeking balance, articulate dialogue, and gracious tact."},
        'M': {"title": "The Diligent Craftsman", "meaning": "You build new beginnings with tireless patience, structural integrity, and hands-on practicality."},
        'N': {"title": "The Imaginative Innovator", "meaning": "You approach opportunities from fresh, unconventional angles with lively curiosity."},
        'O': {"title": "The Conscientious Protector", "meaning": "You meet life through a lens of moral integrity, protective family dedication, and steadfast duty."},
        'P': {"title": "The Discerning Scholar", "meaning": "You examine new horizons with intellectual reserve, philosophical patience, and sharp observation."},
        'Q': {"title": "The Magnetic Enigma", "meaning": "You initiate endeavors with an enigmatic aura, unique originality, and strong persuasive drive."},
        'R': {"title": "The Resilient Striver", "meaning": "You meet obstacles with immense emotional endurance, determination, and broad human compassion."},
        'S': {"title": "The Magnetic Motivator", "meaning": "You spark new paths through emotional charisma, enthusiastic warmth, and magnetic presence."},
        'T': {"title": "The Patient Peacemaker", "meaning": "You navigate beginnings with cooperative patience, sensitivity, and respect for collective harmony."},
        'U': {"title": "The Creative Empath", "meaning": "You meet life with generous self-expression, artistic imagination, and playful social goodwill."},
        'V': {"title": "The Master Organizer", "meaning": "You approach challenges with extraordinary focus, vision for permanence, and executive power."},
        'W': {"title": "The Versatile Voyager", "meaning": "You initiate change through multi-faceted curiosity, swift resourcefulness, and social adaptability."},
        'X': {"title": "The Inspiring Harmonizer", "meaning": "You embrace beginnings with artistic flair, compassionate counsel, and uplifting enthusiasm."},
        'Y': {"title": "The Solitary Mystic", "meaning": "You reflect upon life's avenues with spiritual independence, quiet contemplation, and deep wisdom."},
        'Z': {"title": "The Energetic Achiever", "meaning": "You approach challenges with brisk optimism, strategic speed, and inspirational zest."}
    }

    CAPSTONE_DATA = {
        'A': {"title": "The Decisive Finisher", "meaning": "You close endeavors decisively, refusing lingering delays and clearing the deck for the next summit."},
        'B': {"title": "The Gentle Reconciler", "meaning": "You bring projects to a peaceful, considerate finish, ensuring harmony between all parties involved."},
        'C': {"title": "The Celebratory Closer", "meaning": "You conclude endeavors with cheerful flair, ensuring that accomplishments are celebrated joyfully."},
        'D': {"title": "The Relentless Completer", "meaning": "You work tenaciously until the very last detail is perfected, leaving no loose ends unattended."},
        'E': {"title": "The Swift Concluder", "meaning": "You wrap up tasks briskly and enthusiastically, eager to leap forward into the next fresh horizon."},
        'F': {"title": "The Loving Caretaker", "meaning": "You ensure everyone is comforted and secure as a project completes, prioritizing human well-being."},
        'G': {"title": "The Meticulous Auditor", "meaning": "You review the final product with rigorous scrutiny, ensuring perfection and flawlessness."},
        'H': {"title": "The Practical Evaluator", "meaning": "You measure the final outcome by its tangible returns, commercial value, and enduring strength."},
        'I': {"title": "The High-Standard Finisher", "meaning": "You complete endeavors with artistic finesse, high ethical ideals, and universal generosity."},
        'J': {"title": "The Independent Closer", "meaning": "You conclude projects strictly on your own terms, maintaining personal dignity and self-sufficiency."},
        'K': {"title": "The Intuitive Finisher", "meaning": "You execute final breakthroughs through sudden intuitive leaps and high-voltage precision."},
        'L': {"title": "The Thoughtful Arbiter", "meaning": "You bring closure through fair reflection, intellectual balance, and graceful compromise."},
        'M': {"title": "The Enduring Builder", "meaning": "You ensure the final result is built to stand the test of time, refusing shortcuts of any kind."},
        'N': {"title": "The Inventive Wrap-Up", "meaning": "You add unexpected, creative concluding touches that make your final work stand out distinctly."},
        'O': {"title": "The Principled Guardian", "meaning": "You close projects with strong moral rectitude, protective responsibility, and loyal devotion."},
        'P': {"title": "The Dignified Polisher", "meaning": "You finish with scholarly poise and careful refinement, guarding your professional reputation."},
        'Q': {"title": "The Distinctive Closer", "meaning": "You conclude endeavors with an unforgettable, non-conformist flourish that leaves an indelible mark."},
        'R': {"title": "The Tenacious Anchor", "meaning": "You persevere across the finish line even in the face of fatigue, triumphing through shear grit."},
        'S': {"title": "The Passionate Climax", "meaning": "You complete tasks with inspiring theatrical flair, emotional power, and captivating energy."},
        'T': {"title": "The Cooperative Resolver", "meaning": "You collaborate seamlessly right up to the final second, ensuring the team crosses the goal together."},
        'U': {"title": "The Joyful Celebrant", "meaning": "You wrap up efforts with warm camaraderie, artistic beauty, and infectious good spirits."},
        'V': {"title": "The Monumental Closer", "meaning": "You lock in permanent structures and tangible legacy, building foundations that endure indefinitely."},
        'W': {"title": "The Multi-Thread Finisher", "meaning": "You skillfully tie together diverse complex threads, wrapping up multifaceted operations cleanly."},
        'X': {"title": "The Generous Benefactor", "meaning": "You share the credit of victory with your fellows, ensuring the final triumph heals and inspires."},
        'Y': {"title": "The Reflective Sage", "meaning": "You step back calmly upon completion to assimilate the spiritual lessons of the journey."},
        'Z': {"title": "The Triumphant Victor", "meaning": "You finish with radiant vitality and clear satisfaction, turning victories into springboards."}
    }

    FIRST_VOWEL_DATA = {
        'A': {"title": "Visceral Drive for Independence", "meaning": "Your immediate soul reflex when encountering life is a bold craving for autonomy, self-determination, and original initiative."},
        'E': {"title": "Visceral Drive for Freedom", "meaning": "Your instantaneous emotional reflex is a desire for mental stimulation, progressive variety, and expansive freedom."},
        'I': {"title": "Visceral Drive for Inspiration", "meaning": "Your immediate soul yearning seeks deep meaning, artistic resonance, empathy, and universal ideals."},
        'O': {"title": "Visceral Drive for Harmony", "meaning": "Your core emotional reflex is an instinctive concern for home, family protection, justice, and moral rectitude."},
        'U': {"title": "Visceral Drive for Creative Joy", "meaning": "Your spontaneous soul instinct seeks creative self-expression, humor, connection, and social beauty."}
    }

    @classmethod
    def normalize_name(cls, raw_name: str) -> str:
        """
        Normalizes spaces, capitalization, and strips non-Latin accent diacritics.
        e.g. '  René François  ' -> 'RENE FRANCOIS'
        """
        if not raw_name or not isinstance(raw_name, str):
            return ""
        normalized = unicodedata.normalize('NFKD', raw_name)
        ascii_chars = [c for c in normalized if not unicodedata.combining(c)]
        cleaned = ''.join(ascii_chars).upper()
        words = cleaned.split()
        return ' '.join(words)

    @classmethod
    def reduce_number(cls, n: int, preserve_masters: bool = True) -> Tuple[int, int, List[str]]:
        """
        Reduces number and returns (final_number, root_single_digit, reduction_steps).
        """
        if n <= 0:
            return 0, 0, ["0"]
        steps = []
        val = n
        if preserve_masters and val in cls.MASTER_NUMBERS:
            root = sum(int(c) for c in str(val))
            steps.append(f"{val} is preserved as Master Number {val} (Root {root})")
            return val, root, steps

        while val > 9:
            digits = [int(c) for c in str(val)]
            summed = sum(digits)
            steps.append(f"{val} -> {' + '.join(str(c) for c in digits)} = {summed}")
            val = summed
            if preserve_masters and val in cls.MASTER_NUMBERS:
                root = sum(int(c) for c in str(val))
                steps.append(f"{val} is preserved as Master Number {val} (Root {root})")
                return val, root, steps

        root = val
        if not steps:
            steps.append(f"{val} (single digit)")
        return val, root, steps

    @classmethod
    def analyze_pythagorean(cls, raw_name: str) -> Dict[str, Any]:
        """
        Performs authoritative Pythagorean name analysis.
        """
        if not raw_name or not str(raw_name).strip():
            raise ValueError("Full birth name is required for Name Analysis.")

        if len(str(raw_name).strip()) > 100:
            raise ValueError("Name is too long. Please enter a name under 100 characters.")

        norm_name = cls.normalize_name(raw_name)
        words = norm_name.split()
        recognized_letters = []
        word_breakdowns = []

        total_expression_sum = 0
        total_soul_urge_sum = 0
        total_personality_sum = 0

        cornerstone = None
        capstone = None
        first_vowel = None

        for word_idx, word in enumerate(words):
            word_letters = []
            word_expr_sum = 0
            word_vowel_sum = 0
            word_cons_sum = 0

            clean_word_chars = []
            for ch in word:
                if ch in cls.PYTHAGOREAN_MAP:
                    clean_word_chars.append(ch)

            for char_idx, ch in enumerate(clean_word_chars):
                val = cls.PYTHAGOREAN_MAP[ch]
                is_vowel = ch in cls.VOWELS

                if is_vowel and first_vowel is None:
                    fv_info = cls.FIRST_VOWEL_DATA.get(ch, {"title": f"Vowel {ch}", "meaning": f"The resonance of vowel {ch}"})
                    first_vowel = {
                        "letter": ch,
                        "value": val,
                        "title": fv_info["title"],
                        "meaning": fv_info["meaning"]
                    }

                if word_idx == 0 and char_idx == 0:
                    cs_info = cls.CORNERSTONE_DATA.get(ch, {"title": f"Cornerstone {ch}", "meaning": f"Approach governed by {ch}"})
                    cornerstone = {
                        "letter": ch,
                        "value": val,
                        "title": cs_info["title"],
                        "meaning": cs_info["meaning"]
                    }

                if word_idx == 0 and char_idx == len(clean_word_chars) - 1:
                    cp_info = cls.CAPSTONE_DATA.get(ch, {"title": f"Capstone {ch}", "meaning": f"Finishing tenacity governed by {ch}"})
                    capstone = {
                        "letter": ch,
                        "value": val,
                        "title": cp_info["title"],
                        "meaning": cp_info["meaning"]
                    }

                word_expr_sum += val
                if is_vowel:
                    word_vowel_sum += val
                else:
                    word_cons_sum += val

                entry = {
                    "letter": ch,
                    "value": val,
                    "type": "vowel" if is_vowel else "consonant"
                }
                word_letters.append(entry)
                recognized_letters.append(entry)

            total_expression_sum += word_expr_sum
            total_soul_urge_sum += word_vowel_sum
            total_personality_sum += word_cons_sum

            w_exp_f, _, _ = cls.reduce_number(word_expr_sum, preserve_masters=True)
            w_vow_f, _, _ = cls.reduce_number(word_vowel_sum, preserve_masters=True) if word_vowel_sum > 0 else (0, 0, [])
            w_cons_f, _, _ = cls.reduce_number(word_cons_sum, preserve_masters=True) if word_cons_sum > 0 else (0, 0, [])

            word_breakdowns.append({
                "word": word,
                "letters": word_letters,
                "expression_subtotal": word_expr_sum,
                "expression_reduced": w_exp_f,
                "vowel_subtotal": word_vowel_sum,
                "vowel_reduced": w_vow_f,
                "consonant_subtotal": word_cons_sum,
                "consonant_reduced": w_cons_f
            })

        if not recognized_letters:
            raise ValueError(f"Name '{raw_name}' does not contain recognized Latin letters (A-Z). For non-Latin names (Hindi, Arabic, Cyrillic, etc.), please provide an English transliteration (e.g., 'Amit' instead of 'अमित').")

        expr_final, expr_root, expr_steps = cls.reduce_number(total_expression_sum, preserve_masters=True)
        soul_final, soul_root, soul_steps = cls.reduce_number(total_soul_urge_sum, preserve_masters=True)
        pers_final, pers_root, pers_steps = cls.reduce_number(total_personality_sum, preserve_masters=True)

        return {
            "system": "pythagorean",
            "system_name": "Pythagorean (Western Modern)",
            "vowel_policy": "A, E, I, O, U are counted as vowels; Y is treated as a consonant by default to maintain objective, rule-based calculation.",
            "original_name": raw_name,
            "normalized_name": norm_name,
            "total_letters_count": len(recognized_letters),
            "words": word_breakdowns,
            "recognized_letters": recognized_letters,
            "cornerstone": cornerstone,
            "capstone": capstone,
            "first_vowel": first_vowel,
            "core_numbers": {
                "expression": {
                    "unreduced_total": total_expression_sum,
                    "final_number": expr_final,
                    "root_number": expr_root,
                    "is_master_number": expr_final in cls.MASTER_NUMBERS,
                    "reduction_steps": expr_steps,
                    "label": "Expression / Destiny Number",
                    "description": "Represents your innate natural abilities, overarching life mission, and vocational potential."
                },
                "soul_urge": {
                    "unreduced_total": total_soul_urge_sum,
                    "final_number": soul_final,
                    "root_number": soul_root,
                    "is_master_number": soul_final in cls.MASTER_NUMBERS,
                    "reduction_steps": soul_steps,
                    "label": "Soul Urge / Heart's Desire Number",
                    "description": "Calculated strictly from vowels (A, E, I, O, U); reveals your core emotional motivators and spiritual longings."
                },
                "personality": {
                    "unreduced_total": total_personality_sum,
                    "final_number": pers_final,
                    "root_number": pers_root,
                    "is_master_number": pers_final in cls.MASTER_NUMBERS,
                    "reduction_steps": pers_steps,
                    "label": "Personality Number",
                    "description": "Calculated from consonants; represents your outer demeanor, social aura, and the first impression made on others."
                }
            }
        }

    @classmethod
    def analyze_chaldean(cls, raw_name: str) -> Dict[str, Any]:
        """
        Performs authoritative Chaldean name analysis.
        Letter values 1 to 8 (9 omitted from primary letter values as sacred).
        Compound total preserved and root calculated independently.
        """
        if not raw_name or not str(raw_name).strip():
            raise ValueError("Full birth name is required for Name Analysis.")

        if len(str(raw_name).strip()) > 100:
            raise ValueError("Name is too long. Please enter a name under 100 characters.")

        norm_name = cls.normalize_name(raw_name)
        words = norm_name.split()
        recognized_letters = []
        word_breakdowns = []
        total_sum = 0

        for word in words:
            word_letters = []
            word_sum = 0
            for ch in word:
                if ch in cls.CHALDEAN_MAP:
                    val = cls.CHALDEAN_MAP[ch]
                    word_sum += val
                    entry = {"letter": ch, "value": val}
                    word_letters.append(entry)
                    recognized_letters.append(entry)

            total_sum += word_sum
            w_root, _, _ = cls.reduce_number(word_sum, preserve_masters=False) if word_sum > 0 else (0, 0, [])

            word_breakdowns.append({
                "word": word,
                "letters": word_letters,
                "subtotal": word_sum,
                "reduced": w_root
            })

        if not recognized_letters:
            raise ValueError(f"Name '{raw_name}' does not contain recognized Latin letters (A-Z). For non-Latin names (Hindi, Arabic, Cyrillic, etc.), please provide an English transliteration (e.g., 'Amit' instead of 'अमित').")

        root_val, _, reduction_steps = cls.reduce_number(total_sum, preserve_masters=False)

        return {
            "system": "chaldean",
            "system_name": "Chaldean (Ancient Vibrational)",
            "letter_policy": "Ancient Chaldean formula assigning vibrations 1-8 to letters A-Z (9 omitted as sacred).",
            "original_name": raw_name,
            "normalized_name": norm_name,
            "total_letters_count": len(recognized_letters),
            "words": word_breakdowns,
            "recognized_letters": recognized_letters,
            "chaldean_compound_number": total_sum,
            "chaldean_root_number": root_val,
            "reduction_steps": reduction_steps,
            "label": "Chaldean Compound & Root Number",
            "description": "Compound numbers hold mystical planetary significance in Chaldean numerology, while the root represents your daily operational frequency."
        }

    @classmethod
    def calculate(cls, birth_name: str, current_name: Optional[str] = None, system: str = "pythagorean") -> Dict[str, Any]:
        system_clean = (system or "pythagorean").lower().strip()
        if system_clean not in ["pythagorean", "chaldean"]:
            system_clean = "pythagorean"

        if system_clean == "pythagorean":
            birth_analysis = cls.analyze_pythagorean(birth_name)
            current_analysis = cls.analyze_pythagorean(current_name) if current_name and current_name.strip() else None
        else:
            birth_analysis = cls.analyze_chaldean(birth_name)
            current_analysis = cls.analyze_chaldean(current_name) if current_name and current_name.strip() else None

        comparison = None
        if current_analysis:
            if system_clean == "pythagorean":
                b_exp = birth_analysis["core_numbers"]["expression"]["final_number"]
                c_exp = current_analysis["core_numbers"]["expression"]["final_number"]
                b_soul = birth_analysis["core_numbers"]["soul_urge"]["final_number"]
                c_soul = current_analysis["core_numbers"]["soul_urge"]["final_number"]
                b_pers = birth_analysis["core_numbers"]["personality"]["final_number"]
                c_pers = current_analysis["core_numbers"]["personality"]["final_number"]
                comparison = {
                    "is_harmonized": b_exp == c_exp,
                    "birth_expression": b_exp,
                    "current_expression": c_exp,
                    "birth_soul_urge": b_soul,
                    "current_soul_urge": c_soul,
                    "birth_personality": b_pers,
                    "current_personality": c_pers,
                    "summary": f"Your birth name carries Expression {b_exp}, while your commonly used name projects Expression {c_exp}." + (
                        " Both names vibrate to the exact same destiny frequency!" if b_exp == c_exp else
                        " Your current name activates an alternate vibrational expression that reframes how opportunities manifest."
                    )
                }
            else:
                b_comp = birth_analysis["chaldean_compound_number"]
                c_comp = current_analysis["chaldean_compound_number"]
                b_root = birth_analysis["chaldean_root_number"]
                c_root = current_analysis["chaldean_root_number"]
                comparison = {
                    "is_harmonized": b_root == c_root,
                    "birth_compound": b_comp,
                    "current_compound": c_comp,
                    "birth_root": b_root,
                    "current_root": c_root,
                    "summary": f"Birth name carries compound vibration {b_comp} (Root {b_root}), while current name vibrates to compound {c_comp} (Root {c_root})." + (
                        " Both names align on the same fundamental planetary root frequency!" if b_root == c_root else
                        " Your current name shifts your daily operational vibration to a different planetary ruler."
                    )
                }

        return {
            "status": "success",
            "system": system_clean,
            "birth_name_analysis": birth_analysis,
            "current_name_analysis": current_analysis,
            "name_comparison": comparison,
            "calculation_version": "1.0.0"
        }
