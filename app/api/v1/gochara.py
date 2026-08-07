"""Flask Planetary Transits (Gochara) Blueprint."""
from datetime import datetime
from flask import Blueprint, jsonify
from app.utils.constants import ZODIAC_SIGNS, PLANETS_INFO
from app.services.vedic_engine import (
    calculate_julian_day,
    calculate_lahiri_ayanamsa,
    get_planet_approx_longitudes,
    degree_to_sign_and_dms
)

gochara_bp = Blueprint("gochara", __name__, url_prefix="/api/v1/gochara")


@gochara_bp.route("/daily", methods=["GET"])
def get_daily_transits():
    """Retrieve current daily planetary transits and live ticker pills."""
    now = datetime.now()
    jd = calculate_julian_day(now.year, now.month, now.day, 6.5)
    ayanamsa = calculate_lahiri_ayanamsa(jd)
    planets = get_planet_approx_longitudes(jd, ayanamsa)

    transits = []
    ticker = []

    influences = {
        "Sun": "Illuminates authority, confidence, and government matters.",
        "Moon": "Heightens intuition, emotional depth, and mental clarity.",
        "Mars": "Energizes bold ambitions, technical ventures, and drive.",
        "Mercury": "Enhances commercial diplomacy, data analytics, and communication.",
        "Jupiter": "Bestows divine grace, philosophical wisdom, and wealth.",
        "Venus": "Promotes romance, creative luxury, and artistic flair.",
        "Saturn": "Rewards disciplined effort, patience, and karmic integrity.",
        "Rahu": "Sparks unconventional breakthroughs and digital innovations.",
        "Ketu": "Deepens spiritual detachment and introspective insights."
    }

    for name, (p_deg, speed, is_retro) in planets.items():
        s_idx, s_name, dms, _ = degree_to_sign_and_dms(p_deg)
        s_sanskrit = ZODIAC_SIGNS[s_idx - 1]["sanskrit"]
        retro_str = " (Retrograde)" if is_retro else ""
        
        transits.append({
            "planet": name,
            "sanskrit": PLANETS_INFO[name]["sanskrit"],
            "current_sign": s_name,
            "sign_sanskrit": s_sanskrit,
            "degree": dms,
            "is_retrograde": is_retro,
            "transit_start_date": "Current Period",
            "transit_end_date": "Ongoing",
            "influence": influences.get(name, "Favorable cosmic transit."),
            "color": PLANETS_INFO[name]["color"]
        })
        
        ticker.append(f"{name} in {s_name}{retro_str} ({dms})")

    return jsonify({
        "date": now.strftime("%Y-%m-%d"),
        "planetary_transits": transits,
        "live_ticker_items": ticker
    }), 200
