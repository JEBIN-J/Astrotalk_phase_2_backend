from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import math
import random
from app.services.vedic_engine import (
    calculate_julian_day,
    resolve_coordinates,
    calculate_lahiri_ayanamsa,
    get_planet_longitudes_precise,
    ZODIAC_SIGNS,
    NAKSHATRAS,
)

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

VIMSHOTTARI_YEARS = {
    'Ketu': 7,
    'Venus': 20,
    'Sun': 6,
    'Moon': 10,
    'Mars': 7,
    'Rahu': 18,
    'Jupiter': 16,
    'Saturn': 19,
    'Mercury': 17,
}
DASHA_ORDER = ['Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury']
TOTAL_YEARS = 120

def get_sign_name(idx):
    item = ZODIAC_SIGNS[idx % 12]
    if isinstance(item, dict):
        return item.get('name', '')
    return str(item)

def generate_kp_sublords():
    kp_subs = []
    nakshatra_span = 40.0 / 3.0
    for star_idx in range(27):
        star_lord = DASHA_ORDER[star_idx % 9]
        start_idx = DASHA_ORDER.index(star_lord)
        current_lon = round(star_idx * nakshatra_span, 8)
        for i in range(9):
            sub_lord = DASHA_ORDER[(start_idx + i) % 9]
            sub_span = (VIMSHOTTARI_YEARS[sub_lord] / TOTAL_YEARS) * nakshatra_span
            start_lon = current_lon
            end_lon = round(current_lon + sub_span, 8)
            sign_start = int(round(start_lon, 6) / 30.0)
            sign_end = int(round(end_lon, 6) / 30.0)
            if sign_start != sign_end and (end_lon % 30.0) > 1e-6 and not (abs(end_lon % 30.0 - 30.0) < 1e-6):
                boundary = float((sign_start + 1) * 30)
                kp_subs.append({
                    'number': len(kp_subs) + 1,
                    'sign': get_sign_name(sign_start),
                    'star_lord': star_lord,
                    'sub_lord': sub_lord,
                    'start': start_lon,
                    'end': boundary,
                })
                current_lon = boundary
                kp_subs.append({
                    'number': len(kp_subs) + 1,
                    'sign': get_sign_name(sign_end),
                    'star_lord': star_lord,
                    'sub_lord': sub_lord,
                    'start': boundary,
                    'end': end_lon,
                })
                current_lon = end_lon
            else:
                kp_subs.append({
                    'number': len(kp_subs) + 1,
                    'sign': get_sign_name(sign_start),
                    'star_lord': star_lord,
                    'sub_lord': sub_lord,
                    'start': start_lon,
                    'end': end_lon,
                })
                current_lon = end_lon
    return kp_subs

def generate_kp_sub_sublords():
    kp_sub_subs = []
    nakshatra_span = 40.0 / 3.0
    for star_idx in range(27):
        star_lord = DASHA_ORDER[star_idx % 9]
        start_idx = DASHA_ORDER.index(star_lord)
        current_lon = round(star_idx * nakshatra_span, 8)
        for i in range(9):
            sub_lord = DASHA_ORDER[(start_idx + i) % 9]
            sub_start_idx = DASHA_ORDER.index(sub_lord)
            sub_span = (VIMSHOTTARI_YEARS[sub_lord] / TOTAL_YEARS) * nakshatra_span
            for j in range(9):
                sub_sub_lord = DASHA_ORDER[(sub_start_idx + j) % 9]
                sub_sub_span = (VIMSHOTTARI_YEARS[sub_sub_lord] / TOTAL_YEARS) * sub_span
                start_lon = current_lon
                end_lon = round(current_lon + sub_sub_span, 8)
                sign_start = int(round(start_lon, 6) / 30.0)
                sign_end = int(round(end_lon, 6) / 30.0)
                if sign_start != sign_end and (end_lon % 30.0) > 1e-6 and not (abs(end_lon % 30.0 - 30.0) < 1e-6):
                    boundary = float((sign_start + 1) * 30)
                    kp_sub_subs.append({
                        'number': len(kp_sub_subs) + 1,
                        'sign': get_sign_name(sign_start),
                        'star_lord': star_lord,
                        'sub_lord': sub_lord,
                        'sub_sub_lord': sub_sub_lord,
                        'start': start_lon,
                        'end': boundary,
                    })
                    current_lon = boundary
                    kp_sub_subs.append({
                        'number': len(kp_sub_subs) + 1,
                        'sign': get_sign_name(sign_end),
                        'star_lord': star_lord,
                        'sub_lord': sub_lord,
                        'sub_sub_lord': sub_sub_lord,
                        'start': boundary,
                        'end': end_lon,
                    })
                    current_lon = end_lon
                else:
                    kp_sub_subs.append({
                        'number': len(kp_sub_subs) + 1,
                        'sign': get_sign_name(sign_start),
                        'star_lord': star_lord,
                        'sub_lord': sub_lord,
                        'sub_sub_lord': sub_sub_lord,
                        'start': start_lon,
                        'end': end_lon,
                    })
                    current_lon = end_lon
    return kp_sub_subs

KP_249_TABLE = generate_kp_sublords()
KP_2193_TABLE = generate_kp_sub_sublords()

def calculate_star_and_sub(longitude):
    norm_lon = longitude % 360.0
    nak_idx = int(norm_lon / (40.0 / 3.0))
    pada = int((norm_lon % (40.0 / 3.0)) / (10.0 / 3.0)) + 1
    
    matched_249 = None
    for sub in KP_249_TABLE:
        if sub['start'] <= norm_lon <= sub['end'] or math.isclose(norm_lon, sub['end'], abs_tol=1e-5):
            matched_249 = sub
            break
            
    matched_2193 = None
    for sub_sub in KP_2193_TABLE:
        if sub_sub['start'] <= norm_lon <= sub_sub['end'] or math.isclose(norm_lon, sub_sub['end'], abs_tol=1e-5):
            matched_2193 = sub_sub
            break

    sign_name = get_sign_name(int(norm_lon / 30))
    nak_name = NAKSHATRAS[nak_idx % 27]['name'] if nak_idx < len(NAKSHATRAS) else ''
    star_lord = matched_249['star_lord'] if matched_249 else (matched_2193['star_lord'] if matched_2193 else '')
    sub_lord = matched_249['sub_lord'] if matched_249 else (matched_2193['sub_lord'] if matched_2193 else '')
    sub_sub_lord = matched_2193['sub_sub_lord'] if matched_2193 else ''

    return {
        'sign': sign_name,
        'degree': norm_lon % 30,
        'nakshatra': nak_name,
        'pada': pada,
        'star_lord': star_lord,
        'sub_lord': sub_lord,
        'sub_sub_lord': sub_sub_lord,
        'kp_249_number': matched_249['number'] if matched_249 else None,
        'kp_2193_number': matched_2193['number'] if matched_2193 else None,
    }

@horary_bp.route('/chart', methods=['POST'])
def calculate_horary_chart():
    data = request.json or {}
    try:
        question = data.get('question', '')
        date_str = data.get('date')
        time_str = data.get('time')
        tz_offset = float(data.get('timezone', 5.5))
        lat = float(data.get('latitude', 28.6139))
        lon = float(data.get('longitude', 77.2090))
        ayanamsa_name = data.get('ayanamsa', 'KP_NEW')
        horary_number = data.get('horary_number')
        horary_mode = data.get('horary_mode', '')

        try:
            dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        except Exception:
            try:
                dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %I:%M %p")
            except Exception:
                dt = datetime.now()

        utc_dt = dt - timedelta(hours=tz_offset)
        hour_utc = utc_dt.hour + (utc_dt.minute / 60.0) + (utc_dt.second / 3600.0)
        jd = calculate_julian_day(utc_dt.year, utc_dt.month, utc_dt.day, hour_utc)
        aya = calculate_lahiri_ayanamsa(jd, ayanamsa_name)

        planets_data = get_planet_longitudes_precise(jd, aya, lat, lon)
        planets_formatted = []
        for p_name, (plon, pspeed, retro) in planets_data.items():
            planets_formatted.append({
                'planet': p_name,
                'longitude': plon,
                'retrograde': retro,
                'speed': pspeed,
                **calculate_star_and_sub(plon)
            })

        # Ascendant calculation based on mode
        if horary_number is not None and str(horary_number).strip() != '' and horary_mode != 'current_time':
            num = int(horary_number)
            if horary_mode == 'range_2193' or num > 249:
                if 1 <= num <= len(KP_2193_TABLE):
                    asc_lon = KP_2193_TABLE[num - 1]['start']
                else:
                    asc_lon = KP_2193_TABLE[0]['start']
            elif 1 <= num <= len(KP_249_TABLE):
                asc_lon = KP_249_TABLE[num - 1]['start']
            else:
                asc_lon = KP_249_TABLE[0]['start']
        else:
            # Current Time Direct Ascendant (Placidus system from Swiss Ephemeris)
            if SWISSEPH_AVAILABLE and swe:
                houses, ascmc = swe.houses(jd, lat, lon, b'P')
                asc_lon = (ascmc[0] - aya) % 360.0
            else:
                asc_lon = 0.0

        cusps = [
            {
                'house': i + 1,
                'longitude': (asc_lon + (i * 30)) % 360.0,
                **calculate_star_and_sub((asc_lon + (i * 30)) % 360.0)
            }
            for i in range(12)
        ]

        asc_details = calculate_star_and_sub(asc_lon)

        return jsonify({
            'status': 'success',
            'data': {
                'question': question,
                'ascendant': asc_lon,
                'ascendant_details': asc_details,
                'horary_mode': horary_mode,
                'horary_number': horary_number,
                'ayanamsa_value': aya,
                'planets': planets_formatted,
                'cusps': cusps
            }
        })
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

@horary_bp.route('/generate_number', methods=['GET'])
def generate_kp_number():
    mode = request.args.get('mode', '')
    max_val = int(request.args.get('max', 2193 if mode == 'range_2193' else 249))
    return jsonify({'status': 'success', 'data': {'kp_number': random.randint(1, max_val)}})

@horary_bp.route('/table/<int:table_type>', methods=['GET'])
def get_kp_table(table_type):
    if table_type == 2193:
        return jsonify({'status': 'success', 'count': len(KP_2193_TABLE), 'data': KP_2193_TABLE})
    return jsonify({'status': 'success', 'count': len(KP_249_TABLE), 'data': KP_249_TABLE})
