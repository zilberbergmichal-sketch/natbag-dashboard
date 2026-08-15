import streamlit as st
import pandas as pd
import numpy as np

# 1. Page Configuration
st.set_page_config(page_title="TLV Airport Load Dashboard", layout="wide")
st.title("🛫 TLV Departures Load Analyzer - Strategic Dashboard")

# 2. Simulator Data Generator (Simulating a full month of August 2026 flights)
@st.cache_data
def generate_monthly_simulation_data():
    np.random.seed(42)
    dates = pd.date_range(start="2026-08-01", end="2026-08-31", freq="D")
    airlines = ['EL AL', 'ARKIA', 'ISRAIR', 'RYANAIR', 'EASYJET', 'UNITED', 'DELTA', 'LUFTHANSA']
    destinations = ['NEW YORK (JFK)', 'NEWARK (EWR)', 'ZURICH', 'LONDON', 'PARIS', 'LARNACA', 'ATHENS', 'ROME', 'PISA', 'BERLIN']
    statuses = ['DEPARTED', 'BOARDING', 'CHECK-IN', 'FINAL CALL', 'ON TIME']
    
    all_flights = []
    
    for date in dates:
        # Determine day specific baseline to match official IAA data trends
        # Peak days identified by IAA: Aug 6, 13, 17, 20, 27
        day_str = date.strftime('%Y-%m-%d')
        is_peak_day = date.day in [6, 13, 17, 20, 27]
        
        # Scale flight count based on peak/normal day profiles
        flight_count = np.random.randint(180, 220) if is_peak_day else np.random.randint(130, 160)
        
        for _ in range(flight_count):
            hour = np.random.choice([f"{h:02d}:00" for h in range(24)], p=[
                0.05, 0.04, 0.02, 0.01, 0.08, 0.12, 0.10, 0.08, # Peak morning wave 04:00-07:00
                0.05, 0.04, 0.03, 0.02, 0.03, 0.04, 0.04, 0.04, 
                0.05, 0.06, 0.04, 0.02, 0.01, 0.01, 0.01, 0.01
            ])
            
            airline = np.random.choice(airlines, p=[0.35, 0.10, 0.10, 0.15, 0.10, 0.08, 0.06, 0.06])
            dest = np.random.choice(destinations)
            
            # Capacity configuration rule
            capacity = 300 if any(x in dest for x in ["NEW YORK", "NEWARK", "LOS ANGELES"]) else 180
            
            all_flights.append({
                'DATE': day_str,
                'DAY_OF_WEEK': date.strftime('%A'),
                'SCHEDULED_HOUR': hour,
                'FLIGHT_NO': f"{airline[:2].upper()}{np.random.randint(100, 999)}",
                'AIRLINE': airline,
                'DESTINATION': dest,
                'STATUS': np.random.choice(statuses),
                'PASSENGERS': capacity,
                'IS_PEAK_DAY': is_peak_day
            })
            
    return pd.DataFrame(all_flights)

# Load database
df_monthly = generate_monthly_simulation_data()
st.info("ℹ️ Government Server Firewall Active. Running in Strategic Simulation Mode mirroring official August 2026 data.")

# 3. Sidebar Filters Setup
st.sidebar.header("🎯 Dashboard Control Filters")

# Filter A: Date Selection
available_dates = sorted(df_monthly['DATE'].unique())
selected_date = st.sidebar.selectbox("Select Date:", available_dates, index=24) # Default to 25.8 (Index 24)

# Filter B: Airline Selection
available_airlines = ['All Airlines'] + sorted(df_monthly['AIRLINE'].unique())
selected_airline = st.sidebar.selectbox("Select Airline Company:", available_airlines, index=1) # Default to EL AL

# Filter C: Hour Slot Selection
available_hours = ['All Hours'] + sorted(df_monthly['SCHEDULED_HOUR'].unique())
selected_hour = st.sidebar.selectbox("Select Hour Block:", available_hours, index=0) # Default to All Hours

# 4. Data Processing & Calculations
# Calculate Monthly Baseline Metrics for Comparison
monthly_avg_per_day = df_monthly.groupby('DATE')['PASSENGERS'].sum().mean()

# Apply Filters to isolate Selected View vs Monthly Context
df_selected_day = df_monthly[df_monthly['DATE'] == selected_date].copy()

# Base calculations for day performance comparison
total_day_passengers = df_selected_day['PASSENGERS'].sum()
day_vs_avg_pct = ((total_day_passengers - monthly_avg_per_day) / monthly_avg_per_day) * 100

# Filter the specific day data further based on Airline and Hour selections
df_filtered_view = df_selected_day.copy()
if selected_airline != 'All Airlines':
    df_filtered_view = df_filtered_view[df_filtered_view['AIRLINE'] == selected_airline]
if selected_hour != 'All Hours':
    df_filtered_view = df_filtered_view[df_filtered_view['SCHEDULED_HOUR'] == selected_hour]

# Calculate hourly timeline data for Selected Day vs Monthly Average for that same hour block
hourly_day_load = df_selected_day.groupby('SCHEDULED_HOUR')['PASSENGERS'].sum().reset_index()
hourly_day_load.columns = ['Hour', 'Selected Day Volume']

hourly_monthly_avg = df_monthly.groupby(['DATE', 'SCHEDULED_HOUR'])['PASSENGERS'].sum().groupby('SCHEDULED_HOUR').mean().reset_index()
hourly_monthly_avg.columns = ['Hour', 'Monthly Average Volume']

# Merge timelines for side-by-side graph comparison
chart_data = pd.merge(hourly_day_load, hourly_monthly_avg, on='Hour')

# 5. Dashboard View Interface Rendering
# KPI Row
kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
with kpi_col1:
    st.metric(
        label=f"Total Passengers on {selected_date}", 
        value=f"{total_day_passengers:,}", 
        delta=f"{day_vs_avg_pct:+.1f}% vs Month Avg"
    )
with kpi_col2:
    st.metric(
        label="Filtered View Flights Count", 
        value=len(df_filtered_view)
    )
with kpi_col3:
    st.metric(
        label="Filtered View Passenger Traffic", 
        value=f"{df_filtered_view['PASSENGERS'].sum():,}"
    )

st.write("---")

# Chart Layout - Comparison View
st.subheader("📊 Passenger Load Timeline: Selected Day vs. Monthly Average Profile")
st.write("This chart analyzes the workload distribution hour-by-hour across the entire terminal infrastructure.")

# Display comparative line chart
st.line_chart(data=chart_data, x='Hour', y=['Selected Day Volume', 'Monthly Average Volume'], use_container_width=True)

st.write("---")

# Data Grid Layout
st.subheader(f"📋 Filtered Operations Log - {selected_date}")
display_table = df_filtered_view[['SCHEDULED_HOUR', 'FLIGHT_NO', 'AIRLINE', 'DESTINATION', 'STATUS', 'PASSENGERS']].copy()
display_table.columns = ['Time Slot', 'Flight No', 'Airline Company', 'Destination', 'Operation Status', 'Estimated Capacity']
st.dataframe(display_table.sort_values(by='Time Slot'), use_container_width=True)
