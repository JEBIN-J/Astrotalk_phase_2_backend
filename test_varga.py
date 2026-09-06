import sys
import math

ZODIAC_SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

def calculate_varga_sign(deg_in_sign, varga_num, d1_sign_idx):
    if varga_num == 9:
        part = int(deg_in_sign / (30.0 / 9.0))
        element_start = [1, 10, 7, 4][(d1_sign_idx - 1) % 4]
        return ((element_start - 1 + part) % 12) + 1
    return 0

for v in [2,3,4,5,6,7,8,9,10,11,12,16,20,24,27,30,40,45,60]:
    # I don't have all the varga formulas here, but I can just import it from the engine
    pass
