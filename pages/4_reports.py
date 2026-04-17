import streamlit as st
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from reports.pdf_generator import generate_weekly_report
from utils.ui_components import apply_custom_styles, render_sidebar

st.set_page_config(page_title="Reports", layout="wide")
apply_custom_styles()
render_sidebar()

st.title("Compliance PDF Reports")

st.markdown("""
Generate the official Weekly Cold Chain Compliance & Spoilage Report for the District Health Officer. 
This report aggregates breach data and uses the Q10 model to flag required quarantines.
""")

if st.button("Generate Current Report"):
    with st.spinner("Generating PDF via ReportLab..."):
        report_path = os.path.join(os.path.dirname(__file__), "..", "compliance_report.pdf")
        generate_weekly_report(report_path)
        
        st.success("Report generated successfully!")
        
        with open(report_path, "rb") as pdf_file:
            st.download_button(
                label="📥 Download PDF",
                data=pdf_file,
                file_name="compliance_report.pdf",
                mime="application/pdf",
                type="primary"
            )
