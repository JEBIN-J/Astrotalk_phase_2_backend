"""
test_angel_numbers.py
Automated test suite for Angel Numbers Module.
Covers Tests A through M specified in prompt.
"""

import pytest
import sys
import os

# Add backend directory to path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Astrotalk_phase_2_backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app import create_app
from app.services.angel_number_engine import AngelNumberEngine
from app.services.angel_number_service import AngelNumberService

@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()

# ========================================================
# Test A: Repeated sequence (111)
# ========================================================
def test_a_repeated_sequence_111():
    res = AngelNumberService.lookup_sequence("111")
    assert res["success"] is True
    assert res["normalized_sequence"] == "111"
    assert res["reduction"]["compound_total"] == 3
    assert res["reduction"]["root_number"] == 3
    assert res["has_reviewed_interpretation"] is True
    assert res["interpretation"]["title"] is not None

# ========================================================
# Test B: Repeated sequence (444)
# ========================================================
def test_b_repeated_sequence_444():
    res = AngelNumberService.lookup_sequence("444")
    assert res["success"] is True
    assert res["normalized_sequence"] == "444"
    assert res["reduction"]["compound_total"] == 12
    assert res["reduction"]["root_number"] == 3
    assert len(res["reduction"]["calculation_steps"]) >= 2
    assert res["has_reviewed_interpretation"] is True

# ========================================================
# Test C: Ascending sequence (1234)
# ========================================================
def test_c_ascending_sequence_1234():
    res = AngelNumberService.lookup_sequence("1234")
    assert res["success"] is True
    assert res["reduction"]["compound_total"] == 10
    assert res["reduction"]["root_number"] == 1
    # Check that ascending pattern is detected
    codes = [p["code"] for p in res["detected_patterns"]]
    assert "ascending_consecutive" in codes

# ========================================================
# Test D: Repeated block (1212)
# ========================================================
def test_d_repeated_block_1212():
    res = AngelNumberService.lookup_sequence("1212")
    assert res["success"] is True
    assert res["reduction"]["compound_total"] == 6
    assert res["reduction"]["root_number"] == 6
    codes = [p["code"] for p in res["detected_patterns"]]
    assert "repeated_blocks" in codes

# ========================================================
# Test E: Palindrome (1221)
# ========================================================
def test_e_palindrome_1221():
    res = AngelNumberService.lookup_sequence("1221")
    assert res["success"] is True
    codes = [p["code"] for p in res["detected_patterns"]]
    assert "palindrome" in codes
    assert res["reduction"]["compound_total"] == 6
    assert res["reduction"]["root_number"] == 6

# ========================================================
# Test F: Leading zero (0011)
# ========================================================
def test_f_leading_zero_0011():
    res = AngelNumberService.lookup_sequence("0011")
    assert res["success"] is True
    # Verify leading zeros are preserved in sequence representation
    assert res["normalized_sequence"] == "0011"
    assert res["reduction"]["compound_total"] == 2
    assert res["reduction"]["root_number"] == 2

# ========================================================
# Test G: Invalid inputs
# ========================================================
def test_g_invalid_inputs():
    # Letters
    res1 = AngelNumberService.lookup_sequence("abc")
    assert res1["success"] is False
    assert "Invalid sequence" in res1["error"] or "Only numeric" in res1["error"]

    # Invalid clock hour
    res2 = AngelNumberService.lookup_sequence("25:00")
    assert res2["success"] is False
    assert "invalid hour" in res2["error"].lower()

    # Empty string
    res3 = AngelNumberService.lookup_sequence("")
    assert res3["success"] is False

# ========================================================
# Test H: Missing interpretation returns honest status
# ========================================================
def test_h_missing_interpretation():
    # 9876 is a valid numeric sequence with no published angel number record
    res = AngelNumberService.lookup_sequence("9876")
    assert res["success"] is True
    assert res["normalized_sequence"] == "9876"
    assert res["has_reviewed_interpretation"] is False
    assert res["interpretation"] is None
    # Reduction and patterns are still calculated accurately
    assert res["reduction"]["root_number"] == 3  # 9+8+7+6=30 -> 3
    assert "No reviewed interpretation currently available" in res["status_message"]

# ========================================================
# Test I: Deterministic results
# ========================================================
def test_i_deterministic_results():
    res1 = AngelNumberService.lookup_sequence("777")
    res2 = AngelNumberService.lookup_sequence("777")
    assert res1 == res2

# ========================================================
# Test J: Personal Angel Number
# ========================================================
def test_j_personal_number():
    # Method A: DOB 1992-08-14: 1+9+9+2+0+8+1+4 = 34 -> 7
    res_dob = AngelNumberService.calculate_personal_number(method="dob", dob="1992-08-14")
    assert res_dob["success"] is True
    calc = res_dob["calculation"]
    assert calc["compound_total"] == 34
    assert calc["root_number"] == 7
    assert calc["personal_angel_number"] == "777"

    # Method B: Name Pythagorean calculation
    res_name = AngelNumberService.calculate_personal_number(method="name", name="John Doe")
    assert res_name["success"] is True
    assert res_name["calculation"]["root_number"] is not None

    # Invalid DOB
    res_invalid = AngelNumberService.calculate_personal_number(method="dob", dob="not-a-date")
    assert res_invalid["success"] is False

# ========================================================
# Test K: Journal isolation and authorization
# ========================================================
def test_k_journal_authorization():
    user_a = "user_test_alpha"
    user_b = "user_test_beta"

    # User A records sighting
    add_res = AngelNumberService.add_sighting(
        user_id=user_a,
        observed_sequence="11:11",
        context_category="Clock",
        personal_note="Noticed on kitchen clock",
        mood="Peaceful"
    )
    assert add_res["success"] is True
    sighting_id = add_res["sighting_id"]

    # User B cannot update User A's sighting
    upd_res = AngelNumberService.update_sighting(
        user_id=user_b,
        sighting_id=sighting_id,
        personal_note="Hacked note"
    )
    assert upd_res["success"] is False
    assert "Unauthorized" in upd_res["error"]

    # User B cannot delete User A's sighting
    del_res = AngelNumberService.delete_sighting(
        user_id=user_b,
        sighting_id=sighting_id
    )
    assert del_res["success"] is False
    assert "Unauthorized" in del_res["error"]

    # User A CAN delete their own sighting
    del_res_a = AngelNumberService.delete_sighting(
        user_id=user_a,
        sighting_id=sighting_id
    )
    assert del_res_a["success"] is True

# ========================================================
# Test L: Daily reflection stability
# ========================================================
def test_l_daily_reflection():
    res1 = AngelNumberService.get_daily_reflection("2026-10-14")
    res2 = AngelNumberService.get_daily_reflection("2026-10-14")
    assert res1["success"] is True
    assert res1["daily"]["sequence"] == res2["daily"]["sequence"]
    assert res1["daily"]["reflection"] == res2["daily"]["reflection"]

# ========================================================
# Test M: API Client Integration
# ========================================================
def test_m_api_endpoints(client):
    # Lookup endpoint
    resp = client.post("/api/v1/numerology/angel-numbers/lookup", json={"sequence": "333"})
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["normalized_sequence"] == "333"
    assert data["reduction"]["root_number"] == 9

    # Patterns endpoint
    resp_pat = client.get("/api/v1/numerology/angel-numbers/patterns")
    assert resp_pat.status_code == 200
    assert len(resp_pat.get_json()["data"]) >= 5

    # Mirror hours endpoint
    resp_mh = client.get("/api/v1/numerology/angel-numbers/mirror-hours")
    assert resp_mh.status_code == 200
    assert len(resp_mh.get_json()["data"]) >= 3
