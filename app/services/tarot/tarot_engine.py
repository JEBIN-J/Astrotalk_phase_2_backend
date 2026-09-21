import secrets
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
from .tarot_data import get_all_cards, get_card_by_id

class TarotEngine:
    @staticmethod
    def generate_seed() -> str:
        """Generate a cryptographically secure seed for reproducible readings."""
        return secrets.token_hex(16)

    @staticmethod
    def _get_seeded_random(seed: str, index: int) -> int:
        """Get deterministic random value based on seed and index."""
        hash_input = f"{seed}_{index}".encode('utf-8')
        hash_val = hashlib.sha256(hash_input).hexdigest()
        return int(hash_val, 16)

    @staticmethod
    def draw_cards(num_cards: int, seed: Optional[str] = None) -> List[Dict[str, Any]]:
        """Draw a specified number of unique cards with orientations."""
        deck = get_all_cards()
        if num_cards > len(deck):
            raise ValueError("Cannot draw more cards than are in the deck.")

        if not seed:
            seed = TarotEngine.generate_seed()

        available_indices = list(range(len(deck)))
        drawn = []

        for i in range(num_cards):
            # Deterministic selection
            rand_val = TarotEngine._get_seeded_random(seed, i * 2)
            idx_to_pick = rand_val % len(available_indices)
            card_idx = available_indices.pop(idx_to_pick)
            card = deck[card_idx].copy()
            
            # Deterministic orientation
            orient_val = TarotEngine._get_seeded_random(seed, i * 2 + 1)
            is_reversed = (orient_val % 2) == 1
            card['orientation'] = "Reversed" if is_reversed else "Upright"
            
            drawn.append(card)

        return drawn, seed

    @staticmethod
    def interpret_card(card: Dict[str, Any], context: str = "general") -> Dict[str, Any]:
        """Generate a structured interpretation based on card, orientation, and context."""
        orientation = card['orientation']
        is_up = orientation == "Upright"
        
        # Base meaning
        meaning = card.get('upright_meaning', '') if is_up else card.get('reversed_meaning', '')
        keywords = card.get('keywords', [])
        
        # Contextual meaning
        context_meaning = meaning
        if context == "love":
            context_meaning = card.get('love_meaning', meaning)
        elif context == "career":
            context_meaning = card.get('career_meaning', meaning)
        elif context == "finance":
            context_meaning = card.get('finance_meaning', meaning)
        elif context == "spiritual":
            context_meaning = card.get('spiritual_meaning', meaning)
        elif context == "yes_no":
            yn = card.get('yes_no_meaning', 'Maybe')
            context_meaning = f"The answer leans towards {yn}."
            
        return {
            "card_id": card["id"],
            "name": card["name"],
            "orientation": orientation,
            "keywords": keywords,
            "core_meaning": meaning,
            "context_meaning": context_meaning,
            "astrology_correspondence": None,
            "element": None,
            "yes_no": card.get("yes_no_meaning") if context == "yes_no" else None
        }

    @staticmethod
    def create_spread(spread_type: str, seed: Optional[str] = None) -> Dict[str, Any]:
        """Generate a complete reading for a specific spread."""
        spread_configs = {
            "single": {"count": 1, "positions": ["Focus"]},
            "yes_no": {"count": 1, "positions": ["Answer"]},
            "three_card_past_present_future": {"count": 3, "positions": ["Past", "Present", "Future"]},
            "three_card_situation_challenge_advice": {"count": 3, "positions": ["Situation", "Challenge", "Advice"]},
            "love_five_card": {"count": 5, "positions": ["Your Energy", "Other's Energy", "Dynamic", "Challenge", "Guidance"]},
            "career_five_card": {"count": 5, "positions": ["Current Career", "Strength", "Challenge", "Opportunity", "Advice"]},
            "celtic_cross": {"count": 10, "positions": [
                "Present", "Challenge", "Foundation", "Past", "Goal", 
                "Near Future", "Self", "Environment", "Hopes/Fears", "Outcome"
            ]},
            "year_ahead": {"count": 12, "positions": [
                "Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
            ]},
            "astrological_houses": {"count": 12, "positions": [
                "1st House (Self)", "2nd House (Wealth)", "3rd House (Communication)", "4th House (Home)", 
                "5th House (Creativity)", "6th House (Health/Work)", "7th House (Partnerships)", 
                "8th House (Transformation)", "9th House (Philosophy/Travel)", "10th House (Career)", 
                "11th House (Network)", "12th House (Subconscious)"
            ]}
        }

        if spread_type not in spread_configs:
            raise ValueError(f"Unknown spread type: {spread_type}")

        config = spread_configs[spread_type]
        drawn_cards, used_seed = TarotEngine.draw_cards(config["count"], seed)
        
        # Determine context based on spread name
        context = "general"
        if "love" in spread_type: context = "love"
        elif "career" in spread_type: context = "career"
        elif "yes_no" in spread_type: context = "yes_no"
        
        positions_data = []
        for i, pos_name in enumerate(config["positions"]):
            card_info = TarotEngine.interpret_card(drawn_cards[i], context)
            positions_data.append({
                "position_name": pos_name,
                "card": card_info
            })

        return {
            "spread_type": spread_type,
            "seed": used_seed,
            "positions": positions_data
        }
