"""Master API v1 Router."""
from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.horoscope import router as horoscope_router
from app.api.v1.panchanga import router as panchang_router
from app.api.v1.matching import router as matching_router
from app.api.v1.gochara import router as gochara_router
from app.api.v1.ephemeris import router as ephemeris_router
from app.api.v1.ayanamsa import router as ayanamsa_router
from app.api.v1.places import router as places_router
from app.api.v1.ai_astro import router as ai_astro_router
from app.api.v1.reports import router as reports_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(horoscope_router)
api_router.include_router(panchang_router)
api_router.include_router(matching_router)
api_router.include_router(gochara_router)
api_router.include_router(ephemeris_router)
api_router.include_router(ayanamsa_router)
api_router.include_router(places_router)
api_router.include_router(ai_astro_router)
api_router.include_router(reports_router)
