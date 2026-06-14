bash

mkdir -p /home/claude/solarx && cat > /home/claude/write_app.py << 'WRITER_EOF'
# This script writes the app.py file piece by piece
import os

parts = []

parts.append('''"""
SolarX Professional v4.1 - Zero Error Build
Enterprise Solar Power Estimator
"""
import streamlit as st
st.set_page_config(page_title="SolarX Pro", layout="wide", page_icon="\u2600\ufe0f", initial_sidebar_state="expanded")

def show_terms():
    @st.dialog("Terms & Privacy Agreement")
    def terms_dialog():
        st.markdown("""<div style=\'background:#0f172a;padding:16px;border-radius:12px;color:#e2e8f0\'>
        <h3>\u26a0\ufe0f Disclaimer</h3>
        1. <b>No Liability</b> - Calculations for planning only.<br>
        2. <b>Data Privacy</b> - Location used only for weather API.<br>
        3. <b>Accuracy</b> - Results may vary \xb120%.<br>
        4. <b>APIs</b> - Uses Open-Meteo and Nominatim.<br>
        5. <b>Professional Advice</b> - Consult a certified solar engineer.</div>""", unsafe_allow_html=True)
        c1,c2=st.columns(2)
        with c1:
            if st.button("\u274c Decline",use_container_width=True,type="secondary"): st.stop()
        with c2:
            if st.button("\u2705 I Agree",use_container_width=True,type="primary"):
                st.session_state[\'agreed\']=True; st.rerun()
    if \'agreed\' not in st.session_state: terms_dialog(); st.stop()
show_terms()
''')

parts.append('''import pandas as pd
import numpy as np
import math
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import datetime as dt
import requests
import json
import streamlit.components.v1 as components

GEO_ENABLED=False
try:
    from geopy.geocoders import Nominatim
    GEO_ENABLED=True
except: pass

PDF_ENABLED=False
FPDF=None
try:
    from fpdf import FPDF
    PDF_ENABLED=True
except: pass
''')

parts.append('''st.markdown("""
<style>
@import url(\'https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=Space+Grotesk:wght@400;500;700&display=swap\');
:root{--gold:#F59E0B;--amber:#FCD34D;--navy:#0B1437;--cyan:#06B6D4;--green:#10B981;--red:#EF4444;--muted:#94A3B8;--glass:rgba(255,255,255,0.05);--gb:rgba(255,255,255,0.10);}
html,body,[class*="css"]{font-family:\'Inter\',sans-serif;color:#F1F5F9;}
.stApp{background:linear-gradient(160deg,#0B1437 0%,#0F2057 40%,#071020 100%);background-attachment:fixed;}
[data-testid="stSidebar"]{background:rgba(11,20,55,0.97)!important;border-right:1px solid var(--gb)!important;}
[data-testid="stSidebar"] p{color:#CBD5E1!important;font-size:0.82rem!important;}
[data-testid="stMetricValue"]{color:var(--gold)!important;font-family:\'Space Grotesk\',sans-serif!important;font-size:1.5rem!important;font-weight:700!important;}
[data-testid="stMetricLabel"]{color:var(--muted)!important;font-size:0.75rem!important;text-transform:uppercase;letter-spacing:0.08em;}
div[data-testid="metric-container"]{background:var(--glass)!important;border:1px solid var(--gb)!important;border-radius:16px!important;padding:18px 20px!important;backdrop-filter:blur(20px)!important;transition:transform 0.2s ease;}
div[data-testid="metric-container"]:hover{transform:translateY(-3px);border-color:var(--gold)!important;}
div[data-testid="stTabs"] [data-baseweb="tab-list"]{background:rgba(11,20,55,0.5)!important;border-radius:14px!important;padding:6px!important;border:1px solid var(--gb)!important;gap:4px!important;flex-wrap:wrap;}
div[data-testid="stTabs"] button[data-baseweb="tab"]{background:transparent!important;color:var(--muted)!important;border-radius:10px!important;font-weight:500!important;font-size:0.8rem!important;padding:8px 14px!important;border:none!important;}
div[data-testid="stTabs"] button[aria-selected="true"]{background:linear-gradient(135deg,var(--gold),#D97706)!important;color:#0B1437!important;font-weight:700!important;}
.stButton>button[kind="primary"]{background:linear-gradient(135deg,var(--gold),#D97706)!important;color:#0B1437!important;border:none!important;border-radius:10px!important;font-weight:700!important;}
.stDownloadButton>button{background:linear-gradient(135deg,var(--green),#059669)!important;color:white!important;border:none!important;border-radius:10px!important;font-weight:600!important;width:100%;}
.card{background:rgba(15,32,87,0.4);border:1px solid rgba(245,158,11,0.2);border-radius:16px;padding:20px 24px;margin:8px 0;backdrop-filter:blur(16px);}
.card h4{color:var(--gold);margin:0 0 12px 0;font-size:0.85rem;text-transform:uppercase;letter-spacing:0.08em;}
.card p{color:var(--muted);margin:4px 0;font-size:0.88rem;}.card strong{color:#F1F5F9;}
.warn{background:rgba(245,158,11,0.15);border-left:4px solid var(--gold);border-radius:0 10px 10px 0;padding:12px 16px;color:#FCD34D;margin:8px 0;}
.err{background:rgba(239,68,68,0.15);border-left:4px solid var(--red);border-radius:0 10px 10px 0;padding:12px 16px;color:#FCA5A5;margin:8px 0;}
.ok{background:rgba(16,185,129,0.15);border-left:4px solid var(--green);border-radius:0 10px 10px 0;padding:12px 16px;color:#6EE7B7;margin:8px 0;}
.info{background:rgba(6,182,212,0.12);border-left:4px solid var(--cyan);border-radius:0 10px 10px 0;padding:12px 16px;color:#67E8F9;margin:8px 0;}
.hdr{background:linear-gradient(135deg,rgba(245,158,11,0.12),rgba(30,58,138,0.4));border:1px solid rgba(245,158,11,0.3);border-radius:20px;padding:28px 36px;margin-bottom:24px;text-align:center;backdrop-filter:blur(20px);}
.hdr h1{color:white;font-size:2rem;font-weight:800;margin:0;font-family:\'Space Grotesk\',sans-serif;}
.hdr .sub{color:var(--muted);font-size:0.9rem;margin-top:6px;}
.badge{display:inline-block;background:rgba(245,158,11,0.2);color:var(--gold);border:1px solid rgba(245,158,11,0.4);border-radius:100px;padding:3px 14px;font-size:0.72rem;font-weight:700;letter-spacing:0.1em;margin:8px 4px 0;}
.lbl{display:inline-block;background:linear-gradient(135deg,var(--gold),#D97706);color:#0B1437;padding:5px 16px;border-radius:8px;font-size:0.75rem;font-weight:800;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:16px;}
.kpit{font-size:0.7rem;text-transform:uppercase;letter-spacing:0.12em;color:var(--muted);margin:0 0 10px 0;display:flex;align-items:center;gap:10px;}
.kpit::after{content:\'\';flex:1;height:1px;background:var(--gb);}
.liveb{display:inline-block;background:rgba(16,185,129,0.2);color:#10B981;border:1px solid rgba(16,185,129,0.5);border-radius:100px;padding:2px 10px;font-size:0.7rem;font-weight:700;animation:blink 1.5s ease-in-out infinite;}
@keyframes blink{0%,100%{opacity:1}50%{opacity:0.5}}
</style>
""", unsafe_allow_html=True)
''')

parts.append('''db = {
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
panel_db={
    "Jinko 545W Mono PERC":[21.5,0.55,0.28,-0.35,49.8,13.8,"Tier-1 Standard"],
    "Trina 550W Mono PERC":[21.8,0.58,0.29,-0.36,50.1,13.9,"Tier-1 Standard"],
    "LONGi 540W Hi-MO4":[21.2,0.52,0.27,-0.35,49.5,13.7,"Tier-1 Standard"],
    "Jinko 580W TOPCon N-Type":[23.5,0.65,0.32,-0.30,50.8,14.5,"Tier-1 High Eff"],
    "Trina 575W TOPCon":[23.8,0.68,0.33,-0.29,51.0,14.6,"Tier-1 High Eff"],
    "LONGi 570W Hi-MO5":[23.2,0.62,0.31,-0.31,50.5,14.3,"Tier-1 High Eff"],
    "JA Solar 575W DeepBlue":[23.6,0.66,0.32,-0.30,50.9,14.5,"Tier-1 High Eff"],
    "Risen 590W Hyper-ion":[24.0,0.70,0.34,-0.29,51.2,14.7,"Tier-1 Premium"],
    "REC Alpha 410W HJT":[24.2,0.72,0.37,-0.24,51.3,14.9,"HJT Premium"],
    "Jinko 605W Bifacial TOPCon":[24.2,0.68,0.35,-0.29,51.0,14.6,"Bifacial"],
    "Trina 600W Vertex Bifacial":[24.0,0.65,0.34,-0.29,50.8,14.5,"Bifacial"],
    "SunPower 415W Maxeon IBC":[25.2,0.85,0.42,-0.22,52.5,12.8,"IBC Premium"],
    "Aiko 625W ABC IBC":[25.5,0.88,0.43,-0.21,52.8,13.0,"IBC Ultra"],
    "First Solar 460W CdTe":[18.5,0.35,0.22,-0.25,48.5,14.5,"Thin Film"],
    "QCells 480W Q.TRON":[22.8,0.60,0.30,-0.32,50.3,14.2,"QCells Premium"],
}
battery_db={
    "LiFePO4 LFP":[94,6000,180,2.0,48,"Cobalt Free - Best Cycle Life"],
    "NMC Lithium":[92,4000,220,2.5,48,"High Energy Density"],
    "Lead Acid AGM":[85,1200,120,5.0,24,"Low Cost, Heavy Weight"],
    "Sodium Ion":[90,3000,150,3.0,48,"Emerging - Cobalt/Lithium Free"],
    "Solid State":[96,8000,350,1.5,48,"Future Premium Technology"],
    "No Battery":[0,0,0,0,0,"Grid-Tied System Only"],
}
inverter_db={
    "String Inverter":[97.5,1.00,800,"Central MPPT - Most Common"],
    "Micro Inverter":[96.8,1.05,1200,"Panel-Level MPPT - Shade Tolerant"],
    "Hybrid Inverter":[97.0,1.02,1500,"Battery + Grid - Best Flexibility"],
    "Power Optimizer":[98.0,1.03,1400,"DC Optimizer - High Performance"],
    "Central Inverter":[98.5,0.98,600,"Large-Scale Commercial"],
}
structure_db={
    "Low":{"type":"Aluminum Fixed Tilt","tilt_max":30,"material":"Anodized AL-6005-T5","foundation":"Ground Screw","clamp":"Standard","yield_mpa":270,"E_gpa":70},
    "Moderate":{"type":"Galvanized Steel","tilt_max":25,"material":"Hot-Dip Galvanized Q235","foundation":"Concrete Ballast","clamp":"Reinforced","yield_mpa":235,"E_gpa":200},
    "High":{"type":"Galvanized Steel + Bracing","tilt_max":20,"material":"Galvanized Steel + Cross Bracing","foundation":"Concrete Footing","clamp":"Heavy Duty","yield_mpa":355,"E_gpa":200},
    "Extreme":{"type":"Steel + Wind Deflector","tilt_max":15,"material":"S355 Steel + Wind Deflector","foundation":"Deep Concrete Pile","clamp":"Hurricane Rated","yield_mpa":355,"E_gpa":200},
}
''')

parts.append('''@st.cache_data(ttl=86400)
def safe_geocode(country_name,c_lat_fallback):
    if not GEO_ENABLED: return c_lat_fallback,70.0,country_name
    try:
        from geopy.geocoders import Nominatim
        g=Nominatim(user_agent="solarx_v41",timeout=5)
        loc=g.geocode(country_name)
        if loc: return loc.latitude,loc.longitude,loc.address.split(",")[0]
    except: pass
    return c_lat_fallback,70.0,country_name

@st.cache_data(ttl=1800)
def fetch_live_weather(lat,lon):
    url="https://api.open-meteo.com/v1/forecast"
    params={"latitude":lat,"longitude":lon,
        "hourly":"temperature_2m,wind_speed_10m,cloud_cover,shortwave_radiation",
        "daily":"shortwave_radiation_sum,wind_speed_10m_max,temperature_2m_max,temperature_2m_min",
        "timezone":"auto","forecast_days":7,
        "current":"temperature_2m,wind_speed_10m,cloud_cover,shortwave_radiation"}
    try:
        res=requests.get(url,params=params,timeout=12)
        if res.status_code==200:
            data=res.json()
            h=data.get("hourly",{});d=data.get("daily",{});c=data.get("current",{})
            hdf=pd.DataFrame({"Timestamp":pd.to_datetime(h.get("time",[])),"Temperature":h.get("temperature_2m",[]),
                "Wind_Speed":h.get("wind_speed_10m",[]),"Cloud_Cover":h.get("cloud_cover",[]),"GHI_W":h.get("shortwave_radiation",[])})
            hdf["Hour"]=hdf["Timestamp"].dt.hour
            tdf=hdf[hdf["Timestamp"].dt.date==hdf["Timestamp"].dt.date.iloc[0]].copy()
            ddf=pd.DataFrame({"Date":pd.to_datetime(d.get("time",[])),"GHI_sum":d.get("shortwave_radiation_sum",[]),
                "Wind_max":d.get("wind_speed_10m_max",[]),"Temp_max":d.get("temperature_2m_max",[]),"Temp_min":d.get("temperature_2m_min",[])})
            ag=float(np.mean([x for x in d.get("shortwave_radiation_sum",[0.0]) if x]))/1000.0 if d.get("shortwave_radiation_sum") else None
            at=float(np.mean([x for x in h.get("temperature_2m",[25.0]) if x is not None]))
            aw=float(np.mean([x for x in h.get("wind_speed_10m",[30.0]) if x is not None]))
            ac=float(np.mean([x for x in h.get("cloud_cover",[20.0]) if x is not None]))
            return {"hourly":hdf,"today":tdf,"daily":ddf,"current":{"temp":c.get("temperature_2m",at),"wind":c.get("wind_speed_10m",aw),"cloud":c.get("cloud_cover",ac),"ghi":c.get("shortwave_radiation",0.0)},
                "avg_ghi":ag,"avg_temp":at,"avg_wind":aw,"avg_cloud":ac,"success":True}
    except: pass
    return {"success":False}

def get_weather_params(lat,lon,db_ghi,db_wind,db_temp,use_live):
    if use_live:
        wd=fetch_live_weather(lat,lon)
        if wd.get("success"):
            return {"ghi":wd["avg_ghi"] if wd["avg_ghi"] else db_ghi,"wind":wd["avg_wind"],"temp":wd["avg_temp"],"cloud":wd["avg_cloud"],"live":True,"data":wd}
    return {"ghi":db_ghi,"wind":db_wind,"temp":db_temp,"cloud":20.0,"live":False,"data":None}

def calc_wind_load(ws,tilt,qty,area=2.1):
    wms=ws/3.6;q=0.613*wms**2;cp=1.3 if tilt>30 else(1.0 if tilt>15 else 0.8)
    return q*cp*area*qty/1000.0

def calc_fea_stress(ws,tilt,qty,struct,has_truss=False):
    wms=ws/3.6;q=0.613*wms**2;cp=1.3 if tilt>30 else(1.0 if tilt>15 else 0.8)
    f=q*cp*2.1*qty;moment=f*0.9
    Z=(60*60**2-54*54**2)/6.0/1e6
    sb=moment/max(Z,1e-9)/1e6
    if has_truss: sb*=0.55  # Warren truss reduces bending ~45%
    uplift=f*np.sin(np.radians(tilt))
    sa=uplift/4e-4/1e6
    vm=np.sqrt(sb**2+sa**2)
    yld=struct.get("yield_mpa",235)
    sf=yld/max(vm,0.001)
    return {"von_mises":round(vm,2),"bending":round(sb,2),"axial":round(sa,2),"yield":yld,"sf":round(sf,2),"fail":vm>=yld,"truss":has_truss}

def calc_lightning(h):
    return (h+2,20) if h>20 else (h+1.5,30)

def model_solar(temp,wms,cloud,hour,cfg):
    if not(6<=hour<=18): return {"Power_kW":0.0,"Cell_Temp":temp,"Irradiance":0.0}
    ghi=1050*np.sin(np.pi*(hour-6)/12)*max(0.4,np.cos(np.radians(cfg["tilt"]-25))*np.cos(np.radians(cfg["azimuth"]-180)))
    irr=ghi*(1-(cloud/100)*0.82);cool=1+(wms*0.035)
    ct=temp+(45-20)*(irr/800)/cool
    tl=max(0,1-max(0,ct-25)*abs(cfg["temp_coef"])) if ct>25 else 1.0
    re=max(0.5,1-cfg["system_age"]*(cfg["annual_degrad"]/100))
    kw=(cfg["panel_w"]*cfg["panel_count"])/1000*(irr/1000)*tl*(cfg["inverter_eff"]/100)*(1-cfg["soiling"]/100)*re
    return {"Power_kW":max(0.0,round(kw,3)),"Cell_Temp":round(ct,2),"Irradiance":round(irr,2)}

def compute_fin(gen,load,cfg):
    imp=cfg["tariff_import"];exp=cfg["tariff_export"]
    if gen>=load: cr=(gen-load)*exp;nb=load*imp+cr;bill=0.0
    else: bill=(load-gen)*imp;cr=0.0;nb=gen*imp
    capex=cfg["panel_count"]*cfg["cost_per_panel"]
    annual=nb*365.25;pb=capex/annual if annual>0 else 99.0
    return {"Daily_Savings":round(nb,2),"Daily_Bill":round(bill,2),"Export_Credit":round(cr,2),"Payback_Years":round(pb,2)}

def gen_pdf(data):
    if not PDF_ENABLED: return None
    try:
        pdf=FPDF();pdf.add_page();pdf.set_font("Arial","B",18)
        pdf.cell(0,12,"SolarX Pro Report",0,1,"C");pdf.set_font("Arial","",11)
        pdf.cell(0,8,f\'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}\',0,1,"C");pdf.ln(8)
        for k,v in data.items():
            pdf.cell(0,7,f\'{k}: {v}\'.encode("ascii","ignore").decode("ascii"),0,1)
        raw=pdf.output(dest="S")
        return raw.encode("latin-1","replace") if isinstance(raw,str) else raw
    except: return None
''')

parts.append('''with st.sidebar:
    st.markdown("<div style=\'text-align:center;padding:12px 0 8px\'><span style=\'font-size:2rem\'>\u2600\ufe0f</span><div style=\'color:#F59E0B;font-weight:800;font-size:1.05rem\'>SolarX Professional</div><div style=\'color:#64748B;font-size:0.72rem;letter-spacing:0.08em;text-transform:uppercase\'>Enterprise Edition v4.1</div></div>", unsafe_allow_html=True)
    st.divider()
    country=st.selectbox("\U0001f30d Country",sorted(db.keys()))
    cd=db[country]
    c_lat,c_curr,c_sale,c_buy=cd[0],cd[1],cd[2],cd[3]
    esg_rating,labor_risk,sourcing=cd[4],cd[5],cd[6]
    avg_ghi_db,elec_access,grid_v,grid_f=cd[7],cd[8],cd[9],cd[10]
    wind_kmh_db,wind_zone=cd[11],cd[12]
    st.divider()
    st.markdown("### Panel Config")
    panel_type=st.selectbox("Panel Model",list(panel_db.keys()))
    p_eff,p_cost,voc,p_temp,voc_std,isc,p_note=panel_db[panel_type]
    p_qty=st.number_input("Number of Panels",min_value=1,max_value=50000,value=22)
    st.divider()
    st.markdown("### Inverter")
    inverter_type=st.selectbox("Inverter Type",list(inverter_db.keys()))
    inv_eff,inv_bonus,inv_cost,inv_note=inverter_db[inverter_type]
    st.divider()
    st.markdown("### Orientation")
    tilt=st.slider("Panel Tilt deg",0,60,25)
    azimuth=st.slider("Azimuth deg",-180,180,180)
    st.divider()
    st.markdown("### Site Parameters")
    building_height=st.number_input("Building Height (m)",3.0,50.0,6.0)
    wire_length=st.number_input("DC Cable Length (m)",10,200,50)
    cable_size=st.selectbox("DC Cable Size (mm2)",[4,6,10,16,25])
    st.divider()
    st.markdown("### Live Weather")
    live_w=st.toggle("\U0001f534 Live Weather API",value=False)
    if live_w: st.markdown("<span class=\'liveb\'>\u25cf LIVE TELEMETRY</span>",unsafe_allow_html=True)
    st.divider()
    st.markdown("<div style=\'color:#475569;font-size:0.7rem;text-align:center;padding:8px 0\'>\u00a9 2025 SolarX Professional<br>Enterprise Solar Estimation Platform</div>",unsafe_allow_html=True)
''')

parts.append('''col1,col2,col3=st.columns(3)
with col1:
    with st.expander("\U0001f50b Battery & Load",expanded=False):
        battery_type=st.selectbox("Battery Chemistry",list(battery_db.keys()))
        b_eff,b_cycles,b_cost_kwh,b_degrade,b_voltage,b_note=battery_db[battery_type]
        has_batt=battery_type!="No Battery"
        b_cap=st.number_input("Battery Capacity (kWh)",value=20.0) if has_batt else 0.0
        dod=st.slider("Depth of Discharge %",50,95,85) if has_batt else 0
        h_load=st.number_input("Daily Energy Load (kWh)",value=55.0)
        net_metering=st.checkbox("Net Metering Enabled",value=True)
with col2:
    with st.expander("\U0001f52c Advanced Physics",expanded=False):
        panel_w_adv=st.number_input("Unit Panel Power (W)",200,700,int(p_eff*25),5)
        system_age=st.slider("System Age (Years)",0,25,1)
        annual_degrad=st.number_input("Annual Degradation %",0.1,2.0,0.5,0.1)
        soiling_adv=st.slider("Soiling Loss %",0.0,20.0,3.5,0.5)
with col3:
    with st.expander("\U0001f324\ufe0f Climate",expanded=False):
        sun_h_ov=st.slider("Peak Sun Hours/day",3.0,8.5,float(avg_ghi_db))
        sys_loss=st.slider("System Losses %",8,30,14)
        soiling=st.slider("Soiling %",0,20,5)
        temp_ov=st.slider("Ambient Temp C",15,50,28)
with st.expander("\U0001f4b0 Financial & Tariff",expanded=False):
    fc1,fc2,fc3,fc4=st.columns(4)
    with fc1:
        buy_rate=st.number_input(f"Buy Rate ({c_curr}/kWh)",value=float(c_buy))
        sell_rate=st.number_input(f"Sell Rate ({c_curr}/kWh)",value=float(c_sale))
    with fc2:
        tax_val=st.slider("Tax %",0,30,17)
        disc_rate=st.slider("Discount Rate %",3,15,8)
    with fc3:
        install_cost=st.number_input(f"Install Cost/kWp ({c_curr})",value=42000.0 if country=="Pakistan" else 750.0)
        cpp=st.number_input("Cost per Panel",10.0,10000.0,250.0,10.0)
    with fc4:
        subsidy_pct=st.slider("Subsidy %",0,50,30 if country=="Pakistan" else 0)
        inflation=st.slider("Tariff Inflation %/yr",0.0,15.0,3.0,0.5)
''')

parts.append('''lat,lon,loc_name=safe_geocode(country,c_lat)
weather=get_weather_params(lat,lon,avg_ghi_db,wind_kmh_db,temp_ov,live_w)
eff_ghi=weather["ghi"] if weather["ghi"] else sun_h_ov
eff_wind=weather["wind"];eff_temp=weather["avg_temp"] if weather["live"] else temp_ov
eff_cloud=weather["avg_cloud"] if weather["live"] else 20.0
wind=float(eff_wind if weather["live"] else wind_kmh_db)
sun_h=float(eff_ghi) if eff_ghi else sun_h_ov
temp_amb=float(eff_temp);cloud_pct=float(eff_cloud)

sys_size=(p_eff*p_qty*100)/1000.0
pps=max(1,int(1000/max(voc_std,1)))
strings=math.ceil(p_qty/pps)
voc_str=voc_std*pps;isc_str=isc*strings;mppt_v=voc_str*0.8
struct=structure_db[wind_zone]

if "truss_on" not in st.session_state: st.session_state["truss_on"]=False
fea=calc_fea_stress(wind,tilt,p_qty,struct,st.session_state["truss_on"])
fea_no_truss=calc_fea_stress(wind,tilt,p_qty,struct,False)
fea_truss=calc_fea_stress(wind,tilt,p_qty,struct,True)
wind_force=calc_wind_load(wind,tilt,p_qty)
rod_h,prot_r=calc_lightning(building_height)

idc=(sys_size*1000)/400.0;vdrop=(idc*wire_length*0.0175)/cable_size
vd_pct=(vdrop/mppt_v)*100 if mppt_v>0 else 0

hrs=np.arange(24)
ae=np.cos(np.radians(tilt-abs(c_lat)))*np.cos(np.radians(azimuth))
tl=1+(p_temp/100)*(temp_amb+25-25);sl=1-soiling/100
wf=1-cloud_pct*0.008+wind*0.0003
dy=(sys_size*sun_h*((100-sys_loss)/100)*max(0.3,ae)*(p_eff/21.5)*tl*sl*(inv_eff/100)*inv_bonus*wf)

if weather["live"] and weather["data"] and weather["data"].get("today") is not None:
    td=weather["data"]["today"]
    if len(td)>=24:
        g24=[];l24=td["GHI_W"].values[:24];lt24=td["Temperature"].values[:24];lw24=td["Wind_Speed"].values[:24]
        for i in range(24):
            irr=float(l24[i]) if i<len(l24) else 0.0
            t=float(lt24[i]) if i<len(lt24) else temp_amb
            w=float(lw24[i]) if i<len(lw24) else wind/3.6
            if irr<=0: g24.append(0.0);continue
            ct=t+(45-20)*(irr/800)/(1+w*0.035);ths=max(0,1-(ct-25)*abs(p_temp/100))
            g24.append(max(0,sys_size*(irr/1000)*ths*(inv_eff/100)*(1-soiling/100)))
    else: g24=[max(0,dy/12*np.sin(np.pi*(h-6)/12)) if 6<=h<=18 else 0 for h in hrs]
else: g24=[max(0,dy/12*np.sin(np.pi*(h-6)/12)) if 6<=h<=18 else 0 for h in hrs]

lo24=[(h_load/24)*(2.8 if(h>18 or h<7) else 0.7) for h in hrs]
soc=[];cs=b_cap*(dod/100) if has_batt else 0.0
for g,l in zip(g24,lo24):
    if has_batt: cs=max(0,min(b_cap,cs+(g-l)*(b_eff/100)))
    soc.append(cs)
ex24=[max(0,g-l-(soc[i]-soc[i-1] if i>0 else 0)) for i,(g,l) in enumerate(zip(g24,lo24))]
im24=[max(0,l-g-(soc[i-1]-soc[i] if i>0 else 0)) for i,(g,l) in enumerate(zip(g24,lo24))]

bat_cost=b_cap*b_cost_kwh if has_batt else 0.0
pc=sys_size*1000*p_cost;ic2=sys_size*inv_cost;sc=sys_size*150
cc=wire_length*cable_size*2.5;lc=rod_h*80
gross=(pc+bat_cost+ic2+sc+cc+lc+sys_size*install_cost);net_c=gross*(1-subsidy_pct/100)
yg=[sum(g24)*365*(1-b_degrade/100)**y for y in range(25)]
gr=sum(ex24)/sum(g24) if sum(g24)>0 else 0
yp=[]
for i,ygi in enumerate(yg):
    ti=buy_rate*((1+inflation/100)**i);te=sell_rate*((1+inflation/100)**i)
    yp.append(ygi*((1-gr)*ti+gr*te)*(1-tax_val/100))
pb=net_c/yp[0] if yp[0]>0 else 99.0
npv=sum([p/((1+disc_rate/100)**i) for i,p in enumerate(yp)])-net_c
adv_cfg={"panel_type":"Mono","panel_w":panel_w_adv,"panel_count":p_qty,"cost_per_panel":cpp,
    "temp_coef":p_temp/100,"tilt":tilt,"azimuth":azimuth,"system_age":system_age,
    "annual_degrad":annual_degrad,"inverter_eff":inv_eff,"soiling":soiling_adv,
    "tariff_import":buy_rate,"tariff_export":sell_rate}
fin=compute_fin(sum(g24),h_load,adv_cfg)
usable=b_cap*(dod/100) if has_batt else 0.0
autonomy=usable/(h_load/24) if h_load>0 else 0.0
pr=(sum(g24)/(sys_size*sun_h))*100 if sys_size*sun_h>0 else 0
co2=sum(g24)*365*0.82/1000
anim_cols=min(p_qty,12);anim_rows=math.ceil(p_qty/anim_cols)
''')

parts.append('''lb="<span class=\'liveb\'>\u25cf LIVE WEATHER</span>" if weather["live"] else ""
st.markdown(f"""<div class=\'hdr\'>
  <h1>\u2600\ufe0f SolarX Professional \u2014 {country} {lb}</h1>
  <div class=\'sub\'>\U0001f4cd {loc_name} &nbsp;\u00b7&nbsp; {sys_size:.2f} kWp System &nbsp;\u00b7&nbsp; {p_qty} \u00d7 {panel_type.split()[0]} Panels</div>
  <div><span class=\'badge\'>v4.1</span><span class=\'badge\'>ESG {esg_rating}</span>
  <span class=\'badge\'>{grid_v}V {grid_f}Hz</span><span class=\'badge\'>Wind Zone: {wind_zone}</span>
  <span class=\'badge\'>GHI: {sun_h:.2f} kWh/m\u00b2/d</span><span class=\'badge\'>Wind: {wind:.0f} km/h</span>
  <span class=\'badge\'>Temp: {temp_amb:.0f}\u00b0C</span></div></div>""",unsafe_allow_html=True)

st.markdown("<p class=\'kpit\'>System Performance KPIs</p>",unsafe_allow_html=True)
k=st.columns(5)
k[0].metric("\u26a1 System Size",f"{sys_size:.2f} kWp",f"{p_qty} panels")
k[1].metric("\u2600\ufe0f Daily Output",f"{sum(g24):.1f} kWh",f"PR: {pr:.0f}%")
k[2].metric("\U0001f4c8 Annual Yield",f"{sum(g24)*365:.0f} kWh",f"GHI: {sun_h:.1f}")
k[3].metric("\U0001f33f CO\u2082 Avoided",f"{co2:.1f} T/yr",f"{int(co2*18)} trees/yr")
k[4].metric("\U0001f4b0 Daily Savings",f"{fin[\'Daily_Savings\']:,.1f} {c_curr}",f"Ex: {sum(ex24):.1f} kWh")
st.markdown("<p class=\'kpit\' style=\'margin-top:18px\'>Financial & Structural KPIs</p>",unsafe_allow_html=True)
k2=st.columns(6)
k2[0].metric("\U0001f4b5 Net CapEx",f"{net_c:,.0f} {c_curr}",f"-{subsidy_pct}% subsidy")
k2[1].metric("\u23f1\ufe0f Payback",f"{pb:.1f} yrs",f"NPV: {npv:,.0f}")
k2[2].metric("\U0001f50c VOC String",f"{voc_str:.0f} V",f"ISC: {isc_str:.1f} A")
k2[3].metric("\U0001f4c9 Voltage Drop",f"{vd_pct:.2f}%","\u26a0\ufe0f High" if vd_pct>3 else "\u2705 OK")
k2[4].metric("\U0001f4a8 Wind Risk",wind_zone,f"{wind:.0f} km/h",delta_color="inverse" if wind_zone in["Extreme","High"] else "normal")
k2[5].metric("\U0001f529 FEA Stress",f"{fea[\'von_mises\']:.1f} MPa",f"SF: {fea[\'sf\']:.2f}",delta_color="inverse" if fea["fail"] else "normal")
st.divider()
''')

print("Parts assembled:", len(parts))
print("Total chars:", sum(len(p) for p in parts))

# Write all parts
with open("/home/claude/solarx/app_main.py", "w") as f:
    for p in parts:
        f.write(p)

print("Written app_main.py:", os.path.getsize("/home/claude/solarx/app_main.py"), "bytes")
WRITER_EOF
python3 /home/claude/write_app.py
Output

Parts assembled: 9
Total chars: 28837
Written app_main.py: 28935 bytes
bash

cat > /home/claude/write_tabs.py << 'WRITER_EOF'
# Write the tabs section - key fix: NO Python f-strings with JS template literals
# All JS uses string concatenation instead of backticks for dynamic values

import os

tabs_code = r'''
tabs=st.tabs(["📊 Energy Profile","🏗️ 3D Animator","💨 Wind FEA Sim",
    "🔧 Tech Specs","🔌 Inverter","🔋 Battery","⚡ Electrical",
    "💰 Financial","🌿 Eco & Carbon","🛡️ ESG","📡 Net Metering",
    "🤖 AI Diagnosis","📈 Physics","📦 Storage","📄 Export"])

# ── TAB 0 ────────────────────────────────────────────────────────────────────
with tabs[0]:
    st.markdown("<span class='lbl'>24-Hour Energy Profile</span>",unsafe_allow_html=True)
    if weather["live"]:
        st.markdown(f"<div class='ok'>🛰️ <b>Live Weather Active</b> — {country}. Wind:{wind:.0f}km/h Temp:{temp_amb:.1f}°C Cloud:{cloud_pct:.0f}%</div>",unsafe_allow_html=True)
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=list(hrs),y=g24,name="☀️ Solar Generation",fill='tozeroy',fillcolor='rgba(245,158,11,0.15)',line=dict(color='#F59E0B',width=3),hovertemplate='%{y:.2f} kW<extra>Gen</extra>'))
    fig.add_trace(go.Scatter(x=list(hrs),y=lo24,name="⚡ Load",line=dict(color='#EF4444',width=2.5,dash='dot')))
    if has_batt: fig.add_trace(go.Scatter(x=list(hrs),y=soc,name="🔋 Battery SOC",line=dict(color='#10B981',width=2.5)))
    fig.add_trace(go.Bar(x=list(hrs),y=ex24,name="↑ Export",marker_color='rgba(6,182,212,0.5)'))
    fig.add_trace(go.Bar(x=list(hrs),y=im24,name="↓ Import",marker_color='rgba(239,68,68,0.35)'))
    fig.update_layout(height=480,barmode='overlay',plot_bgcolor='rgba(11,20,55,0.6)',paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#94A3B8'),title=dict(text="Hourly Generation vs Load",font=dict(color='#F1F5F9',size=14)),
        legend=dict(bgcolor='rgba(15,32,87,0.7)'),hovermode='x unified',
        xaxis=dict(title="Hour",gridcolor='rgba(255,255,255,0.06)',tickmode='linear',dtick=2),
        yaxis=dict(title="kW / kWh",gridcolor='rgba(255,255,255,0.06)'))
    st.plotly_chart(fig,use_container_width=True)
    ea,eb,ec,ed=st.columns(4)
    ea.metric("Peak Gen",f"{max(g24):.2f} kW","solar noon")
    eb.metric("Peak Load",f"{max(lo24):.2f} kW","evening peak")
    ec.metric("Self-Consumption",f"{(1-sum(im24)/max(h_load,1))*100:.1f}%","grid independence")
    ed.metric("Net Export",f"{sum(ex24)-sum(im24):.1f} kWh/day")
    if weather["live"] and weather["data"] and weather["data"].get("daily") is not None:
        st.divider()
        dfw=weather["data"]["daily"]
        if len(dfw)>0:
            f7=make_subplots(rows=2,cols=1,shared_xaxes=True,vertical_spacing=0.1,subplot_titles=("GHI kWh/m²","Temp & Wind"))
            f7.add_trace(go.Bar(x=dfw["Date"].astype(str),y=dfw["GHI_sum"],name="GHI",marker_color='rgba(245,158,11,0.7)'),row=1,col=1)
            f7.add_trace(go.Scatter(x=dfw["Date"].astype(str),y=dfw["Temp_max"],name="Max Temp",line=dict(color='#EF4444',width=2)),row=2,col=1)
            f7.add_trace(go.Scatter(x=dfw["Date"].astype(str),y=dfw["Wind_max"],name="Max Wind",line=dict(color='#06B6D4',width=2)),row=2,col=1)
            f7.update_layout(height=380,plot_bgcolor='rgba(11,20,55,0.6)',paper_bgcolor='rgba(0,0,0,0)',font=dict(color='#94A3B8'))
            st.plotly_chart(f7,use_container_width=True)
'''

with open("/home/claude/solarx/tab0.py","w") as f:
    f.write(tabs_code)
print("tab0 written:", os.path.getsize("/home/claude/solarx/tab0.py"))
WRITER_EOF
python3 /home/claude/write_tabs.py
Output

tab0 written: 3248
bash

cat > /home/claude/write_tab1.py << 'PYEOF'
# Write the 3D animator tab - ALL JS uses string concat, NO template literals in f-strings

import os, json

tab1_part1 = '''
# ── TAB 1: 3D Animator ───────────────────────────────────────────────────────
with tabs[1]:
    st.markdown("<span class=\'lbl\'>3D Panel Array Animator</span>",unsafe_allow_html=True)
    st.markdown("<div class=\'info\'>3D isometric animation with structural steel, mounting rails, bolt nodes, sun arc, wind particles, live irradiance mapping.</div>",unsafe_allow_html=True)
    g24_js=json.dumps([round(x,3) for x in g24])
    # Pre-compute all Python values as plain strings before building HTML
    _wind=str(round(wind,1))
    _temp=str(round(temp_amb,1))
    _kwp=str(round(sys_size,4))
    _tilt=str(tilt)
    _pqty=str(p_qty)
    _rows=str(anim_rows)
    _cols=str(anim_cols)
    _str=str(strings)
    _voc=str(round(voc_str,0))
    _mode="LIVE" if weather["live"] else "DB"
    _tc=str(round(abs(p_temp),4))
    _tilt_rad=str(round(tilt*3.14159265/180,6))
'''

# The HTML/JS is built with pure string concatenation (no f-strings that could conflict)
tab1_html_builder = r'''
    _html3d = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'><style>"
        "*{margin:0;padding:0;box-sizing:border-box;}"
        "body{background:#030C1E;overflow:hidden;font-family:'Segoe UI',sans-serif;}"
        "canvas{display:block;}"
        "#hud{position:absolute;top:0;left:0;right:0;display:flex;background:rgba(5,14,37,0.88);"
        "border-bottom:1px solid rgba(245,158,11,0.25);padding:7px 16px;justify-content:space-between;"
        "align-items:center;flex-wrap:wrap;gap:8px;}"
        ".hc{display:flex;flex-direction:column;align-items:center;min-width:80px;}"
        ".hl{color:#4A6FA5;font-size:9px;letter-spacing:0.1em;text-transform:uppercase;}"
        ".hv{color:#F59E0B;font-size:13px;font-weight:700;font-family:'Courier New',monospace;}"
        ".hg{color:#10B981;}.hb{color:#06B6D4;}.hr{color:#EF4444;}"
        "#bot{position:absolute;bottom:0;left:0;right:0;background:rgba(5,14,37,0.88);"
        "border-top:1px solid rgba(245,158,11,0.2);padding:6px 16px;display:flex;gap:20px;align-items:center;flex-wrap:wrap;}"
        ".bi{color:#64748B;font-size:10px;}.bi span{color:#94A3B8;font-weight:600;}"
        "#ib{flex:1;height:5px;background:#0F2057;border-radius:3px;overflow:hidden;min-width:60px;}"
        "#if{height:100%;width:0%;background:linear-gradient(90deg,#1D4ED8,#F59E0B);transition:width 0.4s;border-radius:3px;}"
        "#leg{position:absolute;right:10px;top:60px;background:rgba(5,14,37,0.82);border:1px solid rgba(245,158,11,0.2);"
        "border-radius:10px;padding:10px 14px;font-size:10px;color:#94A3B8;}"
        ".lr{display:flex;align-items:center;gap:7px;margin:3px 0;}"
        ".ls{width:14px;height:14px;border-radius:3px;}"
        "</style></head><body>"
        "<canvas id='c'></canvas>"
        "<div id='hud'>"
        "<div class='hc'><div class='hl'>Sim Time</div><div class='hv' id='hTime'>06:00</div></div>"
        "<div class='hc'><div class='hl'>Irradiance</div><div class='hv' id='hIrr'>0 W/m2</div></div>"
        "<div class='hc'><div class='hl'>Array Output</div><div class='hv hg' id='hPow'>0.00 kW</div></div>"
        "<div class='hc'><div class='hl'>Cell Temp</div><div class='hv hr' id='hTemp'>--C</div></div>"
        "<div class='hc'><div class='hl'>Wind</div><div class='hv hb'>" + _wind + " km/h</div></div>"
        "<div class='hc'><div class='hl'>Panels</div><div class='hv'>" + _pqty + "</div></div>"
        "<div class='hc'><div class='hl'>kWp</div><div class='hv'>" + _kwp[:5] + "</div></div>"
        "<div class='hc'><div class='hl'>Tilt</div><div class='hv'>" + _tilt + "deg</div></div>"
        "<div class='hc'><div class='hl'>Mode</div><div class='hv hg'>" + _mode + "</div></div>"
        "</div>"
        "<div id='leg'>"
        "<div style='font-size:9px;color:#F59E0B;font-weight:700;margin-bottom:6px'>LEGEND</div>"
        "<div class='lr'><div class='ls' style='background:#1E3A8A'></div>Night/Low</div>"
        "<div class='lr'><div class='ls' style='background:#0891B2'></div>Morning</div>"
        "<div class='lr'><div class='ls' style='background:#F59E0B'></div>Peak noon</div>"
        "<div class='lr'><div class='ls' style='background:#78716C'></div>Steel</div>"
        "<div class='lr'><div class='ls' style='background:rgba(6,182,212,0.6)'></div>Wind</div>"
        "<div class='lr'><div class='ls' style='background:rgba(245,158,11,0.4)'></div>Light</div>"
        "</div>"
        "<div id='bot'>"
        "<div class='bi'>Rows:<span>" + _rows + "</span></div>"
        "<div class='bi'>Cols:<span>" + _cols + "</span></div>"
        "<div class='bi'>Strings:<span>" + _str + "</span></div>"
        "<div class='bi'>VOC:<span>" + _voc + "V</span></div>"
        "<div id='ib'><div id='if'></div></div>"
        "<div class='bi'>Irradiance to Peak</div>"
        "</div>"
        "<script>"
        "var cv=document.getElementById('c'),ctx=cv.getContext('2d');"
        "var ROWS=" + _rows + ",COLS=" + _cols + ",NP=" + _pqty + ",TILT=" + _tilt + ",SYS=" + _kwp + ";"
        "var AMB=" + _temp + ",WKH=" + _wind + ",TC=" + _tc + ",GEN=" + g24_js + ";"
        "var W,H;"
        "function resize(){W=cv.width=window.innerWidth;H=cv.height=window.innerHeight-52;cv.style.marginTop='52px';}"
        "resize();window.addEventListener('resize',resize);"
        "var ISO=Math.PI/6,TRAD=" + _tilt_rad + ",PW=1.0,PH=1.7,PG=0.18;"
        "var SCALE=Math.min(800,600)*0.022;"
        "function iso(wx,wy,wz){"
        "  var sx=W/2+(wx-wy)*Math.cos(ISO)*SCALE;"
        "  var sy=H/2-wz*SCALE+(wx+wy)*Math.sin(ISO)*SCALE*0.55;"
        "  return [sx,sy];"
        "}"
        "function lerp(a,b,t){return a+(b-a)*t;}"
        "function panelCol(f){"
        "  var r,g,b;"
        "  if(f<0.5){var t=f*2;r=Math.round(lerp(10,6,t));g=Math.round(lerp(24,122,t));b=Math.round(lerp(66,196,t));}"
        "  else{var t=(f-0.5)*2;r=Math.round(lerp(6,245,t));g=Math.round(lerp(122,158,t));b=Math.round(lerp(196,11,t));}"
        "  return 'rgb('+r+','+g+','+b+')';"
        "}"
        "function steelC(face){"
        "  if(face==='top') return '#78818C';"
        "  if(face==='front') return '#5C6370';"
        "  return '#3D4249';"
        "}"
        "function drawBox(x,y,z,dx,dy,dz,ct,cf,cr){"
        "  var p0=iso(x,y,z),p1=iso(x+dx,y,z),p2=iso(x+dx,y+dy,z),p3=iso(x,y+dy,z);"
        "  var p4=iso(x,y,z+dz),p5=iso(x+dx,y,z+dz),p6=iso(x+dx,y+dy,z+dz),p7=iso(x,y+dy,z+dz);"
        "  ctx.beginPath();ctx.moveTo(p4[0],p4[1]);ctx.lineTo(p5[0],p5[1]);ctx.lineTo(p6[0],p6[1]);ctx.lineTo(p7[0],p7[1]);ctx.closePath();"
        "  ctx.fillStyle=ct;ctx.fill();ctx.strokeStyle='rgba(0,0,0,0.25)';ctx.lineWidth=0.5;ctx.stroke();"
        "  ctx.beginPath();ctx.moveTo(p0[0],p0[1]);ctx.lineTo(p1[0],p1[1]);ctx.lineTo(p5[0],p5[1]);ctx.lineTo(p4[0],p4[1]);ctx.closePath();"
        "  ctx.fillStyle=cf;ctx.fill();ctx.stroke();"
        "  ctx.beginPath();ctx.moveTo(p1[0],p1[1]);ctx.lineTo(p2[0],p2[1]);ctx.lineTo(p6[0],p6[1]);ctx.lineTo(p5[0],p5[1]);ctx.closePath();"
        "  ctx.fillStyle=cr;ctx.fill();ctx.stroke();"
        "}"
        "function drawPanel(bx,by,bz,f){"
        "  var sT=Math.sin(TRAD),cT=Math.cos(TRAD);"
        "  var pBL=iso(bx,by,bz),pBR=iso(bx+PW,by,bz);"
        "  var pTR=iso(bx+PW,by-PH*sT,bz+PH*cT),pTL=iso(bx,by-PH*sT,bz+PH*cT);"
        "  var col=panelCol(f);"
        "  ctx.beginPath();ctx.moveTo(pBL[0],pBL[1]);ctx.lineTo(pBR[0],pBR[1]);"
        "  ctx.lineTo(pTR[0],pTR[1]);ctx.lineTo(pTL[0],pTL[1]);ctx.closePath();"
        "  var grd=ctx.createLinearGradient(pBL[0],pBL[1],pTR[0],pTR[1]);"
        "  grd.addColorStop(0,col);"
        "  if(f>0.5){grd.addColorStop(0.3,'rgba(252,211,77,0.35)');}"
        "  else{grd.addColorStop(0.3,'rgba(37,99,235,0.3)');}"
        "  grd.addColorStop(1.0,col);"
        "  ctx.fillStyle=grd;ctx.fill();"
        "  ctx.strokeStyle=f>0.5?'rgba(245,158,11,0.9)':'rgba(255,255,255,0.12)';"
        "  ctx.lineWidth=f>0.5?1.5:0.7;ctx.stroke();"
        "  if(SCALE>15){"
        "    ctx.strokeStyle='rgba(255,255,255,0.08)';ctx.lineWidth=0.4;"
        "    for(var ci=1;ci<4;ci++){"
        "      var t=ci/4;"
        "      ctx.beginPath();"
        "      ctx.moveTo(pBL[0]+(pTL[0]-pBL[0])*t,pBL[1]+(pTL[1]-pBL[1])*t);"
        "      ctx.lineTo(pBR[0]+(pTR[0]-pBR[0])*t,pBR[1]+(pTR[1]-pBR[1])*t);"
        "      ctx.stroke();"
        "    }"
        "  }"
        "  return {pBL:pBL,pBR:pBR,pTR:pTR,pTL:pTL};"
        "}"
        "function drawLeg(x,y,h){var tw=0.08;drawBox(x-tw/2,y-tw/2,0,tw,tw,h,steelC('top'),steelC('front'),steelC('right'));}"
        "function drawRail(x,y,z,len){drawBox(x,y-0.04,z,len,0.08,0.06,steelC('top'),steelC('front'),steelC('right'));}"
        "function drawBolt(x,y,z){"
        "  var pos=iso(x,y,z);"
        "  ctx.beginPath();ctx.arc(pos[0],pos[1],3,0,Math.PI*2);"
        "  ctx.fillStyle='#A0AEC0';ctx.fill();"
        "  ctx.strokeStyle='#F59E0B';ctx.lineWidth=0.8;ctx.stroke();"
        "}"
        "var wParts=[];"
        "for(var i=0;i<20;i++) wParts.push({wx:(Math.random()-0.5)*(COLS+2)*(PW+PG)+(COLS*(PW+PG))/2,"
        "  wy:-2+Math.random()*(ROWS+4)*(PH+PG)*0.6,wz:Math.random()*3,"
        "  vx:0.04+Math.random()*0.06,life:Math.random(),len:0.3+Math.random()*0.5});"
        "function updateWP(wf){"
        "  for(var i=0;i<wParts.length;i++){"
        "    var p=wParts[i];p.wx+=p.vx*wf;p.life+=0.02;"
        "    if(p.wx>(COLS+3)*(PW+PG)||p.life>1){"
        "      p.wx=-1.5;p.wy=-2+Math.random()*(ROWS+4)*(PH+PG)*0.6;"
        "      p.wz=Math.random()*3;p.life=0;p.len=0.3+Math.random()*0.5;"
        "    }"
        "  }"
        "}"
        "function drawWP(wf){"
        "  var al=Math.min(0.8,0.25+wf*0.4);"
        "  for(var i=0;i<wParts.length;i++){"
        "    var p=wParts[i];"
        "    var x1=iso(p.wx,p.wy,p.wz),x2=iso(p.wx-p.len,p.wy,p.wz);"
        "    ctx.beginPath();ctx.moveTo(x1[0],x1[1]);ctx.lineTo(x2[0],x2[1]);"
        "    var fa=al*(1-p.life*0.5);"
        "    ctx.strokeStyle='rgba(6,182,212,'+fa.toFixed(3)+')';"
        "    ctx.lineWidth=1.2;ctx.stroke();"
        "  }"
        "}"
        "function drawBeams(sx,sy,f,panels){"
        "  if(f<0.05) return;"
        "  ctx.save();ctx.globalAlpha=f*0.18;ctx.strokeStyle='#FCD34D';ctx.lineWidth=0.8;"
        "  var step=Math.max(1,Math.floor(panels.length/8));"
        "  for(var i=0;i<panels.length;i+=step){"
        "    var p=panels[i];if(!p) continue;"
        "    ctx.beginPath();ctx.moveTo(sx,sy);"
        "    ctx.lineTo((p.pTL[0]+p.pTR[0])/2,(p.pTL[1]+p.pTR[1])/2);"
        "    ctx.stroke();"
        "  }"
        "  ctx.restore();"
        "}"
        "function sunPos(hour){"
        "  var t=Math.max(0,Math.min(1,(hour-6)/12));"
        "  var P0=[W*0.05,H*0.85],P1=[W*0.50,H*0.08],P2=[W*0.95,H*0.85];"
        "  return [(1-t)*(1-t)*P0[0]+2*(1-t)*t*P1[0]+t*t*P2[0],(1-t)*(1-t)*P0[1]+2*(1-t)*t*P1[1]+t*t*P2[1]];"
        "}"
        "function drawSun(hour,f){"
        "  if(hour<6||hour>18) return;"
        "  var sp=sunPos(hour);var sx=sp[0],sy=sp[1];var op=0.3+f*0.7;"
        "  var grd=ctx.createRadialGradient(sx,sy,0,sx,sy,90);"
        "  grd.addColorStop(0,'rgba(252,211,77,'+(op*0.9)+')');"
        "  grd.addColorStop(0.4,'rgba(245,158,11,'+(op*0.3)+')');"
        "  grd.addColorStop(1.0,'rgba(245,158,11,0)');"
        "  ctx.beginPath();ctx.arc(sx,sy,90,0,Math.PI*2);ctx.fillStyle=grd;ctx.fill();"
        "  var core=ctx.createRadialGradient(sx,sy,0,sx,sy,22);"
        "  core.addColorStop(0,'#FEFCE8');core.addColorStop(0.5,'#FCD34D');core.addColorStop(1.0,'#F59E0B');"
        "  ctx.beginPath();ctx.arc(sx,sy,22,0,Math.PI*2);ctx.fillStyle=core;ctx.fill();"
        "  ctx.save();ctx.translate(sx,sy);"
        "  ctx.strokeStyle='rgba(252,211,77,'+(op*0.6)+')';ctx.lineWidth=2;"
        "  for(var a=0;a<8;a++){"
        "    var ang=a*Math.PI/4;"
        "    ctx.beginPath();ctx.moveTo(Math.cos(ang)*28,Math.sin(ang)*28);"
        "    ctx.lineTo(Math.cos(ang)*44,Math.sin(ang)*44);ctx.stroke();"
        "  }"
        "  ctx.restore();"
        "}"
        "function drawSky(f){"
        "  var r1=Math.round(2+f*6),g1=Math.round(10+f*12),b1=Math.round(30+f*30);"
        "  var r2=Math.round(8+f*7),g2=Math.round(18+f*22),b2=Math.round(50+f*40);"
        "  var sg=ctx.createLinearGradient(0,0,0,H);"
        "  sg.addColorStop(0,'rgb('+r1+','+g1+','+b1+')');"
        "  sg.addColorStop(1,'rgb('+r2+','+g2+','+b2+')');"
        "  ctx.fillStyle=sg;ctx.fillRect(0,0,W,H);"
        "  var grd=ctx.createLinearGradient(0,H*0.7,0,H);"
        "  grd.addColorStop(0,'#0D1F0D');grd.addColorStop(1,'#060E06');"
        "  ctx.fillStyle=grd;ctx.fillRect(0,H*0.65,W,H*0.35);"
        "  ctx.strokeStyle='rgba(16,185,129,0.1)';ctx.lineWidth=0.5;"
        "  for(var gx=-2;gx<=COLS+2;gx+=2){"
        "    var p1=iso(gx*(PW+PG),0,0),p2=iso(gx*(PW+PG),(ROWS*(PH+PG)*0.5+3),0);"
        "    ctx.beginPath();ctx.moveTo(p1[0],p1[1]);ctx.lineTo(p2[0],p2[1]);ctx.stroke();"
        "  }"
        "  for(var gy=0;gy<=ROWS*(PH+PG)*0.5+3;gy+=2){"
        "    var q1=iso(0,gy,0),q2=iso((COLS+1)*(PW+PG),gy,0);"
        "    ctx.beginPath();ctx.moveTo(q1[0],q1[1]);ctx.lineTo(q2[0],q2[1]);ctx.stroke();"
        "  }"
        "}"
        "function drawSunPath(){"
        "  ctx.beginPath();"
        "  for(var s=0;s<=30;s++){var h=6+s*12/30;var p=sunPos(h);s===0?ctx.moveTo(p[0],p[1]):ctx.lineTo(p[0],p[1]);}"
        "  ctx.strokeStyle='rgba(245,158,11,0.10)';ctx.lineWidth=1.5;"
        "  ctx.setLineDash([4,8]);ctx.stroke();ctx.setLineDash([]);"
        "}"
        "function irr(hour){if(hour<6||hour>18) return 0;return 1050*Math.sin(Math.PI*(hour-6)/12);}"
        "function cellT(ir){var wms=WKH/3.6;return AMB+(45-20)*(ir/800)/(1+wms*0.035);}"
        "function powerKW(ir){var ct=cellT(ir);var tl=Math.max(0,1-Math.max(0,ct-25)*(TC/100));return SYS*(ir/1000)*0.975*tl*0.965;}"
        "var simH=6.0,SPEED=0.03;"
        "function frame(){"
        "  simH+=SPEED;if(simH>=24) simH=0;"
        "  var ir=irr(simH),f=ir/1050,pw=powerKW(ir),ct=cellT(ir);"
        "  ctx.clearRect(0,0,W,H);"
        "  drawSky(f);drawSunPath();drawSun(simH,f);"
        "  var wf=0.8+(WKH/120)*1.5;updateWP(wf);drawWP(wf);"
        "  var geoms=[];var pIdx=0;"
        "  for(var row=ROWS-1;row>=0;row--){"
        "    for(var col=0;col<COLS;col++){"
        "      if(pIdx>=NP) break;"
        "      var wx=col*(PW+PG),wy=row*(PH*Math.cos(TRAD)+0.3),wz=0.8;"
        "      var lh=0.8+row*0.12;"
        "      drawLeg(wx+0.15,wy+0.15,lh);drawLeg(wx+0.85,wy+0.15,lh);"
        "      if(col<COLS-1) drawRail(wx,wy+0.12,lh+0.02,PW+PG);"
        "      drawRail(wx-0.05,wy+0.10,lh,PW+PG*0.8);"
        "      drawBolt(wx+0.5,wy+0.12,lh+0.06);"
        "      geoms.push(drawPanel(wx,wy,wz,f));pIdx++;"
        "    }"
        "  }"
        "  if(simH>=6&&simH<=18){var sp=sunPos(simH);drawBeams(sp[0],sp[1],f,geoms);}"
        "  var hh=Math.floor(simH).toString().padStart(2,'0');"
        "  var mm=Math.floor((simH-Math.floor(simH))*60).toString().padStart(2,'0');"
        "  document.getElementById('hTime').textContent=hh+':'+mm;"
        "  document.getElementById('hIrr').textContent=Math.round(ir)+' W/m2';"
        "  document.getElementById('hPow').textContent=pw.toFixed(2)+' kW';"
        "  document.getElementById('hTemp').textContent=ct.toFixed(1)+'C';"
        "  document.getElementById('if').style.width=(f*100)+'%';"
        "  requestAnimationFrame(frame);"
        "}"
        "requestAnimationFrame(frame);"
        "</script></body></html>"
    )
    components.html(_html3d, height=640, scrolling=False)
    st.markdown(f"<div class='card'><h4>3D Array Layout</h4><p>Array: <strong>{anim_rows} rows x {anim_cols} cols</strong> = <strong>{p_qty} panels</strong> | Area: <strong>{p_qty*2.1:.1f} m2</strong></p><p>Strings: <strong>{strings} x {pps} panels</strong> | String VOC: <strong>{voc_str:.0f} V</strong> | Tilt: <strong>{tilt}deg</strong></p><p>Structure: <strong>{struct['type']}</strong> | Material: <strong>{struct['material']}</strong></p></div>",unsafe_allow_html=True)
'''

all_tab1 = tab1_part1 + tab1_html_builder

with open("/home/claude/solarx/tab1.py", "w") as f:
    f.write(all_tab1)
print("tab1 written:", os.path.getsize("/home/claude/solarx/tab1.py"))
PYEOF
python3 /home/claude/write_tab1.py
Output

tab1 written: 16068

Write FEA tab with truss and remaining tabs

Script
Done

bash

cat > /home/claude/write_tab2_onwards.py << 'PYEOF'
import os

# TAB 2: FEA + Truss simulation
tab2 = r'''
# ── TAB 2: Wind FEA + Truss ──────────────────────────────────────────────────
with tabs[2]:
    st.markdown("<span class='lbl'>SolidWorks-Class FEA Wind Load Simulation</span>",unsafe_allow_html=True)
    
    # TRUSS CONTROL
    st.markdown("### 🔩 Structural Reinforcement — Interactive Truss Addition")
    tc1,tc2,tc3=st.columns([2,1,1])
    with tc1:
        st.markdown("<div class='info'><b>Interactive Truss Addition:</b> Toggle Warren-pattern diagonal truss members to see real-time effect on Von Mises stress and safety factor. Truss reduces bending by ~45% through load redistribution.</div>",unsafe_allow_html=True)
    with tc2:
        add_truss=st.toggle("+ Add Warren Truss",value=st.session_state["truss_on"],help="Add diagonal truss members to reduce stress")
        st.session_state["truss_on"]=add_truss
    with tc3:
        truss_mat=st.selectbox("Truss Material",["Q235 Steel","S355 Steel","6061-T6 Aluminum"])

    cur_fea=fea_truss if add_truss else fea_no_truss
    if add_truss:
        red=((fea_no_truss["von_mises"]-fea_truss["von_mises"])/max(fea_no_truss["von_mises"],0.001))*100
        st.markdown(f"<div class='ok'>✅ <b>Warren Truss Active ({truss_mat})</b> — Von Mises reduced from <b>{fea_no_truss['von_mises']:.1f} MPa</b> to <b>{fea_truss['von_mises']:.1f} MPa</b> (−{red:.1f}% reduction). SF improved: <b>{fea_no_truss['sf']:.2f}</b> → <b>{fea_truss['sf']:.2f}</b></div>",unsafe_allow_html=True)
    else:
        st.markdown("<div class='info'>Toggle <b>Add Warren Truss</b> above to see structural reinforcement in real-time on the 3D simulation below.</div>",unsafe_allow_html=True)

    st.markdown(f"<div class='info'>FEA simulation: Von Mises stress — <b style='color:#10B981'>Green=Safe</b> → <b style='color:#F59E0B'>Yellow=Caution</b> → <b style='color:#EF4444'>Red=Yield</b> | Wind: {wind:.0f} km/h | Tilt: {tilt}° | Panels: {p_qty}</div>",unsafe_allow_html=True)

    # Build FEA HTML with pure string concatenation (NO f-strings with JS)
    _fvm=str(cur_fea["von_mises"])
    _fb=str(cur_fea["bending"])
    _fa=str(cur_fea["axial"])
    _fyld=str(cur_fea["yield"])
    _fsf=str(cur_fea["sf"])
    _ftruss="true" if add_truss else "false"
    _ffail="YIELD FAILURE" if cur_fea["fail"] else "SAFE"
    _sf_class="cf" if cur_fea["sf"]<1.5 else "co"
    _fail_class="cf" if cur_fea["fail"] else "co"
    _wind_js=str(round(wind,1))
    _tilt_js=str(tilt)
    _rows_fea=str(min(anim_rows,4))
    _cols_fea=str(min(anim_cols,5))
    _fstruct=struct["material"][:28]
    _ffound=struct["foundation"]
    _fzone=wind_zone
    _ftruss_label="Warren Truss ACTIVE" if add_truss else "No Truss"
    _fyld25=str(int(cur_fea["yield"]*0.25))
    _fyld50=str(int(cur_fea["yield"]*0.50))
    _fyld75=str(int(cur_fea["yield"]*0.75))

    _fea_html=(
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        "<style>*{margin:0;padding:0;box-sizing:border-box;}"
        "body{background:#020B1A;font-family:'Segoe UI',sans-serif;overflow:hidden;}"
        "canvas{display:block;}"
        "#ctrl{position:absolute;top:8px;left:8px;background:rgba(5,14,37,0.92);border:1px solid rgba(245,158,11,0.25);"
        "border-radius:10px;padding:12px 16px;color:#94A3B8;font-size:11px;min-width:200px;}"
        ".cr{display:flex;justify-content:space-between;margin:4px 0;}"
        ".cv{color:#F59E0B;font-weight:700;}.co{color:#10B981;}.cf{color:#EF4444;}"
        "#cbar{position:absolute;right:10px;top:10px;background:rgba(5,14,37,0.88);"
        "border:1px solid rgba(245,158,11,0.2);border-radius:10px;padding:10px;font-size:10px;color:#94A3B8;}"
        "#bot2{position:absolute;bottom:0;left:0;right:0;background:rgba(5,14,37,0.88);"
        "border-top:1px solid rgba(245,158,11,0.2);padding:8px 16px;display:flex;gap:24px;font-size:10px;color:#64748B;flex-wrap:wrap;}"
        ".bv{color:#94A3B8;font-weight:700;}"
        "</style></head><body><canvas id='fea'></canvas>"
        "<div id='ctrl'>"
        "<div style='color:#F59E0B;font-weight:700;font-size:12px;margin-bottom:8px'>FEA RESULTS</div>"
        "<div class='cr'><span>Von Mises:</span><span class='cv'>" + _fvm + " MPa</span></div>"
        "<div class='cr'><span>Bending:</span><span class='cv'>" + _fb + " MPa</span></div>"
        "<div class='cr'><span>Axial:</span><span class='cv'>" + _fa + " MPa</span></div>"
        "<div class='cr'><span>Yield Str:</span><span class='cv'>" + _fyld + " MPa</span></div>"
        "<div class='cr'><span>Safety Factor:</span><span class='" + _sf_class + "'>" + _fsf + "</span></div>"
        "<div class='cr'><span>Status:</span><span class='" + _fail_class + "'>" + _ffail + "</span></div>"
        "<div class='cr'><span>Truss:</span><span class='" + ("co" if add_truss else "cv") + "'>" + ("ACTIVE" if add_truss else "OFF") + "</span></div>"
        "<div style='margin-top:10px;color:#475569;font-size:9px'>"
        "Wind: <span style='color:#F59E0B'>" + _wind_js + " km/h</span> | Tilt: <span style='color:#F59E0B'>" + _tilt_js + "deg</span><br>"
        "EN 1991-1-4 / IEC 61215 / Warren Truss"
        "</div></div>"
        "<div id='cbar'>"
        "<div style='color:#F59E0B;font-weight:700;font-size:9px;text-align:center'>σ MPa</div>"
        "<div style='display:flex;gap:6px;align-items:center'>"
        "<canvas id='cb' width='18' height='140'></canvas>"
        "<div style='display:flex;flex-direction:column;justify-content:space-between;height:140px;font-size:9px'>"
        "<span>" + _fyld + " Yld</span><span>" + _fyld75 + "</span><span>" + _fyld50 + "</span><span>" + _fyld25 + "</span><span>0</span>"
        "</div></div></div>"
        "<div id='bot2'>"
        "<div>Material:<span class='bv'>" + _fstruct + "</span></div>"
        "<div>Foundation:<span class='bv'>" + _ffound + "</span></div>"
        "<div>Zone:<span class='bv'>" + _fzone + "</span></div>"
        "<div>Truss:<span class='bv'>" + _ftruss_label + "</span></div>"
        "</div>"
        "<script>"
        "var cv=document.getElementById('fea'),ctx=cv.getContext('2d');"
        "cv.width=window.innerWidth;cv.height=window.innerHeight-40;"
        "var YIELD=" + _fyld + ",VM=" + _fvm + ",BEND=" + _fb + ",AXIAL=" + _fa + ",SF=" + _fsf + ";"
        "var WIND=" + _wind_js + ",TILT=" + _tilt_js + ",ROWS=" + _rows_fea + ",COLS=" + _cols_fea + ";"
        "var HAS_TRUSS=" + _ftruss + ";"
        "var cb=document.getElementById('cb'),cbc=cb.getContext('2d');"
        "var grad=cbc.createLinearGradient(0,0,0,140);"
        "grad.addColorStop(0,'#EF4444');grad.addColorStop(0.25,'#F97316');"
        "grad.addColorStop(0.5,'#F59E0B');grad.addColorStop(0.75,'#84CC16');grad.addColorStop(1.0,'#10B981');"
        "cbc.fillStyle=grad;cbc.fillRect(0,0,18,140);"
        "var ISO=Math.PI/6,SC=Math.min(cv.width,cv.height)*0.028,CX=cv.width*0.42,CY=cv.height*0.55;"
        "function iso(wx,wy,wz){return [CX+(wx-wy)*Math.cos(ISO)*SC,CY-wz*SC+(wx+wy)*Math.sin(ISO)*SC*0.55];}"
        "function lerp(a,b,t){return a+(b-a)*t;}"
        "function feaColor(frac,alpha){"
        "  frac=Math.max(0,Math.min(1,frac));var r,g,b;"
        "  if(frac<0.5){var t=frac*2;r=Math.round(lerp(16,245,t));g=Math.round(lerp(185,158,t));b=Math.round(lerp(129,11,t));}"
        "  else{var t=(frac-0.5)*2;r=Math.round(lerp(245,239,t));g=Math.round(lerp(158,68,t));b=Math.round(lerp(11,68,t));}"
        "  return 'rgba('+r+','+g+','+b+','+(alpha||1.0)+')';"
        "}"
        "function feaMember(x1,y1,z1,x2,y2,z2,th,sLo,sHi){"
        "  var steps=8,tw=th*0.5;"
        "  for(var s=0;s<steps;s++){"
        "    var t0=s/steps,t1=(s+1)/steps;"
        "    var mx0=x1+(x2-x1)*t0,my0=y1+(y2-y1)*t0,mz0=z1+(z2-z1)*t0;"
        "    var mx1=x1+(x2-x1)*t1,my1=y1+(y2-y1)*t1,mz1=z1+(z2-z1)*t1;"
        "    var stress=sLo+(sHi-sLo)*((t0+t1)/2);"
        "    var col=feaColor(Math.min(1,stress/YIELD),0.92);"
        "    var p=[iso(mx0-tw,my0,mz0),iso(mx1-tw,my1,mz1),iso(mx1+tw,my1,mz1),iso(mx0+tw,my0,mz0)];"
        "    ctx.beginPath();ctx.moveTo(p[0][0],p[0][1]);"
        "    for(var i=1;i<p.length;i++) ctx.lineTo(p[i][0],p[i][1]);"
        "    ctx.closePath();ctx.fillStyle=col;ctx.fill();"
        "    ctx.strokeStyle='rgba(0,0,0,0.2)';ctx.lineWidth=0.3;ctx.stroke();"
        "  }"
        "}"
        "function drawArrow(x,y,len,col){"
        "  ctx.save();ctx.translate(x,y);"
        "  ctx.strokeStyle=col;ctx.fillStyle=col;ctx.lineWidth=2;"
        "  ctx.beginPath();ctx.moveTo(0,0);ctx.lineTo(len,0);ctx.stroke();"
        "  ctx.beginPath();ctx.moveTo(len,0);ctx.lineTo(len-8,-5);ctx.lineTo(len-8,5);ctx.closePath();ctx.fill();"
        "  ctx.restore();"
        "}"
        "var tick=0;"
        "function drawFrame(){"
        "  tick++;ctx.clearRect(0,0,cv.width,cv.height);"
        "  var bg=ctx.createLinearGradient(0,0,0,cv.height);"
        "  bg.addColorStop(0,'#020B1A');bg.addColorStop(1,'#030F22');"
        "  ctx.fillStyle=bg;ctx.fillRect(0,0,cv.width,cv.height);"
        "  ctx.strokeStyle='rgba(30,58,138,0.3)';ctx.lineWidth=0.5;"
        "  for(var gx=-2;gx<=COLS*2+2;gx++){var p1=iso(gx,-1,0),p2=iso(gx,ROWS*1.5+1,0);ctx.beginPath();ctx.moveTo(p1[0],p1[1]);ctx.lineTo(p2[0],p2[1]);ctx.stroke();}"
        "  for(var gy=-1;gy<=ROWS*1.5+1;gy++){var q1=iso(-2,gy,0),q2=iso(COLS*2+2,gy,0);ctx.beginPath();ctx.moveTo(q1[0],q1[1]);ctx.lineTo(q2[0],q2[1]);ctx.stroke();}"
        "  var wf=Math.min(1,WIND/160),vmf=Math.min(1,VM/YIELD);"
        "  for(var row=ROWS-1;row>=0;row--){"
        "    for(var col=0;col<COLS;col++){"
        "      var bx=col*2.2,by=row*2.0,lh=1.2+row*0.1;"
        "      var sb=VM*(0.9+Math.sin(tick*0.04+col+row)*0.05);"
        "      var sm=sb*0.65,st=sb*0.25;"
        "      // Foundation"
        "      var fb=[iso(bx-0.1,by-0.1,-0.2),iso(bx+0.5,by-0.1,-0.2),iso(bx+0.5,by+0.5,-0.2),iso(bx-0.1,by+0.5,-0.2)];"
        "      ctx.beginPath();ctx.moveTo(fb[0][0],fb[0][1]);"
        "      for(var fi=1;fi<fb.length;fi++) ctx.lineTo(fb[fi][0],fb[fi][1]);"
        "      ctx.closePath();ctx.fillStyle=feaColor(Math.min(1,sb*0.4/YIELD),0.88);ctx.fill();"
        "      ctx.strokeStyle='rgba(0,0,0,0.3)';ctx.lineWidth=0.5;ctx.stroke();"
        "      // Legs"
        "      feaMember(bx+0.1,by+0.1,0,bx+0.1,by+0.1,lh,0.1,sb,sm);"
        "      feaMember(bx+0.9,by+0.1,0,bx+0.9,by+0.1,lh,0.1,sb,sm);"
        "      // Cross brace"
        "      feaMember(bx+0.1,by+0.1,lh*0.4,bx+0.9,by+0.1,lh*0.4,0.06,sm*0.6,sm*0.8);"
        "      // Rail"
        "      feaMember(bx,by+0.1,lh,bx+1.0,by+0.1,lh,0.07,sm,sb*0.9);"
        "      // WARREN TRUSS DIAGONALS - rendered only if HAS_TRUSS"
        "      if(HAS_TRUSS){"
        "        // Diagonal 1 (bottom-left to top-right)"
        "        feaMember(bx+0.1,by+0.1,0,bx+0.9,by+0.1,lh,0.05,sb*0.28,sm*0.18);"
        "        // Diagonal 2 (bottom-right to top-left)"
        "        feaMember(bx+0.9,by+0.1,0,bx+0.1,by+0.1,lh,0.05,sb*0.28,sm*0.18);"
        "        // Mid horizontal"
        "        feaMember(bx+0.1,by+0.1,lh*0.5,bx+0.9,by+0.1,lh*0.5,0.04,sm*0.22,sm*0.28);"
        "        // Glow overlay"
        "        ctx.save();ctx.globalAlpha=0.18+0.08*Math.sin(tick*0.05);"
        "        var t1p=iso(bx+0.1,by+0.1,0),t2p=iso(bx+0.9,by+0.1,lh);"
        "        ctx.beginPath();ctx.moveTo(t1p[0],t1p[1]);ctx.lineTo(t2p[0],t2p[1]);"
        "        ctx.strokeStyle='#10B981';ctx.lineWidth=3;ctx.stroke();"
        "        var t3p=iso(bx+0.9,by+0.1,0),t4p=iso(bx+0.1,by+0.1,lh);"
        "        ctx.beginPath();ctx.moveTo(t3p[0],t3p[1]);ctx.lineTo(t4p[0],t4p[1]);"
        "        ctx.strokeStyle='#10B981';ctx.lineWidth=3;ctx.stroke();"
        "        ctx.restore();"
        "      }"
        "      // Panel face"
        "      var sT=Math.sin(TILT*Math.PI/180),cT=Math.cos(TILT*Math.PI/180);"
        "      var pBL=iso(bx,by+0.1,lh),pBR=iso(bx+1.0,by+0.1,lh);"
        "      var pTR=iso(bx+1.0,by+0.1-1.4*sT,lh+1.4*cT),pTL=iso(bx,by+0.1-1.4*sT,lh+1.4*cT);"
        "      ctx.beginPath();ctx.moveTo(pBL[0],pBL[1]);ctx.lineTo(pBR[0],pBR[1]);ctx.lineTo(pTR[0],pTR[1]);ctx.lineTo(pTL[0],pTL[1]);ctx.closePath();"
        "      var pg=ctx.createLinearGradient(pBL[0],pBL[1],pTR[0],pTR[1]);"
        "      pg.addColorStop(0,feaColor(vmf*0.6,0.85));pg.addColorStop(0.5,feaColor(vmf*0.85,0.75));pg.addColorStop(1.0,feaColor(vmf*0.25,0.65));"
        "      ctx.fillStyle=pg;ctx.fill();ctx.strokeStyle='rgba(245,158,11,0.4)';ctx.lineWidth=1.0;ctx.stroke();"
        "      // Bolts"
        "      var bpts=[[bx+0.1,lh],[bx+0.9,lh]];"
        "      for(var bi=0;bi<bpts.length;bi++){"
        "        var bp=iso(bpts[bi][0],by+0.1,bpts[bi][1]);"
        "        ctx.beginPath();ctx.arc(bp[0],bp[1],4,0,Math.PI*2);"
        "        ctx.fillStyle=feaColor(Math.min(1,st/YIELD),1.0);ctx.fill();"
        "        ctx.strokeStyle='rgba(0,0,0,0.5)';ctx.lineWidth=0.8;ctx.stroke();"
        "      }"
        "      // Wind force arrows on panel"
        "      if(WIND>30){"
        "        var mx=(pBL[0]+pTL[0]+pBR[0]+pTR[0])/4,my=(pBL[1]+pTL[1]+pBR[1]+pTR[1])/4;"
        "        var al=12+wf*20,pl=0.7+0.3*Math.sin(tick*0.08+col*0.7+row*0.5);"
        "        ctx.globalAlpha=pl;"
        "        drawArrow(mx,my,al,'rgba(6,182,212,0.9)');"
        "        ctx.globalAlpha=1.0;"
        "      }"
        "    }"
        "  }"
        "  // Scene wind arrows"
        "  for(var wa=0;wa<5;wa++){"
        "    var wp=iso(-1.5,wa*0.8+0.5,1.5+wa*0.3);"
        "    var al2=30+wf*50,wal=0.3+0.4*Math.sin(tick*0.07+wa);"
        "    drawArrow(wp[0],wp[1],al2,'rgba(6,182,212,'+wal.toFixed(2)+')');"
        "    if(wa===2){ctx.fillStyle='rgba(6,182,212,0.7)';ctx.font='bold 10px Segoe UI';ctx.fillText('W: '+WIND+' km/h',wp[0]+al2+6,wp[1]+4);}"
        "  }"
        "  // SF badge"
        "  var sfc=SF>=2.0?'#10B981':(SF>=1.5?'#F59E0B':'#EF4444');"
        "  var sfp=iso(COLS*2+0.5,-0.5,2.5);"
        "  ctx.save();ctx.fillStyle='rgba(5,14,37,0.9)';"
        "  ctx.beginPath();"
        "  if(ctx.roundRect){ctx.roundRect(sfp[0]-60,sfp[1]-20,120,40,8);}else{ctx.rect(sfp[0]-60,sfp[1]-20,120,40);}"
        "  ctx.fill();ctx.strokeStyle=sfc;ctx.lineWidth=1.5;ctx.stroke();"
        "  ctx.fillStyle=sfc;ctx.font='bold 13px Segoe UI';ctx.textAlign='center';"
        "  ctx.fillText('SF = '+SF.toFixed(2),sfp[0],sfp[1]+2);"
        "  ctx.fillStyle='#64748B';ctx.font='9px Segoe UI';"
        "  ctx.fillText(HAS_TRUSS?'WARREN TRUSS ACTIVE':'NO TRUSS',sfp[0],sfp[1]+16);"
        "  ctx.restore();"
        "  // Stress hotspot glow at failure"
        "  if(vmf>0.7&&!HAS_TRUSS){"
        "    var lb2=iso(0.1,0.1,0),pl2=0.6+0.4*Math.sin(tick*0.06);"
        "    var grd2=ctx.createRadialGradient(lb2[0],lb2[1],0,lb2[0],lb2[1],40);"
        "    grd2.addColorStop(0,'rgba(239,68,68,'+(pl2*0.6)+')');"
        "    grd2.addColorStop(0.5,'rgba(239,68,68,'+(pl2*0.2)+')');"
        "    grd2.addColorStop(1.0,'rgba(239,68,68,0)');"
        "    ctx.beginPath();ctx.arc(lb2[0],lb2[1],40,0,Math.PI*2);ctx.fillStyle=grd2;ctx.fill();"
        "  }"
        "  requestAnimationFrame(drawFrame);"
        "}"
        "requestAnimationFrame(drawFrame);"
        "</script></body></html>"
    )
    components.html(_fea_html, height=600, scrolling=False)

    st.divider()
    st.markdown("<span class='lbl'>FEA Comparison: No Truss vs Warren Truss</span>",unsafe_allow_html=True)
    cc1,cc2=st.columns(2)
    with cc1:
        st.markdown("**Without Truss**")
        fa=st.columns(3)
        fa[0].metric("Von Mises",f"{fea_no_truss['von_mises']:.2f} MPa")
        fa[1].metric("Safety Factor",f"{fea_no_truss['sf']:.2f}")
        fa[2].metric("Status","⚠️ FAIL" if fea_no_truss["fail"] else "✅ SAFE")
    with cc2:
        st.markdown("**With Warren Truss**")
        fb=st.columns(3)
        fb[0].metric("Von Mises",f"{fea_truss['von_mises']:.2f} MPa",delta=f"-{fea_no_truss['von_mises']-fea_truss['von_mises']:.1f}",delta_color="inverse")
        fb[1].metric("Safety Factor",f"{fea_truss['sf']:.2f}",delta=f"+{fea_truss['sf']-fea_no_truss['sf']:.2f}")
        fb[2].metric("Status","⚠️ FAIL" if fea_truss["fail"] else "✅ SAFE")

    tilts_w=list(range(0,61,5))
    vm_nt=[calc_fea_stress(wind,t,p_qty,struct,False)["von_mises"] for t in tilts_w]
    vm_wt=[calc_fea_stress(wind,t,p_qty,struct,True)["von_mises"] for t in tilts_w]
    fig_cmp=go.Figure()
    fig_cmp.add_trace(go.Scatter(x=tilts_w,y=vm_nt,name="No Truss",line=dict(color='#EF4444',width=2.5),fill='tozeroy',fillcolor='rgba(239,68,68,0.08)'))
    fig_cmp.add_trace(go.Scatter(x=tilts_w,y=vm_wt,name="Warren Truss",line=dict(color='#10B981',width=2.5),fill='tozeroy',fillcolor='rgba(16,185,129,0.08)'))
    fig_cmp.add_hline(y=struct["yield_mpa"],line_dash="dash",line_color="#F59E0B",annotation_text=f"Yield: {struct['yield_mpa']} MPa")
    fig_cmp.add_vline(x=tilt,line_dash="dot",line_color="#F59E0B",annotation_text=f"Current {tilt}deg")
    fig_cmp.update_layout(height=320,title="Von Mises: No Truss vs Warren Truss",plot_bgcolor='rgba(11,20,55,0.6)',paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#94A3B8'),legend=dict(bgcolor='rgba(15,32,87,0.5)'),
        xaxis=dict(title="Tilt Angle (deg)",gridcolor='rgba(255,255,255,0.05)'),
        yaxis=dict(title="Von Mises Stress (MPa)",gridcolor='rgba(255,255,255,0.05)'))
    st.plotly_chart(fig_cmp,use_container_width=True)

    hm_sp=[20,40,60,80,100,120,140,160]
    hm_t=[0,10,15,20,25,30,40,60]
    z_vm=[[calc_fea_stress(sp,t,p_qty,struct,add_truss)["von_mises"] for sp in hm_sp] for t in hm_t]
    fig_heat=go.Figure(data=go.Heatmap(z=z_vm,x=hm_sp,y=hm_t,
        colorscale=[[0,'#10B981'],[0.4,'#F59E0B'],[0.7,'#F97316'],[1.0,'#EF4444']],
        hovertemplate='Speed:%{x}km/h Tilt:%{y}deg VM:%{z:.1f}MPa<extra></extra>',
        colorbar=dict(title=dict(text='Von Mises MPa',font=dict(color='#94A3B8')))))
    fig_heat.update_layout(height=280,title=f"Stress Heatmap ({'With Truss' if add_truss else 'No Truss'})",
        plot_bgcolor='rgba(11,20,55,0.6)',paper_bgcolor='rgba(0,0,0,0)',font=dict(color='#94A3B8'),
        xaxis=dict(title="Wind Speed (km/h)"),yaxis=dict(title="Tilt (deg)"))
    st.plotly_chart(fig_heat,use_container_width=True)

    sc1,sc2,sc3,sc4=st.columns(4)
    with sc1: st.markdown(f"<div class='card'><h4>Frame</h4><p>Type:<strong>{struct['type']}</strong></p><p>Max Tilt:<strong>{struct['tilt_max']}deg</strong></p></div>",unsafe_allow_html=True)
    with sc2: st.markdown(f"<div class='card'><h4>Material</h4><p><strong>{struct['material']}</strong></p><p>Yield:<strong>{struct['yield_mpa']} MPa</strong></p><p>E:<strong>{struct['E_gpa']} GPa</strong></p></div>",unsafe_allow_html=True)
    with sc3: st.markdown(f"<div class='card'><h4>Foundation</h4><p>{struct['foundation']}</p><p>Clamp:<strong>{struct['clamp']}</strong></p></div>",unsafe_allow_html=True)
    with sc4:
        scol="#EF4444" if cur_fea["fail"] else("#F59E0B" if cur_fea["sf"]<2 else "#10B981")
        st.markdown(f"<div class='card'><h4>Safety</h4><p>SF:<strong style='color:{scol}'>{cur_fea['sf']:.2f}</strong></p><p>{'Warren Truss ON' if add_truss else 'No Truss'}</p></div>",unsafe_allow_html=True)
    if cur_fea["fail"]: st.markdown(f"<div class='err'>⚠️ STRUCTURAL FAILURE: {cur_fea['von_mises']:.1f} MPa exceeds yield {cur_fea['yield']} MPa. Add truss or upgrade structure.</div>",unsafe_allow_html=True)
    elif cur_fea["sf"]<1.5: st.markdown(f"<div class='warn'>⚠️ Low SF {cur_fea['sf']:.2f} < 1.5. Enable Warren Truss or upgrade structure class.</div>",unsafe_allow_html=True)
    else: st.markdown(f"<div class='ok'>✅ Structure passes FEA. SF {cur_fea['sf']:.2f} >= 1.5. EN 1991-1-4 envelope OK.</div>",unsafe_allow_html=True)
'''

tab_rest = r'''
# ── TAB 3: Technical Specs ────────────────────────────────────────────────────
with tabs[3]:
    st.markdown("<span class='lbl'>Full System Technical Specifications</span>",unsafe_allow_html=True)
    tc1,tc2,tc3=st.columns(3)
    with tc1: st.markdown(f"<div class='card'><h4>Panel Specs</h4><p>Model:<strong>{panel_type}</strong></p><p>Efficiency:<strong>{p_eff}%</strong></p><p>VOC:<strong>{voc} V</strong></p><p>ISC:<strong>{isc} A</strong></p><p>Temp Coeff:<strong>{p_temp}%/degC</strong></p><p>Grade:<strong>{p_note}</strong></p></div>",unsafe_allow_html=True)
    with tc2: st.markdown(f"<div class='card'><h4>Array Config</h4><p>Total:<strong>{p_qty}</strong></p><p>Strings:<strong>{strings}</strong></p><p>Per String:<strong>{pps}</strong></p><p>Area:<strong>{p_qty*2.1:.1f} m2</strong></p><p>Capacity:<strong>{sys_size:.2f} kWp</strong></p></div>",unsafe_allow_html=True)
    with tc3:
        src="LIVE" if weather["live"] else "DB"
        st.markdown(f"<div class='card'><h4>Operating Conditions</h4><p>Tilt:<strong>{tilt}deg</strong> Azimuth:<strong>{azimuth}deg</strong></p><p>Temp:<strong>{temp_amb:.1f}C</strong> [{src}]</p><p>GHI:<strong>{sun_h:.2f} kWh/m2/day</strong> [{src}]</p><p>Wind:<strong>{wind:.0f} km/h</strong> [{src}]</p><p>Losses:<strong>{sys_loss}%</strong></p></div>",unsafe_allow_html=True)
    st.divider()
    pr_losses={"Temperature Loss":abs(p_temp/100*max(0,temp_amb-25))*100,"Cable":vd_pct,"Soiling":float(soiling),"System":float(sys_loss-soiling_adv),"Inverter":float(100-inv_eff)}
    fig_pr=go.Figure(go.Waterfall(name="PR",orientation="v",measure=["absolute"]+["relative"]*len(pr_losses)+["total"],
        x=["Ideal 100%"]+list(pr_losses.keys())+["Performance Ratio"],y=[100]+[-v for v in pr_losses.values()]+[None],
        connector={"line":{"color":"rgba(245,158,11,0.3)"}},decreasing={"marker":{"color":"#EF4444","opacity":0.8}},totals={"marker":{"color":"#F59E0B"}}))
    fig_pr.update_layout(height=320,title="Performance Ratio Waterfall",plot_bgcolor='rgba(11,20,55,0.6)',paper_bgcolor='rgba(0,0,0,0)',font=dict(color='#94A3B8'))
    st.plotly_chart(fig_pr,use_container_width=True)

# ── TAB 4: Inverter ───────────────────────────────────────────────────────────
with tabs[4]:
    st.markdown("<span class='lbl'>Inverter & Grid Interface</span>",unsafe_allow_html=True)
    ic1,ic2,ic3=st.columns(3)
    ic1.metric("Inverter",inverter_type,inv_note);ic2.metric("Efficiency",f"{inv_eff}%");ic3.metric("Grid",f"{grid_v}V / {grid_f}Hz")
    st.divider()
    i1,i2,i3,i4=st.columns(4)
    i1.metric("VOC",f"{voc_str:.0f} V");i2.metric("MPPT",f"{mppt_v:.0f} V");i3.metric("ISC",f"{isc_str:.1f} A");i4.metric("AC Out",f"{sys_size*inv_eff/100:.2f} kWp")

# ── TAB 5: Battery ────────────────────────────────────────────────────────────
with tabs[5]:
    st.markdown("<span class='lbl'>Battery Energy Storage</span>",unsafe_allow_html=True)
    if has_batt:
        bm1,bm2,bm3,bm4=st.columns(4)
        bm1.metric("Chemistry",battery_type,b_note);bm2.metric("Capacity",f"{b_cap:.1f} kWh",f"V:{b_voltage}V")
        bm3.metric("Usable",f"{usable:.1f} kWh",f"DoD:{dod}%");bm4.metric("Backup",f"{autonomy:.1f} hrs")
        fig_soc=go.Figure()
        fig_soc.add_trace(go.Scatter(x=list(hrs),y=soc,name="Battery SOC",fill='tozeroy',fillcolor='rgba(16,185,129,0.15)',line=dict(color='#10B981',width=3)))
        fig_soc.add_hline(y=b_cap*(dod/100),line_dash="dash",line_color="#F59E0B",annotation_text=f"Full Usable: {b_cap*(dod/100):.1f} kWh")
        fig_soc.update_layout(height=300,title="Battery SOC 24hr",plot_bgcolor='rgba(11,20,55,0.6)',paper_bgcolor='rgba(0,0,0,0)',font=dict(color='#94A3B8'))
        st.plotly_chart(fig_soc,use_container_width=True)
    else: st.markdown("<div class='info'>Grid-Tied System. Select battery chemistry to enable storage analysis.</div>",unsafe_allow_html=True)

# ── TAB 6: Electrical ─────────────────────────────────────────────────────────
with tabs[6]:
    st.markdown("<span class='lbl'>Electrical Design IEC 60364</span>",unsafe_allow_html=True)
    ec1,ec2,ec3=st.columns(3)
    with ec1:
        st.metric("DC VOC",f"{voc_str:.0f} V",f"Strings:{strings}");st.metric("DC ISC",f"{isc_str:.1f} A");st.metric("MPPT",f"{mppt_v:.0f} V")
    with ec2:
        st.metric("Cable",f"{cable_size} mm2",f"{wire_length}m");st.metric("VDrop",f"{vdrop:.2f} V",f"{vd_pct:.2f}%");st.metric("IDC",f"{idc:.1f} A")
    with ec3:
        st.metric("Grid",f"{grid_v}V/{grid_f}Hz");st.metric("Lightning Rod",f"{rod_h:.1f} m","IEC 62305");st.metric("Prot Radius",f"{prot_r} m")
    if vd_pct>3: st.markdown(f"<div class='err'>⚠️ VDrop {vd_pct:.2f}% > 3% — upgrade to {cable_size+6}mm2</div>",unsafe_allow_html=True)
    else: st.markdown(f"<div class='ok'>✅ VDrop {vd_pct:.2f}% within 3% limit.</div>",unsafe_allow_html=True)
    css=[4,6,10,16,25]
    vdv=[(idc*wire_length*0.0175)/cs/mppt_v*100 if mppt_v>0 else 0 for cs in css]
    fig_c=go.Figure()
    fig_c.add_trace(go.Bar(x=[f"{cs}mm2" for cs in css],y=vdv,marker_color=['#EF4444' if v>3 else '#10B981' for v in vdv]))
    fig_c.add_hline(y=3,line_dash="dash",line_color="#F59E0B",annotation_text="3% Limit")
    fig_c.update_layout(height=280,title="Voltage Drop by Cable Size",plot_bgcolor='rgba(11,20,55,0.6)',paper_bgcolor='rgba(0,0,0,0)',font=dict(color='#94A3B8'))
    st.plotly_chart(fig_c,use_container_width=True)

# ── TAB 7: Financial ──────────────────────────────────────────────────────────
with tabs[7]:
    st.markdown("<span class='lbl'>25-Year Financial Model</span>",unsafe_allow_html=True)
    fm1,fm2,fm3,fm4=st.columns(4)
    fm1.metric("Gross CapEx",f"{gross:,.0f} {c_curr}");fm2.metric("Net CapEx",f"{net_c:,.0f} {c_curr}",f"-{subsidy_pct}%")
    fm3.metric("Payback",f"{pb:.1f} yrs",f"Yr1:{yp[0]:,.0f}");fm4.metric("25yr NPV",f"{npv:,.0f} {c_curr}")
    st.progress(min(1.0,pb/15))
    cum=np.cumsum(yp)-net_c
    fig_fin=make_subplots(specs=[[{"secondary_y":True}]])
    fig_fin.add_trace(go.Bar(x=list(range(25)),y=list(yp),name="Revenue",marker_color='rgba(245,158,11,0.7)'),secondary_y=False)
    fig_fin.add_trace(go.Scatter(x=list(range(25)),y=list(cum),name="Cumul NPV",line=dict(color='#10B981',width=3)),secondary_y=True)
    fig_fin.update_layout(height=380,title="25-Year Financial Projection",plot_bgcolor='rgba(11,20,55,0.6)',paper_bgcolor='rgba(0,0,0,0)',font=dict(color='#94A3B8'))
    st.plotly_chart(fig_fin,use_container_width=True)
    cl=["Panels","Inverter","Battery","Structure","Cable","Lightning","Install"]
    cv2=[max(0,v) for v in [pc,ic2,bat_cost,sc,cc,lc,sys_size*install_cost]]
    fig_pie=go.Figure(go.Pie(labels=cl,values=cv2,hole=0.45,marker=dict(colors=['#F59E0B','#06B6D4','#10B981','#8B5CF6','#F97316','#EC4899','#64748B'],line=dict(color='#050E25',width=2)),textfont=dict(color='white',size=11)))
    fig_pie.update_layout(height=320,title="CapEx Breakdown",paper_bgcolor='rgba(0,0,0,0)',font=dict(color='#94A3B8'))
    st.plotly_chart(fig_pie,use_container_width=True)

# ── TAB 8: Eco ────────────────────────────────────────────────────────────────
with tabs[8]:
    st.markdown("<span class='lbl'>Environmental Impact</span>",unsafe_allow_html=True)
    ec1,ec2,ec3,ec4=st.columns(4)
    ec1.metric("CO2/Year",f"{co2:.2f} tons");ec2.metric("25yr CO2",f"{co2*25:.0f} tons");ec3.metric("Trees",f"{int(co2*18)}/yr");ec4.metric("Coal Saved",f"{co2/2.2:.1f} t/yr")
    fig_eco=go.Figure()
    fig_eco.add_trace(go.Scatter(x=list(range(1,26)),y=[co2*y for y in range(1,26)],fill='tozeroy',fillcolor='rgba(16,185,129,0.15)',line=dict(color='#10B981',width=3)))
    fig_eco.update_layout(height=280,title="Cumulative CO2 Avoided",plot_bgcolor='rgba(11,20,55,0.6)',paper_bgcolor='rgba(0,0,0,0)',font=dict(color='#94A3B8'))
    st.plotly_chart(fig_eco,use_container_width=True)

# ── TAB 9: ESG ────────────────────────────────────────────────────────────────
with tabs[9]:
    st.markdown("<span class='lbl'>ESG Ethics & Supply Chain</span>",unsafe_allow_html=True)
    eg1,eg2,eg3,eg4=st.columns(4)
    eg1.metric("ESG Rating",esg_rating);eg2.metric("Labor Risk",labor_risk);eg3.metric("Grid Access",f"{elec_access}%");eg4.metric("Sourcing",sourcing)

# ── TAB 10: Net Metering ──────────────────────────────────────────────────────
with tabs[10]:
    st.markdown("<span class='lbl'>Net Metering & Grid Export</span>",unsafe_allow_html=True)
    if net_metering:
        nm1,nm2,nm3,nm4=st.columns(4)
        nm1.metric("Daily Gen",f"{sum(g24):.1f} kWh");nm2.metric("Daily Export",f"{sum(ex24):.1f} kWh",f"@ {sell_rate} {c_curr}/kWh")
        nm3.metric("Daily Import",f"{sum(im24):.1f} kWh",f"@ {buy_rate} {c_curr}/kWh");nm4.metric("Export Credit",f"{sum(ex24)*sell_rate:,.2f} {c_curr}")
        st.markdown("<div class='ok'>✅ Net Metering active. Surplus exported for feed-in credits.</div>",unsafe_allow_html=True)
    else: st.markdown("<div class='warn'>⚠️ Net Metering disabled.</div>",unsafe_allow_html=True)

# ── TAB 11: AI Diagnosis ──────────────────────────────────────────────────────
with tabs[11]:
    st.markdown("<span class='lbl'>AI System Diagnosis</span>",unsafe_allow_html=True)
    d1,d2,d3=st.columns(3)
    d1.metric("Performance Ratio",f"{pr:.1f}%");d2.metric("Grade","A" if pr>80 else "B" if pr>70 else "C");d3.metric("Optimisation Room",f"{max(0,85-pr):.1f}%")
    issues=[];recs=[]
    if vd_pct>3: issues.append(f"🔴 VDrop {vd_pct:.2f}% > 3% — increase cable to {cable_size+6}mm2")
    if tilt>struct["tilt_max"]: issues.append(f"🔴 Tilt {tilt}deg exceeds max {struct['tilt_max']}deg for {wind_zone}")
    if cur_fea["fail"]: issues.append(f"🔴 FEA FAILURE: {cur_fea['von_mises']:.1f} MPa exceeds yield {cur_fea['yield']} MPa")
    elif cur_fea["sf"]<1.5: issues.append(f"🟡 Low SF {cur_fea['sf']:.2f} — enable Warren Truss in FEA tab")
    if pr<70: issues.append(f"🟡 Low PR {pr:.1f}% — review orientation/soiling")
    if not issues: issues.append("🟢 No critical issues — design within all parameters")
    if weather["live"]: recs.append(f"💡 Live weather active for {country}")
    if not add_truss and cur_fea["sf"]<2.0: recs.append("💡 Add Warren Truss in FEA tab to improve safety factor")
    if not has_batt: recs.append("💡 LiFePO4 battery increases self-consumption ~35%")
    recs.append(f"💡 Annual cleaning recovers ~{soiling/2:.1f}% yield loss")
    for issue in issues:
        lv="err" if "🔴" in issue else("warn" if "🟡" in issue else "ok")
        st.markdown(f"<div class='{lv}'>{issue}</div>",unsafe_allow_html=True)
    st.divider()
    for rec in recs: st.markdown(f"<div class='info'>{rec}</div>",unsafe_allow_html=True)
    st.divider()
    st.text_area("Engineering Audit",value=f"""
SolarX Professional v4.1 - AUDIT
Country   : {country} | {loc_name}
Mode      : {'LIVE' if weather['live'] else 'DATABASE'}
System    : {sys_size:.2f} kWp | {p_qty}x{panel_type.split()[0]}
Daily Gen : {sum(g24):.2f} kWh | PR: {pr:.1f}%
FEA       : VM={cur_fea['von_mises']:.2f}MPa SF={cur_fea['sf']:.2f} Truss={'ON' if add_truss else 'OFF'}
Financial : Net={net_c:,.0f}{c_curr} Payback={pb:.1f}yr NPV={npv:,.0f}
CO2/yr    : {co2:.2f} tons
""",height=220)

# ── TAB 12: Physics ───────────────────────────────────────────────────────────
with tabs[12]:
    st.markdown("<span class='lbl'>Advanced Physics Engine</span>",unsafe_allow_html=True)
    if weather["live"] and weather["data"] and weather["data"].get("today") is not None:
        td=weather["data"]["today"].copy()
        if len(td)<24: td=pd.concat([td]*3,ignore_index=True)
        td=td.iloc[:24].copy();td["Hour"]=range(24)
        om=[model_solar(float(r["Temperature"]),float(r["Wind_Speed"])/3.6,float(r["Cloud_Cover"]),int(r["Hour"]),adv_cfg) for _,r in td.iterrows()]
        sim_df=td.copy()
    else:
        mt=[temp_amb-4+8*np.sin(np.pi*(h-6)/12) if 6<=h<=18 else temp_amb-4 for h in range(24)]
        sim_df=pd.DataFrame({"Hour":list(range(24)),"Temperature":mt,"Wind_Speed":[wind/3.6]*24,"Cloud_Cover":[cloud_pct]*24})
        om=[model_solar(r["Temperature"],r["Wind_Speed"],r["Cloud_Cover"],int(r["Hour"]),adv_cfg) for _,r in sim_df.iterrows()]
    calc_df=pd.DataFrame(om);sim_df=sim_df.reset_index(drop=True)
    sim_df["Irradiance"]=calc_df["Irradiance"].values;sim_df["Cell_Temp"]=calc_df["Cell_Temp"].values;sim_df["Power_kW"]=calc_df["Power_kW"].values
    pm1,pm2,pm3,pm4=st.columns(4)
    pm1.metric("Daily Yield",f"{float(sim_df['Power_kW'].sum()):.2f} kWh");pm2.metric("Peak Cell Temp",f"{sim_df['Cell_Temp'].max():.1f} C")
    pm3.metric("Avg Irradiance",f"{sim_df['Irradiance'].mean():.1f} W/m2");pm4.metric("Peak Power",f"{sim_df['Power_kW'].max():.2f} kW")
    fp=make_subplots(rows=2,cols=1,shared_xaxes=True,subplot_titles=("Array Output kW","Cell Temp & Irradiance"))
    fp.add_trace(go.Scatter(x=sim_df["Hour"],y=sim_df["Power_kW"],fill='tozeroy',fillcolor='rgba(245,158,11,0.1)',line=dict(color='#F59E0B',width=2.5)),row=1,col=1)
    fp.add_trace(go.Scatter(x=sim_df["Hour"],y=sim_df["Cell_Temp"],line=dict(color='#EF4444',width=2),name="Cell Temp"),row=2,col=1)
    fp.add_trace(go.Scatter(x=sim_df["Hour"],y=sim_df["Irradiance"],line=dict(color='#06B6D4',width=2),name="Irradiance"),row=2,col=1)
    fp.update_layout(height=480,plot_bgcolor='rgba(11,20,55,0.6)',paper_bgcolor='rgba(0,0,0,0)',font=dict(color='#94A3B8'))
    st.plotly_chart(fp,use_container_width=True)
    st.dataframe(sim_df[["Hour","Temperature","Wind_Speed","Irradiance","Cell_Temp","Power_kW"]].round(2),use_container_width=True,hide_index=True)

# ── TAB 13: Storage ───────────────────────────────────────────────────────────
with tabs[13]:
    st.markdown("<span class='lbl'>Battery Storage Matrix</span>",unsafe_allow_html=True)
    sm1,sm2,sm3,sm4=st.columns(4)
    sm1.metric("Total Storage",f"{b_cap:.2f} kWh");sm2.metric("Usable",f"{usable:.2f} kWh",f"DoD:{dod}%")
    sm3.metric("Backup",f"{autonomy:.1f} hrs");sm4.metric("Battery CapEx",f"{bat_cost:,.0f} {c_curr}")
    st.divider()
    bdf=pd.DataFrame({"Type":list(battery_db.keys()),"Eff%":[v[0] for v in battery_db.values()],"Cycles":[v[1] for v in battery_db.values()],"Cost/kWh":[v[2] for v in battery_db.values()],"Notes":[v[5] for v in battery_db.values()]})
    st.dataframe(bdf,use_container_width=True,hide_index=True)

# ── TAB 14: Export ────────────────────────────────────────────────────────────
with tabs[14]:
    st.markdown("<span class='lbl'>Export Report Package</span>",unsafe_allow_html=True)
    df_exp=pd.DataFrame({"Hour":list(hrs),"Gen_kW":[round(x,3) for x in g24],"Load_kW":[round(x,3) for x in lo24],
        "Export_kW":[round(x,3) for x in ex24],"Import_kW":[round(x,3) for x in im24],"SOC_kWh":[round(x,3) for x in soc]})
    csv=df_exp.to_csv(index=False).encode("utf-8")
    sdf=pd.DataFrame({"Parameter":["Country","System kWp","Panels","Daily Gen kWh","PR%","Von Mises MPa","SF","Truss","Payback yr","NPV","CO2/yr t"],
        "Value":[country,f"{sys_size:.2f}",p_qty,f"{sum(g24):.2f}",f"{pr:.1f}",f"{cur_fea['von_mises']:.2f}",f"{cur_fea['sf']:.2f}","ON" if add_truss else "OFF",f"{pb:.1f}",f"{npv:,.0f}",f"{co2:.2f}"]})
    sc2=sdf.to_csv(index=False).encode("utf-8")
    ec1,ec2,ec3=st.columns(3)
    with ec1: st.download_button("📥 Hourly Profile CSV",csv,f"SolarX_{country}_Hourly.csv",mime="text/csv",use_container_width=True)
    with ec2: st.download_button("📋 System Summary CSV",sc2,f"SolarX_{country}_Summary.csv",mime="text/csv",use_container_width=True)
    with ec3:
        if PDF_ENABLED:
            pb2=gen_pdf({"Country":country,"System":f"{sys_size:.2f}kWp","Panels":p_qty,"PR":f"{pr:.1f}%","Payback":f"{pb:.1f}yr"})
            if pb2: st.download_button("📄 PDF Report",pb2,f"SolarX_{country}.pdf",mime="application/pdf",use_container_width=True)
        else: st.info("Install fpdf2 for PDF export")
    st.divider()
    st.dataframe(df_exp,height=320,use_container_width=True,hide_index=True)

st.divider()
wb="🔴 LIVE WEATHER" if weather["live"] else "📊 Database Mode"
st.markdown(f"<div style='text-align:center;color:#334155;font-size:0.75rem;padding:12px 0'>SolarX Professional v4.1 | {wb} | Wind:{wind:.0f}km/h GHI:{sun_h:.2f}kWh/m2/d Temp:{temp_amb:.1f}C<br><span style='color:#1E3A5F'>All calculations for planning purposes only.</span></div>",unsafe_allow_html=True)
'''

with open("/home/claude/solarx/tab2.py","w") as f:
    f.write(tab2)
with open("/home/claude/solarx/tab_rest.py","w") as f:
    f.write(tab_rest)
print("tab2:", os.path.getsize("/home/claude/solarx/tab2.py"))
print("tab_rest:", os.path.getsize("/home/claude/solarx/tab_rest.py"))
PYEOF
python3 /home/claude/write_tab2_onwards.py
Output

tab2: 19827
tab_rest: 17708
