import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
import pandas as pd
from datetime import datetime

# Local imports
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data.database import get_connection

def generate_weekly_report(output_filename="compliance_report.pdf"):
    print("Generating PDF Report...")
    doc = SimpleDocTemplate(output_filename, pagesize=A4,
                            rightMargin=40, leftMargin=40,
                            topMargin=40, bottomMargin=40)
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='CenterHeading', alignment=1, fontSize=16, spaceAfter=20, fontName='Helvetica-Bold'))
    
    elements = []
    
    # Header
    elements.append(Paragraph("Tamil Nadu District Health Office", styles['CenterHeading']))
    elements.append(Paragraph("Weekly Cold Chain Compliance & Spoilage Report", styles['CenterHeading']))
    elements.append(Paragraph(f"Date generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Intro
    intro_text = "This report summarizes temperature breaches across the monitored Primary Health Centers, flagging inventory that requires quarantine based on AI-estimated viability loss (Q10 Arrhenius model)."
    elements.append(Paragraph(intro_text, styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Get breach data
    conn = get_connection()
    df_breaches = pd.read_sql_query("SELECT phc_id, timestamp, temperature, type FROM breaches", conn)
    conn.close()
    
    if df_breaches.empty:
        elements.append(Paragraph("No breaches detected in the historical period.", styles['Heading2']))
    else:
        elements.append(Paragraph(f"Summary of Detected Breaches (Total: {len(df_breaches)})", styles['Heading2']))
        elements.append(Spacer(1, 10))
        
        # Table of breaches
        table_data = [['PHC ID', 'Timestamp', 'Max/Min Temp (°C)', 'Type']]
        for i, row in df_breaches.head(20).iterrows(): # Show top 20
            table_data.append([row['phc_id'], row['timestamp'], f"{row['temperature']:.1f}", row['type']])
            
        t = Table(table_data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2196F3')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(t)
        
        if len(df_breaches) > 20:
            elements.append(Spacer(1, 10))
            elements.append(Paragraph(f"...and {len(df_breaches) - 20} more. Refer to dashboard for full list.", styles['Normal']))
        
    elements.append(Spacer(1, 30))
    
    # Quarantine / Outcome Warning Section
    elements.append(Paragraph("Clinical Impact Advisory", styles['Heading2']))
    adv_text = "Failure to adhere to quarantine protocols for heat-exposed vaccines will result in direct clinical consequences. For example, administering spoiled Pentavalent vaccine to infants can result in total loss of immunity to Diphtheria, Pertussis, Tetanus, Hepatitis B, and Hib. The Q10 model has marked high-risk batches."
    elements.append(Paragraph(adv_text, styles['Normal']))
    
    # Footer
    elements.append(Spacer(1, 50))
    elements.append(Paragraph("Authorized by: AI System Auto-Generation", styles['Normal']))
    elements.append(Paragraph("For official use by TN District Health Officer", styles['Normal']))

    doc.build(elements)
    print(f"Report saved to {output_filename}")
    return output_filename

if __name__ == "__main__":
    generate_weekly_report()
