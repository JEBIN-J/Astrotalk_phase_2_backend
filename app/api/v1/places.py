"""Flask Places and City Geocoding Blueprint."""
from flask import Blueprint, jsonify, request
from app.utils.constants import POPULAR_CITIES

places_bp = Blueprint('places', __name__)

@places_bp.route("/search", methods=["GET"])
def search_places():
    """Search for cities, coordinates, and timezone offsets."""
    query = request.args.get("query", "")
    query_lower = query.lower().strip()
    if not query_lower:
        return jsonify({"detail": "Query parameter is required"}), 400
        
    matched = []
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
            
    if not matched:
        matched.append({
            "name": query.title(),
            "state": "Custom Region",
            "country": "India",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "timezone": 5.5,
            "formatted_name": f"{query.title()}, India"
        })

    return jsonify({
        "query": query,
        "total_found": len(matched),
        "results": matched
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
