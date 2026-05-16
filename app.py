import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# Page configuration
st.set_page_config(page_title="Global Solar Estimator Pro", layout="wide")

st.title("🌍 Global Renewable Energy: Solar & Load Analytics App")
st.markdown("Is app ke zariye dunya bhar se kahin bhi solar efficiency aur grid management calculate karein.")

# --- SIDEBAR: INPUTS ---
st.sidebar.header("📍 Location & Regional Settings")

# World Countries Data (Example logic for angles)
countries = {
    "Pakistan": {"angle": 30, "currency": "PKR"},
    "USA": {"angle": 35, "currency": "USD"},
    "Germany": {"angle": 45, "currency": "EUR"},
    "UAE": {"angle": 25, "currency": "AED"},
    "Australia": {"angle": 32, "currency": "AUD"},
    "Other": {"angle": 30, "currency": "Local"}
}

country = st.sidebar.selectbox("Select Country", list(countries.keys()))
standard_angle = countries[country]["angle"]
currency = countries[country]["currency"]

st.sidebar.subheader("⚙️ Technical Specs")
panel_power = st.sidebar.number_input("Single Panel Power (Watts)", value=550)
num_panels = st.sidebar.number_input("Number of Panels", value=10)
direction = st.sidebar.radio("Orientation", ["Longitudinal", "Latitudinal"])
manual_angle = st.sidebar.slider("Panel Tilt Angle (Degree)", 0, 90, standard_angle)

st.sidebar.subheader("☀️ Sunlight & Grid")
sun_hours = st.sidebar.slider("Peak Sunlight Hours (Daily)", 1, 14, 6)
sale_rate = st.sidebar.number_input(f"Selling Rate to Grid (Per Unit {currency})", value=40.0)
purchase_rate = st.sidebar.number_input(f"Purchase Rate from Grid (Per Unit {currency})", value=60.0)

st.sidebar.subheader("🏠 Home Load")
daily_load_total = st.sidebar.number_input("Daily Total Load (kWh/Units)", value=15.0)

# --- CALCULATIONS LOGIC ---
system_capacity = (panel_power * num_panels) / 1000  # kW
daily_gen = system_capacity * sun_hours * 0.8  # 20% system loss factor

# Hourly Simulation (24 Hours)
hours = np.arange(24)
# Generation curve (Sin wave during daylight)
gen_curve = [daily_gen * (np.sin(np.pi * (h - 6) / 12)) if 6 <= h <= 18 else 0 for h in hours]
gen_curve = [max(0, x) for x in gen_curve]

# Load curve (Typical home usage pattern)
load_curve = [daily_load_total/24 * (1.2 if (h > 18 or h < 8) else 0.8) for h in hours]

# Energy Balance
# Day time: Use solar, sell excess
# Night time: Full grid purchase
units_used_from_solar = [min(g, l) for g, l in zip(gen_curve, load_curve)]
units_sold = [max(0, g - l) for g, l in zip(gen_curve, load_curve)]
units_purchased = [max(0, l - g) for g, l in zip(gen_curve, load_curve)]

# --- GRAPHS SECTION ---
st.divider()
tab1, tab2, tab3 = st.tabs(["📊 24-Hour Analysis", "📅 Weekly Forecast", "🗓️ Monthly Projection"])

def create_line_chart(h, g, s, u, p, title):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=h, y=g, mode='lines', name='Solar Produced', line=dict(color='orange', width=3)))
    fig.add_trace(go.Scatter(x=h, y=s, mode='lines', name='Units Sold', line=dict(color='green', dash='dot')))
    fig.add_trace(go.Scatter(x=h, y=u, mode='lines', name='Self Used', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=h, y=p, mode='lines', name='Grid Purchase (Night)', line=dict(color='red')))
    fig.update_layout(title=title, xaxis_title="Time", yaxis_title="Units (kWh)", hovermode="x unified")
    return fig

with tab1:
    st.plotly_chart(create_line_chart(hours, gen_curve, units_sold, units_used_from_solar, units_purchased, "Hourly Energy Flow"), use_container_width=True)

with tab2:
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    # Adding some random variation for weather
    weekly_gen = [sum(gen_curve) * np.random.uniform(0.8, 1.1) for _ in range(7)]
    fig_week = go.Figure()
    fig_week.add_trace(go.Scatter(x=days, y=weekly_gen, mode='lines+markers', name='Weekly Gen', line=dict(color='orange')))
    st.plotly_chart(fig_week, use_container_width=True)

with tab3:
    weeks = ["Week 1", "Week 2", "Week 3", "Week 4"]
    monthly_gen = [sum(gen_curve) * 7 * np.random.uniform(0.9, 1.0) for _ in range(4)]
    fig_month = go.Figure()
    fig_month.add_trace(go.Scatter(x=weeks, y=monthly_gen, mode='lines+markers', name='Monthly Gen', line=dict(color='gold')))
    st.plotly_chart(fig_month, use_container_width=True)

# --- SUMMARY CARDS ---
st.divider()
total_sold_daily = sum(units_sold)
total_bought_daily = sum(units_purchased)
daily_profit = (total_sold_daily * sale_rate) - (total_bought_daily * purchase_rate)

c1, c2, c3 = st.columns(3)
c1.metric("Daily Solar Generation", f"{sum(gen_curve):.2f} kWh")
c2.metric("Daily Grid Export (Sale)", f"{total_sold_daily:.2f} Units")
c3.metric("Daily Net Financials", f"{daily_profit:,.2f} {currency}")

if daily_profit < 0:
    st.warning(f"Note: Raat ka load zyada hone ki wajah se aapko grid ko {abs(daily_profit):,.2f} pay karna par raha hai.")
else:
    st.success(f"Great! Aapka system profit generate kar raha hai: {daily_profit:,.2f} {currency}/day")
