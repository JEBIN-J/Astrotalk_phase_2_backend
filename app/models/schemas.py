from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# --- USER & AUTH SCHEMAS ---
class UserRegister(BaseModel):
    name: str = Field(..., json_schema_extra={"example": "Rahul Sharma"})
    email: str = Field(..., json_schema_extra={"example": "rahul@example.com"})
    password: str = Field(..., min_length=6, json_schema_extra={"example": "password123"})
    phone: Optional[str] = Field(None, json_schema_extra={"example": "+919876543210"})


class UserLogin(BaseModel):
    email: str = Field(..., json_schema_extra={"example": "rahul@example.com"})
    password: str = Field(..., json_schema_extra={"example": "password123"})


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    name: str
    email: str


class UserProfile(BaseModel):
    user_id: str
    name: str
    email: str
    phone: Optional[str] = None
    created_at: str
    saved_kundlis_count: int = 0


# --- ASTROLOGICAL INPUT SCHEMAS ---
class BirthDetailsRequest(BaseModel):
    name: str = Field("Rahul Sharma", description="Person's Full Name", json_schema_extra={"example": "Rahul Sharma"})
    date_of_birth: str = Field("1995-08-15", description="YYYY-MM-DD format", json_schema_extra={"example": "1995-08-15"})
    time_of_birth: str = Field("06:30", description="HH:MM in 24-hour format", json_schema_extra={"example": "06:30"})
    place_of_birth: str = Field("New Delhi, India", description="Birth City / Place", json_schema_extra={"example": "New Delhi, India"})
    latitude: float = Field(28.6139, description="Latitude in decimal degrees", json_schema_extra={"example": 28.6139})
    longitude: float = Field(77.2090, description="Longitude in decimal degrees", json_schema_extra={"example": 77.2090})
    timezone: float = Field(5.5, description="Timezone offset from UTC (e.g., 5.5 for IST)", json_schema_extra={"example": 5.5})
    chart_style: Optional[str] = Field("northIndian", description="northIndian, southIndian, or eastIndian", json_schema_extra={"example": "northIndian"})


# --- HOROSCOPE & KUNDLI SCHEMAS ---
class PlanetPosition(BaseModel):
    name: str
    sanskrit_name: str
    sign: str
    sign_sanskrit: str
    sign_lord: str
    house: int
    degree_formatted: str
    degree_decimal: float
    nakshatra: str
    nakshatra_lord: str
    pada: int
    dignity: str
    is_retrograde: bool
    color: str


class HouseDetail(BaseModel):
    house_number: int
    sign: str
    sign_sanskrit: str
    sign_lord: str
    degree: str
    planets_present: List[str]


class DashaPeriod(BaseModel):
    planet: str
    sanskrit_name: str
    duration_years: int
    start_date: str
    end_date: str
    is_current: bool
    status: str


class AshtakvargaHouse(BaseModel):
    house_number: int
    points: int
    is_benefic: bool
    interpretation: str


class KundliResponse(BaseModel):
    person_name: str
    date_of_birth: str
    time_of_birth: str
    place_of_birth: str
    ascendant_lagna: str
    ascendant_sanskrit: str
    ascendant_degree: str
    moon_sign_rashi: str
    moon_sign_sanskrit: str
    sun_sign: str
    nakshatra: str
    nakshatra_pada: int
    nakshatra_lord: str
    planets: List[PlanetPosition]
    houses: List[HouseDetail]
    current_running_dasha: Dict[str, Any]
    vimshottari_dasha_timeline: List[DashaPeriod]
    ashtakvarga: Dict[str, Any]
    summary_insights: List[Dict[str, str]]


# --- PANCHANGA SCHEMAS ---
class PanchangRequest(BaseModel):
    date: Optional[str] = Field(None, description="Date in YYYY-MM-DD format (defaults to today)", json_schema_extra={"example": "2026-08-06"})
    place_name: Optional[str] = Field("New Delhi", json_schema_extra={"example": "New Delhi"})
    latitude: Optional[float] = Field(28.6139, json_schema_extra={"example": 28.6139})
    longitude: Optional[float] = Field(77.2090, json_schema_extra={"example": 77.2090})
    timezone: Optional[float] = Field(5.5, json_schema_extra={"example": 5.5})


class PanchangElement(BaseModel):
    name: str
    sanskrit_name: str
    number: int
    timing: str
    deity_or_nature: str


class MuhurtaElement(BaseModel):
    name: str
    start_time: str
    end_time: str
    is_auspicious: bool
    description: str


class PanchangResponse(BaseModel):
    date: str
    formatted_date: str
    place: str
    sunrise: str
    sunset: str
    moonrise: str
    moonset: str
    paksha: str
    tithi: PanchangElement
    nakshatra: PanchangElement
    yoga: PanchangElement
    karana: PanchangElement
    rahu_kaal: MuhurtaElement
    abhijit_muhurta: MuhurtaElement
    yamaganda: MuhurtaElement
    gulika_kaal: MuhurtaElement
    sun_sign: str
    moon_sign: str
    daily_insights: List[Dict[str, Any]]


# --- HOROSCOPE MATCHING (MILAN) SCHEMAS ---
class PersonProfile(BaseModel):
    name: str
    date_of_birth: str
    time_of_birth: str
    place_of_birth: str
    latitude: float = 28.6139
    longitude: float = 77.2090
    timezone: float = 5.5


class MatchMakingRequest(BaseModel):
    boy: PersonProfile
    girl: PersonProfile


class KootaScore(BaseModel):
    koota_name: str
    description: str
    max_points: float
    obtained_points: float
    boy_attribute: str
    girl_attribute: str
    is_compatible: bool
    remarks: str


class ManglikAnalysis(BaseModel):
    boy_status: str
    boy_details: str
    boy_is_manglik: bool
    girl_status: str
    girl_details: str
    girl_is_manglik: bool
    is_manglik_match: bool
    verdict: str


class MatchMakingResponse(BaseModel):
    boy_name: str
    girl_name: str
    total_score: float
    max_score: float = 36.0
    percentage: float
    status: str
    recommendation: str
    kootas: List[KootaScore]
    manglik_analysis: ManglikAnalysis
    remedies: List[Dict[str, str]]


# --- GOCHARA (TRANSIT) SCHEMAS ---
class PlanetTransit(BaseModel):
    planet: str
    sanskrit: str
    current_sign: str
    sign_sanskrit: str
    degree: str
    is_retrograde: bool
    transit_start_date: str
    transit_end_date: str
    influence: str
    color: str


class GocharaTransitResponse(BaseModel):
    date: str
    planetary_transits: List[PlanetTransit]
    live_ticker_items: List[str]


# --- EPHEMERIS & AYANAMSA SCHEMAS ---
class EphemerisRequest(BaseModel):
    date: str = Field("2026-08-06", json_schema_extra={"example": "2026-08-06"})
    time: str = Field("12:00", json_schema_extra={"example": "12:00"})
    latitude: float = Field(28.6139, json_schema_extra={"example": 28.6139})
    longitude: float = Field(77.2090, json_schema_extra={"example": 77.2090})
    ayanamsa_system: str = Field("lahiri", json_schema_extra={"example": "lahiri"})


class PlanetEphemerisEntry(BaseModel):
    planet: str
    longitude_degrees: float
    formatted_longitude: str
    sign: str
    speed_deg_per_day: float
    is_retrograde: bool
    nakshatra: str
    pada: int


class EphemerisResponse(BaseModel):
    date: str
    julian_day: float
    ayanamsa_name: str
    ayanamsa_value: str
    ayanamsa_degrees: float
    planets: List[PlanetEphemerisEntry]


class AyanamsaResponse(BaseModel):
    year: int
    lahiri_ayanamsa: str
    kp_ayanamsa: str
    raman_ayanamsa: str
    yukteshwar_ayanamsa: str
    definitions: Dict[str, str]


# --- PLACES / GEOCODING SCHEMAS ---
class PlaceSearchResult(BaseModel):
    name: str
    state: str
    country: str
    latitude: float
    longitude: float
    timezone: float
    formatted_name: str


class PlaceSearchResponse(BaseModel):
    query: str
    total_found: int
    results: List[PlaceSearchResult]


# --- AI ASTROLOGER & CHAT SCHEMAS ---
class AIAstroQueryRequest(BaseModel):
    question: str = Field(..., json_schema_extra={"example": "How will my career and finances be in the next 2 years?"})
    birth_details: Optional[BirthDetailsRequest] = None
    category: Optional[str] = Field("general", json_schema_extra={"example": "career"})


class AIAstroResponse(BaseModel):
    question: str
    category: str
    analysis: str
    astrological_factors: List[str]
    predictions: List[str]
    remedies: List[str]
    lucky_gemstone: str
    lucky_color: str
    lucky_day: str
    auspicious_time: str


# --- TAROT SCHEMAS ---
class TarotReadingRequest(BaseModel):
    question: Optional[str] = Field(None, json_schema_extra={"example": "What should I focus on today?"})
    seed: Optional[str] = Field(None, description="Deterministic seed for reproducing reading")

class AstroTarotRequest(BaseModel):
    question: Optional[str] = Field(None)
    birth_date: str = Field(..., description="YYYY-MM-DD format")
    birth_time: str = Field(..., description="HH:MM in 24-hour format")
    latitude: float = Field(...)
    longitude: float = Field(...)
    timezone: float = Field(...)
    seed: Optional[str] = Field(None)
