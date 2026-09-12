import math
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple

VIMSHOTTARI_YEARS = {
    "Ketu": 7,
    "Venus": 20,
    "Sun": 6,
    "Moon": 10,
    "Mars": 7,
    "Rahu": 18,
    "Jupiter": 16,
    "Saturn": 19,
    "Mercury": 17
}

VIMSHOTTARI_SEQUENCE = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]

DAYS_IN_YEAR = 365.256364  # Sidereal year convention used in this engine

def calculate_vimshottari_dasha_full(
    moon_nak_idx: int,
    moon_deg: float,
    calculation_date: datetime,
    moon_sign_name: str,
    moon_nak_name: str,
    moon_nak_lord: str,
    moon_pada: int,
    days_in_year: float = 365.256364
) -> Dict[str, Any]:
    """
    Calculate precise Vimshottari Dasha sequence (up to Pratyantardasha in timeline, and Prana for Current).
    """
    
    DAYS_IN_YEAR = days_in_year
    
    # 1. Moon Details & Balance Calculation
    nak_span_deg = 360.0 / 27.0  # 13° 20'
    
    # Calculate exact elapsed and remaining arc
    nak_start_deg = (moon_nak_idx - 1) * nak_span_deg
    nak_end_deg = nak_start_deg + nak_span_deg
    
    elapsed_arc = moon_deg - nak_start_deg
    remaining_arc = nak_span_deg - elapsed_arc
    
    fraction_remaining = remaining_arc / nak_span_deg
    fraction_elapsed = elapsed_arc / nak_span_deg
    
    starting_lord = moon_nak_lord
    starting_lord_full_years = VIMSHOTTARI_YEARS[starting_lord]
    
    balance_years = starting_lord_full_years * fraction_remaining
    
    balance_info = {
        "elapsed_arc": round(elapsed_arc, 6),
        "remaining_arc": round(remaining_arc, 6),
        "remaining_percentage": round(fraction_remaining * 100, 2),
        "starting_lord": starting_lord,
        "full_years": starting_lord_full_years,
        "balance_years": round(balance_years, 6),
        "nakshatra_start": round(nak_start_deg, 6),
        "nakshatra_end": round(nak_end_deg, 6)
    }

    # 2. Timeline Generation
    start_seq_idx = VIMSHOTTARI_SEQUENCE.index(starting_lord)
    
    mahadashas = []
    antardashas_flat = []
    pratyantardashas_flat = []
    
    current_md_start = calculation_date
    now = datetime.now()
    
    current_dasha_obj = {
        "mahadasha": "-",
        "antardasha": "-",
        "pratyantardasha": "-",
        "sookshma": "-",
        "prana": "-"
    }
    
    # Pre-calculate to find the actual start of birth/prashna (retroactively finding the start of the first MD)
    # The current_md_start is actually the date of Prashna.
    # Wait, if calculation_date is Prashna date, then the first MD starts AT calculation_date.
    # We do NOT subtract the elapsed years from calculation_date, because Prashna chart is cast FOR calculation_date, 
    # so the balance is exactly what is left starting from calculation_date.
    
    current_date_cursor = calculation_date
    
    for i in range(len(VIMSHOTTARI_SEQUENCE)):
        md_lord = VIMSHOTTARI_SEQUENCE[(start_seq_idx + i) % len(VIMSHOTTARI_SEQUENCE)]
        md_full_years = VIMSHOTTARI_YEARS[md_lord]
        
        # If it's the first MD, its actual physical duration from the Prashna date is the balance_years
        md_actual_years = balance_years if i == 0 else md_full_years
        md_end_date = current_date_cursor + timedelta(days=md_actual_years * DAYS_IN_YEAR)
        
        is_md_active = current_date_cursor <= now < md_end_date
        
        md_item = {
            "lord": md_lord,
            "full_years": md_full_years,
            "duration_years_in_timeline": round(md_actual_years, 6),
            "start_date": current_date_cursor.strftime("%d %b %Y"),
            "end_date": md_end_date.strftime("%d %b %Y"),
            "start_dt": current_date_cursor.isoformat(),
            "end_dt": md_end_date.isoformat(),
            "is_active": is_md_active,
            "antardashas": []
        }
        
        if is_md_active:
            current_dasha_obj["mahadasha"] = md_lord
            
        # --- Calculate Antardashas (AD) ---
        ad_start_seq_idx = VIMSHOTTARI_SEQUENCE.index(md_lord)
        
        # NOTE: Even for the first partial MD, we must mathematically calculate the ADs backwards to find out 
        # which ADs fall within the remaining balance. We cannot just shrink all 9 ADs into the balance!
        # To do this correctly, we establish the THEORETICAL start of the MD:
        theoretical_md_start = current_date_cursor if i > 0 else current_date_cursor - timedelta(days=(md_full_years - balance_years) * DAYS_IN_YEAR)
        
        ad_date_cursor = theoretical_md_start
        
        for j in range(len(VIMSHOTTARI_SEQUENCE)):
            ad_lord = VIMSHOTTARI_SEQUENCE[(ad_start_seq_idx + j) % len(VIMSHOTTARI_SEQUENCE)]
            ad_full_years = (md_full_years * VIMSHOTTARI_YEARS[ad_lord]) / 120.0
            ad_end_date = ad_date_cursor + timedelta(days=ad_full_years * DAYS_IN_YEAR)
            
            # If this AD ended before the Prashna date, it is in the past, skip it entirely in the UI.
            if i == 0 and ad_end_date <= calculation_date:
                ad_date_cursor = ad_end_date
                continue
                
            # If this AD started before Prashna date but ends after, its effective start is Prashna date
            effective_ad_start = max(ad_date_cursor, current_date_cursor)
            
            is_ad_active = effective_ad_start <= now < ad_end_date
            
            ad_item = {
                "md_lord": md_lord,
                "lord": ad_lord,
                "duration_years": round(ad_full_years, 6),
                "start_date": effective_ad_start.strftime("%d %b %Y"),
                "end_date": ad_end_date.strftime("%d %b %Y"),
                "start_dt": effective_ad_start.isoformat(),
                "end_dt": ad_end_date.isoformat(),
                "is_active": is_ad_active,
                "pratyantardashas": []
            }
            
            if is_ad_active:
                current_dasha_obj["antardasha"] = ad_lord
                
            # --- Calculate Pratyantardashas (PD) ---
            pd_start_seq_idx = VIMSHOTTARI_SEQUENCE.index(ad_lord)
            pd_date_cursor = ad_date_cursor # Theoretical start of AD
            
            for k in range(len(VIMSHOTTARI_SEQUENCE)):
                pd_lord = VIMSHOTTARI_SEQUENCE[(pd_start_seq_idx + k) % len(VIMSHOTTARI_SEQUENCE)]
                pd_full_years = (ad_full_years * VIMSHOTTARI_YEARS[pd_lord]) / 120.0
                pd_end_date = pd_date_cursor + timedelta(days=pd_full_years * DAYS_IN_YEAR)
                
                if i == 0 and pd_end_date <= calculation_date:
                    pd_date_cursor = pd_end_date
                    continue
                    
                effective_pd_start = max(pd_date_cursor, current_date_cursor)
                is_pd_active = effective_pd_start <= now < pd_end_date
                
                pd_item = {
                    "md_lord": md_lord,
                    "ad_lord": ad_lord,
                    "lord": pd_lord,
                    "duration_years": round(pd_full_years, 6),
                    "start_date": effective_pd_start.strftime("%d %b %Y"),
                    "end_date": pd_end_date.strftime("%d %b %Y"),
                    "start_dt": effective_pd_start.isoformat(),
                    "end_dt": pd_end_date.isoformat(),
                    "is_active": is_pd_active
                }
                
                if is_pd_active:
                    current_dasha_obj["pratyantardasha"] = pd_lord
                    
                    # Calculate Sookshma and Prana purely for the currently active PD to save memory
                    sook_start_seq = VIMSHOTTARI_SEQUENCE.index(pd_lord)
                    sook_cursor = pd_date_cursor
                    for s in range(len(VIMSHOTTARI_SEQUENCE)):
                        sook_lord = VIMSHOTTARI_SEQUENCE[(sook_start_seq + s) % len(VIMSHOTTARI_SEQUENCE)]
                        sook_years = (pd_full_years * VIMSHOTTARI_YEARS[sook_lord]) / 120.0
                        sook_end = sook_cursor + timedelta(days=sook_years * DAYS_IN_YEAR)
                        
                        if sook_cursor <= now < sook_end:
                            current_dasha_obj["sookshma"] = sook_lord
                            
                            prana_start_seq = VIMSHOTTARI_SEQUENCE.index(sook_lord)
                            prana_cursor = sook_cursor
                            for pr in range(len(VIMSHOTTARI_SEQUENCE)):
                                prana_lord = VIMSHOTTARI_SEQUENCE[(prana_start_seq + pr) % len(VIMSHOTTARI_SEQUENCE)]
                                prana_years = (sook_years * VIMSHOTTARI_YEARS[prana_lord]) / 120.0
                                prana_end = prana_cursor + timedelta(days=prana_years * DAYS_IN_YEAR)
                                
                                if prana_cursor <= now < prana_end:
                                    current_dasha_obj["prana"] = prana_lord
                                    break
                                prana_cursor = prana_end
                            break
                        sook_cursor = sook_end

                ad_item["pratyantardashas"].append(pd_item)
                pd_date_cursor = pd_end_date
                
            md_item["antardashas"].append(ad_item)
            ad_date_cursor = ad_end_date
            
        mahadashas.append(md_item)
        current_date_cursor = md_end_date
        
    # If Prashna date is in the future, 'now' won't match anything. Default to first.
    if current_dasha_obj["mahadasha"] == "-":
        first_md = mahadashas[0]
        first_ad = first_md["antardashas"][0]
        first_pd = first_ad["pratyantardashas"][0]
        current_dasha_obj = {
            "mahadasha": first_md["lord"],
            "antardasha": first_ad["lord"],
            "pratyantardasha": first_pd["lord"],
            "sookshma": "N/A",
            "prana": "N/A",
            "note": "Prashna is in the future or past"
        }

    return {
        "system": "vimshottari",
        "calculation_basis": "prashna",
        "moon": {
            "longitude": round(moon_deg, 6),
            "sign": moon_sign_name,
            "nakshatra": moon_nak_name,
            "nakshatra_number": moon_nak_idx,
            "pada": moon_pada,
            "nakshatra_lord": moon_nak_lord
        },
        "balance": balance_info,
        "current": current_dasha_obj,
        "timeline": mahadashas,
        "calculation_details": {
            "nakshatra_span": "13° 20'",
            "calendar_convention": f"Savana Sidereal Year (365.256364 days)" if days_in_year > 365.0 else f"Savana Year ({days_in_year} days)"
        }
    }
