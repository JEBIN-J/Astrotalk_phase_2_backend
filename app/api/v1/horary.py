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

        from app.services.kp_engine import generate_kp_system
        kp_res = generate_kp_system(
            name="Horary Query",
            dob_str=date_str,
            tob_str=time_str,
            pob_str=data.get("place_of_birth") or data.get("place") or "New Delhi, India",
            latitude=lat,
            longitude=lon,
            timezone=tz_offset,
            ayanamsa_name=ayanamsa_name,
            node_type="true",
            horary_number=horary_number,
            horary_mode=horary_mode,
        )

        asc_info = kp_res.get('ascendant', {})
        asc_deg_val = asc_info.get('degree', 0.0) if isinstance(asc_info, dict) else float(asc_info or 0.0)
        
        # Legacy-compatible format for existing horary UI
        compat_planets = []
        for p in kp_res.get('planets', []):
            if p.get('name') != 'Ascendant':
                compat_planets.append({
                    'planet': p.get('name'),
                    'longitude': p.get('longitude', 0.0),
                    'retrograde': p.get('is_retrograde', False),
                    'speed': p.get('speed', 0.0),
                    'sign': p.get('sign_name', ''),
                    'star_lord': p.get('nakshatra_lord', '-'),
                    'sub_lord': p.get('sub_lord', '-'),
                    'sub_sub_lord': p.get('sub_sub_lord', '-'),
                    'nakshatra': p.get('nakshatra', '-'),
                    'pada': p.get('pada', '-'),
                    'house': p.get('house', 1)
                })

        compat_cusps = []
        for c in kp_res.get('bhava_cusps', []):
            compat_cusps.append({
                'house': c.get('house', 1),
                'longitude': c.get('longitude', 0.0),
                'sign': c.get('sign_name', ''),
                'star_lord': c.get('nakshatra_lord', '-'),
                'sub_lord': c.get('sub_lord', '-'),
                'sub_sub_lord': c.get('sub_sub_lord', '-'),
                'nakshatra': c.get('nakshatra', '-'),
                'pada': c.get('pada', 1)
            })

        asc_details = {
            'degree': asc_deg_val,
            'sign': asc_info.get('sign_name', '') if isinstance(asc_info, dict) else '',
            'star_lord': asc_info.get('nakshatra_lord', '-') if isinstance(asc_info, dict) else '-',
            'sub_lord': asc_info.get('sub_lord', '-') if isinstance(asc_info, dict) else '-',
            'sub_sub_lord': asc_info.get('sub_sub_lord', '-') if isinstance(asc_info, dict) else '-',
            'nakshatra': asc_info.get('nakshatra_name', '-') if isinstance(asc_info, dict) else '-',
            'pada': asc_info.get('pada', 1) if isinstance(asc_info, dict) else 1,
            'kp_249_number': horary_number,
        }

        kp_res['question'] = question
        kp_res['horary_number'] = horary_number
        kp_res['horary_mode'] = horary_mode
        kp_res['ascendant'] = asc_deg_val
        kp_res['ascendant_details'] = asc_details
        kp_res['planets_compat'] = compat_planets
        kp_res['cusps_compat'] = compat_cusps

        # Keep legacy cusps and planets at top level if desired, or kp_res has rich structures
        return jsonify({
            'status': 'success',
            'data': kp_res
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
