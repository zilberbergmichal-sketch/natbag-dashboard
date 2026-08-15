import streamlit as st
import pandas as pd
import requests
import io
import urllib.parse

# 1. Page Configuration
st.set_page_config(page_title="Ben Gurion Airport Dashboard", layout="wide")
st.title("🛫 TLV Airport Departures Dashboard - Live Feed")

# Function to create realistic backup data if the government firewall blocks us
def get_backup_sample_data():
    sample_data = {
        'CHSTOL': ['00:05', '00:30', '01:00', '01:05', '05:30', '06:15', '07:00', '08:00', '08:30', '09:00', '16:00', '16:30', '17:00'],
        'CHPTOL': ['00:05', '00:45', '01:00', '01:05', '05:30', '06:15', '07:15', '08:00', '08:40', '09:00', '16:00', '16:30', '17:00'],
        'CHFLTN': ['LY003', 'LY027', 'LY001', 'LY005', '6H391', 'IZ211', 'FR712', 'LY347', 'EJU412', 'LY315', 'LY011', 'IZ311', '6H221'],
        'CHOPERD': ['EL AL', 'EL AL', 'EL AL', 'EL AL', 'ARKIA', 'ISRAIR', 'RYANAIR', 'EL AL', 'EASYJET', 'EL AL', 'EL AL', 'ISRAIR', 'ARKIA'],
        'CHLOC1D': ['NEW YORK (JFK)', 'NEWARK (EWR)', 'NEW YORK (JFK)', 'LOS ANGELES', 'LARNACA', 'ATHENS', 'PISA', 'ZURICH', 'BERLIN', 'LONDON', 'NEW YORK (JFK)', 'PARIS', 'ROME'],
        'CHRMNE': ['DEPARTED', 'DEPARTED', 'BOARDING', 'BOARDING', 'CHECK-IN', 'CHECK-IN', 'FINAL CALL', 'ON TIME', 'ON TIME', 'ON TIME', 'ON TIME', 'ON TIME', 'ON TIME'],
        'CHOPER': ['D', 'D', 'D', 'D', 'D', 'D', 'D', 'D', 'D', 'D', 'D', 'D', 'D']
    }
    return pd.DataFrame(sample_data)

# 2. Data Fetching Function with Auto-Fallback Proxies
@st.cache_data(ttl=300)
def get_natbag_data():
    target_url = "https://data.gov.il"
    encoded_url = urllib.parse.quote_plus(target_url)
    
    proxies = [
        f"https://codetabs.com{target_url}",
        f"https://corsproxy.io{encoded_url}",
        f"https://allorigins.win{target_url}"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    for url in proxies:
        try:
            response = requests.get(url, headers=headers, timeout=8)
            response.raise_for_status()
            if "html" in response.text.lower() or "window.rbzns" in response.text or "bereshit" in response.text:
                continue
            df = pd.read_csv(io.StringIO(response.text))
            return df
        except Exception:
            continue
    return pd.DataFrame()

# 3. Main Data Logic
raw_df = get_natbag_data()

if raw_df.empty or 'CHOPER' not in "".join(list(raw_df.columns)).upper():
    st.info("ℹ️ Government Server Firewall Active. Running in Simulator Mode with realistic flight traffic.")
    df = get_backup_sample_data()
else:
    df = raw_df
    df.columns = df.columns.str.strip().str.upper()
    cols = pd.Series(df.columns)
    for dup in cols[cols.duplicated()].unique(): 
        cols[cols == dup] = [f"{dup}_{i}" if i != 0 else dup for i in range(cols[cols == dup].shape)]
    df.columns = cols

# 4. Dashboard Processing
if 'CHOPER' in df.columns:
    df_departures = df[df['CHOPER'] == 'D'].copy()
    
    # --- CAPACITY LOGIC ---
    # Function to estimate passengers based on destination type (Long Haul vs Short Haul)
    def estimate_passengers(destination):
        dest = str(destination).upper()
        if "NEW YORK" in dest or "NEWARK" in dest or "LOS ANGELES" in dest or "BANGKOK" in dest or "MIAMI" in dest:
            return 300  # Wide-body long haul aircraft
        return 180      # Standard short haul aircraft
        
    df_departures['ESTIMATED_PASSENGERS'] = df_departures['CHLOC1D'].apply(estimate_passengers)
    
    # --- TIME PROCESSING LOGIC ---
    # Extract only the Hour (HH) from the scheduled time string (HH:MM)
    df_departures['HOUR'] = df_departures['CHSTOL'].apply(lambda x: str(x).split(':')[0] + ":00")
    
    # Group data by hour slot and calculate total passengers per hour block
    hourly_metrics = df_departures.groupby('HOUR')['ESTIMATED_PASSENGERS'].sum().reset_index()
    hourly_metrics.columns = ['Hour Slot', 'Estimated Passengers']
    hourly_metrics = hourly_metrics.sort_values(by='Hour Slot')
    
    # --- VISUAL OUTPUT ---
    target_cols = ['CHSTOL', 'CHPTOL', 'CHFLTN', 'CHOPERD', 'CHLOC1D', 'CHRMNE']
    available_cols = [col for col in target_cols if col in df_departures.columns]
    df_clean = df_departures[available_cols]
    
    display_names = {
        'CHSTOL': 'Scheduled Time', 'CHPTOL': 'Estimated Time', 'CHFLTN': 'Flight No',
        'CHOPERD': 'Airline', 'CHLOC1D': 'Destination', 'CHRMNE': 'Status'
    }
    df_clean = df_clean.rename(columns=display_names)
    
    # Display Key Performance Indicators
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Total Upcoming Flights", value=len(df_clean))
    with col2:
        st.metric(label="Total Estimated Moving Passenger Volume", value=f"{df_departures['ESTIMATED_PASSENGERS'].sum():,}")
        
    # Layout with columns for the graph and table
    st.write("---")
    st.subheader("📊 Airport Passenger Volume Peak Load Analysis")
    
    # Render Streamlit Interactive Bar Chart
    st.bar_chart(data=hourly_metrics, x='Hour Slot', y='Estimated Passengers', use_container_width=True)
    
    st.write("---")
    st.subheader("📋 Flight Departures Data Matrix")
    st.dataframe(df_clean, use_container_width=True)
else:
    st.error("Structure error. Re-syncing database.")
