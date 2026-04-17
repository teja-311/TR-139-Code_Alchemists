import streamlit as st
import sys
import os
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data.vaccine_knowledge import VACCINE_DB, get_vaccines
from models.viability_calculator import calculate_viability_loss, get_tier_from_loss
from utils.ui_components import apply_custom_styles, render_sidebar

st.set_page_config(page_title="What-if Simulator", layout="wide")
apply_custom_styles()
render_sidebar()

st.title("🧪 Cold Chain 'What-if' Simulator")
st.markdown("Drag the sliders to simulate a fridge malfunction and instantly see the scientific and clinical impact on vaccine stock.")

# ── Sidebar Controls ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("---")
    st.markdown("### 🎛️ Scenario Configuration")
    sim_temp = st.slider("Simulated Fridge Temperature (°C)", -10.0, 40.0, 15.0, step=0.5)
    sim_duration = st.slider("Failure Duration (Hours)", 1, 120, 24)
    
    st.markdown("### 💰 Financial Assumptions")
    cost_per_dose = st.number_input("Avg Cost per Dose (₹)", value=250)

# ── Header Status ─────────────────────────────────────────────────────────────
status_color = "#FF1744" if (sim_temp > 8 or sim_temp < 2) else "#00E676"
status_text = "DANGEROUS BREACH" if (sim_temp > 8 or sim_temp < 2) else "SAFE RANGE"

st.markdown(f"""
    <div style="background-color: {status_color}22; border: 2px solid {status_color}; border-radius: 10px; padding: 20px; text-align: center; margin-bottom: 30px;">
        <h2 style="color: {status_color}; margin: 0;">{status_text}</h2>
        <p style="margin: 5px 0 0 0; font-size: 1.2rem;">Simulation: <strong>{sim_temp}°C</strong> for <strong>{sim_duration} hours</strong></p>
    </div>
""", unsafe_allow_html=True)

# ── Calculation Logic ─────────────────────────────────────────────────────────
vaccines = get_vaccines()
impact_data = []
total_loss_value = 0

for vac in vaccines:
    info = VACCINE_DB[vac]
    loss = calculate_viability_loss(vac, sim_temp, sim_duration)
    tier = get_tier_from_loss(loss)
    
    # Calculate simulated money loss (assuming 1000 doses per PHC for demo)
    doses = 1000
    monetary_loss = (loss / 100.0) * doses * cost_per_dose
    total_loss_value += monetary_loss
    
    impact_data.append({
        "Vaccine": vac,
        "Name": vac.split("(")[0].strip(),
        "Loss": loss,
        "Tier": tier,
        "Outcome": info['spoilage_tiers'][tier]['human_body_outcome'],
        "Monetary": monetary_loss
    })

# ── Summary Metrics ───────────────────────────────────────────────────────────
m1, m2, m3 = st.columns(3)
with m1:
    st.metric("Total Spoilage Projection", f"₹ {total_loss_value:,.0f}", delta=f"{total_loss_value/12:,.0f} per unit", delta_color="inverse")
with m2:
    avg_loss = sum(d['Loss'] for d in impact_data) / len(impact_data)
    st.metric("Avg Viability Loss", f"{avg_loss:.1f}%", delta=f"{'CRITICAL' if avg_loss > 50 else 'HIGH' if avg_loss > 20 else 'MODERATE' if avg_loss > 5 else 'LOW'}")
with m3:
    st.metric("Affected Units (Simulated)", "12 PHCs", help="Assuming a district-wide power grid failure")

st.markdown("---")

# ── Impact Grid ───────────────────────────────────────────────────────────────
cols = st.columns(3)
for i, data in enumerate(impact_data):
    with cols[i % 3]:
        # Determine color based on loss
        l = data['Loss']
        c = "#00E676" if l < 5 else "#FFEA00" if l < 20 else "#FF9100" if l < 50 else "#FF1744"
        
        st.markdown(f"""
            <div style="background-color: #162238; border: 1px solid #1e2c45; border-radius: 10px; padding: 20px; margin-bottom: 20px; border-top: 5px solid {c}; height: 280px; display: flex; flex-direction: column;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <h4 style="margin: 0; color: #fff;">{data['Name']}</h4>
                    <span style="background-color: {c}22; color: {c}; padding: 2px 8px; border-radius: 5px; font-size: 0.8rem; font-weight: bold;">{l:.1f}% LOSS</span>
                </div>
                <div style="margin-top: 15px; flex-grow: 1;">
                    <p style="font-size: 0.85rem; color: #aaa; margin: 0;">Clinical Outcome:</p>
                    <p style="font-size: 0.95rem; color: #eee; margin: 5px 0;">{data['Outcome']}</p>
                </div>
                <div style="margin-top: auto; border-top: 1px solid #1e2c45; padding-top: 10px; display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 0.8rem; color: #888;">Value At Risk:</span>
                    <span style="font-size: 1rem; color: #F43F5E; font-weight: bold;">₹ {data['Monetary']:,.0f}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.8rem; margin-top: 50px;">
        Scientific Basis: Q10 Thermostability Formulation (Rate_ref * Q10 ^ (delta_T / 10))
    </div>
""", unsafe_allow_html=True)
