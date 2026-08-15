import streamlit as st
import pandas as pd
import requests
import io

# 1. Page Configuration
st.set_page_config(page_title="Ben Gurion Airport Dashboard", layout="wide")
st.title("🛫 TLV Airport Departures Dashboard - Live Feed")

# 2. Data Fetching Function with Auto-Fallback Proxies
@st.cache_data(ttl=300)
def get_natbag_data():
    target_url = "https://data.gov.il"
    
    # List of reliable backup proxies to bypass the government firewall
    proxies = [
        f"https://allorigins.win{target_url}",
        f"https://corsproxy.io?{target_url}"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    for url in proxies:
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Verify we didn't get blocked with security HTML
            if "html" in response.text.lower() or "window.rbzns" in response.text:
                continue
                
            # If data is valid, parse and return it
            df = pd.read_csv(io.StringIO(response.text))
            return df
        except Exception:
            # If this proxy fails, loop continues to the next one
            continue
            
    st.error("All secure connection routes are currently busy. Trying to load directly...")
    try:
        df = pd.read_csv(target_url)
        return df
    except Exception as e:
        st.error(f"Direct connection also failed: {e}")
        return pd.DataFrame()

# 3. Main Data Logic
df = get_natbag_data()

if not df.empty:
    # Clean column names
    df.columns = df.columns.str.strip()
    
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
    
    # Display KPI metric
    st.metric(label="Total Upcoming Departures", value=len(df_clean))
    
    # Display the interactive raw data table
    st.subheader("📋 Real-Time Flight Departures Table")
    st.dataframe(df_clean, use_container_width=True)

else:
    st.warning("Awaiting secure connection to the airport database. Please refresh in a few moments.")
