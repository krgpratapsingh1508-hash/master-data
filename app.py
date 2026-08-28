import streamlit as st
import pandas as pd
import requests
import json

# पेज का लेआउट सेट करें (चौड़ा व्यू)
st.set_page_config(layout="wide")

# सिर्फ डेटा तालिका को प्रिंट करने के लिए स्पेशल CSS कोड (प्रिंट के समय बाकी सब छिप जाएगा)
st.markdown("""
    <style>
    @media print {
        /* ऊपर के सारे फॉर्म, अपलोडर, बटन्स और साइडबार को छुपाएं */
        [data-testid="stHeader"], 
        div[element-to-hide="true"],
        .stButton, 
        .stFileUploader,
        header,
        footer,
        [data-testid="stForm"] {
            display: none !important;
        }
        /* मुख्य कंटेंट का खाली स्पेस सेट करें */
        .main .block-container {
            padding-top: 0px !important;
            padding-bottom: 0px !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

st.title("Permanent Google Sheets Linked Database")

# आपका Google Script Web App URL
API_URL = "https://google.com"

DEFAULT_COLUMNS = [
    "S. No.", "Admission No.", "Eligibility", "Unique ID", "Roll No.", 
    "Application No.", "Enrollment No.", "Student Name", "Father Name",
    "Mother Name", "Date of Birth", "Category", "Subject", 
    "Duration", "Mobile No.", "Email ID", "Address"
]

if "local_db" not in st.session_state:
    st.session_state.local_db = pd.DataFrame(columns=DEFAULT_COLUMNS)

# गूगल शीट से लाइव डेटा लोड करने का फंक्शन
def load_data():
    try:
        response = requests.get(API_URL, timeout=12)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                headers = data[0]
                rows = data[1:]
                if rows:
                    df = pd.DataFrame(rows, columns=headers)
                    return df.loc[:, ~df.columns.duplicated()].reset_index(drop=True)
    except Exception as e:
        pass
    return pd.DataFrame(columns=DEFAULT_COLUMNS)

# गूगल शीट में डेटा पक्का सेव करने का मजबूत फंक्शन
def save_to_google(df_to_save):
    try:
        df_clean = df_to_save.loc[:, ~df_to_save.columns.duplicated()].reset_index(drop=True)
        headers = df_clean.columns.tolist()
        rows = df_clean.fillna("").astype(str).values.tolist()
        full_data = [headers] + rows
        
        # सिंक मोड में पोस्ट करना ताकि डेटा सर्वर पर जाने के बाद ही कोड आगे बढ़े
        with st.spinner("क्लाउड डेटाबेस (Google Sheets) में डेटा सुरक्षित किया जा रहा है..."):
            response = requests.post(API_URL, data=json.dumps(full_data), headers={"Content-Type": "application/json"}, timeout=15)
            if response.status_code == 200:
                return True
    except Exception as e:
        st.error(f"गूगल शीट सिंक एरर: {e}")
    return False

# हमेशा शुरुआत में गूगल शीट से एकदम नया लाइव डेटा खींचें
if st.session_state.local_db.empty:
    fetched_df = load_data()
    if not fetched_df.empty:
        st.session_state.local_db = fetched_df

for col in DEFAULT_COLUMNS:
    if col not in st.session_state.local_db.columns:
        st.session_state.local_db[col] = ""

# --- सेक्शन 1: CSV फ़ाइल अपलोड ---
st.markdown('<div element-to-hide="true">', unsafe_allow_html=True)
st.header("📁 CSV File Se Bulk Data Upload Karein")
uploaded_file = st.file_uploader("CSV फ़ाइल चुनें", type=["csv"])

if uploaded_file is not None:
    try:
        uploaded_df = pd.read_csv(uploaded_file)
        uploaded_df = uploaded_df.loc[:, ~uploaded_df.columns.duplicated()].reset_index(drop=True)
        
        if st.button("Upload CSV", type="primary"):
            df_current_clean = st.session_state.local_db.reset_index(drop=True)
            uploaded_df_clean = uploaded_df.reset_index(drop=True)
            updated_df = pd.concat([df_current_clean, uploaded_df_clean], ignore_index=True)
            
            # --- सेक्शन 2: नया स्टूडेंट डेटा मैनुअली ऐड करें (Form Implementation Fix) ---
st.markdown('<div element-to-hide="true">', unsafe_allow_html=True)
st.header("➕ Naya Student Data Add Karein")

# रिसेट करने के लिए सेशन स्टेट में कुंजियाँ (keys) सेट करें
for col_key in ["adm", "app", "m_nm", "dur", "elig", "enr", "dob", "mob", "uniq", "st_nm", "cat", "eml", "roll", "f_nm", "sub", "adr"]:
    if col_key not in st.session_state:
        st.session_state[col_key] = ""

# अब clear_on_submit को False रखेंगे ताकि सेव होने से पहले डेटा डिलीट न हो
with st.form(key="student_form", clear_on_submit=False):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        adm_no = st.text_input("Admission No.", key="adm")
        app_no = st.text_input("Application No.", key="app")
        m_name = st.text_input("Mother Name", key="m_nm")
        duration = st.text_input("Duration", key="dur")
    with col2:
        eligibility = st.text_input("Eligibility", key="elig")
        enr_no = st.text_input("Enrollment No.", key="enr")
        dob = st.text_input("Date of Birth", key="dob")
        mobile = st.text_input("Mobile No.", key="mob")
    with col3:
        unique_id = st.text_input("Unique ID", key="uniq")
        s_name = st.text_input("Student Name", key="st_nm")
        category = st.text_input("Category", key="cat")
        email = st.text_input("Email ID", key="eml")
    with col4:
        roll_no = st.text_input("Roll No.", key="roll")
        f_name = st.text_input("Father Name", key="f_nm")
        subject = st.text_input("Subject", key="sub")
        address = st.text_input("Address", key="adr")

    submit_button = st.form_submit_button("Save Student Data", use_container_width=True, type="primary")

if submit_button:
    if s_name.strip() == "":
        st.warning("कृपया कम से कम Student Name ज़रूर भरें।")
    else:
        new_row = {
            "Admission No.": adm_no, "Eligibility": eligibility, "Unique ID": unique_id, "Roll No.": roll_no,
            "Application No.": app_no, "Enrollment No.": enr_no, "Student Name": s_name, "Father Name": f_name,
            "Mother Name": m_name, "Date of Birth": dob, "Category": category, "Subject": subject,
            "Duration": duration, "Mobile No.": mobile, "Email ID": email, "Address": address
        }
        
        # ताजा डेटा सर्वर से लाएं
        current_cloud_df = load_data()
        if current_cloud_df.empty:
            current_cloud_df = st.session_state.local_db.copy()
            
        df_current_clean = current_cloud_df.reset_index(drop=True)
        updated_df = pd.concat([df_current_clean, pd.DataFrame([new_row])], ignore_index=True)
        
        # पहले गूगल शीट पर पक्का सेव करें, फिर स्टेट साफ करें
        if save_to_google(updated_df):
            st.session_state.local_db = updated_df
            
            # सफलता पूर्वक सेव होने के बाद अब सभी इनपुट बॉक्स को खाली करें
            for col_key in ["adm", "app", "m_nm", "dur", "elig", "enr", "dob", "mob", "uniq", "st_nm", "cat", "eml", "roll", "f_nm", "sub", "adr"]:
                st.session_state[col_key] = ""
                
            st.success("डेटा सफलतापूर्वक क्लाउड डेटाबेस (Google Sheets) में सुरक्षित हो गया है!")
            st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

        new_row = {
            "Admission No.": adm_no, "Eligibility": eligibility, "Unique ID": unique_id, "Roll No.": roll_no,
            "Application No.": app_no, "Enrollment No.": enr_no, "Student Name": s_name, "Father Name": f_name,
            "Mother Name": m_name, "Date of Birth": dob, "Category": category, "Subject": subject,
            "Duration": duration, "Mobile No.": mobile, "Email ID": email, "Address": address
        }
        
        # ताजा डेटा सर्वर से लाएं ताकि किसी और डिवाइस का डेटा डिलीट न हो
        current_cloud_df = load_data()
        if current_cloud_df.empty:
            current_cloud_df = st.session_state.local_db.copy()
            
        df_current_clean = current_cloud_df.reset_index(drop=True)
        updated_df = pd.concat([df_current_clean, pd.DataFrame([new_row])], ignore_index=True)
        
        # पहले गूगल शीट पर पक्का सेव करें, फिर ऐप रीलोड करें
        if save_to_google(updated_df):
            st.session_state.local_db = updated_df
            st.success("डेटा सफलतापूर्वक क्लाउड डेटाबेस (Google Sheets) में सुरक्षित हो गया है!")
            st.rerun()
st.markdown('</div>', unsafe_allow_html=True)


# --- सेक्शन 3 और 4: लाइव स्टूडेंट डेटाबेस तालिका और डिलीट सिस्टम ---
st.header("📊 Live Student Database")

# हर बार रिफ्रेश बटन के बिना भी पेज पर लाइव क्लाउड डेटा लोड रखने के लिए सहायता
if st.button("🔄 क्लाउड से डेटा रिफ्रेश करें"):
    st.session_state.local_db = load_data()
    st.rerun()

if not st.session_state.local_db.empty and len(st.session_state.local_db) > 0:
    display_df = st.session_state.local_db.copy().reset_index(drop=True)
    
    # प्रिंट व्यू में 'Delete स्टूडेंट' कॉलम न दिखे इसके लिए कंडीशन सेटअप
    display_df.insert(0, "Delete स्टूडेंट", False)
    display_df.index = display_df.index + 1
    display_df.index.name = "S. No."

    edited_df = st.data_editor(
        display_df,
        hide_index=False,
        column_config={
            "Delete स्टूडेंट": st.column_config.CheckboxColumn(
                "Delete स्टूडेंट",
                help="डेटा डिलीट करने के लिए टिक करें",
                default=False,
            )
        },
        disabled=[col for col in display_df.columns if col != "Delete student" and col != "Delete स्टूडेंट"],
        use_container_width=True
    )

    selected_rows = edited_df[edited_df["Delete स्टूडेंट"] == True]

    if len(selected_rows) > 0:
        st.markdown('<div element-to-hide="true">', unsafe_allow_html=True)
        st.warning(f"आपने {len(selected_rows)} स्टूडेंट को डिलीट करने के लिए चुना है।")
        if st.button("🗑️ चयनित स्टूडेंट का डेटा डिलीट करें", type="primary"):
            indices_to_drop = [int(idx) - 1 for idx in selected_rows.index]
            
            # ताजा लाइव क्लाउड डेटा पर एक्शन लें ताकि डेटा सिंक रहे
            current_cloud_df = load_data()
            if current_cloud_df.empty:
                current_cloud_df = st.session_state.local_db.copy()
                
            df_current_clean = current_cloud_df.reset_index(drop=True)
            updated_df = df_current_clean.drop(index=indices_to_drop).reset_index(drop=True)
            
            if save_to_google(updated_df):
                st.session_state.local_db = updated_df
                st.success("चुने गए स्टूडेंट्स का डेटा सफलतापुर्वक डिलीट कर दिया गया है!")
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("डेटाबेस अभी खाली है या लोड हो रहा है...")


# --- SECTION 5: प्रिंट और डाउनलोड विकल्प ---
st.markdown('<div element-to-hide="true">', unsafe_allow_html=True)
st.header("📥 Actions")
action_col1, action_col2 = st.columns(2)
with action_col1:
    csv_data = st.session_state.local_db.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Database as CSV", 
        data=csv_data, 
        file_name="student_database.csv", 
        mime="text/csv", 
        use_container_width=True
    )
with action_col2:
    # सुधरा हुआ प्रिंट बटन जो सिर्फ डेटा टेबल को टारगेट करेगा
    st.markdown('<button onclick="window.print()" style="width:100%; height:38px; background-color:#ff4b4b; color:white; border:none; border-radius:4px; cursor:pointer; font-weight:bold;">PRINT TABLE / SAVE AS PDF</button>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
