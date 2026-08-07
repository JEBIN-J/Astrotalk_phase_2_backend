"""Vedic Astrology Constants and Astronomical Data Tables."""

# 12 Vedic Rashis (Zodiac Signs)
ZODIAC_SIGNS = [
    {
        "index": 1,
        "name": "Aries",
        "sanskrit": "Mesha (मेष)",
        "hindi": "मेष",
        "lord": "Mars",
        "element": "Fire",
        "quality": "Movable",
        "symbol": "Ram",
        "color": "#EF4444"
    },
    {
        "index": 2,
        "name": "Taurus",
        "sanskrit": "Vrishabha (वृषभ)",
        "hindi": "वृषभ",
        "lord": "Venus",
        "element": "Earth",
        "quality": "Fixed",
        "symbol": "Bull",
        "color": "#3B82F6"
    },
    {
        "index": 3,
        "name": "Gemini",
        "sanskrit": "Mithuna (मिथुन)",
        "hindi": "मिथुन",
        "lord": "Mercury",
        "element": "Air",
        "quality": "Dual",
        "symbol": "Twins",
        "color": "#10B981"
    },
    {
        "index": 4,
        "name": "Cancer",
        "sanskrit": "Karkata (कर्क)",
        "hindi": "कर्क",
        "lord": "Moon",
        "element": "Water",
        "quality": "Movable",
        "symbol": "Crab",
        "color": "#6366F1"
    },
    {
        "index": 5,
        "name": "Leo",
        "sanskrit": "Simha (सिंह)",
        "hindi": "सिंह",
        "lord": "Sun",
        "element": "Fire",
        "quality": "Fixed",
        "symbol": "Lion",
        "color": "#F59E0B"
    },
    {
        "index": 6,
        "name": "Virgo",
        "sanskrit": "Kanya (कन्या)",
        "hindi": "कन्या",
        "lord": "Mercury",
        "element": "Earth",
        "quality": "Dual",
        "symbol": "Maiden",
        "color": "#059669"
    },
    {
        "index": 7,
        "name": "Libra",
        "sanskrit": "Tula (तुला)",
        "hindi": "तुला",
        "lord": "Venus",
        "element": "Air",
        "quality": "Movable",
        "symbol": "Scales",
        "color": "#EC4899"
    },
    {
        "index": 8,
        "name": "Scorpio",
        "sanskrit": "Vrishchika (वृश्चिक)",
        "hindi": "वृश्चिक",
        "lord": "Mars",
        "element": "Water",
        "quality": "Fixed",
        "symbol": "Scorpion",
        "color": "#DC2626"
    },
    {
        "index": 9,
        "name": "Sagittarius",
        "sanskrit": "Dhanu (धनु)",
        "hindi": "धनु",
        "lord": "Jupiter",
        "element": "Fire",
        "quality": "Dual",
        "symbol": "Archer",
        "color": "#8B5CF6"
    },
    {
        "index": 10,
        "name": "Capricorn",
        "sanskrit": "Makara (मकर)",
        "hindi": "मकर",
        "lord": "Saturn",
        "element": "Earth",
        "quality": "Movable",
        "symbol": "Sea-Goat",
        "color": "#475569"
    },
    {
        "index": 11,
        "name": "Aquarius",
        "sanskrit": "Kumbha (कुम्भ)",
        "hindi": "कुम्भ",
        "lord": "Saturn",
        "element": "Air",
        "quality": "Fixed",
        "symbol": "Water-Bearer",
        "color": "#2563EB"
    },
    {
        "index": 12,
        "name": "Pisces",
        "sanskrit": "Meena (मीन)",
        "hindi": "मीन",
        "lord": "Jupiter",
        "element": "Water",
        "quality": "Dual",
        "symbol": "Fishes",
        "color": "#0D9488"
    }
]

# 27 Vedic Nakshatras (Lunar Mansions) with Ashtakoota properties
NAKSHATRAS = [
    {"index": 1, "name": "Ashwini", "lord": "Ketu", "gana": "Deva", "yoni": "Horse (Ashwa)", "varna": "Vaishya", "vashya": "Chatushpada", "nadi": "Adi (Vata)"},
    {"index": 2, "name": "Bharani", "lord": "Venus", "gana": "Manushya", "yoni": "Elephant (Gaja)", "varna": "Mleccha", "vashya": "Manava", "nadi": "Madhya (Pitta)"},
    {"index": 3, "name": "Krittika", "lord": "Sun", "gana": "Rakshasa", "yoni": "Sheep (Mesha)", "varna": "Brahmin", "vashya": "Chatushpada", "nadi": "Antya (Kapha)"},
    {"index": 4, "name": "Rohini", "lord": "Moon", "gana": "Manushya", "yoni": "Serpent (Sarpa)", "varna": "Shudra", "vashya": "Chatushpada", "nadi": "Antya (Kapha)"},
    {"index": 5, "name": "Mrigashira", "lord": "Mars", "gana": "Deva", "yoni": "Serpent (Sarpa)", "varna": "Vaishya", "vashya": "Chatushpada", "nadi": "Madhya (Pitta)"},
    {"index": 6, "name": "Ardra", "lord": "Rahu", "gana": "Manushya", "yoni": "Dog (Shwana)", "varna": "Shudra", "vashya": "Manava", "nadi": "Adi (Vata)"},
    {"index": 7, "name": "Punarvasu", "lord": "Jupiter", "gana": "Deva", "yoni": "Cat (Marjara)", "varna": "Vaishya", "vashya": "Manava", "nadi": "Adi (Vata)"},
    {"index": 8, "name": "Pushya", "lord": "Saturn", "gana": "Deva", "yoni": "Goat (Aja)", "varna": "Kshatriya", "vashya": "Jalachara", "nadi": "Madhya (Pitta)"},
    {"index": 9, "name": "Ashlesha", "lord": "Mercury", "gana": "Rakshasa", "yoni": "Cat (Marjara)", "varna": "Mleccha", "vashya": "Keeta", "nadi": "Antya (Kapha)"},
    {"index": 10, "name": "Magha", "lord": "Ketu", "gana": "Rakshasa", "yoni": "Rat (Mooshika)", "varna": "Shudra", "vashya": "Chatushpada", "nadi": "Antya (Kapha)"},
    {"index": 11, "name": "Purva Phalguni", "lord": "Venus", "gana": "Manushya", "yoni": "Rat (Mooshika)", "varna": "Brahmin", "vashya": "Manava", "nadi": "Madhya (Pitta)"},
    {"index": 12, "name": "Uttara Phalguni", "lord": "Sun", "gana": "Manushya", "yoni": "Cow (Gau)", "varna": "Kshatriya", "vashya": "Manava", "nadi": "Adi (Vata)"},
    {"index": 13, "name": "Hasta", "lord": "Mercury", "gana": "Deva", "yoni": "Buffalo (Mahisha)", "varna": "Vaishya", "vashya": "Manava", "nadi": "Adi (Vata)"},
    {"index": 14, "name": "Chitra", "lord": "Mars", "gana": "Rakshasa", "yoni": "Tiger (Vyaghra)", "varna": "Shudra", "vashya": "Manava", "nadi": "Madhya (Pitta)"},
    {"index": 15, "name": "Swati", "lord": "Rahu", "gana": "Deva", "yoni": "Buffalo (Mahisha)", "varna": "Mleccha", "vashya": "Manava", "nadi": "Antya (Kapha)"},
    {"index": 16, "name": "Vishakha", "lord": "Jupiter", "gana": "Rakshasa", "yoni": "Tiger (Vyaghra)", "varna": "Mleccha", "vashya": "Manava", "nadi": "Antya (Kapha)"},
    {"index": 17, "name": "Anuradha", "lord": "Saturn", "gana": "Deva", "yoni": "Deer (Mriga)", "varna": "Shudra", "vashya": "Keeta", "nadi": "Madhya (Pitta)"},
    {"index": 18, "name": "Jyeshtha", "lord": "Mercury", "gana": "Rakshasa", "yoni": "Deer (Mriga)", "varna": "Vaishya", "vashya": "Keeta", "nadi": "Adi (Vata)"},
    {"index": 19, "name": "Mula", "lord": "Ketu", "gana": "Rakshasa", "yoni": "Dog (Shwana)", "varna": "Kshatriya", "vashya": "Chatushpada", "nadi": "Adi (Vata)"},
    {"index": 20, "name": "Purva Ashadha", "lord": "Venus", "gana": "Manushya", "yoni": "Monkey (Vanara)", "varna": "Brahmin", "vashya": "Chatushpada", "nadi": "Madhya (Pitta)"},
    {"index": 21, "name": "Uttara Ashadha", "lord": "Sun", "gana": "Manushya", "yoni": "Mongoose (Nakula)", "varna": "Kshatriya", "vashya": "Chatushpada", "nadi": "Antya (Kapha)"},
    {"index": 22, "name": "Shravana", "lord": "Moon", "gana": "Deva", "yoni": "Monkey (Vanara)", "varna": "Mleccha", "vashya": "Jalachara", "nadi": "Antya (Kapha)"},
    {"index": 23, "name": "Dhanishta", "lord": "Mars", "gana": "Rakshasa", "yoni": "Lion (Simha)", "varna": "Shudra", "vashya": "Chatushpada", "nadi": "Madhya (Pitta)"},
    {"index": 24, "name": "Shatabhisha", "lord": "Rahu", "gana": "Rakshasa", "yoni": "Horse (Ashwa)", "varna": "Vaishya", "vashya": "Jalachara", "nadi": "Adi (Vata)"},
    {"index": 25, "name": "Purva Bhadrapada", "lord": "Jupiter", "gana": "Manushya", "yoni": "Lion (Simha)", "varna": "Brahmin", "vashya": "Manava", "nadi": "Adi (Vata)"},
    {"index": 26, "name": "Uttara Bhadrapada", "lord": "Saturn", "gana": "Manushya", "yoni": "Cow (Gau)", "varna": "Kshatriya", "vashya": "Jalachara", "nadi": "Madhya (Pitta)"},
    {"index": 27, "name": "Revati", "lord": "Mercury", "gana": "Deva", "yoni": "Elephant (Gaja)", "varna": "Shudra", "vashya": "Jalachara", "nadi": "Antya (Kapha)"}
]

# 9 Vedic Grahas (Planets) & Vimshottari Mahadasha Duration in Years
PLANETS_INFO = {
    "Sun": {"sanskrit": "Surya (सूर्य)", "years": 6, "exaltation_sign": 1, "debilitation_sign": 7, "moolatrikona": 5, "own_signs": [5], "color": "#F59E0B"},
    "Moon": {"sanskrit": "Chandra (चन्द्र)", "years": 10, "exaltation_sign": 2, "debilitation_sign": 8, "moolatrikona": 2, "own_signs": [4], "color": "#3B82F6"},
    "Mars": {"sanskrit": "Mangal (मंगल)", "years": 7, "exaltation_sign": 10, "debilitation_sign": 4, "moolatrikona": 1, "own_signs": [1, 8], "color": "#EF4444"},
    "Rahu": {"sanskrit": "Rahu (राहु)", "years": 18, "exaltation_sign": 2, "debilitation_sign": 8, "moolatrikona": 11, "own_signs": [11], "color": "#64748B"},
    "Jupiter": {"sanskrit": "Guru (बृहस्पति)", "years": 16, "exaltation_sign": 4, "debilitation_sign": 10, "moolatrikona": 9, "own_signs": [9, 12], "color": "#FBBF24"},
    "Saturn": {"sanskrit": "Shani (शनि)", "years": 19, "exaltation_sign": 7, "debilitation_sign": 1, "moolatrikona": 11, "own_signs": [10, 11], "color": "#4338CA"},
    "Mercury": {"sanskrit": "Budha (बुध)", "years": 17, "exaltation_sign": 6, "debilitation_sign": 12, "moolatrikona": 6, "own_signs": [3, 6], "color": "#10B981"},
    "Ketu": {"sanskrit": "Ketu (केतु)", "years": 7, "exaltation_sign": 8, "debilitation_sign": 2, "moolatrikona": 9, "own_signs": [8], "color": "#94A3B8"},
    "Venus": {"sanskrit": "Shukra (शुक्र)", "years": 20, "exaltation_sign": 12, "debilitation_sign": 6, "moolatrikona": 7, "own_signs": [2, 7], "color": "#EC4899"}
}

# Vimshottari Mahadasha Sequence (120 years total cycle)
VIMSHOTTARI_SEQUENCE = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]

# 30 Tithis
TITHI_NAMES = [
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima",
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Amavasya"
]

# 27 Yogas
YOGA_NAMES = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana",
    "Atiganda", "Sukarma", "Dhriti", "Shula", "Ganda",
    "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra",
    "Siddhi", "Vyatipata", "Variyan", "Parigha", "Shiva",
    "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma",
    "Indra", "Vaidhriti"
]

# 11 Karanas (7 Movable + 4 Fixed)
KARANA_NAMES = [
    "Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti (Bhadra)",
    "Shakuni", "Chatushpada", "Naga", "Kintughna"
]

# Popular Indian & World Cities for Geocoding
POPULAR_CITIES = [
    {"name": "New Delhi", "state": "Delhi", "country": "India", "latitude": 28.6139, "longitude": 77.2090, "timezone": 5.5},
    {"name": "Mumbai", "state": "Maharashtra", "country": "India", "latitude": 19.0760, "longitude": 72.8777, "timezone": 5.5},
    {"name": "Bengaluru", "state": "Karnataka", "country": "India", "latitude": 12.9716, "longitude": 77.5946, "timezone": 5.5},
    {"name": "Chennai", "state": "Tamil Nadu", "country": "India", "latitude": 13.0827, "longitude": 80.2707, "timezone": 5.5},
    {"name": "Kanyakumari", "state": "Tamil Nadu", "country": "India", "latitude": 8.0883, "longitude": 77.5385, "timezone": 5.5},
    {"name": "Tirunelveli", "state": "Tamil Nadu", "country": "India", "latitude": 8.7139, "longitude": 77.7567, "timezone": 5.5},
    {"name": "Madurai", "state": "Tamil Nadu", "country": "India", "latitude": 9.9252, "longitude": 78.1198, "timezone": 5.5},
    {"name": "Coimbatore", "state": "Tamil Nadu", "country": "India", "latitude": 11.0168, "longitude": 76.9558, "timezone": 5.5},
    {"name": "Thiruvananthapuram", "state": "Kerala", "country": "India", "latitude": 8.5241, "longitude": 76.9366, "timezone": 5.5},
    {"name": "Kochi", "state": "Kerala", "country": "India", "latitude": 9.9312, "longitude": 76.2673, "timezone": 5.5},
    {"name": "Kolkata", "state": "West Bengal", "country": "India", "latitude": 22.5726, "longitude": 88.3639, "timezone": 5.5},
    {"name": "Hyderabad", "state": "Telangana", "country": "India", "latitude": 17.3850, "longitude": 78.4867, "timezone": 5.5},
    {"name": "Ahmedabad", "state": "Gujarat", "country": "India", "latitude": 23.0225, "longitude": 72.5714, "timezone": 5.5},
    {"name": "Pune", "state": "Maharashtra", "country": "India", "latitude": 18.5204, "longitude": 73.8567, "timezone": 5.5},
    {"name": "Jaipur", "state": "Rajasthan", "country": "India", "latitude": 26.9124, "longitude": 75.7873, "timezone": 5.5},
    {"name": "Varanasi", "state": "Uttar Pradesh", "country": "India", "latitude": 25.3176, "longitude": 82.9739, "timezone": 5.5},
    {"name": "Haridwar", "state": "Uttarakhand", "country": "India", "latitude": 29.9457, "longitude": 78.1642, "timezone": 5.5},
    {"name": "Ujjain", "state": "Madhya Pradesh", "country": "India", "latitude": 23.1765, "longitude": 75.7885, "timezone": 5.5},
    {"name": "Lucknow", "state": "Uttar Pradesh", "country": "India", "latitude": 26.8467, "longitude": 80.9462, "timezone": 5.5},
    {"name": "Patna", "state": "Bihar", "country": "India", "latitude": 25.5941, "longitude": 85.1376, "timezone": 5.5},
    {"name": "London", "state": "England", "country": "United Kingdom", "latitude": 51.5074, "longitude": -0.1278, "timezone": 0.0},
    {"name": "New York", "state": "New York", "country": "United States", "latitude": 40.7128, "longitude": -74.0060, "timezone": -5.0},
    {"name": "Dubai", "state": "Dubai", "country": "United Arab Emirates", "latitude": 25.2048, "longitude": 55.2708, "timezone": 4.0},
    {"name": "Singapore", "state": "Singapore", "country": "Singapore", "latitude": 1.3521, "longitude": 103.8198, "timezone": 8.0}
]

