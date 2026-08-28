import streamlit as st
import pandas as pd
import requests
import json

# पेज का लेआउट सेट करें
st.set_page_config(layout="wide")

st.title("Permanent Google Sheets Linked Database")

# आपका बिल्कुल सही Google Script Web App URL
API_URL = "https://google.com"

# डिफ़ॉल्ट कॉलम सूची जो हमारी शीट में होनी चाहिए
DEFAULT_COLUMNS = [
    "Admission No.", "Eligibility", "Unique ID", "Roll No.", 
    "Application No.", "Enrollment No.", "Student Name", "Father Name",
    "Mother Name", "Date of Birth", "Category", "Subject", 
    "Duration", "Mobile No.", "Email ID", "Address"
]

# गूगल शीट से लाइव डेटा लोड करने का फंक्शन
def load_data():
    try:
        response = requests.get(API_URL, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                headers = data[0]
                rows = data[1:]
                if not rows:
                    return pd.DataFrame(columns=headers)
                return pd.DataFrame(rows, columns=headers)
    except Exception as e:
        pass
    
    # अगर शीट खाली है या एरर आए तो खाली ढांचा वापस करें
    return pd.DataFrame(columns=DEFAULT_COLUMNS)

# गूगल शीट में पूरा डेटा अपडेट करने का फंक्शन
def save_to_google(df_to_save):
    try:
        headers = df_to_save.columns.tolist()
        rows = df_to_save.fillna("").values.tolist()
        full_data = [headers] + rows
        
        response = requests.post(API_URL, data=json.dumps(full_data), timeout=10)
        if response.status_code == 200 and response.text == "Success":
            return True
    except Exception as e:
        st.error(f"Google Sheet में सेव करने में विफल: {e}")
    return False

# लाइव डेटा लोड करें
df_current = load_data()

# सुनिश्चित करें कि सभी ज़रूरी कॉलम्स मौजूद हों
for col in DEFAULT_COLUMNS:
    if col not in df_current.columns:
        df_current[col] = ""

# --- सेक्शन 1: CSV फ़ाइल से बल्क डेटा अपलोड करें ---
st.header("📁 CSV File Se Bulk Data Upload Karein")
uploaded_file = st.file_uploader("CSV फ़ाइल चुनें", type=["csv"])

if uploaded_file is not None:
    try:
        uploaded_df = pd.read_csv(uploaded_file)
        if st.button("Upload CSV", type="primary"):
            updated_df = pd.concat([df_current, uploaded_df], ignore_index=True)
            if save_to_google(updated_df):
                st.success("CSV डेटा सफलतापूर्वक Google Sheet में लॉक हो गया है!")
                st.rerun()
    except Exception as e:
        st.error(f"CSV फ़ाइल पढ़ने में त्रुटि: {e}")


# --- सेक्शन 2: नया स्टूडेंट डेटा मैनुअली ऐड करें ---
st.header("➕ Naya Student Data Add Karein")

col1, col2, col3, col4 = st.columns(4)
with col1:
    adm_no = st.text_input("Admission No.")
    app_no = st.text_input("Application No.")
    m_name = st.text_input("Mother Name")
    duration = st.text_input("Duration")
with col2:
    eligibility = st.text_input("Eligibility")
    enr_no = st.text_input("Enrollment No.")
    dob = st.text_input("Date of Birth")
    mobile = st.text_input("Mobile No.")
with col3:
    unique_id = st.text_input("Unique ID")
    s_name = st.text_input("Student Name")
    category = st.text_input("Category")
    email = st.text_input("Email ID")
with col4:
    roll_no = st.text_input("Roll No.")
    f_name = st.text_input("Father Name")
    subject = st.text_input("Subject")
    address = st.text_input("Address")

if st.button("Save Student Data", use_container_width=True):
    if s_name.strip() == "":
        st.warning("कृपया कम से कम Student Name ज़रूर भरें।")
    else:
        new_row = {
            "Admission No.": adm_no, "Eligibility": eligibility, "Unique ID": unique_id, "Roll No.": roll_no,
            "Application No.": app_no, "Enrollment No.": enr_no, "Student Name": s_name, "Father Name": f_name,
            "Mother Name": m_name, "Date of Birth": dob, "Category": category, "Subject": subject,
            "Duration": duration, "Mobile No.": mobile, "Email ID": email, "Address": address
        }
        updated_df = pd.concat([df_current, pd.DataFrame([new_row])], ignore_index=True)
        if save_to_google(updated_df):
            st.success("डेटा स्थायी रूप से सेव हो गया है!")
            st.rerun()


# --- सेक्शन 3: डेटा डिलीट करने का विकल्प ---
st.header("🗑️ Delete Student Data")
if not df_current.empty and "Student Name" in df_current.columns and len(df_current) > 0:
    student_list = df_current.apply(lambda row: f"Index {row.name} | {row['Student Name']} (Roll: {row['Roll No.']})", axis=1).tolist()
    selected_student_string = st.selectbox("डिलीट करने के लिए स्टूडेंट चुनें:", ["-- चुनें --"] + student_list)
    
    if selected_student_string != "-- चुनें --":
        selected_idx = int(selected_student_string.split(" | ")[0].split(" ")[1])
        if st.button("चयनित स्टूडेंट का डेटा डिलीट करें", type="primary"):
            updated_df = df_current.drop(index=selected_idx).reset_index(drop=True)
            if save_to_google(updated_df):
                st.success("डेटा हमेशा के लिए डिलीट कर दिया गया है!")
                st.rerun()
else:
    st.info("डेटाबेस अभी खाली है।")


# --- सेक्शन 4: लाइव स्टूडेंट डेटाबेस तालिका ---
st.header("📊 Live Student Database")
if not df_current.empty and len(df_current) > 0:
    display_df = df_current.copy()
    display_df.index = display_df.index + 1
    display_df.index.name = "S. No."
    st.dataframe(display_df, use_container_width=True)
else:
    st.write("दिखाने के लिए कोई डेटा उपलब्ध नहीं है।")


# --- सेक्शन 5: प्रिंट और डाउनलोड विकल्प ---
st.header("📥 Actions")
action_col1, action_col2 = st.columns(2)
with action_col1:
    if not df_current.empty and len(df_current) > 0:
        csv_data = df_current.to_csv(index=False).encode('utf-8')
        st.download_button(label="Download Database as CSV", data=csv_data, file_name="student_database.csv", mime="text/csv", use_container_width=True)
    else:
        st.button("Download Database as CSV", disabled=True, use_container_width=True)
with action_col2:
    st.markdown('<button onclick="window.print()" style="width:100%; height:38px; background-color:#ff4b4b; color:white; border:none; border-radius:4px; cursor:pointer;">Print Page / Save as PDF</button>', unsafe_allow_html=True)
