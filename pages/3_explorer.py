import streamlit as st
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data.vaccine_knowledge import VACCINE_DB, get_vaccines
from utils.ui_components import apply_custom_styles, render_sidebar

st.set_page_config(page_title="Impact Explorer", layout="wide")
apply_custom_styles()
render_sidebar()

st.title("Vaccine Spoilage Impact Explorer")
st.markdown("Explore the detailed clinical consequences of administering temperature-breached vaccines based on Q10 estimated viability loss tiers.")

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### Selection")
    vaccine_name = st.selectbox("Select Vaccine", get_vaccines())
    
    # 0 to 100 step 10
    spoilage = st.slider("Select Estimated Spoilage (%)", 0, 100, 15, step=10)
    
    info = VACCINE_DB[vaccine_name]
    st.markdown(f"**Target Disease:** {info['disease']}")
    st.markdown(f"**Storage Range:** {info['temp_range'][0]} to {info['temp_range'][1]} °C")
    
    tier_idx = min(spoilage // 10, 9)
    tier_key = f"{tier_idx*10}-{(tier_idx+1)*10}%"
    tier_data = info['spoilage_tiers'][tier_key]
    
    st.markdown(f"### Tier: {tier_key} Loss")
    st.info(f"**Efficacy Remaining:** {tier_data['efficacy_retained']}")

with col2:
    st.markdown("### Human-Body Clinical Outcomes")
    
    st.warning(tier_data['human_body_outcome'])
    
    st.markdown("### Representative Medical Evidence (Symptoms/Pathology)")
    st.caption("Warning: Contains medical imagery")
    
    img_col1, img_col2 = st.columns(2)
    
    import requests
    
    @st.cache_data(ttl=3600, show_spinner=False)
    def fetch_image_bytes(url):
        headers = {'User-Agent': 'Mozilla/5.0 (ColdChainApp/1.0)'}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            return response.content
        return None

    def render_image(url, caption):
        try:
            content = fetch_image_bytes(url)
            if content:
                st.image(content, caption=caption, use_container_width=True)
            else:
                st.error("Image load failed (HTTP 429 Rate Limited or 404)")
        except Exception as e:
            st.error(f"Error loading image: {e}")
            
    with img_col1:
        render_image(info['images'][0], f"{vaccine_name} failure clinical sign 1")
            
    with img_col2:
        render_image(info['images'][1], f"{vaccine_name} failure clinical sign 2")
