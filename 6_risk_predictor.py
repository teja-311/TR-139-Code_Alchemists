import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys, os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data.phc_definitions import get_all_phcs
from models.risk_predictor import predict_tomorrow_risk
from utils.ui_components import apply_custom_styles, render_sidebar

st.set_page_config(page_title="Risk Predictor", layout="wide")
apply_custom_styles()
render_sidebar()

# ── Extra Page-level CSS ────────────────────────────────────────────────────────
st.markdown("""
<style>
.risk-card {
    background-color: #162238;
    border: 1px solid #1e2c45;
    border-radius: 10px;
    padding: 28px 32px;
    text-align: center;
}
.risk-probability {
    font-size: 4rem;
    font-weight: 800;
    line-height: 1;
    margin: 12px 0 4px 0;
}
.risk-label-low      { color: #00E676; }
.risk-label-medium   { color: #FFEA00; }
.risk-label-high     { color: #FF9800; }
.risk-label-critical { color: #F43F5E; }

.insight-card {
    background-color: #162238;
    border: 1px solid #1e2c45;
    border-radius: 8px;
    padding: 20px 24px;
    margin-bottom: 16px;
}
.factor-bar-bg {
    background-color: #0b1120;
    border-radius: 4px;
    height: 8px;
    overflow: hidden;
    width: 100%;
}
.factor-bar-fill {
    height: 8px;
    border-radius: 4px;
}
.stat-chip {
    display: inline-block;
    background: rgba(6,182,212,0.1);
    border: 1px solid rgba(6,182,212,0.25);
    color: #06B6D4;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.78rem;
    margin: 4px 4px 4px 0;
    font-weight: 600;
}
.warn-chip {
    background: rgba(244,63,94,0.1);
    border-color: rgba(244,63,94,0.3);
    color: #F43F5E;
}
</style>
""", unsafe_allow_html=True)

# ── Header ──────────────────────────────────────────────────────────────────────
st.title("🤖 AI Risk Predictor — Tomorrow's Breach Forecast")
st.markdown(
    "<p style='color:#8A9BB1;'>Random Forest model trained on rolling daily feature windows "
    "extracted from 30 days of IoT telemetry. Predicts cold-chain breach probability for the next 24 hours.</p>",
    unsafe_allow_html=True
)

# ── PHC Selection ───────────────────────────────────────────────────────────────
phcs = get_all_phcs()
phc_map = {p['name']: p for p in phcs}
selected_name = st.selectbox("Select PHC / Storage Unit", list(phc_map.keys()), key="rp_select")
phc_info = phc_map[selected_name]

st.markdown(
    f"<div style='color:#8A9BB1;font-size:0.9rem;margin-bottom:20px;'>"
    f"📍 {selected_name} — {phc_info['district']} District</div>",
    unsafe_allow_html=True
)

# ── Run Prediction ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=120, show_spinner=False)
def run_prediction(phc_id):
    return predict_tomorrow_risk(phc_id)

with st.spinner("Running AI model…"):
    result = run_prediction(phc_info['id'])

if not result['enough_data']:
    st.warning("⚠️ Fewer than 7 days of history — showing rule-based estimate. Run Simulation to generate more data.")

prob_pct = round(result['probability'] * 100, 1)
risk = result['risk_level']
risk_css = risk.lower()

# ── Color helpers ────────────────────────────────────────────────────────────────
RISK_COLORS = {
    'LOW':      '#00E676',
    'MEDIUM':   '#FFEA00',
    'HIGH':     '#FF9800',
    'CRITICAL': '#F43F5E',
}
risk_color = RISK_COLORS.get(risk, '#8A9BB1')

# ── Layout: Gauge | Insight card ─────────────────────────────────────────────────
left_col, right_col = st.columns([1, 1], gap="large")

with left_col:
    # Plotly Gauge
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=prob_pct,
        number={'suffix': '%', 'font': {'size': 48, 'color': risk_color}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': '#1e2c45',
                     'tickfont': {'color': '#8A9BB1'}},
            'bar': {'color': risk_color, 'thickness': 0.22},
            'bgcolor': '#162238',
            'borderwidth': 0,
            'steps': [
                {'range': [0, 30],  'color': 'rgba(0,230,118,0.08)'},
                {'range': [30, 55], 'color': 'rgba(255,234,0,0.08)'},
                {'range': [55, 75], 'color': 'rgba(255,152,0,0.08)'},
                {'range': [75, 100],'color': 'rgba(244,63,94,0.10)'},
            ],
            'threshold': {
                'line': {'color': risk_color, 'width': 3},
                'thickness': 0.8,
                'value': prob_pct
            }
        },
        title={'text': f"<b>Tomorrow's Breach Risk</b>",
               'font': {'color': '#8A9BB1', 'size': 15}},
        domain={'x': [0, 1], 'y': [0, 1]},
    ))
    fig_gauge.update_layout(
        paper_bgcolor='#162238',
        font={'color': '#8A9BB1'},
        margin=dict(l=20, r=20, t=30, b=10),
        height=320,
    )
    st.plotly_chart(fig_gauge, use_container_width=True)

    # Risk level badge + verdict
    risk_icons = {'LOW': '✅', 'MEDIUM': '⚠️', 'HIGH': '🔶', 'CRITICAL': '🚨'}
    st.markdown(
        f"<div class='risk-card' style='border-color:{risk_color}; border-width:2px;'>"
        f"<div class='risk-label-{risk_css}' style='font-size:1.8rem; font-weight:800;'>"
        f"{risk_icons.get(risk,'⚠️')} {risk} RISK</div>"
        f"<div class='risk-probability risk-label-{risk_css}'>{prob_pct}%</div>"
        f"<div style='color:#8A9BB1; font-size:0.9rem; margin-top:8px;'>"
        f"chance of cold-chain breach tomorrow</div>"
        f"</div>",
        unsafe_allow_html=True
    )

with right_col:
    # AI Insight Box
    st.markdown(
        f"<div class='insight-card'>"
        f"<p style='color:#8A9BB1;font-size:0.8rem;text-transform:uppercase;letter-spacing:0.1em;margin:0 0 6px 0;'>🤖 AI Insight</p>"
        f"<p style='font-size:1.05rem; color:#fff; margin:0;'>"
        f"Based on today's pattern, there is a <strong style='color:{risk_color}'>{prob_pct}% chance</strong> of a "
        f"cold-chain breach tomorrow — key driver: <em>{result['primary_factor']}</em>."
        f"</p></div>",
        unsafe_allow_html=True
    )

    # Today's Stats chips
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**📊 Today's Sensor Summary**")
    s = result['today_stats']
    chips = [
        (f"Avg Temp: {s['avg_temp']}°C",  s['avg_temp'] > 7),
        (f"Max Temp: {s['max_temp']}°C",  s['max_temp'] > 8),
        (f"Min Temp: {s['min_temp']}°C",  s['min_temp'] < 2),
        (f"Variance: {s['temp_variance']}°C²", s['temp_variance'] > 2),
        (f"Breaches Today: {s['breach_count_today']}", s['breach_count_today'] > 0),
        (f"Night Peak: {s['night_max_temp']}°C", s['night_max_temp'] > 9),
        (f"Temp Trend: {'↑ Rising' if s['trend_slope'] > 0.02 else '↓ Stable'}", s['trend_slope'] > 0.02),
    ]
    chip_html = ""
    for label, is_warn in chips:
        cls = "warn-chip" if is_warn else ""
        chip_html += f"<span class='stat-chip {cls}'>{label}</span>"
    st.markdown(chip_html, unsafe_allow_html=True)

    # Feature Importance Breakdown
    if result['top_features']:
        st.markdown("<br>**🔬 Top Risk Drivers (Model Feature Importance)**")
        feat_html = ""
        for feat, imp in result['top_features']:
            pct_imp = int(imp * 100)
            readable = feat.replace('_', ' ').title()
            feat_html += (
                f"<div style='margin-bottom:12px;'>"
                f"<div style='display:flex;justify-content:space-between;margin-bottom:4px;'>"
                f"<span style='color:#fff;font-size:0.85rem;'>{readable}</span>"
                f"<span style='color:{risk_color};font-size:0.85rem;font-weight:700;'>{pct_imp}%</span>"
                f"</div>"
                f"<div class='factor-bar-bg'>"
                f"<div class='factor-bar-fill' style='width:{pct_imp}%;background-color:{risk_color};'></div>"
                f"</div></div>"
            )
        st.markdown(feat_html, unsafe_allow_html=True)

# ── Network-wide Risk Heatmap ────────────────────────────────────────────────────
st.markdown("---")
st.subheader("🗺️ Network-Wide Tomorrow's Risk — All PHCs")
st.caption("Scores computed in parallel across all 12 PHCs using the same Random Forest engine.")

@st.cache_data(ttl=120, show_spinner=False)
def load_all_predictions():
    rows = []
    for p in get_all_phcs():
        res = predict_tomorrow_risk(p['id'])
        rows.append({
            'PHC': p['name'].replace(" PHC", ""),
            'District': p['district'],
            'Risk %': round(res['probability'] * 100, 1),
            'Level': res['risk_level'],
            'Key Driver': res['primary_factor'],
        })
    return pd.DataFrame(rows).sort_values('Risk %', ascending=False)

with st.spinner("Scoring all 12 PHCs…"):
    all_risk_df = load_all_predictions()

# Bar chart with color mapping
bar_colors = [RISK_COLORS.get(lvl, '#8A9BB1') for lvl in all_risk_df['Level']]
fig_bar = go.Figure(go.Bar(
    x=all_risk_df['PHC'],
    y=all_risk_df['Risk %'],
    marker_color=bar_colors,
    text=[f"{v}%" for v in all_risk_df['Risk %']],
    textposition='outside',
    textfont=dict(color='#FFFFFF', size=11),
    hovertemplate="<b>%{x}</b><br>Risk: %{y}%<extra></extra>",
))
fig_bar.update_layout(
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='#162238',
    font=dict(color='#8A9BB1'),
    xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(size=11)),
    yaxis=dict(showgrid=True, gridcolor='#1e2c45', zeroline=False, range=[0, 110],
               title='Breach Probability (%)'),
    margin=dict(l=20, r=20, t=20, b=20),
    height=340,
)
st.plotly_chart(fig_bar, use_container_width=True)

# Table below chart
st.markdown("<div class='dark-table-container'>", unsafe_allow_html=True)
RISK_BADGE = {
    'LOW':      "<span style='color:#00E676;background:rgba(0,230,118,0.1);padding:3px 10px;border-radius:4px;font-size:0.75rem;'>LOW</span>",
    'MEDIUM':   "<span style='color:#FFEA00;background:rgba(255,234,0,0.1);padding:3px 10px;border-radius:4px;font-size:0.75rem;'>MEDIUM</span>",
    'HIGH':     "<span style='color:#FF9800;background:rgba(255,152,0,0.1);padding:3px 10px;border-radius:4px;font-size:0.75rem;'>HIGH</span>",
    'CRITICAL': "<span style='color:#F43F5E;background:rgba(244,63,94,0.1);padding:3px 10px;border-radius:4px;font-size:0.75rem;'>CRITICAL</span>",
}
tbl_html = "<table class='dark-table'><thead><tr><th>PHC</th><th>District</th><th>Risk Score</th><th>Risk Level</th><th>Key Driver</th></tr></thead><tbody>"
for _, r in all_risk_df.iterrows():
    color_val = RISK_COLORS.get(r["Level"], '#8A9BB1')
    risk_pct = r['Risk %']
    pct_w = int(risk_pct)
    bar = (f"<div style='display:flex;align-items:center;gap:10px;'>"
           f"<div style='width:80px;background:#0b1120;border-radius:4px;height:6px;overflow:hidden;'>"
           f"<div style='width:{pct_w}%;background:{color_val};height:6px;border-radius:4px;'></div>"
           f"</div><span style='color:#fff;font-weight:700;'>{risk_pct}%</span></div>")
    tbl_html += (f"<tr><td><strong>{r['PHC']}</strong></td>"
                 f"<td style='color:#8A9BB1;'>{r['District']}</td>"
                 f"<td>{bar}</td>"
                 f"<td>{RISK_BADGE.get(r['Level'], r['Level'])}</td>"
                 f"<td style='color:#8A9BB1;font-size:0.82rem;'>{r['Key Driver']}</td></tr>")
tbl_html += "</tbody></table></div>"
st.markdown(tbl_html, unsafe_allow_html=True)
