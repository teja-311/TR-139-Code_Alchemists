import streamlit as st
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from simulator.iot_simulator import generate_sensor_data
from models.anomaly_detector import run_anomaly_detection
from utils.ui_components import apply_custom_styles, render_sidebar

st.set_page_config(page_title="Simulation Control", layout="wide")
apply_custom_styles()
render_sidebar()

st.title("Data Simulation & Model Execution")

st.markdown("""
Use this module to generate 30 days of realistic time-series IoT data for the 12 Primary Health Centers.
The simulation will automatically inject temperature breaches and random hardware failures.
It will then run the **Isolation Forest Anomaly Detection** model to flag these breaches.
""")

if st.button("Generate 30 Days Synthetic IoT Data"):
    with st.spinner("Generating IoT Data (This may take a few seconds)..."):
        generate_sensor_data(days=30, interval_minutes=15)
    
    with st.spinner("Running Isolation Forest Anomaly Detection..."):
        run_anomaly_detection()
        
    st.success("Simulation & Anomaly Detection Completed Successfully!")
    st.info("Check the Dashboard and Unit Monitor to view the results.")
