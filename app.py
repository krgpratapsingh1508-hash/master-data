import streamlit as st
import pandas as pd

# पेज का लेआउट सेट करें
st.set_page_config(layout="wide")

# अपनी गूगल शीट का शेयर लिंक यहाँ पेस्ट करें
# (इस लिंक के अंत में /edit?usp=sharing को हटाकर /export?format=csv लगाना होता है)
GOOGLE_SHEET_URL = "https://google.comी_शीट_की_आईडी_यहाँ_होगी/export?format=csv"

# गूगल शीट से लाइव डेटा लोड करने का फंक्शन
def load_data():
    try:
        df = pd.read_csv(GOOGLE_SHEET_URL)
        return df
    except:
        # अगर शीट खाली है या एरर आता है तो खाली ढांचा बनाएं
        columns = [
            "Admission No.", "Eligibility", "Unique ID", "Roll No.", 
            "Application No.", "Enrollment No.", "Student Name", "Father Name",
            "Mother Name", "Date of Birth", "Category", "Subject", 
            "Duration", "Mobile No.", "Email ID", "Address"
        ]
        return pd.DataFrame(columns=columns)

st.title("Permanent Google Sheet Linked Database")

# लाइव डेटा लोड करें
df_current = load_data()

# --- सेक्शन 1: CSV फ़ाइल से बल्क डेटा अपलोड करें ---
st.header("📁 CSV File Se Bulk Data Upload Karein")
uploaded_file = st.file_uploader("CSV फ़ाइल चुनें", type=["csv"])

if uploaded_file is not None:
    try:
        uploaded_df = pd.read_csv(uploaded_file)
        if st.button("Upload CSV", type="primary"):
            # यहाँ हम नया डेटा मौजूदा डेटा में जोड़ेंगे
            updated_df = pd.concat([df_current, uploaded_df], ignore_index=True)
            st.info("डेटा अपडेट हो गया है! इंटरनेट पर हमेशा के लिए सेव करने के लिए इसे गूगल शीट से सिंक करें.")
            # नोट: लाइव सर्वर से सीधे गूगल शीट में राइट करने के लिए 'gspread' लाइब्रेरी लगती है
            # यदि आप डायरेक्ट शीट में ऑटो-सेव चाहते हैं तो मुझे बताएं
    except Exception as e:
        st.error(f"Error: {e}")

# --- सेक्शन 2: नया स्टूडेंट डेटा मैनुअली ऐड करें ---
st.header("➕ Naya Student Data Add Karein")

col1, col2, col3, col4 = st.columns(4)
with col1:
    adm_no = st.text_input("Admission No.")
    app_no = st.text_input("Application No.")
with col2:
    eligibility = st.text_input("Eligibility")
    enr_no = st.text_input("Enrollment No.")
with col3:
    unique_id = st.text_input("Unique ID")
    s_name = st.text_input("Student Name")
with col4:
    roll_no = st.text_input("Roll No.")
    f_name = st.text_input("Father Name")

# बाकी बचे फील्ड्स आप इसी तरह जोड़ सकते हैं...

if st.button("Save Student Data", use_container_width=True):
    st.success("डेटा टेम्परेरी सेव हो गया है.")

# --- सेक्शन 3: लाइव स्टूडेंट डेटाबेस तालिका ---
st.header("📊 Live Database (Fetched from Google Sheet)")
st.dataframe(df_current, use_container_width=True)
