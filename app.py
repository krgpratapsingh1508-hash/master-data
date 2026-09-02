import streamlit as st
import pandas as pd
import os
import base64
import json
import io

# ==========================================================
# ⚙️ स्टेप 1: पेज का लेआउट सेट करें और डिफ़ॉल्ट थीम्स बनाएं
# ==========================================================
st.set_page_config(layout="wide", page_title="Permanent Shared Live Database")

# डेटा स्टोरेज फ़ाइलों के पाथ और नाम परिभाषा
DB_FILE = "shared_student_database.csv"
CRED_FILE = "user_credentials_v15.json"
MAP_FILE = "column_mapping_schema.json"
PANEL_NAME_FILE = "panel_names_schema.json"
NOTICE_FILE = "notice_board_schema.json"
PRE_LOGIN_CONFIG_FILE = "pre_login_view_config.json"
MERGE_SCHEMA_FILE = "merge_custom_schemas.json"

# डिफ़ॉल्ट कॉन्फ़िगरेशन बैकअप डिक्शनरी (लॉगिन से पहले की थीम के लिए)
DEFAULT_PRE_LOGIN_CONFIG = {
    "show_header_text": True,
    "header_mantra": "ॐ श्री गुरवे नमः",
    "system_title": "Permanent Shared Live Database System",
    "notice_board_border_color": "#FF5733",
    "notice_board_bg_color": "#f9f9f9"
}

# पैनल 13 के लिए डायनेमिक ड्रॉपडाउन लिस्ट स्कीमा बैकअप
DEFAULT_MERGE_SCHEMAS = {
    "file_types": ["admission file", "admission fee file"],
    "academic_years": [str(year) for year in range(2014, 2027)]
}

# डिफ़ॉल्ट कॉलेज नोटिस बोर्ड टेक्स्ट
DEFAULT_NOTICE = (
    "1. यह एक पूर्णतः सुरक्षित, लाइव क्लाउड स्टूडेंट डेटाबेस मैनेजमेंट सिस्टम है।\n"
    "2. डेटा प्रविष्टि, सुधार, स्कॉलरशिप वेरिफिकेशन या परीक्षा परिणाम अपडेट करने के लिए अधिकृत यूजर क्रेडेंशियल्स का उपयोग करें।\n"
    "3. बिना लॉगिन के डेटाबेस तक पहुँच पूर्णतः प्रतिबंधित है। किसी भी समस्या के लिए सुपर-एडमिन से संपर्क करें।"
)

# 🔒 15 पैनल्स के हिसाब से मास्टर भूमिका अधिकार डिक्शनरी
DEFAULT_CREDENTIALS = {
    "admin": {"password": "admin15master", "role": "full_admin", "label": "👑 Super Admin (All 15 Panels Control)"},
    "p1_entry": {"password": "entry1123", "role": "p1_role", "label": "📝 P1: Student Data Onboarding Operator"},
    "p2_admission": {"password": "adm2123", "role": "p2_role", "label": "🎓 P2: Admission Control Manager"},
    "p3_unique": {"password": "uniq3123", "role": "p3_role", "label": "🆔 P3: Unique ID Assignment Manager"},
    "p4_roll": {"password": "roll4123", "role": "p4_role", "label": "🔢 P4: Roll Number Allocation Manager"},
    "p5_enrollment": {"password": "enr5123", "role": "p5_role", "label": "📑 P5: University Enrollment Manager"},
    "p6_scholarship": {"password": "sch6123", "role": "p6_role", "label": "💰 P6: Portal & Scholarship Tracker"},
    "p7_foil": {"password": "foil7123", "role": "p7_role", "label": "🖨️ P7: CCE Foil Sheet Generator"},
    "p8_cce_record": {"password": "cce8123", "role": "p8_role", "label": "📋 P8: Internal Assessment Ledger Entry"},
    "p9_promotion": {"password": "pro9123", "role": "p9_role", "label": "📈 P9: Batch Progression Controller"},
    "p10_result": {"password": "res10123", "role": "p10_role", "label": "📊 P10: Tabulation Register Exam Controller"},
    "p11_notice": {"password": "not11123", "role": "p11_role", "label": "📢 P11: Notice Board Editor"},
    "p12_login_view": {"password": "view12123", "role": "p12_role", "label": "👁️ P12: Pre-Login Landing View Customizer"},
    "p13_merge": {"password": "mrg13123", "role": "p13_role", "label": "🔀 P13: External Database Smart Merge"},
    "p14_viewer": {"password": "view14123", "role": "p14_role", "label": "👁️ P14: Multi-Panel Inspection Window"}
}

# 🛠️ डिफ़ॉल्ट 15 पैनल्स की डिक्शनरी मैपिंग (P1 से P15)
DEFAULT_PANELS = {
    "P1": "Panal entry", "P2": "Panal admission", "P3": "Panal unique",
    "P4": "Panal roll", "P5": "Panal enrollment", "P6": "Panal scholarship",
    "P7": "Panal foil", "P8": "Panal cce record", "P9": "Panal promotion",
    "P10": "Panal result", "P11": "notice board edit", "P12": "login karne se phle jo view dikha hai use edit karne ka",
    "P13": "Panal merge", "P14": "Panal viewer", "P15": "Panel admin"
}

# 🎯 मास्टर स्कीमा कॉलम्स सूची
DEFAULT_COLUMNS = [
    "Admission Year", "Admission Session", "Eligibility Name", "Admission Application Number",
    "Admission Date", "Unique ID", "Roll No.", "Application Enrollment No.",
    "Enrollment No.", "Student Name", "Father Name", "Mother Name", "Date of Birth",
    "Category", "Subject Code", "Subject", "Duration", "Mobile Number", "Email ID", "Address", "Status",
    "Current Year", "Is_From_Merge", "Merge_File_Source"
]

# ==========================================================
# 📁स्टेप 2: डेटा सहेजने और लोड करने वाले कोर फंक्शन्स
# ==========================================================
def load_pre_login_config():
    if os.path.exists(PRE_LOGIN_CONFIG_FILE):
        try:
            with open(PRE_LOGIN_CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict): return data
        except: return DEFAULT_PRE_LOGIN_CONFIG.copy()
    return DEFAULT_PRE_LOGIN_CONFIG.copy()

def save_pre_login_config(config_dict):
    with open(PRE_LOGIN_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config_dict, f, ensure_ascii=False, indent=4)

def load_merge_schemas():
    if os.path.exists(MERGE_SCHEMA_FILE):
        try:
            with open(MERGE_SCHEMA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and "file_types" in data and "academic_years" in data:
                    return data
        except: return DEFAULT_MERGE_SCHEMAS.copy()
    return DEFAULT_MERGE_SCHEMAS.copy()

def save_merge_schemas(schemas_dict):
    with open(MERGE_SCHEMA_FILE, "w", encoding="utf-8") as f:
        json.dump(schemas_dict, f, ensure_ascii=False, indent=4)

def load_credentials():
    if os.path.exists(CRED_FILE):
        try:
            with open(CRED_FILE, "r") as f: return json.load(f)
        except: return DEFAULT_CREDENTIALS.copy()
    else:
        with open(CRED_FILE, "w") as f: json.dump(DEFAULT_CREDENTIALS, f)
        return DEFAULT_CREDENTIALS.copy()

def load_panel_names():
    if os.path.exists(PANEL_NAME_FILE):
        try:
            with open(PANEL_NAME_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: return DEFAULT_PANELS.copy()
    return DEFAULT_PANELS.copy()

def save_panel_names(panel_dict):
    with open(PANEL_NAME_FILE, "w", encoding="utf-8") as f:
        json.dump(panel_dict, f, ensure_ascii=False, indent=4)

def load_column_mappings():
    if os.path.exists(MAP_FILE):
        try:
            with open(MAP_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: return {}
    return {}

def load_notice_board():
    if os.path.exists(NOTICE_FILE):
        try:
            with open(NOTICE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("notice_text", DEFAULT_NOTICE)
        except: return DEFAULT_NOTICE
    return DEFAULT_NOTICE

def save_notice_board(text):
    with open(NOTICE_FILE, "w", encoding="utf-8") as f:
        json.dump({"notice_text": text}, f, ensure_ascii=False, indent=4)

def load_live_data():
    if not os.path.exists(DB_FILE) or os.path.getsize(DB_FILE) == 0:
        df_empty = pd.DataFrame(columns=DEFAULT_COLUMNS)
        df_empty.to_csv(DB_FILE, index=False)
        return df_empty
    try:
        df = pd.read_csv(DB_FILE, dtype=str)
        for col in DEFAULT_COLUMNS:
            if col not in df.columns: df[col] = ""
        if "Is_From_Merge" in df.columns:
            df["Is_From_Merge"] = df["Is_From_Merge"].replace({"": "False", "nan": "False"}).fillna("False")
        return df.fillna("").reset_index(drop=True)
    except:
        return pd.DataFrame(columns=DEFAULT_COLUMNS)

def save_live_data(df_to_save):
    df_to_save.fillna("").astype(str).to_csv(DB_FILE, index=False)

def get_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as image_file:
            return f"data:image/png;base64,{base64.b64encode(image_file.read()).decode()}"
    return ""

# ==========================================================
# 🧠 स्टेप 3: सेशन स्टेट (Session State) वेरिएबल्स इनिशियलाइज़ेशन
# ==========================================================
if "pre_login_config" not in st.session_state or not isinstance(st.session_state.pre_login_config, dict):
    st.session_state.pre_login_config = load_pre_login_config()

if "merge_schemas" not in st.session_state:
    st.session_state.merge_schemas = load_merge_schemas()

if "credentials" not in st.session_state or len(st.session_state.credentials) < 15:
    st.session_state.credentials = load_credentials()

if "column_mappings" not in st.session_state: 
    st.session_state.column_mappings = load_column_mappings()

if "panel_names" not in st.session_state or len(st.session_state.panel_names) < 15:
    st.session_state.panel_names = load_panel_names()

if "notice_text" not in st.session_state:
    st.session_state.notice_text = load_notice_board()

if "user_role" not in st.session_state: st.session_state.user_role = None  
if "logged_username" not in st.session_state: st.session_state.logged_username = None
if "show_login_form" not in st.session_state: st.session_state.show_login_form = False
if "admin_columns_order" not in st.session_state: st.session_state.admin_columns_order = [c for c in DEFAULT_COLUMNS if c not in ["Is_From_Merge", "Merge_File_Source"]]
if "admin_lock_state" not in st.session_state: st.session_state.admin_lock_state = True  
if "admin_unhide_edit" not in st.session_state: st.session_state.admin_unhide_edit = False
if "admin_unhide_move" not in st.session_state: st.session_state.admin_unhide_move = False
if "admin_hide_master_data" not in st.session_state: st.session_state.admin_hide_master_data = False
if "cce_foil_generated" not in st.session_state: st.session_state.cce_foil_generated = False

for k in DEFAULT_PANELS.keys():
    if f"hide_panel_{k}" not in st.session_state: st.session_state[f"hide_panel_{k}"] = False

# 🌟 NameError को रोकने के लिए वेरिएबल्स को ग्लोबल स्तर पर डिफ़ॉल्ट मान दें
role = ""
username = ""
allowed_panels = []
active_tabs_names = []
current_panel_id = None  

# मास्टर रिपॉजिटरी लोड करना
live_db = load_live_data()

def get_display_name(internal_col_name):
    return st.session_state.column_mappings.get(internal_col_name, internal_col_name)

def get_panel_title(panel_id):
    return st.session_state.panel_names.get(panel_id, DEFAULT_PANELS[panel_id])

# ==========================================================
# 🎨 स्टेप 4: डायनेमिक सीएसएस (CSS) रेंडरिंग引擎
# ==========================================================
b_color = st.session_state.pre_login_config.get("notice_board_border_color", "#FF5733")
bg_color = st.session_state.pre_login_config.get("notice_board_bg_color", "#f9f9f9")

st.markdown(f"""
    <style>
    @media print {{
        header, [data-testid="stHeader"], [data-testid="stSidebar"], 
        .stButton, .stFileUploader, [data-testid="stDecoration"], 
        [data-testid="stNotification"], [data-testid="stForm"], .print-hide {{
            display: none !important;
        }}
        @page {{ margin: 5mm; size: A4 landscape; }}
        .main .block-container {{ padding: 0 !important; margin: 0 !important; }}
    }}
    .header-container {{ display: flex; align-items: center; gap: 20px; margin-bottom: 20px; }}
    .header-text {{ display: flex; flex-direction: column; }}
    .header-text h3 {{ margin: 0 !important; padding: 0 !important; color: #1465de; }}
    .header-text h1 {{ margin: 0 !important; }}
    
    .notice-board {{
        background-color: {bg_color};
        border-left: 6px solid {b_color};
        padding: 15px;
        margin-bottom: 25px;
        border-radius: 4px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }}
    .notice-title {{ font-weight: bold; color: #333; margin-bottom: 8px; font-size: 18px; }}
    </style>
""", unsafe_allow_html=True)

# लोगो और हेडर रेंडरिंग
img_base64 = get_image_base64("logo pratap.png")
logo_html = f'<img src="{img_base64}" width="90" style="border-radius: 10px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);"/>' if img_base64 else ""

if st.session_state.pre_login_config.get("show_header_text", True):
    st.markdown(f"""
        <div class="header-container">
            {logo_html}
            <div class="header-text">
                <h3>{st.session_state.pre_login_config.get("header_mantra", "ॐ श्री गुरवे नमः")}</h3>
                <h1>{st.session_state.pre_login_config.get("system_title", "Permanent Shared Live Database System")}</h1>
            </div>
        </div>
    """, unsafe_allow_html=True)

# ==========================================================
# 🛑 स्टेप 5: सुरक्षित लॉगिन ऑथेंटिकेशन गेटवे
# ==========================================================
if st.session_state.user_role is None:
    formatted_notice = "".join([f"<p>{line.strip()}</p>" for line in st.session_state.notice_text.split('\n') if line.strip()])
    
    st.markdown(f"""
        <div class="notice-board">
            <div class="notice-title">📢 कॉलेज सूचना पटल (Official Notice Board)</div>
            {formatted_notice}
        </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.show_login_form:
        if st.button("🔐 Click Here to Open Secure Login System", type="primary", use_container_width=True):
            st.session_state.show_login_form = True
            st.rerun()
            
    if st.session_state.show_login_form:
        st.markdown("---")
        st.subheader("🔒 Enter Secure Gateway Credentials")
        col_l1, col_l2 = st.columns(2)
        
        with col_l1:
            user_list_options = list(st.session_state.credentials.keys())
            def get_lbl(uid): return st.session_state.credentials[uid].get("label", uid)
            user_input = st.selectbox("👤 Select Your User ID / Panel Account:", options=user_list_options, format_func=get_lbl)
            
        with col_l2:
            password_input = st.text_input("🔑 Enter Secure Password:", type="password")
            
        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
            if st.button("🔓 Verify & Access System", type="primary", use_container_width=True):
                if user_input in st.session_state.credentials and st.session_state.credentials[user_input]["password"] == password_input:
                    st.session_state.user_role = st.session_state.credentials[user_input]["role"]
                    st.session_state.logged_username = user_input
                    st.session_state.show_login_form = False
                    st.success("✅ क्रेडेंशियल स्वीकृत! पैनल में प्रवेश किया जा रहा है...")
                    st.rerun()
                else:
                    st.error("❌ गलत पासवर्ड दर्ज किया गया है!")
                    
        with c_btn2:
            if st.button("❌ Close Login Windows", type="secondary", use_container_width=True):
                st.session_state.show_login_form = False
                st.rerun()

# ==========================================================
# 🧭 स्टेप 6: पोस्ट-लॉगिन वर्कस्पेस और पैनल राउटिंग इंजन
# ==========================================================
if st.session_state.user_role is not None:
    role = st.session_state.user_role
    username = st.session_state.logged_username
    
    st.markdown('<div class="print-hide">', unsafe_allow_html=True)
    col_top1, col_top2 = st.columns(2)
    with col_top1:
        st.success(f"🔑 सक्रिय सत्र: {username.upper()} | भूमिका अधिकार: {role.upper()}")
    with col_top2:
        if st.button("🔒 Secure Logout / Exit System", type="primary", use_container_width=True):
            st.session_state.user_role = None
            st.session_state.logged_username = None
            st.session_state.cce_foil_generated = False
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("---")

    if role == "full_admin":
        allowed_panels = list(DEFAULT_PANELS.keys()) 
    elif role == "p1_role": allowed_panels = ["P1", "P14"]
    elif role == "p2_role": allowed_panels = ["P2", "P14"]
    elif role == "p3_role": allowed_panels = ["P3", "P14"]
    elif role == "p4_role": allowed_panels = ["P4", "P14"]
    elif role == "p5_role": allowed_panels = ["P5", "P14"]
    elif role == "p6_role": allowed_panels = ["P6", "P14"]
    elif role == "p7_role": allowed_panels = ["P7", "P14"]
    elif role == "p8_role": allowed_panels = ["P8", "P14"]
    elif role == "p9_role": allowed_panels = ["P9", "P14"]
    elif role == "p10_role": allowed_panels = ["P10", "P14"]
    elif role == "p11_role": allowed_panels = ["P11", "P14"]
    elif role == "p12_role": allowed_panels = ["P12", "P14"]
    elif role == "p13_role": allowed_panels = ["P13", "P14"]
    elif role == "p14_role": allowed_panels = ["P14"]

    active_tabs_names = [f"{p} : {get_panel_title(p)}" for p in allowed_panels if not st.session_state.get(f"hide_panel_{p}", False) or role == "full_admin"]
    
    if not active_tabs_names:
        st.warning("⚠️ वर्तमान में आपकी भूमिका के लिए कोई भी पैनल एक्टिव नहीं किया गया है।")
    else:
        selected_tab_ui = st.sidebar.radio("🧭 Navigate Active Modules:", options=active_tabs_names)
        # 🌟 सुधार: यहाँ केवल शुद्ध स्ट्रिंग (जैसे 'P1') निकालने के लिए [0] इंडेक्स का उपयोग किया गया है
        current_panel_id = selected_tab_ui.split(" : ")[0]

# ----------------------------------------------------------------------
# P1: PANEL ENTRY MODULE
# ----------------------------------------------------------------------
if st.session_state.user_role is not None and current_panel_id == "P1":
    st.header(f"📝 {get_panel_title('P1')} (Student Data Onboarding)")
    entry_method = st.selectbox("⚙️ डेटा एंट्री का माध्यम चुनें:", options=["📁 CSV फ़ाइल बल्क अपलोड (Bulk CSV Upload)", "➕ नया छात्र मैनुअल फॉर्म (Manual Form Entry)"])
    
    if entry_method == "📁 CSV फ़ाइल बल्क अपलोड (Bulk CSV Upload)":
        uploaded_file = st.file_uploader("CSV फ़ाइल चुनें", type=["csv"])
        if uploaded_file is not None:
            if st.button("Upload CSV Now", type="primary", use_container_width=True):
                try:
                    uploaded_df = pd.read_csv(uploaded_file, dtype=str).fillna("")
                    for col in DEFAULT_COLUMNS:
                        if col not in uploaded_df.columns: 
                            uploaded_df[col] = ""
                    cleaned_uploaded_df = uploaded_df[DEFAULT_COLUMNS].copy()
                    
                    cleaned_uploaded_df["Is_From_Merge"] = "False"
                    cleaned_uploaded_df["Merge_File_Source"] = ""
                    
                    updated_df = pd.concat([load_live_data(), cleaned_uploaded_df], ignore_index=True)
                    save_live_data(updated_df)
                    st.success("✅ CSV डेटा सफलतापूर्वक मुख्य डेटाबेस में अपलोड हो गया है!")
                except Exception as e: 
                    st.error(f"त्रुटि: {e}")
                    
    elif entry_method == "➕ नया छात्र मैनुअल फॉर्म (Manual Form Entry)":
        with st.form(key="student_add_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                admission_year = st.text_input("Admission Year")
                eligibility_name = st.text_input("Eligibility Name")
                admission_date = st.text_input("Admission Date")
                roll_no = st.text_input("Roll No.")
                enrollment_no = st.text_input("Enrollment No.")
                f_name = st.text_input("Father Name")
                dob = st.text_input("Date of Birth")
                subject_code = st.text_input("Subject Code")
                subject = st.text_input("Subject")
                mobile = st.text_input("Mobile Number")
            with col2:
                admission_session = st.text_input("Admission Session")
                                admission_app_no = st.text_input("Admission Application Number")
                unique_id = st.text_input("Unique ID")
                app_enroll_no = st.text_input("Application Enrollment No.")
                s_name = st.text_input("Student Name")
                m_name = st.text_input("Mother Name")
                category = st.selectbox("Category", ["General", "OBC", "SC", "ST"])
                duration = st.text_input("Duration")
                email = st.text_input("Email ID")
                address = st.text_input("Address")
                status_input = st.selectbox("Status", ["Regular Student", "Regular", "Pending", "Pass", "EX-STUDENT"])
            submit_student = st.form_submit_button("Save Student Data Systematically", type="primary", use_container_width=True)
            
        if submit_student:
            if s_name.strip() == "": 
                st.warning("Student Name भरना अनिवार्य है।")
            else:
                new_row = {c: "" for c in DEFAULT_COLUMNS}
                new_row.update({
                    "Admission Year": admission_year, "Admission Session": admission_session, 
                    "Eligibility Name": eligibility_name, "Admission Application Number": admission_app_no, 
                    "Admission Date": admission_date, "Unique ID": unique_id, "Roll No.": roll_no, 
                    "Application Enrollment No.": app_enroll_no, "Enrollment No.": enrollment_no, 
                    "Student Name": s_name, "Father Name": f_name, "Mother Name": m_name, 
                    "Date of Birth": dob, "Category": category, "Subject Code": subject_code, 
                    "Subject": subject, "Duration": duration, "Mobile Number": mobile, 
                    "Email ID": email, "Address": address, "Status": status_input,
                    "Is_From_Merge": "False", "Merge_File_Source": ""
                })
                updated_df = pd.concat([load_live_data(), pd.DataFrame([new_row])], ignore_index=True)
                save_live_data(updated_df)
                st.success("✅ नया छात्र रिकॉर्ड सुरक्षित सेव हो गया है!")

# ----------------------------------------------------------------------
# P2: PANEL ADMISSION MODULE (केवल मर्ज किया हुआ डेटा ही दिखाएगा)
# ----------------------------------------------------------------------
elif current_panel_id == "P2":
    st.header(f"🎓 {get_panel_title('P2')} (Admission Control & Payment Tracker)")
    
    if live_db.empty: 
        st.warning("⚠️ डेटाबेस वर्तमान में खाली है। कृपया पहले Panel 1 (Entry) या Panel 13 (Merge) से छात्र लोड करें।")
    else:
        if "admitted payment date" not in live_db.columns:
            live_db["admitted payment date"] = ""
        
        # 🎯 फ़िल्टर लॉजिक: केवल वही डेटा चुनें जो मर्ज पैनल से आया हो
        admission_display_db = live_db[live_db["Is_From_Merge"].astype(str).str.strip().str.lower() == "true"].copy()
        
        if admission_display_db.empty:
            st.info("💡 वर्तमान में एडमीशन पैनल पर कोई रिकॉर्ड नहीं है। यहाँ डेटा तभी दिखाई देगा जब आप Panel 13 (Smart Merge) से 'admission file' या 'admission fee file' मर्ज करेंगे।")
        else:
            st.subheader("📆 Filter Records By Payment Date Range")
            use_date_filter = st.checkbox("Enable Date Range Filter (तिथि सीमा फ़िल्टर सक्रिय करें)", key="p2_enable_date_filter_secure")
            
            if use_date_filter:
                col_dt1, col_dt2 = st.columns(2)
                with col_dt1:
                    start_date = st.date_input("इस तिथि से (From Date):", value=pd.to_datetime("2024-01-01"), key="p2_start_date_secure")
                with col_dt2:
                    end_date = st.date_input("इस तिथि तक (To Date):", value=pd.to_datetime("2026-12-31"), key="p2_end_date_secure")
                
                try:
                    admission_display_db["_parsed_date"] = pd.to_datetime(admission_display_db["admitted payment date"], errors="coerce")
                    admission_display_db = admission_display_db[
                        (admission_display_db["_parsed_date"] >= pd.to_datetime(start_date)) & 
                        (admission_display_db["_parsed_date"] <= pd.to_datetime(end_date))
                    ]
                    admission_display_db = admission_display_db.drop(columns=["_parsed_date"])
                except Exception as date_err:
                    st.error(f"तिथि फ़ॉर्मेट मिलान में तकनीकी त्रुटि: {date_err}")

            st.markdown("---")
            
            # 'Merge_File_Source' कॉलम को लिस्ट लेआउट ग्रिड में शामिल किया गया
            admission_fixed_cols = [
                "Admission Application Number", "Admission Year", "Admission Session", 
                "Student Name", "Father Name", "Admission Date", "Status", "admitted payment date", "Merge_File_Source"
            ]
            
            for target_col in admission_fixed_cols:
                if target_col not in admission_display_db.columns:
                    admission_display_db[target_col] = ""
            
            if role == "full_admin":
                st.subheader("⚙️ Select Columns for View, Print & Export (Admin Power Only)")
                available_to_select = [c for c in live_db.columns if c in DEFAULT_COLUMNS or c == "admitted payment date"]
                selected_columns_to_show = st.multiselect(
                    "ग्रिड में प्रदर्शित करने के लिए कॉलम्स चुनें / हटाएँ:",
                    options=available_to_select,
                    default=[c for c in admission_fixed_cols if c in available_to_select],
                    key="p2_admin_multiselect"
                )
            else:
                selected_columns_to_show = admission_fixed_cols
            
            if not selected_columns_to_show:
                st.warning("⚠️ कृपया विज़ुअलाइज़ेशन ग्रिड प्रदर्शित करने के लिए कम से कम एक कॉलम चुनें।")
            else:
                render_df = admission_display_db[selected_columns_to_show].copy()
                render_df.insert(0, "S.No.", range(1, len(render_df) + 1))
                
                st.write(f"📊 वर्तमान एडमिशन ग्रिड में कुल उपलब्ध छात्र रिकॉर्ड्स (Merged From Files): **{len(render_df)}**")
                
                if role == "full_admin":
                    disabled_cols = ["S.No.", "Student Name", "Father Name", "Merge_File_Source"]
                    st.info("🔓 **एडमिन कंट्रोल मोड:** आपके पास इस ग्रिड को एडिट और सिंक करने का पूर्ण अधिकार है।")
                else:
                    disabled_cols = [c for c in render_df.columns]
                    st.warning("🔒 **रीड-ओनली मोड:** सुरक्षा कारणों से आपके पास इस एडमिशन लिस्ट में बदलाव करने का अधिकार नहीं है।")
                
                edited_admission_df = st.data_editor(
                    render_df, 
                    use_container_width=True, 
                    disabled=disabled_cols,
                    column_config={
                        "Status": st.column_config.SelectboxColumn(
                            "Status", 
                            options=["Regular Student", "Regular", "Pending", "Pass", "EX-STUDENT"],
                            required=True
                        )
                    },
                    key="admission_live_editor_grid_p2_secure_engine", 
                    hide_index=True
                )
                
                if role == "full_admin":
                    if st.button("Save Changes to Live Database", type="primary", use_container_width=True, key="p2_save_secure_btn"):
                        try:
                            clean_edited = edited_admission_df.drop(columns=["S.No."])
                            if "Admission Application Number" not in clean_edited.columns:
                                st.error("❌ डेटा सिंक करने के लिए ग्रिड व्यू में 'Admission Application Number' कॉलम का होना अनिवार्य है!")
                            else:
                                for _, row_edit in clean_edited.iterrows():
                                    target_app_num = str(row_edit["Admission Application Number"]).strip()
                                    idx_matches = live_db[live_db["Admission Application Number"].astype(str).str.strip() == target_app_num].index
                                    
                                    if not idx_matches.empty:
                                        for match_idx in idx_matches:
                                            for col in clean_edited.columns:
                                                if col in live_db.columns and col not in ["Admission Application Number", "Student Name", "Father Name", "Merge_File_Source"]:
                                                    live_db.at[match_idx, col] = str(row_edit[col]).strip()
                                
                                save_live_data(live_db)
                                st.success("🎉 संपूर्ण एडमिशन चेंजेस मास्टर डेटाबेस (Live CSV) में सुरक्षित सिंक हो गए हैं!")
                                st.rerun()
                        except Exception as e:
                            st.error(f"डेटाबेस सिंक चक्र में तकनीकी समस्या आई: {e}")
                
                st.markdown("---")
                col_exp1, col_exp2 = st.columns(2)
                with col_exp1:
                    st.markdown("""
                        <button onclick="window.print()" style="width:100%; height:38px; background-color:#1465de; color:white; border:none; border-radius:4px; font-weight:bold; cursor:pointer;">
                            🖨️ Print Current Selected Grid List (A4 Landscape)
                        </button>
                    """, unsafe_allow_html=True)
                    
                with col_exp2:
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                                                        export_clean_df.to_excel(writer, index=False, sheet_name='Admission_Report')
                            
                            st.download_button(
                                label="📥 Export Current Selection as Excel (.xlsx)",
                                data=buffer.getvalue(),
                                file_name=f"admission_report_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True,
                                key="p2_download_excel_secure_btn"
                            )

            # ----------------------------------------------------------------------
    # P3: PANEL UNIQUE ID MODULE (Student Unique ID Mapping - Isolated View)
    # ----------------------------------------------------------------------
    elif current_panel_id == "P3":
        st.header(f"🆔 {get_panel_title('P3')} (Student Unique ID Mapping Engine)")
        
        if live_db.empty: 
            st.warning("⚠️ डेटाबेस वर्तमान में खाली है। कृपया पहले Panel 1 (Entry) से छात्र डेटा लोड करें।")
        else:
            st.markdown("""
                <div style="background-color: #f0f7ff; border-left: 5px solid #1465de; padding: 10px; border-radius: 4px; margin-bottom: 15px;">
                    📌 <b>ऑपरेटर निर्देश:</b> इस ग्रिड में विशिष्ट पहचान पत्र संख्या (Unique ID) से संबंधित डेटा प्रदर्शित है। सुरक्षा और पारदर्शिता के लिए केवल सुपर एडमिन ही इसमें बदलाव कर सकता है।
                </div>
            """, unsafe_allow_html=True)
            
            # 🔍 Real-time Search Filter Sub-system
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                search_field = st.selectbox("खोजने का माध्यम चुनें (Search By):", ["Student Name", "Admission Application Number", "Father Name"], key="p3_search_field_secure")
            with col_s2:
                search_query = st.text_input(f"यहाँ {search_field} दर्ज करें:", key="p3_search_query_secure").strip()
            
            # Apply dynamic string matching filter to keep runtime workspace clean
            unique_filter_df = live_db.copy()
            if search_query != "":
                unique_filter_df = unique_filter_df[
                    unique_filter_df[search_field].astype(str).str.contains(search_query, case=False, na=False)
                ]
            
            # 🎛️ केवल यूनिक आईडी पैनल के लिए मान्य निश्चित कॉलम्स की सूची (Isolated Layout Rule)
            unique_fixed_cols = ["Admission Application Number", "Student Name", "Father Name", "Unique ID"]
            
            # Auto-verify column integrity inside current system dataframe mapping array
            for col in unique_fixed_cols:
                if col not in unique_filter_df.columns:
                    unique_filter_df[col] = ""
            
            # Format localized output frame canvas layout and inject incremental serial counters
            render_df = unique_filter_df[unique_fixed_cols].copy()
            render_df.insert(0, "S.No.", range(1, len(render_df) + 1))
            
            st.write(f"ग्रिड में प्रदर्शित कुल छात्र रिकॉर्ड संख्या (Matching Records): **{len(render_df)}**")
            
            # 🔐 एडमिट और डिसेबल रिस्ट्रिक्शन इंजन (Security Firewall)
            if role == "full_admin":
                # एडमिन के लिए केवल Unique ID ही एडिट करने योग्य रहेगी
                disabled_cols = ["S.No.", "Admission Application Number", "Student Name", "Father Name"]
                st.info("🔓 **एडमिन कंट्रोल मोड:** आपके पास छात्रों की Unique ID एडिट और सिंक करने का पूर्ण अधिकार है।")
            else:
                # सामान्य ऑपरेटर के लिए पूरे ग्रिड के सभी कॉलम्स लॉक (Read-Only List View) रहेंगे
                disabled_cols = [c for c in render_df.columns]
                st.warning("🔒 **रीड-ओनली मोड:** सुरक्षा कारणों से आपके पास इस लिस्ट में Unique ID बदलने का अधिकार नहीं है।")
            
            # 📊 Transactional Isolated Read/Write Grid Spreadsheet Container
            edited_unique_df = st.data_editor(
                render_df, 
                use_container_width=True, 
                disabled=disabled_cols, 
                column_config={
                    "Unique ID": st.column_config.TextColumn(
                        "Unique ID (Permanent Tracking Key)",
                        help="संस्था द्वारा निर्धारित स्थायी विशिष्ट पहचान पत्र संख्या दर्ज करें",
                        required=True
                    )
                },
                key="unique_live_editor_grid_p3_secure_engine", 
                hide_index=True
            )
            
            # Live master database serialization file updates trigger (केवल सुपर एडमिन को विज़िबल)
            if role == "full_admin":
                if st.button("Save & Sync Unique IDs", type="primary", use_container_width=True, key="p3_save_btn_secure"):
                    try:
                        clean_edited = edited_unique_df.drop(columns=["S.No."])
                        sync_counter = 0
                        
                        # Loop through and map tracking mutations step-by-step
                        for _, row_edit in clean_edited.iterrows():
                            target_app_no = str(row_edit["Admission Application Number"]).strip()
                            unique_val = str(row_edit["Unique ID"]).strip()
                            
                            # Locate structural alignment match indices inside central repository files
                            idx_matches = live_db[live_db["Admission Application Number"].astype(str).str.strip() == target_app_no].index
                            
                            if not idx_matches.empty:
                                for match_idx in idx_matches:
                                    # Overwrite the isolated specific unique id record parameter
                                    live_db.at[match_idx, "Unique ID"] = unique_val
                                    sync_counter += 1
                        
                        # Execute permanent file-write storage stream sequence
                        save_live_data(live_db)
                        st.success(f"🎉 सफलता! कुल {sync_counter} छात्र रिकॉर्ड्स की Unique ID मुख्य डेटाबेस (Live CSV) में सुरक्षित सिंक हो गई है।")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"डेटाबेस सिंक्रोनाइज़ेशन चक्र में तकनीकी समस्या आई: {e}")

    # ----------------------------------------------------------------------
    # P4: PANEL ROLL NO MODULE (University Roll Number Allocation - Isolated View)
    # ----------------------------------------------------------------------
    elif current_panel_id == "P4":
        st.header(f"🔢 {get_panel_title('P4')} (University Roll Number Allocation Engine)")
        
        if live_db.empty: 
            st.warning("⚠️ डेटाबेस वर्तमान में खाली है। कृपया पहले Panel 1 (Entry) से छात्र डेटा लोड करें।")
        else:
            st.markdown("""
                <div style="background-color: #f7f9fa; border-left: 5px solid #28a745; padding: 10px; border-radius: 4px; margin-bottom: 15px;">
                    📌 <b>ऑपरेटर निर्देश:</b> इस ग्रिड में विश्वविद्यालय रोल नंबर (Roll No.) से संबंधित डेटा प्रदर्शित है। सुरक्षा नियमों के अनुसार केवल सुपर एडमिन ही इसमें बदलाव कर सकता. है।
                </div>
            """, unsafe_allow_html=True)
            
            # 🔍 Real-time Local Filtering Sub-system
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                roll_search_field = st.selectbox("खोजने का माध्यम चुनें (Filter By):", ["Student Name", "Unique ID", "Admission Application Number"], key="p4_search_field_secure")
            with col_r2:
                roll_search_query = st.text_input(f"यहाँ {roll_search_field} प्रविष्टि खोजें:", key="p4_search_query_secure").strip()
            
            # Apply dynamic string matching filter onto target schema copy array
            roll_filter_df = live_db.copy()
            if roll_search_query != "":
                roll_filter_df = roll_filter_df[
                    roll_filter_df[roll_search_field].astype(str).str.contains(roll_search_query, case=False, na=False)
                ]
            
            # 🎛️ केवल रोल नंबर पैनल के लिए मान्य निश्चित कॉलम्स की सूची (Isolated Layout Rule)
            roll_fixed_cols = ["Admission Application Number", "Unique ID", "Student Name", "Roll No."]
            
            # Verify structure uniform constraints prior to grid binding operations
            for col in roll_fixed_cols:
                if col not in roll_filter_df.columns:
                    roll_filter_df[col] = ""
            
            # Extract targeted frame layouts and inject visual row sequence indicators
            render_df = roll_filter_df[roll_fixed_cols].copy()
            render_df.insert(0, "S.No.", range(1, len(render_df) + 1))
            
            st.write(f"ग्रिड में प्रदर्शित कुल मैचिंग छात्र रिकॉर्ड संख्या (Active Matrix Records): **{len(render_df)}**")
            
            # 🔐 एडिट और डिसेबल रिस्ट्रिक्शन इंजन (Security Firewall)
            if role == "full_admin":
                # एडमिन के लिए केवल Roll No. ही एडिट करने योग्य रहेगी
                disabled_cols = ["S.No.", "Admission Application Number", "Unique ID", "Student Name"]
                st.info("🔓 **एडमिन कंट्रोल मोड:** आपके पास विश्वविद्यालय रोल नंबर एडिट और सिंक करने का पूर्ण अधिकार है।")
            else:
                # सामान्य ऑपरेटर के लिए पूरे ग्रिड के सभी कॉलम्स लॉक (Read-Only List View) रहेंगे
                disabled_cols = [c for c in render_df.columns]
                st.warning("🔒 **रीड-ओनली मोड:** सुरक्षा कारणों से आपके पास इस लिस्ट में Roll No. बदलने का अधिकार नहीं है।")
            
            # 📊 Transactional Isolated Read/Write Grid Spreadsheet Container
            edited_roll_df = st.data_editor(
                render_df, 
                use_container_width=True, 
                disabled=disabled_cols, 
                column_config={
                    "Roll No.": st.column_config.TextColumn(
                        "University Roll No.",
                        help="विश्वविद्यालय द्वारा आवंटित आधिकारिक परीक्षा रोल नंबर दर्ज करें",
                        required=True
                    )
                },
                key="roll_live_editor_grid_p4_secure_engine", 
                hide_index=True
            )
            
            # Live master structural updates compilation file write pipeline trigger (केवल सुपर एडमिन को विज़िबल)
            if role == "full_admin":
                if st.button("Save & Sync Roll Numbers", type="primary", use_container_width=True, key="p4_save_btn_secure"):
                    try:
                        clean_edited = edited_roll_df.drop(columns=["S.No."])
                        roll_sync_counter = 0
                        
                        # Loop through and map tracking mutations layer by layer
                        for _, row_edit in clean_edited.iterrows():
                            target_app_num = str(row_edit["Admission Application Number"]).strip()
                            roll_number_val = str(row_edit["Roll No."]).strip()
                            
                            # Locate matching transaction references alignment rows indexes inside registry records
                            idx_matches = live_db[live_db["Admission Application Number"].astype(str).str.strip() == target_app_num].index
                            
                            if not idx_matches.empty:
                                for match_idx in idx_matches:
                                    # Overwrite the isolated university roll number data record property parameter
                                    live_db.at[match_idx, "Roll No."] = roll_number_val
                                    roll_sync_counter += 1
                        
                        # Execute permanent local physical save stream write operations
                        save_live_data(live_db)
                        st.success(f"🎉 सफलता! कुल {roll_sync_counter} छात्र रिकॉर्ड्स की Roll No. मुख्य डेटाबेस (Live CSV) में सफलतापूर्वक सिंक और अपडेट हो गई है।")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"डेटाबेस सिंक्रोनाइज़ेशन चक्र में तकनीकी समस्या आई: {e}")

    # ----------------------------------------------------------------------
    # P5: PANEL ENROLLMENT MODULE (University Enrollment Manager - Isolated View)
    # ----------------------------------------------------------------------
    elif current_panel_id == "P5":
        st.header(f"📑 {get_panel_title('P5')} (University Enrollment Manager)")
        
        if live_db.empty: 
            st.warning("⚠️ डेटाबेस वर्तमान में खाली है। कृपया पहले Panel 1 (Entry) से छात्र लोड करें।")
        else:
            st.markdown("""
                <div style="background-color: #fff9e6; border-left: 5px solid #ffc107; padding: 10px; border-radius: 4px; margin-bottom: 15px;">
                    📌 <b>ऑपरेटर निर्देश:</b> इस ग्रिड में विश्वविद्यालय नामांकन (Enrollment No.) से संबंधित डेटा प्रदर्शित है। सुरक्षा नियमों के अनुसार केवल सुपर एडमिन ही इसमें बदलाव कर सकता है।
                </div>
            """, unsafe_allow_html=True)
            
            # यूनीक विषयों (Subjects) की सूची निकालकर फ़िल्टर तैयार करना
            available_subjects = ["All"] + sorted(list(set(live_db["Subject"].dropna().astype(str).str.strip())))
            selected_subject = st.selectbox("Subject (विषय) फ़िल्टर चुनें:", options=available_subjects, key="p5_subject_filter_secure_select")
            
            # फ़िल्टर के आधार पर डेटा को अलग करना
            filtered_enrollment = live_db.copy()
            if selected_subject != "All": 
                filtered_enrollment = filtered_enrollment[filtered_enrollment["Subject"].str.strip() == selected_subject]
            
            # 🎛️ केवल एनरोलमेंट पैनल के लिए मान्य निश्चित कॉलम्स की सूची (Isolated Layout Rule)
            enrollment_fixed_cols = ["Admission Application Number", "Student Name", "Father Name", "Subject", "Application Enrollment No.", "Enrollment No."]
            
            # सुनिश्चित करना कि सभी लक्षित कॉलम्स डेटाफ़्रेम में मौजूद हों
            for col in enrollment_fixed_cols:
                if col not in filtered_enrollment.columns:
                    filtered_enrollment[col] = ""
                    
            # रेंडर टेबल तैयार करना और क्रम संख्या (S.No.) जोड़ना
            render_df = filtered_enrollment[enrollment_fixed_cols].copy()
            render_df.insert(0, "S.No.", range(1, len(render_df) + 1))
            
            st.write(f"ग्रिड में प्रदर्शित कुल छात्र रिकॉर्ड संख्या (Active Enrollment Records): **{len(render_df)}**")
            
            # 🔐 एडमिट और डिसेबल रिस्ट्रिक्शन इंजन (Security Firewall)
            if role == "full_admin":
                # एडमिन के लिए केवल एनरोलमेंट नंबर फ़ील्ड्स ही एडिट करने योग्य रहेंगे
                disabled_cols = ["S.No.", "Admission Application Number", "Student Name", "Father Name", "Subject"]
                st.info("🔓 **एडमिन कंट्रोल मोड:** आपके पास विश्वविद्यालय नामांकन नंबर एडिट और सिंक करने का पूर्ण अधिकार है।")
            else:
                # सामान्य ऑपरेटर के लिए पूरे ग्रिड के सभी कॉलम्स लॉक (Read-Only List View) रहेंगे
                disabled_cols = [c for c in render_df.columns]
                st.warning("🔒 **रीड-ओनली मोड:** सुरक्षा कारणों से आपके पास इस लिस्ट में नामांकन संख्या बदलने का अधिकार नहीं है।")
            
            # डेटा एडिटर ग्रिड
            edited_enrollment_df = st.data_editor(
                render_df, 
                use_container_width=True, 
                disabled=disabled_cols, 
                column_config={
                    "Application Enrollment No.": st.column_config.TextColumn("Application Enrollment No.", help="विश्वविद्यालय आवेदन पंजीकरण संख्या दर्ज करें"),
                    "Enrollment No.": st.column_config.TextColumn("University Enrollment No.", help="विश्वविद्यालय द्वारा आवंटित स्थायी नामांकन संख्या दर्ज करें")
                },
                key="enrollment_live_editor_grid_p5_secure_engine", 
                hide_index=True
            )
            
            # डेटाबेस में लाइव सिंक करने का बटन (केवल सुपर एडमिन को विज़िबल)
            if role == "full_admin":
                if st.button("Save & Sync Enrollment Numbers", type="primary", use_container_width=True, key="p5_save_btn_secure_tracker"):
                    try:
                        clean_edited = edited_enrollment_df.drop(columns=["S.No."])
                        enroll_sync_counter = 0
                        
                        # प्रत्येक एडिट की गई रो को मुख्य डेटाबेस (live_db) से सिंक करना
                        for _, row_edit in clean_edited.iterrows():
                            app_num = str(row_edit["Admission Application Number"]).strip()
                            
                            # 'Admission Application Number' के आधार पर इंडेक्स match खोजना
                            idx_matches = live_db[live_db["Admission Application Number"].astype(str).str.strip() == app_num].index
                            
                            if not idx_matches.empty:
                                for match_idx in idx_matches:
                                    live_db.at[match_idx, "Application Enrollment No."] = str(row_edit["Application Enrollment No."]).strip()
                                    live_db.at[match_idx, "Enrollment No."] = str(row_edit["Enrollment No."]).strip()
                                    enroll_sync_counter += 1
                        
                        # लाइव सी.एस.वी फ़ाइल में डेटा सुरक्षित सेव करना
                        save_live_data(live_db)
                        st.success(f"🎉 सफलता! कुल {enroll_sync_counter} छात्र रिकॉर्ड्स का विश्वविद्यालय नामांकन नंबर मुख्य डेटाबेस (Live CSV) में सिंक और अपडेट हो गया है!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"डेटा सिंक्रोनाइज़ेशन चक्र में तकनीकी समस्या आई: {e}")




