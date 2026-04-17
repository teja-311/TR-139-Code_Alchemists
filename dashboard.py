import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data.database import get_all_recent_sensor_data, get_connection
from data.phc_definitions import get_all_phcs
from utils.ui_components import apply_custom_styles, render_sidebar, render_metric_card

st.set_page_config(page_title="Dashboard", layout="wide")
apply_custom_styles()
render_sidebar()

st.title("Network Overview Dashboard")

@st.cache_data(ttl=60)
def fetch_dashboard_data():
    recent_data = get_all_recent_sensor_data()
    conn = get_connection()
    # Count breaches
    breaches_df = pd.read_sql_query("SELECT phc_id, COUNT(*) as breach_count FROM breaches GROUP BY phc_id", conn)
    conn.close()
    return recent_data, breaches_df

recent_data, breaches_df = fetch_dashboard_data()

phcs = get_all_phcs()

if recent_data.empty:
    st.warning("No sensor data available. Please run the Simulation module first.")
    st.stop()

# Summaries
col1, col2, col3 = st.columns(3)
total_phcs = len(phcs)
total_breaches = breaches_df['breach_count'].sum() if not breaches_df.empty else 0
active_alerts = len(recent_data[recent_data['is_anomaly'] == 1])

with col1: render_metric_card("Total Units Configured", total_phcs, "normal")
with col2: render_metric_card("Total Historical Breaches", total_breaches, "warning" if total_breaches > 0 else "normal")
with col3: render_metric_card("Current Active Alerts", active_alerts, "alert" if active_alerts > 0 else "normal")

if active_alerts > 0:
    import streamlit.components.v1 as components
    components.html("""
        <div style="display:flex; justify-content:center; align-items:center;">
             <button onclick="speakTamilAlert()" style="
                background-color: rgba(244, 63, 94, 0.2); 
                color: #F43F5E; 
                border: 1px solid rgba(244, 63, 94, 0.6); 
                padding: 12px 30px; 
                border-radius: 8px; 
                font-size: 1.0rem; 
                font-family: -apple-system, system-ui, sans-serif; 
                font-weight: bold; 
                cursor: pointer; 
                transition: all 0.2s;"
                onmouseover="this.style.backgroundColor='rgba(244, 63, 94, 0.4)'"
                onmouseout="this.style.backgroundColor='rgba(244, 63, 94, 0.2)'">
                <span style="font-size: 1.2rem;">🔊</span> Play Tamil Alert / தமிழ் எச்சரிக்கை
             </button>
        </div>
        <script>
            function speakTamilAlert() {
                window.speechSynthesis.cancel(); // kill any buffered speech
                var u = new SpeechSynthesisUtterance("எச்சரிக்கை! மருந்து குளிர்சாதனம் வெப்பமடைந்தது!");
                u.lang = "ta-IN";
                u.rate = 0.85; // slightly slower for clarity
                u.pitch = 1.0;
                window.speechSynthesis.speak(u);
            }
        </script>
    """, height=80)

st.markdown("---")

# ── Spoilage Score Map ────────────────────────────────────────────────────────
st.subheader("🗺️ Spoilage Score Map — Tamil Nadu PHC Network")
st.caption("Color-coded risk: 🟢 Safe · 🟡 Warning · 🔴 Danger. Hover for live details.")

# Build per-PHC score dataframe
map_rows = []
for phc in phcs:
    phc_data = recent_data[recent_data['phc_id'] == phc['id']]
    breach_info = breaches_df[breaches_df['phc_id'] == phc['id']]
    b_count = int(breach_info['breach_count'].values[0]) if not breach_info.empty else 0

    temp_val, is_alert = None, False
    if not phc_data.empty:
        row = phc_data.iloc[0]
        temp_val = row['temperature']
        is_alert = bool(row['is_anomaly'] == 1)

    # Classify risk
    if is_alert or (temp_val is not None and (temp_val > 8.0 or temp_val < 2.0)):
        risk = "DANGER"
        color = "#F43F5E"          # red
        symbol = "circle"
        size = 18
    elif b_count > 2:
        risk = "WARNING"
        color = "#FFEA00"          # yellow
        symbol = "circle"
        size = 15
    else:
        risk = "SAFE"
        color = "#00E676"          # green
        symbol = "circle"
        size = 14

    temp_str = f"{temp_val:.1f}°C" if temp_val is not None else "No data"
    hover = (f"<b>{phc['name']}</b><br>"
             f"District: {phc['district']}<br>"
             f"Status: <b>{risk}</b><br>"
             f"Live Temp: {temp_str}<br>"
             f"Historical Breaches: {b_count}")

    map_rows.append({
        "name": phc['name'],
        "lat": phc['lat'],
        "lon": phc['lon'],
        "risk": risk,
        "color": color,
        "size": size,
        "hover": hover,
    })

map_df = pd.DataFrame(map_rows)

# Build Plotly scattermapbox (token-free open-street-map tiles)
fig_map = go.Figure()
for risk_level, marker_color in [("DANGER", "#F43F5E"), ("WARNING", "#FFEA00"), ("SAFE", "#00E676")]:
    subset = map_df[map_df['risk'] == risk_level]
    if subset.empty:
        continue
    fig_map.add_trace(go.Scattermapbox(
        lat=subset['lat'],
        lon=subset['lon'],
        mode='markers+text',
        marker=dict(
            size=subset['size'],
            color=marker_color,
            opacity=0.92,
        ),
        text=subset['name'].str.replace(" PHC", ""),
        textfont=dict(color="#FFFFFF", size=11),
        textposition="top right",
        customdata=subset['hover'],
        hovertemplate="%{customdata}<extra></extra>",
        name=risk_level,
    ))

fig_map.update_layout(
    mapbox=dict(
        style="carto-darkmatter",
        center=dict(lat=10.85, lon=78.70),
        zoom=8.0,
    ),
    paper_bgcolor="#0b1120",
    plot_bgcolor="#0b1120",
    margin=dict(l=0, r=0, t=0, b=0),
    height=480,
    legend=dict(
        bgcolor="rgba(22,34,56,0.9)",
        bordercolor="#1e2c45",
        borderwidth=1,
        font=dict(color="#8A9BB1"),
        x=0.01, y=0.98,
    ),
    font=dict(color="#8A9BB1"),
)

st.plotly_chart(fig_map, use_container_width=True)

st.markdown("---")
st.subheader("PHC Live Status Grid")

cols = st.columns(3)
for i, phc in enumerate(phcs):
    with cols[i % 3]:
        # Get data for this PHC
        phc_data = recent_data[recent_data['phc_id'] == phc['id']]
        breach_info = breaches_df[breaches_df['phc_id'] == phc['id']]
        b_count = breach_info['breach_count'].values[0] if not breach_info.empty else 0
        
        status_class = "phc-card"
        temp_str = "--"
        hum_str = "--"
        ts_str = "--"
        
        if not phc_data.empty:
            row = phc_data.iloc[0]
            temp = row['temperature']
            hum = row['humidity']
            ts_str = row['timestamp']
            
            temp_str = f"{temp:.1f} °C"
            hum_str = f"{hum:.1f} %"
            
            if row['is_anomaly'] == 1:
                status_class = "phc-card alert"
            elif temp < 2.0 or temp > 8.0:
                status_class = "phc-card warning"
        
        st.markdown(f"""
            <div class="{status_class}">
                <h4>{phc['name']}</h4>
                <p style="margin:0; color:#aaa;">{phc['district']} District</p>
                <hr style="margin:10px 0; border-color:#444;" />
                <div style="display:flex; justify-content:space-between;">
                    <div>Temp: <strong>{temp_str}</strong></div>
                    <div>Hum: <strong>{hum_str}</strong></div>
                </div>
                <div style="margin-top:5px; font-size:0.85em;">
                    Previous Breaches: {b_count} | Last Update: {ts_str.split(' ')[1] if ts_str != '--' else ts_str}
                </div>
            </div>
        """, unsafe_allow_html=True)
