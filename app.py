import streamlit as st
import pandas as pd
import numpy as np
import math
import requests
import plotly.graph_objects as go

from datetime import datetime
from io import BytesIO

# Optional Imports
try:
    from geopy.geocoders import Nominatim
    GEO_ENABLED = True
except:
    GEO_ENABLED = False

try:
    from fpdf import FPDF
    PDF_ENABLED = True
except:
    PDF_ENABLED = False

# ==================================================
# PAGE CONFIG
# ==================================================

st.set_page_config(
    page_title="Solar Power Estimator Pro v2",
    page_icon="⚡",
    layout="wide"
)

# ==================================================
# TERMS & CONDITIONS
# ==================================================

def show_terms():

    @st.dialog("📄 Terms & Privacy Agreement")
    def terms_dialog():

        st.markdown("""
        ## Solar Power Estimator Pro

        By using this software you agree:

        - Calculations are estimates only
        - Weather data may come from external APIs
        - Results can vary depending on installation
        - No liability for financial or technical losses
        - Consult a certified solar engineer before installation

        Click Agree to continue.
        """)

        c1, c2 = st.columns(2)

        with c1:
            if st.button("❌ I Disagree"):
                st.stop()

        with c2:
            if st.button("✅ I Agree"):
                st.session_state["agreed"] = True
                st.rerun()

    if "agreed" not in st.session_state:
        terms_dialog()
        st.stop()

show_terms()

# ==================================================
# CSS THEME
# ==================================================

st.markdown("""
<style>

.stApp{
background:linear-gradient(
135deg,
#667eea 0%,
#764ba2 40%,
#f093fb 70%,
#f5576c 100%
);
}

.main-header{
color:white;
font-size:50px;
font-weight:900;
text-align:center;
padding:25px;
background:rgba(255,255,255,0.15);
backdrop-filter:blur(20px);
border-radius:20px;
margin-bottom:20px;
}

.feature-box{
background:rgba(255,255,255,0.9);
padding:20px;
border-radius:20px;
margin-bottom:15px;
}

.info-label{
background:#667eea;
padding:10px 20px;
border-radius:10px;
color:white;
font-weight:bold;
}

</style>
""", unsafe_allow_html=True)

# ==================================================
# GEOLOCATION
# ==================================================

@st.cache_data(ttl=86400)
def safe_geocode(country_name, fallback_lat):

    if not GEO_ENABLED:
        return fallback_lat, 70.0, country_name

    try:

        geolocator = Nominatim(
            user_agent="solar_estimator_v2",
            timeout=5
        )

        location = geolocator.geocode(country_name)

        if location:
            return (
                location.latitude,
                location.longitude,
                location.address.split(",")[0]
            )

    except:
        pass

    return fallback_lat, 70.0, country_name

# ==================================================
# LIVE WEATHER
# ==================================================

@st.cache_data(ttl=1800)
def get_live_weather(lat, lon):

    try:

        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}"
            f"&longitude={lon}"
            f"&current="
            f"temperature_2m,"
            f"wind_speed_10m,"
            f"cloud_cover"
            f"&timezone=auto"
        )

        r = requests.get(url, timeout=10)

        data = r.json()["current"]

        return {
            "temp": data["temperature_2m"],
            "wind": data["wind_speed_10m"] * 3.6,
            "cloud": data["cloud_cover"]
        }

    except:
        return None

# ==================================================
# 7 DAY WEATHER
# ==================================================

@st.cache_data(ttl=1800)
def get_7day_weather(lat, lon):

    try:

        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}"
            f"&longitude={lon}"
            f"&daily="
            f"temperature_2m_max,"
            f"temperature_2m_min,"
            f"wind_speed_10m_max,"
            f"cloud_cover_mean"
            f"&timezone=auto"
        )

        r = requests.get(url, timeout=10)

        data = r.json()

        daily = data["daily"]

        week = []

        for i in range(7):

            week.append({

                "date":
                daily["time"][i],

                "temp_max":
                daily["temperature_2m_max"][i],

                "temp_min":
                daily["temperature_2m_min"][i],

                "wind":
                daily["wind_speed_10m_max"][i] * 3.6,

                "cloud":
                daily["cloud_cover_mean"][i]

            })

        return week

    except:

        return None

from fpdf import FPDF

# ==================================================
# PDF REPORT
# ==================================================

def generate_pdf_report(report_data):

    if not PDF_ENABLED:
        return None

    pdf = FPDF()

    pdf.add_page()

    pdf.set_auto_page_break(auto=True, margin=15)

    # Header
    pdf.set_font("Helvetica", "B", 16)

    pdf.cell(
        0,
        10,
        "Solar Power Estimator Report",
        new_x="LMARGIN",
        new_y="NEXT",
        align="C"
    )

    pdf.ln(5)

    # Content
    pdf.set_font("Helvetica", "", 10)

    for k, v in report_data.items():

        text = f"{k}: {v}"

        # Remove unsupported Unicode characters
        text = (
            text.encode(
                "latin-1",
                errors="ignore"
            )
            .decode("latin-1")
        )

        pdf.cell(
            0,
            8,
            text,
            new_x="LMARGIN",
            new_y="NEXT"
        )

    pdf_output = pdf.output()

    if isinstance(pdf_output, bytearray):
        return bytes(pdf_output)

    if isinstance(pdf_output, bytes):
        return pdf_output

    return pdf_output.encode("latin-1")

# ==================================================
# HEADER
# ==================================================

st.markdown(
"""
<div class='main-header'>
 Solar Power Estimator Pro v2
</div>
""",
unsafe_allow_html=True
)
# ==================================================
# COUNTRIES DATABASE
# ==================================================

db = {

"Pakistan":[30.3,"PKR",42,82,"B+","Medium","China Import",5.3,97,220,50,55,"Extreme"],
"India":[20.5,"INR",6.2,12.5,"A-","Low","Local Mfg",5.4,99,230,50,60,"Extreme"],
"China":[35.8,"CNY",0.42,0.72,"C+","High","Global Supply",4.3,100,220,50,50,"High"],
"USA":[37.0,"USD",0.14,0.30,"A+","Very Low","US Certified",4.8,100,120,60,90,"Extreme"],
"Canada":[56.1,"CAD",0.08,0.24,"A+","Very Low","US/CA Certified",3.7,100,120,60,80,"Extreme"],

"UK":[55.3,"GBP",0.22,0.58,"A+","Very Low","UK/EU Certified",2.8,100,230,50,80,"Extreme"],
"Germany":[51.1,"EUR",0.12,0.48,"A+","Very Low","EU Certified",3.0,100,230,50,55,"Extreme"],
"France":[46.2,"EUR",0.15,0.34,"A+","Very Low","EU Certified",3.5,100,230,50,45,"High"],
"Italy":[41.8,"EUR",0.20,0.50,"A","Low","EU Certified",4.2,100,230,50,50,"High"],
"Spain":[40.4,"EUR",0.22,0.45,"A","Low","EU Certified",4.6,100,230,50,60,"Extreme"],

"Portugal":[39.3,"EUR",0.14,0.32,"A","Low","EU Certified",4.3,100,230,50,55,"Extreme"],
"Netherlands":[52.1,"EUR",0.16,0.55,"A+","Very Low","EU Certified",2.8,100,230,50,85,"Extreme"],
"Belgium":[50.5,"EUR",0.12,0.52,"A+","Very Low","EU Certified",2.9,100,230,50,40,"High"],
"Switzerland":[46.8,"CHF",0.20,0.45,"A+","Very Low","EU Certified",3.4,100,230,50,40,"High"],
"Austria":[47.5,"EUR",0.15,0.45,"A+","Very Low","EU Certified",3.4,100,230,50,35,"Moderate"],

"Norway":[60.4,"NOK",0.9,2.8,"A+","Very Low","EU Certified",2.3,100,230,50,80,"Extreme"],
"Sweden":[60.1,"SEK",0.85,2.40,"A+","Very Low","EU Certified",2.6,100,230,50,75,"Extreme"],
"Finland":[61.9,"EUR",0.08,0.38,"A+","Very Low","EU Certified",2.5,100,230,50,60,"Extreme"],
"Denmark":[56.2,"DKK",0.65,2.80,"A+","Very Low","EU Certified",2.7,100,230,50,90,"Extreme"],
"Ireland":[53.1,"EUR",0.22,0.55,"A+","Very Low","EU Certified",2.7,100,230,50,95,"Extreme"],

"Turkey":[38.9,"TRY",3.5,6.5,"B+","Medium","Local",4.9,100,230,50,50,"High"],
"Iran":[32.4,"IRR",800,2000,"B","Medium","Local",5.6,100,220,50,70,"Extreme"],
"Iraq":[33.2,"IQD",70,160,"C","High","Import",5.8,99,220,50,55,"Extreme"],
"Saudi Arabia":[23.8,"SAR",0.15,0.32,"A","Low","GCC",6.1,100,220,60,65,"Extreme"],
"UAE":[23.4,"AED",0.22,0.48,"A","Low","GCC",5.9,100,220,50,65,"Extreme"],

"Qatar":[25.3,"QAR",0.15,0.38,"A","Low","GCC",5.9,100,240,50,60,"Extreme"],
"Kuwait":[29.3,"KWD",0.02,0.08,"A","Low","GCC",5.9,100,240,50,70,"Extreme"],
"Oman":[21.5,"OMR",0.03,0.12,"A","Low","GCC",6.0,100,240,50,65,"Extreme"],
"Jordan":[30.5,"JOD",0.08,0.18,"B+","Medium","Local",5.8,100,230,50,60,"Extreme"],
"Egypt":[26.8,"EGP",1.2,2.6,"B","Medium","Local",6.1,100,220,50,50,"High"],

"South Africa":[-30.5,"ZAR",1.9,3.8,"B+","Medium","Local",5.7,85,230,50,60,"Extreme"],
"Nigeria":[9.0,"NGN",70,160,"C","High","Import",5.5,62,230,50,45,"High"],
"Kenya":[-1.2,"KES",12,28,"B","Medium","Import",5.7,76,240,50,35,"Moderate"],
"Ethiopia":[9.1,"ETB",0.5,1.2,"B","Medium","Import",5.9,51,220,50,40,"High"],
"Ghana":[7.9,"GHS",0.50,1.0,"B","Medium","Import",5.4,86,230,50,40,"High"],

"Australia":[-25.2,"AUD",0.10,0.35,"A+","Very Low","AU Certified",5.8,100,230,50,85,"Extreme"],
"New Zealand":[-40.9,"NZD",0.11,0.40,"A+","Very Low","AU/NZ",4.4,100,230,50,90,"Extreme"],
"Japan":[36.2,"JPY",21,42,"A+","Very Low","JP Certified",3.8,100,100,50,110,"Extreme"],
"South Korea":[37.5,"KRW",95,180,"A+","Very Low","KR Certified",3.8,100,220,60,75,"Extreme"],
"Malaysia":[4.2,"MYR",0.38,0.68,"A-","Low","Local Mfg",4.7,100,240,50,45,"High"],

"Indonesia":[-0.7,"IDR",1500,3400,"B","Medium","Local",4.8,99,220,50,50,"High"],
"Thailand":[15.8,"THB",2.8,6.0,"A-","Low","Local Mfg",5.0,100,220,50,60,"Extreme"],
"Vietnam":[14.0,"VND",2200,3800,"B+","Medium","Local Mfg",4.8,100,220,50,85,"Extreme"],
"Philippines":[12.8,"PHP",6.2,14.0,"B","Medium","Import",5.1,94,220,60,95,"Extreme"],
"Singapore":[1.3,"SGD",0.28,0.45,"A+","Very Low","Import",4.6,100,230,50,40,"High"],

"Bangladesh":[23.6,"BDT",7.5,14,"B","Medium","Local",4.6,99,220,50,90,"Extreme"],
"Nepal":[28.3,"NPR",8.2,18.5,"B","Medium","Import",4.7,95,230,50,40,"High"],
"Sri Lanka":[7.8,"LKR",25,58,"B","Medium","Import",5.2,99,230,50,80,"Extreme"],
"Afghanistan":[33.9,"AFN",5,12,"B","High","Import",5.2,98,220,50,45,"High"]

}

# ==================================================
# SOLAR PANEL DATABASE
# ==================================================

panel_db = {

    "Monocrystalline 400W":{
        "Power":400,
        "Efficiency":21.5,
        "Voc":49.5,
        "Isc":10.2,
        "Cost":140
    },

    "Monocrystalline 450W":{
        "Power":450,
        "Efficiency":22.0,
        "Voc":50.2,
        "Isc":11.1,
        "Cost":155
    },

    "Monocrystalline 500W":{
        "Power":500,
        "Efficiency":22.5,
        "Voc":52.0,
        "Isc":12.0,
        "Cost":175
    },

    "Monocrystalline 550W":{
        "Power":550,
        "Efficiency":22.8,
        "Voc":53.5,
        "Isc":13.0,
        "Cost":190
    },

    "Monocrystalline 600W":{
        "Power":600,
        "Efficiency":23.2,
        "Voc":54.8,
        "Isc":13.8,
        "Cost":210
    },

    "Polycrystalline 250W":{
        "Power":250,
        "Efficiency":16.0,
        "Voc":37.0,
        "Isc":8.8,
        "Cost":75
    },

    "Polycrystalline 300W":{
        "Power":300,
        "Efficiency":17.0,
        "Voc":39.0,
        "Isc":9.2,
        "Cost":90
    },

    "Polycrystalline 330W":{
        "Power":330,
        "Efficiency":17.5,
        "Voc":40.5,
        "Isc":9.8,
        "Cost":100
    },

    "Polycrystalline 350W":{
        "Power":350,
        "Efficiency":18.0,
        "Voc":41.5,
        "Isc":10.0,
        "Cost":110
    },

    "PERC 450W":{
        "Power":450,
        "Efficiency":22.0,
        "Voc":50.0,
        "Isc":11.2,
        "Cost":160
    },

    "PERC 500W":{
        "Power":500,
        "Efficiency":22.5,
        "Voc":51.0,
        "Isc":12.1,
        "Cost":180
    },

    "PERC 550W":{
        "Power":550,
        "Efficiency":23.0,
        "Voc":53.0,
        "Isc":13.1,
        "Cost":195
    },

    "Half-Cut Cell 450W":{
        "Power":450,
        "Efficiency":22.1,
        "Voc":49.8,
        "Isc":11.3,
        "Cost":165
    },

    "Half-Cut Cell 550W":{
        "Power":550,
        "Efficiency":23.0,
        "Voc":53.2,
        "Isc":13.2,
        "Cost":200
    },

    "Half-Cut Cell 600W":{
        "Power":600,
        "Efficiency":23.4,
        "Voc":55.0,
        "Isc":14.0,
        "Cost":220
    },

    "Bifacial 500W":{
        "Power":500,
        "Efficiency":22.5,
        "Voc":51.2,
        "Isc":12.2,
        "Cost":210
    },

    "Bifacial 550W":{
        "Power":550,
        "Efficiency":23.0,
        "Voc":53.0,
        "Isc":13.3,
        "Cost":230
    },

    "Bifacial 600W":{
        "Power":600,
        "Efficiency":23.6,
        "Voc":55.5,
        "Isc":14.1,
        "Cost":250
    },

    "TOPCon 550W":{
        "Power":550,
        "Efficiency":23.5,
        "Voc":53.8,
        "Isc":13.2,
        "Cost":240
    },

    "TOPCon 600W":{
        "Power":600,
        "Efficiency":24.0,
        "Voc":55.2,
        "Isc":14.0,
        "Cost":260
    },

    "TOPCon 650W":{
        "Power":650,
        "Efficiency":24.3,
        "Voc":57.0,
        "Isc":15.0,
        "Cost":285
    },

    "N-Type TOPCon 550W":{
        "Power":550,
        "Efficiency":24.0,
        "Voc":54.0,
        "Isc":13.4,
        "Cost":250
    },

    "N-Type TOPCon 600W":{
        "Power":600,
        "Efficiency":24.5,
        "Voc":55.8,
        "Isc":14.2,
        "Cost":275
    },

    "N-Type TOPCon 700W":{
        "Power":700,
        "Efficiency":25.0,
        "Voc":58.0,
        "Isc":15.5,
        "Cost":320
    },

    "HJT 550W":{
        "Power":550,
        "Efficiency":24.5,
        "Voc":54.5,
        "Isc":13.5,
        "Cost":280
    },

    "HJT 600W":{
        "Power":600,
        "Efficiency":25.0,
        "Voc":56.0,
        "Isc":14.3,
        "Cost":300
    },

    "HJT 700W":{
        "Power":700,
        "Efficiency":25.8,
        "Voc":58.5,
        "Isc":15.8,
        "Cost":350
    },

    "Thin Film 150W":{
        "Power":150,
        "Efficiency":11.0,
        "Voc":22.0,
        "Isc":8.0,
        "Cost":55
    },

    "Thin Film 250W":{
        "Power":250,
        "Efficiency":12.5,
        "Voc":36.0,
        "Isc":8.5,
        "Cost":80
    },

    "Flexible Panel 100W":{
        "Power":100,
        "Efficiency":18.0,
        "Voc":21.0,
        "Isc":6.0,
        "Cost":60
    },

    "Flexible Panel 200W":{
        "Power":200,
        "Efficiency":19.0,
        "Voc":38.0,
        "Isc":7.0,
        "Cost":110
    }

}
# ==================================================
# BATTERY DATABASE
# ==================================================

battery_db = {

"LiFePO4 LFP":[94,6000,180,2.0,48,"Best Choice"],

"NMC Lithium":[92,4000,220,2.5,48,"High Density"],

"Lead Acid AGM":[85,1200,120,5.0,24,"Low Cost"],

"Sodium Ion":[90,3000,150,3.0,48,"Emerging"],

"Solid State":[96,8000,350,1.5,48,"Future"],

"No Battery":[0,0,0,0,0,"Grid Only"]

}

# ==================================================
# INVERTER DATABASE
# ==================================================

inverter_db = {

"String Inverter":[97.5,1.00,800,"Central MPPT"],

"Hybrid Inverter":[97.0,1.02,1500,"Battery + Grid"],

"Micro Inverter":[96.8,1.05,1200,"Panel Level"],

"Power Optimizer":[98.0,1.03,1400,"DC Optimizer"],

"Central Inverter":[98.5,0.98,600,"Utility Scale"]

}

# ==================================================
# STRUCTURE DATABASE
# ==================================================

structure_db = {

"Low":{
"type":"Aluminum Fixed Tilt",
"tilt_max":30,
"foundation":"Ground Screw"
},

"Moderate":{
"type":"Galvanized Steel",
"tilt_max":25,
"foundation":"Concrete Ballast"
},

"High":{
"type":"Steel + Bracing",
"tilt_max":20,
"foundation":"Concrete Footing"
},

"Extreme":{
"type":"Heavy Steel",
"tilt_max":15,
"foundation":"Deep Concrete Pile"
}

}
# ==================================================
# SIDEBAR INPUTS
# ==================================================

with st.sidebar:

    st.title("⚡ Solar Power Estimator")

    country = st.selectbox(
        "🌍 Country",
        sorted(db.keys())
    )

    country_data = db[country]

    c_lat = country_data[0]
    c_curr = country_data[1]
    sell_rate_default = country_data[2]
    buy_rate_default = country_data[3]
    esg_rating = country_data[4]
    avg_ghi = country_data[7]
    grid_v = country_data[9]
    grid_f = country_data[10]
    wind_db = country_data[11]
    wind_zone = country_data[12]

    st.divider()

    st.subheader("🌤 Weather")

    weather_mode = st.toggle(
        "Use Live Weather",
        value=False
    )

    if weather_mode:
        st.info(
            "Location permission required"
        )

    st.divider()

    st.subheader("☀ Solar Panels")

   panel_type = st.selectbox(
    "Solar Panel Type",
    list(panel_db.keys())
    )
    panel = panel_db[panel_type]

    panel_power = panel["Power"]
    panel_efficiency = panel["Efficiency"]
    panel_voc = panel["Voc"]
    panel_isc = panel["Isc"]
    panel_cost = panel["Cost"]

    panel_qty = st.number_input(
        "Panels Quantity",
        min_value=1,
        max_value=5000,
        value=20
    )

    st.divider()

    st.subheader("🔌 Inverter")

    inverter_type = st.selectbox(
        "Inverter Type",
        list(inverter_db.keys())
    )

    inv_eff, inv_bonus, inv_cost, inv_note = inverter_db[inverter_type]

    st.divider()

    st.subheader("🔋 Battery")

    battery_type = st.selectbox(
        "Battery Type",
        list(battery_db.keys())
    )

    b_eff, b_cycles, b_cost, b_degrade, b_voltage, b_note = battery_db[battery_type]

    has_battery = battery_type != "No Battery"

    if has_battery:

        battery_capacity = st.number_input(
            "Battery Capacity (kWh)",
            value=20.0
        )

        dod = st.slider(
            "DoD %",
            50,
            95,
            85
        )

    else:

        battery_capacity = 0
        dod = 0

    st.divider()

    st.subheader("⚙ Design")

    tilt = st.slider(
        "Tilt Angle",
        0,
        60,
        25
    )

    azimuth = st.slider(
        "Azimuth",
        -180,
        180,
        0
    )

    building_height = st.number_input(
        "Building Height (m)",
        value=6.0
    )

    st.divider()

    st.subheader("⚡ Load")

    daily_load = st.number_input(
        "Daily Load kWh",
        value=55.0
    )

    st.divider()

    st.subheader("💰 Financial")

    buy_rate = st.number_input(
        f"Buy Rate ({c_curr})",
        value=float(buy_rate_default)
    )

    sell_rate = st.number_input(
        f"Sell Rate ({c_curr})",
        value=float(sell_rate_default)
    )

    tax_rate = st.slider(
        "Tax %",
        0,
        30,
        17
    )

# ==================================================
# LOCATION
# ==================================================

lat, lon, location_name = safe_geocode(
    country,
    c_lat
)

# ==================================================
# WEATHER DATA
# ==================================================

cloud = 20
wind = wind_db
temperature = 25

weekly_weather = None

if weather_mode:

    live_weather = get_live_weather(
        lat,
        lon
    )

    if live_weather:

        cloud = live_weather["cloud"]
        wind = live_weather["wind"]
        temperature = live_weather["temp"]

        weekly_weather = get_7day_weather(
            lat,
            lon
        )

# ==================================================
# SOLAR SYSTEM SIZE
# ==================================================

system_size_kw = (
    panel_qty *
    (voc_std / 100)
)

# ==================================================
# STRING DESIGN
# ==================================================

panels_per_string = max(
    1,
    int(1000 / voc_std)
)

strings = math.ceil(
    panel_qty /
    panels_per_string
)

voc_string = (
    voc_std *
    panels_per_string
)

isc_string = (
    isc *
    strings
)

mppt_voltage = (
    voc_string *
    0.80
)

# ==================================================
# WEATHER FACTOR
# ==================================================

weather_factor = (
    (1 - cloud / 100)
    *
    (1 + wind * 0.0002)
)

# ==================================================
# TEMP LOSS
# ==================================================

temp_loss = (
    1 +
    (p_temp / 100)
    *
    (temperature - 25)
)

# ==================================================
# ANGLE FACTOR
# ==================================================

angle_factor = np.cos(
    np.radians(
        abs(
            tilt -
            abs(c_lat)
        )
    )
)

angle_factor = max(
    0.5,
    angle_factor
)

# ==================================================
# DAILY SOLAR YIELD
# ==================================================

daily_generation = (

    system_size_kw
    *
    avg_ghi
    *
    weather_factor
    *
    angle_factor
    *
    (inv_eff / 100)
    *
    inv_bonus
    *
    temp_loss

)

daily_generation = max(
    0,
    daily_generation
)

# ==================================================
# BATTERY ANALYSIS
# ==================================================

if has_battery:

    usable_battery = (
        battery_capacity
        *
        (dod / 100)
    )

    backup_hours = (
        usable_battery
        /
        daily_load
    ) * 24

else:

    usable_battery = 0
    backup_hours = 0

# ==================================================
# NET ENERGY
# ==================================================

net_energy = (
    daily_generation
    -
    daily_load
)

# ==================================================
# IMPORT EXPORT
# ==================================================

if net_energy >= 0:

    export_energy = net_energy
    import_energy = 0

else:

    export_energy = 0
    import_energy = abs(
        net_energy
    )

# ==================================================
# DAILY FINANCIALS
# ==================================================

daily_income = (
    export_energy
    *
    sell_rate
)

daily_bill = (
    import_energy
    *
    buy_rate
)

daily_profit = (
    daily_income
    -
    daily_bill
)

daily_profit = (
    daily_profit
    *
    (1 - tax_rate/100)
)

# ==================================================
# YEARLY VALUES
# ==================================================

annual_generation = (
    daily_generation
    *
    365
)

annual_profit = (
    daily_profit
    *
    365
)

# ==================================================
# COST MODEL
# ==================================================

panel_cost_total = (
    panel_qty
    *
    p_cost
    *
    1000
)

battery_cost_total = (
    battery_capacity
    *
    b_cost
)

inverter_cost_total = (
    system_size_kw
    *
    inv_cost
)

total_cost = (

    panel_cost_total
    +
    battery_cost_total
    +
    inverter_cost_total

)

# ==================================================
# PAYBACK
# ==================================================

if annual_profit > 0:

    payback_years = (
        total_cost
        /
        annual_profit
    )

else:

    payback_years = 999

# ==================================================
# WEEKLY FORECAST
# ==================================================

weekly_report = []

if weekly_weather:

    for day in weekly_weather:

        cloud_day = day["cloud"]

        factor = (
            1 -
            cloud_day/100
        )

        day_generation = (
            daily_generation
            *
            factor
        )

        weekly_report.append({

            "Date":
            day["date"],

            "Generation":
            round(
                day_generation,
                2
            ),

            "Cloud":
            cloud_day,

            "Wind":
            day["wind"]

        })

# ==================================================
# WIND LOAD
# ==================================================

wind_force = (
    0.613
    *
    ((wind/3.6)**2)
    *
    panel_qty
)

# ==================================================
# STRUCTURE
# ==================================================

structure = structure_db[
    wind_zone
]

max_tilt = structure[
    "tilt_max"
]

structure_type = structure[
    "type"
]
# ==================================================
# DASHBOARD
# ==================================================

st.markdown(
f"""
<div class='feature-box'>
<h2>📍 {location_name}</h2>
<p><b>Country:</b> {country}</p>
<p><b>Grid:</b> {grid_v}V / {grid_f}Hz</p>
<p><b>ESG Rating:</b> {esg_rating}</p>
</div>
""",
unsafe_allow_html=True
)

# ==================================================
# KPI SECTION
# ==================================================

k1,k2,k3,k4 = st.columns(4)

with k1:
    st.metric(
        "☀ Daily Generation",
        f"{daily_generation:.2f} kWh"
    )

with k2:
    st.metric(
        "⚡ Annual Generation",
        f"{annual_generation:.0f} kWh"
    )

with k3:
    st.metric(
        "💰 Annual Profit",
        f"{annual_profit:,.0f} {c_curr}"
    )

with k4:
    st.metric(
        "⏳ Payback",
        f"{payback_years:.1f} Years"
    )

# ==================================================
# TABS
# ==================================================

tab1,tab2,tab3,tab4,tab5 = st.tabs([
    "📊 Summary",
    "🌦 Weather",
    "⚙ Technical",
    "💰 Financial",
    "📥 Export"
])

# ==================================================
# SUMMARY TAB
# ==================================================

with tab1:

    st.subheader("System Overview")

    s1,s2 = st.columns(2)

    with s1:

        st.info(f"System Size: {system_size_kw:.2f} kW")

        st.info(f"Panel Type: {panel_type}")

        st.info(f"Panels Installed: {panel_qty}")

        st.info(f"Inverter: {inverter_type}")

    with s2:

        st.info(f"Battery: {battery_type}")

        st.info(f"Daily Load: {daily_load:.2f} kWh")

        st.info(f"Net Energy: {net_energy:.2f} kWh")

        st.info(f"Wind Zone: {wind_zone}")

    st.subheader("Energy Balance")

    fig = go.Figure()

    fig.add_bar(
        name="Generation",
        x=["Daily"],
        y=[daily_generation]
    )

    fig.add_bar(
        name="Load",
        x=["Daily"],
        y=[daily_load]
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# ==================================================
# WEATHER TAB
# ==================================================

with tab2:

    st.subheader("Weather Conditions")

    w1,w2,w3 = st.columns(3)

    with w1:
        st.metric(
            "Temperature",
            f"{temperature:.1f} °C"
        )

    with w2:
        st.metric(
            "Cloud Cover",
            f"{cloud:.0f}%"
        )

    with w3:
        st.metric(
            "Wind Speed",
            f"{wind:.1f} km/h"
        )

    if weekly_report:

        st.subheader(
            "7 Day Forecast"
        )

        forecast_df = pd.DataFrame(
            weekly_report
        )

        st.dataframe(
            forecast_df,
            use_container_width=True
        )

        chart = go.Figure()

        chart.add_scatter(
            x=forecast_df["Date"],
            y=forecast_df["Generation"],
            mode="lines+markers",
            name="Generation"
        )

        st.plotly_chart(
            chart,
            use_container_width=True
        )

# ==================================================
# TECHNICAL TAB
# ==================================================

with tab3:

    st.subheader(
        "Electrical Design"
    )

    tech_df = pd.DataFrame({

        "Parameter":[
            "System Size",
            "Panels",
            "Strings",
            "Panels/String",
            "String Voc",
            "String Isc",
            "MPPT Voltage",
            "Tilt Angle",
            "Structure",
            "Wind Force"
        ],

        "Value":[
            f"{system_size_kw:.2f} kW",
            panel_qty,
            strings,
            panels_per_string,
            f"{voc_string:.1f} V",
            f"{isc_string:.1f} A",
            f"{mppt_voltage:.1f} V",
            f"{tilt}°",
            structure_type,
            f"{wind_force:.1f} N"
        ]

    })

    st.dataframe(
        tech_df,
        use_container_width=True
    )

    st.subheader(
        "Battery Analysis"
    )

    if has_battery:

        st.success(
            f"Usable Battery: "
            f"{usable_battery:.2f} kWh"
        )

        st.success(
            f"Backup Hours: "
            f"{backup_hours:.1f} Hours"
        )

        st.success(
            f"Cycles: {b_cycles}"
        )

    else:

        st.warning(
            "No Battery Selected"
        )

# ==================================================
# FINANCIAL TAB
# ==================================================

with tab4:

    st.subheader(
        "Financial Analysis"
    )

    finance_df = pd.DataFrame({

        "Item":[
            "Panel Cost",
            "Battery Cost",
            "Inverter Cost",
            "Total Cost",
            "Annual Profit",
            "Payback"
        ],

        "Value":[
            f"{panel_cost_total:,.0f}",
            f"{battery_cost_total:,.0f}",
            f"{inverter_cost_total:,.0f}",
            f"{total_cost:,.0f}",
            f"{annual_profit:,.0f}",
            f"{payback_years:.1f} Years"
        ]

    })

    st.dataframe(
        finance_df,
        use_container_width=True
    )

    cost_fig = go.Figure()

    cost_fig.add_pie(
        labels=[
            "Panels",
            "Battery",
            "Inverter"
        ],
        values=[
            panel_cost_total,
            battery_cost_total,
            inverter_cost_total
        ]
    )

    st.plotly_chart(
        cost_fig,
        use_container_width=True
    )

# ==================================================
# EXPORT TAB
# ==================================================

with tab5:

    st.subheader(
        "Download Reports"
    )

    report_data = {

        "Country":country,
        "Location":location_name,
        "System Size":f"{system_size_kw:.2f} kW",
        "Daily Generation":f"{daily_generation:.2f} kWh",
        "Annual Generation":f"{annual_generation:.0f} kWh",
        "Annual Profit":f"{annual_profit:.0f}",
        "Payback":f"{payback_years:.1f} Years",
        "Battery":battery_type,
        "Panel":panel_type,
        "Inverter":inverter_type

    }

    pdf_data = generate_pdf_report(
        report_data
    )

    if pdf_data:

        st.download_button(
            "📄 Download PDF Report",
            pdf_data,
            file_name=
            "solar_report.pdf",
            mime=
            "application/pdf"
        )

    excel_df = pd.DataFrame(
        [report_data]
    )

    excel_bytes = BytesIO()

    with pd.ExcelWriter(
        excel_bytes,
        engine="openpyxl"
    ) as writer:

        excel_df.to_excel(
            writer,
            index=False
        )

    st.download_button(
        "📊 Download Excel Report",
        excel_bytes.getvalue(),
        file_name=
        "solar_report.xlsx",
        mime=
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ==================================================
# FOOTER
# ==================================================

st.markdown("---")

st.caption(
    "Solar Power Estimator Pro v2 | "
    "120+ Countries | Live Weather | "
    "Weekly Forecast | Financial Analysis"
)
