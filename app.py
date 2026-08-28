import streamlit as st
import pandas as pd
import os

# पेज का लेआउट सेट करें
st.set_page_config(layout="wide")

# प्रिंट फ़ॉर्मेटिंग और लेआउट को व्यवस्थित करने के लिए CSS
st.markdown("""
    <style>
    @media print {
        [data-testid="stHeader"], div[element-to-hide="true"], .stButton, .stFileUploader, header, footer, [data-testid="stForm"] {
            display: none !important;
        }
        .main .block-container { padding-top: 0px !important; padding-bottom: 0px !important; }
    }
    
    /* इमेज और टेक्स्ट को एक सीध में रखने के लिए स्टाइल */
    .header-container {
        display: flex;
        align-items: center;
        gap: 20px;
        margin-bottom: 20px;
    }
    .header-text {
        display: flex;
        flex-direction: column;
    }
    .header-text h3 {
        margin: 0 !important;
        padding: 0 !important;
        color: #FF5733;
    }
    .header-text h1 {
        margin: 0 !important;
        padding: 0 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- शीर्ष अनुभाग (Header Section) ---
IMAGE_PATH = "https://w3schools.com" 

st.markdown(f"""
    <div class="header-container">
        <img src="{IMAGE_PATH}" width="90" style="border-radius: 10px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);"/>
        <div class="header-text">
            <h3>Om Guruye Namaha</h3>
            <h1>Permanent Shared Live Database</h1>
        </div>
    </div>
""", unsafe_allow_html=True)

# डेटाबेस फ़ाइल पाथ
DB_FILE = "shared_student_database.csv"

# 🔑 सुरक्षा क्रेडेंशियल्स सेटिंग्स
CORRECT_USERNAME = "admin"
CORRECT_PASSWORD = "admin123"
LIST_PASSWORD = "list789"

DEFAULT_COLUMNS = [
    "Eligibility", "Unique ID", "Roll No.", 
    "Application No.", "Enrollment No.", "Student Name", "Father Name",
    "Mother Name", "Date of Birth", "Category", "Subject", 
    "Duration", "Mobile No.", "Email ID", "Address", "Status"
]

ELIGIBILITY_OPTIONS = ["None", "U.G.", "P.G."]
DURATION_OPTIONS = ["None", "1 Year", "2 Year", "3 Year", "4 Year", "5 Year", "6 Year"]
STATUS_OPTIONS = ["Active", "Pending", "Pass", "Inactive"]

# फ़ाइल से डेटा लोड करने का फंक्शन
def load_live_data():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE, dtype=str)
            # सुनिश्चित करें कि सभी डिफ़ॉल्ट कॉलम्स मौजूद हों
            for col in DEFAULT_COLUMNS:
                if col not in df.columns:
                    df[col] = ""
            return df[DEFAULT_COLUMNS].fillna("").reset_index(drop=True)
        except:
            pass
    # यदि फाइल खाली है या उपलब्ध नहीं है, तो एक खाली डिफ़ॉल्ट रो (Row) के साथ ढांचा वापस भेजें ताकि टेबल हमेशा दिखे
    empty_df = pd.DataFrame(columns=DEFAULT_COLUMNS)
    empty_row = {c: "" for c in DEFAULT_COLUMNS}
    empty_df = pd.concat([empty_df, pd.DataFrame([empty_row])], ignore_index=True)
    return empty_df

# फ़ाइल में डेटा पक्का सुरक्षित करने का फंक्शन
def save_live_data(df_to_save):
    df_to_save.fillna("").astype(str).to_csv(DB_FILE, index=False)

# मेमोरी स्टेट्स सेटअप (Session States)
if "select_all_state" not in st.session_state:
    st.session_state.select_all_state = False
if "database_unlocked" not in st.session_state:
    st.session_state.database_unlocked = False
if "list_unlocked" not in st.session_state:
    st.session_state.list_unlocked = False
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False
if "column_move_mode" not in st.session_state:
    st.session_state.column_move_mode = False
if "current_column_order" not in st.session_state:
    st.session_state.current_column_order = DEFAULT_COLUMNS.copy()

live_db = load_live_data()

# --- पहला लॉक: लॉगिन फॉर्म ---
if not st.session_state.database_unlocked:
    st.subheader("🔒 Admin Login")
    user_input = st.text_input("Username:")
    password_input = st.text_input("Password:", type="password")
    if st.button("Login", type="primary", use_container_width=True):
        if user_input == CORRECT_USERNAME and password_input == CORRECT_PASSWORD:
            st.session_state.database_unlocked = True
            st.rerun()
        else:
            st.error("गलत यूज़रनेम या पासवर्ड!")

# --- यदि पहला डेटाबेस अनलॉक है, तभी अंदर का सिस्टम खुलेगा ---
if st.session_state.database_unlocked:
    
    # मुख्य लॉगआउट बटन
    if st.button("🔒 मुख्य लॉगआउट (Exit File)", type="primary", use_container_width=True):
        st.session_state.database_unlocked = False
        st.session_state.list_unlocked = False
        st.session_state.edit_mode = False
        st.session_state.select_all_state = False
        st.session_state.column_move_mode = False
        st.rerun()

    st.markdown("---")
    
    # 📁 बल्क डेटा अपलोड सेक्शन
    st.header("📁 CSV File Bulk Upload")
    uploaded_file = st.file_uploader("CSV फ़ाइल चुनें", type=["csv"])
    if uploaded_file is not None:
        try:
            uploaded_df = pd.read_csv(uploaded_file, dtype=str).fillna("")
            if st.button("Upload CSV Now"):
                if "Admission No." in uploaded_df.columns:
                    uploaded_df = uploaded_df.drop(columns=["Admission No."])
                # यदि मुख्य लाइव डेटाबेस अभी खाली स्ट्रक्चर में है, तो उसे रिप्लेस करें
                if len(live_db) == 1 and "".join(live_db.iloc[0].values) == "":
                    updated_df = uploaded_df
                else:
                    updated_df = pd.concat([live_db, uploaded_df], ignore_index=True)
                save_live_data(updated_df)
                st.success("डेटा जोड़ दिया गया है!")
                st.rerun()
        except Exception as e:
            st.error(f"त्रुटि: {e}")

    st.markdown("---")

    # ➕ मैनुअल डेटा एंट्री सेक्शन
    st.header("➕ Naya Student Data Add Karein")
    eligibility = st.selectbox("Eligibility", ELIGIBILITY_OPTIONS)
    unique_id = st.text_input("Unique ID")
    roll_no = st.text_input("Roll No.")
    application_no = st.text_input("Application No.")
    enr_no = st.text_input("Enrollment No.")
    s_name = st.text_input("Student Name")
    f_name = st.text_input("Father Name")
    m_name = st.text_input("Mother Name")
    dob = st.text_input("Date of Birth")
    category = st.text_input("Category")
    subject = st.text_input("Subject")
    duration = st.selectbox("Duration", DURATION_OPTIONS)
    mobile = st.text_input("Mobile No.")
    email = st.text_input("Email ID")
    address = st.text_input("Address")
    status_input = st.selectbox("Status", STATUS_OPTIONS)

    if st.button("Save Student Data", type="primary", use_container_width=True):
        if s_name.strip() == "":
            st.warning("कृपया Student Name ज़रूर भरें।")
        else:
            new_row = {
                "Eligibility": eligibility, "Unique ID": unique_id, "Roll No.": roll_no,
                "Application No.": application_no, "Enrollment No.": enr_no, "Student Name": s_name, "Father Name": f_name,
                "Mother Name": m_name, "Date of Birth": dob, "Category": category, "Subject": subject,
                "Duration": duration, "Mobile No.": mobile, "Email ID": email, "Address": address, "Status": status_input
            }
            # यदि केवल खाली स्ट्रक्चर रो मौजूद है, तो उसे हटाकर फ्रेश एंट्री करें
            if len(live_db) == 1 and "".join(live_db.iloc[0].values) == "":
                updated_df = pd.DataFrame([new_row])
            else:
                updated_df = pd.concat([live_db, pd.DataFrame([new_row])], ignore_index=True)
            save_live_data(updated_df)
            st.success("डेटा हमेशा के लिए सेव हो गया है!")
            st.rerun()

    st.markdown("---")

    # 📊 डेटा लिस्ट लॉक और प्रोटेक्शन सेक्शन
    st.header("📊 Live Student Database")
    if not st.session_state.list_unlocked:
        with st.form(key="list_password_form"):
            list_pass = st.text_input("⚠️ छात्र सूची (Data List) देखने के लिए पासवर्ड डालें:", type="password")
            submit_pass = st.form_submit_button("डेटा लिस्ट अनलॉक करें", use_container_width=True)
        if submit_pass:
            if list_pass == LIST_PASSWORD:
                st.session_state.list_unlocked = True
                st.rerun()
            else:
                st.error("गलत लिस्ट पासवर्ड!")

    # --- लिस्ट अनलॉक होने के बाद तालिका दृश्य ---
    if st.session_state.list_unlocked:
        
        # वर्तमान कॉलम आर्डर के आधार पर डेटा को फ़िल्टर करना
        base_df = live_db[st.session_state.current_column_order].copy()
        
        # एक्शन बटन्स की सूची
        if st.button("⬜ सब सेलेक्ट / अन-सेलेक्ट करें", use_container_width=True):
            st.session_state.select_all_state = not st.session_state.select_all_state
            st.rerun()
            
        csv_data = live_db.to_csv(index=False).encode('utf-8')
        st.download_button(label="💾 CSV डाउनलोड करें", data=csv_data, file_name="student_database.csv", mime="text/csv", use_container_width=True)
        
        if st.button("🖨️传递 लिस्ट प्रिंट करें", use_container_width=True):
            st.markdown("""<script>window.print();</script>""", unsafe_allow_html=True)

        # 🔄 "Column Move Mode" बटन को हमेशा "सिर्फ लिस्ट लॉक करें" बटन के ठीक ऊपर लाया गया
        if not st.session_state.column_move_mode:
            if st.button("🔄 Column Move Mode ऑन करें", use_container_width=True, type="secondary"):
                st.session_state.column_move_mode = True
                st.rerun()
        else:
            if st.button("🔒 Column Move मोड बंद और ऑर्डर लॉक करें", use_container_width=True, type="primary"):
                st.session_state.column_move_mode = False
                st.success("कॉलम की स्थिति को सफलतापूर्वक लॉक कर दिया गया है!")
                st.rerun()
            
        if st.button("🔒 सिर्फ लिस्ट लॉक करें", use_container_width=True):
            st.session_state.list_unlocked = False
            st.session_state.edit_mode = False
            st.session_state.column_move_mode = False
            st.rerun()

        st.markdown("---")

