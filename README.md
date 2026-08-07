# 🌟 AstroTalk Vedic & AI Kundli Backend (Pure Python Flask)

A modular, production-grade **Flask 3.x** backend powering the **AstroTalk** application. Built with high-precision Vedic astrological calculation engines, 36 Guna Ashtakoota Milan, live Panchanga, planetary ephemeris, real-time Gochara transits, AI consultation, JWT authentication, and PDF report generation.

---

## ⚡ Quick Start

### 1. Activate Virtual Environment & Run

```bash
cd /Users/apple/Desktop/Astrotalk_phase_2_with_flutter/Astrotalk_phase_2_backend

# Activate venv
source venv/bin/activate

# Run Flask server
python run.py
```

The Flask server will start at `http://0.0.0.0:5000` (or `http://127.0.0.1:5000`).

### 2. Status & Health
- **Root**: `http://127.0.0.1:5000/`
- **Health Check**: `http://127.0.0.1:5000/health`
- **API v1 Base**: `http://127.0.0.1:5000/api/v1`

---

## 📁 Project Architecture

```
Astrotalk_phase_2_backend/
├── venv/                       # Isolated Python Virtual Environment
├── requirements.txt            # Pure Flask dependencies (Flask, Flask-CORS, PyJWT, bcrypt, reportlab, etc.)
├── .env.example                # Environment variables template
├── run.py                      # Pure Flask application runner
├── app/
│   ├── __init__.py             # Flask create_app() factory, CORS setup, Blueprint registrations
│   ├── core/
│   │   ├── config.py           # Application Configuration
│   │   └── security.py         # Bcrypt hashing & PyJWT token generator
│   ├── services/
│   │   ├── vedic_engine.py     # Kundli D1, Planet positions, Dignities, Vimshottari Dasha, SAV
│   │   ├── panchang_engine.py  # Tithi, Nakshatra, Yoga, Karana, Rahu Kaal, Abhijit Muhurta
│   │   ├── matching_engine.py  # 36 Guna Ashtakoota Milan & Manglik Dosh Analysis
│   │   ├── ephemeris_engine.py # Astronomical Ephemeris & Ayanamsa offsets (Lahiri, KP, Raman)
│   │   └── ai_astro_engine.py  # AI Astrologer Consultation & Predictions
│   ├── api/v1/
│   │   ├── auth.py             # User Register, Login, JWT Profile
│   │   ├── horoscope.py        # Kundli calculation, Planetary states, Dasha, Ashtakvarga
│   │   ├── panchanga.py        # Live daily Panchanga, Muhurtas, Sunrise/Sunset
│   │   ├── matching.py         # Ashtakoota 36 Guna Milan & Manglik match verification
│   │   ├── gochara.py          # Daily planetary transits
│   │   ├── ephemeris.py        # Astronomical planetary ephemeris tables
│   │   ├── ayanamsa.py         # Lahiri, KP, Raman Ayanamsa calculations
│   │   ├── places.py           # Geocoding & City coordinates database
│   │   ├── ai_astro.py         # AI Astrologer chat & predictions
│   │   └── reports.py          # PDF report generators (Kundli & Milan PDFs)
│   └── utils/
│       └── constants.py        # 12 Zodiac signs, 27 Nakshatras, 9 Grahas, Yogas, Cities DB
└── tests/
    └── test_api.py             # Flask TestClient automated test suite (14/14 passed)
```

---

## 📡 Complete API Endpoints Reference

### 1. 🔮 Horoscope & Kundli (`/api/v1/horoscope`)
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/horoscope/kundli` | Generate full Janam Kundli (D1 chart, planets, dasha, SAV) |
| `GET` | `/api/v1/horoscope/sample` | Instant preview sample Kundli data for UI testing |
| `POST` | `/api/v1/horoscope/planets` | Isolated planetary positions, nakshatras, and dignities |
| `POST` | `/api/v1/horoscope/dasha` | 120-year Vimshottari Mahadasha timeline |
| `POST` | `/api/v1/horoscope/ashtakvarga` | Sarvashtakvarga (SAV) points for all 12 houses |

### 2. 📅 Panchanga & Muhurta (`/api/v1/panchang`)
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/panchang/today` | Real-time live Panchanga for current location |
| `POST` | `/api/v1/panchang/daily` | Hindu Panchanga for custom date and coordinates |
| `GET` | `/api/v1/panchang/muhurta` | Abhijit Muhurta, Rahu Kaal, Yamaganda, Gulika Kaal |

### 3. 💍 Kundli Matching (Milan) (`/api/v1/matching`)
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/matching/ashtakoota` | 36 Guna Ashtakoota Milan + Manglik Analysis |
| `GET` | `/api/v1/matching/sample` | Sample bride & groom compatibility report |

### 4. 🪐 Gochara Transits (`/api/v1/gochara`)
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/gochara/daily` | Current planetary transits and live ticker pills |

### 5. 🔭 Ephemeris & Ayanamsa (`/api/v1/ephemeris` & `/api/v1/ayanamsa`)
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/ephemeris/calculate` | Astronomical planetary degrees & Julian Day |
| `GET` | `/api/v1/ayanamsa/calculate` | Lahiri, KP, Raman, Yukteshwar Ayanamsa offsets |

### 6. 📍 Places & Geocoding (`/api/v1/places`)
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/places/search?query=delhi` | Search cities with coordinates and timezones |
| `GET` | `/api/v1/places/popular` | Pre-configured list of popular spiritual & world cities |

### 7. 🤖 AI Astrologer (`/api/v1/ai-astro`)
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/ai-astro/chat` | AI consultation on career, relationship, finances |

### 8. 📄 PDF Reports (`/api/v1/reports`)
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/reports/kundli-pdf` | Stream HD Janam Kundli PDF document |
| `POST` | `/api/v1/reports/matching-pdf` | Stream Ashtakoota Milan PDF document |

### 9. 🔐 Authentication (`/api/v1/auth`)
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/auth/register` | Register new user account |
| `POST` | `/api/v1/auth/login` | Login and obtain JWT token |
| `GET` | `/api/v1/auth/me` | Retrieve authenticated profile |

---

## 📱 Flutter Integration Example

In your Flutter app (`http` or `dio` package):

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;

class AstroApiService {
  // Use http://10.0.2.2:5000 for Android Emulator, or http://127.0.0.1:5000 for iOS/Web
  static const String baseUrl = 'http://127.0.0.1:5000/api/v1';

  // 1. Fetch Today's Live Panchang
  static Future<Map<String, dynamic>> fetchLivePanchang() async {
    final response = await http.get(Uri.parse('$baseUrl/panchang/today'));
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    throw Exception('Failed to load Panchang');
  }

  // 2. Calculate Janam Kundli
  static Future<Map<String, dynamic>> calculateKundli({
    required String name,
    required String dob, // YYYY-MM-DD
    required String tob, // HH:MM
    required String pob,
    double latitude = 28.6139,
    double longitude = 77.2090,
    double timezone = 5.5,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/horoscope/kundli'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'name': name,
        'date_of_birth': dob,
        'time_of_birth': tob,
        'place_of_birth': pob,
        'latitude': latitude,
        'longitude': longitude,
        'timezone': timezone,
      }),
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    throw Exception('Failed to calculate Kundli');
  }
}
```

---

## 🧪 Running Tests

Execute the automated test suite with pytest:

```bash
./venv/bin/pytest tests/test_api.py -v
```
