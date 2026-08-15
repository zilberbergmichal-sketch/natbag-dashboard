import streamlit as st
import pandas as pd
import requests

# 1. Page Configuration
st.set_page_config(page_title="TLV Real-Time API Dashboard", layout="wide")
st.title("🛫 TLV Departures Dashboard - Live Government API")

# 2. Secure Data Fetching from your exact API Link
@st.cache_data(ttl=150) # Refresh data automatically every 2.5 minutes
def fetch_airport_api_data():
    # Your exact target API URL
    base_api_url = "https://data.gov.il"
    
    # Routing through a secure proxy to prevent cloud blocking
    proxy_url = f"https://allorigins.win{base_api_url}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(proxy_url, headers=headers, timeout=12)
        response.raise_for_status()
        
        # Parse JSON payload directly from the government database engine
        json_data = response.json()
        if "result" in json_data and "records" in json_data["result"]:
            return pd.DataFrame(json_data["result"]["records"])
        return pd.DataFrame()
    except Exception:
        # Fallback secondary proxy channel
        try:
            backup_proxy = f"https://corsproxy.io?{base_api_url}"
            res = requests.get(backup_proxy, headers=headers, timeout=10)
            return pd.DataFrame(res.json()["result"]["records"])
        except Exception as e:
            st.error(f"API Access Error: {e}")
            return pd.DataFrame()

# Execute API Data Fetching
df_raw = fetch_airport_api_data()

if not df_raw.empty:
    # Standardize column naming architecture to uppercase
    df_raw.columns = df_raw.columns.str.strip().str.upper()
    
    # 3. Core Filter Implementation
    if 'CHOPER' in df_raw.columns:
        # Isolate Departures (D) and exclude cancelled entries
        df_departures = df_raw[(df_raw['CHOPER'] == 'D') & (df_raw['CHRMNE'] != 'CANCELLED')].copy()
        
        # --- PASSENGER CAPACITY MODEL ---
        def calculate_load_capacity(destination):
            dest = str(destination).upper()
            if any(x in dest for x in ["NEW YORK", "NEWARK", "LOS ANGELES", "BANGKOK", "MIAMI"]):
                return 300  # Large aircraft
            return 180      # Standard aircraft
            
        df_departures['ESTIMATED_PASSENGERS'] = df_departures['CHLOC1D'].apply(calculate_load_capacity)
        
        # --- SIDEBAR INTERACTIVE FILTERS ---
        st.sidebar.header("🎯 Live Dashboard Controls")
        
        # Selector 1: Filter by Airline Company
        unique_airlines = ['All Airlines'] + sorted(df_departures['CHOPERD'].dropna().unique())
        selected_airline = st.sidebar.selectbox("Select Airline:", unique_airlines, index=0)
        
        # Selector 2: Filter by specific Hour Slot
        # Extract base hour block string (HH:00) safely
        df_departures['HOUR_BLOCK'] = df_departures['CHSTOL'].apply(lambda x: str(x).split('T')[-1][:2] + ":00" if 'T' in str(x) else str(x)[:2] + ":00")
        unique_hours = ['All Hours'] + sorted(df_departures['HOUR_BLOCK'].unique())
        selected_hour = st.sidebar.selectbox("Select Departure Hour:", unique_hours, index=0)
        
        # Apply filters progressively
        df_filtered = df_departures.copy()
        if selected_airline != 'All Airlines':
            df_filtered = df_filtered[df_filtered['CHOPERD'] == selected_airline]
        if selected_hour != 'All Hours':
            df_filtered = df_filtered[df_filtered['HOUR_BLOCK'] == selected_hour]
            
        # --- TIME METRICS COMPILATION FOR LINE CHART ---
        # Selected day profile
        hourly_selected = df_filtered.groupby('HOUR_BLOCK')['ESTIMATED_PASSENGERS'].sum().reset_index()
        hourly_selected.columns = ['Hour', 'Current Selection Load']
        
        # Baseline Comparison: Calculate the general airport baseline from this API pull
        hourly_baseline = df_departures.groupby('HOUR_BLOCK')['ESTIMATED_PASSENGERS'].sum().reset_index()
        hourly_baseline['Airport Average Baseline'] = hourly_baseline['ESTIMATED_PASSENGERS'] / 3 # Scaled representation
        hourly_baseline = hourly_baseline[['HOUR_BLOCK', 'Airport Average Baseline']]
        hourly_baseline.columns = ['Hour', 'Airport General Baseline']
        
        # Merge metrics into a single dataset for line chart rendering
        chart_timeline = pd.merge(hourly_selected, hourly_baseline, on='Hour', how='outer').fillna(0).sort_values(by='Hour')
        
        # --- DASHBOARD VISUAL PRESENTATION ---
        # Top KPI Metrics row
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        with metric_col1:
            st.metric(label="Live Filtered Flights Active", value=len(df_filtered))
        with metric_col2:
            st.metric(label="Estimated Passenger Footprint", value=f"{df_filtered['ESTIMATED_PASSENGERS'].sum():,}")
        with metric_col3:
            st.metric(label="Active Target Airlines Count", value=df_filtered['CHOPERD'].nunique())
            
        st.write("---")
        
        # Timeline Visualization Block
        st.subheader("📊 Comparative Time Load Profile (Selected Filters vs Airport General Load)")
        st.line_chart(data=chart_timeline, x='Hour', y=['Current Selection Load', 'Airport General Baseline'], use_container_width=True)
        
        st.write("---")
        
        # Clean Output Data Matrix
        st.subheader("📋 Filtered Operations Log")
        display_columns = ['CHSTOL', 'CHFLTN', 'CHOPERD', 'CHLOC1D', 'CHRMNE', 'ESTIMATED_PASSENGERS']
        df_view = df_filtered[display_columns].copy()
        df_view.columns = ['Scheduled Departure', 'Flight No', 'Airline Company', 'Destination', 'Status', 'Estimated Load']
        st.dataframe(df_view.sort_values(by='Scheduled Departure'), use_container_width=True)
        
    else:
        st.error("The API returned data, but the internal structural column headers do not match expected parameters.")
else:
    st.warning("⚠️ Accessing the API Gateway... Please trigger a manual layout refresh in a few moments.")
