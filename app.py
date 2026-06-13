"""
╔══════════════════════════════════════════════════════════════════════╗
║          SOLARX PROFESSIONAL — SOLAR POWER ESTIMATOR PRO            ║
║          Enterprise Edition v3.0 | Ready for Commercial Sale         ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import streamlit as st

st.set_page_config(
    page_title="SolarX Pro — Enterprise Solar Estimator",
    layout="wide",
    page_icon="☀️",
    initial_sidebar_state="expanded",
)

# ─── TERMS & AGREEMENT ───────────────────────────────────────────────────────
def show_terms():
    @st.dialog("📄 Terms & Privacy Agreement — SolarX Professional")
    def terms_dialog():
        st.markdown("""
        <div style='background:#0f172a;padding:16px;border-radius:12px;color:#e2e8f0;font-size:0.92rem'>

        ### ⚠️ Important Disclaimer

        By using **SolarX Professional**, you confirm:

        1. **No Liability** — Calculations are for planning only. We are not liable for financial loss or installation errors.
        2. **Data Privacy** — Location data is used solely for weather API calls. Nothing is stored or shared.
        3. **Accuracy** — Results may vary ±20% due to real-world conditions.
        4. **Third-Party APIs** — Uses Open-Meteo & Nominatim. Offline fallback uses database values.
        5. **Professional Advice** — Always consult a certified solar engineer before installation.

        </div>
        """, unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("❌ Decline", use_container_width=True, type="secondary"):
                st.stop()
        with c2:
            if st.button("✅ I Agree & Continue", use_container_width=True, type="primary"):
                st.session_state['agreed'] = True
                st.rerun()
    if 'agreed' not in st.session_state:
        terms_dialog()
        st.stop()

show_terms()

# ─── IMPORTS ─────────────────────────────────────────────────────────────────
import pandas as pd
import numpy as np
import math
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime
import datetime as dt
import requests
from io import BytesIO

GEO_ENABLED = False
try:
    from geopy.geocoders import Nominatim
    GEO_ENABLED = True
except Exception:
    pass

PDF_ENABLED = False
FPDF = None
try:
    from fpdf import FPDF
    PDF_ENABLED = True
except Exception:
    pass

FOLIUM_ENABLED = False
try:
    import folium
    from streamlit_folium import st_folium
    FOLIUM_ENABLED = True
except Exception:
    pass

# ─── GLOBAL THEME ────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Space+Grotesk:wght@400;500;700&display=swap');

:root {
  --solar-gold: #F59E0B;
  --solar-amber: #FCD34D;
  --deep-navy: #0B1437;
  --mid-navy: #0F2057;
  --panel-blue: #1E3A8A;
  --sky-cyan: #06B6D4;
  --energy-green: #10B981;
  --alert-red: #EF4444;
  --text-primary: #F1F5F9;
  --text-muted: #94A3B8;
  --glass: rgba(255,255,255,0.05);
  --glass-border: rgba(255,255,255,0.10);
}

html, body, [class*="css"] {
  font-family: 'Inter', sans-serif;
  color: var(--text-primary);
}

.stApp {
  background: linear-gradient(160deg, #0B1437 0%, #0F2057 40%, #0B2040 70%, #071020 100%);
  background-attachment: fixed;
  min-height: 100vh;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
  background: rgba(11,20,55,0.97) !important;
  border-right: 1px solid var(--glass-border) !important;
}
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stNumberInput label,
[data-testid="stSidebar"] .stSlider label,
[data-testid="stSidebar"] p {
  color: #CBD5E1 !important;
  font-size: 0.82rem !important;
}

/* ── Metrics ── */
[data-testid="stMetricValue"] {
  color: var(--solar-gold) !important;
  font-family: 'Space Grotesk', sans-serif !important;
  font-size: 1.5rem !important;
  font-weight: 700 !important;
}
[data-testid="stMetricLabel"] { color: var(--text-muted) !important; font-size: 0.75rem !important; text-transform: uppercase; letter-spacing: 0.08em; }
[data-testid="stMetricDelta"] { font-size: 0.78rem !important; }
div[data-testid="metric-container"] {
  background: var(--glass) !important;
  border: 1px solid var(--glass-border) !important;
  border-radius: 16px !important;
  padding: 18px 20px !important;
  backdrop-filter: blur(20px) !important;
  transition: transform 0.2s ease, border-color 0.2s ease;
}
div[data-testid="metric-container"]:hover {
  transform: translateY(-3px);
  border-color: var(--solar-gold) !important;
}

/* ── Tabs ── */
div[data-testid="stTabs"] [data-baseweb="tab-list"] {
  background: rgba(11,20,55,0.5) !important;
  border-radius: 14px !important;
  padding: 6px !important;
  border: 1px solid var(--glass-border) !important;
  gap: 4px !important;
  flex-wrap: wrap;
}
div[data-testid="stTabs"] button[data-baseweb="tab"] {
  background: transparent !important;
  color: var(--text-muted) !important;
  border-radius: 10px !important;
  font-weight: 500 !important;
  font-size: 0.8rem !important;
  padding: 8px 14px !important;
  border: none !important;
  transition: all 0.2s;
}
div[data-testid="stTabs"] button[aria-selected="true"] {
  background: linear-gradient(135deg, var(--solar-gold), #D97706) !important;
  color: #0B1437 !important;
  font-weight: 700 !important;
}

/* ── Expanders ── */
[data-testid="stExpander"] {
  background: var(--glass) !important;
  border: 1px solid var(--glass-border) !important;
  border-radius: 14px !important;
}
[data-testid="stExpander"] summary {
  color: var(--solar-gold) !important;
  font-weight: 600 !important;
}

/* ── Inputs ── */
.stSelectbox > div > div,
.stNumberInput > div > div > input,
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
  background: rgba(15,32,87,0.8) !important;
  border: 1px solid rgba(245,158,11,0.25) !important;
  border-radius: 10px !important;
  color: var(--text-primary) !important;
}
.stSelectbox > div > div:focus-within,
.stNumberInput > div > div > input:focus {
  border-color: var(--solar-gold) !important;
  box-shadow: 0 0 0 3px rgba(245,158,11,0.15) !important;
}

/* ── Slider ── */
.stSlider [data-baseweb="slider"] [data-testid="stSlider"] div {
  background: var(--solar-gold) !important;
}
.stSlider .rc-slider-track { background: var(--solar-gold) !important; }
.stSlider .rc-slider-handle { border-color: var(--solar-gold) !important; }

/* ── Buttons ── */
.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, var(--solar-gold), #D97706) !important;
  color: #0B1437 !important;
  border: none !important;
  border-radius: 10px !important;
  font-weight: 700 !important;
}
.stButton > button[kind="secondary"] {
  background: var(--glass) !important;
  color: var(--text-primary) !important;
  border: 1px solid var(--glass-border) !important;
  border-radius: 10px !important;
}
.stDownloadButton > button {
  background: linear-gradient(135deg, var(--energy-green), #059669) !important;
  color: white !important;
  border: none !important;
  border-radius: 10px !important;
  font-weight: 600 !important;
  width: 100%;
}

/* ── Cards ── */
.sxpro-card {
  background: rgba(15,32,87,0.4);
  border: 1px solid rgba(245,158,11,0.2);
  border-radius: 16px;
  padding: 20px 24px;
  margin: 8px 0;
  backdrop-filter: blur(16px);
}
.sxpro-card h4 { color: var(--solar-gold); margin: 0 0 12px 0; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.08em; }
.sxpro-card p  { color: var(--text-muted); margin: 4px 0; font-size: 0.88rem; }
.sxpro-card strong { color: var(--text-primary); }

/* ── Alert banners ── */
.sxpro-warn  { background: rgba(245,158,11,0.15); border-left: 4px solid var(--solar-gold); border-radius: 0 10px 10px 0; padding: 12px 16px; color: #FCD34D; margin: 8px 0; }
.sxpro-error { background: rgba(239,68,68,0.15);  border-left: 4px solid var(--alert-red);  border-radius: 0 10px 10px 0; padding: 12px 16px; color: #FCA5A5; margin: 8px 0; }
.sxpro-ok    { background: rgba(16,185,129,0.15); border-left: 4px solid var(--energy-green); border-radius: 0 10px 10px 0; padding: 12px 16px; color: #6EE7B7; margin: 8px 0; }
.sxpro-info  { background: rgba(6,182,212,0.12);  border-left: 4px solid var(--sky-cyan);   border-radius: 0 10px 10px 0; padding: 12px 16px; color: #67E8F9; margin: 8px 0; }

/* ── Page header ── */
.sxpro-header {
  background: linear-gradient(135deg, rgba(245,158,11,0.12), rgba(30,58,138,0.4));
  border: 1px solid rgba(245,158,11,0.3);
  border-radius: 20px;
  padding: 28px 36px;
  margin-bottom: 24px;
  text-align: center;
  backdrop-filter: blur(20px);
  position: relative;
  overflow: hidden;
}
.sxpro-header::before {
  content: '';
  position: absolute;
  top: -50%; left: -50%;
  width: 200%; height: 200%;
  background: radial-gradient(circle at 50% 50%, rgba(245,158,11,0.06) 0%, transparent 60%);
  animation: pulse-glow 4s ease-in-out infinite;
}
@keyframes pulse-glow {
  0%, 100% { transform: scale(1); opacity: 0.5; }
  50% { transform: scale(1.1); opacity: 1; }
}
.sxpro-header h1 { color: white; font-size: 2rem; font-weight: 800; margin: 0; font-family: 'Space Grotesk', sans-serif; letter-spacing: -0.02em; }
.sxpro-header .subtitle { color: var(--text-muted); font-size: 0.9rem; margin-top: 6px; }
.sxpro-badge { display: inline-block; background: rgba(245,158,11,0.2); color: var(--solar-gold); border: 1px solid rgba(245,158,11,0.4); border-radius: 100px; padding: 3px 14px; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.1em; margin: 8px 4px 0; }

/* ── Section labels ── */
.sxpro-section-label {
  display: inline-block;
  background: linear-gradient(135deg, var(--solar-gold), #D97706);
  color: #0B1437;
  padding: 5px 16px;
  border-radius: 8px;
  font-size: 0.75rem;
  font-weight: 800;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  margin-bottom: 16px;
}

/* ── Dataframe ── */
.stDataFrame { border-radius: 12px !important; overflow: hidden; }
.stDataFrame thead th { background: rgba(245,158,11,0.15) !important; color: var(--solar-gold) !important; }

/* ── Divider ── */
hr { border-color: rgba(255,255,255,0.07) !important; }

/* ── Progress ── */
.stProgress > div > div > div { background: linear-gradient(90deg, var(--solar-gold), var(--sky-cyan)) !important; }

/* ── Checkbox / Toggle ── */
.stCheckbox label { color: var(--text-muted) !important; font-size: 0.85rem !important; }
.stToggle label { color: var(--text-muted) !important; }

/* ── Mobile responsive ── */
@media (max-width: 768px) {
  .sxpro-header h1 { font-size: 1.3rem; }
  div[data-testid="metric-container"] { padding: 12px 14px !important; }
}

/* ── Animation for canvas panels ── */
.panel-canvas-wrapper {
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid rgba(245,158,11,0.2);
  background: #050E25;
}

/* ── KPI row separator ── */
.kpi-section-title {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--text-muted);
  margin: 0 0 10px 0;
  display: flex;
  align-items: center;
  gap: 10px;
}
.kpi-section-title::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--glass-border);
}
</style>
""", unsafe_allow_html=True)

# ╔══════════════════════════════════════════════════════════════════════╗
# ║                          DATABASES                                   ║
# ╚══════════════════════════════════════════════════════════════════════╝

db = {
    "Afghanistan": [33.9, "AFN", 5, 12, "B", "High", "Import", 5.2, 98, 220, 50, 45, "High"],
    "Albania": [41.1, "ALL", 10, 18, "B+", "Medium", "EU Import", 4.1, 100, 230, 50, 25, "Low"],
    "Algeria": [28.0, "DZD", 4, 12, "B", "Medium", "Local", 6.0, 99, 230, 50, 55, "Extreme"],
    "Andorra": [42.5, "EUR", 0.12, 0.28, "A+", "Very Low", "EU Certified", 4.3, 100, 230, 50, 30, "Moderate"],
    "Angola": [-11.2, "AOA", 15, 30, "C", "High", "Import", 5.5, 42, 220, 50, 35, "Moderate"],
    "Argentina": [-38.4, "ARS", 25, 65, "B+", "Medium", "Local", 5.1, 100, 220, 50, 70, "Extreme"],
    "Armenia": [40.2, "AMD", 12, 25, "B+", "Medium", "Import", 4.2, 100, 230, 50, 40, "High"],
    "Australia": [-25.2, "AUD", 0.10, 0.35, "A+", "Very Low", "AU Certified", 5.8, 100, 230, 50, 85, "Extreme"],
    "Austria": [47.5, "EUR", 0.15, 0.45, "A+", "Very Low", "EU Certified", 3.4, 100, 230, 50, 35, "Moderate"],
    "Azerbaijan": [40.1, "AZN", 0.05, 0.12, "B", "Medium", "Import", 4.8, 100, 220, 50, 50, "High"],
    "Bahrain": [26.0, "BHD", 0.02, 0.06, "A", "Low", "GCC", 5.9, 100, 230, 50, 60, "Extreme"],
    "Bangladesh": [23.6, "BDT", 7.5, 14.0, "B", "Medium", "Local Assembly", 4.6, 99, 220, 50, 90, "Extreme"],
    "Belgium": [50.5, "EUR", 0.12, 0.52, "A+", "Very Low", "EU Certified", 2.9, 100, 230, 50, 40, "High"],
    "Bhutan": [27.5, "BTN", 3, 8, "A", "Low", "Hydro+Solar", 4.5, 99, 230, 50, 30, "Moderate"],
    "Bolivia": [-16.2, "BOB", 0.4, 0.9, "B", "Medium", "Import", 5.8, 94, 220, 50, 25, "Low"],
    "Bosnia": [44.2, "BAM", 0.08, 0.16, "B+", "Medium", "EU Import", 3.6, 100, 230, 50, 45, "High"],
    "Botswana": [-22.3, "BWP", 1.2, 2.4, "B+", "Medium", "Local", 6.1, 72, 230, 50, 50, "High"],
    "Brazil": [-14.2, "BRL", 0.55, 1.15, "A-", "Low", "Local Mfg", 5.5, 99, 220, 60, 60, "Extreme"],
    "Bulgaria": [42.7, "BGN", 0.09, 0.18, "A-", "Low", "EU Certified", 3.8, 100, 230, 50, 40, "High"],
    "Burkina Faso": [12.4, "XOF", 85, 170, "C", "High", "Import", 5.8, 19, 220, 50, 55, "Extreme"],
    "Cambodia": [12.6, "KHR", 600, 1200, "B", "Medium", "Import", 5.0, 89, 230, 50, 70, "Extreme"],
    "Canada": [56.1, "CAD", 0.08, 0.24, "A+", "Very Low", "US/CA Certified", 3.7, 100, 120, 60, 80, "Extreme"],
    "Chile": [-35.6, "CLP", 65, 155, "A", "Low", "Local", 6.2, 100, 220, 50, 75, "Extreme"],
    "China": [35.8, "CNY", 0.42, 0.72, "C+", "High", "Global Supply", 4.3, 100, 220, 50, 50, "High"],
    "Colombia": [4.5, "COP", 380, 750, "B+", "Medium", "Import", 4.5, 99, 110, 60, 30, "Moderate"],
    "Croatia": [45.1, "EUR", 0.10, 0.20, "A", "Low", "EU Certified", 3.7, 100, 230, 50, 50, "High"],
    "Cyprus": [35.1, "EUR", 0.15, 0.30, "A", "Low", "EU Certified", 5.6, 100, 230, 50, 55, "Extreme"],
    "Czech": [49.8, "CZK", 2.2, 4.8, "A", "Low", "EU Certified", 3.1, 100, 230, 50, 35, "Moderate"],
    "Denmark": [56.2, "DKK", 0.65, 2.80, "A+", "Very Low", "EU Certified", 2.7, 100, 230, 50, 90, "Extreme"],
    "Dominican": [18.7, "DOP", 8.5, 17, "B", "Medium", "Import", 5.5, 99, 120, 60, 85, "Extreme"],
    "Ecuador": [-1.8, "USD", 0.10, 0.20, "B+", "Medium", "Import", 4.8, 97, 120, 60, 25, "Low"],
    "Egypt": [26.8, "EGP", 1.2, 2.6, "B", "Medium", "Local Assembly", 6.1, 100, 220, 50, 50, "High"],
    "Ethiopia": [9.1, "ETB", 0.5, 1.2, "B", "Medium", "China Import", 5.9, 51, 220, 50, 40, "High"],
    "Finland": [61.9, "EUR", 0.08, 0.38, "A+", "Very Low", "EU Certified", 2.5, 100, 230, 50, 60, "Extreme"],
    "France": [46.2, "EUR", 0.15, 0.34, "A+", "Very Low", "EU Certified", 3.5, 100, 230, 50, 45, "High"],
    "Germany": [51.1, "EUR", 0.12, 0.48, "A+", "Very Low", "EU Certified", 3.0, 100, 230, 50, 55, "Extreme"],
    "Ghana": [7.9, "GHS", 0.50, 1.0, "B", "Medium", "Import", 5.4, 86, 230, 50, 40, "High"],
    "Greece": [39.0, "EUR", 0.18, 0.38, "A", "Low", "EU Import", 4.5, 100, 230, 50, 65, "Extreme"],
    "India": [20.5, "INR", 6.2, 12.5, "A-", "Low", "Local Mfg", 5.4, 99, 230, 50, 60, "Extreme"],
    "Indonesia": [-0.7, "IDR", 1500, 3400, "B", "Medium", "Local", 4.8, 99, 220, 50, 50, "High"],
    "Iran": [32.4, "IRR", 800, 2000, "B", "Medium", "Local", 5.6, 100, 220, 50, 70, "Extreme"],
    "Iraq": [33.2, "IQD", 70, 160, "C", "High", "Import", 5.8, 99, 220, 50, 55, "Extreme"],
    "Ireland": [53.1, "EUR", 0.22, 0.55, "A+", "Very Low", "EU Certified", 2.7, 100, 230, 50, 95, "Extreme"],
    "Israel": [31.0, "ILS", 0.40, 0.60, "A", "Low", "Local", 5.7, 100, 230, 50, 50, "High"],
    "Italy": [41.8, "EUR", 0.20, 0.50, "A", "Low", "EU Certified", 4.2, 100, 230, 50, 50, "High"],
    "Japan": [36.2, "JPY", 21, 42, "A+", "Very Low", "JP Certified", 3.8, 100, 100, 50, 110, "Extreme"],
    "Jordan": [30.5, "JOD", 0.08, 0.18, "B+", "Medium", "Local", 5.8, 100, 230, 50, 60, "Extreme"],
    "Kazakhstan": [48.0, "KZT", 8, 18, "B", "Medium", "Local", 4.6, 100, 220, 50, 65, "Extreme"],
    "Kenya": [-1.2, "KES", 12, 28, "B", "Medium", "Import", 5.7, 76, 240, 50, 35, "Moderate"],
    "Kuwait": [29.3, "KWD", 0.02, 0.08, "A", "Low", "GCC", 5.9, 100, 240, 50, 70, "Extreme"],
    "Malaysia": [4.2, "MYR", 0.38, 0.68, "A-", "Low", "Local Mfg", 4.7, 100, 240, 50, 45, "High"],
    "Mexico": [23.6, "MXN", 2.2, 4.8, "B+", "Medium", "US Import", 5.6, 99, 127, 60, 80, "Extreme"],
    "Morocco": [31.7, "MAD", 1.1, 2.2, "B+", "Medium", "Local", 5.9, 99, 220, 50, 55, "Extreme"],
    "Netherlands": [52.1, "EUR", 0.16, 0.55, "A+", "Very Low", "EU Certified", 2.8, 100, 230, 50, 85, "Extreme"],
    "New Zealand": [-40.9, "NZD", 0.11, 0.40, "A+", "Very Low", "AU/NZ", 4.4, 100, 230, 50, 90, "Extreme"],
    "Nigeria": [9.0, "NGN", 70, 160, "C", "High", "Import", 5.5, 62, 230, 50, 45, "High"],
    "Norway": [60.4, "NOK", 0.9, 2.8, "A+", "Very Low", "EU Certified", 2.3, 100, 230, 50, 80, "Extreme"],
    "Oman": [21.5, "OMR", 0.03, 0.12, "A", "Low", "GCC", 6.0, 100, 240, 50, 65, "Extreme"],
    "Pakistan": [30.3, "PKR", 42.0, 82.0, "B+", "Medium", "China Import", 5.3, 97, 220, 50, 55, "Extreme"],
    "Philippines": [12.8, "PHP", 6.2, 14.0, "B", "Medium", "China Import", 5.1, 94, 220, 60, 95, "Extreme"],
    "Poland": [51.9, "PLN", 0.45, 0.95, "A", "Low", "EU Certified", 3.1, 100, 230, 50, 50, "High"],
    "Portugal": [39.3, "EUR", 0.14, 0.32, "A", "Low", "EU Certified", 4.3, 100, 230, 50, 55, "Extreme"],
    "Qatar": [25.3, "QAR", 0.15, 0.38, "A", "Low", "GCC", 5.9, 100, 240, 50, 60, "Extreme"],
    "Romania": [45.9, "RON", 0.45, 0.95, "A-", "Low", "EU Certified", 3.6, 100, 230, 50, 45, "High"],
    "Russia": [61.5, "RUB", 3.5, 6.2, "B", "Medium", "Local", 3.2, 100, 220, 50, 70, "Extreme"],
    "Saudi Arabia": [23.8, "SAR", 0.15, 0.32, "A", "Low", "GCC Local", 6.1, 100, 220, 60, 65, "Extreme"],
    "Singapore": [1.3, "SGD", 0.28, 0.45, "A+", "Very Low", "Import", 4.6, 100, 230, 50, 40, "High"],
    "South Africa": [-30.5, "ZAR", 1.9, 3.8, "B+", "Medium", "Local", 5.7, 85, 230, 50, 60, "Extreme"],
    "South Korea": [37.5, "KRW", 95, 180, "A+", "Very Low", "KR Certified", 3.8, 100, 220, 60, 75, "Extreme"],
    "Spain": [40.4, "EUR", 0.22, 0.45, "A", "Low", "EU Certified", 4.6, 100, 230, 50, 60, "Extreme"],
    "Sri Lanka": [7.8, "LKR", 25, 58, "B", "Medium", "India Import", 5.2, 99, 230, 50, 80, "Extreme"],
    "Sweden": [60.1, "SEK", 0.85, 2.40, "A+", "Very Low", "EU Certified", 2.6, 100, 230, 50, 75, "Extreme"],
    "Switzerland": [46.8, "CHF", 0.20, 0.45, "A+", "Very Low", "EU Certified", 3.4, 100, 230, 50, 40, "High"],
    "Thailand": [15.8, "THB", 2.8, 6.0, "A-", "Low", "Local Mfg", 5.0, 100, 220, 50, 60, "Extreme"],
    "Tunisia": [34.0, "TND", 0.18, 0.38, "B+", "Medium", "Local", 5.8, 100, 230, 50, 55, "Extreme"],
    "Turkey": [38.9, "TRY", 3.5, 6.5, "B+", "Medium", "Local", 4.9, 100, 230, 50, 50, "High"],
    "UAE": [23.4, "AED", 0.22, 0.48, "A", "Low", "GCC Local", 5.9, 100, 220, 50, 65, "Extreme"],
    "Ukraine": [48.3, "UAH", 1.8, 4.2, "B", "Medium", "EU Import", 3.4, 100, 220, 50, 50, "High"],
    "UK": [55.3, "GBP", 0.22, 0.58, "A+", "Very Low", "UK/EU Certified", 2.8, 100, 230, 50, 80, "Extreme"],
    "Uruguay": [-32.5, "UYU", 3.8, 7.6, "A", "Low", "Import", 4.8, 100, 230, 50, 70, "Extreme"],
    "USA": [37.0, "USD", 0.14, 0.30, "A+", "Very Low", "US Certified", 4.8, 100, 120, 60, 90, "Extreme"],
    "Uzbekistan": [41.3, "UZS", 250, 500, "B", "Medium", "Local", 5.2, 100, 220, 50, 50, "High"],
    "Venezuela": [6.4, "VES", 0.02, 0.04, "C", "High", "Import", 5.2, 99, 120, 60, 35, "Moderate"],
    "Vietnam": [14.0, "VND", 2200, 3800, "B+", "Medium", "Local Mfg", 4.8, 100, 220, 50, 85, "Extreme"],
    "Yemen": [15.4, "YER", 40, 80, "C", "High", "Import", 5.9, 47, 220, 50, 60, "Extreme"],
    "Zambia": [-13.1, "ZMW", 1.2, 2.4, "B", "Medium", "Import", 5.7, 45, 230, 50, 35, "Moderate"],
    "Zimbabwe": [-19.0, "USD", 0.10, 0.25, "C", "High", "Import", 5.8, 47, 230, 50, 40, "High"],
}

panel_db = {
    "Jinko 545W Mono PERC":           [21.5, 0.55, 0.28, -0.35, 49.8, 13.8, "Tier-1 Standard"],
    "Trina 550W Mono PERC":           [21.8, 0.58, 0.29, -0.36, 50.1, 13.9, "Tier-1 Standard"],
    "LONGi 540W Hi-MO4":              [21.2, 0.52, 0.27, -0.35, 49.5, 13.7, "Tier-1 Standard"],
    "Canadian 545W CS3W":             [21.6, 0.56, 0.28, -0.35, 49.9, 13.8, "Tier-1 Standard"],
    "Jinko 580W TOPCon N-Type":       [23.5, 0.65, 0.32, -0.30, 50.8, 14.5, "Tier-1 High Eff"],
    "Trina 575W TOPCon":              [23.8, 0.68, 0.33, -0.29, 51.0, 14.6, "Tier-1 High Eff"],
    "LONGi 570W Hi-MO5":             [23.2, 0.62, 0.31, -0.31, 50.5, 14.3, "Tier-1 High Eff"],
    "JA Solar 575W DeepBlue 3.0":    [23.6, 0.66, 0.32, -0.30, 50.9, 14.5, "Tier-1 High Eff"],
    "Risen 590W Hyper-ion":          [24.0, 0.70, 0.34, -0.29, 51.2, 14.7, "Tier-1 Premium"],
    "Huansheng 610W HJT":            [24.5, 0.75, 0.38, -0.25, 51.5, 15.0, "HJT Premium"],
    "REC Alpha Pure 410W HJT":       [24.2, 0.72, 0.37, -0.24, 51.3, 14.9, "HJT Premium"],
    "Tongwei 600W TNC HJT":          [24.8, 0.78, 0.39, -0.24, 51.8, 15.2, "HJT Premium"],
    "Jinko 605W Bifacial TOPCon":    [24.2, 0.68, 0.35, -0.29, 51.0, 14.6, "Bifacial Dual Glass"],
    "Trina 600W Vertex Bifacial":    [24.0, 0.65, 0.34, -0.29, 50.8, 14.5, "Bifacial Dual Glass"],
    "Canadian 590W Bifacial":        [23.6, 0.62, 0.33, -0.30, 50.5, 14.3, "Bifacial Dual Glass"],
    "SunPower 415W Maxeon 6 IBC":   [25.2, 0.85, 0.42, -0.22, 52.5, 12.8, "IBC Premium"],
    "Maxeon 3 400W IBC":            [24.8, 0.80, 0.40, -0.23, 52.0, 12.6, "IBC Premium"],
    "Aiko 625W ABC IBC":            [25.5, 0.88, 0.43, -0.21, 52.8, 13.0, "IBC Ultra Premium"],
    "Oxford PV 550W Perovskite":    [29.5, 1.20, 0.55, -0.20, 53.5, 12.5, "Future Tech"],
    "LONGi 530W Si-Perovskite":     [28.8, 1.15, 0.52, -0.21, 53.0, 12.4, "Future Tech"],
    "First Solar 460W CdTe TF":     [18.5, 0.35, 0.22, -0.25, 48.5, 14.5, "Thin Film"],
    "QCells 415W Q.PEAK DUO":       [21.0, 0.50, 0.26, -0.35, 49.2, 13.5, "QCells Standard"],
    "QCells 480W Q.TRON":           [22.8, 0.60, 0.30, -0.32, 50.3, 14.2, "QCells Premium"],
    "JA 545W DeepBlue 3.0 Mono":    [21.4, 0.54, 0.28, -0.35, 49.7, 13.7, "JA Standard"],
    "Risen 550W RSM144":             [21.7, 0.57, 0.28, -0.35, 49.9, 13.8, "Risen Standard"],
}

battery_db = {
    "LiFePO4 LFP":    [94, 6000, 180, 2.0, 48, "Cobalt Free — Best Cycle Life"],
    "NMC Lithium":    [92, 4000, 220, 2.5, 48, "High Energy Density"],
    "Lead Acid AGM":  [85, 1200, 120, 5.0, 24, "Low Cost, Heavy Weight"],
    "Sodium Ion":     [90, 3000, 150, 3.0, 48, "Emerging — Cobalt/Lithium Free"],
    "Solid State":    [96, 8000, 350, 1.5, 48, "Future Premium Technology"],
    "No Battery":     [0,  0,    0,   0,   0,  "Grid-Tied System Only"],
}

inverter_db = {
    "String Inverter":    [97.5, 1.00, 800,  "Central MPPT — Most Common"],
    "Micro Inverter":     [96.8, 1.05, 1200, "Panel-Level MPPT — Shade Tolerant"],
    "Hybrid Inverter":    [97.0, 1.02, 1500, "Battery + Grid — Best Flexibility"],
    "Power Optimizer":    [98.0, 1.03, 1400, "DC Optimizer — High Performance"],
    "Central Inverter":   [98.5, 0.98, 600,  "Large-Scale Commercial"],
}

structure_db = {
    "Low":      {"type": "Aluminum Fixed Tilt",              "tilt_max": 30, "material": "Anodized AL-6005-T5",                "foundation": "Ground Screw",     "clamp": "Standard Mid/End"},
    "Moderate": {"type": "Galvanized Steel",                 "tilt_max": 25, "material": "Hot-Dip Galvanized Steel Q235",      "foundation": "Concrete Ballast", "clamp": "Reinforced Clamp"},
    "High":     {"type": "Galvanized Steel + Bracing",       "tilt_max": 20, "material": "Galvanized Steel + Cross Bracing",   "foundation": "Concrete Footing", "clamp": "Heavy Duty Clamp"},
    "Extreme":  {"type": "Steel Structure + Wind Deflector", "tilt_max": 15, "material": "S355 Steel + Wind Deflector Shield", "foundation": "Deep Concrete Pile","clamp": "Hurricane Rated Clamp"},
}

BATTERY_TYPES = {
    "Lithium-Ion": {"default_dod": 90, "efficiency": 95, "life_years": 10},
    "Lead-Acid":   {"default_dod": 50, "efficiency": 80, "life_years": 3},
    "Gel Battery": {"default_dod": 70, "efficiency": 85, "life_years": 5},
}

# ╔══════════════════════════════════════════════════════════════════════╗
# ║                          UTILITIES                                   ║
# ╚══════════════════════════════════════════════════════════════════════╝

@st.cache_data(ttl=86400)
def safe_geocode(country_name, c_lat_fallback):
    if not GEO_ENABLED:
        return c_lat_fallback, 70.0, country_name
    try:
        geolocator = Nominatim(user_agent="solarx_pro_v3", timeout=3)
        location = geolocator.geocode(country_name)
        if location:
            return location.latitude, location.longitude, location.address.split(',')[0]
    except Exception:
        pass
    return c_lat_fallback, 70.0, country_name

@st.cache_data(ttl=1800)
def fetch_meteorological_data(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {"latitude": lat, "longitude": lon,
              "hourly": "temperature_2m,wind_speed_10m,cloud_cover",
              "timezone": "auto", "forecast_days": 3}
    try:
        res = requests.get(url, params=params, timeout=10)
        if res.status_code == 200:
            h_data = res.json().get("hourly", {})
            df = pd.DataFrame({
                "Timestamp": pd.to_datetime(h_data.get("time")),
                "Temperature": h_data.get("temperature_2m"),
                "Wind_Speed": h_data.get("wind_speed_10m"),
                "Cloud_Cover": h_data.get("cloud_cover"),
            })
            df["Hour"] = df["Timestamp"].dt.hour
            return df
    except Exception:
        pass
    return None

def calc_wind_load(wind_speed_kmh, tilt_angle, panel_qty, panel_area_m2=2.1):
    wind_ms = wind_speed_kmh / 3.6
    q = 0.613 * wind_ms ** 2
    cp = 1.3 if tilt_angle > 30 else (1.0 if tilt_angle > 15 else 0.8)
    force_per_panel = q * cp * panel_area_m2 / 1000
    return force_per_panel * panel_qty

def calc_lightning_protection(building_height):
    if building_height > 20:
        return building_height + 2, 20
    return building_height + 1.5, 30

def model_solar_physics(temp, wind, cloud, hour, cfg, scenario_mode="live"):
    if 6 <= hour <= 18:
        amplitude = 1050.0 if scenario_mode == "live" else 950.0
        base_ghi = amplitude * np.sin(np.pi * (hour - 6) / 12)
        tilt_factor   = np.cos(np.radians(cfg["tilt"] - 25))
        azimuth_factor = np.cos(np.radians(cfg["azimuth"] - 180))
        effective_ghi = base_ghi * max(0.4, tilt_factor * azimuth_factor)
    else:
        return {"Power_kW": 0.0, "Cell_Temp": temp, "Irradiance": 0.0}

    attenuation = (cloud / 100.0) * 0.82
    incident_irradiance = effective_ghi * (1.0 - attenuation)

    noct_constant = 45.0 if cfg["panel_type"] == "Monocrystalline" else 48.0
    cooling_index = 1.0 + (wind * 0.035)
    cell_temp = temp + ((noct_constant - 20.0) * (incident_irradiance / 800.0) / cooling_index)

    thermal_loss = 1.0
    if cell_temp > 25.0:
        thermal_loss = 1.0 - ((cell_temp - 25.0) * abs(cfg["temp_coef"]))

    total_age_loss = cfg["system_age"] * (cfg["annual_degrad"] / 100.0)
    retained_efficiency = max(0.5, 1.0 - total_age_loss)

    field_peak_kw = (cfg["panel_w"] * cfg["panel_count"]) / 1000.0
    net_output_kw = (field_peak_kw * (incident_irradiance / 1000.0) * thermal_loss
                     * (cfg["inverter_eff"] / 100.0) * (1.0 - cfg["soiling"] / 100.0) * retained_efficiency)
    return {"Power_kW": max(0.0, round(net_output_kw, 3)),
            "Cell_Temp": round(cell_temp, 2),
            "Irradiance": round(incident_irradiance, 2)}

def compute_financial_net_metering(daily_gen_kwh, daily_load_kwh, cfg):
    imp = cfg["tariff_import"]
    exp = cfg["tariff_export"]
    if daily_gen_kwh >= daily_load_kwh:
        surplus = daily_gen_kwh - daily_load_kwh
        credit  = surplus * exp
        net_benefit = (daily_load_kwh * imp) + credit
        bill = 0.0
    else:
        deficit = daily_load_kwh - daily_gen_kwh
        bill = deficit * imp
        credit = 0.0
        net_benefit = daily_gen_kwh * imp
    capex = cfg["panel_count"] * cfg["cost_per_panel"]
    annual = net_benefit * 365.25
    payback = capex / annual if annual > 0 else 99.0
    return {"Daily_Savings_Currency": round(net_benefit, 2),
            "Daily_Bill_Due": round(bill, 2),
            "Export_Credit": round(credit, 2),
            "Estimated_Payback_Years": round(payback, 2),
            "Total_CapEx": capex}

def generate_pdf_report(data_dict):
    if not PDF_ENABLED:
        return None
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 18)
    def s(t): return str(t).encode('ascii', 'ignore').decode('ascii')
    pdf.cell(0, 12, s('SolarX Pro — Solar Analysis Report'), 0, 1, 'C')
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 8, s(f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}'), 0, 1, 'C')
    pdf.ln(8)
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, s('SYSTEM CONFIGURATION'), 0, 1)
    pdf.set_font('Arial', '', 11)
    for k, v in data_dict.items():
        pdf.cell(0, 7, s(f'{k}: {v}'), 0, 1)
    raw = pdf.output(dest='S')
    if isinstance(raw, str):
        raw = raw.encode('latin-1', 'replace')
    return raw

# ╔══════════════════════════════════════════════════════════════════════╗
# ║                            SIDEBAR                                   ║
# ╚══════════════════════════════════════════════════════════════════════╝
with st.sidebar:
    st.markdown("""
    <div style='text-align:center;padding:12px 0 8px'>
      <span style='font-size:2rem'>☀️</span>
      <div style='color:#F59E0B;font-weight:800;font-size:1.05rem;font-family:Space Grotesk,sans-serif;letter-spacing:-0.01em'>SolarX Professional</div>
      <div style='color:#64748B;font-size:0.72rem;letter-spacing:0.08em;text-transform:uppercase'>Enterprise Edition v3.0</div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    country = st.selectbox("🌍 Country (120+ supported)", sorted(db.keys()), key="country_select_main")
    cd = list(db[country]) + [None] * 15
    c_lat, c_curr, c_sale, c_buy = cd[0], cd[1], cd[2], cd[3]
    esg_rating, labor_risk, sourcing = cd[4], cd[5], cd[6]
    avg_ghi, elec_access, grid_v, grid_f = cd[7], cd[8], cd[9], cd[10]
    wind_kmh_db, wind_zone = cd[11], cd[12]

    st.divider()
    st.markdown("### ⚡ Panel Configuration")
    panel_type = st.selectbox("Panel Model", list(panel_db.keys()), key="panel_sel")
    p_eff, p_cost, voc, p_temp, voc_std, isc, p_note = panel_db[panel_type]
    p_qty = st.number_input("Number of Panels", min_value=1, max_value=50000, value=22, key="p_qty")

    st.divider()
    st.markdown("### 🔄 Inverter")
    inverter_type = st.selectbox("Inverter Type", list(inverter_db.keys()), key="inv_sel")
    inv_eff, inv_bonus, inv_cost, inv_note = inverter_db[inverter_type]

    st.divider()
    st.markdown("### 📐 Orientation")
    tilt    = st.slider("Panel Tilt Angle °", 0, 60, 25)
    azimuth = st.slider("Azimuth °", -180, 180, 180)

    st.divider()
    st.markdown("### 🏗️ Site Parameters")
    building_height = st.number_input("Building Height (m)", 3.0, 50.0, 6.0)
    wire_length     = st.number_input("DC Cable Length (m)", 10, 200, 50)
    cable_size      = st.selectbox("DC Cable Size (mm²)", [4, 6, 10, 16, 25])

    st.divider()
    st.markdown("### 🛰️ Telemetry Mode")
    live_weather_toggle = st.toggle("Live Satellite Telemetry", value=False,
                                    help="ON = Live GPS/API | OFF = Country Database")

    st.divider()
    st.markdown("""
    <div style='color:#475569;font-size:0.7rem;text-align:center;padding:8px 0'>
      © 2025 SolarX Professional<br>
      Enterprise Solar Estimation Platform<br>
      <span style='color:#F59E0B'>☀️</span> Powered by Physics-Based AI Engine
    </div>
    """, unsafe_allow_html=True)

# ╔══════════════════════════════════════════════════════════════════════╗
# ║                       EXPANDED INPUTS                                ║
# ╚══════════════════════════════════════════════════════════════════════╝
col1, col2, col3 = st.columns(3)
with col1:
    with st.expander("🔋 Battery & Load Configuration", expanded=False):
        battery_type = st.selectbox("Battery Chemistry", list(battery_db.keys()), key="bat_sel")
        b_eff, b_cycles, b_cost, b_degrade, b_voltage, b_note = battery_db[battery_type]
        has_batt = battery_type != "No Battery"
        b_cap = st.number_input("Battery Capacity (kWh)", value=20.0) if has_batt else 0
        dod   = st.slider("Depth of Discharge %", 50, 95, 85) if has_batt else 0
        h_load = st.number_input("Daily Energy Load (kWh)", value=55.0, key="h_load")
        net_metering = st.checkbox("✅ Net Metering Enabled", value=True)

with col2:
    with st.expander("🔬 Advanced Physics Engine", expanded=False):
        panel_w_adv   = st.number_input("Unit Panel Power (W)", 200, 700, int(p_eff * 25), 5)
        system_age    = st.slider("System Age (Years)", 0, 25, 1)
        annual_degrad = st.number_input("Annual Degradation %", 0.1, 2.0, 0.5, 0.1)
        soiling_adv   = st.slider("Soiling Loss %", 0.0, 20.0, 3.5, 0.5)

with col3:
    with st.expander("🌤️ Climate & Environment", expanded=False):
        sun_h       = st.slider("Peak Sun Hours/day", 3.0, 8.5, float(avg_ghi))
        sys_loss    = st.slider("System Losses %", 8, 30, 14)
        soiling     = st.slider("Soiling %", 0, 20, 5)
        temp_ambient = st.slider("Ambient Temp °C", 15, 50, 28)

with st.expander("💰 Financial & Tariff Parameters", expanded=False):
    fc1, fc2, fc3, fc4 = st.columns(4)
    with fc1:
        buy_rate  = st.number_input(f"Buy Rate ({c_curr}/kWh)", value=float(c_buy))
        sell_rate = st.number_input(f"Sell Rate ({c_curr}/kWh)", value=float(c_sale))
    with fc2:
        tax_val       = st.slider("Tax %", 0, 30, 17)
        discount_rate = st.slider("Discount Rate %", 3, 15, 8)
    with fc3:
        install_cost     = st.number_input(f"Install Cost/kWp ({c_curr})", value=42000.0 if country == "Pakistan" else 750.0)
        cost_per_panel_adv = st.number_input("Cost per Panel (installed)", 10.0, 10000.0, 250.0, 10.0)
    with fc4:
        subsidy_pct = st.slider("Government Subsidy %", 0, 50, 30 if country == "Pakistan" else 0)
        inflation   = st.slider("Tariff Inflation %/yr", 0.0, 15.0, 3.0, 0.5)

# ╔══════════════════════════════════════════════════════════════════════╗
# ║                         CALCULATIONS                                 ║
# ╚══════════════════════════════════════════════════════════════════════╝
sys_size = (p_eff * p_qty * 100) / 1000
panels_per_string = int(1000 / voc_std)
strings = math.ceil(p_qty / panels_per_string)
voc_string = voc_std * panels_per_string
isc_string = isc * strings
mppt_voltage = voc_string * 0.8

lat, lon, location_name = safe_geocode(country, c_lat)
wind = wind_kmh_db
cloud_pct = 20

wind_force = calc_wind_load(wind, tilt, p_qty)
struct = structure_db[wind_zone]
wind_safe = wind_force < (sys_size * 50)
rod_height, protection_radius = calc_lightning_protection(building_height)

current_dc = (sys_size * 1000) / 400
voltage_drop = (current_dc * wire_length * 0.0175) / cable_size
vd_percent   = (voltage_drop / mppt_voltage) * 100 if mppt_voltage > 0 else 0

hours_arr = np.arange(24)
angle_eff  = np.cos(np.radians(tilt - abs(c_lat))) * np.cos(np.radians(azimuth))
temp_loss  = 1 + (p_temp / 100) * (temp_ambient + 25 - 25)
soiling_loss   = 1 - soiling / 100
weather_factor = 1 - cloud_pct * 0.008 + wind * 0.0003

daily_yield = (sys_size * sun_h * ((100 - sys_loss) / 100) * max(0.3, angle_eff)
               * (p_eff / 21.5) * temp_loss * soiling_loss * (inv_eff / 100) * inv_bonus * weather_factor)

gen_24  = [max(0, daily_yield / 12 * np.sin(np.pi * (h - 6) / 12)) if 6 <= h <= 18 else 0 for h in hours_arr]
load_24 = [(h_load / 24) * (2.8 if (h > 18 or h < 7) else 0.7) for h in hours_arr]

soc = []
c_soc = b_cap * (dod / 100) if has_batt else 0
for g, l in zip(gen_24, load_24):
    if has_batt:
        diff  = g - l
        c_soc = max(0, min(b_cap, c_soc + diff * (b_eff / 100)))
    soc.append(c_soc)

export_24 = [max(0, g - l - (soc[i] - soc[i-1] if i > 0 else 0)) for i, (g, l) in enumerate(zip(gen_24, load_24))]
import_24 = [max(0, l - g - (soc[i-1] - soc[i] if i > 0 else 0)) for i, (g, l) in enumerate(zip(gen_24, load_24))]

battery_cost   = b_cap * b_cost if has_batt else 0
panel_cost     = sys_size * 1000 * p_cost
inverter_cost  = sys_size * inv_cost
structure_cost = sys_size * 150
cable_cost     = wire_length * cable_size * 2.5
lightning_cost = rod_height * 80
gross_cost = (panel_cost + battery_cost + inverter_cost + structure_cost
              + cable_cost + lightning_cost + sys_size * install_cost)
net_cost = gross_cost * (1 - subsidy_pct / 100)

years_arr   = np.arange(25)
yearly_gen  = [sum(gen_24) * 365 * (1 - b_degrade / 100) ** y for y in years_arr]
gen_ratio   = sum(export_24) / sum(gen_24) if sum(gen_24) > 0 else 0
yearly_profit = []
for i, yg in enumerate(yearly_gen):
    tariff_import_inflated = buy_rate  * ((1 + inflation/100) ** i)
    tariff_export_inflated = sell_rate * ((1 + inflation/100) ** i)
    profit = yg * ((1 - gen_ratio) * tariff_import_inflated + gen_ratio * tariff_export_inflated) * (1 - tax_val / 100)
    yearly_profit.append(profit)

payback = net_cost / yearly_profit[0] if yearly_profit[0] > 0 else 99
npv = sum([p / ((1 + discount_rate / 100) ** i) for i, p in enumerate(yearly_profit)]) - net_cost

adv_cfg = {
    "panel_type": "Monocrystalline", "panel_w": panel_w_adv, "panel_count": p_qty,
    "cost_per_panel": cost_per_panel_adv, "temp_coef": p_temp / 100,
    "tilt": tilt, "azimuth": azimuth, "system_age": system_age,
    "annual_degrad": annual_degrad, "inverter_eff": inv_eff,
    "soiling": soiling_adv, "tariff_import": buy_rate, "tariff_export": sell_rate,
    "battery_ah": int(b_cap * 1000 / max(b_voltage, 1)) if has_batt else 200,
    "battery_v": b_voltage if has_batt else 48,
}

fin_report = compute_financial_net_metering(daily_yield, h_load, adv_cfg)
usable_battery_kwh = b_cap * (dod / 100) if has_batt else 0
hours_of_autonomy  = usable_battery_kwh / (h_load / 24) if h_load > 0 else 0

pr = (sum(gen_24) / (sys_size * sun_h)) * 100 if sys_size * sun_h > 0 else 0
co2_annual = sum(gen_24) * 365 * 0.82 / 1000

# ╔══════════════════════════════════════════════════════════════════════╗
# ║                          PAGE HEADER                                 ║
# ╚══════════════════════════════════════════════════════════════════════╝
st.markdown(f"""
<div class='sxpro-header'>
  <h1>☀️ SolarX Professional — {country}</h1>
  <div class='subtitle'>📍 {location_name} &nbsp;·&nbsp; {sys_size:.2f} kWp System &nbsp;·&nbsp; {p_qty} × {panel_type.split()[0]} Panels</div>
  <div>
    <span class='sxpro-badge'>ENTERPRISE v3.0</span>
    <span class='sxpro-badge'>ESG {esg_rating}</span>
    <span class='sxpro-badge'>{grid_v}V {grid_f}Hz Grid</span>
    <span class='sxpro-badge'>Wind Zone: {wind_zone}</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ╔══════════════════════════════════════════════════════════════════════╗
# ║                          KPI DASHBOARD                               ║
# ╚══════════════════════════════════════════════════════════════════════╝
st.markdown("<p class='kpi-section-title'>System Performance KPIs</p>", unsafe_allow_html=True)
k = st.columns(5)
k[0].metric("⚡ System Size",   f"{sys_size:.2f} kWp",   f"{p_qty} panels")
k[1].metric("☀️ Daily Output",  f"{sum(gen_24):.1f} kWh", f"PR: {pr:.0f}%")
k[2].metric("📈 Annual Yield",  f"{sum(gen_24)*365:.0f} kWh", f"GHI: {avg_ghi}")
k[3].metric("🌿 CO₂ Avoided",   f"{co2_annual:.1f} T/yr",  f"{int(co2_annual*18)} trees/yr")
k[4].metric("💰 Daily Savings", f"{fin_report['Daily_Savings_Currency']:,.1f} {c_curr}", f"Ex: {sum(export_24):.1f} kWh")

st.markdown("<p class='kpi-section-title' style='margin-top:18px'>Financial & Electrical KPIs</p>", unsafe_allow_html=True)
k2 = st.columns(5)
k2[0].metric("💵 Net CapEx",    f"{net_cost:,.0f} {c_curr}", f"-{subsidy_pct}% subsidy")
k2[1].metric("⏱️ Payback",      f"{payback:.1f} yrs",       f"NPV: {npv:,.0f}")
k2[2].metric("🔌 VOC String",   f"{voc_string:.0f} V",       f"ISC: {isc_string:.1f} A")
k2[3].metric("📉 Voltage Drop", f"{vd_percent:.2f}%",        "⚠️ High" if vd_percent > 3 else "✅ OK")
k2[4].metric("💨 Wind Risk",    wind_zone, f"{wind:.0f} km/h",
             delta_color="inverse" if wind_zone in ["Extreme", "High"] else "normal")

st.divider()

# ╔══════════════════════════════════════════════════════════════════════╗
# ║                          MAIN TABS                                   ║
# ╚══════════════════════════════════════════════════════════════════════╝
tabs = st.tabs([
    "📊 Energy Profile",
    "🏗️ Panel Animator",
    "💨 Wind Load",
    "🔧 Technical Specs",
    "🔌 Inverter Design",
    "🔋 Battery System",
    "⚡ Electrical",
    "💰 Financial Model",
    "🌿 Eco & Carbon",
    "🛡️ ESG Ethics",
    "📡 Net Metering",
    "🤖 AI Diagnosis",
    "📈 Physics Engine",
    "📦 Storage Matrix",
    "📄 Export Report",
])

# ── TAB 0: Energy Profile ──────────────────────────────────────────────
with tabs[0]:
    st.markdown("<span class='sxpro-section-label'>24-Hour Energy Profile</span>", unsafe_allow_html=True)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(hours_arr), y=gen_24, name="☀️ Solar Generation",
        fill='tozeroy', fillcolor='rgba(245,158,11,0.15)',
        line=dict(color='#F59E0B', width=3),
        hovertemplate='%{y:.2f} kW<extra>Generation</extra>'
    ))
    fig.add_trace(go.Scatter(
        x=list(hours_arr), y=load_24, name="⚡ Load Demand",
        line=dict(color='#EF4444', width=2.5, dash='dot'),
        hovertemplate='%{y:.2f} kW<extra>Load</extra>'
    ))
    if has_batt:
        fig.add_trace(go.Scatter(
            x=list(hours_arr), y=soc, name="🔋 Battery SOC",
            line=dict(color='#10B981', width=2.5),
            hovertemplate='%{y:.2f} kWh<extra>Battery SOC</extra>'
        ))
    fig.add_trace(go.Bar(
        x=list(hours_arr), y=export_24, name="↑ Export to Grid",
        marker_color='rgba(6,182,212,0.5)',
        hovertemplate='%{y:.2f} kWh<extra>Export</extra>'
    ))
    fig.add_trace(go.Bar(
        x=list(hours_arr), y=import_24, name="↓ Import from Grid",
        marker_color='rgba(239,68,68,0.35)',
        hovertemplate='%{y:.2f} kWh<extra>Import</extra>'
    ))
    fig.update_layout(
        height=480, barmode='overlay',
        plot_bgcolor='rgba(11,20,55,0.6)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#94A3B8', family='Inter'),
        title=dict(text="Hourly Solar Generation vs. Load Demand Profile", font=dict(color='#F1F5F9', size=14)),
        legend=dict(bgcolor='rgba(15,32,87,0.7)', bordercolor='rgba(255,255,255,0.1)', borderwidth=1),
        xaxis=dict(title="Hour of Day", gridcolor='rgba(255,255,255,0.06)', tickmode='linear', dtick=2),
        yaxis=dict(title="Power (kW) / Energy (kWh)", gridcolor='rgba(255,255,255,0.06)'),
        hovermode='x unified',
    )
    st.plotly_chart(fig, use_container_width=True)

    ea, eb, ec, ed = st.columns(4)
    ea.metric("Peak Generation", f"{max(gen_24):.2f} kW", "at solar noon")
    eb.metric("Peak Load",        f"{max(load_24):.2f} kW", "evening peak")
    ec.metric("Self-Consumption", f"{(1 - sum(import_24)/h_load)*100:.1f}%", "grid independence")
    ed.metric("Net Export",       f"{sum(export_24) - sum(import_24):.1f} kWh/day")

# ── TAB 1: Panel Animator ───────────────────────────────────────────────
with tabs[1]:
    st.markdown("<span class='sxpro-section-label'>Interactive Panel Array Visualizer</span>", unsafe_allow_html=True)
    st.markdown("""
    <div class='sxpro-info'>
      ℹ️ This animated 3D-perspective view simulates your panel array layout, structural mounting, and live irradiance cycle.
      Panel colours shift from deep blue → amber as irradiance increases through the day.
    </div>
    """, unsafe_allow_html=True)

    # We render the full SVG+JS animation in an HTML iframe via st.components.v1.html
    import streamlit.components.v1 as components

    anim_cols_count = min(p_qty, 15)
    anim_rows_count = math.ceil(p_qty / anim_cols_count)

    # Build panel grid SVG positions
    panel_svg_items = ""
    panel_idx = 0
    for row in range(anim_rows_count):
        for col in range(anim_cols_count):
            if panel_idx >= p_qty:
                break
            px = 60 + col * 58
            py = 60 + row * 110
            pid = f"panel_{panel_idx}"
            panel_svg_items += f"""
            <g id="{pid}" transform="skewY(-{tilt // 3})">
              <rect x="{px}" y="{py}" width="50" height="90" rx="2"
                    fill="url(#panelGrad_{panel_idx % 4})"
                    stroke="rgba(245,158,11,0.6)" stroke-width="1.2"
                    class="solar-panel" data-idx="{panel_idx}"/>
              <!-- Cell lines -->
              <line x1="{px}" y1="{py+22}" x2="{px+50}" y2="{py+22}" stroke="rgba(255,255,255,0.12)" stroke-width="0.5"/>
              <line x1="{px}" y1="{py+44}" x2="{px+50}" y2="{py+44}" stroke="rgba(255,255,255,0.12)" stroke-width="0.5"/>
              <line x1="{px}" y1="{py+66}" x2="{px+50}" y2="{py+66}" stroke="rgba(255,255,255,0.12)" stroke-width="0.5"/>
              <line x1="{px+17}" y1="{py}" x2="{px+17}" y2="{py+90}" stroke="rgba(255,255,255,0.10)" stroke-width="0.5"/>
              <line x1="{px+34}" y1="{py}" x2="{px+34}" y2="{py+90}" stroke="rgba(255,255,255,0.10)" stroke-width="0.5"/>
            </g>"""
            panel_idx += 1

    # Structure legs (simplified)
    structure_svg = ""
    for col in range(min(anim_cols_count, 15)):
        lx = 82 + col * 58
        bot = 60 + anim_rows_count * 110 + 20
        structure_svg += f"""
        <line x1="{lx}" y1="{60 + anim_rows_count * 110 - 20}" x2="{lx - 8}" y2="{bot}"
              stroke="#78716C" stroke-width="2.5"/>
        <line x1="{lx}" y1="{60 + anim_rows_count * 110 - 20}" x2="{lx + 8}" y2="{bot}"
              stroke="#78716C" stroke-width="2.5"/>"""

    canvas_h = 80 + anim_rows_count * 110 + 80
    canvas_w = max(900, 60 + anim_cols_count * 58 + 60)

    html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ background: #050E25; overflow-x: auto; font-family: Inter, sans-serif; }}
  svg {{ display: block; }}
  .solar-panel {{ transition: fill 0.8s ease; cursor: pointer; }}
  .solar-panel:hover {{ stroke: #FCD34D !important; stroke-width: 2.5 !important; filter: drop-shadow(0 0 8px rgba(245,158,11,0.8)); }}
  #info-bar {{ position: fixed; bottom: 0; left: 0; right: 0; background: rgba(11,20,55,0.95);
               border-top: 1px solid rgba(245,158,11,0.3); padding: 8px 16px;
               color: #94A3B8; font-size: 12px; display: flex; gap: 24px; align-items: center; }}
  #info-bar span {{ color: #F59E0B; font-weight: 700; }}
  #clock {{ color: #FCD34D !important; font-size: 14px; font-weight: 800; }}
  #irr-bar {{ flex: 1; height: 6px; background: #1E3A5F; border-radius: 3px; overflow: hidden; }}
  #irr-fill {{ height: 100%; background: linear-gradient(90deg,#1D4ED8,#F59E0B); width: 0%; transition: width 0.5s; border-radius: 3px; }}
  .wind-particle {{ fill: rgba(6,182,212,0.5); }}
</style>
</head>
<body>
<svg id="mainSvg" viewBox="0 0 {canvas_w} {canvas_h}" width="100%" height="{min(canvas_h, 520)}px"
     xmlns="http://www.w3.org/2000/svg">
  <defs>
    <!-- Sky gradient (animated) -->
    <linearGradient id="skyGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#020B22" id="skyTop"/>
      <stop offset="100%" stop-color="#0F2057" id="skyBot"/>
    </linearGradient>
    <!-- Ground -->
    <linearGradient id="groundGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#1C3A1C"/>
      <stop offset="100%" stop-color="#0A1A0A"/>
    </linearGradient>
    <!-- Panel gradients (4 variants) -->
    <linearGradient id="panelGrad_0" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#1E3A8A" id="pg0a"/><stop offset="100%" stop-color="#1E40AF" id="pg0b"/>
    </linearGradient>
    <linearGradient id="panelGrad_1" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#1E3A8A" id="pg1a"/><stop offset="100%" stop-color="#1D4ED8" id="pg1b"/>
    </linearGradient>
    <linearGradient id="panelGrad_2" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#1E3A8A" id="pg2a"/><stop offset="100%" stop-color="#2563EB" id="pg2b"/>
    </linearGradient>
    <linearGradient id="panelGrad_3" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#1D4ED8" id="pg3a"/><stop offset="100%" stop-color="#3B82F6" id="pg3b"/>
    </linearGradient>
    <!-- Sun glow -->
    <radialGradient id="sunGlow">
      <stop offset="0%" stop-color="#FCD34D" stop-opacity="0.9"/>
      <stop offset="60%" stop-color="#F59E0B" stop-opacity="0.4"/>
      <stop offset="100%" stop-color="#F59E0B" stop-opacity="0"/>
    </radialGradient>
    <!-- Sun core -->
    <radialGradient id="sunCore">
      <stop offset="0%" stop-color="#FEFCE8"/>
      <stop offset="50%" stop-color="#FCD34D"/>
      <stop offset="100%" stop-color="#F59E0B"/>
    </radialGradient>
  </defs>

  <!-- Background sky -->
  <rect width="{canvas_w}" height="{canvas_h}" fill="url(#skyGrad)"/>

  <!-- Sun path arc (decorative) -->
  <path d="M 40 {canvas_h-80} Q {canvas_w//2} 20 {canvas_w-40} {canvas_h-80}"
        stroke="rgba(245,158,11,0.10)" stroke-width="1.5" fill="none" stroke-dasharray="4 6"/>

  <!-- Sun (animated along arc) -->
  <g id="sunGroup">
    <circle cx="0" cy="0" r="60" fill="url(#sunGlow)" opacity="0.7"/>
    <circle cx="0" cy="0" r="22" fill="url(#sunCore)"/>
    <!-- Sun rays -->
    <g id="sunRays">
      <line x1="0" y1="-30" x2="0" y2="-42" stroke="#FCD34D" stroke-width="2.5" stroke-linecap="round"/>
      <line x1="0" y1="30"  x2="0" y2="42"  stroke="#FCD34D" stroke-width="2.5" stroke-linecap="round"/>
      <line x1="-30" y1="0" x2="-42" y2="0" stroke="#FCD34D" stroke-width="2.5" stroke-linecap="round"/>
      <line x1="30"  y1="0" x2="42"  y2="0"  stroke="#FCD34D" stroke-width="2.5" stroke-linecap="round"/>
      <line x1="-21" y1="-21" x2="-30" y2="-30" stroke="#FCD34D" stroke-width="2" stroke-linecap="round"/>
      <line x1="21"  y1="-21" x2="30"  y2="-30" stroke="#FCD34D" stroke-width="2" stroke-linecap="round"/>
      <line x1="-21" y1="21"  x2="-30" y2="30"  stroke="#FCD34D" stroke-width="2" stroke-linecap="round"/>
      <line x1="21"  y1="21"  x2="30"  y2="30"  stroke="#FCD34D" stroke-width="2" stroke-linecap="round"/>
    </g>
  </g>

  <!-- Light beam from sun to panels -->
  <g id="lightBeams" opacity="0"></g>

  <!-- Ground -->
  <rect x="0" y="{canvas_h - 75}" width="{canvas_w}" height="75" fill="url(#groundGrad)"/>
  <rect x="0" y="{canvas_h - 75}" width="{canvas_w}" height="3" fill="rgba(16,185,129,0.4)"/>

  <!-- Structure legs -->
  {structure_svg}

  <!-- Mounting rail (horizontal) -->
  {''.join([f'<rect x="55" y="{60 + r * 110 + 80}" width="{anim_cols_count * 58 + 10}" height="4" rx="2" fill="#57534E" opacity="0.8"/>' for r in range(anim_rows_count)])}

  <!-- Panel array -->
  {panel_svg_items}

  <!-- Wind arrows (right side) -->
  <g id="windArrows" opacity="0.7">
    <text x="{canvas_w - 100}" y="40" fill="#67E8F9" font-size="11" font-family="Inter">
      WIND {wind:.0f} km/h
    </text>
  </g>

  <!-- Energy flow lines (animated) -->
  <g id="energyFlow">
    <!-- From panels to inverter label -->
    <text x="40" y="{canvas_h - 85}" fill="#94A3B8" font-size="10" font-family="Inter">
      ⚡ {sys_size:.1f} kWp → DC Bus
    </text>
  </g>

  <!-- UI overlay: time + irradiance label -->
  <rect x="8" y="8" width="170" height="44" rx="8" fill="rgba(11,20,55,0.85)" stroke="rgba(245,158,11,0.3)" stroke-width="1"/>
  <text x="16" y="24" fill="#94A3B8" font-size="9" font-family="Inter">SIMULATION TIME</text>
  <text id="timeDisplay" x="16" y="40" fill="#FCD34D" font-size="14" font-weight="bold" font-family="Space Grotesk">06:00</text>

  <rect x="{canvas_w - 185}" y="8" width="177" height="44" rx="8" fill="rgba(11,20,55,0.85)" stroke="rgba(245,158,11,0.3)" stroke-width="1"/>
  <text x="{canvas_w - 177}" y="24" fill="#94A3B8" font-size="9" font-family="Inter">IRRADIANCE W/m²</text>
  <text id="irrDisplay" x="{canvas_w - 177}" y="40" fill="#F59E0B" font-size="14" font-weight="bold" font-family="Space Grotesk">0</text>

  <!-- Power output label -->
  <rect x="{canvas_w//2 - 90}" y="8" width="180" height="44" rx="8" fill="rgba(11,20,55,0.85)" stroke="rgba(16,185,129,0.3)" stroke-width="1"/>
  <text x="{canvas_w//2 - 82}" y="24" fill="#94A3B8" font-size="9" font-family="Inter">ARRAY OUTPUT kW</text>
  <text id="powerDisplay" x="{canvas_w//2 - 82}" y="40" fill="#10B981" font-size="14" font-weight="bold" font-family="Space Grotesk">0.00</text>

</svg>

<div id="info-bar">
  <div>Time: <span id="clock">06:00</span></div>
  <div>Irradiance: <span id="irrLabel">0</span> W/m²</div>
  <div>Output: <span id="powerLabel">0.00</span> kW</div>
  <div>Cell Temp: <span id="tempLabel">--</span> °C</div>
  <div style="flex:1">
    <div style="font-size:10px;color:#475569;margin-bottom:3px">IRRADIANCE</div>
    <div id="irr-bar"><div id="irr-fill"></div></div>
  </div>
  <div>Wind: <span>{wind:.0f} km/h</span> · Zone: <span>{wind_zone}</span></div>
</div>

<script>
const W = {canvas_w};
const H = {canvas_h};
const PANELS = {p_qty};
const ROWS   = {anim_rows_count};
const COLS   = {anim_cols_count};
const SYS_KWP = {sys_size:.3f};
const TILT    = {tilt};
const AMB_TEMP= {temp_ambient};
const WIND_MS = {wind / 3.6:.2f};

// Simulate hour (0–23), cycled continuously
let simH = 6; // start at dawn
let simFrac = 0.0; // fractional hour

function lerp(a, b, t) {{ return a + (b - a) * t; }}
function clamp(v, lo, hi) {{ return Math.max(lo, Math.min(hi, v)); }}

// Sun path: arc from left(40, H-80) through apex(W/2, 28) to right(W-40, H-80)
function sunPos(hour) {{
  const t = clamp((hour - 6) / 12, 0, 1); // 0 at 6am, 1 at 6pm
  // Quadratic bezier: P0=(40,H-80), P1=(W/2,28), P2=(W-40,H-80)
  const P0x = 40, P0y = H - 80;
  const P1x = W / 2, P1y = 28;
  const P2x = W - 40, P2y = H - 80;
  const x = (1-t)*(1-t)*P0x + 2*(1-t)*t*P1x + t*t*P2x;
  const y = (1-t)*(1-t)*P0y + 2*(1-t)*t*P1y + t*t*P2y;
  return {{x, y}};
}}

function irradiance(hour) {{
  if (hour < 6 || hour > 18) return 0;
  return 1050 * Math.sin(Math.PI * (hour - 6) / 12);
}}

function cellTemp(irr) {{
  return AMB_TEMP + (45 - 20) * (irr / 800) / (1 + WIND_MS * 0.035);
}}

function powerKW(irr) {{
  const tempLoss = 1 - Math.max(0, (cellTemp(irr) - 25) * 0.0035);
  return SYS_KWP * (irr / 1000) * 0.975 * tempLoss * 0.965;
}}

// Color interpolation: night-blue → panel-blue → gold at peak
function panelColor(irrFrac) {{
  // 0 = deep blue, 0.5 = mid blue+teal, 1 = amber/gold
  if (irrFrac < 0.5) {{
    const t = irrFrac * 2;
    const r = Math.round(lerp(0x1E, 0x06, t));
    const g = Math.round(lerp(0x3A, 0x7A, t));
    const b = Math.round(lerp(0x8A, 0xC4, t));
    return `rgb(${{r}},${{g}},${{b}})`;
  }} else {{
    const t = (irrFrac - 0.5) * 2;
    const r = Math.round(lerp(0x06, 0xF5, t));
    const g = Math.round(lerp(0x7A, 0x9E, t));
    const b = Math.round(lerp(0xC4, 0x0B, t));
    return `rgb(${{r}},${{g}},${{b}})`;
  }}
}}

function skyTopColor(irrFrac) {{
  // dark navy → deep blue → rich dark blue at noon
  if (irrFrac < 0.5) {{
    const t = irrFrac * 2;
    return `rgb(${{Math.round(lerp(2,5,t))}},${{Math.round(lerp(11,15,t))}},${{Math.round(lerp(34,60,t))}})`;
  }} else {{
    const t = (irrFrac - 0.5) * 2;
    return `rgb(${{Math.round(lerp(5,8,t))}},${{Math.round(lerp(15,25,t))}},${{Math.round(lerp(60,80,t))}})`;
  }}
}}

// Wind particles
const NUM_WIND = 8;
let windParticles = [];
function initWind() {{
  for (let i = 0; i < NUM_WIND; i++) {{
    windParticles.push({{ x: Math.random() * W, y: 30 + Math.random() * (H - 120), vx: 1.5 + Math.random() * 2.5, vy: (Math.random()-0.5)*0.5 }});
  }}
  const svg = document.getElementById('mainSvg');
  const group = document.getElementById('windArrows');
  for (let i = 0; i < NUM_WIND; i++) {{
    const g = document.createElementNS('http://www.w3.org/2000/svg','g');
    g.setAttribute('id', 'wp'+i);
    const line = document.createElementNS('http://www.w3.org/2000/svg','line');
    line.setAttribute('stroke','rgba(6,182,212,0.6)');
    line.setAttribute('stroke-width','1.5');
    line.setAttribute('stroke-linecap','round');
    g.appendChild(line);
    group.appendChild(g);
  }}
}}

function updateWind(speed_factor) {{
  for (let i = 0; i < NUM_WIND; i++) {{
    const p = windParticles[i];
    p.x += p.vx * speed_factor;
    p.y += p.vy;
    if (p.x > W + 20) {{ p.x = -20; p.y = 30 + Math.random() * (H - 120); }}
    const g = document.getElementById('wp'+i);
    const line = g.querySelector('line');
    if (line) {{
      line.setAttribute('x1', p.x - p.vx * 12);
      line.setAttribute('y1', p.y);
      line.setAttribute('x2', p.x);
      line.setAttribute('y2', p.y);
      line.setAttribute('stroke-opacity', 0.3 + Math.random() * 0.4);
    }}
  }}
}}

// Light beams from sun to panels
function updateLightBeams(sunX, sunY, irrFrac) {{
  const group = document.getElementById('lightBeams');
  while (group.firstChild) group.removeChild(group.firstChild);
  if (irrFrac < 0.05) return;
  const opacity = irrFrac * 0.15;
  const targets = [
    [70, 80], [180, 80], [300, 80],
    [70, 190], [180, 190], [300, 190],
  ];
  targets.forEach(([tx, ty]) => {{
    const line = document.createElementNS('http://www.w3.org/2000/svg','line');
    line.setAttribute('x1', sunX); line.setAttribute('y1', sunY);
    line.setAttribute('x2', tx);   line.setAttribute('y2', ty);
    line.setAttribute('stroke', '#FCD34D');
    line.setAttribute('stroke-width', '0.8');
    line.setAttribute('stroke-opacity', opacity);
    group.appendChild(line);
  }});
}}

// Panels hover tooltip
document.querySelectorAll('.solar-panel').forEach((el, idx) => {{
  el.addEventListener('mouseenter', (e) => {{
    el.setAttribute('filter','url(#glow)');
  }});
}});

// Main animation loop
initWind();
const FPS = 30;
const SPEED = 0.04; // hours per frame (completes 24h in ~20s)

let lastTime = null;
function animate(ts) {{
  if (!lastTime) lastTime = ts;
  const dt = (ts - lastTime) / 1000; // seconds
  lastTime = ts;

  simH += SPEED;
  if (simH >= 24) simH = 0;

  const irr = irradiance(simH);
  const irrFrac = irr / 1050;
  const power = powerKW(irr);
  const cT = cellTemp(irr);

  // Sun position
  const spos = sunPos(simH);
  const sunG = document.getElementById('sunGroup');
  sunG.setAttribute('transform', `translate(${{spos.x}},${{spos.y}})`);
  sunG.style.opacity = simH >= 6 && simH <= 18 ? String(0.3 + irrFrac * 0.7) : '0';

  // Spin rays
  const rays = document.getElementById('sunRays');
  if (rays) rays.setAttribute('transform', `rotate(${{simH * 15 % 360}})`);

  // Sky colour
  document.getElementById('skyTop').setAttribute('stop-color', skyTopColor(irrFrac));

  // Update panel colours
  const color = panelColor(irrFrac);
  for (let i = 0; i < Math.min(PANELS, 225); i++) {{
    const el = document.getElementById('panel_' + i);
    if (el) el.setAttribute('fill', color);
  }}

  // Light beams
  updateLightBeams(spos.x, spos.y, irrFrac);

  // Wind
  updateWind(1.0 + irrFrac * 0.5);

  // Format time
  const hInt = Math.floor(simH);
  const mInt = Math.floor((simH - hInt) * 60);
  const timeStr = String(hInt).padStart(2,'0') + ':' + String(mInt).padStart(2,'0');

  // Update displays
  document.getElementById('timeDisplay').textContent = timeStr;
  document.getElementById('irrDisplay').textContent  = Math.round(irr);
  document.getElementById('powerDisplay').textContent= power.toFixed(2);
  document.getElementById('clock').textContent       = timeStr;
  document.getElementById('irrLabel').textContent    = Math.round(irr);
  document.getElementById('powerLabel').textContent  = power.toFixed(2);
  document.getElementById('tempLabel').textContent   = cT.toFixed(1);
  document.getElementById('irr-fill').style.width    = (irrFrac * 100) + '%';

  requestAnimationFrame(animate);
}}
requestAnimationFrame(animate);
</script>
</body>
</html>"""

    components.html(html_content, height=min(canvas_h + 60, 620), scrolling=True)

    st.markdown(f"""
    <div class='sxpro-card' style='margin-top:12px'>
      <h4>🏗️ Array Layout Summary</h4>
      <p>Array Configuration: <strong>{anim_rows_count} rows × {anim_cols_count} columns</strong> = <strong>{p_qty} panels</strong></p>
      <p>Total Panel Area: <strong>{p_qty * 2.1:.1f} m²</strong> &nbsp;·&nbsp; 
         Strings: <strong>{strings} × {panels_per_string} panels</strong> &nbsp;·&nbsp;
         String Voltage: <strong>{voc_string:.0f} V</strong></p>
      <p>Animation simulates irradiance from 00:00→24:00 showing panel temperature & output in real-time.</p>
    </div>
    """, unsafe_allow_html=True)

# ── TAB 2: Wind Load Visualizer ──────────────────────────────────────────
with tabs[2]:
    st.markdown("<span class='sxpro-section-label'>Wind Load Analysis & Structural Engineering</span>", unsafe_allow_html=True)

    wc1, wc2 = st.columns([2, 1])
    with wc2:
        # Wind speed gauge
        fig_wind = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=wind,
            delta={'reference': 50, 'increasing': {'color': "#EF4444"}, 'decreasing': {'color': "#10B981"}},
            gauge={
                'axis': {'range': [0, 200], 'tickwidth': 1, 'tickcolor': "#94A3B8",
                         'tickfont': {'color': '#94A3B8'}},
                'bar': {'color': "#F59E0B"},
                'bgcolor': "rgba(15,32,87,0.5)",
                'borderwidth': 2, 'bordercolor': "rgba(245,158,11,0.3)",
                'steps': [
                    {'range': [0, 40],   'color': 'rgba(16,185,129,0.25)'},
                    {'range': [40, 80],  'color': 'rgba(245,158,11,0.25)'},
                    {'range': [80, 120], 'color': 'rgba(239,68,68,0.25)'},
                    {'range': [120, 200],'color': 'rgba(220,38,38,0.4)'},
                ],
                'threshold': {'line': {'color': "#EF4444", 'width': 3}, 'thickness': 0.75, 'value': 120}
            },
            title={'text': "Wind Speed (km/h)", 'font': {'color': '#94A3B8', 'size': 12}}
        ))
        fig_wind.update_layout(
            height=300,
            paper_bgcolor='rgba(0,0,0,0)',
            font={'color': '#F59E0B', 'family': 'Space Grotesk'}
        )
        st.plotly_chart(fig_wind, use_container_width=True)

        # Wind load metrics
        zone_color = {"Low": "#10B981", "Moderate": "#F59E0B", "High": "#F97316", "Extreme": "#EF4444"}
        zc = zone_color.get(wind_zone, "#94A3B8")
        st.markdown(f"""
        <div class='sxpro-card'>
          <h4>Wind Load Summary</h4>
          <p>Zone: <strong style='color:{zc}'>{wind_zone}</strong></p>
          <p>Total Wind Force: <strong>{wind_force:.2f} kN</strong></p>
          <p>Force / Panel: <strong>{wind_force/max(p_qty,1)*1000:.1f} N</strong></p>
          <p>Status: <strong style='color:{"#10B981" if wind_safe else "#EF4444"}'>
            {"✅ Within Safe Limits" if wind_safe else "❌ EXCEEDS SAFE LIMIT"}</strong></p>
        </div>
        """, unsafe_allow_html=True)

    with wc1:
        # Wind load vs tilt angle chart
        tilts   = list(range(0, 61, 5))
        forces  = [calc_wind_load(wind, t, p_qty) for t in tilts]
        max_safe = sys_size * 50

        fig_wl = go.Figure()
        fig_wl.add_trace(go.Scatter(
            x=tilts, y=forces, name="Wind Force (kN)",
            line=dict(color='#06B6D4', width=3),
            fill='tozeroy', fillcolor='rgba(6,182,212,0.1)',
            hovertemplate='Tilt: %{x}°<br>Force: %{y:.2f} kN<extra></extra>'
        ))
        fig_wl.add_hline(y=max_safe, line_dash="dash", line_color="#EF4444",
                         annotation_text=f"Max Safe: {max_safe:.1f} kN", annotation_font_color="#EF4444")
        fig_wl.add_vline(x=tilt, line_dash="dot", line_color="#F59E0B",
                         annotation_text=f"Current: {tilt}°", annotation_font_color="#F59E0B")
        fig_wl.update_layout(
            height=320, title="Wind Force vs. Panel Tilt Angle",
            plot_bgcolor='rgba(11,20,55,0.6)', paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#94A3B8', family='Inter'),
            xaxis=dict(title="Tilt Angle (°)", gridcolor='rgba(255,255,255,0.05)'),
            yaxis=dict(title="Wind Force (kN)", gridcolor='rgba(255,255,255,0.05)'),
            legend=dict(bgcolor='rgba(0,0,0,0)'),
        )
        st.plotly_chart(fig_wl, use_container_width=True)

        # Wind pressure heatmap at different speeds & tilts
        speeds = [20, 40, 60, 80, 100, 120, 140, 160, 180, 200]
        tilts2  = [0, 10, 15, 20, 25, 30, 35, 40, 45, 60]
        z_heat = [[calc_wind_load(sp, t, p_qty) for sp in speeds] for t in tilts2]

        fig_heat = go.Figure(data=go.Heatmap(
            z=z_heat, x=speeds, y=tilts2,
            colorscale=[[0, '#10B981'], [0.4, '#F59E0B'], [0.7, '#F97316'], [1.0, '#EF4444']],
            hoverongaps=False,
            hovertemplate='Speed: %{x} km/h<br>Tilt: %{y}°<br>Force: %{z:.2f} kN<extra></extra>',
           colorbar=dict(
                  title=dict(
                  text='Force (kN)',
                  font=dict(color='#94A3B8')
                  ),
                  tickfont=dict(color='#94A3B8')
           )
        ))
        fig_heat.update_layout(
            height=280, title="Wind Load Heat Map — Force (kN) by Speed & Tilt",
            plot_bgcolor='rgba(11,20,55,0.6)', paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#94A3B8'),
            xaxis=dict(title="Wind Speed (km/h)"),
            yaxis=dict(title="Tilt Angle (°)"),
        )
        st.plotly_chart(fig_heat, use_container_width=True)

    st.divider()
    st.markdown("<span class='sxpro-section-label'>Recommended Structure Specification</span>", unsafe_allow_html=True)
    sc1, sc2, sc3, sc4 = st.columns(4)
    with sc1:
        st.markdown(f"""<div class='sxpro-card'>
          <h4>Frame Type</h4>
          <p><strong>{struct['type']}</strong></p>
          <p>Max Tilt: <strong>{struct['tilt_max']}°</strong></p>
          <p>Wind Zone: <strong>{wind_zone}</strong></p>
        </div>""", unsafe_allow_html=True)
    with sc2:
        st.markdown(f"""<div class='sxpro-card'>
          <h4>Material Spec</h4>
          <p><strong>{struct['material']}</strong></p>
          <p>Foundation: <strong>{struct['foundation']}</strong></p>
        </div>""", unsafe_allow_html=True)
    with sc3:
        st.markdown(f"""<div class='sxpro-card'>
          <h4>Fastening System</h4>
          <p>Clamp Type: <strong>{struct['clamp']}</strong></p>
          <p>Bolts: <strong>M12 × Grade 8.8</strong></p>
          <p>Torque: <strong>75 Nm</strong></p>
        </div>""", unsafe_allow_html=True)
    with sc4:
        st.markdown(f"""<div class='sxpro-card'>
          <h4>Safety Factors</h4>
          <p>Wind: <strong>{wind_force:.2f} kN</strong> / <strong>{max_safe:.0f} kN</strong> limit</p>
          <p>Safety Margin: <strong>{((max_safe - wind_force)/max_safe*100):.0f}%</strong></p>
          <p>Standard: <strong>EN 1991-1-4</strong></p>
        </div>""", unsafe_allow_html=True)

    if tilt > struct['tilt_max']:
        st.markdown(f"<div class='sxpro-error'>⚠️ <strong>TILT WARNING:</strong> Current tilt {tilt}° exceeds maximum recommended {struct['tilt_max']}° for {wind_zone} wind zone. Reduce tilt or upgrade structure grade.</div>", unsafe_allow_html=True)
    elif not wind_safe:
        st.markdown(f"<div class='sxpro-error'>⚠️ <strong>WIND LOAD CRITICAL:</strong> Total force {wind_force:.1f} kN exceeds safe limit. Upgrade to higher wind zone structure or reduce panel count per mounting.</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='sxpro-ok'>✅ Structure design is within safe limits. Wind load {wind_force:.2f} kN is {((max_safe-wind_force)/max_safe*100):.0f}% below threshold.</div>", unsafe_allow_html=True)

# ── TAB 3: Technical Specs ──────────────────────────────────────────────
with tabs[3]:
    st.markdown("<span class='sxpro-section-label'>Full System Technical Specifications</span>", unsafe_allow_html=True)
    tc1, tc2, tc3 = st.columns(3)
    with tc1:
        st.markdown(f"""<div class='sxpro-card'>
          <h4>🔆 Panel Specifications</h4>
          <p>Model: <strong>{panel_type}</strong></p>
          <p>Efficiency: <strong>{p_eff}%</strong></p>
          <p>Open Circuit Voltage: <strong>{voc} V</strong></p>
          <p>Short Circuit Current: <strong>{isc} A</strong></p>
          <p>Temp. Coefficient: <strong>{p_temp}%/°C</strong></p>
          <p>Grade: <strong>{p_note}</strong></p>
        </div>""", unsafe_allow_html=True)
    with tc2:
        st.markdown(f"""<div class='sxpro-card'>
          <h4>⚡ Array Configuration</h4>
          <p>Total Panels: <strong>{p_qty}</strong></p>
          <p>Strings: <strong>{strings}</strong></p>
          <p>Panels per String: <strong>{panels_per_string}</strong></p>
          <p>Total Area: <strong>{p_qty * 2.1:.1f} m²</strong></p>
          <p>System Size: <strong>{sys_size:.2f} kWp</strong></p>
        </div>""", unsafe_allow_html=True)
    with tc3:
        st.markdown(f"""<div class='sxpro-card'>
          <h4>🌡️ Operating Conditions</h4>
          <p>Tilt: <strong>{tilt}°</strong> | Azimuth: <strong>{azimuth}°</strong></p>
          <p>Ambient Temp: <strong>{temp_ambient} °C</strong></p>
          <p>GHI: <strong>{avg_ghi} kWh/m²/day</strong></p>
          <p>Peak Sun Hours: <strong>{sun_h} hrs</strong></p>
          <p>System Losses: <strong>{sys_loss}%</strong></p>
        </div>""", unsafe_allow_html=True)

    st.divider()
    # Performance ratio breakdown
    pr_losses = {
        "Temperature Loss": abs(p_temp / 100 * (temp_ambient - 25)) * 100,
        "Cable & Wiring": vd_percent,
        "Soiling": soiling,
        "System Losses": sys_loss - soiling_adv,
        "Inverter Inefficiency": 100 - inv_eff,
    }
    fig_pr = go.Figure(go.Waterfall(
        name="PR Breakdown", orientation="v",
        measure=["absolute"] + ["relative"] * len(pr_losses) + ["total"],
        x=["Ideal 100%"] + list(pr_losses.keys()) + ["Performance Ratio"],
        y=[100] + [-v for v in pr_losses.values()] + [None],
        connector={"line": {"color": "rgba(245,158,11,0.3)"}},
        decreasing={"marker": {"color": "#EF4444", "opacity": 0.8}},
        increasing={"marker": {"color": "#10B981"}},
        totals={"marker": {"color": "#F59E0B"}},
    ))
    fig_pr.update_layout(
        height=320, title="Performance Ratio Waterfall — Loss Breakdown",
        plot_bgcolor='rgba(11,20,55,0.6)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#94A3B8'), yaxis=dict(title="% of Ideal", gridcolor='rgba(255,255,255,0.05)'),
    )
    st.plotly_chart(fig_pr, use_container_width=True)

# ── TAB 4: Inverter Design ──────────────────────────────────────────────
with tabs[4]:
    st.markdown("<span class='sxpro-section-label'>Inverter & Grid Interface Design</span>", unsafe_allow_html=True)
    ic1, ic2, ic3 = st.columns(3)
    ic1.metric("Inverter Model",   inverter_type, inv_note)
    ic2.metric("Efficiency",       f"{inv_eff}%", f"+{(inv_bonus-1)*100:.1f}% bonus factor")
    ic3.metric("Grid Interface",   f"{grid_v}V / {grid_f}Hz", "Utility Grid Standard")

    st.divider()
    i1, i2, i3, i4 = st.columns(4)
    i1.metric("DC Input Voltage",   f"{voc_string:.0f} V",   "String VOC")
    i2.metric("MPPT Voltage",       f"{mppt_voltage:.0f} V",  "80% of VOC")
    i3.metric("DC Input Current",   f"{isc_string:.1f} A",    "All Strings")
    i4.metric("Estimated AC Out",   f"{sys_size * inv_eff / 100:.2f} kWp", "After losses")

    st.markdown(f"""<div class='sxpro-info' style='margin-top:12px'>
      ℹ️ <strong>{inv_note}</strong> — Recommended for {p_qty}-panel systems in {wind_zone} wind zones.
      String configuration: {strings} strings × {panels_per_string} panels @ {voc_string:.0f}V each.
    </div>""", unsafe_allow_html=True)

# ── TAB 5: Battery System ───────────────────────────────────────────────
with tabs[5]:
    st.markdown("<span class='sxpro-section-label'>Battery Energy Storage System</span>", unsafe_allow_html=True)
    if has_batt:
        bm1, bm2, bm3, bm4 = st.columns(4)
        bm1.metric("Chemistry",      battery_type,                b_note)
        bm2.metric("Total Capacity", f"{b_cap:.1f} kWh",          f"Voltage: {b_voltage}V")
        bm3.metric("Usable Energy",  f"{usable_battery_kwh:.1f} kWh", f"DoD: {dod}%")
        bm4.metric("Backup Hours",   f"{hours_of_autonomy:.1f} hrs",   f"At {h_load:.0f} kWh/day load")

        st.divider()
        b1, b2, b3 = st.columns(3)
        b1.metric("Round-Trip Eff.", f"{b_eff}%")
        b2.metric("Cycle Life",      f"{b_cycles:,} cycles")
        b3.metric("Lifetime",        f"{b_cycles/365:.1f} years")

        # Battery SOC animated chart
        fig_soc = go.Figure()
        fig_soc.add_trace(go.Scatter(
            x=list(hours_arr), y=soc, name="Battery SOC (kWh)",
            fill='tozeroy', fillcolor='rgba(16,185,129,0.15)',
            line=dict(color='#10B981', width=3),
        ))
        fig_soc.add_hline(y=b_cap * (dod / 100), line_dash="dash", line_color="#F59E0B",
                          annotation_text=f"Full Usable: {b_cap*(dod/100):.1f} kWh")
        fig_soc.update_layout(
            height=300, title="Battery State of Charge — 24hr Profile",
            plot_bgcolor='rgba(11,20,55,0.6)', paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#94A3B8'), xaxis=dict(title="Hour", gridcolor='rgba(255,255,255,0.05)'),
            yaxis=dict(title="kWh", gridcolor='rgba(255,255,255,0.05)'),
        )
        st.plotly_chart(fig_soc, use_container_width=True)
    else:
        st.markdown("<div class='sxpro-info'>ℹ️ Grid-Tied System — No Battery Storage configured. Select a battery type from the Battery & Load section to enable storage analysis.</div>", unsafe_allow_html=True)

    st.divider()
    st.markdown("<span class='sxpro-section-label'>Battery Chemistry Comparison Matrix</span>", unsafe_allow_html=True)
    bat_data = pd.DataFrame([
        {"Chemistry": k, "DoD %": v["default_dod"], "Efficiency %": v["efficiency"],
         "Life (yrs)": v["life_years"], "Best For": "Budget" if k == "Lead-Acid" else "Longevity" if k == "Lithium-Ion" else "Mid-Range"}
        for k, v in BATTERY_TYPES.items()
    ])
    st.dataframe(bat_data, use_container_width=True, hide_index=True)

# ── TAB 6: Electrical Design ────────────────────────────────────────────
with tabs[6]:
    st.markdown("<span class='sxpro-section-label'>Electrical System Design — IEC 60364 / NEC</span>", unsafe_allow_html=True)
    ec1, ec2, ec3 = st.columns(3)
    with ec1:
        st.metric("DC Voltage (VOC)", f"{voc_string:.0f} V",  f"Strings: {strings}")
        st.metric("DC Current (ISC)", f"{isc_string:.1f} A",   "All strings combined")
        st.metric("MPPT Voltage",     f"{mppt_voltage:.0f} V", "Operating point")
    with ec2:
        st.metric("Cable Size",       f"{cable_size} mm²",     f"{wire_length} m run")
        st.metric("Voltage Drop",     f"{voltage_drop:.2f} V",  f"{vd_percent:.2f}%")
        st.metric("DC Current/cable", f"{current_dc:.1f} A",   "Sizing current")
    with ec3:
        st.metric("Grid Standard",    f"{grid_v}V / {grid_f}Hz", country)
        st.metric("Lightning Rod Ht.", f"{rod_height:.1f} m",  "IEC 62305")
        st.metric("Protection Radius",f"{protection_radius} m","Rolling sphere method")

    st.divider()
    if vd_percent > 3:
        st.markdown(f"<div class='sxpro-error'>⚠️ <strong>Voltage Drop {vd_percent:.2f}% exceeds 3% limit!</strong> Upgrade cable from {cable_size}mm² to {cable_size+6}mm² or reduce cable length to {wire_length*0.7:.0f}m.</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='sxpro-ok'>✅ Voltage drop {vd_percent:.2f}% is within the 3% design limit. Cable sizing is adequate.</div>", unsafe_allow_html=True)

    # Cable sizing chart
    cable_sizes = [4, 6, 10, 16, 25]
    vd_vals = [(current_dc * wire_length * 0.0175) / cs / mppt_voltage * 100 if mppt_voltage > 0 else 0 for cs in cable_sizes]
    fig_cable = go.Figure()
    fig_cable.add_trace(go.Bar(
        x=[f"{cs}mm²" for cs in cable_sizes], y=vd_vals,
        marker_color=['#EF4444' if v > 3 else '#10B981' for v in vd_vals],
        hovertemplate='%{x}: %{y:.2f}%<extra></extra>'
    ))
    fig_cable.add_hline(y=3, line_dash="dash", line_color="#F59E0B", annotation_text="3% Limit")
    fig_cable.update_layout(
        height=300, title="Voltage Drop % by Cable Size",
        plot_bgcolor='rgba(11,20,55,0.6)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#94A3B8'),
        yaxis=dict(title="Voltage Drop %", gridcolor='rgba(255,255,255,0.05)'),
        xaxis=dict(title="Cable Cross-Section"),
    )
    st.plotly_chart(fig_cable, use_container_width=True)

# ── TAB 7: Financial Model ──────────────────────────────────────────────
with tabs[7]:
    st.markdown("<span class='sxpro-section-label'>25-Year Financial Investment Model</span>", unsafe_allow_html=True)

    fm1, fm2, fm3, fm4 = st.columns(4)
    fm1.metric("Gross CapEx",    f"{gross_cost:,.0f} {c_curr}",  "Before subsidy")
    fm2.metric("Net CapEx",      f"{net_cost:,.0f} {c_curr}",   f"-{subsidy_pct}% subsidy")
    fm3.metric("Simple Payback", f"{payback:.1f} yrs",           f"Yr1: {yearly_profit[0]:,.0f} {c_curr}")
    fm4.metric("25-yr NPV",      f"{npv:,.0f} {c_curr}",         f"IRR ~{(yearly_profit[0]/net_cost*100):.1f}%")

    st.progress(min(1.0, payback / 15))

    # 25-year cashflow
    cumulative = np.cumsum(yearly_profit) - net_cost
    fig_fin = make_subplots(specs=[[{"secondary_y": True}]])
    fig_fin.add_trace(go.Bar(x=list(range(25)), y=list(yearly_profit), name="Annual Revenue",
                             marker_color='rgba(245,158,11,0.7)'), secondary_y=False)
    fig_fin.add_trace(go.Scatter(x=list(range(25)), y=list(cumulative), name="Cumulative NPV",
                                 line=dict(color='#10B981', width=3)), secondary_y=True)
    fig_fin.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.2)")
    fig_fin.update_layout(
        height=400, title="25-Year Financial Projection (with Tariff Inflation)",
        plot_bgcolor='rgba(11,20,55,0.6)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#94A3B8'),
        legend=dict(bgcolor='rgba(0,0,0,0)'),
    )
    fig_fin.update_yaxes(title_text=f"Annual Revenue ({c_curr})", gridcolor='rgba(255,255,255,0.05)', secondary_y=False)
    fig_fin.update_yaxes(title_text=f"Cumulative NPV ({c_curr})", secondary_y=True)
    st.plotly_chart(fig_fin, use_container_width=True)

    st.divider()
    # Cost breakdown pie
    cost_labels = ["Panels", "Inverter", "Battery", "Structure", "Cable", "Lightning", "Installation"]
    cost_values = [panel_cost, inverter_cost, battery_cost, structure_cost, cable_cost, lightning_cost, sys_size * install_cost]
    cost_values = [max(0, v) for v in cost_values]

    fig_pie = go.Figure(go.Pie(
        labels=cost_labels, values=cost_values,
        hole=0.45,
        marker=dict(colors=['#F59E0B','#06B6D4','#10B981','#8B5CF6','#F97316','#EC4899','#64748B'],
                    line=dict(color='#050E25', width=2)),
        textfont=dict(color='white', size=11),
        hovertemplate='%{label}: %{value:,.0f} %{customdata}<extra></extra>',
        customdata=[c_curr]*7,
    ))
    fig_pie.update_layout(
        height=350, title="CapEx Cost Breakdown",
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#94A3B8'),
        legend=dict(bgcolor='rgba(15,32,87,0.5)', bordercolor='rgba(255,255,255,0.1)', borderwidth=1),
        annotations=[dict(text=f"{c_curr}<br>{net_cost/1000:,.0f}K", x=0.5, y=0.5, font_size=13,
                          font_color='#F59E0B', showarrow=False)]
    )
    st.plotly_chart(fig_pie, use_container_width=True)

    st.divider()
    fa1, fa2, fa3 = st.columns(3)
    fa1.metric("Daily Savings",    f"{fin_report['Daily_Savings_Currency']:,.2f} {c_curr}")
    fa2.metric("Export Credit/day",f"{fin_report['Export_Credit']:,.2f} {c_curr}")
    fa3.metric("Adv. Payback",     f"{fin_report['Estimated_Payback_Years']:.1f} yrs",  "Physics engine result")

# ── TAB 8: Eco & Carbon ─────────────────────────────────────────────────
with tabs[8]:
    st.markdown("<span class='sxpro-section-label'>Environmental Impact & Carbon Analysis</span>", unsafe_allow_html=True)
    ec1, ec2, ec3, ec4 = st.columns(4)
    ec1.metric("CO₂ Avoided/Year",     f"{co2_annual:.2f} tons",   "vs grid average")
    ec2.metric("Lifetime CO₂ Saved",   f"{co2_annual*25:.0f} tons","25-year period")
    ec3.metric("Trees Equivalent",     f"{int(co2_annual*18)}/yr",  "annual carbon offset")
    ec4.metric("Coal Saved/Year",       f"{co2_annual/2.2:.1f} tons","coal power equivalent")

    years_range = list(range(1, 26))
    co2_cumulative = [co2_annual * y for y in years_range]
    fig_eco = go.Figure()
    fig_eco.add_trace(go.Scatter(
        x=years_range, y=co2_cumulative, name="Cumulative CO₂ Avoided",
        fill='tozeroy', fillcolor='rgba(16,185,129,0.15)',
        line=dict(color='#10B981', width=3)
    ))
    fig_eco.update_layout(
        height=300, title="Cumulative CO₂ Avoided Over System Lifetime",
        plot_bgcolor='rgba(11,20,55,0.6)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#94A3B8'),
        xaxis=dict(title="Year", gridcolor='rgba(255,255,255,0.05)'),
        yaxis=dict(title="Tons CO₂", gridcolor='rgba(255,255,255,0.05)'),
    )
    st.plotly_chart(fig_eco, use_container_width=True)

# ── TAB 9: ESG Ethics ───────────────────────────────────────────────────
with tabs[9]:
    st.markdown("<span class='sxpro-section-label'>ESG, Ethics & Supply Chain Compliance</span>", unsafe_allow_html=True)
    eg1, eg2, eg3, eg4 = st.columns(4)
    eg1.metric("ESG Rating",       esg_rating,    country)
    eg2.metric("Labor Risk",       labor_risk,     "Supply chain")
    eg3.metric("Electricity Access",f"{elec_access}%","National average")
    eg4.metric("Panel Sourcing",   sourcing)

    st.markdown(f"""
    <div class='sxpro-card' style='margin-top:16px'>
      <h4>🌍 ESG Profile — {country}</h4>
      <p><strong>Rating:</strong> {esg_rating} &nbsp;&nbsp; <strong>Sourcing Standard:</strong> {sourcing}</p>
      <p><strong>Labor Risk Level:</strong> {labor_risk} &nbsp;&nbsp; <strong>Grid Access:</strong> {elec_access}%</p>
      <p style='margin-top:12px;color:#64748B;font-size:0.8rem'>
        ESG ratings reflect country-level governance, environmental commitments, and labor standards in the solar supply chain.
        Sourcing category indicates whether panels originate from locally certified, EU-certified, or import supply chains.
      </p>
    </div>
    """, unsafe_allow_html=True)

# ── TAB 10: Net Metering ────────────────────────────────────────────────
with tabs[10]:
    st.markdown("<span class='sxpro-section-label'>Net Metering & Grid Export Analysis</span>", unsafe_allow_html=True)
    if net_metering:
        nm1, nm2, nm3, nm4 = st.columns(4)
        nm1.metric("Daily Generation",   f"{sum(gen_24):.1f} kWh")
        nm2.metric("Daily Export",       f"{sum(export_24):.1f} kWh",  f"@ {sell_rate} {c_curr}/kWh")
        nm3.metric("Daily Import",       f"{sum(import_24):.1f} kWh",  f"@ {buy_rate} {c_curr}/kWh")
        nm4.metric("Export Credit/day",  f"{sum(export_24)*sell_rate:,.2f} {c_curr}")
        st.markdown("<div class='sxpro-ok'>✅ Net Metering is active. Export surplus to grid and earn feed-in credits.</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='sxpro-warn'>⚠️ Net Metering disabled. All excess generation is curtailed.</div>", unsafe_allow_html=True)

# ── TAB 11: AI Diagnosis ────────────────────────────────────────────────
with tabs[11]:
    st.markdown("<span class='sxpro-section-label'>🤖 AI System Diagnosis & Optimisation Advisor</span>", unsafe_allow_html=True)

    d1, d2, d3 = st.columns(3)
    d1.metric("Performance Ratio", f"{pr:.1f}%",     "System quality index")
    d2.metric("Design Score",      f"{'A' if pr>80 else 'B' if pr>70 else 'C'}",  "Overall grade")
    d3.metric("Optimisation Potential", f"{max(0, 85 - pr):.1f}%", "Improvement room")

    issues = []
    recommendations = []

    if vd_percent > 3:
        issues.append(f"🔴 Voltage drop {vd_percent:.2f}% exceeds 3% — increase cable to {cable_size+6}mm²")
    if tilt > struct['tilt_max']:
        issues.append(f"🔴 Tilt {tilt}° exceeds structural max {struct['tilt_max']}° for {wind_zone} zone")
    if not wind_safe:
        issues.append(f"🔴 Wind load {wind_force:.1f} kN exceeds safe structure limit")
    if pr < 70:
        issues.append(f"🟡 Low performance ratio {pr:.1f}% — review orientation, soiling, and shading")
    if soiling > 10:
        issues.append("🟡 High soiling losses — consider automatic cleaning schedule")
    if payback > 12:
        issues.append("🟡 Long payback period — review tariff rates or reduce system cost")

    if not issues:
        issues.append("🟢 No critical issues detected — system design is within all parameters")

    if tilt < abs(c_lat) - 5:
        recommendations.append(f"💡 Increase tilt to ~{int(abs(c_lat))}° to match latitude for maximum annual yield")
    if cable_size < 10 and sys_size > 10:
        recommendations.append("💡 Consider upgrading to 10mm² cable for improved reliability on large systems")
    if not has_batt:
        recommendations.append("💡 Adding LiFePO4 battery would increase self-consumption by ~35%")
    recommendations.append(f"💡 Annual cleaning schedule (2–4 times/yr) could recover {soiling/2:.1f}% in yield losses")

    st.markdown("<div class='sxpro-section-label' style='margin-top:8px'>Issues Detected</div>", unsafe_allow_html=True)
    for issue in issues:
        level = "sxpro-error" if "🔴" in issue else ("sxpro-warn" if "🟡" in issue else "sxpro-ok")
        st.markdown(f"<div class='{level}'>{issue}</div>", unsafe_allow_html=True)

    st.markdown("<div class='sxpro-section-label' style='margin-top:12px'>Optimisation Recommendations</div>", unsafe_allow_html=True)
    for rec in recommendations:
        st.markdown(f"<div class='sxpro-info'>{rec}</div>", unsafe_allow_html=True)

    st.divider()
    st.text_area("📋 Full Engineering Audit Report", value=f"""
════════════════════════════════════════════════════════════════════
       SOLARX PROFESSIONAL — ENGINEERING AUDIT REPORT
════════════════════════════════════════════════════════════════════
Generated : {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Country   : {country} | Location: {location_name}
════════════════════════════════════════════════════════════════════
SYSTEM SUMMARY
  Peak PV Capacity    : {sys_size:.2f} kWp
  Panel Configuration : {p_qty} × {panel_type}
  Inverter            : {inverter_type} @ {inv_eff}%
  Battery             : {battery_type} — {b_cap} kWh
  Backup Autonomy     : {hours_of_autonomy:.1f} hours

PERFORMANCE ANALYSIS
  Daily Generation    : {sum(gen_24):.2f} kWh
  Performance Ratio   : {pr:.1f}%
  Self-Consumption    : {(1-sum(import_24)/max(h_load,1))*100:.1f}%
  Annual Yield        : {sum(gen_24)*365:.0f} kWh/year

ELECTRICAL DESIGN
  String Voltage VOC  : {voc_string:.0f} V
  DC Current ISC      : {isc_string:.1f} A
  Cable Size          : {cable_size} mm² × {wire_length} m
  Voltage Drop        : {vd_percent:.2f}%

STRUCTURAL & SAFETY
  Wind Zone           : {wind_zone}
  Wind Speed          : {wind:.0f} km/h
  Wind Force          : {wind_force:.2f} kN
  Structure Type      : {struct['type']}
  Lightning Rod       : {rod_height:.1f} m (IEC 62305)

FINANCIAL ANALYSIS
  Gross CapEx         : {gross_cost:,.0f} {c_curr}
  Net CapEx           : {net_cost:,.0f} {c_curr} (after {subsidy_pct}% subsidy)
  Simple Payback      : {payback:.1f} years
  25-Year NPV         : {npv:,.0f} {c_curr}
  CO₂ Avoided/Year    : {co2_annual:.2f} tons

════════════════════════════════════════════════════════════════════
ISSUES   : {len([i for i in issues if '🔴' in i])} critical | {len([i for i in issues if '🟡' in i])} warnings
GRADE    : {"A — Excellent Design" if pr > 80 else "B — Good Design" if pr > 70 else "C — Needs Optimisation"}
════════════════════════════════════════════════════════════════════
""", height=340)

# ── TAB 12: Physics Engine ──────────────────────────────────────────────
with tabs[12]:
    st.markdown("<span class='sxpro-section-label'>Advanced Physics Engine — Real-Time Simulation</span>", unsafe_allow_html=True)

    if live_weather_toggle:
        st.markdown("<div class='sxpro-info'>🛰️ Live satellite telemetry mode active — fetching real meteorological data</div>", unsafe_allow_html=True)
        col_la, col_lo = st.columns(2)
        lat_in = col_la.text_input("GPS Latitude",  str(round(lat, 4)))
        lon_in = col_lo.text_input("GPS Longitude", str(round(lon, 4)))
        sim_data_df = fetch_meteorological_data(float(lat_in), float(lon_in))
        mode_tag = "live"
        if sim_data_df is None:
            st.markdown("<div class='sxpro-warn'>⚠️ Weather API unavailable — using database fallback values.</div>", unsafe_allow_html=True)
            sim_data_df = pd.DataFrame({
                "Hour": list(range(24)) * 3,
                "Temperature": [temp_ambient] * 72,
                "Wind_Speed": [wind / 3.6] * 72,
                "Cloud_Cover": [cloud_pct] * 72,
            })
    else:
        st.markdown("<div class='sxpro-info'>🗺️ Country database simulation mode — using regional climate profiles</div>", unsafe_allow_html=True)
        sim_hours  = list(range(24))
        mock_temps = [temp_ambient - 4 + 8 * np.sin(np.pi * (h - 6) / 12) if 6 <= h <= 18 else temp_ambient - 4 for h in sim_hours]
        sim_data_df = pd.DataFrame({
            "Hour": sim_hours,
            "Temperature": mock_temps,
            "Wind_Speed": [wind / 3.6] * 24,
            "Cloud_Cover": [cloud_pct] * 24,
        })
        mode_tag = "country"

    output_metrics = []
    for _, row in sim_data_df.iterrows():
        calc = model_solar_physics(row["Temperature"], row["Wind_Speed"], row["Cloud_Cover"],
                                   int(row["Hour"]), adv_cfg, scenario_mode=mode_tag)
        output_metrics.append(calc)

    calc_res_df = pd.DataFrame(output_metrics)
    sim_data_df = sim_data_df.copy()
    sim_data_df["Incident_Irradiance"] = calc_res_df["Irradiance"].values
    sim_data_df["Cell_Temperature"]    = calc_res_df["Cell_Temp"].values
    sim_data_df["Hourly_Yield_kW"]     = calc_res_df["Power_kW"].values

    total_adv_gen = sim_data_df["Hourly_Yield_kW"].sum() if mode_tag == "country" else (sim_data_df["Hourly_Yield_kW"].sum() / 3.0)

    pm1, pm2, pm3, pm4 = st.columns(4)
    pm1.metric("Physics Engine Daily Yield", f"{total_adv_gen:.2f} kWh")
    pm2.metric("Peak Cell Temp",             f"{sim_data_df['Cell_Temperature'].max():.1f} °C")
    pm3.metric("Avg Irradiance",             f"{sim_data_df['Incident_Irradiance'].mean():.1f} W/m²")
    pm4.metric("Peak Power",                 f"{sim_data_df['Hourly_Yield_kW'].max():.2f} kW")

    fig_phys = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                             subplot_titles=("Array Output (kW)", "Cell Temperature & Irradiance"))
    fig_phys.add_trace(go.Scatter(x=sim_data_df["Hour"], y=sim_data_df["Hourly_Yield_kW"],
                                   fill='tozeroy', fillcolor='rgba(245,158,11,0.1)',
                                   line=dict(color='#F59E0B', width=2.5), name="Power kW"), row=1, col=1)
    fig_phys.add_trace(go.Scatter(x=sim_data_df["Hour"], y=sim_data_df["Cell_Temperature"],
                                   line=dict(color='#EF4444', width=2), name="Cell Temp °C"), row=2, col=1)
    fig_phys.add_trace(go.Scatter(x=sim_data_df["Hour"], y=sim_data_df["Incident_Irradiance"],
                                   line=dict(color='#06B6D4', width=2), name="Irradiance W/m²"), row=2, col=1)
    fig_phys.update_layout(height=500, plot_bgcolor='rgba(11,20,55,0.6)', paper_bgcolor='rgba(0,0,0,0)',
                            font=dict(color='#94A3B8'), showlegend=True,
                            legend=dict(bgcolor='rgba(0,0,0,0)'))
    st.plotly_chart(fig_phys, use_container_width=True)
    st.dataframe(sim_data_df.round(2), use_container_width=True, hide_index=True)

# ── TAB 13: Storage Matrix ──────────────────────────────────────────────
with tabs[13]:
    st.markdown("<span class='sxpro-section-label'>Battery & Storage Configuration Matrix</span>", unsafe_allow_html=True)
    sm1, sm2, sm3, sm4 = st.columns(4)
    sm1.metric("Total Storage",     f"{b_cap:.2f} kWh")
    sm2.metric("Usable Capacity",   f"{usable_battery_kwh:.2f} kWh",  f"DoD: {dod}%")
    sm3.metric("Backup Autonomy",   f"{hours_of_autonomy:.1f} hrs",    f"@ {h_load:.0f} kWh/day")
    sm4.metric("Battery CapEx",     f"{battery_cost:,.0f} {c_curr}",   f"{b_cost}/kWh")

    st.divider()
    full_bat_df = pd.DataFrame({
        "Battery Type":     list(battery_db.keys()),
        "Efficiency (%)":   [v[0] for v in battery_db.values()],
        "Cycle Life":       [v[1] for v in battery_db.values()],
        "Cost/kWh":         [v[2] for v in battery_db.values()],
        "Annual Degrade %": [v[3] for v in battery_db.values()],
        "Bus Voltage (V)":  [v[4] for v in battery_db.values()],
        "Notes":            [v[5] for v in battery_db.values()],
    })
    st.dataframe(full_bat_df, use_container_width=True, hide_index=True)

    if b_cost > 0:
        fig_bat = go.Figure()
        eff_vals  = [v[0] for v in battery_db.values() if v[0] > 0]
        cyc_vals  = [v[1] for v in battery_db.values() if v[0] > 0]
        cost_vals = [v[2] for v in battery_db.values() if v[0] > 0]
        bat_names = [k for k, v in battery_db.items() if v[0] > 0]

        fig_bat.add_trace(go.Scatter(
            x=eff_vals, y=cyc_vals,
            mode='markers+text', text=bat_names,
            textposition="top center", textfont=dict(color='#94A3B8', size=10),
            marker=dict(size=[c/5 for c in cost_vals], color=cost_vals,
                        colorscale='Plasma', showscale=True,
                        colorbar=dict(title="Cost/kWh", tickfont=dict(color='#94A3B8')),
                        line=dict(color='#F59E0B', width=1.5)),
        ))
        fig_bat.update_layout(
            height=350, title="Battery Technology: Efficiency vs. Cycle Life (bubble size = cost)",
            plot_bgcolor='rgba(11,20,55,0.6)', paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#94A3B8'),
            xaxis=dict(title="Round-Trip Efficiency (%)", gridcolor='rgba(255,255,255,0.05)'),
            yaxis=dict(title="Cycle Life (cycles)", gridcolor='rgba(255,255,255,0.05)'),
        )
        st.plotly_chart(fig_bat, use_container_width=True)

# ── TAB 14: Export Report ───────────────────────────────────────────────
with tabs[14]:
    st.markdown("<span class='sxpro-section-label'>Export — Full Report Package</span>", unsafe_allow_html=True)

    df_export = pd.DataFrame({
        "Hour":              list(hours_arr),
        "Generation_kW":     [round(x, 3) for x in gen_24],
        "Load_kW":           [round(x, 3) for x in load_24],
        "Export_kW":         [round(x, 3) for x in export_24],
        "Import_kW":         [round(x, 3) for x in import_24],
        "Battery_SOC_kWh":   [round(x, 3) for x in soc],
        "Battery_SOC_pct":   [round((x / b_cap) * 100, 1) if has_batt and b_cap > 0 else 0 for x in soc],
    })
    csv = df_export.to_csv(index=False).encode('utf-8')

    # Summary CSV
    summary_data = {
        "Parameter": [
            "Country", "Location", "System Size kWp", "Panel Count", "Panel Model",
            "Inverter", "Battery", "Daily Generation kWh", "Performance Ratio %",
            "Wind Zone", "Wind Speed km/h", "Wind Force kN", "Cable Size mm²",
            "Voltage Drop %", "Gross CapEx", "Net CapEx", "Payback Years",
            "25yr NPV", "CO2 Avoided t/yr", "ESG Rating", "Grid Voltage", "Autonomy Hours"
        ],
        "Value": [
            country, location_name, f"{sys_size:.2f}", p_qty, panel_type,
            inverter_type, battery_type, f"{sum(gen_24):.2f}", f"{pr:.1f}",
            wind_zone, f"{wind:.0f}", f"{wind_force:.2f}", cable_size,
            f"{vd_percent:.2f}", f"{gross_cost:,.0f}", f"{net_cost:,.0f}",
            f"{payback:.1f}", f"{npv:,.0f}", f"{co2_annual:.2f}", esg_rating,
            f"{grid_v}V/{grid_f}Hz", f"{hours_of_autonomy:.1f}"
        ]
    }
    summary_df  = pd.DataFrame(summary_data)
    summary_csv = summary_df.to_csv(index=False).encode('utf-8')

    ec1, ec2, ec3 = st.columns(3)
    with ec1:
        st.download_button(
            "📥 Download Hourly Profile (CSV)",
            csv, f"SolarX_{country}_Hourly_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv", use_container_width=True
        )
    with ec2:
        st.download_button(
            "📋 Download System Summary (CSV)",
            summary_csv, f"SolarX_{country}_Summary_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv", use_container_width=True
        )
    with ec3:
        enable_pdf = st.checkbox("Enable PDF Export (requires fpdf2)")
        if enable_pdf:
            report_data_pdf = {
                "Country": country, "Location": location_name,
                "System Size": f"{sys_size:.2f} kWp", "Panel Count": p_qty,
                "Panel Model": panel_type, "Daily Gen": f"{sum(gen_24):.2f} kWh",
                "PR": f"{pr:.1f}%", "Wind": f"{wind:.0f} km/h / {wind_zone}",
                "Wind Force": f"{wind_force:.2f} kN", "Cable": f"{cable_size}mm²",
                "VD Loss": f"{vd_percent:.2f}%", "Gross Cost": f"{gross_cost:,.0f} {c_curr}",
                "Net Cost": f"{net_cost:,.0f} {c_curr}", "Payback": f"{payback:.1f} yrs",
                "25yr NPV": f"{npv:,.0f} {c_curr}", "CO2/yr": f"{co2_annual:.2f} t",
                "ESG": esg_rating,
            }
            pdf_bytes = generate_pdf_report(report_data_pdf)
            if pdf_bytes:
                st.download_button(
                    "📄 Download PDF Report",
                    pdf_bytes, f"SolarX_Report_{country}.pdf",
                    mime="application/pdf", use_container_width=True
                )
            else:
                st.info("Install fpdf2: `pip install fpdf2`")

    st.divider()
    st.markdown("<span class='sxpro-section-label'>Hourly Data Preview</span>", unsafe_allow_html=True)
    st.dataframe(df_export, height=340, use_container_width=True, hide_index=True)

# ╔══════════════════════════════════════════════════════════════════════╗
# ║                          PAGE FOOTER                                 ║
# ╚══════════════════════════════════════════════════════════════════════╝
st.divider()
st.markdown(f"""
<div style='text-align:center;color:#334155;font-size:0.75rem;padding:16px 0 8px'>
  <strong style='color:#475569'>SolarX Professional v3.0</strong> — Enterprise Solar Power Estimation Platform<br>
  Physics-Based | 120+ Countries | 25+ Panel Models | Wind Load Analysis | ESG Compliance<br>
  <span style='color:#1E3A5F'>Designed for commercial sale — all calculations for planning purposes only.</span>
</div>
""", unsafe_allow_html=True)
