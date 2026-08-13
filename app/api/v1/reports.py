"""Flask PDF Report Generation Blueprint."""
import io
from flask import Blueprint, request, send_file, jsonify
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from app.services.vedic_engine import generate_full_kundli

reports_bp = Blueprint('reports', __name__)

@reports_bp.route("/kundli-pdf", methods=["POST"])
def generate_kundli_pdf():
    """Generate and stream Janam Kundli PDF."""
    data = request.json or {}
    name = data.get("name", "Rahul Sharma")
    date_of_birth = data.get("date_of_birth", "1995-08-15")
    time_of_birth = data.get("time_of_birth", "06:30")
    place_of_birth = data.get("place_of_birth", "New Delhi, India")
    latitude = float(data.get("latitude", 28.6139))
    longitude = float(data.get("longitude", 77.2090))
    timezone = float(data.get("timezone", 5.5))

    kundli = generate_full_kundli(
        name, date_of_birth, time_of_birth,
        place_of_birth, latitude, longitude, timezone
    )
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#4338CA'),
        spaceAfter=12
    )
    
    elements = []
    elements.append(Paragraph("✨ ASTROTALK - VEDIC JANAM KUNDLI REPORT", title_style))
    elements.append(Spacer(1, 10))
    
    info_data = [
        ["Full Name", kundli["person_name"], "Date of Birth", kundli["date_of_birth"]],
        ["Time of Birth", kundli["time_of_birth"], "Place of Birth", kundli["place_of_birth"]],
        ["Ascendant (Lagna)", kundli["ascendant_lagna"], "Moon Sign (Rashi)", kundli["moon_sign_rashi"]],
        ["Nakshatra", f"{kundli['nakshatra']} (Pada {kundli['nakshatra_pada']})", "Active Mahadasha", kundli["current_running_dasha"]["active_mahadasha"]]
    ]
    t_info = Table(info_data, colWidths=[120, 150, 120, 150])
    t_info.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F1F5F9')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1E293B')),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(t_info)
    elements.append(Spacer(1, 16))
    
    elements.append(Paragraph("<b>Planetary Positions & Dignities</b>", styles['Heading2']))
    elements.append(Spacer(1, 8))
    
    planet_rows = [["Planet", "Sign", "House", "Degree", "Nakshatra", "Dignity"]]
    for p in kundli["planets"]:
        planet_rows.append([
            p["name"],
            p["sign"],
            str(p["house"]),
            p["degree_formatted"],
            p["nakshatra"],
            p["dignity"]
        ])
    t_planets = Table(planet_rows, colWidths=[110, 80, 50, 90, 90, 120])
    t_planets.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4338CA')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('PADDING', (0, 0), (-1, -1), 4.5),
    ]))
    elements.append(t_planets)
    
    doc.build(elements)
    buffer.seek(0)
    
    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"kundli_{name.replace(' ', '_')}.pdf"
    )
