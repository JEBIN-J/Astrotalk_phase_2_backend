"""AstroTalk Backend Application Entrypoint."""
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.api.v1.api_router import api_router

tags_metadata = [
    {"name": "Authentication & User", "description": "User registration, login, JWT token auth, and user profiles."},
    {"name": "Horoscope & Kundli", "description": "D1 Natal Kundli, planetary dignities, 120-year Vimshottari Mahadasha, and Ashtakvarga scores."},
    {"name": "Panchanga & Muhurta", "description": "Daily Hindu Panchang, Tithi, Nakshatra, Yoga, Karana, and Shubh/Ashubh Muhurta timings."},
    {"name": "Horoscope Matching (Kundli Milan)", "description": "36 Guna Ashtakoota Milan matching, Manglik Dosha detection, and remedies."},
    {"name": "Gochara (Transits)", "description": "Live planetary transits (Gochara) and daily header ticker pills."},
    {"name": "Ephemeris", "description": "Astronomical planet longitudes, speed, retrograde states, and Julian Day."},
    {"name": "Ayanamsa Calculator", "description": "Lahiri, KP, Raman, and Yukteshwar Ayanamsa calculations."},
    {"name": "Places & Geocoding", "description": "Search cities with accurate geographical coordinates and timezone offsets."},
    {"name": "AI Astrologer & Consultation", "description": "AI-powered Vedic horoscope interpretation and instant question answering."},
    {"name": "PDF Reports", "description": "Generate high-definition downloadable Kundli and Milan PDF documents."},
]

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    🚀 **AstroTalk Vedic & AI Kundli API**
    
    Complete backend suite powering the AstroTalk Flutter mobile and web application.
    Supports Vedic astrology algorithms, Ashtakoota 36 Guna Milan, Live Panchang,
    Planetary Transits, Astronomical Ephemeris, AI consultation, and PDF generation.
    """,
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware (Fully permissive for Flutter Mobile, Web, and Desktop)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    return response


@app.get("/", tags=["Health & Status"])
async def root():
    """Root welcoming endpoint with API status and documentation link."""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "online",
        "documentation": "/docs",
        "redoc": "/redoc",
        "api_v1_root": settings.API_V1_STR
    }


@app.get("/health", tags=["Health & Status"])
async def health_check():
    """Health check endpoint for monitoring uptime."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": settings.APP_VERSION
    }


# Include Master v1 Router
app.include_router(api_router, prefix=settings.API_V1_STR)
