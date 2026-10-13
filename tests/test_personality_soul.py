import pytest
from app import create_app
from app.services.personality_soul_calculator import (
    PersonalityNumberCalculator,
    SoulUrgeNumberCalculator,
    PersonalitySoulAnalyzer,
)
from app.services.numerology_repository import NumerologyRepository


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


# =========================================================================
# 1. MANDATORY FIXTURE TESTS (SECTION 8)
# =========================================================================

def test_mandatory_elizabeth_anne_taylor_fixture():
    """
    ELIZABETH ANNE TAYLOR
    Soul Urge:
      ELIZABETH: E(5) + I(9) + A(1) + E(5) = 20
      ANNE: A(1) + E(5) = 6
      TAYLOR: A(1) + O(6) = 7
      Total: 20 + 6 + 7 = 33 (Master 33 preserved)
    Personality:
      ELIZABETH: L(3) + Z(8) + B(2) + T(2) + H(8) = 23
      ANNE: N(5) + N(5) = 10
      TAYLOR: T(2) + Y(7) + L(3) + R(9) = 21
      Total: 23 + 10 + 21 = 54 -> 5 + 4 = 9
    """
    result = PersonalitySoulAnalyzer.analyze("ELIZABETH ANNE TAYLOR", y_policy="always_consonant")
    
    assert result["personality"]["number"] == 9
    assert result["personality"]["unreduced_sum"] == 54
    assert result["personality"]["is_master_number"] is False
    assert result["personality"]["formula_summary"] == "23 + 10 + 21 = 54"

    assert result["soul_urge"]["number"] == 33
    assert result["soul_urge"]["unreduced_sum"] == 33
    assert result["soul_urge"]["is_master_number"] is True
    assert result["soul_urge"]["formula_summary"] == "20 + 6 + 7 = 33"


def test_elizabeth_anne_taylor_always_vowel_y_policy():
    """
    With Y as a vowel:
    Soul Urge: TAYLOR adds Y(7) -> 14, total = 20 + 6 + 14 = 40 -> 4
    Personality: TAYLOR loses Y(7) -> 14, total = 23 + 10 + 14 = 47 -> 4 + 7 = 11 (Master 11)
    """
    result = PersonalitySoulAnalyzer.analyze("ELIZABETH ANNE TAYLOR", y_policy="always_vowel")
    
    assert result["personality"]["number"] == 11
    assert result["personality"]["is_master_number"] is True
    assert result["soul_urge"]["number"] == 4
    assert result["soul_urge"]["unreduced_sum"] == 40


# =========================================================================
# 2. SEPARATION OF CONSONANTS AND VOWELS
# =========================================================================

def test_vowels_do_not_contribute_to_personality():
    """Vowels must not contribute to Personality total."""
    # "AEIOU" has zero consonants
    result = PersonalitySoulAnalyzer.analyze("AEIOU", y_policy="always_consonant")
    assert result["personality"]["number"] == 0
    assert result["personality"]["unreduced_sum"] == 0
    assert result["personality"]["included_letters_count"] == 0
    # Vowels sum: 1 + 5 + 9 + 6 + 3 = 24 -> 2 + 4 = 6
    assert result["soul_urge"]["unreduced_sum"] == 24
    assert result["soul_urge"]["number"] == 6


def test_consonants_do_not_contribute_to_soul_urge():
    """Consonants must not contribute to Soul Urge total."""
    # "BCDFG" has zero vowels
    result = PersonalitySoulAnalyzer.analyze("BCDFG")
    assert result["soul_urge"]["number"] == 0
    assert result["soul_urge"]["unreduced_sum"] == 0
    assert result["soul_urge"]["included_letters_count"] == 0
    # Consonants sum: 2 + 3 + 4 + 6 + 7 = 22 (Master 22 preserved)
    assert result["personality"]["unreduced_sum"] == 22
    assert result["personality"]["number"] == 22
    assert result["personality"]["is_master_number"] is True


# =========================================================================
# 3. MASTER NUMBER PRESERVATION (11, 22, 33)
# =========================================================================

def test_master_number_11_preservation():
    # K(2) + B(2) + T(2) + K(2) + C(3) = 11
    result = PersonalitySoulAnalyzer.analyze("K B T K C")
    assert result["personality"]["number"] == 11
    assert result["personality"]["is_master_number"] is True


def test_master_number_22_preservation():
    # V(4) + M(4) + D(4) + M(4) + M(4) + B(2) = 22
    result = PersonalitySoulAnalyzer.analyze("V M D M M B")
    assert result["personality"]["number"] == 22
    assert result["personality"]["is_master_number"] is True


# =========================================================================
# 4. NORMALIZATION, SPACES, PUNCTUATION & UNICODE
# =========================================================================

def test_normalization_with_accents_and_hyphens():
    result1 = PersonalitySoulAnalyzer.analyze("Mary-Jane")
    result2 = PersonalitySoulAnalyzer.analyze("MARY JANE")
    assert result1["personality"]["number"] == result2["personality"]["number"]
    assert result1["soul_urge"]["number"] == result2["soul_urge"]["number"]


def test_unicode_diacritics_stripped_properly():
    # Using explicit unicode escape for 'Ren\u00e9e Marie'
    result = PersonalitySoulAnalyzer.analyze("Ren\u00e9e Marie")
    assert result["normalized_name"] == "RENEE MARIE"
    # Consonants: R(9)+N(5)+M(4)+R(9) = 27 -> 2 + 7 = 9
    assert result["personality"]["number"] == 9
    # Vowels: E(5)+E(5)+A(1)+I(9)+E(5) = 25 -> 2 + 5 = 7
    assert result["soul_urge"]["unreduced_sum"] == 30
    assert result["soul_urge"]["number"] == 3


def test_unsupported_script_raises_value_error():
    with pytest.raises(ValueError) as excinfo:
        PersonalitySoulAnalyzer.analyze("\u0906\u0930\u0935 \u0936\u0930\u094d\u092e\u093e")
    assert "non-Latin scripts" in str(excinfo.value)


def test_empty_name_raises_value_error():
    with pytest.raises(ValueError):
        PersonalitySoulAnalyzer.analyze("   ")


# =========================================================================
# 5. DATABASE INTERPRETATION INTEGRITY
# =========================================================================

def test_all_numbers_have_database_interpretations():
    """Verify that 1-9, 11, 22, 33 exist in database for both personality and soul urge."""
    required_numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 22, 33]
    for n in required_numbers:
        p_interp = NumerologyRepository.get_name_interpretation("pythagorean", "personality", n)
        assert p_interp is not None, f"Missing personality interpretation for {n}"
        assert len(p_interp["overview"]) > 20
        assert len(p_interp["strengths"]) > 0

        s_interp = NumerologyRepository.get_name_interpretation("pythagorean", "soul_urge", n)
        assert s_interp is not None, f"Missing soul urge interpretation for {n}"
        assert len(s_interp["overview"]) > 20
        assert len(s_interp["strengths"]) > 0


# =========================================================================
# 6. API ENDPOINT INTEGRATION TESTS
# =========================================================================

def test_api_endpoint_post_success(client):
    response = client.post(
        "/api/v1/numerology/personality-soul",
        json={"birth_name": "ELIZABETH ANNE TAYLOR", "y_policy": "always_consonant"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert data["personality"]["number"] == 9
    assert data["soul_urge"]["number"] == 33
    assert data["personality"]["interpretation"]["number_value"] == 9
    assert data["soul_urge"]["interpretation"]["number_value"] == 33
    assert "Dynamic Complementary Synergy" in data["harmony_analysis"]["harmony_summary"]


def test_api_endpoint_get_success(client):
    response = client.get("/api/v1/numerology/personality-soul?birth_name=ELIZABETH+ANNE+TAYLOR")
    assert response.status_code == 200
    data = response.get_json()
    assert data["personality"]["number"] == 9
    assert data["soul_urge"]["number"] == 33


def test_api_endpoint_missing_name_error(client):
    response = client.post("/api/v1/numerology/personality-soul", json={})
    assert response.status_code == 400
    data = response.get_json()
    assert data["error_code"] == "MISSING_BIRTH_NAME"


def test_api_endpoint_unsupported_script_error(client):
    response = client.post(
        "/api/v1/numerology/personality-soul",
        json={"birth_name": "\u0930\u093e\u0939\u0941\u0932"},
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data["error_code"] == "UNSUPPORTED_SCRIPT"

