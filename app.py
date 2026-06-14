bash

cat > /home/claude/app.py << 'PYEOF'
"""
SolarX Professional v4.1 — Solar Power Estimator
Enterprise Edition — Zero-Error Build
"""
import streamlit as st

st.set_page_config(
    page_title="SolarX Pro — Enterprise Solar Estimator",
    layout="wide",
    page_icon="☀️",
    initial_sidebar_state="expanded",
)

# ─── TERMS ───────────────────────────────────────────────────────────────────
def show_terms():
    @st.dialog("📄 Terms & Privacy Agreement — SolarX Professional")
    def terms_dialog():
        st.markdown("""
        <div style='background:#0f172a;padding:16px;border-radius:12px;color:#e2e8f0;font-size:0.92rem'>
        <h3>⚠️ Important Disclaimer</h3>
        By using <strong>SolarX Professional</strong>, you confirm:<br><br>
        1. <strong>No Liability</strong> — Calculations are for planning only.<br>
        2. <strong>Data Privacy</strong> — Location used only for weather API. Nothing stored.<br>
        3. <strong>Accuracy</strong> — Results may vary ±20% due to real-world conditions.<br>
        4. <strong>Third-Party APIs</strong> — Uses Open-Meteo & Nominatim.<br>
        5. <strong>Professional Advice</strong> — Always consult a certified solar engineer.
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
import json
import streamlit.components.v1 as components

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

# ─── THEME ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Space+Grotesk:wght@400;500;700&display=swap');
:root {
  --solar-gold:#F59E0B; --solar-amber:#FCD34D; --deep-navy:#0B1437;
  --mid-navy:#0F2057; --panel-blue:#1E3A8A; --sky-cyan:#06B6D4;
  --energy-green:#10B981; --alert-red:#EF4444;
  --text-primary:#F1F5F9; --text-muted:#94A3B8;
  --glass:rgba(255,255,255,0.05); --glass-border:rgba(255,255,255,0.10);
}
html,body,[class*="css"]{font-family:'Inter',sans-serif;color:var(--text-primary);}
.stApp{background:linear-gradient(160deg,#0B1437 0%,#0F2057 40%,#0B2040 70%,#071020 100%);background-attachment:fixed;min-height:100vh;}
[data-testid="stSidebar"]{background:rgba(11,20,55,0.97)!important;border-right:1px solid var(--glass-border)!important;}
[data-testid="stSidebar"] p{color:#CBD5E1!important;font-size:0.82rem!important;}
[data-testid="stMetricValue"]{color:var(--solar-gold)!important;font-family:'Space Grotesk',sans-serif!important;font-size:1.5rem!important;font-weight:700!important;}
[data-testid="stMetricLabel"]{color:var(--text-muted)!important;font-size:0.75rem!important;text-transform:uppercase;letter-spacing:0.08em;}
div[data-testid="metric-container"]{background:var(--glass)!important;border:1px solid var(--glass-border)!important;border-radius:16px!important;padding:18px 20px!important;backdrop-filter:blur(20px)!important;transition:transform 0.2s ease;}
div[data-testid="metric-container"]:hover{transform:translateY(-3px);border-color:var(--solar-gold)!important;}
div[data-testid="stTabs"] [data-baseweb="tab-list"]{background:rgba(11,20,55,0.5)!important;border-radius:14px!important;padding:6px!important;border:1px solid var(--glass-border)!important;gap:4px!important;flex-wrap:wrap;}
div[data-testid="stTabs"] button[data-baseweb="tab"]{background:transparent!important;color:var(--text-muted)!important;border-radius:10px!important;font-weight:500!important;font-size:0.8rem!important;padding:8px 14px!important;border:none!important;}
div[data-testid="stTabs"] button[aria-selected="true"]{background:linear-gradient(135deg,var(--solar-gold),#D97706)!important;color:#0B1437!important;font-weight:700!important;}
.stButton>button[kind="primary"]{background:linear-gradient(135deg,var(--solar-gold),#D97706)!important;color:#0B1437!important;border:none!important;border-radius:10px!important;font-weight:700!important;}
.stButton>button[kind="secondary"]{background:var(--glass)!important;color:var(--text-primary)!important;border:1px solid var(--glass-border)!important;border-radius:10px!important;}
.stDownloadButton>button{background:linear-gradient(135deg,var(--energy-green),#059669)!important;color:white!important;border:none!important;border-radius:10px!important;font-weight:600!important;width:100%;}
.sxcard{background:rgba(15,32,87,0.4);border:1px solid rgba(245,158,11,0.2);border-radius:16px;padding:20px 24px;margin:8px 0;backdrop-filter:blur(16px);}
.sxcard h4{color:var(--solar-gold);margin:0 0 12px 0;font-size:0.85rem;text-transform:uppercase;letter-spacing:0.08em;}
.sxcard p{color:var(--text-muted);margin:4px 0;font-size:0.88rem;}
.sxcard strong{color:var(--text-primary);}
.sx-warn{background:rgba(245,158,11,0.15);border-left:4px solid var(--solar-gold);border-radius:0 10px 10px 0;padding:12px 16px;color:#FCD34D;margin:8px 0;}
.sx-error{background:rgba(239,68,68,0.15);border-left:4px solid var(--alert-red);border-radius:0 10px 10px 0;padding:12px 16px;color:#FCA5A5;margin:8px 0;}
.sx-ok{background:rgba(16,185,129,0.15);border-left:4px solid var(--energy-green);border-radius:0 10px 10px 0;padding:12px 16px;color:#6EE7B7;margin:8px 0;}
.sx-info{background:rgba(6,182,212,0.12);border-left:4px solid var(--sky-cyan);border-radius:0 10px 10px 0;padding:12px 16px;color:#67E8F9;margin:8px 0;}
.sxheader{background:linear-gradient(135deg,rgba(245,158,11,0.12),rgba(30,58,138,0.4));border:1px solid rgba(245,158,11,0.3);border-radius:20px;padding:28px 36px;margin-bottom:24px;text-align:center;backdrop-filter:blur(20px);}
.sxheader h1{color:white;font-size:2rem;font-weight:800;margin:0;font-family:'Space Grotesk',sans-serif;}
.sxheader .sub{color:var(--text-muted);font-size:0.9rem;margin-top:6px;}
.sxbadge{display:inline-block;background:rgba(245,158,11,0.2);color:var(--solar-gold);border:1px solid rgba(245,158,11,0.4);border-radius:100px;padding:3px 14px;font-size:0.72rem;font-weight:700;letter-spacing:0.1em;margin:8px 4px 0;}
.sxlabel{display:inline-block;background:linear-gradient(135deg,var(--solar-gold),#D97706);color:#0B1437;padding:5px 16px;border-radius:8px;font-size:0.75rem;font-weight:800;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:16px;}
.kpi-title{font-size:0.7rem;text-transform:uppercase;letter-spacing:0.12em;color:var(--text-muted);margin:0 0 10px 0;display:flex;align-items:center;gap:10px;}
.kpi-title::after{content:'';flex:1;height:1px;background:var(--glass-border);}
.live-badge{display:inline-block;background:rgba(16,185,129,0.2);color:#10B981;border:1px solid rgba(16,185,129,0.5);border-radius:100px;padding:2px 10px;font-size:0.7rem;font-weight:700;letter-spacing:0.08em;animation:blink 1.5s ease-in-out infinite;}
@keyframes blink{0%,100%{opacity:1}50%{opacity:0.5}}
@media(max-width:768px){.sxheader h1{font-size:1.3rem;}}
</style>
""", unsafe_allow_html=True)

# ─── DATABASES ───────────────────────────────────────────────────────────────
db = {
    "Afghanistan":[33.9,"AFN",5,12,"B","High","Import",5.2,98,220,50,45,"High"],
    "Albania":[41.1,"ALL",10,18,"B+","Medium","EU Import",4.1,100,230,50,25,"Low"],
    "Algeria":[28.0,"DZD",4,12,"B","Medium","Local",6.0,99,230,50,55,"Extreme"],
    "Argentina":[-38.4,"ARS",25,65,"B+","Medium","Local",5.1,100,220,50,70,"Extreme"],
    "Australia":[-25.2,"AUD",0.10,0.35,"A+","Very Low","AU Certified",5.8,100,230,50,85,"Extreme"],
    "Austria":[47.5,"EUR",0.15,0.45,"A+","Very Low","EU Certified",3.4,100,230,50,35,"Moderate"],
    "Bangladesh":[23.6,"BDT",7.5,14.0,"B","Medium","Local Assembly",4.6,99,220,50,90,"Extreme"],
    "Belgium":[50.5,"EUR",0.12,0.52,"A+","Very Low","EU Certified",2.9,100,230,50,40,"High"],
    "Brazil":[-14.2,"BRL",0.55,1.15,"A-","Low","Local Mfg",5.5,99,220,60,60,"Extreme"],
    "Canada":[56.1,"CAD",0.08,0.24,"A+","Very Low","US/CA Certified",3.7,100,120,60,80,"Extreme"],
    "Chile":[-35.6,"CLP",65,155,"A","Low","Local",6.2,100,220,50,75,"Extreme"],
    "China":[35.8,"CNY",0.42,0.72,"C+","High","Global Supply",4.3,100,220,50,50,"High"],
    "Colombia":[4.5,"COP",380,750,"B+","Medium","Import",4.5,99,110,60,30,"Moderate"],
    "Denmark":[56.2,"DKK",0.65,2.80,"A+","Very Low","EU Certified",2.7,100,230,50,90,"Extreme"],
    "Egypt":[26.8,"EGP",1.2,2.6,"B","Medium","Local Assembly",6.1,100,220,50,50,"High"],
    "France":[46.2,"EUR",0.15,0.34,"A+","Very Low","EU Certified",3.5,100,230,50,45,"High"],
    "Germany":[51.1,"EUR",0.12,0.48,"A+","Very Low","EU Certified",3.0,100,230,50,55,"Extreme"],
    "Greece":[39.0,"EUR",0.18,0.38,"A","Low","EU Import",4.5,100,230,50,65,"Extreme"],
    "India":[20.5,"INR",6.2,12.5,"A-","Low","Local Mfg",5.4,99,230,50,60,"Extreme"],
    "Indonesia":[-0.7,"IDR",1500,3400,"B","Medium","Local",4.8,99,220,50,50,"High"],
    "Iran":[32.4,"IRR",800,2000,"B","Medium","Local",5.6,100,220,50,70,"Extreme"],
    "Italy":[41.8,"EUR",0.20,0.50,"A","Low","EU Certified",4.2,100,230,50,50,"High"],
    "Japan":[36.2,"JPY",21,42,"A+","Very Low","JP Certified",3.8,100,100,50,110,"Extreme"],
    "Jordan":[30.5,"JOD",0.08,0.18,"B+","Medium","Local",5.8,100,230,50,60,"Extreme"],
    "Kenya":[-1.2,"KES",12,28,"B","Medium","Import",5.7,76,240,50,35,"Moderate"],
    "Malaysia":[4.2,"MYR",0.38,0.68,"A-","Low","Local Mfg",4.7,100,240,50,45,"High"],
    "Mexico":[23.6,"MXN",2.2,4.8,"B+","Medium","US Import",5.6,99,127,60,80,"Extreme"],
    "Morocco":[31.7,"MAD",1.1,2.2,"B+","Medium","Local",5.9,99,220,50,55,"Extreme"],
    "Netherlands":[52.1,"EUR",0.16,0.55,"A+","Very Low","EU Certified",2.8,100,230,50,85,"Extreme"],
    "New Zealand":[-40.9,"NZD",0.11,0.40,"A+","Very Low","AU/NZ",4.4,100,230,50,90,"Extreme"],
    "Nigeria":[9.0,"NGN",70,160,"C","High","Import",5.5,62,230,50,45,"High"],
    "Norway":[60.4,"NOK",0.9,2.8,"A+","Very Low","EU Certified",2.3,100,230,50,80,"Extreme"],
    "Oman":[21.5,"OMR",0.03,0.12,"A","Low","GCC",6.0,100,240,50,65,"Extreme"],
    "Pakistan":[30.3,"PKR",42.0,82.0,"B+","Medium","China Import",5.3,97,220,50,55,"Extreme"],
    "Philippines":[12.8,"PHP",6.2,14.0,"B","Medium","China Import",5.1,94,220,60,95,"Extreme"],
    "Poland":[51.9,"PLN",0.45,0.95,"A","Low","EU Certified",3.1,100,230,50,50,"High"],
    "Portugal":[39.3,"EUR",0.14,0.32,"A","Low","EU Certified",4.3,100,230,50,55,"Extreme"],
    "Qatar":[25.3,"QAR",0.15,0.38,"A","Low","GCC",5.9,100,240,50,60,"Extreme"],
    "Russia":[61.5,"RUB",3.5,6.2,"B","Medium","Local",3.2,100,220,50,70,"Extreme"],
    "Saudi Arabia":[23.8,"SAR",0.15,0.32,"A","Low","GCC Local",6.1,100,220,60,65,"Extreme"],
    "Singapore":[1.3,"SGD",0.28,0.45,"A+","Very Low","Import",4.6,100,230,50,40,"High"],
    "South Africa":[-30.5,"ZAR",1.9,3.8,"B+","Medium","Local",5.7,85,230,50,60,"Extreme"],
    "South Korea":[37.5,"KRW",95,180,"A+","Very Low","KR Certified",3.8,100,220,60,75,"Extreme"],
    "Spain":[40.4,"EUR",0.22,0.45,"A","Low","EU Certified",4.6,100,230,50,60,"Extreme"],
    "Sri Lanka":[7.8,"LKR",25,58,"B","Medium","India Import",5.2,99,230,50,80,"Extreme"],
    "Sweden":[60.1,"SEK",0.85,2.40,"A+","Very Low","EU Certified",2.6,100,230,50,75,"Extreme"],
    "Switzerland":[46.8,"CHF",0.20,0.45,"A+","Very Low","EU Certified",3.4,100,230,50,40,"High"],
    "Thailand":[15.8,"THB",2.8,6.0,"A-","Low","Local Mfg",5.0,100,220,50,60,"Extreme"],
    "Turkey":[38.9,"TRY",3.5,6.5,"B+","Medium","Local",4.9,100,230,50,50,"High"],
    "UAE":[23.4,"AED",0.22,0.48,"A","Low","GCC Local",5.9,100,220,50,65,"Extreme"],
    "UK":[55.3,"GBP",0.22,0.58,"A+","Very Low","UK/EU Certified",2.8,100,230,50,80,"Extreme"],
    "USA":[37.0,"USD",0.14,0.30,"A+","Very Low","US Certified",4.8,100,120,60,90,"Extreme"],
    "Vietnam":[14.0,"VND",2200,3800,"B+","Medium","Local Mfg",4.8,100,220,50,85,"Extreme"],
    "Zimbabwe":[-19.0,"USD",0.10,0.25,"C","High","Import",5.8,47,230,50,40,"High"],
}

panel_db = {
    "Jinko 545W Mono PERC":       [21.5,0.55,0.28,-0.35,49.8,13.8,"Tier-1 Standard"],
    "Trina 550W Mono PERC":       [21.8,0.58,0.29,-0.36,50.1,13.9,"Tier-1 Standard"],
    "LONGi 540W Hi-MO4":          [21.2,0.52,0.27,-0.35,49.5,13.7,"Tier-1 Standard"],
    "Jinko 580W TOPCon N-Type":   [23.5,0.65,0.32,-0.30,50.8,14.5,"Tier-1 High Eff"],
    "Trina 575W TOPCon":          [23.8,0.68,0.33,-0.29,51.0,14.6,"Tier-1 High Eff"],
    "LONGi 570W Hi-MO5":          [23.2,0.62,0.31,-0.31,50.5,14.3,"Tier-1 High Eff"],
    "JA Solar 575W DeepBlue 3.0": [23.6,0.66,0.32,-0.30,50.9,14.5,"Tier-1 High Eff"],
    "Risen 590W Hyper-ion":       [24.0,0.70,0.34,-0.29,51.2,14.7,"Tier-1 Premium"],
    "REC Alpha Pure 410W HJT":    [24.2,0.72,0.37,-0.24,51.3,14.9,"HJT Premium"],
    "Jinko 605W Bifacial TOPCon": [24.2,0.68,0.35,-0.29,51.0,14.6,"Bifacial Dual Glass"],
    "Trina 600W Vertex Bifacial": [24.0,0.65,0.34,-0.29,50.8,14.5,"Bifacial Dual Glass"],
    "SunPower 415W Maxeon 6 IBC": [25.2,0.85,0.42,-0.22,52.5,12.8,"IBC Premium"],
    "Aiko 625W ABC IBC":          [25.5,0.88,0.43,-0.21,52.8,13.0,"IBC Ultra Premium"],
    "First Solar 460W CdTe TF":   [18.5,0.35,0.22,-0.25,48.5,14.5,"Thin Film"],
    "QCells 415W Q.PEAK DUO":     [21.0,0.50,0.26,-0.35,49.2,13.5,"QCells Standard"],
    "QCells 480W Q.TRON":         [22.8,0.60,0.30,-0.32,50.3,14.2,"QCells Premium"],
}

battery_db = {
    "LiFePO4 LFP":   [94,6000,180,2.0,48,"Cobalt Free — Best Cycle Life"],
    "NMC Lithium":   [92,4000,220,2.5,48,"High Energy Density"],
    "Lead Acid AGM": [85,1200,120,5.0,24,"Low Cost, Heavy Weight"],
    "Sodium Ion":    [90,3000,150,3.0,48,"Emerging — Cobalt/Lithium Free"],
    "Solid State":   [96,8000,350,1.5,48,"Future Premium Technology"],
    "No Battery":    [0,0,0,0,0,"Grid-Tied System Only"],
}

inverter_db = {
    "String Inverter":  [97.5,1.00,800,"Central MPPT — Most Common"],
    "Micro Inverter":   [96.8,1.05,1200,"Panel-Level MPPT — Shade Tolerant"],
    "Hybrid Inverter":  [97.0,1.02,1500,"Battery + Grid — Best Flexibility"],
    "Power Optimizer":  [98.0,1.03,1400,"DC Optimizer — High Performance"],
    "Central Inverter": [98.5,0.98,600,"Large-Scale Commercial"],
}

structure_db = {
    "Low":      {"type":"Aluminum Fixed Tilt","tilt_max":30,"material":"Anodized AL-6005-T5","foundation":"Ground Screw","clamp":"Standard","yield_mpa":270,"E_gpa":70},
    "Moderate": {"type":"Galvanized Steel","tilt_max":25,"material":"Hot-Dip Galvanized Q235","foundation":"Concrete Ballast","clamp":"Reinforced","yield_mpa":235,"E_gpa":200},
    "High":     {"type":"Galvanized Steel + Bracing","tilt_max":20,"material":"Galvanized Steel + Cross Bracing","foundation":"Concrete Footing","clamp":"Heavy Duty","yield_mpa":355,"E_gpa":200},
    "Extreme":  {"type":"Steel + Wind Deflector","tilt_max":15,"material":"S355 Steel + Wind Deflector","foundation":"Deep Concrete Pile","clamp":"Hurricane Rated","yield_mpa":355,"E_gpa":200},
}

BATTERY_TYPES = {
    "Lithium-Ion":{"default_dod":90,"efficiency":95,"life_years":10},
    "Lead-Acid":  {"default_dod":50,"efficiency":80,"life_years":3},
    "Gel Battery":{"default_dod":70,"efficiency":85,"life_years":5},
}

# ─── WEATHER ──────────────────────────────────────────────────────────────────
@st.cache_data(ttl=86400)
def safe_geocode(country_name, c_lat_fallback):
    if not GEO_ENABLED:
        return c_lat_fallback, 70.0, country_name
    try:
        from geopy.geocoders import Nominatim
        geolocator = Nominatim(user_agent="solarx_pro_v41", timeout=5)
        location = geolocator.geocode(country_name)
        if location:
            return location.latitude, location.longitude, location.address.split(',')[0]
    except Exception:
        pass
    return c_lat_fallback, 70.0, country_name

@st.cache_data(ttl=1800)
def fetch_live_weather(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude":lat,"longitude":lon,
        "hourly":"temperature_2m,wind_speed_10m,cloud_cover,shortwave_radiation",
        "daily":"shortwave_radiation_sum,wind_speed_10m_max,temperature_2m_max,temperature_2m_min",
        "timezone":"auto","forecast_days":7,
        "current":"temperature_2m,wind_speed_10m,cloud_cover,shortwave_radiation"
    }
    try:
        res = requests.get(url, params=params, timeout=12)
        if res.status_code == 200:
            data = res.json()
            h = data.get("hourly",{})
            d = data.get("daily",{})
            c = data.get("current",{})
            hourly_df = pd.DataFrame({
                "Timestamp":pd.to_datetime(h.get("time",[])),
                "Temperature":h.get("temperature_2m",[]),
                "Wind_Speed":h.get("wind_speed_10m",[]),
                "Cloud_Cover":h.get("cloud_cover",[]),
                "GHI_W":h.get("shortwave_radiation",[]),
            })
            hourly_df["Hour"] = hourly_df["Timestamp"].dt.hour
            today_df = hourly_df[hourly_df["Timestamp"].dt.date == hourly_df["Timestamp"].dt.date.iloc[0]].copy()
            daily_df = pd.DataFrame({
                "Date":pd.to_datetime(d.get("time",[])),
                "GHI_sum":d.get("shortwave_radiation_sum",[]),
                "Wind_max":d.get("wind_speed_10m_max",[]),
                "Temp_max":d.get("temperature_2m_max",[]),
                "Temp_min":d.get("temperature_2m_min",[]),
            })
            avg_ghi_live = float(np.mean([x for x in d.get("shortwave_radiation_sum",[0.0]) if x]))/1000.0 if d.get("shortwave_radiation_sum") else None
            avg_temp_live = float(np.mean([x for x in h.get("temperature_2m",[25.0]) if x is not None]))
            avg_wind_live = float(np.mean([x for x in h.get("wind_speed_10m",[30.0]) if x is not None]))
            avg_cloud_live = float(np.mean([x for x in h.get("cloud_cover",[20.0]) if x is not None]))
            current_vals = {
                "temp":c.get("temperature_2m",avg_temp_live),
                "wind":c.get("wind_speed_10m",avg_wind_live),
                "cloud":c.get("cloud_cover",avg_cloud_live),
                "ghi":c.get("shortwave_radiation",0.0),
            }
            return {
                "hourly":hourly_df,"today":today_df,"daily":daily_df,"current":current_vals,
                "avg_ghi":avg_ghi_live,"avg_temp":avg_temp_live,"avg_wind":avg_wind_live,
                "avg_cloud":avg_cloud_live,"success":True,
            }
    except Exception:
        pass
    return {"success":False}

def get_weather_params(lat, lon, db_ghi, db_wind, db_temp, use_live):
    if use_live:
        wd = fetch_live_weather(lat, lon)
        if wd.get("success"):
            return {
                "ghi":wd["avg_ghi"] if wd["avg_ghi"] else db_ghi,
                "wind":wd["avg_wind"],"temp":wd["avg_temp"],"cloud":wd["avg_cloud"],
                "live":True,"data":wd,
            }
    return {"ghi":db_ghi,"wind":db_wind,"temp":db_temp,"cloud":20.0,"live":False,"data":None}

# ─── ENGINEERING ──────────────────────────────────────────────────────────────
def calc_wind_load(wind_speed_kmh, tilt_angle, panel_qty, panel_area_m2=2.1):
    wind_ms = wind_speed_kmh / 3.6
    q = 0.613 * wind_ms**2
    cp = 1.3 if tilt_angle > 30 else (1.0 if tilt_angle > 15 else 0.8)
    return q * cp * panel_area_m2 * panel_qty / 1000.0

def calc_fea_stress(wind_speed_kmh, tilt_angle, panel_qty, struct, has_truss=False):
    wind_ms = wind_speed_kmh / 3.6
    q = 0.613 * wind_ms**2
    cp = 1.3 if tilt_angle > 30 else (1.0 if tilt_angle > 15 else 0.8)
    f_panel = q * cp * 2.1
    f_total = f_panel * panel_qty
    moment = f_total * 0.9
    Z_rail = (60*60**2 - 54*54**2) / 6.0 / 1e6
    sigma_bending = moment / max(Z_rail, 1e-9) / 1e6
    uplift = f_total * np.sin(np.radians(tilt_angle))
    post_area = 4e-4
    sigma_axial = uplift / post_area / 1e6
    # Truss reduces effective bending by redistributing load
    truss_factor = 0.60 if has_truss else 1.0
    sigma_bending *= truss_factor
    von_mises = np.sqrt(sigma_bending**2 + sigma_axial**2)
    yield_mpa = struct.get("yield_mpa", 235)
    safety_factor = yield_mpa / max(von_mises, 0.001)
    return {
        "von_mises":round(von_mises,2),"bending":round(sigma_bending,2),
        "axial":round(sigma_axial,2),"yield":yield_mpa,
        "sf":round(safety_factor,2),"fail":von_mises>=yield_mpa,
        "truss_active":has_truss,
    }

def calc_lightning_protection(building_height):
    if building_height > 20:
        return building_height+2, 20
    return building_height+1.5, 30

def model_solar_physics(temp, wind_ms, cloud, hour, cfg):
    if 6 <= hour <= 18:
        amplitude = 1050.0
        base_ghi = amplitude * np.sin(np.pi*(hour-6)/12)
        tilt_factor = np.cos(np.radians(cfg["tilt"]-25))
        azimuth_factor = np.cos(np.radians(cfg["azimuth"]-180))
        effective_ghi = base_ghi * max(0.4, tilt_factor*azimuth_factor)
    else:
        return {"Power_kW":0.0,"Cell_Temp":temp,"Irradiance":0.0}
    attenuation = (cloud/100.0)*0.82
    incident_irr = effective_ghi*(1.0-attenuation)
    cooling_index = 1.0+(wind_ms*0.035)
    cell_temp = temp+((45.0-20.0)*(incident_irr/800.0)/cooling_index)
    thermal_loss = 1.0-max(0,(cell_temp-25.0)*abs(cfg["temp_coef"])) if cell_temp>25 else 1.0
    total_age_loss = cfg["system_age"]*(cfg["annual_degrad"]/100.0)
    retained_eff = max(0.5,1.0-total_age_loss)
    field_peak_kw = (cfg["panel_w"]*cfg["panel_count"])/1000.0
    net_kw = (field_peak_kw*(incident_irr/1000.0)*thermal_loss
              *(cfg["inverter_eff"]/100.0)*(1.0-cfg["soiling"]/100.0)*retained_eff)
    return {"Power_kW":max(0.0,round(net_kw,3)),"Cell_Temp":round(cell_temp,2),"Irradiance":round(incident_irr,2)}

def compute_financial(daily_gen_kwh, daily_load_kwh, cfg):
    imp = cfg["tariff_import"]
    exp = cfg["tariff_export"]
    if daily_gen_kwh >= daily_load_kwh:
        surplus = daily_gen_kwh - daily_load_kwh
        credit = surplus * exp
        net_benefit = daily_load_kwh * imp + credit
        bill = 0.0
    else:
        deficit = daily_load_kwh - daily_gen_kwh
        bill = deficit * imp
        credit = 0.0
        net_benefit = daily_gen_kwh * imp
    capex = cfg["panel_count"] * cfg["cost_per_panel"]
    annual = net_benefit * 365.25
    payback = capex / annual if annual > 0 else 99.0
    return {
        "Daily_Savings":round(net_benefit,2),"Daily_Bill":round(bill,2),
        "Export_Credit":round(credit,2),"Payback_Years":round(payback,2),"CapEx":capex,
    }

def generate_pdf_report(data_dict):
    if not PDF_ENABLED:
        return None
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial','B',18)
        pdf.cell(0,12,'SolarX Pro -- Solar Analysis Report',0,1,'C')
        pdf.set_font('Arial','',11)
        pdf.cell(0,8,f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}',0,1,'C')
        pdf.ln(8)
        pdf.set_font('Arial','B',14)
        pdf.cell(0,10,'SYSTEM CONFIGURATION',0,1)
        pdf.set_font('Arial','',11)
        for k,v in data_dict.items():
            line = f'{str(k)}: {str(v)}'
            pdf.cell(0,7,line.encode('ascii','ignore').decode('ascii'),0,1)
        raw = pdf.output(dest='S')
        if isinstance(raw,str):
            raw = raw.encode('latin-1','replace')
        return raw
    except Exception:
        return None

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center;padding:12px 0 8px'>
      <span style='font-size:2rem'>☀️</span>
      <div style='color:#F59E0B;font-weight:800;font-size:1.05rem;font-family:Space Grotesk,sans-serif'>SolarX Professional</div>
      <div style='color:#64748B;font-size:0.72rem;letter-spacing:0.08em;text-transform:uppercase'>Enterprise Edition v4.1</div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()
    country = st.selectbox("🌍 Country", sorted(db.keys()), key="country_select_main")
    cd = db[country]
    c_lat,c_curr,c_sale,c_buy = cd[0],cd[1],cd[2],cd[3]
    esg_rating,labor_risk,sourcing = cd[4],cd[5],cd[6]
    avg_ghi_db,elec_access,grid_v,grid_f = cd[7],cd[8],cd[9],cd[10]
    wind_kmh_db,wind_zone = cd[11],cd[12]
    st.divider()
    st.markdown("### ⚡ Panel Config")
    panel_type = st.selectbox("Panel Model", list(panel_db.keys()))
    p_eff,p_cost,voc,p_temp,voc_std,isc,p_note = panel_db[panel_type]
    p_qty = st.number_input("Number of Panels", min_value=1, max_value=50000, value=22)
    st.divider()
    st.markdown("### 🔄 Inverter")
    inverter_type = st.selectbox("Inverter Type", list(inverter_db.keys()))
    inv_eff,inv_bonus,inv_cost,inv_note = inverter_db[inverter_type]
    st.divider()
    st.markdown("### 📐 Orientation")
    tilt = st.slider("Panel Tilt °", 0, 60, 25)
    azimuth = st.slider("Azimuth °", -180, 180, 180)
    st.divider()
    st.markdown("### 🏗️ Site")
    building_height = st.number_input("Building Height (m)", 3.0, 50.0, 6.0)
    wire_length = st.number_input("DC Cable Length (m)", 10, 200, 50)
    cable_size = st.selectbox("DC Cable Size (mm²)", [4,6,10,16,25])
    st.divider()
    st.markdown("### 🛰️ Live Weather")
    live_weather_toggle = st.toggle("🔴 Live Weather API", value=False)
    if live_weather_toggle:
        st.markdown("<span class='live-badge'>● LIVE TELEMETRY</span>", unsafe_allow_html=True)
    st.divider()
    st.markdown("""
    <div style='color:#475569;font-size:0.7rem;text-align:center;padding:8px 0'>
      © 2025 SolarX Professional<br>Enterprise Solar Estimation Platform
    </div>
    """, unsafe_allow_html=True)

# ─── EXPANDERS ────────────────────────────────────────────────────────────────
col1,col2,col3 = st.columns(3)
with col1:
    with st.expander("🔋 Battery & Load Config", expanded=False):
        battery_type = st.selectbox("Battery Chemistry", list(battery_db.keys()))
        b_eff,b_cycles,b_cost_kwh,b_degrade,b_voltage,b_note = battery_db[battery_type]
        has_batt = battery_type != "No Battery"
        b_cap = st.number_input("Battery Capacity (kWh)", value=20.0) if has_batt else 0.0
        dod = st.slider("Depth of Discharge %", 50, 95, 85) if has_batt else 0
        h_load = st.number_input("Daily Energy Load (kWh)", value=55.0)
        net_metering = st.checkbox("Net Metering Enabled", value=True)
with col2:
    with st.expander("🔬 Advanced Physics", expanded=False):
        panel_w_adv = st.number_input("Unit Panel Power (W)", 200, 700, int(p_eff*25), 5)
        system_age = st.slider("System Age (Years)", 0, 25, 1)
        annual_degrad = st.number_input("Annual Degradation %", 0.1, 2.0, 0.5, 0.1)
        soiling_adv = st.slider("Soiling Loss %", 0.0, 20.0, 3.5, 0.5)
with col3:
    with st.expander("🌤️ Climate & Environment", expanded=False):
        sun_h_override = st.slider("Peak Sun Hours/day", 3.0, 8.5, float(avg_ghi_db))
        sys_loss = st.slider("System Losses %", 8, 30, 14)
        soiling = st.slider("Soiling %", 0, 20, 5)
        temp_ambient_override = st.slider("Ambient Temp °C", 15, 50, 28)

with st.expander("💰 Financial & Tariff", expanded=False):
    fc1,fc2,fc3,fc4 = st.columns(4)
    with fc1:
        buy_rate = st.number_input(f"Buy Rate ({c_curr}/kWh)", value=float(c_buy))
        sell_rate = st.number_input(f"Sell Rate ({c_curr}/kWh)", value=float(c_sale))
    with fc2:
        tax_val = st.slider("Tax %", 0, 30, 17)
        discount_rate = st.slider("Discount Rate %", 3, 15, 8)
    with fc3:
        install_cost = st.number_input(f"Install Cost/kWp ({c_curr})", value=42000.0 if country=="Pakistan" else 750.0)
        cost_per_panel_adv = st.number_input("Cost per Panel (installed)", 10.0, 10000.0, 250.0, 10.0)
    with fc4:
        subsidy_pct = st.slider("Government Subsidy %", 0, 50, 30 if country=="Pakistan" else 0)
        inflation = st.slider("Tariff Inflation %/yr", 0.0, 15.0, 3.0, 0.5)

# ─── WEATHER RESOLUTION ──────────────────────────────────────────────────────
lat,lon,location_name = safe_geocode(country,c_lat)
weather = get_weather_params(lat,lon,avg_ghi_db,wind_kmh_db,temp_ambient_override,live_weather_toggle)

effective_ghi = weather["ghi"] if weather["ghi"] else sun_h_override
effective_wind = weather["wind"]
effective_temp = weather["avg_temp"] if weather["live"] else temp_ambient_override
effective_cloud = weather["avg_cloud"] if weather["live"] else 20.0

if weather["live"]:
    effective_wind_kmh = effective_wind
else:
    effective_wind_kmh = wind_kmh_db

sun_h = float(effective_ghi) if effective_ghi else sun_h_override
wind = float(effective_wind_kmh)
temp_ambient = float(effective_temp)
cloud_pct = float(effective_cloud)

# ─── CALCULATIONS ─────────────────────────────────────────────────────────────
sys_size = (p_eff*p_qty*100)/1000.0
panels_per_string = max(1,int(1000/max(voc_std,1)))
strings = math.ceil(p_qty/panels_per_string)
voc_string = voc_std*panels_per_string
isc_string = isc*strings
mppt_voltage = voc_string*0.8

wind_force = calc_wind_load(wind,tilt,p_qty)
struct = structure_db[wind_zone]

# Truss toggle stored in session for FEA tab
if "truss_enabled" not in st.session_state:
    st.session_state["truss_enabled"] = False

fea_result = calc_fea_stress(wind,tilt,p_qty,struct,st.session_state["truss_enabled"])
wind_safe = not fea_result["fail"]
rod_height,protection_radius = calc_lightning_protection(building_height)

current_dc = (sys_size*1000)/400.0
voltage_drop = (current_dc*wire_length*0.0175)/cable_size
vd_percent = (voltage_drop/mppt_voltage)*100 if mppt_voltage>0 else 0

hours_arr = np.arange(24)
angle_eff = np.cos(np.radians(tilt-abs(c_lat)))*np.cos(np.radians(azimuth))
temp_loss = 1+(p_temp/100)*(temp_ambient+25-25)
soiling_loss = 1-soiling/100
weather_factor = 1-cloud_pct*0.008+wind*0.0003

daily_yield = (sys_size*sun_h*((100-sys_loss)/100)
               *max(0.3,angle_eff)*(p_eff/21.5)*temp_loss
               *soiling_loss*(inv_eff/100)*inv_bonus*weather_factor)

if weather["live"] and weather["data"] and weather["data"].get("today") is not None:
    today_df = weather["data"]["today"]
    if len(today_df) >= 24:
        live_ghi_24 = today_df["GHI_W"].values[:24]
        live_temp_24 = today_df["Temperature"].values[:24]
        live_wind_24 = today_df["Wind_Speed"].values[:24]
        gen_24 = []
        for h_idx in range(24):
            irr = float(live_ghi_24[h_idx]) if h_idx < len(live_ghi_24) else 0.0
            t = float(live_temp_24[h_idx]) if h_idx < len(live_temp_24) else temp_ambient
            w = float(live_wind_24[h_idx]) if h_idx < len(live_wind_24) else wind/3.6
            if irr <= 0:
                gen_24.append(0.0)
                continue
            cell_t = t+(45-20)*(irr/800)/(1+w*0.035)
            th_loss = max(0,1-(cell_t-25)*abs(p_temp/100))
            kw = sys_size*(irr/1000)*th_loss*(inv_eff/100)*(1-soiling/100)
            gen_24.append(max(0,kw))
    else:
        gen_24 = [max(0,daily_yield/12*np.sin(np.pi*(h-6)/12)) if 6<=h<=18 else 0 for h in hours_arr]
else:
    gen_24 = [max(0,daily_yield/12*np.sin(np.pi*(h-6)/12)) if 6<=h<=18 else 0 for h in hours_arr]

load_24 = [(h_load/24)*(2.8 if (h>18 or h<7) else 0.7) for h in hours_arr]

soc = []
c_soc = b_cap*(dod/100) if has_batt else 0.0
for g,l in zip(gen_24,load_24):
    if has_batt:
        diff = g-l
        c_soc = max(0,min(b_cap,c_soc+diff*(b_eff/100)))
    soc.append(c_soc)

export_24 = [max(0,g-l-(soc[i]-soc[i-1] if i>0 else 0)) for i,(g,l) in enumerate(zip(gen_24,load_24))]
import_24 = [max(0,l-g-(soc[i-1]-soc[i] if i>0 else 0)) for i,(g,l) in enumerate(zip(gen_24,load_24))]

battery_cost = b_cap*b_cost_kwh if has_batt else 0.0
panel_cost = sys_size*1000*p_cost
inverter_cost = sys_size*inv_cost
structure_cost = sys_size*150
cable_cost = wire_length*cable_size*2.5
lightning_cost = rod_height*80
gross_cost = (panel_cost+battery_cost+inverter_cost+structure_cost+cable_cost+lightning_cost+sys_size*install_cost)
net_cost = gross_cost*(1-subsidy_pct/100)

years_arr = np.arange(25)
yearly_gen = [sum(gen_24)*365*(1-b_degrade/100)**y for y in years_arr]
gen_ratio = sum(export_24)/sum(gen_24) if sum(gen_24)>0 else 0
yearly_profit = []
for i,yg in enumerate(yearly_gen):
    ti = buy_rate*((1+inflation/100)**i)
    te = sell_rate*((1+inflation/100)**i)
    profit = yg*((1-gen_ratio)*ti+gen_ratio*te)*(1-tax_val/100)
    yearly_profit.append(profit)

payback = net_cost/yearly_profit[0] if yearly_profit[0]>0 else 99.0
npv = sum([p/((1+discount_rate/100)**i) for i,p in enumerate(yearly_profit)])-net_cost

adv_cfg = {
    "panel_type":"Monocrystalline","panel_w":panel_w_adv,"panel_count":p_qty,
    "cost_per_panel":cost_per_panel_adv,"temp_coef":p_temp/100,
    "tilt":tilt,"azimuth":azimuth,"system_age":system_age,"annual_degrad":annual_degrad,
    "inverter_eff":inv_eff,"soiling":soiling_adv,"tariff_import":buy_rate,"tariff_export":sell_rate,
    "battery_ah":int(b_cap*1000/max(b_voltage,1)) if has_batt else 200,
    "battery_v":b_voltage if has_batt else 48,
}

fin_report = compute_financial(sum(gen_24),h_load,adv_cfg)
usable_battery_kwh = b_cap*(dod/100) if has_batt else 0.0
hours_of_autonomy = usable_battery_kwh/(h_load/24) if h_load>0 else 0.0
pr = (sum(gen_24)/(sys_size*sun_h))*100 if sys_size*sun_h>0 else 0
co2_annual = sum(gen_24)*365*0.82/1000

# ─── PAGE HEADER ──────────────────────────────────────────────────────────────
anim_cols_count = min(p_qty,12)
anim_rows_count = math.ceil(p_qty/anim_cols_count)

live_badge = "<span class='live-badge'>● LIVE WEATHER</span>" if weather["live"] else ""
st.markdown(f"""
<div class='sxheader'>
  <h1>☀️ SolarX Professional — {country} {live_badge}</h1>
  <div class='sub'>📍 {location_name} &nbsp;·&nbsp; {sys_size:.2f} kWp System &nbsp;·&nbsp; {p_qty} × {panel_type.split()[0]} Panels</div>
  <div>
    <span class='sxbadge'>ENTERPRISE v4.1</span>
    <span class='sxbadge'>ESG {esg_rating}</span>
    <span class='sxbadge'>{grid_v}V {grid_f}Hz</span>
    <span class='sxbadge'>Wind Zone: {wind_zone}</span>
    <span class='sxbadge'>GHI: {sun_h:.2f} kWh/m²/d</span>
    <span class='sxbadge'>Wind: {wind:.0f} km/h</span>
    <span class='sxbadge'>Temp: {temp_ambient:.0f}°C</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ─── KPIs ─────────────────────────────────────────────────────────────────────
st.markdown("<p class='kpi-title'>System Performance KPIs</p>", unsafe_allow_html=True)
k = st.columns(5)
k[0].metric("⚡ System Size",f"{sys_size:.2f} kWp",f"{p_qty} panels")
k[1].metric("☀️ Daily Output",f"{sum(gen_24):.1f} kWh",f"PR: {pr:.0f}%")
k[2].metric("📈 Annual Yield",f"{sum(gen_24)*365:.0f} kWh",f"GHI: {sun_h:.1f}")
k[3].metric("🌿 CO₂ Avoided",f"{co2_annual:.1f} T/yr",f"{int(co2_annual*18)} trees/yr")
k[4].metric("💰 Daily Savings",f"{fin_report['Daily_Savings']:,.1f} {c_curr}",f"Ex: {sum(export_24):.1f} kWh")

st.markdown("<p class='kpi-title' style='margin-top:18px'>Financial & Structural KPIs</p>", unsafe_allow_html=True)
k2 = st.columns(6)
k2[0].metric("💵 Net CapEx",f"{net_cost:,.0f} {c_curr}",f"-{subsidy_pct}% subsidy")
k2[1].metric("⏱️ Payback",f"{payback:.1f} yrs",f"NPV: {npv:,.0f}")
k2[2].metric("🔌 VOC String",f"{voc_string:.0f} V",f"ISC: {isc_string:.1f} A")
k2[3].metric("📉 Voltage Drop",f"{vd_percent:.2f}%","⚠️ High" if vd_percent>3 else "✅ OK")
k2[4].metric("💨 Wind Risk",wind_zone,f"{wind:.0f} km/h",delta_color="inverse" if wind_zone in ["Extreme","High"] else "normal")
k2[5].metric("🔩 FEA Stress",f"{fea_result['von_mises']:.1f} MPa",f"SF: {fea_result['sf']:.2f}",delta_color="inverse" if fea_result["fail"] else "normal")

st.divider()

# ─── TABS ─────────────────────────────────────────────────────────────────────
tabs = st.tabs([
    "📊 Energy Profile","🏗️ 3D Animator","💨 Wind FEA Sim",
    "🔧 Tech Specs","🔌 Inverter","🔋 Battery",
    "⚡ Electrical","💰 Financial","🌿 Eco & Carbon",
    "🛡️ ESG","📡 Net Metering","🤖 AI Diagnosis",
    "📈 Physics Engine","📦 Storage Matrix","📄 Export",
])

# ── TAB 0: Energy Profile ──────────────────────────────────────────────────────
with tabs[0]:
    st.markdown("<span class='sxlabel'>24-Hour Energy Profile</span>", unsafe_allow_html=True)
    if weather["live"]:
        st.markdown(f"<div class='sx-ok'>🛰️ <strong>Live Weather Active</strong> — Real irradiance data for {country}. Wind: {wind:.0f} km/h · Temp: {temp_ambient:.1f}°C · Cloud: {cloud_pct:.0f}%</div>", unsafe_allow_html=True)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(hours_arr),y=gen_24,name="☀️ Solar Generation",
        fill='tozeroy',fillcolor='rgba(245,158,11,0.15)',
        line=dict(color='#F59E0B',width=3),
        hovertemplate='%{y:.2f} kW<extra>Generation</extra>'))
    fig.add_trace(go.Scatter(x=list(hours_arr),y=load_24,name="⚡ Load Demand",
        line=dict(color='#EF4444',width=2.5,dash='dot'),
        hovertemplate='%{y:.2f} kW<extra>Load</extra>'))
    if has_batt:
        fig.add_trace(go.Scatter(x=list(hours_arr),y=soc,name="🔋 Battery SOC",
            line=dict(color='#10B981',width=2.5),
            hovertemplate='%{y:.2f} kWh<extra>Battery SOC</extra>'))
    fig.add_trace(go.Bar(x=list(hours_arr),y=export_24,name="↑ Export",marker_color='rgba(6,182,212,0.5)'))
    fig.add_trace(go.Bar(x=list(hours_arr),y=import_24,name="↓ Import",marker_color='rgba(239,68,68,0.35)'))
    fig.update_layout(
        height=480,barmode='overlay',
        plot_bgcolor='rgba(11,20,55,0.6)',paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#94A3B8',family='Inter'),
        title=dict(text="Hourly Solar Generation vs Load Demand",font=dict(color='#F1F5F9',size=14)),
        legend=dict(bgcolor='rgba(15,32,87,0.7)',bordercolor='rgba(255,255,255,0.1)',borderwidth=1),
        xaxis=dict(title="Hour of Day",gridcolor='rgba(255,255,255,0.06)',tickmode='linear',dtick=2),
        yaxis=dict(title="Power (kW) / Energy (kWh)",gridcolor='rgba(255,255,255,0.06)'),
        hovermode='x unified',
    )
    st.plotly_chart(fig, use_container_width=True)
    ea,eb,ec,ed = st.columns(4)
    ea.metric("Peak Generation",f"{max(gen_24):.2f} kW","solar noon")
    eb.metric("Peak Load",f"{max(load_24):.2f} kW","evening peak")
    ec.metric("Self-Consumption",f"{(1-sum(import_24)/max(h_load,1))*100:.1f}%","grid independence")
    ed.metric("Net Export",f"{sum(export_24)-sum(import_24):.1f} kWh/day")

    if weather["live"] and weather["data"] and weather["data"].get("daily") is not None:
        st.divider()
        st.markdown("<span class='sxlabel'>7-Day Weather Forecast</span>", unsafe_allow_html=True)
        daily_df_w = weather["data"]["daily"]
        if len(daily_df_w) > 0:
            fig7 = make_subplots(rows=2,cols=1,shared_xaxes=True,vertical_spacing=0.1,
                                 subplot_titles=("Daily GHI (kWh/m²)","Temperature & Wind"))
            fig7.add_trace(go.Bar(x=daily_df_w["Date"].astype(str),y=daily_df_w["GHI_sum"],
                                  name="GHI kWh/m²",marker_color='rgba(245,158,11,0.7)'),row=1,col=1)
            fig7.add_trace(go.Scatter(x=daily_df_w["Date"].astype(str),y=daily_df_w["Temp_max"],
                                      name="Max Temp °C",line=dict(color='#EF4444',width=2)),row=2,col=1)
            fig7.add_trace(go.Scatter(x=daily_df_w["Date"].astype(str),y=daily_df_w["Wind_max"],
                                      name="Max Wind km/h",line=dict(color='#06B6D4',width=2)),row=2,col=1)
            fig7.update_layout(height=380,plot_bgcolor='rgba(11,20,55,0.6)',paper_bgcolor='rgba(0,0,0,0)',
                                font=dict(color='#94A3B8'),legend=dict(bgcolor='rgba(0,0,0,0)'))
            st.plotly_chart(fig7, use_container_width=True)

# ── TAB 1: 3D Panel Animator ──────────────────────────────────────────────────
with tabs[1]:
    st.markdown("<span class='sxlabel'>3D SolidWorks-Style Panel Array Animator</span>", unsafe_allow_html=True)
    st.markdown("<div class='sx-info'>ℹ️ Full 3D isometric animation with structural steel, mounting rails, bolt nodes, sun arc, volumetric light beams and live irradiance colour mapping. Canvas 2.5D WebGL-class engine.</div>", unsafe_allow_html=True)

    gen_24_js = json.dumps([round(x,3) for x in gen_24])
    live_mode_js = "true" if weather["live"] else "false"

    # Build JS strings with pre-computed Python values to avoid f-string/template literal conflicts
    wind_val = f"{wind:.1f}"
    temp_val = f"{temp_ambient:.1f}"
    sys_kwp_val = f"{sys_size:.4f}"
    tilt_val = str(tilt)
    p_qty_val = str(p_qty)
    rows_val = str(anim_rows_count)
    cols_val = str(anim_cols_count)
    strings_val = str(strings)
    voc_str_val = f"{voc_string:.0f}"
    isc_str_val = f"{isc_string:.1f}"
    p_temp_val = f"{abs(p_temp)}"

    html_3d = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{background:#030C1E;overflow:hidden;font-family:'Segoe UI',sans-serif;}
canvas{display:block;}
#hud{
  position:absolute;top:0;left:0;right:0;
  display:flex;gap:0;background:rgba(5,14,37,0.88);
  border-bottom:1px solid rgba(245,158,11,0.25);
  padding:7px 16px;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;
}
.hc{display:flex;flex-direction:column;align-items:center;min-width:80px;}
.hl{color:#4A6FA5;font-size:9px;letter-spacing:0.1em;text-transform:uppercase;}
.hv{color:#F59E0B;font-size:13px;font-weight:700;font-family:'Courier New',monospace;}
.hg{color:#10B981;}.hb{color:#06B6D4;}.hr{color:#EF4444;}
#bot{
  position:absolute;bottom:0;left:0;right:0;
  background:rgba(5,14,37,0.88);border-top:1px solid rgba(245,158,11,0.2);
  padding:6px 16px;display:flex;gap:20px;align-items:center;flex-wrap:wrap;
}
.bi{color:#64748B;font-size:10px;}.bi span{color:#94A3B8;font-weight:600;}
#ibar{flex:1;height:5px;background:#0F2057;border-radius:3px;overflow:hidden;min-width:60px;}
#ifill{height:100%;width:0%;background:linear-gradient(90deg,#1D4ED8,#F59E0B);transition:width 0.4s;border-radius:3px;}
#leg{
  position:absolute;right:10px;top:60px;
  background:rgba(5,14,37,0.82);border:1px solid rgba(245,158,11,0.2);
  border-radius:10px;padding:10px 14px;font-size:10px;color:#94A3B8;
}
.lr{display:flex;align-items:center;gap:7px;margin:3px 0;}
.ls{width:14px;height:14px;border-radius:3px;}
</style>
</head>
<body>
<canvas id="c"></canvas>
<div id="hud">
  <div class="hc"><div class="hl">Sim Time</div><div class="hv" id="hTime">06:00</div></div>
  <div class="hc"><div class="hl">Irradiance</div><div class="hv" id="hIrr">0 W/m2</div></div>
  <div class="hc"><div class="hl">Array Output</div><div class="hv hg" id="hPow">0.00 kW</div></div>
  <div class="hc"><div class="hl">Cell Temp</div><div class="hv hr" id="hTemp">--C</div></div>
  <div class="hc"><div class="hl">Wind</div><div class="hv hb">""" + wind_val + """ km/h</div></div>
  <div class="hc"><div class="hl">Panels</div><div class="hv">""" + p_qty_val + """</div></div>
  <div class="hc"><div class="hl">Sys kWp</div><div class="hv">""" + sys_kwp_val[:5] + """</div></div>
  <div class="hc"><div class="hl">Tilt</div><div class="hv">""" + tilt_val + """deg</div></div>
</div>
<div id="leg">
  <div style="font-size:9px;color:#F59E0B;font-weight:700;margin-bottom:6px;letter-spacing:0.1em">LEGEND</div>
  <div class="lr"><div class="ls" style="background:#1E3A8A"></div>Night/Low irr</div>
  <div class="lr"><div class="ls" style="background:#0891B2"></div>Morning ramp</div>
  <div class="lr"><div class="ls" style="background:#F59E0B"></div>Peak solar noon</div>
  <div class="lr"><div class="ls" style="background:#78716C"></div>Steel structure</div>
  <div class="lr"><div class="ls" style="background:rgba(6,182,212,0.6)"></div>Wind vectors</div>
  <div class="lr"><div class="ls" style="background:rgba(245,158,11,0.4)"></div>Light beams</div>
</div>
<div id="bot">
  <div class="bi">Rows: <span>""" + rows_val + """</span></div>
  <div class="bi">Cols: <span>""" + cols_val + """</span></div>
  <div class="bi">Strings: <span>""" + strings_val + """</span></div>
  <div class="bi">VOC: <span>""" + voc_str_val + """V</span></div>
  <div id="ibar"><div id="ifill"></div></div>
  <div class="bi">Irradiance to Peak</div>
</div>
<script>
var canvas=document.getElementById('c');
var ctx=canvas.getContext('2d');
var ROWS=""" + rows_val + """;
var COLS=""" + cols_val + """;
var N_PANELS=""" + p_qty_val + """;
var TILT=""" + tilt_val + """;
var SYS_KWP=""" + sys_kwp_val + """;
var AMB_T=""" + temp_val + """;
var WIND_KMH=""" + wind_val + """;
var GEN_24=""" + gen_24_js + """;
var TEMP_COEF=""" + p_temp_val + """;
var W,H;
function resize(){W=canvas.width=window.innerWidth;H=canvas.height=window.innerHeight-52;canvas.style.marginTop='52px';}
resize();window.addEventListener('resize',resize);
var ISO=Math.PI/6;
var SCALE=Math.min(800,600)*0.022;
var TILT_RAD=(TILT*Math.PI)/180;
var PW=1.0,PH=1.7,PG=0.18;
function iso(wx,wy,wz){
  var sx=W/2+(wx-wy)*Math.cos(ISO)*SCALE;
  var sy=H/2-wz*SCALE+(wx+wy)*Math.sin(ISO)*SCALE*0.55;
  return [sx,sy];
}
function lerp(a,b,t){return a+(b-a)*t;}
function lerpRGB(r1,g1,b1,r2,g2,b2,t){
  return [Math.round(lerp(r1,r2,t)),Math.round(lerp(g1,g2,t)),Math.round(lerp(b1,b2,t))];
}
function panelColor(irrFrac){
  var r,g,b;
  if(irrFrac<0.5){var t=irrFrac*2;var c=lerpRGB(10,24,66,6,122,196,t);r=c[0];g=c[1];b=c[2];}
  else{var t=(irrFrac-0.5)*2;var c=lerpRGB(6,122,196,245,158,11,t);r=c[0];g=c[1];b=c[2];}
  return 'rgb('+r+','+g+','+b+')';
}
function steelColor(face){
  if(face==='top') return '#78818C';
  if(face==='front') return '#5C6370';
  return '#3D4249';
}
function drawBox(x,y,z,dx,dy,dz,ct,cf,cr){
  var p0=iso(x,y,z),p1=iso(x+dx,y,z),p2=iso(x+dx,y+dy,z),p3=iso(x,y+dy,z);
  var p4=iso(x,y,z+dz),p5=iso(x+dx,y,z+dz),p6=iso(x+dx,y+dy,z+dz),p7=iso(x,y+dy,z+dz);
  ctx.beginPath();ctx.moveTo(p4[0],p4[1]);ctx.lineTo(p5[0],p5[1]);ctx.lineTo(p6[0],p6[1]);ctx.lineTo(p7[0],p7[1]);ctx.closePath();
  ctx.fillStyle=ct;ctx.fill();ctx.strokeStyle='rgba(0,0,0,0.25)';ctx.lineWidth=0.5;ctx.stroke();
  ctx.beginPath();ctx.moveTo(p0[0],p0[1]);ctx.lineTo(p1[0],p1[1]);ctx.lineTo(p5[0],p5[1]);ctx.lineTo(p4[0],p4[1]);ctx.closePath();
  ctx.fillStyle=cf;ctx.fill();ctx.stroke();
  ctx.beginPath();ctx.moveTo(p1[0],p1[1]);ctx.lineTo(p2[0],p2[1]);ctx.lineTo(p6[0],p6[1]);ctx.lineTo(p5[0],p5[1]);ctx.closePath();
  ctx.fillStyle=cr;ctx.fill();ctx.stroke();
}
function drawPanel(baseX,baseY,baseZ,irrFrac){
  var sinT=Math.sin(TILT_RAD),cosT=Math.cos(TILT_RAD);
  var pBL=iso(baseX,baseY,baseZ);
  var pBR=iso(baseX+PW,baseY,baseZ);
  var pTR=iso(baseX+PW,baseY-PH*sinT,baseZ+PH*cosT);
  var pTL=iso(baseX,baseY-PH*sinT,baseZ+PH*cosT);
  var col=panelColor(irrFrac);
  ctx.beginPath();ctx.moveTo(pBL[0],pBL[1]);ctx.lineTo(pBR[0],pBR[1]);ctx.lineTo(pTR[0],pTR[1]);ctx.lineTo(pTL[0],pTL[1]);ctx.closePath();
  var grd=ctx.createLinearGradient(pBL[0],pBL[1],pTR[0],pTR[1]);
  grd.addColorStop(0,col);
  if(irrFrac>0.5){grd.addColorStop(0.3,'rgba(252,211,77,0.35)');}
  else{grd.addColorStop(0.3,'rgba(37,99,235,0.3)');}
  grd.addColorStop(1.0,col);
  ctx.fillStyle=grd;ctx.fill();
  ctx.strokeStyle=irrFrac>0.5?'rgba(245,158,11,0.9)':'rgba(255,255,255,0.12)';
  ctx.lineWidth=irrFrac>0.5?1.5:0.7;ctx.stroke();
  if(SCALE>15){
    ctx.strokeStyle='rgba(255,255,255,0.08)';ctx.lineWidth=0.4;
    for(var ci=1;ci<4;ci++){
      var t=ci/4;
      ctx.beginPath();
      ctx.moveTo(pBL[0]+(pTL[0]-pBL[0])*t,pBL[1]+(pTL[1]-pBL[1])*t);
      ctx.lineTo(pBR[0]+(pTR[0]-pBR[0])*t,pBR[1]+(pTR[1]-pBR[1])*t);
      ctx.stroke();
    }
  }
  return {pBL:pBL,pBR:pBR,pTR:pTR,pTL:pTL};
}
function drawLeg(x,y,h){var tw=0.08;drawBox(x-tw/2,y-tw/2,0,tw,tw,h,steelColor('top'),steelColor('front'),steelColor('right'));}
function drawRail(x,y,z,len){drawBox(x,y-0.04,z,len,0.08,0.06,steelColor('top'),steelColor('front'),steelColor('right'));}
function drawBolt(x,y,z){
  var pos=iso(x,y,z);
  ctx.beginPath();ctx.arc(pos[0],pos[1],3,0,Math.PI*2);
  ctx.fillStyle='#A0AEC0';ctx.fill();
  ctx.strokeStyle='#F59E0B';ctx.lineWidth=0.8;ctx.stroke();
}
var NUM_WP=20;
var wParticles=[];
for(var i=0;i<NUM_WP;i++){
  wParticles.push({wx:(Math.random()-0.5)*(COLS+2)*(PW+PG)+(COLS*(PW+PG))/2,
    wy:-2+Math.random()*(ROWS+4)*(PH+PG)*0.6,wz:Math.random()*3,
    vx:0.04+Math.random()*0.06,life:Math.random(),len:0.3+Math.random()*0.5});
}
function updateWP(wf){
  for(var i=0;i<wParticles.length;i++){
    var p=wParticles[i];
    p.wx+=p.vx*wf;p.life+=0.02;
    if(p.wx>(COLS+3)*(PW+PG)||p.life>1){
      p.wx=-1.5;p.wy=-2+Math.random()*(ROWS+4)*(PH+PG)*0.6;
      p.wz=Math.random()*3;p.life=0;p.len=0.3+Math.random()*0.5;
    }
  }
}
function drawWP(wf){
  var al=Math.min(0.8,0.25+wf*0.4);
  for(var i=0;i<wParticles.length;i++){
    var p=wParticles[i];
    var x1=iso(p.wx,p.wy,p.wz);var x2=iso(p.wx-p.len,p.wy,p.wz);
    ctx.beginPath();ctx.moveTo(x1[0],x1[1]);ctx.lineTo(x2[0],x2[1]);
    var fadeAl=al*(1-p.life*0.5);
    ctx.strokeStyle='rgba(6,182,212,'+fadeAl.toFixed(3)+')';
    ctx.lineWidth=1.2;ctx.stroke();
  }
}
function drawLightBeams(sunX,sunY,irrFrac,panels){
  if(irrFrac<0.05) return;
  ctx.save();ctx.globalAlpha=irrFrac*0.18;ctx.strokeStyle='#FCD34D';ctx.lineWidth=0.8;
  var step=Math.max(1,Math.floor(panels.length/8));
  for(var i=0;i<panels.length;i+=step){
    var p=panels[i];if(!p) continue;
    ctx.beginPath();ctx.moveTo(sunX,sunY);
    ctx.lineTo((p.pTL[0]+p.pTR[0])/2,(p.pTL[1]+p.pTR[1])/2);
    ctx.stroke();
  }
  ctx.restore();
}
function sunScreenPos(hour){
  var t=Math.max(0,Math.min(1,(hour-6)/12));
  var P0=[W*0.05,H*0.85],P1=[W*0.50,H*0.08],P2=[W*0.95,H*0.85];
  var x=(1-t)*(1-t)*P0[0]+2*(1-t)*t*P1[0]+t*t*P2[0];
  var y=(1-t)*(1-t)*P0[1]+2*(1-t)*t*P1[1]+t*t*P2[1];
  return [x,y];
}
function drawSun(hour,irrFrac,tick){
  if(hour<6||hour>18) return;
  var pos=sunScreenPos(hour);var sx=pos[0],sy=pos[1];
  var opacity=0.3+irrFrac*0.7;
  var grd=ctx.createRadialGradient(sx,sy,0,sx,sy,90);
  grd.addColorStop(0,'rgba(252,211,77,'+(opacity*0.9)+')');
  grd.addColorStop(0.4,'rgba(245,158,11,'+(opacity*0.3)+')');
  grd.addColorStop(1.0,'rgba(245,158,11,0)');
  ctx.beginPath();ctx.arc(sx,sy,90,0,Math.PI*2);ctx.fillStyle=grd;ctx.fill();
  var core=ctx.createRadialGradient(sx,sy,0,sx,sy,22);
  core.addColorStop(0,'#FEFCE8');core.addColorStop(0.5,'#FCD34D');core.addColorStop(1.0,'#F59E0B');
  ctx.beginPath();ctx.arc(sx,sy,22,0,Math.PI*2);ctx.fillStyle=core;ctx.fill();
  ctx.save();ctx.translate(sx,sy);ctx.rotate(tick*0.8);
  ctx.strokeStyle='rgba(252,211,77,'+(opacity*0.6)+')';ctx.lineWidth=2;
  for(var a=0;a<8;a++){
    var angle=a*Math.PI/4;
    ctx.beginPath();ctx.moveTo(Math.cos(angle)*28,Math.sin(angle)*28);
    ctx.lineTo(Math.cos(angle)*44,Math.sin(angle)*44);ctx.stroke();
  }
  ctx.restore();
}
function drawSkyGround(irrFrac){
  var r1=Math.round(lerp(2,8,irrFrac)),g1=Math.round(lerp(10,22,irrFrac)),b1=Math.round(lerp(30,60,irrFrac));
  var r2=Math.round(lerp(8,15,irrFrac)),g2=Math.round(lerp(18,40,irrFrac)),b2=Math.round(lerp(50,90,irrFrac));
  var sg=ctx.createLinearGradient(0,0,0,H);
  sg.addColorStop(0,'rgb('+r1+','+g1+','+b1+')');
  sg.addColorStop(1,'rgb('+r2+','+g2+','+b2+')');
  ctx.fillStyle=sg;ctx.fillRect(0,0,W,H);
  var grd=ctx.createLinearGradient(0,H*0.7,0,H);
  grd.addColorStop(0,'#0D1F0D');grd.addColorStop(1,'#060E06');
  ctx.fillStyle=grd;ctx.fillRect(0,H*0.65,W,H*0.35);
  ctx.strokeStyle='rgba(16,185,129,0.1)';ctx.lineWidth=0.5;
  for(var gx=-2;gx<=COLS+2;gx+=2){
    var p1=iso(gx*(PW+PG),0,0),p2=iso(gx*(PW+PG),(ROWS*(PH+PG)*0.5+3),0);
    ctx.beginPath();ctx.moveTo(p1[0],p1[1]);ctx.lineTo(p2[0],p2[1]);ctx.stroke();
  }
  for(var gy=0;gy<=ROWS*(PH+PG)*0.5+3;gy+=2){
    var q1=iso(0,gy,0),q2=iso((COLS+1)*(PW+PG),gy,0);
    ctx.beginPath();ctx.moveTo(q1[0],q1[1]);ctx.lineTo(q2[0],q2[1]);ctx.stroke();
  }
}
function drawSunPath(){
  ctx.beginPath();
  for(var s=0;s<=30;s++){
    var h=6+s*12/30,p=sunScreenPos(h);
    if(s===0) ctx.moveTo(p[0],p[1]);else ctx.lineTo(p[0],p[1]);
  }
  ctx.strokeStyle='rgba(245,158,11,0.10)';ctx.lineWidth=1.5;
  ctx.setLineDash([4,8]);ctx.stroke();ctx.setLineDash([]);
}
function irradiance(hour){
  if(hour<6||hour>18) return 0;
  return 1050*Math.sin(Math.PI*(hour-6)/12);
}
function cellTemp(irr){
  var wms=WIND_KMH/3.6;
  return AMB_T+(45-20)*(irr/800)/(1+wms*0.035);
}
function powerKW(irr){
  var ct=cellTemp(irr);
  var tl=Math.max(0,1-Math.max(0,ct-25)*(TEMP_COEF/100));
  return SYS_KWP*(irr/1000)*0.975*tl*0.965;
}
var simH=6.0;
var SPEED=0.03;
function frame(){
  simH+=SPEED;if(simH>=24) simH=0;
  var irr=irradiance(simH);
  var irrFrac=irr/1050;
  var power=powerKW(irr);
  var cTemp=cellTemp(irr);
  ctx.clearRect(0,0,W,H);
  drawSkyGround(irrFrac);
  drawSunPath();
  drawSun(simH,irrFrac,simH);
  var wf=0.8+(WIND_KMH/120)*1.5;
  updateWP(wf);drawWP(wf);
  var panelGeoms=[];
  var pIdx=0;
  for(var row=ROWS-1;row>=0;row--){
    for(var col=0;col<COLS;col++){
      if(pIdx>=N_PANELS) break;
      var wx=col*(PW+PG);
      var wy=row*(PH*Math.cos(TILT_RAD)+0.3);
      var wz=0.8;
      var legH=0.8+row*0.12;
      drawLeg(wx+0.15,wy+0.15,legH);
      drawLeg(wx+0.85,wy+0.15,legH);
      if(col<COLS-1) drawRail(wx,wy+0.12,legH+0.02,PW+PG);
      drawRail(wx-0.05,wy+0.10,legH,PW+PG*0.8);
      drawBolt(wx+0.5,wy+0.12,legH+0.06);
      var geom=drawPanel(wx,wy,wz,irrFrac);
      panelGeoms.push(geom);
      pIdx++;
    }
  }
  if(simH>=6&&simH<=18){
    var spos=sunScreenPos(simH);
    drawLightBeams(spos[0],spos[1],irrFrac,panelGeoms);
  }
  var hh=Math.floor(simH).toString().padStart(2,'0');
  var mm=Math.floor((simH-Math.floor(simH))*60).toString().padStart(2,'0');
  document.getElementById('hTime').textContent=hh+':'+mm;
  document.getElementById('hIrr').textContent=Math.round(irr)+' W/m2';
  document.getElementById('hPow').textContent=power.toFixed(2)+' kW';
  document.getElementById('hTemp').textContent=cTemp.toFixed(1)+'C';
  document.getElementById('ifill').style.width=(irrFrac*100)+'%';
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
</script>
</body>
</html>"""

    components.html(html_3d, height=640, scrolling=False)

    st.markdown(f"""
    <div class='sxcard' style='margin-top:12px'>
      <h4>🏗️ 3D Array Layout Summary</h4>
      <p>Array: <strong>{anim_rows_count} rows × {anim_cols_count} cols</strong> = <strong>{p_qty} panels</strong>
         &nbsp;·&nbsp; Panel Area: <strong>{p_qty*2.1:.1f} m²</strong></p>
      <p>Strings: <strong>{strings} × {panels_per_string} panels</strong>
         &nbsp;·&nbsp; String VOC: <strong>{voc_string:.0f} V</strong>
         &nbsp;·&nbsp; Tilt: <strong>{tilt}°</strong></p>
      <p>Structure: <strong>{struct['type']}</strong> &nbsp;·&nbsp; Material: <strong>{struct['material']}</strong></p>
    </div>
    """, unsafe_allow_html=True)

# ── TAB 2: Wind FEA Simulation ────────────────────────────────────────────────
with tabs[2]:
    st.markdown("<span class='sxlabel'>SolidWorks-Class FEA Wind Load Simulation</span>", unsafe_allow_html=True)

    # ── TRUSS CONTROL ──
    st.markdown("### 🔩 Structural Reinforcement")
    truss_cols = st.columns([2,1,1,1])
    with truss_cols[0]:
        st.markdown("""
        <div class='sx-info'>
        <strong>Interactive Truss Addition:</strong> Toggle diagonal truss members to see real-time 
        effect on Von Mises stress, safety factor, and structural load distribution. 
        Truss geometry follows Warren truss pattern for optimal load redistribution.
        </div>
        """, unsafe_allow_html=True)
    with truss_cols[1]:
        add_truss = st.toggle("➕ Add Truss Members", value=st.session_state["truss_enabled"],
                              help="Add Warren-pattern diagonal trusses to reduce bending stress by ~40%")
        st.session_state["truss_enabled"] = add_truss
    with truss_cols[2]:
        truss_material = st.selectbox("Truss Material", ["Q235 Steel","S355 Steel","6061-T6 Aluminum"], index=0)
    with truss_cols[3]:
        truss_section = st.selectbox("Truss Section", ["30×30×3mm RHS","40×40×4mm RHS","50×50×4mm SHS"], index=0)

    # Recompute with truss setting
    fea_with_truss = calc_fea_stress(wind, tilt, p_qty, struct, add_truss)
    fea_without_truss = calc_fea_stress(wind, tilt, p_qty, struct, False)

    if add_truss:
        stress_reduction = ((fea_without_truss["von_mises"] - fea_with_truss["von_mises"]) / max(fea_without_truss["von_mises"],0.001)) * 100
        st.markdown(f"""
        <div class='sx-ok'>
        ✅ <strong>Truss Members Active ({truss_material} — {truss_section})</strong><br>
        Von Mises stress reduced from <strong>{fea_without_truss['von_mises']:.1f} MPa</strong> to 
        <strong>{fea_with_truss['von_mises']:.1f} MPa</strong> 
        (−{stress_reduction:.1f}% reduction). Safety Factor improved from 
        <strong>{fea_without_truss['sf']:.2f}</strong> → <strong>{fea_with_truss['sf']:.2f}</strong>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("<div class='sx-info'>ℹ️ Toggle <strong>Add Truss Members</strong> above to see structural reinforcement effect in real-time.</div>", unsafe_allow_html=True)

    st.markdown(f"""
    <div class='sx-info'>
      FEA: Von Mises stress field — Colour map: 
      <strong style='color:#10B981'>Green=Safe</strong> → 
      <strong style='color:#F59E0B'>Yellow=Caution</strong> → 
      <strong style='color:#EF4444'>Red=Yield/Fail</strong> &nbsp;|&nbsp; 
      Wind: {wind:.0f} km/h &nbsp;|&nbsp; Tilt: {tilt}° &nbsp;|&nbsp; Panels: {p_qty}
    </div>
    """, unsafe_allow_html=True)

    # ── FEA CANVAS ──
    fea_yield = fea_with_truss["yield"]
    fea_vm = fea_with_truss["von_mises"]
    fea_bend = fea_with_truss["bending"]
    fea_axial = fea_with_truss["axial"]
    fea_sf = fea_with_truss["sf"]
    fea_fail = fea_with_truss["fail"]
    rows_fea = min(anim_rows_count,4)
    cols_fea = min(anim_cols_count,5)
    truss_js = "true" if add_truss else "false"

    fea_html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        "<style>"
        "*{margin:0;padding:0;box-sizing:border-box;}"
        "body{background:#020B1A;font-family:'Segoe UI',sans-serif;overflow:hidden;}"
        "canvas{display:block;}"
        "#ctrl{position:absolute;top:8px;left:8px;background:rgba(5,14,37,0.92);border:1px solid rgba(245,158,11,0.25);border-radius:10px;padding:12px 16px;color:#94A3B8;font-size:11px;min-width:200px;}"
        ".cr{display:flex;justify-content:space-between;margin:4px 0;}"
        ".cv{color:#F59E0B;font-weight:700;}"
        ".co{color:#10B981;}.cf{color:#EF4444;}"
        "#cbar{position:absolute;right:10px;top:10px;background:rgba(5,14,37,0.88);border:1px solid rgba(245,158,11,0.2);border-radius:10px;padding:10px;font-size:10px;color:#94A3B8;}"
        "#bot2{position:absolute;bottom:0;left:0;right:0;background:rgba(5,14,37,0.88);border-top:1px solid rgba(245,158,11,0.2);padding:8px 16px;display:flex;gap:24px;font-size:10px;color:#64748B;flex-wrap:wrap;}"
        ".bv{color:#94A3B8;font-weight:700;}"
        "</style></head><body>"
        "<canvas id='fea'></canvas>"
        "<div id='ctrl'>"
        "<div style='color:#F59E0B;font-weight:700;font-size:12px;margin-bottom:8px;letter-spacing:0.08em'>FEA RESULTS</div>"
        "<div class='cr'><span>Von Mises:</span><span class='cv'>" + str(fea_vm) + " MPa</span></div>"
        "<div class='cr'><span>Bending:</span><span class='cv'>" + str(fea_bend) + " MPa</span></div>"
        "<div class='cr'><span>Axial:</span><span class='cv'>" + str(fea_axial) + " MPa</span></div>"
        "<div class='cr'><span>Yield:</span><span class='cv'>" + str(fea_yield) + " MPa</span></div>"
        "<div class='cr'><span>Safety Factor:</span><span class='" + ("cf" if fea_sf < 1.5 else "co") + "'>" + str(fea_sf) + "</span></div>"
        "<div class='cr'><span>Status:</span><span class='" + ("cf" if fea_fail else "co") + "'>" + ("YIELD FAILURE" if fea_fail else "SAFE") + "</span></div>"
        "<div class='cr'><span>Truss:</span><span class='" + ("co" if add_truss else "cv") + "'>" + ("ACTIVE" if add_truss else "OFF") + "</span></div>"
        "<div style='margin-top:10px;color:#475569;font-size:9px'>"
        "Wind: <span style='color:#F59E0B'>" + str(int(wind)) + " km/h</span> &bull; Tilt: <span style='color:#F59E0B'>" + str(tilt) + "deg</span><br>"
        "Panels: " + str(p_qty) + " &bull; EN 1991-1-4 / IEC 61215"
        "</div></div>"
        "<div id='cbar'>"
        "<div style='color:#F59E0B;font-weight:700;font-size:9px;text-align:center;letter-spacing:0.1em'>σ MPa</div>"
        "<div style='display:flex;gap:6px;align-items:center'>"
        "<canvas id='cb' width='18' height='140'></canvas>"
        "<div style='display:flex;flex-direction:column;justify-content:space-between;height:140px;font-size:9px;text-align:right'>"
        "<span>" + str(fea_yield) + "</span><span>" + str(int(fea_yield*0.75)) + "</span><span>" + str(int(fea_yield*0.50)) + "</span><span>" + str(int(fea_yield*0.25)) + "</span><span>0</span>"
        "</div></div></div>"
        "<div id='bot2'>"
        "<div>Material: <span class='bv'>" + struct['material'][:28] + "</span></div>"
        "<div>Foundation: <span class='bv'>" + struct['foundation'] + "</span></div>"
        "<div>Wind Zone: <span class='bv'>" + wind_zone + "</span></div>"
        "<div>Truss: <span class='bv'>" + ("Warren Pattern Active" if add_truss else "No Truss") + "</span></div>"
        "</div>"
        "<script>"
        "var cv=document.getElementById('fea');var ctx=cv.getContext('2d');"
        "cv.width=window.innerWidth;cv.height=window.innerHeight-40;"
        "var YIELD=" + str(fea_yield) + ";"
        "var VM=" + str(fea_vm) + ";"
        "var BEND=" + str(fea_bend) + ";"
        "var AXIAL=" + str(fea_axial) + ";"
        "var SF=" + str(fea_sf) + ";"
        "var WIND=" + str(int(wind)) + ";"
        "var TILT=" + str(tilt) + ";"
        "var ROWS=" + str(rows_fea) + ";"
        "var COLS=" + str(cols_fea) + ";"
        "var HAS_TRUSS=" + truss_js + ";"
        """
var cb=document.getElementById('cb');var cbc=cb.getContext('2d');
var grad=cbc.createLinearGradient(0,0,0,140);
grad.addColorStop(0,'#EF4444');grad.addColorStop(0.25,'#F97316');
grad.addColorStop(0.5,'#F59E0B');grad.addColorStop(0.75,'#84CC16');grad.addColorStop(1.0,'#10B981');
cbc.fillStyle=grad;cbc.fillRect(0,0,18,140);
var ISO=Math.PI/6;
var SC=Math.min(cv.width,cv.height)*0.028;
var CX=cv.width*0.42;var CY=cv.height*0.55;
function iso(wx,wy,wz){
  var sx=CX+(wx-wy)*Math.cos(ISO)*SC;
  var sy=CY-wz*SC+(wx+wy)*Math.sin(ISO)*SC*0.55;
  return [sx,sy];
}
function lerp(a,b,t){return a+(b-a)*t;}
function feaColor(fraction,alpha){
  fraction=Math.max(0,Math.min(1,fraction));
  var r,g,b;
  if(fraction<0.5){var t=fraction*2;r=Math.round(lerp(16,245,t));g=Math.round(lerp(185,158,t));b=Math.round(lerp(129,11,t));}
  else{var t=(fraction-0.5)*2;r=Math.round(lerp(245,239,t));g=Math.round(lerp(158,68,t));b=Math.round(lerp(11,68,t));}
  return 'rgba('+r+','+g+','+b+','+(alpha||1.0)+')';
}
function feaMember(x1,y1,z1,x2,y2,z2,thickness,sLo,sHi){
  var steps=8;var tw=thickness*0.5;
  for(var s=0;s<steps;s++){
    var t0=s/steps,t1=(s+1)/steps;
    var mx0=x1+(x2-x1)*t0,my0=y1+(y2-y1)*t0,mz0=z1+(z2-z1)*t0;
    var mx1=x1+(x2-x1)*t1,my1=y1+(y2-y1)*t1,mz1=z1+(z2-z1)*t1;
    var stress=sLo+(sHi-sLo)*((t0+t1)/2);
    var frac=Math.min(1,stress/YIELD);
    var col=feaColor(frac,0.92);
    var p=[iso(mx0-tw,my0,mz0),iso(mx1-tw,my1,mz1),iso(mx1+tw,my1,mz1),iso(mx0+tw,my0,mz0)];
    ctx.beginPath();ctx.moveTo(p[0][0],p[0][1]);
    for(var i=1;i<p.length;i++) ctx.lineTo(p[i][0],p[i][1]);
    ctx.closePath();ctx.fillStyle=col;ctx.fill();
    ctx.strokeStyle='rgba(0,0,0,0.2)';ctx.lineWidth=0.3;ctx.stroke();
  }
}
function drawArrow(x,y,len,col){
  ctx.save();ctx.translate(x,y);
  ctx.strokeStyle=col;ctx.fillStyle=col;ctx.lineWidth=2;
  ctx.beginPath();ctx.moveTo(0,0);ctx.lineTo(len,0);ctx.stroke();
  ctx.beginPath();ctx.moveTo(len,0);ctx.lineTo(len-8,-5);ctx.lineTo(len-8,5);ctx.closePath();ctx.fill();
  ctx.restore();
}
var tick=0;
function drawFrame(){
  tick++;
  ctx.clearRect(0,0,cv.width,cv.height);
  var bg=ctx.createLinearGradient(0,0,0,cv.height);
  bg.addColorStop(0,'#020B1A');bg.addColorStop(1,'#030F22');
  ctx.fillStyle=bg;ctx.fillRect(0,0,cv.width,cv.height);
  ctx.strokeStyle='rgba(30,58,138,0.3)';ctx.lineWidth=0.5;
  for(var gx=-2;gx<=COLS*2+2;gx++){
    var p1=iso(gx,-1,0),p2=iso(gx,ROWS*1.5+1,0);
    ctx.beginPath();ctx.moveTo(p1[0],p1[1]);ctx.lineTo(p2[0],p2[1]);ctx.stroke();
  }
  for(var gy=-1;gy<=ROWS*1.5+1;gy++){
    var q1=iso(-2,gy,0),q2=iso(COLS*2+2,gy,0);
    ctx.beginPath();ctx.moveTo(q1[0],q1[1]);ctx.lineTo(q2[0],q2[1]);ctx.stroke();
  }
  var windFrac=Math.min(1,WIND/160);
  var vmFrac=Math.min(1,VM/YIELD);
  for(var row=ROWS-1;row>=0;row--){
    for(var col=0;col<COLS;col++){
      var bx=col*2.2;var by=row*2.0;var legH=1.2+row*0.1;
      var stressBase=VM*(0.9+Math.sin(tick*0.04+col+row)*0.05);
      var stressMid=stressBase*0.65;var stressTop=stressBase*0.25;
      // Foundation
      var fb=[iso(bx-0.1,by-0.1,-0.2),iso(bx+0.5,by-0.1,-0.2),iso(bx+0.5,by+0.5,-0.2),iso(bx-0.1,by+0.5,-0.2)];
      ctx.beginPath();ctx.moveTo(fb[0][0],fb[0][1]);for(var fi=1;fi<fb.length;fi++) ctx.lineTo(fb[fi][0],fb[fi][1]);ctx.closePath();
      ctx.fillStyle=feaColor(Math.min(1,stressBase*0.4/YIELD),0.88);ctx.fill();
      ctx.strokeStyle='rgba(0,0,0,0.3)';ctx.lineWidth=0.5;ctx.stroke();
      // Legs
      feaMember(bx+0.1,by+0.1,0,bx+0.1,by+0.1,legH,0.1,stressBase,stressMid);
      feaMember(bx+0.9,by+0.1,0,bx+0.9,by+0.1,legH,0.1,stressBase,stressMid);
      // Cross brace
      feaMember(bx+0.1,by+0.1,legH*0.4,bx+0.9,by+0.1,legH*0.4,0.06,stressMid*0.6,stressMid*0.8);
      // Rail
      feaMember(bx,by+0.1,legH,bx+1.0,by+0.1,legH,0.07,stressMid,stressBase*0.9);
      // TRUSS MEMBERS (Warren pattern) — only if HAS_TRUSS
      if(HAS_TRUSS){
        // Diagonal 1: bottom-left to top-right
        feaMember(bx+0.1,by+0.1,0,bx+0.9,by+0.1,legH,0.05,stressBase*0.3,stressMid*0.2);
        // Diagonal 2: bottom-right to top-left
        feaMember(bx+0.9,by+0.1,0,bx+0.1,by+0.1,legH,0.05,stressBase*0.3,stressMid*0.2);
        // Horizontal mid bracing
        feaMember(bx+0.1,by+0.1,legH*0.5,bx+0.9,by+0.1,legH*0.5,0.04,stressMid*0.25,stressMid*0.3);
        // Glow effect on truss
        ctx.save();ctx.globalAlpha=0.15+0.1*Math.sin(tick*0.05);
        var t1p=iso(bx+0.1,by+0.1,0),t2p=iso(bx+0.9,by+0.1,legH);
        ctx.beginPath();ctx.moveTo(t1p[0],t1p[1]);ctx.lineTo(t2p[0],t2p[1]);
        ctx.strokeStyle='#10B981';ctx.lineWidth=3;ctx.stroke();
        var t3p=iso(bx+0.9,by+0.1,0),t4p=iso(bx+0.1,by+0.1,legH);
        ctx.beginPath();ctx.moveTo(t3p[0],t3p[1]);ctx.lineTo(t4p[0],t4p[1]);
        ctx.strokeStyle='#10B981';ctx.lineWidth=3;ctx.stroke();
        ctx.restore();
      }
      // Panel face
      var sinT=Math.sin(TILT*Math.PI/180),cosT=Math.cos(TILT*Math.PI/180);
      var panFrac=Math.min(1,(BEND*0.3)/YIELD);
      var pBL=iso(bx,by+0.1,legH),pBR=iso(bx+1.0,by+0.1,legH);
      var pTR=iso(bx+1.0,by+0.1-1.4*sinT,legH+1.4*cosT);
      var pTL=iso(bx,by+0.1-1.4*sinT,legH+1.4*cosT);
      ctx.beginPath();ctx.moveTo(pBL[0],pBL[1]);ctx.lineTo(pBR[0],pBR[1]);ctx.lineTo(pTR[0],pTR[1]);ctx.lineTo(pTL[0],pTL[1]);ctx.closePath();
      var pg=ctx.createLinearGradient(pBL[0],pBL[1],pTR[0],pTR[1]);
      pg.addColorStop(0,feaColor(vmFrac*0.6,0.85));
      pg.addColorStop(0.5,feaColor(vmFrac*0.85,0.75));
      pg.addColorStop(1.0,feaColor(vmFrac*0.25,0.65));
      ctx.fillStyle=pg;ctx.fill();
      ctx.strokeStyle='rgba(245,158,11,0.4)';ctx.lineWidth=1.0;ctx.stroke();
      // Bolts
      var boltPts=[[bx+0.1,legH],[bx+0.9,legH]];
      for(var bi=0;bi<boltPts.length;bi++){
        var bpos=iso(boltPts[bi][0],by+0.1,boltPts[bi][1]);
        ctx.beginPath();ctx.arc(bpos[0],bpos[1],4,0,Math.PI*2);
        ctx.fillStyle=feaColor(Math.min(1,stressTop/YIELD),1.0);ctx.fill();
        ctx.strokeStyle='rgba(0,0,0,0.5)';ctx.lineWidth=0.8;ctx.stroke();
      }
      // Wind arrows on panel
      if(WIND>30){
        var midX=(pBL[0]+pTL[0]+pBR[0]+pTR[0])/4;
        var midY=(pBL[1]+pTL[1]+pBR[1]+pTR[1])/4;
        var alen=12+windFrac*20;
        var pulse=0.7+0.3*Math.sin(tick*0.08+col*0.7+row*0.5);
        ctx.globalAlpha=pulse;
        drawArrow(midX,midY,alen,'rgba(6,182,212,0.9)');
        ctx.globalAlpha=1.0;
      }
    }
  }
  // Scene wind arrows
  for(var wa=0;wa<5;wa++){
    var wpos=iso(-1.5,wa*0.8+0.5,1.5+wa*0.3);
    var alen2=30+windFrac*50;
    var wal=0.3+0.4*Math.sin(tick*0.07+wa);
    drawArrow(wpos[0],wpos[1],alen2,'rgba(6,182,212,'+wal.toFixed(2)+')');
    if(wa===2){
      ctx.fillStyle='rgba(6,182,212,0.7)';ctx.font='bold 10px Segoe UI';
      ctx.fillText('W: '+WIND+' km/h',wpos[0]+alen2+6,wpos[1]+4);
    }
  }
  // SF badge
  var sfColor=SF>=2.0?'#10B981':(SF>=1.5?'#F59E0B':'#EF4444');
  var sfPos=iso(COLS*2+0.5,-0.5,2.5);
  ctx.save();ctx.fillStyle='rgba(5,14,37,0.9)';
  ctx.beginPath();if(ctx.roundRect){ctx.roundRect(sfPos[0]-55,sfPos[1]-18,110,36,8);}else{ctx.rect(sfPos[0]-55,sfPos[1]-18,110,36);}
  ctx.fill();ctx.strokeStyle=sfColor;ctx.lineWidth=1.5;ctx.stroke();
  ctx.fillStyle=sfColor;ctx.font='bold 13px Segoe UI';ctx.textAlign='center';
  ctx.fillText('SF = '+SF.toFixed(2),sfPos[0],sfPos[1]);
  ctx.fillStyle='#64748B';ctx.font='9px Segoe UI';
  ctx.fillText(HAS_TRUSS?'TRUSS REINFORCED':'NO TRUSS',sfPos[0],sfPos[1]+14);
  ctx.restore();
  // Stress hotspot glow
  if(vmFrac>0.7&&!HAS_TRUSS){
    var legBase=iso(0.1,0.1,0);
    var pulse2=0.6+0.4*Math.sin(tick*0.06);
    var grds=ctx.createRadialGradient(legBase[0],legBase[1],0,legBase[0],legBase[1],40);
    grds.addColorStop(0,'rgba(239,68,68,'+(pulse2*0.6)+')');
    grds.addColorStop(0.5,'rgba(239,68,68,'+(pulse2*0.2)+')');
    grds.addColorStop(1.0,'rgba(239,68,68,0)');
    ctx.beginPath();ctx.arc(legBase[0],legBase[1],40,0,Math.PI*2);ctx.fillStyle=grds;ctx.fill();
  }
  requestAnimationFrame(drawFrame);
}
requestAnimationFrame(drawFrame);
"""
        "</script></body></html>"
    )

    components.html(fea_html, height=600, scrolling=False)

    st.divider()
    st.markdown("<span class='sxlabel'>FEA Numerical Comparison</span>", unsafe_allow_html=True)

    comp_cols = st.columns(2)
    with comp_cols[0]:
        st.markdown("**Without Truss**")
        fa = st.columns(3)
        fa[0].metric("Von Mises", f"{fea_without_truss['von_mises']:.2f} MPa")
        fa[1].metric("Safety Factor", f"{fea_without_truss['sf']:.2f}")
        fa[2].metric("Status", "⚠️ FAIL" if fea_without_truss["fail"] else "✅ SAFE")
    with comp_cols[1]:
        st.markdown("**With Truss (Warren Pattern)**")
        fb = st.columns(3)
        fb[0].metric("Von Mises", f"{fea_with_truss['von_mises']:.2f} MPa",
                     delta=f"-{fea_without_truss['von_mises']-fea_with_truss['von_mises']:.1f} MPa",
                     delta_color="inverse")
        fb[1].metric("Safety Factor", f"{fea_with_truss['sf']:.2f}",
                     delta=f"+{fea_with_truss['sf']-fea_without_truss['sf']:.2f}",
                     delta_color="normal")
        fb[2].metric("Status", "⚠️ FAIL" if fea_with_truss["fail"] else "✅ SAFE")

    # Comparison chart
    tilts_w = list(range(0,61,5))
    vm_no_truss = [calc_fea_stress(wind,t,p_qty,struct,False)["von_mises"] for t in tilts_w]
    vm_truss = [calc_fea_stress(wind,t,p_qty,struct,True)["von_mises"] for t in tilts_w]

    fig_cmp = go.Figure()
    fig_cmp.add_trace(go.Scatter(x=tilts_w,y=vm_no_truss,name="No Truss",
        line=dict(color='#EF4444',width=2.5),
        fill='tozeroy',fillcolor='rgba(239,68,68,0.08)'))
    fig_cmp.add_trace(go.Scatter(x=tilts_w,y=vm_truss,name="With Warren Truss",
        line=dict(color='#10B981',width=2.5),
        fill='tozeroy',fillcolor='rgba(16,185,129,0.08)'))
    fig_cmp.add_hline(y=fea_yield,line_dash="dash",line_color="#F59E0B",
                      annotation_text=f"Yield: {fea_yield} MPa")
    fig_cmp.add_vline(x=tilt,line_dash="dot",line_color="#F59E0B",
                      annotation_text=f"Current {tilt}°")
    fig_cmp.update_layout(height=340,title="Von Mises Stress: No Truss vs Warren Truss Pattern",
        plot_bgcolor='rgba(11,20,55,0.6)',paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#94A3B8'),
        legend=dict(bgcolor='rgba(15,32,87,0.5)'),
        xaxis=dict(title="Tilt Angle (°)",gridcolor='rgba(255,255,255,0.05)'),
        yaxis=dict(title="Von Mises Stress (MPa)",gridcolor='rgba(255,255,255,0.05)'))
    st.plotly_chart(fig_cmp, use_container_width=True)

    # Heatmap
    hm_speeds = [20,40,60,80,100,120,140,160]
    hm_tilts = [0,10,15,20,25,30,40,60]
    z_vm = [[calc_fea_stress(sp,t,p_qty,struct,add_truss)["von_mises"] for sp in hm_speeds] for t in hm_tilts]
    fig_heat = go.Figure(data=go.Heatmap(
        z=z_vm,x=hm_speeds,y=hm_tilts,
        colorscale=[[0,'#10B981'],[0.4,'#F59E0B'],[0.7,'#F97316'],[1.0,'#EF4444']],
        hovertemplate='Speed: %{x} km/h<br>Tilt: %{y}°<br>σ: %{z:.1f} MPa<extra></extra>',
        colorbar=dict(title=dict(text='Von Mises (MPa)',font=dict(color='#94A3B8')),tickfont=dict(color='#94A3B8'))
    ))
    fig_heat.update_layout(height=300,
        title=f"Stress Heatmap — Wind Speed vs Tilt ({'With Truss' if add_truss else 'No Truss'})",
        plot_bgcolor='rgba(11,20,55,0.6)',paper_bgcolor='rgba(0,0,0,0)',font=dict(color='#94A3B8'),
        xaxis=dict(title="Wind Speed (km/h)"),yaxis=dict(title="Tilt Angle (°)"))
    st.plotly_chart(fig_heat, use_container_width=True)

    s1,s2,s3,s4 = st.columns(4)
    with s1:
        st.markdown(f"<div class='sxcard'><h4>Frame</h4><p>Type: <strong>{struct['type']}</strong></p><p>Max Tilt: <strong>{struct['tilt_max']}°</strong></p></div>", unsafe_allow_html=True)
    with s2:
        st.markdown(f"<div class='sxcard'><h4>Material</h4><p><strong>{struct['material']}</strong></p><p>Yield: <strong>{struct['yield_mpa']} MPa</strong></p><p>E: <strong>{struct['E_gpa']} GPa</strong></p></div>", unsafe_allow_html=True)
    with s3:
        st.markdown(f"<div class='sxcard'><h4>Foundation</h4><p>{struct['foundation']}</p><p>Clamp: <strong>{struct['clamp']}</strong></p></div>", unsafe_allow_html=True)
    with s4:
        sc = "#EF4444" if fea_fail else ("#F59E0B" if fea_sf<2 else "#10B981")
        truss_label = "Warren Truss ACTIVE" if add_truss else "No Truss"
        st.markdown(f"<div class='sxcard'><h4>Safety</h4><p>SF: <strong style='color:{sc}'>{fea_sf:.2f}</strong></p><p>{truss_label}</p></div>", unsafe_allow_html=True)

    if fea_fail:
        st.markdown(f"<div class='sx-error'>⚠️ STRUCTURAL FAILURE: {fea_vm:.1f} MPa exceeds yield {fea_yield} MPa. Add truss members or upgrade wind zone structure.</div>", unsafe_allow_html=True)
    elif fea_sf < 1.5:
        st.markdown(f"<div class='sx-warn'>⚠️ Low SF {fea_sf:.2f} < 1.5. Enable truss reinforcement or upgrade structure class.</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='sx-ok'>✅ Structure passes FEA. SF {fea_sf:.2f} ≥ 1.5. Design within EN 1991-1-4 envelope.</div>", unsafe_allow_html=True)

# ── TAB 3: Technical Specs ────────────────────────────────────────────────────
with tabs[3]:
    st.markdown("<span class='sxlabel'>Full System Technical Specifications</span>", unsafe_allow_html=True)
    tc1,tc2,tc3 = st.columns(3)
    with tc1:
        st.markdown(f"""<div class='sxcard'><h4>Panel Specs</h4>
          <p>Model: <strong>{panel_type}</strong></p>
          <p>Efficiency: <strong>{p_eff}%</strong></p>
          <p>VOC: <strong>{voc} V</strong></p>
          <p>ISC: <strong>{isc} A</strong></p>
          <p>Temp Coeff: <strong>{p_temp}%/°C</strong></p>
          <p>Grade: <strong>{p_note}</strong></p></div>""", unsafe_allow_html=True)
    with tc2:
        st.markdown(f"""<div class='sxcard'><h4>Array Config</h4>
          <p>Total: <strong>{p_qty}</strong> panels</p>
          <p>Strings: <strong>{strings}</strong></p>
          <p>Per String: <strong>{panels_per_string}</strong></p>
          <p>Area: <strong>{p_qty*2.1:.1f} m²</strong></p>
          <p>Capacity: <strong>{sys_size:.2f} kWp</strong></p></div>""", unsafe_allow_html=True)
    with tc3:
        src = "🔴 LIVE" if weather["live"] else "📊 DB"
        st.markdown(f"""<div class='sxcard'><h4>Operating Conditions</h4>
          <p>Tilt: <strong>{tilt}°</strong> | Azimuth: <strong>{azimuth}°</strong></p>
          <p>Ambient Temp: <strong>{temp_ambient:.1f} °C</strong> {src}</p>
          <p>GHI: <strong>{sun_h:.2f} kWh/m²/day</strong> {src}</p>
          <p>Wind: <strong>{wind:.0f} km/h</strong> {src}</p>
          <p>System Losses: <strong>{sys_loss}%</strong></p></div>""", unsafe_allow_html=True)
    st.divider()
    pr_losses = {
        "Temperature Loss": abs(p_temp/100*max(0,temp_ambient-25))*100,
        "Cable & Wiring": vd_percent,
        "Soiling": float(soiling),
        "System Losses": float(sys_loss-soiling_adv),
        "Inverter Inefficiency": float(100-inv_eff),
    }
    fig_pr = go.Figure(go.Waterfall(
        name="PR",orientation="v",
        measure=["absolute"]+["relative"]*len(pr_losses)+["total"],
        x=["Ideal 100%"]+list(pr_losses.keys())+["Performance Ratio"],
        y=[100]+[-v for v in pr_losses.values()]+[None],
        connector={"line":{"color":"rgba(245,158,11,0.3)"}},
        decreasing={"marker":{"color":"#EF4444","opacity":0.8}},
        totals={"marker":{"color":"#F59E0B"}},
    ))
    fig_pr.update_layout(height=320,title="Performance Ratio Waterfall — Loss Breakdown",
        plot_bgcolor='rgba(11,20,55,0.6)',paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#94A3B8'),yaxis=dict(title="% of Ideal",gridcolor='rgba(255,255,255,0.05)'))
    st.plotly_chart(fig_pr, use_container_width=True)

# ── TAB 4: Inverter ───────────────────────────────────────────────────────────
with tabs[4]:
    st.markdown("<span class='sxlabel'>Inverter & Grid Interface</span>", unsafe_allow_html=True)
    ic1,ic2,ic3 = st.columns(3)
    ic1.metric("Inverter",inverter_type,inv_note)
    ic2.metric("Efficiency",f"{inv_eff}%",f"+{(inv_bonus-1)*100:.1f}% bonus")
    ic3.metric("Grid",f"{grid_v}V / {grid_f}Hz","Utility Standard")
    st.divider()
    i1,i2,i3,i4 = st.columns(4)
    i1.metric("DC Input VOC",f"{voc_string:.0f} V","String VOC")
    i2.metric("MPPT Voltage",f"{mppt_voltage:.0f} V","80% of VOC")
    i3.metric("DC Current ISC",f"{isc_string:.1f} A","All Strings")
    i4.metric("AC Output",f"{sys_size*inv_eff/100:.2f} kWp","After losses")

# ── TAB 5: Battery ────────────────────────────────────────────────────────────
with tabs[5]:
    st.markdown("<span class='sxlabel'>Battery Energy Storage System</span>", unsafe_allow_html=True)
    if has_batt:
        bm1,bm2,bm3,bm4 = st.columns(4)
        bm1.metric("Chemistry",battery_type,b_note)
        bm2.metric("Capacity",f"{b_cap:.1f} kWh",f"Voltage: {b_voltage}V")
        bm3.metric("Usable",f"{usable_battery_kwh:.1f} kWh",f"DoD: {dod}%")
        bm4.metric("Backup",f"{hours_of_autonomy:.1f} hrs",f"At {h_load:.0f} kWh/day")
        fig_soc = go.Figure()
        fig_soc.add_trace(go.Scatter(x=list(hours_arr),y=soc,name="Battery SOC (kWh)",
            fill='tozeroy',fillcolor='rgba(16,185,129,0.15)',line=dict(color='#10B981',width=3)))
        fig_soc.add_hline(y=b_cap*(dod/100),line_dash="dash",line_color="#F59E0B",
                          annotation_text=f"Full Usable: {b_cap*(dod/100):.1f} kWh")
        fig_soc.update_layout(height=300,title="Battery SOC — 24hr Profile",
            plot_bgcolor='rgba(11,20,55,0.6)',paper_bgcolor='rgba(0,0,0,0)',font=dict(color='#94A3B8'),
            xaxis=dict(title="Hour",gridcolor='rgba(255,255,255,0.05)'),
            yaxis=dict(title="kWh",gridcolor='rgba(255,255,255,0.05)'))
        st.plotly_chart(fig_soc, use_container_width=True)
    else:
        st.markdown("<div class='sx-info'>ℹ️ Grid-Tied System — No Battery. Select battery chemistry to enable storage analysis.</div>", unsafe_allow_html=True)
    st.divider()
    bat_data = pd.DataFrame([
        {"Chemistry":k,"DoD %":v["default_dod"],"Efficiency %":v["efficiency"],"Life (yrs)":v["life_years"]}
        for k,v in BATTERY_TYPES.items()
    ])
    st.dataframe(bat_data, use_container_width=True, hide_index=True)

# ── TAB 6: Electrical ─────────────────────────────────────────────────────────
with tabs[6]:
    st.markdown("<span class='sxlabel'>Electrical Design — IEC 60364 / NEC</span>", unsafe_allow_html=True)
    ec1,ec2,ec3 = st.columns(3)
    with ec1:
        st.metric("DC VOC",f"{voc_string:.0f} V",f"Strings: {strings}")
        st.metric("DC ISC",f"{isc_string:.1f} A","All strings")
        st.metric("MPPT",f"{mppt_voltage:.0f} V","Operating point")
    with ec2:
        st.metric("Cable Size",f"{cable_size} mm²",f"{wire_length} m run")
        st.metric("Voltage Drop",f"{voltage_drop:.2f} V",f"{vd_percent:.2f}%")
        st.metric("DC Current",f"{current_dc:.1f} A","Sizing current")
    with ec3:
        st.metric("Grid",f"{grid_v}V / {grid_f}Hz",country)
        st.metric("Lightning Rod",f"{rod_height:.1f} m","IEC 62305")
        st.metric("Protection R",f"{protection_radius} m","Rolling sphere")
    st.divider()
    if vd_percent > 3:
        st.markdown(f"<div class='sx-error'>⚠️ Voltage drop {vd_percent:.2f}% exceeds 3% — upgrade cable to {cable_size+6}mm².</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='sx-ok'>✅ Voltage drop {vd_percent:.2f}% within 3% limit.</div>", unsafe_allow_html=True)
    cable_sizes = [4,6,10,16,25]
    vd_vals = [(current_dc*wire_length*0.0175)/cs/mppt_voltage*100 if mppt_voltage>0 else 0 for cs in cable_sizes]
    fig_cable = go.Figure()
    fig_cable.add_trace(go.Bar(x=[f"{cs}mm²" for cs in cable_sizes],y=vd_vals,
        marker_color=['#EF4444' if v>3 else '#10B981' for v in vd_vals],
        hovertemplate='%{x}: %{y:.2f}%<extra></extra>'))
    fig_cable.add_hline(y=3,line_dash="dash",line_color="#F59E0B",annotation_text="3% Limit")
    fig_cable.update_layout(height=300,title="Voltage Drop % by Cable Size",
        plot_bgcolor='rgba(11,20,55,0.6)',paper_bgcolor='rgba(0,0,0,0)',font=dict(color='#94A3B8'),
        yaxis=dict(title="Voltage Drop %",gridcolor='rgba(255,255,255,0.05)'))
    st.plotly_chart(fig_cable, use_container_width=True)

# ── TAB 7: Financial ──────────────────────────────────────────────────────────
with tabs[7]:
    st.markdown("<span class='sxlabel'>25-Year Financial Investment Model</span>", unsafe_allow_html=True)
    fm1,fm2,fm3,fm4 = st.columns(4)
    fm1.metric("Gross CapEx",f"{gross_cost:,.0f} {c_curr}","Before subsidy")
    fm2.metric("Net CapEx",f"{net_cost:,.0f} {c_curr}",f"-{subsidy_pct}% subsidy")
    fm3.metric("Simple Payback",f"{payback:.1f} yrs",f"Yr1: {yearly_profit[0]:,.0f} {c_curr}")
    fm4.metric("25-yr NPV",f"{npv:,.0f} {c_curr}",f"IRR ~{(yearly_profit[0]/net_cost*100):.1f}%")
    st.progress(min(1.0,payback/15))
    cumulative = np.cumsum(yearly_profit)-net_cost
    fig_fin = make_subplots(specs=[[{"secondary_y":True}]])
    fig_fin.add_trace(go.Bar(x=list(range(25)),y=list(yearly_profit),name="Annual Revenue",
                              marker_color='rgba(245,158,11,0.7)'),secondary_y=False)
    fig_fin.add_trace(go.Scatter(x=list(range(25)),y=list(cumulative),name="Cumulative NPV",
                                  line=dict(color='#10B981',width=3)),secondary_y=True)
    fig_fin.add_hline(y=0,line_dash="dash",line_color="rgba(255,255,255,0.2)")
    fig_fin.update_layout(height=400,title="25-Year Financial Projection",
        plot_bgcolor='rgba(11,20,55,0.6)',paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#94A3B8'),legend=dict(bgcolor='rgba(0,0,0,0)'))
    fig_fin.update_yaxes(title_text=f"Annual Revenue ({c_curr})",gridcolor='rgba(255,255,255,0.05)',secondary_y=False)
    fig_fin.update_yaxes(title_text=f"Cumulative NPV ({c_curr})",secondary_y=True)
    st.plotly_chart(fig_fin, use_container_width=True)
    cost_labels = ["Panels","Inverter","Battery","Structure","Cable","Lightning","Installation"]
    cost_values = [max(0,v) for v in [panel_cost,inverter_cost,battery_cost,structure_cost,cable_cost,lightning_cost,sys_size*install_cost]]
    fig_pie = go.Figure(go.Pie(labels=cost_labels,values=cost_values,hole=0.45,
        marker=dict(colors=['#F59E0B','#06B6D4','#10B981','#8B5CF6','#F97316','#EC4899','#64748B'],
                    line=dict(color='#050E25',width=2)),
        textfont=dict(color='white',size=11),
        hovertemplate='%{label}: %{value:,.0f}<extra></extra>'))
    fig_pie.update_layout(height=350,title="CapEx Breakdown",paper_bgcolor='rgba(0,0,0,0)',font=dict(color='#94A3B8'),
        legend=dict(bgcolor='rgba(15,32,87,0.5)'),
        annotations=[dict(text=f"{c_curr}<br>{net_cost/1000:,.0f}K",x=0.5,y=0.5,font_size=13,font_color='#F59E0B',showarrow=False)])
    st.plotly_chart(fig_pie, use_container_width=True)

# ── TAB 8: Eco & Carbon ───────────────────────────────────────────────────────
with tabs[8]:
    st.markdown("<span class='sxlabel'>Environmental Impact & Carbon</span>", unsafe_allow_html=True)
    ec1,ec2,ec3,ec4 = st.columns(4)
    ec1.metric("CO₂ Avoided/Year",f"{co2_annual:.2f} tons","vs grid")
    ec2.metric("Lifetime CO₂",f"{co2_annual*25:.0f} tons","25-year")
    ec3.metric("Trees Equiv.",f"{int(co2_annual*18)}/yr","annual offset")
    ec4.metric("Coal Saved",f"{co2_annual/2.2:.1f} tons/yr","coal equiv")
    fig_eco = go.Figure()
    fig_eco.add_trace(go.Scatter(x=list(range(1,26)),y=[co2_annual*y for y in range(1,26)],
        fill='tozeroy',fillcolor='rgba(16,185,129,0.15)',line=dict(color='#10B981',width=3),name="Cumulative CO₂ Avoided"))
    fig_eco.update_layout(height=300,title="Cumulative CO₂ Avoided Over Lifetime",
        plot_bgcolor='rgba(11,20,55,0.6)',paper_bgcolor='rgba(0,0,0,0)',font=dict(color='#94A3B8'),
        xaxis=dict(title="Year",gridcolor='rgba(255,255,255,0.05)'),
        yaxis=dict(title="Tons CO₂",gridcolor='rgba(255,255,255,0.05)'))
    st.plotly_chart(fig_eco, use_container_width=True)

# ── TAB 9: ESG ────────────────────────────────────────────────────────────────
with tabs[9]:
    st.markdown("<span class='sxlabel'>ESG, Ethics & Supply Chain</span>", unsafe_allow_html=True)
    eg1,eg2,eg3,eg4 = st.columns(4)
    eg1.metric("ESG Rating",esg_rating,country)
    eg2.metric("Labor Risk",labor_risk,"Supply chain")
    eg3.metric("Electricity Access",f"{elec_access}%","National avg")
    eg4.metric("Panel Sourcing",sourcing)

# ── TAB 10: Net Metering ──────────────────────────────────────────────────────
with tabs[10]:
    st.markdown("<span class='sxlabel'>Net Metering & Grid Export</span>", unsafe_allow_html=True)
    if net_metering:
        nm1,nm2,nm3,nm4 = st.columns(4)
        nm1.metric("Daily Generation",f"{sum(gen_24):.1f} kWh")
        nm2.metric("Daily Export",f"{sum(export_24):.1f} kWh",f"@ {sell_rate} {c_curr}/kWh")
        nm3.metric("Daily Import",f"{sum(import_24):.1f} kWh",f"@ {buy_rate} {c_curr}/kWh")
        nm4.metric("Export Credit",f"{sum(export_24)*sell_rate:,.2f} {c_curr}")
        st.markdown("<div class='sx-ok'>✅ Net Metering active. Surplus exported for feed-in credits.</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='sx-warn'>⚠️ Net Metering disabled. Excess generation curtailed.</div>", unsafe_allow_html=True)

# ── TAB 11: AI Diagnosis ──────────────────────────────────────────────────────
with tabs[11]:
    st.markdown("<span class='sxlabel'>AI System Diagnosis & Optimisation</span>", unsafe_allow_html=True)
    d1,d2,d3 = st.columns(3)
    d1.metric("Performance Ratio",f"{pr:.1f}%","System quality")
    d2.metric("Design Grade","A" if pr>80 else "B" if pr>70 else "C","Overall")
    d3.metric("Optimisation Room",f"{max(0,85-pr):.1f}%","Improvement")
    issues = []
    recs = []
    if vd_percent > 3:
        issues.append(f"🔴 Voltage drop {vd_percent:.2f}% exceeds 3% — increase cable to {cable_size+6}mm²")
    if tilt > struct['tilt_max']:
        issues.append(f"🔴 Tilt {tilt}° exceeds structural max {struct['tilt_max']}° for {wind_zone}")
    if fea_result["fail"]:
        issues.append(f"🔴 FEA FAILURE: {fea_result['von_mises']:.1f} MPa exceeds yield {fea_result['yield']} MPa")
    elif fea_result["sf"] < 1.5:
        issues.append(f"🟡 Low SF {fea_result['sf']:.2f} — enable truss reinforcement in FEA tab")
    if pr < 70:
        issues.append(f"🟡 Low PR {pr:.1f}% — review orientation, soiling, shading")
    if soiling > 10:
        issues.append("🟡 High soiling — consider automatic cleaning system")
    if payback > 12:
        issues.append("🟡 Long payback — review tariff rates or reduce system cost")
    if not issues:
        issues.append("🟢 No critical issues — design within all parameters")
    if weather["live"]:
        recs.append(f"💡 Live weather active — calculations reflect real {country} conditions")
    if tilt < abs(c_lat)-5:
        recs.append(f"💡 Increase tilt to ~{int(abs(c_lat))}° to match latitude for max yield")
    if not has_batt:
        recs.append("💡 LiFePO4 battery would increase self-consumption ~35%")
    if not add_truss and fea_sf < 2.0:
        recs.append("💡 Add Warren truss members in FEA tab to improve structural safety factor")
    recs.append(f"💡 Annual cleaning (2-4×/yr) recovers ~{soiling/2:.1f}% yield loss")
    for issue in issues:
        level = "sx-error" if "🔴" in issue else ("sx-warn" if "🟡" in issue else "sx-ok")
        st.markdown(f"<div class='{level}'>{issue}</div>", unsafe_allow_html=True)
    st.divider()
    for rec in recs:
        st.markdown(f"<div class='sx-info'>{rec}</div>", unsafe_allow_html=True)
    st.divider()
    st.text_area("📋 Engineering Audit Report", value=f"""
══════════════════════════════════════════════════════
     SOLARX PROFESSIONAL v4.1 — ENGINEERING AUDIT
══════════════════════════════════════════════════════
Generated  : {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Country    : {country} | Location: {location_name}
Data Mode  : {'LIVE WEATHER API' if weather['live'] else 'Country Database'}
Wind Speed : {wind:.0f} km/h | Temp: {temp_ambient:.1f}C | GHI: {sun_h:.2f} kWh/m2/d
══════════════════════════════════════════════════════
SYSTEM
  Capacity : {sys_size:.2f} kWp | Panels: {p_qty} x {panel_type.split()[0]}
  Inverter : {inverter_type} @ {inv_eff}%
  Battery  : {battery_type} {b_cap:.0f} kWh | Autonomy: {hours_of_autonomy:.1f} hrs

PERFORMANCE
  Daily Gen: {sum(gen_24):.2f} kWh | PR: {pr:.1f}%
  Annual   : {sum(gen_24)*365:.0f} kWh/yr | CO2: {co2_annual:.2f} t/yr

STRUCTURAL
  Wind Zone: {wind_zone} | {wind:.0f} km/h
  Von Mises: {fea_with_truss['von_mises']:.2f} MPa (truss={'ON' if add_truss else 'OFF'})
  Safety F : {fea_with_truss['sf']:.2f} | Yield: {fea_yield} MPa
  Structure: {struct['type']}

FINANCIAL
  Net CapEx: {net_cost:,.0f} {c_curr} (after {subsidy_pct}% subsidy)
  Payback  : {payback:.1f} yrs | 25yr NPV: {npv:,.0f} {c_curr}
══════════════════════════════════════════════════════
""", height=300)

# ── TAB 12: Physics Engine ────────────────────────────────────────────────────
with tabs[12]:
    st.markdown("<span class='sxlabel'>Advanced Physics Engine</span>", unsafe_allow_html=True)
    if weather["live"] and weather["data"] and weather["data"].get("today") is not None:
        st.markdown(f"<div class='sx-ok'>🛰️ Live hourly data for {country}</div>", unsafe_allow_html=True)
        today_data = weather["data"]["today"].copy()
        if len(today_data) < 24:
            today_data = pd.concat([today_data]*3,ignore_index=True)
        today_data = today_data.iloc[:24].copy()
        today_data["Hour"] = range(24)
        output_metrics = []
        for _,row in today_data.iterrows():
            calc = model_solar_physics(
                float(row["Temperature"]),float(row["Wind_Speed"])/3.6,
                float(row["Cloud_Cover"]),int(row["Hour"]),adv_cfg)
            output_metrics.append(calc)
        sim_df = today_data.copy()
    else:
        mock_temps = [temp_ambient-4+8*np.sin(np.pi*(h-6)/12) if 6<=h<=18 else temp_ambient-4 for h in range(24)]
        sim_df = pd.DataFrame({
            "Hour":list(range(24)),"Temperature":mock_temps,
            "Wind_Speed":[wind/3.6]*24,"Cloud_Cover":[cloud_pct]*24,
        })
        output_metrics = []
        for _,row in sim_df.iterrows():
            calc = model_solar_physics(row["Temperature"],row["Wind_Speed"],row["Cloud_Cover"],int(row["Hour"]),adv_cfg)
            output_metrics.append(calc)

    calc_df = pd.DataFrame(output_metrics)
    sim_df = sim_df.reset_index(drop=True)
    sim_df["Incident_Irradiance"] = calc_df["Irradiance"].values
    sim_df["Cell_Temperature"] = calc_df["Cell_Temp"].values
    sim_df["Hourly_Yield_kW"] = calc_df["Power_kW"].values
    total_adv_gen = float(sim_df["Hourly_Yield_kW"].sum())

    pm1,pm2,pm3,pm4 = st.columns(4)
    pm1.metric("Daily Yield",f"{total_adv_gen:.2f} kWh")
    pm2.metric("Peak Cell Temp",f"{sim_df['Cell_Temperature'].max():.1f} °C")
    pm3.metric("Avg Irradiance",f"{sim_df['Incident_Irradiance'].mean():.1f} W/m²")
    pm4.metric("Peak Power",f"{sim_df['Hourly_Yield_kW'].max():.2f} kW")

    fig_phys = make_subplots(rows=2,cols=1,shared_xaxes=True,vertical_spacing=0.08,
                             subplot_titles=("Array Output (kW)","Cell Temperature & Irradiance"))
    fig_phys.add_trace(go.Scatter(x=sim_df["Hour"],y=sim_df["Hourly_Yield_kW"],
        fill='tozeroy',fillcolor='rgba(245,158,11,0.1)',line=dict(color='#F59E0B',width=2.5),name="Power kW"),row=1,col=1)
    fig_phys.add_trace(go.Scatter(x=sim_df["Hour"],y=sim_df["Cell_Temperature"],
        line=dict(color='#EF4444',width=2),name="Cell Temp °C"),row=2,col=1)
    fig_phys.add_trace(go.Scatter(x=sim_df["Hour"],y=sim_df["Incident_Irradiance"],
        line=dict(color='#06B6D4',width=2),name="Irradiance W/m²"),row=2,col=1)
    fig_phys.update_layout(height=500,plot_bgcolor='rgba(11,20,55,0.6)',paper_bgcolor='rgba(0,0,0,0)',
                            font=dict(color='#94A3B8'),legend=dict(bgcolor='rgba(0,0,0,0)'))
    st.plotly_chart(fig_phys, use_container_width=True)

    display_cols = [c for c in ["Hour","Temperature","Wind_Speed","Cloud_Cover","Incident_Irradiance","Cell_Temperature","Hourly_Yield_kW"] if c in sim_df.columns]
    st.dataframe(sim_df[display_cols].round(2), use_container_width=True, hide_index=True)

# ── TAB 13: Storage Matrix ────────────────────────────────────────────────────
with tabs[13]:
    st.markdown("<span class='sxlabel'>Battery & Storage Matrix</span>", unsafe_allow_html=True)
    sm1,sm2,sm3,sm4 = st.columns(4)
    sm1.metric("Total Storage",f"{b_cap:.2f} kWh")
    sm2.metric("Usable",f"{usable_battery_kwh:.2f} kWh",f"DoD: {dod}%")
    sm3.metric("Backup",f"{hours_of_autonomy:.1f} hrs",f"@ {h_load:.0f} kWh/day")
    sm4.metric("Battery CapEx",f"{battery_cost:,.0f} {c_curr}",f"{b_cost_kwh}/kWh")
    st.divider()
    full_bat_df = pd.DataFrame({
        "Battery Type":list(battery_db.keys()),
        "Efficiency (%)": [v[0] for v in battery_db.values()],
        "Cycle Life":     [v[1] for v in battery_db.values()],
        "Cost/kWh":       [v[2] for v in battery_db.values()],
        "Annual Degrade %":[v[3] for v in battery_db.values()],
        "Bus Voltage (V)":[v[4] for v in battery_db.values()],
        "Notes":          [v[5] for v in battery_db.values()],
    })
    st.dataframe(full_bat_df, use_container_width=True, hide_index=True)

# ── TAB 14: Export ────────────────────────────────────────────────────────────
with tabs[14]:
    st.markdown("<span class='sxlabel'>Export — Full Report Package</span>", unsafe_allow_html=True)
    df_export = pd.DataFrame({
        "Hour":list(hours_arr),
        "Generation_kW":[round(x,3) for x in gen_24],
        "Load_kW":[round(x,3) for x in load_24],
        "Export_kW":[round(x,3) for x in export_24],
        "Import_kW":[round(x,3) for x in import_24],
        "Battery_SOC_kWh":[round(x,3) for x in soc],
        "Battery_SOC_pct":[round((x/b_cap)*100,1) if has_batt and b_cap>0 else 0 for x in soc],
    })
    csv = df_export.to_csv(index=False).encode('utf-8')
    summary_data = {
        "Parameter":["Country","Location","Weather Mode","Wind km/h","Temp C","GHI",
                     "System kWp","Panels","Panel Model","Inverter","Battery",
                     "Daily Gen kWh","PR %","Von Mises MPa","Safety Factor",
                     "Wind Zone","CapEx","Net CapEx","Payback","NPV","CO2/yr"],
        "Value":[country,location_name,"LIVE" if weather["live"] else "DB",
                 f"{wind:.0f}",f"{temp_ambient:.1f}",f"{sun_h:.2f}",
                 f"{sys_size:.2f}",p_qty,panel_type,inverter_type,battery_type,
                 f"{sum(gen_24):.2f}",f"{pr:.1f}",f"{fea_with_truss['von_mises']:.2f}",
                 f"{fea_with_truss['sf']:.2f}",wind_zone,f"{gross_cost:,.0f}",
                 f"{net_cost:,.0f}",f"{payback:.1f}",f"{npv:,.0f}",f"{co2_annual:.2f}"],
    }
    summary_df = pd.DataFrame(summary_data)
    summary_csv = summary_df.to_csv(index=False).encode('utf-8')
    ec1,ec2,ec3 = st.columns(3)
    with ec1:
        st.download_button("📥 Hourly Profile (CSV)", csv,
            f"SolarX_{country}_Hourly.csv", mime="text/csv", use_container_width=True)
    with ec2:
        st.download_button("📋 System Summary (CSV)", summary_csv,
            f"SolarX_{country}_Summary.csv", mime="text/csv", use_container_width=True)
    with ec3:
        if PDF_ENABLED:
            pdf_bytes = generate_pdf_report({"Country":country,"System":f"{sys_size:.2f} kWp",
                "Panels":p_qty,"Daily Gen":f"{sum(gen_24):.2f} kWh","PR":f"{pr:.1f}%",
                "Payback":f"{payback:.1f} yrs","NPV":f"{npv:,.0f} {c_curr}"})
            if pdf_bytes:
                st.download_button("📄 PDF Report", pdf_bytes,
                    f"SolarX_Report_{country}.pdf", mime="application/pdf", use_container_width=True)
        else:
            st.info("Install fpdf2 for PDF export")
    st.divider()
    st.dataframe(df_export, height=340, use_container_width=True, hide_index=True)

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.divider()
weather_badge = "🔴 LIVE WEATHER ACTIVE" if weather["live"] else "📊 Country Database Mode"
st.markdown(f"""
<div style='text-align:center;color:#334155;font-size:0.75rem;padding:16px 0 8px'>
  <strong style='color:#475569'>SolarX Professional v4.1</strong> — Enterprise Solar Power Estimation Platform<br>
  Physics-Based FEA | {len(db)}+ Countries | Warren Truss Structural Simulation | Live Weather API<br>
  <span style='color:#10B981'>{weather_badge}</span> · Wind: {wind:.0f} km/h · GHI: {sun_h:.2f} kWh/m²/d · Temp: {temp_ambient:.1f}°C<br>
  <span style='color:#1E3A5F'>All calculations for planning purposes only.</span>
</div>
""", unsafe_allow_html=True)
PYEOF
echo "Done writing app.py"
wc -l /home/claude/app.py
Output

Command argument is 103_798 bytes, exceeding the 100_000-byte per-argument limit. For large content, pipe via stdin or use a file-write API instead of embedding the content inline in the command. Argument preview: 'cat > /home/claude/app.py << \'PYEOF\'\n"""\nSolarX Professional v4.1 — Solar Power Estimator\nEnterprise Edition — Zero-Error Build\n"""\nimport streamlit as st\n\nst.set_page_config(\n    page_title="SolarX P'
Done

