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
                headers = data
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
            
            if save_to_google(updated_df):
                st.session_state.local_db = updated_df
                st.success("CSV डेटा सफलतापूर्वक क्लाउड डेटाबेस में जोड़ दिया गया है!")
                st.rerun()
    except Exception as e:
        st.error(f"CSV फ़ाइल पढ़ने में त्रुटि: {e}")
st.markdown('</div>', unsafe_allow_html=True)


# --- सेक्शन 2: नया स्टूडेंट डेटा मैनुअली ऐड करें (परफेक्ट सिंक और ऑटो-रीसेट फिक्स) ---
st.markdown('<div element-to-hide="true">', unsafe_allow_html=True)
st.header("➕ Naya Student Data Add Karein")

# रीसेट के लिए कॉलबैक फंक्शन - यह सबमिट होते ही बिना डेटा लॉक किए फॉर्म साफ करेगा
def handle_form_submission():
    # वैल्यूज़ सीधे सेशन स्टेट विजेट्स से निकालें
    s_name_val = st.session_state.get("st_nm", "").strip()
    
    if s_name_val == "":
        st.error("कृपया कम से कम Student Name ज़रूर भरें।")
        return

    new_row = {
        "Admission No.": st.session_state.get("adm", ""),
        "Eligibility": st.session_state.get("elig", ""),
        "Unique ID": st.session_state.get("uniq", ""),
        "Roll No.": st.session_state.get("roll", ""),
        "Application No.": st.session_state.get("app", ""),
        "Enrollment No.": st.session_state.get("enr", ""),
        "Student Name": s_name_val,
        "Father Name": st.session_state.get("f_nm", ""),
        "Mother Name": st.session_state.get("m_nm", ""),
        "Date of Birth": st.session_state.get("dob", ""),
        "Category": st.session_state.get("cat", ""),
        "Subject": st.session_state.get("sub", ""),
        "Duration": st.session_state.get("dur", ""),
        "Mobile No.": st.session_state.get("mob", ""),
        "Email ID": st.session_state.get("eml", ""),
        "Address": st.session_state.get("adr", "")
    }
    
    # ताजा लाइव डेटा लाएं
    current_cloud_df = load_data()
    if current_cloud_df.empty:
        current_cloud_df = st.session_state.local_db.copy()
        
    df_current_clean = current_cloud_df.reset_index(drop=True)
    updated_df = pd.concat([df_current_clean, pd.DataFrame([new_row])], ignore_index=True)
    
    # गूगल शीट पर पक्का सेव होने पर ही आगे का कदम उठाएं
    if save_to_google(updated_df):
        st.session_state.local_db = updated_df
        
        # फॉर्म खाली (Reset) करें
        form_keys = ["adm", "app", "m_nm", "dur", "elig", "enr", "dob", "mob", "uniq", "st_nm", "cat", "eml", "roll", "f_nm", "sub", "adr"]
        for key in form_keys:
            st.session_state[key] = ""
            
        st.success("डेटा सफलतापूर्वक क्लाउड डेटाबेस (Google Sheets) में सुरक्षित हो गया है!")
    else:
        st.error("डेटा सर्वर पर सेव नहीं हो पाया। कृपया नेटवर्क की जांच करें।")

# फॉर्म बनाना
with st.form(key="student_form", clear_on_submit=False):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.text_input("Admission No.", key="adm")
        st.text_input("Application No.", key="app")
        st.text_input("Mother Name", key="m_nm")
        st.text_input("Duration", key="dur")
    with col2:
        st.text_input("Eligibility", key="elig")
        st.text_input("Enrollment No.", key="enr")
        st.text_input("Date of Birth", key="dob")
        st.text_input("Mobile No.", key="mob")
    with col3:
        st.text_input("Unique ID", key="uniq")
        st.text_input("Student Name", key="st_nm")
        st.text_input("Category", key="cat")
        st.text_input("Email ID", key="eml")
    with col4:
        st.text_input("Roll No.", key="roll")
        st.text_input("Father Name", key="f_nm")
        st.text_input("Subject", key="sub")
        st.text_input("Address", key="adr")

    # कॉलबैक अटैच किया गया ताकि एरर न आए
    st.form_submit_button("Save Student Data", use_container_width=True, type="primary", on_click=handle_form_submission)

st.markdown('</div>', unsafe_allow_html=True)


# --- सेक्शन 3 और 4: लाइव स्टूडेंट डेटाबेस तालिका और डिलीट सिस्टम ---
st.header("📊 Live Student Database")

# डिवाइस सिंक के लिए मैनुअल रिफ्रेश बटन
if st.button("🔄 क्लाउड से डेटा रिफ्रेश करें"):
    st.session_state.local_db = load_data()
    st.rerun()

if not st.session_state.local_db.empty and len(st.session_state.local_db) > 0:
    display_df = st.session_state.local_db.copy().reset_index(drop=True)
    
    # डिलीट टिक मार्क के लिए फॉल्स (False) वैल्यू वाला कॉलम बनाएं
    display_df.insert(0, "Delete स्टूडेंट", False)
    display_df.index = display_df.index + 1
    display_df.index.name = "S. No."

    # डेटा एडिटर जिससे टिक मार्क बॉक्स इनेबल हो सके
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

    # जिन रोज़ पर टिक लगा है उन्हें पहचानें
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
    
