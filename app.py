import streamlit as st
import requests
import pandas as pd

# 1. Page Configuration
st.set_page_config(page_title="Ben Gurion Airport Dashboard", layout="wide")
st.title("🛫 TLV Airport Departures Dashboard - Connection Test")

# 2. Data Fetching Function
@st.cache_data(ttl=300)
def get_natbag_data():
    url = "https://data.gov.il"
    
    # Live flight schedule resource ID from Israeli Airport Authority
    params = {
        'resource_id': 'e83f763b-b7d7-479e-b172-ae981ddc6de5',
        'limit': 300
    }
    
    # Custom headers to prevent blocking by government servers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        return pd.DataFrame(data['result']['records'])
    except Exception as e:
        st.error(f"Error connecting to data server: {e}")
        return pd.DataFrame()

# 3. Main Data Logic
df = get_natbag_data()

if not df.empty:
    # Filter for Departures (D) only and remove cancelled flights
    df_departures = df[(df['CHOPER'] == 'D') & (df['CHRMNE'] != 'CANCELLED')].copy()
    
    # Select key structural columns
    df_clean = df_departures[[
        'CHSTOL',    # Scheduled Departure Time
        'CHPTOL',    # Estimated/Updated Departure Time
        'CHFLTN',    # Flight Number
        'CHOPERD',   # Airline Name
        'CHLOC1D',   # Destination City
        'CHRMNE'     # Flight Status
    ]]
    
    # Rename columns for clarity in English
    df_clean.columns = ['Scheduled Time', 'Estimated Time', 'Flight No', 'Airline', 'Destination', 'Status']
    
    # Display simple KPI metric
    st.metric(label="Total Upcoming Departures", value=len(df_clean))
    
    # Display the interactive raw data table
    st.subheader("📋 Real-Time Flight Departures Table")
    st.dataframe(df_clean, use_container_width=True)

else:
    st.warning("No data received. Please check your internet connection or data server status.")
