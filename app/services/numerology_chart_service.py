from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
from app.services.numerology_dasha_service import NumerologyDashaService

class NumerologyChartService:
    """
    Dedicated Service for Numerology Chart calculations:
    - Section A: Basic Chart (3x3 Grid Model, Cell Multiplicities, 8 Directional Planes, Core Numbers)
    - Section B: Dasha and Antardasha Chart (Horizontal 3x3 Grid Models for each period with Dasha + Antardasha added)
    - Section C: Pratyantar Dasha Chart (Horizontal 3x3 Grid Models for each subperiod with Dasha + Antardasha + Pratyantar added)
    """

    LOSHU_CELL_SPECS = {
        1: {
            "planet": "Sun", "vedic_name": "Surya",
            "element": "Water", "direction": "North",
            "attribute": "Career, Life Path & Personal Flow",
            "theme": "Drive, individuality, leadership and independence."
        },
        2: {
            "planet": "Moon", "vedic_name": "Chandra",
            "element": "Earth", "direction": "South-West",
            "attribute": "Relationships, Sensitivity & Diplomacy",
            "theme": "Empathy, cooperation, intuition and partnerships."
        },
        3: {
            "planet": "Jupiter", "vedic_name": "Guru",
            "element": "Wood", "direction": "East",
            "attribute": "Wisdom, Intellect & Spiritual Growth",
            "theme": "Optimism, higher knowledge, learning and expansion."
        },
        4: {
            "planet": "Rahu", "vedic_name": "North Node",
            "element": "Wood", "direction": "South-East",
            "attribute": "Order, Practicality & Discipline",
            "theme": "Organization, structural execution and ambition."
        },
        5: {
            "planet": "Mercury", "vedic_name": "Budha",
            "element": "Earth", "direction": "Center",
            "attribute": "Balance, Communication & Adaptability",
            "theme": "Emotional poise, commerce, versatility and freedom."
        },
        6: {
            "planet": "Venus", "vedic_name": "Shukra",
            "element": "Metal", "direction": "North-West",
            "attribute": "Luxury, Harmony, Family & Creativity",
            "theme": "Artistic aesthetics, love, responsibility and domestic bliss."
        },
        7: {
            "planet": "Ketu", "vedic_name": "South Node",
            "element": "Metal", "direction": "West",
            "attribute": "Intuition, Research, Spirituality & Analysis",
            "theme": "Esoteric exploration, critical discernment and depth."
        },
        8: {
            "planet": "Saturn", "vedic_name": "Shani",
            "element": "Earth", "direction": "North-East",
            "attribute": "Perseverance, Wealth & Structural Knowledge",
            "theme": "Material stability, methodical discipline and karmic mastery."
        },
        9: {
            "planet": "Mars", "vedic_name": "Mangal",
            "element": "Fire", "direction": "South",
            "attribute": "Courage, Passion, Fame & Vital Energy",
            "theme": "Bold execution, humanitarian zeal and energetic assertion."
        }
    }

    # Classical 3x3 Layouts:
    # Vedic Ank Kundli: Row 0: [3, 1, 9], Row 1: [6, 7, 5], Row 2: [2, 8, 4]
    # Lo Shu Magic Square: Row 0: [4, 9, 2], Row 1: [3, 5, 7], Row 2: [8, 1, 6]
    VEDIC_LAYOUT = [[3, 1, 9], [6, 7, 5], [2, 8, 4]]
    LOSHU_LAYOUT = [[4, 9, 2], [3, 5, 7], [8, 1, 6]]

    PLANES_SPECS = [
        {"id": "mental_plane", "name": "Mental Plane", "type": "Horizontal", "numbers": [4, 9, 2], "description": "Intellect, memory and analytical thinking."},
        {"id": "emotional_plane", "name": "Emotional Plane", "type": "Horizontal", "numbers": [3, 5, 7], "description": "Spiritual balance, empathy and intuitive connection."},
        {"id": "practical_plane", "name": "Practical Plane", "type": "Horizontal", "numbers": [8, 1, 6], "description": "Physical execution, commerce and practical manifestation."},
        {"id": "thought_plane", "name": "Thought Plane", "type": "Vertical", "numbers": [4, 3, 8], "description": "Strategic planning, idea generation and conceptual vision."},
        {"id": "will_plane", "name": "Will Plane", "type": "Vertical", "numbers": [9, 5, 1], "description": "Determination, persistence and willpower."},
        {"id": "action_plane", "name": "Action Plane", "type": "Vertical", "numbers": [2, 7, 6], "description": "Initiative and real-world execution."},
        {"id": "golden_diagonal", "name": "Golden Diagonal", "type": "Diagonal", "numbers": [4, 5, 6], "description": "Universal fortune, harmonious success and wealth."},
        {"id": "silver_diagonal", "name": "Silver Diagonal", "type": "Diagonal", "numbers": [2, 5, 8], "description": "Landed property, stability and grounding."}
    ]

    @classmethod
    def build_grid_matrix(
        cls,
        counts: Dict[int, int],
        grid_type: str = "vedic",
        highlight_numbers: Optional[List[int]] = None
    ) -> List[List[Dict[str, Any]]]:
        layout = cls.LOSHU_LAYOUT if grid_type.lower() == "loshu" else cls.VEDIC_LAYOUT
        highlights = set(highlight_numbers or [])

        matrix = []
        for r_idx, row in enumerate(layout):
            row_cells = []
            for c_idx, num in enumerate(row):
                cnt = counts.get(num, 0)
                display_str = "".join(str(num) for _ in range(cnt)) if cnt > 0 else ""
                spec = cls.LOSHU_CELL_SPECS.get(num, {})
                row_cells.append({
                    "number": num,
                    "row": r_idx,
                    "col": c_idx,
                    "count": cnt,
                    "display_text": display_str,
                    "is_present": cnt > 0,
                    "is_added": num in highlights,
                    "planet": spec.get("planet", ""),
                    "vedic_name": spec.get("vedic_name", ""),
                    "element": spec.get("element", ""),
                    "direction": spec.get("direction", "")
                })
            matrix.append(row_cells)
        return matrix

    @classmethod
    def calculate_base_counts(
        cls,
        dob: date,
        mulank: int,
        bhagyank: int,
        grid_type: str = "vedic"
    ) -> Dict[int, int]:
        digit_counts = {i: 0 for i in range(1, 10)}
        
        # Day digits (DD)
        for ch in f"{dob.day:02d}":
            if ch != '0':
                digit_counts[int(ch)] += 1
                
        # Month digits (MM)
        for ch in f"{dob.month:02d}":
            if ch != '0':
                digit_counts[int(ch)] += 1
                
        # Year digits: in Vedic Ank Kundli, century is excluded, only last 2 digits of year (YY) are included
        year_last_two = dob.year % 100
        for ch in f"{year_last_two:02d}":
            if ch != '0':
                digit_counts[int(ch)] += 1
                
        # Add Mulank (Driver Number)
        if 1 <= mulank <= 9:
            digit_counts[mulank] += 1
            
        # Add Bhagyank (Destiny / Conductor Number)
        if 1 <= bhagyank <= 9:
            digit_counts[bhagyank] += 1
            
        return digit_counts

    @classmethod
    def calculate_basic_chart(cls, name: str, dob_str: str, system: str = "pythagorean", grid_type: str = "loshu") -> Dict[str, Any]:
        dob = NumerologyDashaService.parse_date(dob_str)
        basic_info = NumerologyDashaService.calculate_basic_info(name, dob_str, system)

        mulank = basic_info["basic_number"]["number"]
        bhagyank = basic_info["destiny_number"]["number"]

        digit_counts = cls.calculate_base_counts(dob, mulank, bhagyank, grid_type=grid_type)

        # Build 3x3 Grid matrix
        grid_matrix = cls.build_grid_matrix(digit_counts, grid_type=grid_type)

        # 8 Planes evaluation
        planes_results = []
        for plane in cls.PLANES_SPECS:
            present_nums = [n for n in plane["numbers"] if digit_counts.get(n, 0) > 0]
            missing_nums = [n for n in plane["numbers"] if digit_counts.get(n, 0) == 0]
            num_present = len(present_nums)
            pct = int((num_present / 3.0) * 100)
            status = "Complete" if num_present == 3 else ("Partial" if num_present > 0 else "Empty")
            planes_results.append({
                "id": plane["id"],
                "name": plane["name"],
                "type": plane["type"],
                "target_numbers": plane["numbers"],
                "present_numbers": present_nums,
                "missing_numbers": missing_nums,
                "count_present": num_present,
                "percentage": pct,
                "status": status,
                "description": plane["description"]
            })

        present_list = [n for n, cnt in digit_counts.items() if cnt > 0]
        missing_list = [n for n, cnt in digit_counts.items() if cnt == 0]

        cells = {}
        for num in range(1, 10):
            spec = cls.LOSHU_CELL_SPECS[num]
            cnt = digit_counts.get(num, 0)
            if cnt == 0:
                s_label = "Missing"
                d_text = "-"
            elif cnt == 1:
                s_label = "Balanced"
                d_text = str(num)
            elif cnt == 2:
                s_label = "Strong"
                d_text = f"{num}{num}"
            else:
                s_label = "Excessive"
                d_text = str(num) * cnt

            cells[num] = {
                "number": num,
                "count": cnt,
                "display_text": d_text,
                "strength_label": s_label,
                "is_present": cnt > 0,
                "planet": spec["planet"],
                "vedic_name": spec["vedic_name"],
                "element": spec["element"],
                "direction": spec["direction"],
                "attribute": spec["attribute"],
                "theme": spec["theme"]
            }

        return {
            "profile": {
                "name": name,
                "dob": dob.strftime("%Y-%m-%d"),
                "formatted_dob": dob.strftime("%d %b %Y"),
                "system": system,
                "grid_type": grid_type
            },
            "grid_type": grid_type,
            "grid_matrix": grid_matrix,
            "cells": cells,
            "planes_analysis": planes_results,
            "base_counts": digit_counts,
            "planes": planes_results,
            "present_numbers": present_list,
            "missing_numbers": missing_list,
            "core_numbers": {
                "mulank": basic_info["basic_number"],
                "supportive": basic_info["supportive_number"],
                "destiny": basic_info["destiny_number"],
                "name_number": basic_info.get("name_number", {})
            }
        }

    @classmethod
    def calculate_dasha_chart(
        cls,
        dob_str: str,
        start_date_str: Optional[str] = None,
        duration_years: int = 10,
        end_date_str: Optional[str] = None,
        ref_date_str: Optional[str] = None,
        grid_type: str = "vedic"
    ) -> Dict[str, Any]:
        """
        Calculates Section B — Dasha and Antardasha Chart:
        - Intersecting annual Antardashas & parent Mahadashas
        - Generates the 3x3 Chart Model for each period with Dasha + Antardasha numbers added to the base grid!
        """
        dob = NumerologyDashaService.parse_date(dob_str)
        ref_date = NumerologyDashaService.parse_date(ref_date_str) if ref_date_str else date.today()

        if start_date_str:
            w_start = NumerologyDashaService.parse_date(start_date_str)
        else:
            w_start = ref_date

        if end_date_str:
            w_end = NumerologyDashaService.parse_date(end_date_str)
            if w_end <= w_start:
                raise ValueError("Timeline end_date must be strictly after start_date.")
            actual_duration_years = round((w_end - w_start).days / 365.25, 1)
            duration_label = f"Custom ({actual_duration_years} Yrs)"
        else:
            duration_years = max(1, duration_years)
            try:
                w_end = w_start.replace(year=w_start.year + duration_years)
            except ValueError:
                w_end = w_start.replace(year=w_start.year + duration_years, day=28)
            duration_label = f"{duration_years} Years"

        # Compute Base counts with century excluded and Mulank + Bhagyank included
        basic_info = NumerologyDashaService.calculate_basic_info("", dob_str)
        mulank = basic_info["basic_number"]["number"]
        bhagyank = basic_info["destiny_number"]["number"]
        base_counts = cls.calculate_base_counts(dob, mulank, bhagyank, grid_type=grid_type)

        # Calculate annual Antardashas intersecting [w_start, w_end]
        min_year = max(dob.year, w_start.year - 1)
        max_year = min(dob.year + 100, w_end.year + 1)
        past_yrs = max(0, ref_date.year - min_year)
        future_yrs = max(5, max_year - ref_date.year + 2)

        all_antardashas = NumerologyDashaService.calculate_antardashas(
            dob_str,
            ref_date_str=ref_date.strftime("%Y-%m-%d"),
            past_years=past_yrs,
            future_years=future_yrs
        )

        dasha_antardasha_charts = []
        for ad in all_antardashas:
            ad_start = NumerologyDashaService.parse_date(ad["start_date"])
            ad_end = NumerologyDashaService.parse_date(ad["end_date"])

            if not (ad_start < w_end and ad_end > w_start):
                continue

            d_num = ad["parent_dasha"]
            ad_num = ad["antardasha_number"]

            # Period-specific counts: base counts + Dasha + Antardasha
            period_counts = dict(base_counts)
            period_counts[d_num] = period_counts.get(d_num, 0) + 1
            period_counts[ad_num] = period_counts.get(ad_num, 0) + 1

            # Build 3x3 Grid Matrix for this period
            chart_matrix = cls.build_grid_matrix(period_counts, grid_type=grid_type, highlight_numbers=[d_num, ad_num])

            is_active = (ad_start <= ref_date < ad_end)
            status = "Active" if is_active else ("Completed" if ref_date >= ad_end else "Upcoming")

            display_end = ad_end - timedelta(days=1)
            dasha_antardasha_charts.append({
                "cycle_year": ad["cycle_year"],
                "from_date": ad_start.strftime("%d-%b-%Y"),
                "to_date": display_end.strftime("%d-%b-%Y"),
                "start_date": ad["start_date"],
                "end_date": ad["end_date"],
                "dasha": d_num,
                "dasha_lord": ad["parent_lord"],
                "antardasha": ad_num,
                "antardasha_lord": ad["lord"],
                "added_numbers": [d_num, ad_num],
                "status": status,
                "is_active": is_active,
                "grid_matrix": chart_matrix
            })

        # Calculate all Mahadashas up to 100 years for timeline summary
        all_mahadashas = NumerologyDashaService.calculate_mahadashas(dob_str, ref_date_str=ref_date.strftime("%Y-%m-%d"), max_years=100)
        intersecting_mds = []
        for m in all_mahadashas:
            m_start = NumerologyDashaService.parse_date(m["start_date"])
            m_end = NumerologyDashaService.parse_date(m["end_date"])
            if m_start < w_end and m_end > w_start:
                m_copy = dict(m)
                m_copy["starts_before_window"] = m_start < w_start
                m_copy["ends_after_window"] = m_end > w_end
                intersecting_mds.append(m_copy)

        active_period = next((m for m in all_mahadashas if m["is_active"]), None)

        return {
            "timeline": {
                "start_date": w_start.strftime("%Y-%m-%d"),
                "end_date": w_end.strftime("%Y-%m-%d"),
                "formatted_window": f"{w_start.strftime('%d %b %Y')} - {w_end.strftime('%d %b %Y')}",
                "duration_years": duration_years,
                "duration_label": duration_label,
                "reference_date": ref_date.strftime("%Y-%m-%d"),
                "active_dasha": active_period,
                "charts_count": len(dasha_antardasha_charts)
            },
            "charts": dasha_antardasha_charts,
            "periods": intersecting_mds
        }

    @classmethod
    def calculate_pratyantar_chart(
        cls,
        dob_str: str,
        start_date_str: Optional[str] = None,
        duration_years: int = 10,
        end_date_str: Optional[str] = None,
        ref_date_str: Optional[str] = None,
        parent_dasha_filter: Optional[int] = None,
        antardasha_year_filter: Optional[int] = None,
        grid_type: str = "vedic"
    ) -> Dict[str, Any]:
        """
        Calculates Section C — Pratyantar Dasha Chart:
        - Intersecting 9 Pratantardashas
        - Generates the 3x3 Chart Model for each subperiod with Dasha + Antardasha + Pratyantar added to base grid!
        """
        dob = NumerologyDashaService.parse_date(dob_str)
        ref_date = NumerologyDashaService.parse_date(ref_date_str) if ref_date_str else date.today()

        if start_date_str:
            w_start = NumerologyDashaService.parse_date(start_date_str)
        else:
            w_start = ref_date

        if end_date_str:
            w_end = NumerologyDashaService.parse_date(end_date_str)
        else:
            duration_years = max(1, duration_years)
            try:
                w_end = w_start.replace(year=w_start.year + duration_years)
            except ValueError:
                w_end = w_start.replace(year=w_start.year + duration_years, day=28)

        # Compute Base counts with century excluded and Mulank + Bhagyank included
        basic_info = NumerologyDashaService.calculate_basic_info("", dob_str)
        mulank = basic_info["basic_number"]["number"]
        bhagyank = basic_info["destiny_number"]["number"]
        base_counts = cls.calculate_base_counts(dob, mulank, bhagyank, grid_type=grid_type)

        min_year = max(dob.year, w_start.year - 1)
        max_year = min(dob.year + 100, w_end.year + 1)
        past_yrs = max(0, ref_date.year - min_year)
        future_yrs = max(5, max_year - ref_date.year + 2)

        all_antardashas = NumerologyDashaService.calculate_antardashas(
            dob_str,
            ref_date_str=ref_date.strftime("%Y-%m-%d"),
            past_years=past_yrs,
            future_years=future_yrs
        )

        pratyantar_charts = []
        for ad in all_antardashas:
            ad_start = NumerologyDashaService.parse_date(ad["start_date"])
            ad_end = NumerologyDashaService.parse_date(ad["end_date"])

            if not (ad_start < w_end and ad_end > w_start):
                continue
            if parent_dasha_filter is not None and ad["parent_dasha"] != parent_dasha_filter:
                continue
            if antardasha_year_filter is not None and ad["cycle_year"] != antardasha_year_filter:
                continue

            pds = NumerologyDashaService.calculate_paryantardashas(
                dob_str,
                antardasha_year=ad["cycle_year"],
                ref_date_str=ref_date.strftime("%Y-%m-%d")
            )

            for pd in pds:
                pd_start = NumerologyDashaService.parse_date(pd["start_date"])
                pd_end = NumerologyDashaService.parse_date(pd["end_date"])

                if pd_start < w_end and pd_end > w_start:
                    d_num = pd["parent_dasha"]
                    ad_num = pd["antardasha"]
                    pd_num = pd["paryantardasha_number"]

                    # Counts: base + Dasha + Antardasha + Pratyantar Dasha
                    sub_counts = dict(base_counts)
                    sub_counts[d_num] = sub_counts.get(d_num, 0) + 1
                    sub_counts[ad_num] = sub_counts.get(ad_num, 0) + 1
                    sub_counts[pd_num] = sub_counts.get(pd_num, 0) + 1

                    chart_matrix = cls.build_grid_matrix(sub_counts, grid_type=grid_type, highlight_numbers=[d_num, ad_num, pd_num])

                    is_active = (pd_start <= ref_date < pd_end)
                    status = "Active" if is_active else ("Completed" if ref_date >= pd_end else "Upcoming")

                    pratyantar_charts.append({
                        "cycle_year": ad["cycle_year"],
                        "from_date": pd_start.strftime("%d-%b-%Y"),
                        "to_date": pd_end.strftime("%d-%b-%Y"),
                        "start_date": pd["start_date"],
                        "end_date": pd["end_date"],
                        "dasha": d_num,
                        "dasha_lord": pd["parent_lord"],
                        "antardasha": ad_num,
                        "antardasha_lord": pd["antardasha_lord"],
                        "pratyantar_dasha": pd_num,
                        "pratyantar_lord": pd["lord"],
                        "added_numbers": [d_num, ad_num, pd_num],
                        "status": status,
                        "is_active": is_active,
                        "duration_days": pd["duration_days"],
                        "grid_matrix": chart_matrix
                    })

        return {
            "total_subperiods_count": len(pratyantar_charts),
            "charts": pratyantar_charts,
            "subperiods": pratyantar_charts
        }

    @classmethod
    def get_full_chart_workspace(
        cls,
        name: str,
        dob_str: str,
        system: str = "pythagorean",
        start_date_str: Optional[str] = None,
        duration_years: int = 10,
        end_date_str: Optional[str] = None,
        ref_date_str: Optional[str] = None,
        parent_dasha_filter: Optional[int] = None,
        grid_type: str = "vedic"
    ) -> Dict[str, Any]:
        if not dob_str or not dob_str.strip():
            raise ValueError("Date of birth (dob) is required for Chart calculation.")

        if not name or not name.strip():
            name = "Seeker"

        ref_date = NumerologyDashaService.parse_date(ref_date_str) if ref_date_str else date.today()

        basic_chart = cls.calculate_basic_chart(name=name, dob_str=dob_str, system=system, grid_type=grid_type)
        dasha_chart = cls.calculate_dasha_chart(
            dob_str=dob_str,
            start_date_str=start_date_str,
            duration_years=duration_years,
            end_date_str=end_date_str,
            ref_date_str=ref_date.strftime("%Y-%m-%d"),
            grid_type=grid_type
        )
        pratyantar_chart = cls.calculate_pratyantar_chart(
            dob_str=dob_str,
            start_date_str=start_date_str,
            duration_years=duration_years,
            end_date_str=end_date_str,
            ref_date_str=ref_date.strftime("%Y-%m-%d"),
            parent_dasha_filter=parent_dasha_filter,
            grid_type=grid_type
        )

        return {
            "status": "success",
            "reference_date": ref_date.strftime("%Y-%m-%d"),
            "grid_type": grid_type,
            "basic_chart": basic_chart,
            "dasha_chart": dasha_chart,
            "pratyantar_chart": pratyantar_chart,
            "methodology": {
                "system": system,
                "grid_type": grid_type,
                "description": "Deterministic 3x3 Numerology Chart calculation matching authentic Vedic and Lo Shu paradigms."
            }
        }