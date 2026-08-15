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
    
    proxies = [
        f"https://corsproxy.io?{target_url}",
        f"https://allorigins.win{target_url}"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    for url in proxies:
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            if "html" in response.text.lower() or "window.rbzns" in response.text:
                continue
                
            df = pd.read_csv(io.StringIO(response.text))
            return df
        except Exception:
            continue
            
    # Try direct as last resort
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
    
    # Debug: Print found columns on the screen so we can see them
    st.info(f"Available columns found in database: {list(df.columns)}")
    
    # Safely check if our target columns exist
    if 'CHOPER' in df.columns:
        # Filter for Departures (D) only
        df_departures = df[df['CHOPER'] == 'D'].copy()
        
        # Select columns that are highly likely to be there
        available_cols = [col for col in ['CHSTOL', 'CHPTOL', 'CHFLTN', 'CHOPERD', 'CHLOC1D', 'CHRMNE'] if col in df_departures.columns]
        df_clean = df_departures[available_cols]
        
        st.metric(label="Total Upcoming Departures", value=len(df_clean))
        st.subheader("📋 Real-Time Flight Departures Table")
        st.dataframe(df_clean, use_container_width=True)
    else:
        st.warning("Column 'CHOPER' not found. Displaying raw data instead:")
        st.dataframe(df.head(10), use_container_width=True)

else:
    st.warning("Awaiting secure connection to the airport database. Please refresh in a few moments.")
