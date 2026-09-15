import pytest
from app.services.tarot.tarot_data import get_all_cards
from app.services.tarot.tarot_engine import TarotEngine

def test_deck_integrity():
    cards = get_all_cards()
    assert len(cards) == 78
    
    majors = [c for c in cards if c['arcana'] == 'Major']
    assert len(majors) == 22
    
    minors = [c for c in cards if c['arcana'] == 'Minor']
    assert len(minors) == 56
    
    wands = [c for c in minors if c['suit'] == 'Wands']
    cups = [c for c in minors if c['suit'] == 'Cups']
    swords = [c for c in minors if c['suit'] == 'Swords']
    pentacles = [c for c in minors if c['suit'] == 'Pentacles']
    
    assert len(wands) == 14
    assert len(cups) == 14
    assert len(swords) == 14
    assert len(pentacles) == 14

def test_randomization_engine():
    seed = "test_seed_123"
    draw1, seed1 = TarotEngine.draw_cards(3, seed)
    draw2, seed2 = TarotEngine.draw_cards(3, seed)
    
    # Should be deterministic
    assert seed1 == seed2
    assert draw1[0]['id'] == draw2[0]['id']
    assert draw1[1]['id'] == draw2[1]['id']
    assert draw1[2]['id'] == draw2[2]['id']
    
    # Should not have duplicates
    ids = [c['id'] for c in draw1]
    assert len(set(ids)) == 3

def test_spread_creation():
    # Single card
    spread = TarotEngine.create_spread("single")
    assert len(spread['positions']) == 1
    assert spread['positions'][0]['position_name'] == 'Focus'
    
    # Celtic cross
    spread_cc = TarotEngine.create_spread("celtic_cross")
    assert len(spread_cc['positions']) == 10
    
    ids = [p['card']['card_id'] for p in spread_cc['positions']]
    assert len(set(ids)) == 10
