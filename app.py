import streamlit as st
import pandas as pd
import requests
import io
import urllib.parse

# 1. Page Configuration
st.set_page_config(page_title="Ben Gurion Airport Dashboard", layout="wide")
st.title("🛫 TLV Airport Departures Dashboard - Live Feed")

# 2. Data Fetching Function with Auto-Fallback Proxies
@st.cache_data(ttl=300)
def get_natbag_data():
    # Complete direct download link to the CSV dataset file
    target_url = "https://data.gov.il"
    
    # URL encoding to pass the target safely through proxy strings
    encoded_url = urllib.parse.quote_plus(target_url)
    
    # Corrected endpoints matching official proxy API standards
    proxies = [
        f"https://corsproxy.io{encoded_url}",
        f"https://allorigins.win{target_url}"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    for url in proxies:
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Ensure the firewall didn't return an HTML block page
            if "html" in response.text.lower() or "window.rbzns" in response.text:
                continue
                
            df = pd.read_csv(io.StringIO(response.text))
            return df
        except Exception:
            continue
            
    # Try direct connection as a last resort
    try:
        df = pd.read_csv(target_url)
        return df
    except Exception as e:
        st.error(f"All connections failed: {e}")
        return pd.DataFrame()

# 3. Main Data Logic
df = get_natbag_data()

if not df.empty:
    # Standardize column names: strip spaces and convert to UPPERCASE
    df.columns = df.columns.str.strip().str.upper()
    
    # Safely check if our target filter column exists
    if 'CHOPER' in df.columns:
        # Filter for Departures (D) only
        df_departures = df[df['CHOPER'] == 'D'].copy()
        
        # Select target dashboard columns
        target_cols = ['CHSTOL', 'CHPTOL', 'CHFLTN', 'CHOPERD', 'CHLOC1D', 'CHRMNE']
        available_cols = [col for col in target_cols if col in df_departures.columns]
        df_clean = df_departures[available_cols]
        
        # Rename structural columns to friendly English display titles
        display_names = {
            'CHSTOL': 'Scheduled Time',
            'CHPTOL': 'Estimated Time',
            'CHFLTN': 'Flight No',
            'CHOPERD': 'Airline',
            'CHLOC1D': 'Destination',
            'CHRMNE': 'Status'
        }
        df_clean = df_clean.rename(columns=display_names)
        
        # Dashboard display elements
        st.metric(label="Total Upcoming Departures", value=len(df_clean))
        st.subheader("📋 Real-Time Flight Departures Table")
        st.dataframe(df_clean, use_container_width=True)
    else:
        st.warning("Target column layout altered. Displaying raw data input:")
        st.dataframe(df.head(10), use_container_width=True)

else:
    st.warning("Awaiting secure connection to the airport database. Please refresh in a few moments.")
