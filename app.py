import streamlit as st
import pandas as pd
import os
import base64
import json

# पेज का लेआउट सेट करें
st.set_page_config(layout="wide")

# प्रिंट फ़ॉर्मेटिंग और लेआउट को व्यवस्थित करने के लिए सीएसएस (CSS)
st.markdown("""
    <style>
    @media print {
        header, [data-testid="stHeader"], [data-testid="stSidebar"], 
        .stButton, .stFileUploader, [data-testid="stDecoration"], 
        [data-testid="stNotification"], [data-testid="stForm"], .print-hide {
            display: none !important;
        }
        @page {
            margin: 5mm;
            size: A4 landscape;
        }
        .main .block-container {
            padding: 0 !important;
            margin: 0 !important;
        }
    }
    .header-container { display: flex; align-items: center; gap: 20px; margin-bottom: 20px; }
    .header-text { display: flex; flex-direction: column; }
    .header-text h3 { margin: 0 !important; padding: 0 !important; color: #FF5733; }
    .header-text h1 { margin: 0 !important; }
    </style>
""", unsafe_allow_html=True)

# लोगो लोड करने का फंक्शन
def get_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as image_file:
            return f"data:image/png;base64,{base64.b64encode(image_file.read()).decode()}"
    return ""

img_base64 = get_image_base64("logo pratap.png")
logo_html = f'<img src="{img_base64}" width="90" style="border-radius: 10px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);"/>' if img_base64 else ""

st.markdown(f"""
    <div class="header-container">
        {logo_html}
        <div class="header-text">
            <h3>ॐ गुरुवर्य नमः</h3>
            <h1>Permanent Shared Live Database</h1>
        </div>
    </div>
""", unsafe_allow_html=True)

DB_FILE = "shared_student_database.csv"
CRED_FILE = "user_credentials.json"
MAP_FILE = "column_mapping_schema.json"

# 🔒 क्रेडेंशियल्स डिफ़ॉल्ट डेटा
DEFAULT_CREDENTIALS = {
    "entry": {"password": "entry123", "role": "data_entry"},
    "viewer": {"password": "viewer123", "role": "list_viewer"},
    "cce": {"password": "cce123", "role": "cce_handler"},
    "admin": {"password": "admin123", "role": "full_admin"}
}

def load_credentials():
    if os.path.exists(CRED_FILE):
        try:
            with open(CRED_FILE, "r") as f:
                return json.load(f)
        except:
            return DEFAULT_CREDENTIALS.copy()
    else:
        with open(CRED_FILE, "w") as f:
            json.dump(DEFAULT_CREDENTIALS, f)
        return DEFAULT_CREDENTIALS.copy()

def save_credentials(creds):
    with open(CRED_FILE, "w") as f:
        json.dump(creds, f)

# 🔄 डायनेमिक कॉलम मैपिंग लोडर और सेवर
def load_column_mappings():
    if os.path.exists(MAP_FILE):
        try:
            with open(MAP_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_column_mappings(mapping_dict):
    with open(MAP_FILE, "w", encoding="utf-8") as f:
        json.dump(mapping_dict, f, ensure_ascii=False, indent=4)

if "credentials" not in st.session_state:
    st.session_state.credentials = load_credentials()

if "column_mappings" not in st.session_state:
    st.session_state.column_mappings = load_column_mappings()

# 🎯 मास्टर कॉलम्स सूची (Subject ID को यहाँ से पूरी तरह हटा दिया गया है)
DEFAULT_COLUMNS = [
    "Admission Year", "Admission Session", "Eligibility Name", "Admission Application Number",
    "Admission Date", "Unique ID", "Roll No.", "Application Enrollment No.",
    "Enrollment No.", "Student Name", "Father Name", "Mother Name", "Date of Birth",
    "Category", "Subject Code", "Subject", "Duration", "Mobile Number", "Email ID", "Address", "Status",
    "Current Year"
]

def load_live_data():
    if not os.path.exists(DB_FILE) or os.path.getsize(DB_FILE) == 0:
        df_empty = pd.DataFrame(columns=DEFAULT_COLUMNS)
        df_empty.to_csv(DB_FILE, index=False)
        return df_empty
    try:
        df = pd.read_csv(DB_FILE, dtype=str)
        for col in DEFAULT_COLUMNS:
            if col not in df.columns:
                df[col] = ""
                
        years_series = pd.to_numeric(df["Admission Year"], errors='coerce')
        if not years_series.dropna().empty:
            max_year = int(years_series.max())
            mapping = {
                max_year: "1 year", max_year - 1: "2 year", max_year - 2: "3 year",
                max_year - 3: "4 year", max_year - 4: "5 year", max_year - 5: "6 year"
            }
            df["Current Year"] = years_series.map(mapping).fillna("EX-STUDENT")
        else:
            df["Current Year"] = "EX-STUDENT"
            
        return df.fillna("").reset_index(drop=True)
    except:
        return pd.DataFrame(columns=DEFAULT_COLUMNS)

def save_live_data(df_to_save):
    df_to_save.fillna("").astype(str).to_csv(DB_FILE, index=False)

# स्टेट मैनेजमेंट इनिशियलाइजेशन
if "user_role" not in st.session_state: st.session_state.user_role = None  
if "upload_success" not in st.session_state: st.session_state.upload_success = False
if "save_success" not in st.session_state: st.session_state.save_success = False
if "admin_columns_order" not in st.session_state: st.session_state.admin_columns_order = DEFAULT_COLUMNS.copy()
if "admin_lock_state" not in st.session_state: st.session_state.admin_lock_state = True  
if "admin_unhide_edit" not in st.session_state: st.session_state.admin_unhide_edit = False
if "admin_unhide_move" not in st.session_state: st.session_state.admin_unhide_move = False
if "cce_foil_generated" not in st.session_state: st.session_state.cce_foil_generated = False

if "admin_hide_entry" not in st.session_state: st.session_state.admin_hide_entry = False
if "admin_hide_viewer" not in st.session_state: st.session_state.admin_hide_viewer = False
if "admin_hide_cce" not in st.session_state: st.session_state.admin_hide_cce = False
if "admin_hide_cred_panel" not in st.session_state: st.session_state.admin_hide_cred_panel = False

live_db = load_live_data()

# 🛠️ हेल्पर फंक्शन: विज़ुअल लेबल्स रिटर्न करना
def get_display_name(internal_col_name):
    return st.session_state.column_mappings.get(internal_col_name, internal_col_name)

# ==========================================================
# 🔒 सिक्योर लॉगिन गेटवे (डेटा लीक सुरक्षा नियंत्रण)
# ==========================================================
if st.session_state.user_role is None:
    st.markdown("---")
    st.subheader("🔒 Multi-User Secure Login Gateway")
    
    user_input = st.selectbox("Username (भूमिका) चुनें:", options=list(st.session_state.credentials.keys()))
    password_input = st.text_input("Password दर्ज करें:", type="password")
    
    if st.button("Secure Login", use_container_width=True, type="primary"):
        if user_input in st.session_state.credentials and st.session_state.credentials[user_input]["password"] == password_input:
            st.session_state.user_role = st.session_state.credentials[user_input]["role"]
            st.success("✅ लॉगिन सफल!")
            st.rerun()
        else:
            st.error("❌ गलत पासवर्ड दर्ज किया गया है!")

# ==========================================================
# 🔑 लॉगिन अधिकृत सत्र (सभी पैनल्स केवल इसके अंदर ही चलेंगे)
# ==========================================================
else:
    st.markdown('<div class="print-hide">', unsafe_allow_html=True)
    if st.button("🔒 मुख्य लॉगआउट (Exit Secure System)", type="primary", use_container_width=True):
        st.session_state.user_role = None
        st.session_state.cce_foil_generated = False
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    role = st.session_state.user_role
    st.info(f"🔑 वर्तमान सत्र भूमिका: **{role.upper()}**")
    st.markdown("---")

    # ----------------------------------------------------------------------
    # 📝 STUDENT DATA ENTRY PANEL - (Role: data_entry, full_admin)
    # ----------------------------------------------------------------------
    if role in ["data_entry", "full_admin"] and not st.session_state.admin_hide_entry:
        st.header("📝 Student Data Entry Panel")
        entry_method = st.selectbox(
            "⚙️ डेटा एंट्री का माध्यम चुनें:",
            options=["📁 CSV फ़ाइल बल्क अपलोड (Bulk CSV Upload)", "➕ नया छात्र मैनुअल फॉर्म (Manual Form Entry)"]
        )
        
        if entry_method == "📁 CSV फ़ाइल बल्क अपलोड (Bulk CSV Upload)":
            uploaded_file = st.file_uploader("CSV फ़ाइल चुनें", type=["csv"])
            if uploaded_file is not None:
                if st.button("Upload CSV Now", type="primary"):
                    try:
                        uploaded_df = pd.read_csv(uploaded_file, dtype=str).fillna("")
                        for col in DEFAULT_COLUMNS:
                            if col not in uploaded_df.columns: uploaded_df[col] = ""
                        cleaned_uploaded_df = uploaded_df[DEFAULT_COLUMNS].copy()
                        updated_df = pd.concat([load_live_data(), cleaned_uploaded_df], ignore_index=True)
                        save_live_data(updated_df)
                        st.success("✅ CSV डेटा सफलतापूर्वक अपलोड हो गया!")
                        st.rerun()
                    except Exception as e: st.error(f"त्रुटि: {e}")

        elif entry_method == "➕ नया छात्र मैनुअल फॉर्म (Manual Form Entry)":
            with st.form(key="student_add_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    admission_year = st.text_input(get_display_name("Admission Year"))
                    eligibility_name = st.text_input(get_display_name("Eligibility Name"))
                    admission_date = st.text_input(get_display_name("Admission Date"))
                    roll_no = st.text_input(get_display_name("Roll No."))
                    enrollment_no = st.text_input(get_display_name("Enrollment No."))
                    f_name = st.text_input(get_display_name("Father Name"))
                    dob = st.text_input(get_display_name("Date of Birth"))
                    
                    # 🎯 क्रम परिवर्तन: सब्जेक्ट आईडी (Subject ID) पूरी तरह हटा दी गई है।
                    # अब सीधे विषय कोड के बाद विषय (Subject) का टेक्स्ट बॉक्स आता है।
                    subject_code = st.text_input(get_display_name("Subject Code"))
                    subject = st.text_input(get_display_name("Subject"))
                    
                    mobile = st.text_input(get_display_name("Mobile Number"))
                with col2:
                    admission_session = st.text_input(get_display_name("Admission Session"))
                    admission_app_no = st.text_input(get_display_name("Admission Application Number"))
                    unique_id = st.text_input(get_display_name("Unique ID"))
                    app_enroll_no = st.text_input(get_display_name("Application Enrollment No."))
                    s_name = st.text_input(get_display_name("Student Name"))
                    m_name = st.text_input(get_display_name("Mother Name"))
                    category = st.selectbox(get_display_name("Category"), ["General", "OBC", "SC", "ST"])
                    duration = st.text_input(get_display_name("Duration"))
                    email = st.text_input(get_display_name("Email ID"))
                    address = st.text_input(get_display_name("Address"))
                    status_input = st.selectbox(get_display_name("Status"), ["Regular", "Pending", "Pass", "Inactive", "EX-STUDENT"])
                submit_student = st.form_submit_button("Save Student Data", type="primary")

            if submit_student:
                if s_name.strip() == "": st.warning("Student Name भरना आवश्यक है।")
                else:
                    new_row = {
                        "Admission Year": admission_year, "Admission Session": admission_session, "Eligibility Name": eligibility_name,
                        "Admission Application Number": admission_app_no, "Admission Date": admission_date, "Unique ID": unique_id,
                        "Roll No.": roll_no, "Application Enrollment No.": app_enroll_no, "Enrollment No.": enrollment_no,
                        "Student Name": s_name, "Father Name": f_name, "Mother Name": m_name, "Date of Birth": dob,
                        "Category": category, "Subject Code": subject_code, "Subject": subject, "Duration": duration,
                        "Mobile Number": mobile, "Email ID": email, "Address": address, "Status": status_input, "Current Year": ""
                    }
                    updated_df = pd.concat([load_live_data(), pd.DataFrame([new_row])], ignore_index=True)
                    save_live_data(updated_df)
                    st.success("✅ डेटा सुरक्षित सेव हुआ!")
                    st.rerun()
        st.markdown("---")

# ----------------------------------------------------------------------
    # 👁️ STUDENT LIVE DATABASE LIST PANEL - (Role: list_viewer, full_admin)
    # ----------------------------------------------------------------------
    if role in ["list_viewer", "full_admin"] and not st.session_state.admin_hide_viewer:
        st.header("Student Live Database List (Viewer Mode)")
        st.markdown('<div class="print-hide">', unsafe_allow_html=True)
        
        # सर्च ड्रॉपडाउन के विकल्पों को भी परिवर्तित नाम के साथ रेंडर करें
        search_options_map = {col: get_display_name(col) for col in DEFAULT_COLUMNS}
        selected_display_col = st.selectbox("🔍 सर्च करने के लिए कॉलम चुनें:", options=list(search_options_map.values()), key="viewer_col")
        selected_search_column = [k for k, v in search_options_map.items() if v == selected_display_col]
        
        search_query = st.text_input(f"'{selected_display_col}' में सर्च करें:", key="viewer_query")
        st.markdown('</div>', unsafe_allow_html=True)

        filtered_db = live_db.copy()
        if search_query:
            filtered_db = filtered_db[filtered_db[selected_search_column].str.contains(search_query, case=False, na=False)]
            
        st.write(f"कुल रिकॉर्ड संख्या: **{len(filtered_db)}**")
        if not filtered_db.empty:
            display_df = filtered_db.copy()
            display_df = display_df.rename(columns={c: get_display_name(c) for c in display_df.columns})
            display_df.insert(0, "S.No.", range(1, len(display_df) + 1))
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            st.markdown('<div class="print-hide">', unsafe_allow_html=True)
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                st.download_button("Download Student List (CSV)", filtered_db.to_csv(index=False).encode('utf-8'), "students.csv", "text/csv", use_container_width=True)
            with col_btn2:
                st.markdown('<button onclick="window.print()" style="width: 100%; background-color: #FF5733; color: white; border: none; padding: 0.5rem; border-radius: 0.5rem; cursor: pointer; font-weight: bold;">Direct Print</button>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else: 
            st.warning("कोई रिकॉर्ड नहीं मिला।")
        st.markdown("---")
