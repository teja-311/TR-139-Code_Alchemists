import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data.database import get_connection, get_sensor_data_df, get_inventory_df
from data.phc_definitions import get_all_phcs
from models.viability_calculator import calculate_viability_loss
from utils.ui_components import apply_custom_styles, render_sidebar, render_metric_card

st.set_page_config(page_title="Unit Monitor", layout="wide")
apply_custom_styles()
render_sidebar()

st.title("Multi-Unit Deep Dive Monitor")

phcs = {p['name']: p['id'] for p in get_all_phcs()}
selected_phc_name = st.sidebar.selectbox("Select PHC Unit", list(phcs.keys()))
selected_phc_id = phcs[selected_phc_name]

st.subheader(f"Telemetry & Analytics: {selected_phc_name}")

@st.cache_data(ttl=60)
def fetch_unit_data(phc_id):
    # Fetch sensor data
    df_sensors = get_sensor_data_df(phc_id, limit=3000) # Ensure we get a good window
    
    # Fetch inventory
    df_inv = get_inventory_df(phc_id)
    
    # Fetch breaches
    conn = get_connection()
    df_breaches = pd.read_sql_query(f"SELECT * FROM breaches WHERE phc_id='{phc_id}'", conn)
    conn.close()
    
    return df_sensors, df_inv, df_breaches

df_sensors, df_inv, df_breaches = fetch_unit_data(selected_phc_id)

if df_sensors.empty:
    st.warning("No data found. Run simulation first.")
    st.stop()

# Time series chart
st.markdown("#### Live Time-Series Chart (Last 7 Days)")

# Ensure timestamp is datetime
df_sensors['timestamp'] = pd.to_datetime(df_sensors['timestamp'])

# Plotly dual axis
fig = go.Figure()

# Add Temperature Trace
fig.add_trace(go.Scatter(
    x=df_sensors['timestamp'], y=df_sensors['temperature'],
    line=dict(color='#00E676', width=2),
    name='Temperature (°C)'
))

# Add Humidity Trace
fig.add_trace(go.Scatter(
    x=df_sensors['timestamp'], y=df_sensors['humidity'],
    line=dict(color='#2196F3', width=1, dash='dot'),
    name='Humidity (%)',
    yaxis='y2'
))

# Add Safe Zones
fig.add_hrect(y0=2, y1=8, line_width=0, fillcolor="rgba(0, 230, 118, 0.1)", annotation_text="Safe Zone", annotation_position="top left")

fig.update_layout(
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    font=dict(color='#FFFFFF'),
    xaxis=dict(showgrid=True, gridcolor='#333', title="Time"),
    yaxis=dict(showgrid=True, gridcolor='#333', title="Temperature (°C)"),
    yaxis2=dict(title="Humidity (%)", overlaying='y', side='right', showgrid=False),
    hovermode='x unified',
    margin=dict(l=0, r=0, t=30, b=0)
)
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("#### Historical Breaches")
    if df_breaches.empty:
        st.success("No breaches recorded for this unit!")
    else:
        st.dataframe(df_breaches[['timestamp', 'type', 'temperature']], use_container_width=True, hide_index=True)

with col2:
    st.markdown("#### Affected Inventory & Quarantine Recs")
    
    if not df_inv.empty:
        # Calculate real-time cumulative spoilage for each vaccine based on df_breaches
        spoilage_data = []
        for idx, row in df_inv.iterrows():
            total_loss = 0.0
            
            # Aggregate loss from all breaches
            for _, breach in df_breaches.iterrows():
                # Assumption: average breach is ~4 hours in our simulation model
                loss = calculate_viability_loss(row['vaccine_name'], breach['temperature'], duration_hours=4.0)
                total_loss += loss
            
            total_loss = min(100.0, total_loss)
            status = "Quarantine" if total_loss > 10.0 else "OK"
            
            spoilage_data.append({
                "Vaccine": row['vaccine_name'],
                "Batch ID": row['batch_id'],
                "Viability Loss (%)": round(total_loss, 2),
                "Status": status
            })
        
        df_spoilage = pd.DataFrame(spoilage_data)
        
        # Style the dataframe
        def color_status(val):
            color = '#FF1744' if val == 'Quarantine' else '#00E676'
            return f'color: {color}'
            
        st.dataframe(df_spoilage.style.map(color_status, subset=['Status']), use_container_width=True, hide_index=True)
    else:
        st.info("No inventory data found.")
