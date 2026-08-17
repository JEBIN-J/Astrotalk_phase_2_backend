"""Flask Content Blueprint for Quotes, Notifications, and Muhurat."""
from flask import Blueprint, jsonify, request
from datetime import datetime

content_bp = Blueprint('content', __name__)

@content_bp.route("/quotes", methods=["GET"])
def get_daily_quotes():
    """Retrieve daily astrological quotes."""
    return jsonify([
        {"id": 1, "text": "The stars only impel, they do not compel.", "author": "Vedic Wisdom", "category": "Motivation"},
        {"id": 2, "text": "Saturn delays, but it never denies.", "author": "Astrology Proverb", "category": "Patience"},
        {"id": 3, "text": "A favorable Jupiter brings expansion where you least expect it.", "author": "Cosmic Insight", "category": "Growth"}
    ])

@content_bp.route("/notifications", methods=["GET"])
def get_notifications():
    """Retrieve user notifications and alerts."""
    return jsonify([
        {"id": 1, "title": "Moon enters Taurus", "body": "An emotionally stable and grounding period begins.", "type": "transit", "time": "1 hour ago"},
        {"id": 2, "title": "Abhijit Muhurta Active", "body": "Perfect time to start new ventures (11:58 AM - 12:49 PM).", "type": "muhurta", "time": "Just now"},
        {"id": 3, "title": "Pro Subscription Expiring", "body": "Your Pro plan expires in 3 days. Renew now for uninterrupted access.", "type": "account", "time": "1 day ago"}
    ])

@content_bp.route("/muhurat", methods=["GET"])
def get_muhurat():
    """Retrieve highly detailed mathematical Muhurat timing calculations."""
    from app.services.muhurat_engine import MuhuratEngine
    
    date_str = request.args.get('date', datetime.now().strftime("%Y-%m-%d"))
    lat = float(request.args.get('latitude', 28.6139))
    lon = float(request.args.get('longitude', 77.2090))
    tz = float(request.args.get('timezone', 5.5))
    
    try:
        engine = MuhuratEngine(lat=lat, lon=lon, tz=tz)
        data = engine.get_full_muhurat(date_str)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@content_bp.route("/muhurat/month", methods=["GET"])
def get_muhurat_month():
    """Retrieve auspicious dates for a given month and year using MuhuratEngine logic."""
    from app.services.muhurat_engine import MuhuratEngine
    import calendar
    
    year = int(request.args.get('year', datetime.now().year))
    month = int(request.args.get('month', datetime.now().month))
    lat = float(request.args.get('latitude', 28.6139))
    lon = float(request.args.get('longitude', 77.2090))
    tz = float(request.args.get('timezone', 5.5))
    
    auspicious_dates = []
    num_days = calendar.monthrange(year, month)[1]
    
    try:
        engine = MuhuratEngine(lat=lat, lon=lon, tz=tz)
        for day in range(1, num_days + 1):
            date_str = f"{year}-{month:02d}-{day:02d}"
            # For monthly overview, just a quick calculation is enough.
            # Calling full get_full_muhurat for 30 days is too slow.
            # We'll use the internal calculation logic.
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            import swisseph as swe
            jd_ut = swe.julday(dt.year, dt.month, dt.day, 0.0)
            res_rise = swe.rise_trans(jd_ut, swe.SUN, swe.CALC_RISE, engine.geopos)
            rise_jd = res_rise[1][0]
            sun_lon = swe.calc_ut(rise_jd, swe.SUN)[0][0]
            moon_lon = swe.calc_ut(rise_jd, swe.MOON)[0][0]
            
            tithi_val = (moon_lon - sun_lon) % 360
            tithi_index = int(tithi_val / 12.0)
            nak_index = int((moon_lon % 360) / (360.0 / 27.0))
            
            if tithi_index not in [3, 8, 13, 14, 29] and nak_index not in [8, 9, 10]:
                auspicious_dates.append(date_str)
                
        return jsonify({
            "year": year,
            "month": month,
            "auspicious_dates": auspicious_dates
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
