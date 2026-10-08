from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import math
from app.services.vedic_engine import calculate_julian_day, resolve_coordinates, calculate_lahiri_ayanamsa, get_planet_longitudes_precise, ZODIAC_SIGNS, NAKSHATRAS

try:
    import swisseph as swe
    SWISSEPH_AVAILABLE = True
except ImportError:
    try:
        import pyswisseph as swe
        SWISSEPH_AVAILABLE = True
    except ImportError:
        swe = None
        SWISSEPH_AVAILABLE = False

horary_bp = Blueprint('horary_api', __name__, url_prefix='/api/v1/horary')

VIMSHOTTARI_YEARS = {'Ketu': 7, 'Venus': 20, 'Sun': 6, 'Moon': 10, 'Mars': 7, 'Rahu': 18, 'Jupiter': 16, 'Saturn': 19, 'Mercury': 17}
DASHA_ORDER = ['Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury']
TOTAL_YEARS = 120

def generate_kp_sublords():
    kp_subs = []
    current_lon = 0.0
    nakshatra_span = 13.333333333333333
    for star_idx in range(27):
        star_lord = DASHA_ORDER[star_idx % 9]
        start_idx = DASHA_ORDER.index(star_lord)
        for i in range(9):
            sub_lord = DASHA_ORDER[(start_idx + i) % 9]
            sub_span = (VIMSHOTTARI_YEARS[sub_lord] / TOTAL_YEARS) * nakshatra_span
            start_lon = current_lon
            end_lon = current_lon + sub_span
            sign_start = int(start_lon / 30.0)
            sign_end = int(end_lon / 30.0)
            if sign_start != sign_end and (end_lon % 30.0) > 0.000001:
                boundary = (sign_start + 1) * 30.0
                kp_subs.append({'number': len(kp_subs) + 1, 'sign': ZODIAC_SIGNS[sign_start], 'star_lord': star_lord, 'sub_lord': sub_lord, 'start': start_lon, 'end': boundary})
                current_lon = boundary
                kp_subs.append({'number': len(kp_subs) + 1, 'sign': ZODIAC_SIGNS[sign_end], 'star_lord': star_lord, 'sub_lord': sub_lord, 'start': boundary, 'end': end_lon})
                current_lon = end_lon
            else:
                kp_subs.append({'number': len(kp_subs) + 1, 'sign': ZODIAC_SIGNS[sign_start], 'star_lord': star_lord, 'sub_lord': sub_lord, 'start': start_lon, 'end': end_lon})
                current_lon = end_lon
    return kp_subs

KP_249_TABLE = generate_kp_sublords()

def calculate_star_and_sub(longitude):
    norm_lon = longitude % 360.0
    for sub in KP_249_TABLE:
        if sub['start'] <= norm_lon <= sub['end'] or math.isclose(norm_lon, sub['end']):
            nak_idx = int(norm_lon / 13.333333333333333)
            pada = int((norm_lon % 13.333333333333333) / 3.333333333333333) + 1
            return {'sign': ZODIAC_SIGNS[int(norm_lon / 30)], 'degree': norm_lon % 30, 'nakshatra': NAKSHATRAS[nak_idx]['name'], 'pada': pada, 'star_lord': sub['star_lord'], 'sub_lord': sub['sub_lord']}
    return {}

@horary_bp.route('/chart', methods=['POST'])
def calculate_horary_chart():
    data = request.json
    try:
        question = data.get('question', '')
        date_str = data.get('date')
        time_str = data.get('time')
        tz_offset = float(data.get('timezone', 5.5))
        lat = float(data.get('latitude', 28.6139))
        lon = float(data.get('longitude', 77.2090))
        ayanamsa_name = data.get('ayanamsa', 'KP_NEW')
        horary_number = data.get('horary_number')
        
        try:
            dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        except:
            try:
                dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %I:%M %p")
            except:
                dt = datetime.now()
        utc_dt = dt - timedelta(hours=tz_offset)
        hour_utc = utc_dt.hour + (utc_dt.minute / 60.0)
        jd = calculate_julian_day(utc_dt.year, utc_dt.month, utc_dt.day, hour_utc)
        aya = calculate_lahiri_ayanamsa(jd, ayanamsa_name)
        
        planets_data = get_planet_longitudes_precise(jd, aya, lat, lon)
        planets_formatted = []
        for p_name, (plon, pspeed, retro) in planets_data.items():
            planets_formatted.append({'planet': p_name, 'longitude': plon, 'retrograde': retro, 'speed': pspeed, **calculate_star_and_sub(plon)})
            
        if horary_number and 1 <= int(horary_number) <= 249:
            asc_lon = KP_249_TABLE[int(horary_number) - 1]['start']
        else:
            if SWISSEPH_AVAILABLE and swe:
                houses, ascmc = swe.houses(jd, lat, lon, b'P')
                asc_lon = (ascmc[0] - aya) % 360.0
            else:
                asc_lon = 0.0
                
        cusps = [{'house': i + 1, 'longitude': (asc_lon + (i * 30)) % 360.0, **calculate_star_and_sub((asc_lon + (i * 30)) % 360.0)} for i in range(12)]
            
        return jsonify({'status': 'success', 'data': {'question': question, 'ascendant': asc_lon, 'ayanamsa_value': aya, 'planets': planets_formatted, 'cusps': cusps}})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400


HORARY_QUESTIONS = [
    {'category': 'Marriage', 'questions': ['When will I get married?', 'Will it be a love or arranged marriage?', 'Will my marriage be successful?']},
    {'category': 'Career', 'questions': ['Will I get the job I applied for?', 'When will I get a promotion?', 'Should I change my career path?', 'Will I be successful in my new business?']},
    {'category': 'Finance', 'questions': ['When will my financial situation improve?', 'Will I recover my lost money?', 'Is it a good time to invest?']},
    {'category': 'Health', 'questions': ['When will I recover from this illness?', 'Is the diagnosis correct?', 'Will the surgery be successful?']},
    {'category': 'Children', 'questions': ['When will I have a child?', 'Will my child be healthy?', 'Will my child succeed in exams?']},
    {'category': 'Litigation & Disputes', 'questions': ['Will I win the court case?', 'Will there be a settlement?', 'Is my lawyer competent?']},
    {'category': 'Travel & Relocation', 'questions': ['Will I go abroad?', 'Is this trip safe?', 'Should I relocate to the new city?']},
    {'category': 'Lost Items & Missing Persons', 'questions': ['Where is my lost item?', 'Will the stolen property be recovered?', 'Is the missing person safe?']}
]

@horary_bp.route('/questions', methods=['GET'])
def get_horary_questions():
    return jsonify({'status': 'success', 'data': HORARY_QUESTIONS})

import random
@horary_bp.route('/generate_number', methods=['GET'])
def generate_kp_number():
    return jsonify({'status': 'success', 'data': {'kp_number': random.randint(1, 249)}})
