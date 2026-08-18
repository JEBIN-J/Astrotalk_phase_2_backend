"""Flask Places and City Geocoding Blueprint."""
from flask import Blueprint, jsonify, request
from app.utils.constants import POPULAR_CITIES

places_bp = Blueprint('places', __name__)

@places_bp.route("/search", methods=["GET"])
def search_places():
    """Search for cities, coordinates, and timezone offsets using Open-Meteo API."""
    import requests
    import pytz
    from datetime import datetime

    query = request.args.get("query", "")
    query_lower = query.lower().strip()
    if not query_lower:
        return jsonify({"detail": "Query parameter is required"}), 400
        
    matched = []
    
    # Check popular cities first for instant local resolution
    for city in POPULAR_CITIES:
        if query_lower in city["name"].lower() or query_lower in city["state"].lower() or query_lower in city["country"].lower():
            matched.append({
                "name": city["name"],
                "state": city["state"],
                "country": city["country"],
                "latitude": city["latitude"],
                "longitude": city["longitude"],
                "timezone": city["timezone"],
                "formatted_name": f"{city['name']}, {city['state']}, {city['country']}"
            })
            
    # If not enough local matches, fetch from live Open-Meteo Geocoding API
    if len(matched) < 5:
        try:
            url = f"https://geocoding-api.open-meteo.com/v1/search?name={query}&count=5&language=en&format=json"
            res = requests.get(url, timeout=5).json()
            if "results" in res:
                for r in res["results"]:
                    # Convert IANA timezone string to float offset (e.g. Asia/Kolkata -> 5.5)
                    tz_str = r.get("timezone", "UTC")
                    tz = pytz.timezone(tz_str)
                    offset_seconds = tz.utcoffset(datetime.now()).total_seconds()
                    offset_hours = offset_seconds / 3600.0
                    
                    state = r.get("admin1", r.get("country", "Unknown"))
                    country = r.get("country", "Unknown")
                    name = r.get("name", query.title())
                    
                    # Avoid duplicates from popular cities
                    if not any(m["name"].lower() == name.lower() and m["country"].lower() == country.lower() for m in matched):
                        matched.append({
                            "name": name,
                            "state": state,
                            "country": country,
                            "latitude": round(r.get("latitude", 0.0), 4),
                            "longitude": round(r.get("longitude", 0.0), 4),
                            "timezone": round(offset_hours, 2),
                            "formatted_name": f"{name}, {state}, {country}"
                        })
        except Exception as e:
            pass # Fallback to local matches if API fails
            
    # If absolutely nothing is found and API fails, provide a default fallback
    if not matched:
        matched.append({
            "name": query.title(),
            "state": "Custom Region",
            "country": "India",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "timezone": 5.5,
            "formatted_name": f"{query.title()}, India (Fallback)"
        })

    return jsonify({
        "query": query,
        "total_found": len(matched),
        "results": matched[:10]
    })

@places_bp.route("/popular", methods=["GET"])
def get_popular():
    """Retrieve pre-configured list of popular cities."""
    results = [
        {
            "name": c["name"],
            "state": c["state"],
            "country": c["country"],
            "latitude": c["latitude"],
            "longitude": c["longitude"],
            "timezone": c["timezone"],
            "formatted_name": f"{c['name']}, {c['state']}, {c['country']}"
        }
        for c in POPULAR_CITIES
    ]
    return jsonify(results)
