"""Automated Test Suite for AstroTalk Pure Flask Backend."""
import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "online"
    assert data["framework"] == "Flask 3.x"


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "healthy"


def test_auth_flow(client):
    # 1. Register
    reg_payload = {
        "name": "Test Astrologer",
        "email": "astrologer_flask@example.com",
        "password": "securepassword123",
        "phone": "+919876543210"
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code in [201, 400]
    
    # 2. Login
    login_payload = {
        "email": "astrologer_flask@example.com",
        "password": "securepassword123"
    }
    login_res = client.post("/api/v1/auth/login", json=login_payload)
    if login_res.status_code == 200:
        token = login_res.get_json()["access_token"]
        # 3. Profile
        me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me_res.status_code == 200
        assert me_res.get_json()["email"] == "astrologer_flask@example.com"


def test_horoscope_sample_endpoint(client):
    response = client.get("/api/v1/horoscope/sample")
    assert response.status_code == 200
    data = response.get_json()
    assert data["person_name"] == "Rahul Sharma"
    assert len(data["planets"]) == 10  # Ascendant + 9 Planets
    assert len(data["houses"]) == 12
    assert "current_running_dasha" in data
    assert "ashtakvarga" in data


def test_horoscope_kundli_calculation(client):
    payload = {
        "name": "Aarav Gupta",
        "date_of_birth": "1998-11-20",
        "time_of_birth": "14:15",
        "place_of_birth": "Mumbai, India",
        "latitude": 19.0760,
        "longitude": 72.8777,
        "timezone": 5.5
    }
    response = client.post("/api/v1/horoscope/kundli", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["person_name"] == "Aarav Gupta"
    assert data["moon_sign_rashi"] is not None
    assert len(data["vimshottari_dasha_timeline"]) > 0


def test_panchang_endpoints(client):
    # 1. Today
    res_today = client.get("/api/v1/panchang/today")
    assert res_today.status_code == 200
    data = res_today.get_json()
    assert "tithi" in data
    assert "nakshatra" in data
    assert "yoga" in data
    assert "karana" in data
    assert "abhijit_muhurta" in data
    assert "rahu_kaal" in data

    # 2. Daily with custom date
    payload = {
        "date": "2026-10-15",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "timezone": 5.5,
        "place_name": "New Delhi"
    }
    res_daily = client.post("/api/v1/panchang/daily", json=payload)
    assert res_daily.status_code == 200
    assert res_daily.get_json()["date"] == "2026-10-15"


def test_matchmaking_sample(client):
    response = client.get("/api/v1/matching/sample")
    assert response.status_code == 200
    data = response.get_json()
    assert data["max_score"] == 36.0
    assert 0 <= data["total_score"] <= 36.0
    assert len(data["kootas"]) == 8
    assert "manglik_analysis" in data


def test_matchmaking_calculation(client):
    payload = {
        "boy": {
            "name": "Rohan Verma",
            "date_of_birth": "1993-05-10",
            "time_of_birth": "08:30",
            "place_of_birth": "Delhi",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "timezone": 5.5
        },
        "girl": {
            "name": "Pooja Sharma",
            "date_of_birth": "1995-12-18",
            "time_of_birth": "11:20",
            "place_of_birth": "Jaipur",
            "latitude": 26.9124,
            "longitude": 75.7873,
            "timezone": 5.5
        }
    }
    response = client.post("/api/v1/matching/ashtakoota", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["boy_name"] == "Rohan Verma"
    assert data["girl_name"] == "Pooja Sharma"
    assert len(data["kootas"]) == 8


def test_gochara_transits(client):
    response = client.get("/api/v1/gochara/daily")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data["planetary_transits"]) >= 9
    assert len(data["live_ticker_items"]) >= 9


def test_ephemeris_calculation(client):
    payload = {
        "date": "2026-08-06",
        "time": "12:00",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "ayanamsa_system": "lahiri"
    }
    response = client.post("/api/v1/ephemeris/calculate", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert len(data["planets"]) >= 9
    assert "ayanamsa_value" in data


def test_ayanamsa_endpoint(client):
    response = client.get("/api/v1/ayanamsa/calculate?year=2026")
    assert response.status_code == 200
    data = response.get_json()
    assert data["year"] == 2026
    assert "lahiri_ayanamsa" in data
    assert "kp_ayanamsa" in data


def test_places_search(client):
    # 1. Search existing city
    res_delhi = client.get("/api/v1/places/search?query=delhi")
    assert res_delhi.status_code == 200
    assert len(res_delhi.get_json()["results"]) > 0

    # 2. Popular cities
    res_pop = client.get("/api/v1/places/popular")
    assert res_pop.status_code == 200
    assert len(res_pop.get_json()) >= 10


def test_ai_astro_chat(client):
    payload = {
        "question": "How will my career and promotion progress this year?",
        "category": "career"
    }
    response = client.post("/api/v1/ai-astro/chat", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert len(data["predictions"]) > 0
    assert len(data["remedies"]) > 0
    assert "lucky_gemstone" in data


def test_pdf_report_generation(client):
    payload = {
        "name": "Rahul Sharma",
        "date_of_birth": "1995-08-15",
        "time_of_birth": "06:30",
        "place_of_birth": "New Delhi, India",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "timezone": 5.5
    }
    response = client.post("/api/v1/reports/kundli-pdf", json=payload)
    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert len(response.data) > 1000  # Non-empty binary PDF stream
