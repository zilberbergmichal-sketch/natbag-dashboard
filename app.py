import streamlit as st
import pandas as pd

# 1. Page Configuration
st.set_page_config(page_title="Ben Gurion Airport Dashboard", layout="wide")
st.title("🛫 TLV Airport Departures Dashboard - Live Connection")

# 2. Data Fetching Function (Using Direct CSV URL to bypass cloud blocks)
@st.cache_data(ttl=300)
def get_natbag_data():
    # Direct official CSV download URL from data.gov.il
    csv_url = "https://data.gov.il"
    
    try:
        # Read the live CSV file directly into a pandas DataFrame
        df = pd.read_csv(csv_url)
        return df
    except Exception as e:
        st.error(f"Error connecting to data server: {e}")
        return pd.DataFrame()

# 3. Main Data Logic
df = get_natbag_data()

if not df.empty:
    # Filter for Departures (D) only and remove cancelled flights
    # Note: Strip whitespace from column names or values if needed
    df.columns = df.columns.str.strip()
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
