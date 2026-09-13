import yaml
import os

swagger = {
    "openapi": "3.0.0",
    "info": {
        "title": "AstroTalk Phase 2 API",
        "description": "API Documentation for AstroTalk Backend.",
        "version": "1.0.0"
    },
    "servers": [
        {
            "url": "http://localhost:5000",
            "description": "Local server"
        }
    ],
    "components": {
        "securitySchemes": {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            }
        },
        "schemas": {
            "HoroscopeRequest": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "example": "Rahul Sharma"},
                    "date_of_birth": {"type": "string", "example": "1995-08-15"},
                    "time_of_birth": {"type": "string", "example": "06:30"},
                    "place_of_birth": {"type": "string", "example": "New Delhi, India"},
                    "latitude": {"type": "number", "example": 28.6139},
                    "longitude": {"type": "number", "example": 77.2090},
                    "timezone": {"type": "number", "example": 5.5}
                }
            }
        }
    },
    "paths": {}
}

endpoints = {
    "/api/v1/horoscope/kundli": {
        "tag": "Vedic",
        "summary": "Full Janam Kundli",
        "desc": "Returns all Vedic details."
    },
    "/api/v1/horoscope/divisional": {
        "tag": "Vedic",
        "summary": "Divisional Charts (Rashi, Navamsa, Bhava, etc.)",
        "desc": "Returns all 16 charts."
    },
    "/api/v1/horoscope/planets": {
        "tag": "Vedic",
        "summary": "Planetary Info",
        "desc": "Returns exact planetary degrees."
    },
    "/api/v1/horoscope/upagrahas": {
        "tag": "Vedic",
        "summary": "Upagrahas",
        "desc": "Returns Upagrahas."
    },
    "/api/v1/horoscope/arudhas": {
        "tag": "Vedic",
        "summary": "Arudhas",
        "desc": "Returns Arudha Padas."
    },
    "/api/v1/horoscope/dasha": {
        "tag": "Dasha",
        "summary": "Dasha timeline",
        "desc": "Returns Dasha timeline."
    },
    "/api/v1/horoscope/ashtakvarga": {
        "tag": "Ashtakvarga",
        "summary": "Ashtakvarga",
        "desc": "Returns Ashtakvarga points."
    },
    "/api/v1/horoscope/jaimini": {
        "tag": "Jaimini",
        "summary": "Jaimini Astrology",
        "desc": "Returns Jaimini details."
    },
    "/api/v1/horoscope/bnn": {
        "tag": "BNN",
        "summary": "Bhrigu Nandi Nadi (BNN)",
        "desc": "Returns BNN linkages."
    },
    "/api/v1/horoscope/lal-kitab": {
        "tag": "Lal Kitab",
        "summary": "Lal Kitab",
        "desc": "Returns Lal Kitab details."
    },
    "/api/v1/horoscope/kota-chakra": {
        "tag": "Kota Chakra",
        "summary": "Kota Chakra",
        "desc": "Returns Kota Chakra details."
    }
}

for path, info in endpoints.items():
    swagger["paths"][path] = {
        "post": {
            "tags": [info["tag"]],
            "summary": info["summary"],
            "description": info["desc"],
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/HoroscopeRequest"}
                        if path != "/api/v1/horoscope/dasha"
                        else {
                            "allOf": [
                                {"$ref": "#/components/schemas/HoroscopeRequest"},
                                {
                                    "type": "object",
                                    "properties": {
                                        "dasha_type": {"type": "string", "example": "Vimshottari Dasha"}
                                    }
                                }
                            ]
                        }
                    }
                }
            },
            "responses": {"200": {"description": "Successful response"}}
        }
    }

# Also add Places and Content back, just in case
swagger["paths"]["/api/v1/places/search"] = {
    "get": {
        "tags": ["Places"],
        "summary": "Search cities",
        "parameters": [{"name": "q", "in": "query", "required": True, "schema": {"type": "string"}}],
        "responses": {"200": {"description": "List of cities"}}
    }
}
swagger["paths"]["/api/v1/content/quotes"] = {
    "get": {
        "tags": ["Content"],
        "summary": "Get astrology quotes",
        "responses": {"200": {"description": "List of quotes"}}
    }
}

os.makedirs("app/static", exist_ok=True)
with open("app/static/swagger.yaml", "w") as f:
    yaml.dump(swagger, f, sort_keys=False, allow_unicode=True)

print("Swagger YAML with exact tags generated successfully!")
