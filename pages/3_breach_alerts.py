import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
import os
import urllib.parse
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data.database import (get_connection, get_sensor_data_df, get_inventory_df,
                            log_quarantine_action, get_quarantine_log)
from data.phc_definitions import get_all_phcs
from models.viability_calculator import calculate_viability_loss
from utils.ui_components import apply_custom_styles, render_sidebar, render_metric_card

st.set_page_config(page_title="Breach Alerts", layout="wide")
apply_custom_styles()
render_sidebar()

# ── CSS for quarantine panel ────────────────────────────────────────────────────
st.markdown("""
<style>
.quarantine-panel {
    background: linear-gradient(135deg, rgba(244,63,94,0.08) 0%, rgba(22,34,56,1) 60%);
    border: 1px solid rgba(244,63,94,0.4);
    border-radius: 10px;
    padding: 24px;
    margin: 16px 0;
}
.whatsapp-btn {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background-color: #25D366;
    color: #fff !important;
    padding: 10px 22px;
    border-radius: 8px;
    font-weight: 700;
    font-size: 0.9rem;
    text-decoration: none !important;
    border: none;
    cursor: pointer;
}
.whatsapp-btn:hover { background-color: #1aad52; }
.quarantine-badge {
    background: rgba(244,63,94,0.15);
    color: #F43F5E;
    border: 1px solid rgba(244,63,94,0.4);
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 700;
}
.quarantine-done-badge {
    background: rgba(0,230,118,0.12);
    color: #00E676;
    border: 1px solid rgba(0,230,118,0.3);
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 700;
}
</style>
""", unsafe_allow_html=True)

# ── Facility Selection ───────────────────────────────────────────────────────────
phcs = {p['name']: p for p in get_all_phcs()}
selected_phc_name = st.selectbox("Select Storage Unit / PHC", list(phcs.keys()), key="ba_select")
phc_info = phcs[selected_phc_name]
selected_phc_id = phc_info['id']

st.markdown(
    f"<div style='color:#8A9BB1;font-size:0.9rem;margin-bottom:20px;'>"
    f"📍 {selected_phc_name}, {phc_info['district']} District &nbsp;|&nbsp; "
    f"📦 Capacity: {phc_info['capacity_liters']}L</div>",
    unsafe_allow_html=True
)

# ── Officer Phone Config (sidebar) ───────────────────────────────────────────────
with st.sidebar:
    st.markdown("---")
    st.markdown("### 📱 District Officer Contact")
    officer_phone = st.text_input(
        "WhatsApp Phone (with country code)",
        value="+919876543210",
        help="e.g. +91 9876543210 — used for auto-quarantine WhatsApp alerts"
    )

@st.cache_data(ttl=30)
def fetch_data(phc_id):
    df_sensors = get_sensor_data_df(phc_id, limit=3000)
    df_inv = get_inventory_df(phc_id)
    conn = get_connection()
    df_breaches = pd.read_sql_query(
        f"SELECT * FROM breaches WHERE phc_id='{phc_id}' ORDER BY timestamp DESC", conn)
    conn.close()
    return df_sensors, df_inv, df_breaches

df_sensors, df_inv, df_breaches = fetch_data(selected_phc_id)

if df_sensors.empty:
    st.warning("No data found. Please run the Simulation module first.")
    st.stop()

current_temp = df_sensors.iloc[-1]['temperature']
current_hum = df_sensors.iloc[-1]['humidity']
total_breaches = len(df_breaches)
temp_in_danger = current_temp > 8 or current_temp < 2

# ── Top Metric Cards ─────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns(3)
with c1:
    render_metric_card("CURRENT TEMPERATURE", f"{current_temp:.1f}°C",
                       "alert" if temp_in_danger else "cyan")
with c2:
    render_metric_card("CURRENT HUMIDITY", f"{current_hum:.1f}%", "cyan")
with c3:
    render_metric_card("BREACH HISTORY", str(total_breaches),
                       "alert" if total_breaches > 0 else "normal")

# ── Auto-Quarantine + WhatsApp Panel (shown when temp is DANGER) ────────────────
if temp_in_danger or total_breaches > 0:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div class='quarantine-panel'>
        <h4 style='margin:0 0 8px 0; color:#F43F5E;'>🚨 Active Breach Detected — Quarantine Action Required</h4>
        <p style='color:#8A9BB1; font-size:0.9rem; margin-bottom:16px;'>
        Select a vaccine batch below to quarantine it and send an instant WhatsApp alert to the District Officer.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Batch selector
    at_risk_batches = df_inv[df_inv['status'] != 'QUARANTINED']
    if at_risk_batches.empty:
        st.success("✅ All batches at this unit are already quarantined.")
    else:
        batch_options = {
            f"{row['batch_id']} — {row['vaccine_name'].split('(')[0].strip()} ({row['quantity']} units)": row
            for _, row in at_risk_batches.iterrows()
        }
        selected_batch_label = st.selectbox(
            "🔬 Select Batch to Quarantine",
            list(batch_options.keys()),
            key="qbatch"
        )
        selected_batch = batch_options[selected_batch_label]

        # Build the WhatsApp message
        breach_temp = df_breaches.iloc[0]['temperature'] if not df_breaches.empty else current_temp
        breach_ts = df_breaches.iloc[0]['timestamp'] if not df_breaches.empty else "now"
        msg = (
            f"⚠️ COLD CHAIN BREACH ALERT\n"
            f"PHC: {selected_phc_name}\n"
            f"District: {phc_info['district']}\n"
            f"Batch: {selected_batch['batch_id']}\n"
            f"Vaccine: {selected_batch['vaccine_name'].split('(')[0].strip()}\n"
            f"Quantity: {selected_batch['quantity']} units\n"
            f"Breach Temp: {breach_temp:.1f}°C (safe: 2–8°C)\n"
            f"Detected At: {breach_ts}\n\n"
            f"Action Required: Quarantine this batch immediately.\n"
            f"Reply CONFIRMED to acknowledge."
        )
        encoded_msg = urllib.parse.quote(msg)
        phone_clean = officer_phone.replace("+", "").replace(" ", "")
        wa_url = f"https://wa.me/{phone_clean}?text={encoded_msg}"

        # Two action columns
        btn_col1, btn_col2 = st.columns([1, 1])

        with btn_col1:
            # WhatsApp deep-link button (opens WhatsApp with pre-filled message)
            st.markdown(
                f"<a href='{wa_url}' target='_blank' class='whatsapp-btn'>"
                f"<svg xmlns='http://www.w3.org/2000/svg' width='18' height='18' fill='white' viewBox='0 0 16 16'>"
                f"<path d='M13.601 2.326A7.85 7.85 0 0 0 7.994 0C3.627 0 .068 3.558.064 7.926c0 1.399.366 2.76 1.057 3.965L0 16l4.204-1.102a7.9 7.9 0 0 0 3.79.965h.004c4.368 0 7.926-3.558 7.93-7.93A7.9 7.9 0 0 0 13.6 2.326zM7.994 14.521a6.6 6.6 0 0 1-3.356-.92l-.24-.144-2.494.654.666-2.433-.156-.251a6.56 6.56 0 0 1-1.007-3.505c0-3.626 2.957-6.584 6.591-6.584a6.56 6.56 0 0 1 4.66 1.931 6.56 6.56 0 0 1 1.928 4.66c-.004 3.639-2.961 6.592-6.592 6.592'/>"
                f"</svg>"
                f" Send WhatsApp Alert</a>",
                unsafe_allow_html=True
            )

        with btn_col2:
            if st.button("🔒 Confirm Quarantine in System", key="quarantine_btn", type="primary"):
                log_quarantine_action(
                    phc_id=selected_phc_id,
                    phc_name=selected_phc_name,
                    batch_id=selected_batch['batch_id'],
                    vaccine_name=selected_batch['vaccine_name'],
                    quantity=selected_batch['quantity'],
                    officer_phone=officer_phone
                )
                st.cache_data.clear()
                st.success(
                    f"✅ Batch **{selected_batch['batch_id']}** has been marked as **QUARANTINED** "
                    f"and the officer at {officer_phone} was notified via WhatsApp!"
                )
                st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# ── Telemetry Chart ──────────────────────────────────────────────────────────────
st.markdown("<div style='background-color: #162238; border: 1px solid #1e2c45; border-radius: 8px; padding: 20px;'>", unsafe_allow_html=True)
st.markdown("<h4 style='margin:0 0 5px 0; font-size: 1.1rem;'>Sensor Telemetry (Last 24h)</h4><p style='color:#8A9BB1; font-size:0.85rem; margin-top:0;'>Live temperature with safe-zone threshold lines</p>", unsafe_allow_html=True)

df_sensors['timestamp'] = pd.to_datetime(df_sensors['timestamp'])
recent_sensors = df_sensors.tail(96)

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=recent_sensors['timestamp'], y=recent_sensors['temperature'],
    line=dict(color='#06B6D4', width=2), name='Temp (°C)',
    fill='tozeroy', fillcolor='rgba(6,182,212,0.06)'
))
fig.add_hrect(y0=2, y1=8, line_width=1, line_dash="dash",
              line_color="#00E676", fillcolor="rgba(0,230,118,0.04)",
              annotation_text="Safe Zone", annotation_font_color="#00E676",
              annotation_position="top left")
fig.update_layout(
    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
    font=dict(color='#8A9BB1'),
    xaxis=dict(showgrid=False, zeroline=False),
    yaxis=dict(showgrid=True, gridcolor='#1e2c45', zeroline=False, range=[0, 20]),
    margin=dict(l=0, r=0, t=10, b=0), height=300, showlegend=False
)
st.plotly_chart(fig, use_container_width=True)
st.markdown("</div><br>", unsafe_allow_html=True)

# ── Inventory + Incident History ─────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown("<div class='dark-table-container'>", unsafe_allow_html=True)
    st.markdown("<h4 style='margin:0 0 5px 0;'>Inventory in Unit</h4><p style='color:#8A9BB1;font-size:0.85rem;margin-top:0;'>Vaccine batches currently stored here</p>", unsafe_allow_html=True)

    html = "<table class='dark-table'><thead><tr><th>Vaccine</th><th>Batch</th><th>Qty</th><th>Viability</th><th>Status</th></tr></thead><tbody>"
    for _, row in df_inv.iterrows():
        loss = sum(calculate_viability_loss(row['vaccine_name'], b['temperature'], 4.0)
                   for _, b in df_breaches.iterrows())
        viability = max(0.0, 100.0 - loss)
        vs = f"<span style='color:{'#F43F5E' if viability < 90 else '#FFEA00' if viability < 98 else '#00E676'}'>{viability:.1f}%</span>"
        v_name = row['vaccine_name'].split("(")[0].strip()[:20]
        status_html = "<span class='quarantine-badge'>QUARANTINED</span>" if row.get('status') == 'QUARANTINED' else "<span style='color:#00E676'>Active</span>"
        html += f"<tr><td><strong>{v_name}</strong></td><td style='color:#8A9BB1;font-size:0.8rem;'>{row['batch_id']}</td><td>{row['quantity']}</td><td>{vs}</td><td>{status_html}</td></tr>"
    html += "</tbody></table></div>"
    st.markdown(html, unsafe_allow_html=True)

with col2:
    st.markdown("<div class='dark-table-container'>", unsafe_allow_html=True)
    st.markdown("<h4 style='margin:0 0 5px 0;'>Incident History</h4><p style='color:#8A9BB1;font-size:0.85rem;margin-top:0;'>Detected anomalies and breaches for this unit</p>", unsafe_allow_html=True)

    html = "<table class='dark-table'><thead><tr><th>Detected</th><th>Severity</th><th>Status</th><th>Impact</th></tr></thead><tbody>"
    if df_breaches.empty:
        html += "<tr><td colspan='4'>No incidents recorded</td></tr>"
    else:
        for i, row in df_breaches.head(6).iterrows():
            dt = datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S').strftime('%b %d, %H:%M')
            sev = "HIGH" if row['temperature'] > 12 or row['temperature'] < 0 else "MEDIUM"
            sev_badge = f"<span class='badge-high'>{sev}</span>" if sev == "HIGH" else f"<span class='badge-medium'>{sev}</span>"
            status = "Open" if i == df_breaches.index[0] else "Resolved"
            stat_badge = f"<span class='badge-high'>{status}</span>" if status == "Open" else f"<span class='badge-resolved'>{status}</span>"
            impact = f"-{min(15.0, abs(row['temperature'] - 8) * 1.5):.1f}%"
            html += f"<tr><td style='color:#8A9BB1;'>{dt}</td><td>{sev_badge}</td><td>{stat_badge}</td><td style='color:#FFEA00;'>{impact}</td></tr>"
    html += "</tbody></table></div>"
    st.markdown(html, unsafe_allow_html=True)

# ── Quarantine Action Log ─────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("<div class='dark-table-container'>", unsafe_allow_html=True)
st.markdown("<h4 style='margin:0 0 5px 0;'>📋 Quarantine Action Log</h4><p style='color:#8A9BB1;font-size:0.85rem;margin-top:0;'>Audit trail of all quarantine actions across the PHC network</p>", unsafe_allow_html=True)

qlog = get_quarantine_log()
if qlog.empty:
    st.markdown("<p style='color:#8A9BB1; padding:16px 0;'>No quarantine actions recorded yet.</p>", unsafe_allow_html=True)
else:
    html = "<table class='dark-table'><thead><tr><th>PHC</th><th>Batch</th><th>Vaccine</th><th>Qty</th><th>Officer Notified</th><th>Actioned At</th><th>WhatsApp</th></tr></thead><tbody>"
    for _, row in qlog.iterrows():
        wa_icon = "<span style='color:#25D366;font-size:1.1rem;'>✅ Sent</span>" if row['whatsapp_sent'] else "<span style='color:#8A9BB1;'>—</span>"
        vac_short = str(row['vaccine_name']).split("(")[0].strip()[:22]
        html += (f"<tr><td><strong>{row['phc_name']}</strong></td>"
                 f"<td style='color:#8A9BB1;font-size:0.8rem;'>{row['batch_id']}</td>"
                 f"<td>{vac_short}</td>"
                 f"<td>{row['quantity']}</td>"
                 f"<td style='color:#8A9BB1;'>{row['officer_phone']}</td>"
                 f"<td style='color:#8A9BB1;font-size:0.8rem;'>{row['actioned_at']}</td>"
                 f"<td>{wa_icon}</td></tr>")
    html += "</tbody></table>"
    st.markdown(html, unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)
