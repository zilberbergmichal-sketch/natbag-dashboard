import streamlit as st
import requests
import pandas as pd

# הגדרת כותרת לדשבורד
st.set_page_config(page_title="נתב\"ג - דשבורד עומסים", layout="wide")
st.title("🛫 דשבורד עומסי המראות בנתב\"ג - בדיקת חיבור")

# פונקציה למשיכת הנתונים מה-API הממשלתי
@st.cache_data(ttl=300) # שומר את המידע בזכרון ל-5 דקות כדי לא להעמיס על השרת
def get_natbag_data():
    url = "https://data.gov.il"
    
    #resource_id של לוח הטיסות בזמן אמת של רש"ת
    params = {
        'resource_id': 'e83f763b-b7d7-479e-b172-ae981ddc6de5',
        'limit': 300 # מושך את 300 הטיסות הקרובות
    }
    
    # הגדרת כותרת דפדפן כדי למנוע חסימה מהשרת הממשלתי
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status() # בודק שלא קיבלנו שגיאת שרת
        data = response.json()
        return pd.DataFrame(data['result']['records'])
    except Exception as e:
        st.error(f"שגיאה בהתחברות לשרת הממשלתי: {e}")
        return pd.DataFrame()

# הרצת הפונקציה
df = get_natbag_data()

if not df.empty:
    # 1. סינון לפי המראות בלבד (D) וסינון טיסות שבוטלו
    df_departures = df[(df['CHOPER'] == 'D') & (df['CHRMNE'] != 'CANCELLED')].copy()
    
    # 2. סידור וניקוי השמות של העמודות שיהיה נוח לקרוא
    df_clean = df_departures[[
        'CHSTOL',    # שעת המראה מתוכננת
        'CHPTOL',    # שעת המראה מעודכנת
        'CHFLTN',    # מספר טיסה
        'CHOPERD',   # חברת תעופה
        'CHLOC1D',   # עיר יעד
        'CHRMNE'     # סטטוס (Boarding, Check-in וכו')
    ]]
    
    # שינוי שמות העמודות לעברית
    df_clean.columns = ['שעה מתוכננת', 'שעה מעודכנת', 'מספר טיסה', 'חברת תעופה', 'יעד', 'סטטוס']
    
    # הצגת נתונים סטטיסטיים מהירים
    st.metric("סה"כ המראות קרובות במערכת", len(df_clean))
    
    # הצגת הטבלה האינטראקטיבית ב-Streamlit
    st.subheader("📋 לוח המראות בזמן אמת (נתונים גולמיים)")
    st.dataframe(df_clean, use_container_width=True)

else:
    st.warning("לא התקבלו נתונים. ודא שהאינטרנט מחובר ושה-API הממשלתי זמין.")
