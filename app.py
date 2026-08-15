import streamlit as st
import pandas as pd

# 1. Page Configuration
st.set_page_config(page_title="Ben Gurion Airport Dashboard", layout="wide")
st.title("🛫 TLV Airport Departures Dashboard - Column Check")

# 2. Data Fetching Function
@st.cache_data(ttl=300)
def get_natbag_data():
    csv_url = "https://data.gov.il"
    try:
        df = pd.read_csv(csv_url)
        return df
    except Exception as e:
        st.error(f"Error connecting to data server: {e}")
        return pd.DataFrame()

# 3. Main Data Logic
df = get_natbag_data()

if not df.empty:
    # Print available columns to the screen for debugging
    st.subheader("Available Columns in the CSV:")
    st.write(list(df.columns))
    
    # Display the raw dataframe to see how the data looks
    st.subheader("📋 Raw Data Preview")
    st.dataframe(df.head(20), use_container_width=True)

else:
    st.warning("No data received. Please check your internet connection or data server status.")
