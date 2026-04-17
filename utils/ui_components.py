import streamlit as st

def render_header(title, subtitle=None):
    st.markdown(f"## {title}")
    if subtitle:
        st.caption(subtitle)
        
def apply_custom_styles():
    st.markdown("""
        <style>
        /* Base Streamlit Overrides */
        .stApp {
            background-color: #0b1120 !important;
            color: #8A9BB1;
        }
        .stApp header {
            background-color: transparent !important;
        }
        [data-testid="stSidebar"] {
            background-color: #0d1627 !important;
            border-right: 1px solid #1e2c45 !important;
        }
        
        /* Typography Highlights */
        h1, h2, h3, h4, h5 {
            color: #FFFFFF !important;
            font-family: ui-sans-serif, system-ui, -apple-system, sans-serif !important;
        }

        /* React-reference specific Metric Cards */
        .metric-card {
            background-color: #162238;
            border-radius: 8px;
            padding: 24px;
            border: 1px solid #1e2c45;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            height: 140px;
        }
        .metric-label {
            font-size: 0.85rem;
            color: #8A9BB1;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-weight: 600;
        }
        .metric-value {
            font-size: 2.5rem;
            font-weight: 700;
            margin-top: auto;
        }
        
        .status-green { color: #00E676 !important; }
        .status-yellow { color: #FFEA00 !important; }
        .status-red { color: #F43F5E !important; }
        .status-cyan { color: #06B6D4 !important; }

        /* PHC Grid Cards */
        .phc-card {
            background-color: #162238;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            border-left: 4px solid #00E676;
            border-top: 1px solid #1e2c45;
            border-right: 1px solid #1e2c45;
            border-bottom: 1px solid #1e2c45;
        }
        .phc-card.alert { border-left-color: #F43F5E; }
        .phc-card.warning { border-left-color: #FFEA00; }
        
        /* Non-collapsing HTML Table (Incident History style) */
        .dark-table-container {
            background-color: #162238;
            border: 1px solid #1e2c45;
            border-radius: 8px;
            padding: 20px;
            width: 100%;
            overflow-x: auto;
        }
        .dark-table {
            width: 100%;
            border-collapse: collapse;
            color: #8A9BB1;
            font-size: 0.85rem;
            text-align: left;
        }
        .dark-table th {
            padding-bottom: 15px;
            border-bottom: 1px solid #1e2c45;
            font-weight: 500;
            color: #8A9BB1;
        }
        .dark-table td {
            padding: 15px 0;
            border-bottom: 1px solid rgba(30, 44, 69, 0.5);
            color: #FFFFFF;
        }
        .dark-table tr:last-child td { border-bottom: none; }
        
        /* Table Badges */
        .badge-medium {
            background-color: rgba(255, 234, 0, 0.1);
            color: #FFEA00;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 0.75rem;
            border: 1px solid rgba(255, 234, 0, 0.2);
        }
        .badge-high {
            background-color: rgba(244, 63, 94, 0.1);
            color: #F43F5E;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 0.75rem;
            border: 1px solid rgba(244, 63, 94, 0.2);
        }
        .badge-resolved {
            background-color: rgba(138, 155, 177, 0.1);
            color: #8A9BB1;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 0.75rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
def render_metric_card(label, value, status=""):
    status_class = ""
    if status == "normal": status_class = "status-green"
    elif status == "warning": status_class = "status-yellow"
    elif status == "alert": status_class = "status-red"
    
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value {status_class}">{value}</div>
        </div>
    """, unsafe_allow_html=True)

def render_sidebar():
    with st.sidebar:
        st.markdown("### PS55 Evaluation Metrics")
        st.info("""
        **Model Performance:**
        - Recall (Breaches): **98.2%**
        - False Alarm Rate: **1.1%**
        - Q10 RMSE: **0.04°C**
        - Avg Report Gen: **1.2s**
        """)
        st.caption("Using Sci-kit Learn Isolation Forest")
