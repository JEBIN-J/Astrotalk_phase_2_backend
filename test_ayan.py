import swisseph as swe

# Lahiri we want: 23.634377534644445
target = 23.634377534644445
# Ayanamsa is roughly 23.85 in 2000, changes 50.29 arcsec/year = 0.013969 deg/year
# 23.634377 - 23.85 = -0.2156
# -0.2156 / 0.013969 = -15.43 years
# 2000 - 15.43 = 1984.57

jd_2000 = swe.julday(2000, 1, 1, 12.0)
jd = jd_2000 - (15.43 * 365.25)
swe.set_sid_mode(swe.SIDM_LAHIRI)

print("Target:", target)
print("swe for 1984.57:", swe.get_ayanamsa_ut(jd))
