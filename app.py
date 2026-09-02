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

# न्यू कस्टमाइज़्ड सूचियों के लिए स्कीमा फ़ाइल पाथ
DYNAMIC_LISTS_FILE = "p1_dynamic_lists_schema.json"

# डिफ़ॉल्ट कॉन्फ़िगरेशन बैकअप डिक्शनरी (लॉगिन से पहले की थीम के लिए)
DEFAULT_PRE_LOGIN_CONFIG = {
    "show_header_text": True,
    "header_mantra": "ॐ श्री गुरवे नमः",
    "system_title": "Permanent Shared Live Database System",
    "notice_board_border_color": "#FF5733",
    "notice_board_bg_color": "#f9f9f9"
}

# 🎯 Panel 1 के लिए डिफ़ॉल्ट 3 स्क्रॉल सूचियों का स्कीमा बैकअप
DEFAULT_DYNAMIC_LISTS = {
    "file_types": [
        "admission file", "admission fee file", "unique id file", 
        "roll no file", "enrollment file", "promotion file", "result file"
    ],
    "academic_years": [str(year) for year in range(2014, 2027)],
    "academic_sessions": [f"{year}-{str(year+1)[2:]}" for year in range(2014, 2027)]
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
    "p11_notice": {"password": "not11123", "role": "p11_role", "label": "📢 P11: System Informer Block"},
    "p12_login_view": {"password": "view12123", "role": "p12_role", "label": "📢 P12: Desk Board Editer"},
    "p13_merge": {"password": "mrg13123", "role": "p13_role", "label": "🔀 P13: External Database Smart Merge"},
    "p14_viewer": {"password": "view14123", "role": "p14_role", "label": "👁️ P14: Multi-Panel Inspection Window"}
}

# 🛠️ डिफ़ॉल्ट 15 पैनल्स की डिक्शनरी मैपिंग (P1 से P15)
DEFAULT_PANELS = {
    "P1": "Panal entry", "P2": "Panal admission", "P3": "Panal unique",
    "P4": "Panal roll", "P5": "Panal enrollment", "P6": "Panal scholarship",
    "P7": "Panal foil", "P8": "Panal cce record", "P9": "Panal promotion",
    "P10": "Panal result", "P11": "notice board info", "P12": "📢 Desk Board Editer",
    "P13": "Panal merge", "P14": "Panal viewer", "P15": "Panel admin"
}

# 🎯 मास्टर स्कीमा कॉलम्स सूची
DEFAULT_COLUMNS = [
    "Admission Year", "Admission Session", "Eligibility Name", "Admission Application Number",
    "Admission Date", "Unique ID", "Roll No.", "Application Enrollment No.",
    "Enrollment No.", "Student Name", "Father Name", "Mother Name", "Date of Birth",
    "Category", "Subject Code", "Subject", "Duration", "Mobile Number", "Email ID", "Address", "Status",
    "Current Year", "Application Number", "Student Abc Id", "Gender", "Admission Category", "Degree",
    "Branch", "Minor Subjects", "Vocational Subjects", "MDC Subjects", "PW/Ap/CE Subjects",
    "Admssion & Enrollment Fees", "Scholarship Name", "Payment Date"
]

# ==========================================================
# 📁 स्टेप 2: डेटा सहेजने और लोड करने वाले कोर फंक्शन्स
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

def load_dynamic_lists():
    if os.path.exists(DYNAMIC_LISTS_FILE):
        try:
            with open(DYNAMIC_LISTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and "file_types" in data and "academic_years" in data and "academic_sessions" in data:
                    return data
        except: return DEFAULT_DYNAMIC_LISTS.copy()
    return DEFAULT_DYNAMIC_LISTS.copy()

def save_dynamic_lists(lists_dict):
    with open(DYNAMIC_LISTS_FILE, "w", encoding="utf-8") as f:
        json.dump(lists_dict, f, ensure_ascii=False, indent=4)

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

if "dynamic_lists" not in st.session_state:
    st.session_state.dynamic_lists = load_dynamic_lists()

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
if "admin_columns_order" not in st.session_state: st.session_state.admin_columns_order = DEFAULT_COLUMNS.copy()
if "admin_lock_state" not in st.session_state: st.session_state.admin_lock_state = True  
if "admin_unhide_edit" not in st.session_state: st.session_state.admin_unhide_edit = False
if "admin_unhide_move" not in st.session_state: st.session_state.admin_unhide_move = False
if "admin_hide_master_data" not in st.session_state: st.session_state.admin_hide_master_data = False
if "admin_hide_master_data" not in st.session_state: st.session_state.admin_hide_master_data = False
if "cce_foil_generated" not in st.session_state: st.session_state.cce_foil_generated = False

for k in DEFAULT_PANELS.keys():
    if f"hide_panel_{k}" not in st.session_state: st.session_state[f"hide_panel_{k}"] = False

# मास्टर रिपॉजिटरी लोड करना
live_db = load_live_data()

# ⚙️ स्टेप 2.5: पैनल 1 के लिए डायनेमिक ड्रॉपडाउन लिस्ट स्कीमा बैकअप और लोड इंजन
if "p1_dropdown_schemas" not in st.session_state:
    P1_SCHEMA_FILE = "p1_dropdown_config_schema.json"
    DEFAULT_P1_SCHEMAS = {
        "file_types": [
            "admission file", "admission fee file", "Unique id file", 
            "Roll No File", "Enrollment File", "Promotion File", "Result File"
        ],
        "academic_years": [str(year) for year in range(2014, 2027)],
        "academic_sessions": [f"{year}-{str(year+1)[2:]}" for year in range(2014, 2027)]
    }
    if os.path.exists(P1_SCHEMA_FILE):
        try:
            with open(P1_SCHEMA_FILE, "r", encoding="utf-8") as f:
                st.session_state.p1_dropdown_schemas = json.load(f)
        except:
            st.session_state.p1_dropdown_schemas = DEFAULT_P1_SCHEMAS.copy()
    else:
        st.session_state.p1_dropdown_schemas = DEFAULT_P1_SCHEMAS.copy()

def save_p1_dropdown_schemas():
    P1_SCHEMA_FILE = "p1_dropdown_config_schema.json"
    with open(P1_SCHEMA_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.p1_dropdown_schemas, f, ensure_ascii=False, indent=4)

def get_display_name(internal_col_name):
    return st.session_state.column_mappings.get(internal_col_name, internal_col_name)

def get_panel_title(panel_id):
    # पी12 का नाम हमेशा 'desh Board Editer' दिखाने के लिए कंडीशन
    if panel_id == "P12":
        return "desh Board Editer"
    return st.session_state.panel_names.get(panel_id, DEFAULT_PANELS[panel_id])

# ==========================================================
# 🎨 स्टेप 4: डायनेमिक सीएसएस (CSS) रेंडरिंग इंजन
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
# 🛑स्टेप 5: सुरक्षित लॉगिन ऑथेंटिकेशन गेटवे (ओरिजनल ड्रॉपडाउन सिस्टम)
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
else:
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

    allowed_panels = []
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
        current_panel_id = selected_tab_ui.split(" : ")[0]

        # ----------------------------------------------------------------------
        # P1: PANEL ENTRY MODULE (3 Scroll Lists & Multi-Format Upload System)
        # ----------------------------------------------------------------------
        if current_panel_id == "P1":
            st.header(f"📝 {get_panel_title('P1')} (Student Data Onboarding)")
            entry_method = st.selectbox(
                "⚙️ डेटा एंट्री का माध्यम चुनें:", 
                options=["📁 फ़ाइल बल्क अपलोड (Bulk File Upload)", "➕ नया छात्र मैनुअल फॉर्म (Manual Form Entry)"]
            )
            
            # ----------------------------------------------------------------------
            # 📁 बल्क फ़ाइल अपलोड सब-सिस्टम (Bulk Upload Sub-System)
            # ----------------------------------------------------------------------
            if entry_method == "📁 फ़ाइल बल्क अपलोड (Bulk File Upload)":
                st.subheader("📊 Select Target Configurations Before Upload")
                col_sc1, col_sc2, col_sc3 = st.columns(3)
                
                with col_sc1:
                    p1_file_type = st.selectbox(
                        "1. फ़ाइल प्रकार चुनें (Select File Type):",
                        options=["-- चुनें --"] + st.session_state.p1_dropdown_schemas["file_types"],
                        key="p1_scroll_file_type"
                    )
                with col_sc2:
                    p1_admission_year = st.selectbox(
                        "2. Admission Year चुनें:",
                        options=["-- चुनें --"] + st.session_state.p1_dropdown_schemas["academic_years"],
                        key="p1_scroll_admission_year"
                    )
                with col_sc3:
                    p1_admission_session = st.selectbox(
                        "3. Admission Session चुनें:",
                        options=["-- चुनें --"] + st.session_state.p1_dropdown_schemas["academic_sessions"],
                        key="p1_session_scroll_secure_bulk_main"
                    )

                # 🎯 फ़ायरवॉल कंडीशन और अपलोड लॉजिक
                if (p1_file_type == "-- चुनें --" or 
                    p1_admission_year == "-- चुनें --" or 
                    p1_admission_session == "-- चुनें --"):
                    st.info("💡 कृपया फ़ाइल अपलोड विंडो खोलने के लिए ऊपर दिए गए तीनों विकल्पों (File Segment, Year और Session) का चयन करें।")
                else:
                    st.success(f"✅ कॉन्फ़िगरेशन लॉक: **{p1_file_type.upper()}** | वर्ष: **{p1_admission_year}** | सत्र: **{p1_admission_session}**")
                    
                    # 📁 CSV, XLSX, XLS तीनों फ़ाइल फॉर्मेट्स का सपोर्ट
                    uploaded_file = st.file_uploader(
                        f"अपलोड करने के लिए '{p1_file_type}' की फ़ाइल चुनें:", 
                        type=["csv", "xlsx", "xls"],
                        key="p1_bulk_file_uploader_widget"
                    )
                    
                    if uploaded_file is not None:
                        if st.button("Upload & Send to System Database Now", type="primary", use_container_width=True):
                            try:
                                # फ़ाइल एक्सटेंशन के आधार पर सही रीड इंजन का चयन
                                if uploaded_file.name.endswith('.csv'):
                                    uploaded_df = pd.read_csv(uploaded_file, dtype=str).fillna("")
                                elif uploaded_file.name.endswith('.xlsx'):
                                    uploaded_df = pd.read_excel(uploaded_file, engine='openpyxl', dtype=str).fillna("")
                                elif uploaded_file.name.endswith('.xls'):
                                    try:
                                        uploaded_df = pd.read_excel(uploaded_file, engine='xlrd', dtype=str).fillna("")
                                    except Exception as xls_err:
                                        try:
                                            uploaded_file.seek(0) 
                                            html_tables = pd.read_html(uploaded_file)
                                            if html_tables:
                                                uploaded_df = html_tables[0].astype(str).fillna("")
                                            else:
                                                st.error("फ़ाइल के अंदर कोई मान्य डेटा टेबल नहीं मिली।")
                                                st.stop()
                                        except Exception as html_err:
                                            try:
                                                uploaded_file.seek(0)
                                                raw_text = uploaded_file.read().decode('utf-8', errors='ignore')
                                                import re
                                                rows = re.findall(r'<tr[^>]*>(.*?)</tr>', raw_text, re.DOTALL)
                                                data_list = []
                                                for row in rows:
                                                    cols = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
                                                    cols = [re.sub(r'<[^>]+>', '', c).strip() for c in cols]
                                                    if cols: data_list.append(cols)
                                                if data_list:
                                                    uploaded_df = pd.DataFrame(data_list)
                                                    uploaded_df.columns = uploaded_df.iloc[0]
                                                    uploaded_df = uploaded_df[1:].reset_index(drop=True)
                                                else:
                                                    raise Exception("No table entries found")
                                            except:
                                                st.error("यह .xls फ़ाइल सपोर्टेड नहीं है। कृपया इसे अपने कंप्यूटर में खोलकर '.xlsx' फॉर्मेट में 'Save As' करें और फिर अपलोड करें।")
                                                st.stop()
                                
                                # डेटा क्लीनिंग (स्ट्रिपिंग)
                                uploaded_df = uploaded_df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
                                
                                # यह सुनिश्चित करना कि मास्टर स्कीमा के न्यू कस्टमाइज्ड कॉलम्स मौजूद हों
                                for col in DEFAULT_COLUMNS:
                                    if col not in uploaded_df.columns: 
                                        uploaded_df[col] = ""
                                
                                # यूज़र द्वारा चुने गए पैरामीटर्स को डेटा रो में मैप करना
                                uploaded_df["Admission Year"] = p1_admission_year
                                uploaded_df["Admission Session"] = p1_admission_session
                                
                                if "Uploaded File Type" not in uploaded_df.columns:
                                    uploaded_df["Uploaded File Type"] = p1_file_type
                                
                                cleaned_uploaded_df = uploaded_df[DEFAULT_COLUMNS].copy()
                                
                                # पुराने लाइव डेटाबेस के साथ सुरक्षित रूप से कंबाइन करना
                                current_live_db = load_live_data()
                                updated_df = pd.concat([current_live_db, cleaned_uploaded_df], ignore_index=True)
                                
                                save_live_data(updated_df)
                                st.success(f"🎉 सफलता! '{p1_file_type.upper()}' का डेटा कस्टमाइज्ड एडमिशन स्कीमा के साथ सफलतापूर्वक सेव हो गया है!")
                                st.rerun()
                            except Exception as e: 
                                st.error(f"फ़ाइल प्रोसेसिंग चक्र में तकनीकी त्रुटि आई: {e}")
                                
                        # ----------------------------------------------------------------------
            # ➕ नया छात्र मैनुअल फॉर्म सब-सिस्टम (New Manual Form Custom Layout)
            # ----------------------------------------------------------------------
            elif entry_method == "➕ नया छात्र मैनुअल फॉर्म (Manual Form Entry)":
                with st.form(key="student_add_form", clear_on_submit=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        admission_year = st.selectbox("Admission Year *", options=st.session_state.p1_dropdown_schemas["academic_years"])
                        app_number = st.text_input("Application Number *")
                        abc_id = st.text_input("Student Abc Id")
                        s_name = st.text_input("Student Name *")
                        f_name = st.text_input("Father Name")
                        m_name = st.text_input("Mother Name")
                        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
                        dob = st.text_input("Date Of Birth (DD-MM-YYYY)")
                        category = st.selectbox("Category", ["General", "OBC", "SC", "ST"])
                        adm_category = st.selectbox("Admission Category", ["General", "OBC", "SC", "ST"])
                        degree = st.text_input("Degree")
                        branch = st.text_input("Branch")
                    with col2:
                        admission_session = st.selectbox("Admission Session *", options=st.session_state.p1_dropdown_schemas["academic_sessions"])
                        minor_sub = st.text_input("Minor Subjects")
                        vocational_sub = st.text_input("Vocational Subjects")
                        mdc_sub = st.text_input("MDC Subjects")
                        pw_ap_ce_sub = st.text_input("PW/Ap/CE Subjects")
                        mobile = st.text_input("Mobile Number")
                        email = st.text_input("Email")
                        address = st.text_area("Address", height=68)
                        enroll_no = st.text_input("Enrollment No")
                        fees_paid = st.text_input("Admssion & Enrollment Fees")
                        scholarship_name = st.text_input("Scholarship Name")
                        payment_date = st.text_input("Payment Date (YYYY-MM-DD)")
                    
                    st.markdown("<p style='color:gray;'>* चिन्ह वाले फ़ील्ड्स डेटाबेस ट्रैकिंग के लिए महत्वपूर्ण हैं।</p>", unsafe_allow_html=True)
                    submit_student = st.form_submit_button("Save Student Data Systematically", type="primary", use_container_width=True)
                    
                if submit_student:
                    if s_name.strip() == "" or app_number.strip() == "": 
                        st.warning("⚠️ Student Name और Application Number भरना अनिवार्य है।")
                    else:
                        new_row = {c: "" for c in DEFAULT_COLUMNS}
                        new_row.update({
                            "Application Number": app_number, "Student Abc Id": abc_id, 
                            "Student Name": s_name, "Father Name": f_name, "Mother Name": m_name, 
                            "Gender": gender, "Date Of Birth": dob, "Category": category, 
                            "Admission Category": adm_category, "Degree": degree, "Branch": branch, 
                            "Minor Subjects": minor_sub, "Vocational Subjects": vocational_sub, 
                            "MDC Subjects": mdc_sub, "PW/Ap/CE Subjects": pw_ap_ce_sub, 
                            "Mobile Number": mobile, "Email": email, "Address": address, 
                            "Enrollment No": enroll_no, "Admssion & Enrollment Fees": fees_paid, 
                            "Scholarship Name": scholarship_name, "Payment Date": payment_date,
                            "Admission Year": admission_year, "Admission Session": admission_session, 
                            "Status": "Regular Student", "Current Year": "1"
                        })
                        updated_df = pd.concat([load_live_data(), pd.DataFrame([new_row])], ignore_index=True)
                        save_live_data(updated_df)
                        st.success("✅ नया छात्र रिकॉर्ड नए कस्टमाइज्ड स्कीमा के साथ मास्टर डेटाबेस में सुरक्षित सेव हो गया है!")
                        st.rerun()

        # ----------------------------------------------------------------------
        # P2: PANEL ADMISSION MODULE (Admission Control & Isolated View)
        # ----------------------------------------------------------------------
        elif current_panel_id == "P2":
            st.header(f"🎓 {get_panel_title('P2')} (Admission Control & Payment Tracker)")
            
            if live_db.empty: 
                st.warning("⚠️ डेटाबेस वर्तमान में खाली है। कृपया पहले Panel 1 (Entry) या Panel 13 (Merge) से छात्र लोड करें।")
            else:
                # 📅 डेट रेंज फ़िल्टर सब-सिस्टम
                st.subheader("📆 Filter Records By Payment Date Range")
                use_date_filter = st.checkbox("Enable Date Range Filter (तिथि सीमा फ़िल्टर सक्रिय करें)", key="p2_enable_date_filter_secure")
                
                # बेस डेटा कॉपी बनाएँ
                admission_display_db = live_db.copy()
                
                if use_date_filter:
                    col_dt1, col_dt2 = st.columns(2)
                    with col_dt1:
                        start_date = st.date_input("इस तिथि से (From Date):", value=pd.to_datetime("2024-01-01"), key="p2_start_date_secure")
                    with col_dt2:
                        end_date = st.date_input("इस तिथि तक (To Date):", value=pd.to_datetime("2026-12-31"), key="p2_end_date_secure")
                    
                    try:
                        admission_display_db["_parsed_date"] = pd.to_datetime(admission_display_db["Payment Date"], errors="coerce")
                        admission_display_db = admission_display_db[
                            (admission_display_db["_parsed_date"] >= pd.to_datetime(start_date)) & 
                            (admission_display_db["_parsed_date"] <= pd.to_datetime(end_date))
                        ]
                        admission_display_db = admission_display_db.drop(columns=["_parsed_date"])
                    except Exception as date_err:
                        st.error(f"तिथि फ़ॉर्मेट मिलान में तकनीकी त्रुटि: {date_err}")

                st.markdown("---")
                
                # 🎛️ यूज़र निर्देशानुसार केवल एडमिशन के लिए मान्य निश्चित कॉलम्स की सूची (As Requested)
                admission_fixed_cols = [
                    "Application Number", "Student Abc Id", "Student Name", "Father Name", 
                    "Mother Name", "Gender", "Date Of Birth", "Category", "Admission Category", 
                    "Degree", "Branch", "Minor Subjects", "Vocational Subjects", "MDC Subjects", 
                    "PW/Ap/CE Subjects", "Mobile Number", "Email", "Address", "Enrollment No", 
                    "Admssion & Enrollment Fees", "Scholarship Name", "Payment Date"
                ]
                
                # सुनिश्चित करें कि ये कॉलम्स डेटाबेस स्कीमा में उपलब्ध हों
                for target_col in admission_fixed_cols:
                    if target_col not in admission_display_db.columns:
                        admission_display_db[target_col] = ""
                
                # 🛠️ एडमिन और सामान्य यूज़र के बीच कॉलम विज़िबिलिटी डिसीजन इंजन
                if role == "full_admin":
                    st.subheader("⚙️ Select Columns for View, Print & Export (Admin Power Only)")
                    # एडमिन को सारे कॉलम्स चुनने की आज़ादी दें
                    available_to_select = [c for c in live_db.columns if c in DEFAULT_COLUMNS]
                    selected_columns_to_show = st.multiselect(
                        "ग्रिड में प्रदर्शित करने के लिए कॉलम्स चुनें / हटाएँ:",
                        options=available_to_select,
                        default=[c for c in admission_fixed_cols if c in available_to_select],
                        key="p2_admin_multiselect"
                    )
                else:
                    # सामान्य ऑपरेटर के लिए केवल एडमिशन से जुड़े निश्चित कॉलम्स ही लॉक रहेंगे (No extra columns allowed)
                    selected_columns_to_show = admission_fixed_cols
                
                if not selected_columns_to_show:
                    st.warning("⚠️ कृपया विज़ुअलाइज़ेशन ग्रिड प्रदर्शित करने के लिए कम से कम एक कॉलम चुनें।")
                else:
                    # फ़िल्टर्ड फ्रेम लेआउट तैयार करना और क्रम संख्या (S. No) जोड़ना
                    render_df = admission_display_db[selected_columns_to_show].copy()
                    render_df.insert(0, "S. No", range(1, len(render_df) + 1))
                    
                    st.write(f"📊 वर्तमान एडमिशन ग्रिड में कुल उपलब्ध छात्र रिकॉर्ड्स: **{len(render_df)}**")
                    
                    # 🔐 एडिट और डिसेबल रिस्ट्रिक्शन इंजन (Security Firewall)
                    if role == "full_admin":
                        # एडमिन के लिए केवल S. No, Application Number और नाम लॉक रहेंगे, बाकी वह एडिट कर सकता है
                        disabled_cols = ["S. No", "Application Number", "Student Name", "Father Name"]
                        st.info("🔓 **एडमिन कंट्रोल मोड:** आपके पास इस ग्रिड को एडिट और सिंक करने का पूर्ण अधिकार है।")
                    else:
                        # सामान्य ऑपरेटर के लिए पूरे ग्रिड के सभी कॉलम्स लॉक (Read-Only List View) रहेंगे
                        disabled_cols = [c for c in render_df.columns]
                        st.warning("🔒 **रीड-ओनली मोड:** सुरक्षा कारणों से आपके पास इस एडमिशन लिस्ट में बदलाव करने का अधिकार नहीं है।")
                    
                    # 📊 इंटरएक्टिव डेटा एडिटर ग्रिड
                    edited_admission_df = st.data_editor(
                        render_df, 
                        use_container_width=True, 
                        disabled=disabled_cols,
                        key="admission_live_editor_grid_p2_secure_engine", 
                        hide_index=True
                    )
                    
                    # 💾 सिंक बटन (केवल सुपर एडमिन को दिखेगा और प्रोसेस करेगा)
                    if role == "full_admin":
                        if st.button("Save Changes to Live Database", type="primary", use_container_width=True, key="p2_save_secure_btn"):
                            try:
                                clean_edited = edited_admission_df.drop(columns=["S. No"])
                                if "Application Number" not in clean_edited.columns:
                                    st.error("❌ डेटा सिंक करने के लिए ग्रिड व्यू में 'Application Number' कॉलम का होना अनिवार्य है!")
                                else:
                                    for _, row_edit in clean_edited.iterrows():
                                        target_app_num = str(row_edit["Application Number"]).strip()
                                        idx_matches = live_db[live_db["Application Number"].astype(str).str.strip() == target_app_num].index
                                        
                                        if not idx_matches.empty:
                                            for match_idx in idx_matches:
                                                # एडमिन द्वारा किए गए बदलावों को सिंक करना
                                                for col in clean_edited.columns:
                                                    if col in live_db.columns and col not in ["Application Number", "Student Name", "Father Name"]:
                                                        live_db.at[match_idx, col] = str(row_edit[col]).strip()
                                    
                                    save_live_data(live_db)
                                    st.success("🎉 संपूर्ण एडमिशन चेंजेस मास्टर डेटाबेस (Live CSV) में सुरक्षित सिंक हो गए हैं!")
                                    st.rerun()
                            except Exception as e:
                                st.error(f"डेटाबेस सिंक चक्र में तकनीकी समस्या आई: {e}")
                    
                    # 🖨️ प्रिंट और एक्सेल एक्सपोर्ट ऐक्शन्स पैनल
                    st.markdown("---")
                    col_exp1, col_exp2 = st.columns(2)
                    
                    with col_exp1:
                        st.markdown("""
                            <button onclick="window.print()" style="width:100%; height:38px; background-color:#1465de; color:white; border:none; border-radius:4px; font-weight:bold; cursor:pointer;">
                                🖨️ Print Current Selected Grid List (A4 Landscape)
                            </button>
                        """, unsafe_allow_html=True)
                        
                    with col_exp2:
                        import io
                        buffer = io.BytesIO()
                        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                            export_clean_df = edited_admission_df.drop(columns=["S. No"], errors="ignore")
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
                    search_field = st.selectbox("खोजने का माध्यम चुनें (Search By):", ["Student Name", "Application Number", "Father Name"], key="p3_search_field_secure")
                with col_s2:
                    search_query = st.text_input(f"यहाँ {search_field} दर्ज करें:", key="p3_search_query_secure").strip()
                
                # central repository से फ़िल्टर मैच करना
                unique_filter_df = live_db.copy()
                if search_query != "":
                    unique_filter_df = unique_filter_df[
                        unique_filter_df[search_field].astype(str).str.contains(search_query, case=False, na=False)
                    ]
                
                # केवल यूनिक आईडी पैनल के लिए निश्चित कॉलम्स की सूची
                unique_fixed_cols = ["Application Number", "Student Name", "Father Name", "Unique ID"]
                
                for col in unique_fixed_cols:
                    if col not in unique_filter_df.columns:
                        unique_filter_df[col] = ""
                
                render_df = unique_filter_df[unique_fixed_cols].copy()
                render_df.insert(0, "S. No", range(1, len(render_df) + 1))
                
                st.write(f"ग्रिड में प्रदर्शित कुल छात्र रिकॉर्ड संख्या (Matching Records): **{len(render_df)}**")
                
                if role == "full_admin":
                    disabled_cols = ["S. No", "Application Number", "Student Name", "Father Name"]
                    st.info("🔓 **एडमिन कंट्रोल मोड:** आपके पास छात्रों की Unique ID एडिट और सिंक करने का पूर्ण अधिकार है।")
                else:
                    disabled_cols = [c for c in render_df.columns]
                    st.warning("🔒 **रीड-ओनली मोड:** सुरक्षा कारणों से आपके पास इस लिस्ट में Unique ID बदलने का अधिकार नहीं है।")
                
                edited_unique_df = st.data_editor(
                    render_df, 
                    use_container_width=True, 
                    disabled=disabled_cols, 
                    key="unique_live_editor_grid_p3_secure_engine", 
                    hide_index=True
                )
                
                if role == "full_admin":
                    if st.button("Save & Sync Unique IDs", type="primary", use_container_width=True, key="p3_save_btn_secure"):
                        try:
                            clean_edited = edited_unique_df.drop(columns=["S. No"])
                            sync_counter = 0
                            
                            for _, row_edit in clean_edited.iterrows():
                                target_app_no = str(row_edit["Application Number"]).strip()
                                unique_val = str(row_edit["Unique ID"]).strip()
                                
                                idx_matches = live_db[live_db["Application Number"].astype(str).str.strip() == target_app_no].index
                                
                                if not idx_matches.empty:
                                    for match_idx in idx_matches:
                                        live_db.at[match_idx, "Unique ID"] = unique_val
                                        sync_counter += 1
                            
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
                        📌 <b>ऑपरेटर निर्देश:</b> इस ग्रिड में विश्वविद्यालय रोल नंबर (Roll No.) से संबंधित डेटा प्रदर्शित है। सुरक्षा नियमों के अनुसार केवल सुपर एडमिन ही इसमें बदलाव कर सकता है।
                    </div>
                """, unsafe_allow_html=True)
                
                col_r1, col_r2 = st.columns(2)
                with col_r1:
                    roll_search_field = st.selectbox("खोजने का माध्यम चुनें (Filter By):", ["Student Name", "Unique ID", "Application Number"], key="p4_search_field_secure")
                with col_r2:
                    roll_search_query = st.text_input(f"यहाँ {roll_search_field} प्रविष्टि खोजें:", key="p4_search_query_secure").strip()
                
                roll_filter_df = live_db.copy()
                if roll_search_query != "":
                    roll_filter_df = roll_filter_df[
                        roll_filter_df[roll_search_field].astype(str).str.contains(roll_search_query, case=False, na=False)
                    ]
                
                roll_fixed_cols = ["Application Number", "Unique ID", "Student Name", "Roll No."]
                
                for col in roll_fixed_cols:
                    if col not in roll_filter_df.columns:
                        roll_filter_df[col] = ""
                
                render_df = roll_filter_df[roll_fixed_cols].copy()
                render_df.insert(0, "S. No", range(1, len(render_df) + 1))
                
                st.write(f"ग्रिड में प्रदर्शित कुल मैचिंग छात्र रिकॉर्ड संख्या (Active Matrix Records): **{len(render_df)}**")
                
                if role == "full_admin":
                    disabled_cols = ["S. No", "Application Number", "Unique ID", "Student Name"]
                    st.info("🔓 **एडमिन कंट्रोल मोड:** आपके पास विश्वविद्यालय रोल नंबर एडिट और सिंक करने का पूर्ण अधिकार है।")
                else:
                    disabled_cols = [c for c in render_df.columns]
                    st.warning("🔒 **रीड-ओनली मोड:** सुरक्षा कारणों से आपके पास इस लिस्ट में Roll No. बदलने का अधिकार नहीं है।")
                
                edited_roll_df = st.data_editor(
                    render_df, 
                    use_container_width=True, 
                    disabled=disabled_cols, 
                    key="roll_live_editor_grid_p4_secure_engine", 
                    hide_index=True
                )
                
                if role == "full_admin":
                    if st.button("Save & Sync Roll Numbers", type="primary", use_container_width=True, key="p4_save_btn_secure"):
                        try:
                            clean_edited = edited_roll_df.drop(columns=["S. No"])
                            roll_sync_counter = 0
                            
                            for _, row_edit in clean_edited.iterrows():
                                target_app_num = str(row_edit["Application Number"]).strip()
                                roll_number_val = str(row_edit["Roll No."]).strip()
                                
                                idx_matches = live_db[live_db["Application Number"].astype(str).str.strip() == target_app_num].index
                                
                                if not idx_matches.empty:
                                    for match_idx in idx_matches:
                                        live_db.at[match_idx, "Roll No."] = roll_number_val
                                        roll_sync_counter += 1
                            
                            save_live_data(live_db)
                            st.success(f"🎉 सफलता! कुल {roll_sync_counter} छात्र रिकॉर्ड्स की Roll No. मुख्य डेटाबेस (Live CSV) में सफलतापूर्वक सिंक हो गई है।")
                            st.rerun()
                        except Exception as e:
                            st.error(f"डेटाबेस सिंक्रोनाइज़ेशन चक्र में तकनीकी समस्या आई: {e}")

                # ----------------------------------------------------------------------
        # P5: PANEL ENROLLMENT MODULE (University Enrollment Manager - Isolated View)
        # ----------------------------------------------------------------------
        elif current_panel_id == "P5":
            st.header(f"📑 {get_panel_title('P5')} (University Enrollment Manager)")
            
            if live_db.empty: 
                st.warning("⚠️ डेटाबेस वर्तमान में खाली है। कृपया पहले Panel 1 (Entry) या Panel 13 (Merge) से छात्र लोड करें।")
            else:
                st.markdown("""
                    <div style="background-color: #fff9e6; border-left: 5px solid #ffc107; padding: 10px; border-radius: 4px; margin-bottom: 15px;">
                        📌 <b>ऑपरेटर निर्देश:</b> इस ग्रिड में विश्वविद्यालय नामांकन (Enrollment No) से संबंधित डेटा प्रदर्शित है। सुरक्षा नियमों के अनुसार केवल सुपर एडमिन ही इसमें बदलाव कर सकता है।
                    </div>
                """, unsafe_allow_html=True)
                
                # यूनीक शाखाओं (Branch) की सूची निकालकर फ़िल्टर तैयार करना
                available_subjects = ["All"] + sorted(list(set(live_db["Branch"].dropna().astype(str).str.strip())))
                selected_subject = st.selectbox("Branch (शाखा) फ़िल्टर चुनें:", options=available_subjects, key="p5_subject_filter_secure_select")
                
                # फ़िल्टर के आधार पर डेटा को अलग करना
                filtered_enrollment = live_db.copy()
                if selected_subject != "All": 
                    filtered_enrollment = filtered_enrollment[filtered_enrollment["Branch"].str.strip() == selected_subject]
                
                # 🎛️ केवल एनरोलमेंट पैनल के लिए मान्य निश्चित कॉलम्स की सूची (As Per Custom Layout)
                enrollment_fixed_cols = ["Application Number", "Student Name", "Father Name", "Branch", "Enrollment No"]
                
                # सुनिश्चित करना कि सभी लक्षित कॉलम्स डेटाफ़्रेम में मौजूद हों
                for col in enrollment_fixed_cols:
                    if col not in filtered_enrollment.columns:
                        filtered_enrollment[col] = ""
                        
                # रेंडर टेबल तैयार करना और क्रम संख्या (S. No) जोड़ करना
                render_df = filtered_enrollment[enrollment_fixed_cols].copy()
                render_df.insert(0, "S. No", range(1, len(render_df) + 1))
                
                st.write(f"ग्रिड में प्रदर्शित कुल छात्र रिकॉर्ड संख्या (Active Enrollment Records): **{len(render_df)}**")
                
                # 🔐 एडिट और डिसेबल रिस्ट्रिक्शन इंजन (Security Firewall)
                if role == "full_admin":
                    # एडमिन के लिए केवल एनरोलमेंट नंबर फ़ील्ड ही एडिट करने योग्य रहेगी
                    disabled_cols = ["S. No", "Application Number", "Student Name", "Father Name", "Branch"]
                    st.info("🔓 **एडमिन控制 मोड:** आपके पास विश्वविद्यालय नामांकन संख्या (Enrollment No) एडिट और सिंक करने का पूर्ण अधिकार है।")
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
                        "Enrollment No": st.column_config.TextColumn(
                            "University Enrollment No", 
                            help="विश्वविद्यालय द्वारा आवंटित स्थायी नामांकन संख्या दर्ज करें"
                        )
                    },
                    key="enrollment_live_editor_grid_p5_secure_engine", 
                    hide_index=True
                )
                
                # डेटाबेस में लाइव सिंक करने का बटन (केवल सुपर एडमिन को विज़िबल)
                if role == "full_admin":
                    if st.button("Save & Sync Enrollment Numbers", type="primary", use_container_width=True, key="p5_save_btn_secure_tracker"):
                        try:
                            clean_edited = edited_enrollment_df.drop(columns=["S. No"])
                            enroll_sync_counter = 0
                            
                            # प्रत्येक एडिट की गई रो को मुख्य डेटाबेस (live_db) से सिंक करना
                            for _, row_edit in clean_edited.iterrows():
                                app_num = str(row_edit["Application Number"]).strip()
                                
                                # 'Application Number' के आधार पर इंडेक्स match खोजना
                                idx_matches = live_db[live_db["Application Number"].astype(str).str.strip() == app_num].index
                                
                                if not idx_matches.empty:
                                    for match_idx in idx_matches:
                                        live_db.at[match_idx, "Enrollment No"] = str(row_edit["Enrollment No"]).strip()
                                        enroll_sync_counter += 1
                            
                            # लाइव सी.एस.वी फ़ाइल में डेटा सुरक्षित सेव करना
                            save_live_data(live_db)
                            st.success(f"🎉 सफलता! कुल {enroll_sync_counter} छात्र रिकॉर्ड्स का विश्वविद्यालय नामांकन नंबर मुख्य डेटाबेस (Live CSV) में सिंक और अपडेट हो गया है!")
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"डेटा सिंक्रोनाइज़ेशन चक्र में तकनीकी समस्या आई: {e}")

        # ----------------------------------------------------------------------
        # P6: PANEL SCHOLARSHIP MODULE (Portal & Scholarship Tracker - Isolated View)
        # ----------------------------------------------------------------------
        elif current_panel_id == "P6":
            st.header(f"💰 {get_panel_title('P6')} (Portal & Scholarship Tracker)")
            
            # सुनिश्चित करें कि स्कॉलरशिप स्टेटस कॉलम स्कीमा में मौजूद हो
            if "Scholarship Status" not in live_db.columns: 
                live_db["Scholarship Status"] = "Not Applied"
            
            if live_db.empty:
                st.warning("⚠️ डेटाबेस वर्तमान में खाली है। कृपया पहले Panel 1 (Entry) या Panel 13 (Merge) से छात्र लोड करें।")
            else:
                st.markdown("""
                    <div style="background-color: #f4fbf7; border-left: 5px solid #2e7d32; padding: 10px; border-radius: 4px; margin-bottom: 15px;">
                        📌 <b>ऑपरेटर निर्देश:</b> इस ग्रिड में छात्रवृत्ति प्रोग्रेस (Scholarship Status) से संबंधित डेटा प्रदर्शित है। सुरक्षा नियमों के अनुसार केवल सुपर एडमिन ही इसमें बदलाव कर सकता है।
                    </div>
                """, unsafe_allow_html=True)
                
                # यूनीक श्रेणियों (Category) की सूची निकालकर फ़िल्टर तैयार करना
                available_categories = ["All"] + sorted(list(set(live_db["Category"].dropna().astype(str).str.strip())))
                selected_category = st.selectbox("Category (वर्ग) फ़िल्टर चुनें:", options=available_categories, key="p6_category_filter_secure_select_box")
                
                # फ़िल्टर के आधार पर डेटा को अलग करना
                filtered_scholarship = live_db.copy()
                if selected_category != "All": 
                    filtered_scholarship = filtered_scholarship[filtered_scholarship["Category"].str.strip() == selected_category]
                
                # 🎛️ केवल स्कॉलरशिप पैनल के लिए मान्य निश्चित कॉलम्स की सूची (As Per Custom Layout)
                scholarship_fixed_cols = ["Application Number", "Unique ID", "Student Name", "Category", "Scholarship Name", "Scholarship Status"]
                
                # सुनिश्चित करना कि सभी लक्षित कॉलम्स डेटाफ़्रेम में मौजूद हों
                for col in scholarship_fixed_cols:
                    if col not in filtered_scholarship.columns:
                        filtered_scholarship[col] = ""
                
                # रेंडर टेबल तैयार करना और क्रम संख्या (S. No) जोड़ना
                render_df = filtered_scholarship[scholarship_fixed_cols].copy()
                render_df.insert(0, "S. No", range(1, len(render_df) + 1))
                
                st.write(f"ग्रिड में प्रदर्शित कुल सक्रिय रिकॉर्ड संख्या (Active Matrix Profiles): **{len(render_df)}**")
                
                # 🔐 एडिट और डिसेबल रिस्ट्रिक्शन इंजन (Security Firewall)
                if role == "full_admin":
                    # एडमिन के लिए केवल Scholarship Status फ़ील्ड ही एडिट करने योग्य रहेगी
                    disabled_cols = ["S. No", "Application Number", "Unique ID", "Student Name", "Category", "Scholarship Name"]
                    st.info("🔓 **एडमिन कंट्रोल मोड:** आपके पास छात्रवृत्ति ट्रैकिंग मैट्रिक्स (Scholarship Status) एडिट और सिंक करने का पूर्ण अधिकार है।")
                else:
                    # सामान्य ऑपरेटर के लिए पूरे ग्रिड के सभी कॉलम्स लॉक (Read-Only List View) रहेंगे
                    disabled_cols = [c for c in render_df.columns]
                    st.warning("🔒 **रीड-ओनली मोड:** सुरक्षा कारणों से आपके पास इस लिस्ट में छात्रवृत्ति स्थिति बदलने का अधिकार नहीं है।")
                
                # डेटा एडिटर ग्रिड (ड्रॉपडाउन चयन के साथ)
                edited_scholarship_df = st.data_editor(
                    render_df, 
                    use_container_width=True, 
                    disabled=disabled_cols, 
                    column_config={
                        "Scholarship Status": st.column_config.SelectboxColumn(
                            "Scholarship Status", 
                            options=["Not Applied", "Applied", "Sanctioned", "Disbursed", "Rejected"],
                            required=True,
                            help="छात्रवृत्ति आवेदन की वर्तमान स्थिति चुनें"
                        )
                    }, 
                    key="scholarship_live_editor_grid_p6_secure_engine", 
                    hide_index=True
                )
                
                # डेटाबेस में लाइव सिंक करने का बटन (केवल सुपर एडमिन को विज़िबल)
                if role == "full_admin":
                    if st.button("Save & Sync Scholarship Matrix", type="primary", use_container_width=True, key="p6_save_btn_secure_tracker_engine"):
                        try:
                            clean_edited = edited_scholarship_df.drop(columns=["S. No"])
                            scholarship_sync_counter = 0
                            
                            # प्रत्येक एडिट की गई रो को मुख्य डेटाबेस (live_db) से सिंक करना
                            for _, row_edit in clean_edited.iterrows():
                                app_num = str(row_edit["Application Number"]).strip()
                                
                                # 'Application Number' के आधार पर इंडेक्स match खोजना
                                idx_matches = live_db[live_db["Application Number"].astype(str).str.strip() == app_num].index
                                
                                if not idx_matches.empty:
                                    for match_idx in idx_matches:
                                        live_db.at[match_idx, "Scholarship Status"] = str(row_edit["Scholarship Status"]).strip()
                                        scholarship_sync_counter += 1
                            
                            # लाइव सी.एस.वी फ़ाइल में डेटा सुरक्षित सेव करना
                            save_live_data(live_db)
                            st.success(f"🎉 सफलता! कुल {scholarship_sync_counter} छात्र रिकॉर्ड्स का छात्रवृत्ति स्टेटस डेटा मुख्य डेटाबेस (Live CSV) में सुरक्षित सिंक हो गया है!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"डेटा सिंक्रोनाइज़ेशन चक्र में तकनीकी समस्या आई: {e}")

        # ----------------------------------------------------------------------
        # P7: PANEL FOIL SHEET GENERATOR MODULE (Smart Year Mapping Engine)
        # ----------------------------------------------------------------------
        elif current_panel_id == "P7":
            st.header(f"🖨️ {get_panel_title('P7')} (University CCE Foil Sheet Generator)")
            
            def num_to_words(num_str):
                try:
                    num = int(float(num_str))
                    words = {
                        0: "Zero", 1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five",
                        6: "Six", 7: "Seven", 8: "Eight", 9: "Nine", 10: "Ten",
                        11: "Eleven", 12: "Twelve", 13: "Thirteen", 14: "Fourteen", 15: "Fifteen",
                        16: "Sixteen", 17: "Seventeen", 18: "Eighteen", 19: "Nineteen", 20: "Twenty"
                    }
                    return words.get(num, str(num))
                except:
                    return ""

            if live_db.empty: 
                st.warning("⚠️ मास्टर डेटाबेस वर्तमान में खाली है। कृपया पहले Panel 1 (Entry) या Panel 13 (Merge) से छात्र लोड करें।")
            else:
                st.markdown('<div class="print-hide">', unsafe_allow_html=True)
                st.subheader("⚙️ Foil Sheet Generation Parameters")
                col_p7_1, col_p7_2 = st.columns(2)
                
                with col_p7_1:
                    # नए स्कीमा के अनुसार 'Branch' का उपयोग करके यूनीक शाखाओं की लिस्ट बनाना
                    unique_subjects = sorted(list(set(live_db['Branch'].dropna().astype(str).str.strip())))
                    selected_subject = st.selectbox(
                        "📚 Select Branch Name:", 
                        options=["All Branches"] + [s for s in unique_subjects if s != ""], 
                        key="cce_p7_sub_secure_engine"
                    )
                with col_p7_2:
                    chosen_option = st.selectbox(
                        "📆 Select Semester / Year Scope:",
                        options=[
                            "1 Semester", "2 Semester", "1 Year",
                            "3 Semester", "4 Semester", "2 Year",
                            "5 Semester", "6 Semester", "3 Year"
                        ],
                        key="cce_p7_sem_secure_engine"
                    )
                
                col_p7_3, col_p7_4 = st.columns(2)
                with col_p7_3:
                    max_marks = st.text_input("Maximum Marks:", value="20")
                with col_p7_4:
                    min_marks = st.text_input("Minimum Pass Marks:", value="07")

                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if st.button("🔄 Generate Foil Sheets Canvas Now", use_container_width=True, type="primary", key="p7_generate_canvas_btn_secure"): 
                        st.session_state.cce_foil_generated = True
                with btn_col2:
                    if st.session_state.get('cce_foil_generated', False):
                        st.markdown('<button onclick="window.print()" style="width:100%; height:38px; background-color:#28a745; color:white; border:none; border-radius:4px; font-weight:bold; cursor:pointer;">🖨️ Direct Print / Save as PDF (A4 Portrait)</button>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
                if st.session_state.get('cce_foil_generated', False):
                    st.markdown("---")
                    foil_filter_df = live_db.copy()
                    
                    target_db_year = "1"
                    if chosen_option in ["1 Semester", "2 Semester", "1 Year"]:
                        target_db_year = "1"
                    elif chosen_option in ["3 Semester", "4 Semester", "2 Year"]:
                        target_db_year = "2"
                    elif chosen_option in ["5 Semester", "6 Semester", "3 Year"]:
                        target_db_year = "3"
                    
                    foil_filter_df["Current Year"] = foil_filter_df["Current Year"].astype(str).str.strip()
                    foil_filter_df = foil_filter_df[foil_filter_df["Current Year"] == target_db_year]
                    
                    if selected_subject != "All Branches": 
                        foil_filter_df = foil_filter_df[foil_filter_df["Branch"].astype(str).str.strip() == selected_subject]
                    
                    if foil_filter_df.empty: 
                        st.warning(f"🔍 चयनित मापदंडों (Current Year: {target_db_year}) के आधार पर डेटाबेस में कोई छात्र रिकॉर्ड नहीं मिला।")
                    else:
                        for essential_col in ["Roll No.", "CCE Marks Obtained", "CCE Attendance Status"]:
                            if essential_col not in foil_filter_df.columns: 
                                foil_filter_df[essential_col] = ""
                        
                        full_html_output = f"""<div style="font-family: Arial, sans-serif; max-width: 650px; margin: 0 auto; border: 1px solid #333; padding: 15px; background-color: #fff; text-align: left;">
<div style="display: flex; justify-content: space-between; font-size: 13px; font-weight: bold; margin-bottom: 10px;">
<span>Paper Code...................</span>
<span>Bundle No...................</span>
</div>
<div style="text-align: center; border-bottom: 2px solid #000; padding-bottom: 5px; margin-bottom: 10px;">
<h2 style="margin: 0; font-size: 16px; font-weight: bold; letter-spacing: 0.5px;">GOVT. K.R.G. POST-GRADUATE AUTONOMOUS COLLEGE,</h2>
<h2 style="margin: 2px 0 0 0; font-size: 16px; font-weight: bold;">GWALIOR (M.P.)</h2>
</div>
<div style="display: flex; justify-content: space-between; font-size: 13px; font-weight: bold; border-bottom: 1px dashed #333; padding-bottom: 5px; margin-bottom: 10px;">
<span>Examination :- CCE</span>
<span>{chosen_option.upper()}</span>
</div>
<div style="font-size: 13px; font-weight: bold; border-bottom: 1px dashed #333; padding-bottom: 5px; margin-bottom: 10px; display: flex; justify-content: space-between;">
<span>Branch: {selected_subject.upper()}</span>
<span>Paper: ...................................</span>
</div>
<div style="display: flex; justify-content: space-between; font-size: 13px; font-weight: bold; border-bottom: 2px double #000; padding-bottom: 5px; margin-bottom: 5px;">
<span>Maximum Marks: {max_marks}</span>
<span>Minimum Pass Marks: {min_marks}</span>
</div>
<div style="text-align: center; font-weight: bold; font-size: 14px; margin-bottom: 10px; letter-spacing: 2px;">FOIL</div>
<table style="width: 100%; border-collapse: collapse; font-family: Arial, sans-serif; font-size: 12px; text-align: center; margin-bottom: 15px;">
<thead>
<tr>
<th colspan="2" style="border: 1px solid #000; padding: 4px; width: 40%; font-size: 11px;">1</th>
<th colspan="2" style="border: 1px solid #000; padding: 4px; width: 60%; font-size: 11px;">2</th>
</tr>
<tr>
<th rowspan="2" style="border: 1px solid #000; padding: 6px; width: 15%;">Code No.</th>
<th rowspan="2" style="border: 1px solid #000; padding: 6px; width: 30%;">Roll No.</th>
<th colspan="2" style="border: 1px solid #000; padding: 4px;">Marks Obtained</th>
</tr>
<tr>
<th style="border: 1px solid #000; padding: 4px; width: 20%;">In Figures</th>
<th style="border: 1px solid #000; padding: 4px; width: 35%;">In Words</th>
</tr>
</thead>
<tbody>"""

                        for idx, row in foil_filter_df.reset_index(drop=True).iterrows():
                            att_status = str(row["CCE Attendance Status"]).strip().upper()
                            if att_status in ["ABSENT", "A", "ABS"]:
                                marks_fig = "ABS"
                                marks_word = "Absent"
                            else:
                                val = str(row["CCE Marks Obtained"]).strip()
                                marks_fig = val if val and val != "nan" else ""
                                marks_word = num_to_words(marks_fig) if marks_fig else ""
                            
                            full_html_output += f"""<tr>
<td style="border: 1px solid #000; padding: 5px; font-weight: bold;">{idx + 1}</td>
<td style="border: 1px solid #000; padding: 5px; font-family: monospace; font-size: 13px;">{row["Roll No."]}</td>
<td style="border: 1px solid #000; padding: 5px; font-weight: bold;">{marks_fig}</td>
<td style="border: 1px solid #000; padding: 5px; text-align: left; padding-left: 10px;">{marks_word}</td>
</tr>"""

                        full_html_output += """</tbody></table>
<div style="margin-top: 15px; font-family: Arial, sans-serif; font-size: 11px; line-height: 1.4; border-top: 1px solid #000; padding-top: 8px;">
<b>Note:</b> Roll Number and Marks awarded to the candidate may be entered under respective columns very carefully. Marks and Roll Number should be legible. These may be checked again to ensure that no mistake remains.
</div>
<div style="margin-top: 25px; font-family: Arial, sans-serif; font-size: 12px; font-weight: bold; line-height: 1.8;">
<div style="border-bottom: 1px dashed #666; padding-bottom: 4px;">Signature of Examiner...............................................................................</div>
<div style="border-bottom: 1px dashed #666; padding-bottom: 4px; margin-top: 5px;">Name of Examiner.....................................................................................</div>
<div style="display: flex; justify-content: space-between; margin-top: 5px;">
<span style="width: 55%; border-bottom: 1px dashed #666; padding-bottom: 4px;">Place............................................................</span>
<span style="width: 40%; border: 1px solid #000; padding: 2px 5px; font-size: 12px; display: inline-block; text-align: left;">Date: &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;| 2026</span>
</div>
</div>
</div>"""
                        
                        st.markdown(full_html_output, unsafe_allow_html=True)

        # ----------------------------------------------------------------------
        # P8: PANEL CCE RECORD MODULE (Internal Assessment Ledger Entry - Isolated View)
        # ----------------------------------------------------------------------
        elif current_panel_id == "P8":
            st.header(f"📋 {get_panel_title('P8')} (Internal Assessment Marks Ledger)")
            
            for f in ["CCE Marks Obtained", "CCE Attendance Status"]:
                if f not in live_db.columns: 
                    live_db[f] = ""
            
            if live_db.empty:
                st.warning("⚠️ मास्टर डेटाबेस वर्तमान में खाली है। कृपया पहले Panel 1 (Entry) से छात्र लोड करें।")
            else:
                st.markdown("""
                    <div style="background-color: #f1f8e9; border-left: 5px solid #558b2f; padding: 10px; border-radius: 4px; margin-bottom: 15px;">
                        📌 <b>ऑपरेटर निर्देश:</b> इस ग्रिड में आंतरिक मूल्यांकन अंक (CCE Marks) से संबंधित डेटा प्रदर्शित है। सुरक्षा नियमों के अनुसार केवल सुपर एडमिन ही इसमें बदलाव कर सकता है।
                    </div>
                """, unsafe_allow_html=True)
                
                available_subjects = ["All"] + sorted(list(set(live_db["Branch"].dropna().astype(str).str.strip())))
                selected_sub = st.selectbox("Branch (शाखा) फ़िल्टर चुनें:", options=available_subjects, key="p8_subject_filter_secure_engine")
                
                filtered_cce = live_db.copy()
                if selected_sub != "All": 
                    filtered_cce = filtered_cce[filtered_cce["Branch"].str.strip() == selected_sub]
                
                cce_fixed_cols = ["Application Number", "Roll No.", "Student Name", "Branch", "CCE Marks Obtained", "CCE Attendance Status"]
                
                for col in cce_fixed_cols:
                    if col not in filtered_cce.columns:
                        filtered_cce[col] = ""
                
                render_df = filtered_cce[cce_fixed_cols].copy()
                render_df.insert(0, "S. No", range(1, len(render_df) + 1))
                
                st.write(f"ग्रिड में प्रदर्शित कुल छात्र रिकॉर्ड संख्या (Active CCE Profiles): **{len(render_df)}**")
                
                if role == "full_admin":
                    disabled_cols = ["S. No", "Application Number", "Roll No.", "Student Name", "Branch"]
                    st.info("🔓 **एडमिन कंट्रोल मोड:** आपके पास सीसीई आंतरिक मूल्यांकन डेटा एडमिट और सिंक करने का पूर्ण अधिकार है।")
                else:
                    disabled_cols = [c for c in render_df.columns]
                    st.warning("🔒 **रीड-ओनली मोड:** सुरक्षा कारणों से आपके पास इस लिस्ट में सीसीई अंक बदलने का अधिकार नहीं है।")
                
                edited_cce = st.data_editor(
                    render_df, 
                    use_container_width=True, 
                    disabled=disabled_cols, 
                    column_config={
                        "CCE Marks Obtained": st.column_config.TextColumn("CCE Marks (Max 20)"),
                        "CCE Attendance Status": st.column_config.SelectboxColumn(
                            "Attendance Status", 
                            options=["Present", "Absent", "Detained"],
                            required=True
                        )
                    }, 
                    key="cce_record_live_editor_grid_p8_secure_engine", 
                    hide_index=True
                )
                
                if role == "full_admin":
                    if st.button("Save & Sync CCE Assessment Ledger", type="primary", use_container_width=True, key="p8_save_btn_secure"):
                        try:
                            clean_edited = edited_cce.drop(columns=["S. No"])
                            cce_sync_counter = 0
                            
                            for _, r_edit in clean_edited.iterrows():
                                app_num = str(r_edit["Application Number"]).strip()
                                
                                idx_matches = live_db[live_db["Application Number"].astype(str).str.strip() == app_num].index
                                
                                if not idx_matches.empty:
                                    for match_idx in idx_matches:
                                        live_db.at[match_idx, "CCE Marks Obtained"] = str(r_edit["CCE Marks Obtained"]).strip()
                                        live_db.at[match_idx, "CCE Attendance Status"] = str(r_edit["CCE Attendance Status"]).strip()
                                        cce_sync_counter += 1
                            
                            save_live_data(live_db)
                            st.success(f"🎉 सफलता! कुल {cce_sync_counter} छात्र रिकॉर्ड्स का सीसीई मुख्य डेटाबेस में सिंक हो गया है!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"डेटा सिंक्रोनाइज़ेशन चक्र में तकनीकी समस्या आई: {e}")
        
                # ----------------------------------------------------------------------
        # P9: PANEL PROMOTION MODULE (Academic Year Batch Progression Control)
        # ----------------------------------------------------------------------
        elif current_panel_id == "P9":
            st.header(f"📈 {get_panel_title('P9')} (Academic Year Batch Progression Control)")
            
            if "Promotion Status" not in live_db.columns: 
                live_db["Promotion Status"] = "Eligible"
                
            if live_db.empty: 
                st.warning("⚠️ मास्टर डेटाबेस वर्तमान में खाली है। कृपया पहले Panel 1 (Entry) से छात्र लोड करें।")
            else:
                st.markdown("""
                    <div style="background-color: #f7f9fa; border-left: 5px solid #0288d1; padding: 10px; border-radius: 4px; margin-bottom: 15px;">
                        📌 <b>ऑपरेटर निर्देश:</b> इस ग्रिड में बैच प्रमोशन (Batch Progression) से संबंधित डेटा प्रदर्शित है। सुरक्षा नियमों के अनुसार केवल सुपर एडमिन ही इसमें बदलाव कर सकता है।
                    </div>
                """, unsafe_allow_html=True)
                
                available_years = ["All"] + sorted(list(set(live_db["Current Year"].dropna().astype(str).str.strip())))
                selected_year = st.selectbox("Current Year (वर्तमान वर्ष) फ़िल्टर चुनें:", options=available_years, key="p9_year_filter_secure_engine")
                
                filtered_promo = live_db.copy()
                if selected_year != "All": 
                    filtered_promo = filtered_promo[filtered_promo["Current Year"].str.strip() == selected_year]
                
                promotion_fixed_cols = ["Application Number", "Roll No.", "Student Name", "Current Year", "Status", "Promotion Status"]
                
                for col in promotion_fixed_cols:
                    if col not in filtered_promo.columns:
                        filtered_promo[col] = ""
                        
                render_df = filtered_promo[promotion_fixed_cols].copy()
                render_df.insert(0, "S. No", range(1, len(render_df) + 1))
                
                st.write(f"ग्रिड में प्रदर्शित कुल छात्र रिकॉर्ड संख्या (Active Promotion Profiles): **{len(render_df)}**")
                
                if role == "full_admin":
                    disabled_cols = ["S. No", "Application Number", "Roll No.", "Student Name", "Current Year"]
                    st.info("🔓 **एडमिन कंट्रोल मोड:** आपके पास बैच प्रमोशन प्रोग्रेशन डेटा एडिट और सिंक करने का पूर्ण अधिकार है।")
                else:
                    disabled_cols = [c for c in render_df.columns]
                    st.warning("🔒 **रीड-ओनली मोड:** सुरक्षा कारणों से आपके पास इस लिस्ट में प्रमोशन स्थिति बदलने का अधिकार नहीं है।")
                
                edited_promo = st.data_editor(
                    render_df, 
                    use_container_width=True, 
                    disabled=disabled_cols, 
                    column_config={
                        "Status": st.column_config.SelectboxColumn("Academic Status", options=["Regular", "EX-STUDENT", "Pass", "Pending"], required=True), 
                        "Promotion Status": st.column_config.SelectboxColumn("Promotion Status", options=["Eligible", "Promoted", "Detained (Year Back)", "Course Completed"], required=True)
                    }, 
                    key="promotion_live_editor_grid_p9_secure_engine", 
                    hide_index=True
                )
                
                if role == "full_admin":
                    if st.button("Save & Sync Promotion Register", type="primary", use_container_width=True, key="p9_save_btn_secure"):
                        try:
                            clean_edited = edited_promo.drop(columns=["S. No"])
                            promo_sync_counter = 0
                            
                            for _, r_edit in clean_edited.iterrows():
                                app_num = str(r_edit["Application Number"]).strip()
                                
                                idx_matches = live_db[live_db["Application Number"].astype(str).str.strip() == app_num].index
                                
                                if not idx_matches.empty:
                                    for match_idx in idx_matches:
                                        live_db.at[match_idx, "Status"] = str(r_edit["Status"]).strip()
                                        live_db.at[match_idx, "Promotion Status"] = str(r_edit["Promotion Status"]).strip()
                                        promo_sync_counter += 1
                                        
                            save_live_data(live_db)
                            st.success(f"🎉 सफलता! कुल {promo_sync_counter} छात्र रिकॉर्ड्स का प्रमोशन प्रोग्रेशन डेटा मुख्य डेटाबेस में सुरक्षित सिंक हो गया है!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"डेटा सिंक्रोनाइज़ेशन चक्र में तकनीकी समस्या आई: {e}")

        # ----------------------------------------------------------------------
        # P10: PANEL RESULT MODULE (Tabulation Register & Exam Controller)
        # ----------------------------------------------------------------------
        elif current_panel_id == "P10":
            st.header(f"📊 {get_panel_title('P10')} (Tabulation Register & Exam Controller)")
            
            for f in ["Marks Obtained", "Result Status", "Exam Remarks"]:
                if f not in live_db.columns: 
                    live_db[f] = ""
            
            if live_db.empty: 
                st.warning("⚠️ MASTER DATABASE वर्तमान में खाली है। कृपया पहले Panel 1 (Entry) से छात्र लोड करें।")
            else:
                st.markdown("""
                    <div style="background-color: #f3e5f5; border-left: 5px solid #8e24aa; padding: 10px; border-radius: 4px; margin-bottom: 15px;">
                        📌 <b>ऑपरेटर निर्देश:</b> इस ग्रिड में परीक्षा परिणाम (Exam Result) से संबंधित डेटा प्रदर्शित है। सुरक्षा नियमों के अनुसार केवल सुपर एडमिन ही इसमें बदलाव कर सकता है।
                    </div>
                """, unsafe_allow_html=True)
                
                available_subjects = ["All"] + sorted(list(set(live_db["Branch"].dropna().astype(str).str.strip())))
                selected_sub = st.selectbox("Branch (शाखा) फ़िल्टर चुनें:", options=available_subjects, key="p10_subject_filter_secure_engine")
                
                filtered_res = live_db.copy()
                if selected_sub != "All": 
                    filtered_res = filtered_res[filtered_res["Branch"].str.strip() == selected_sub]
                
                result_fixed_cols = ["Application Number", "Roll No.", "Enrollment No", "Student Name", "Branch", "Marks Obtained", "Result Status", "Exam Remarks"]
                
                for col in result_fixed_cols:
                    if col not in filtered_res.columns:
                        filtered_res[col] = ""
                        
                render_df = filtered_res[result_fixed_cols].copy()
                render_df.insert(0, "S. No", range(1, len(render_df) + 1))
                
                st.write(f"ग्रिड में प्रदर्शित कुल छात्र रिकॉर्ड संख्या (Active Result Profiles): **{len(render_df)}**")
                
                if role == "full_admin":
                    disabled_cols = ["S. No", "Application Number", "Roll No.", "Enrollment No", "Student Name", "Branch"]
                    st.info("🔓 **एडमिन कंट्रोल मोड:** आपके पास परीक्षा परिणाम पंजी (Tabulation Register) एडिट और सिंक करने का पूर्ण अधिकार है।")
                else:
                    disabled_cols = [c for c in render_df.columns]
                    st.warning("🔒 **रीड-ओनली मोड:** सुरक्षा कारणों से आपके पास इस लिस्ट में परीक्षा परिणाम बदलने का अधिकार नहीं है।")
                
                edited_res = st.data_editor(
                    render_df, 
                    use_container_width=True, 
                    disabled=disabled_cols, 
                    column_config={
                        "Marks Obtained": st.column_config.TextColumn("Marks Obtained"),
                        "Result Status": st.column_config.SelectboxColumn("Result Status", options=["Pass", "Fail", "ATKT", "Withheld", "Absent"], required=True),
                        "Exam Remarks": st.column_config.TextColumn("Exam Remarks")
                    }, 
                    key="result_live_editor_grid_p10_secure_engine", 
                    hide_index=True
                )
                
                if role == "full_admin":
                    if st.button("Save & Sync Tabulation Register", type="primary", use_container_width=True, key="p10_save_btn_secure"):
                        try:
                            clean_edited = edited_res.drop(columns=["S. No"])
                            result_sync_counter = 0
                            
                            for _, r_edit in clean_edited.iterrows():
                                app_num = str(r_edit["Application Number"]).strip()
                                
                                idx_matches = live_db[live_db["Application Number"].astype(str).str.strip() == app_num].index
                                
                                if not idx_matches.empty:
                                    for match_idx in idx_matches:
                                        live_db.at[match_idx, "Marks Obtained"] = str(r_edit["Marks Obtained"]).strip()
                                        live_db.at[match_idx, "Result Status"] = str(r_edit["Result Status"]).strip()
                                        live_db.at[match_idx, "Exam Remarks"] = str(r_edit["Exam Remarks"]).strip()
                                        result_sync_counter += 1
                                        
                            save_live_data(live_db)
                            st.success(f"🎉 सफलता! कुल {result_sync_counter} छात्र रिकॉर्ड्स का परीक्षा परिणाम पंजी मुख्य डेटाबेस में सुरक्षित सिंक हो गया है!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"डेटा सिंक्रोनाइज़ेशन चक्र में तकनीकी समस्या आई: {e}")

        # ----------------------------------------------------------------------
        # P12: DASH BOARD EDITER MODULE (Pre-Login & Notice Customizer Combined)
        # ----------------------------------------------------------------------
        elif current_panel_id == "P12":
            st.header(f"🛠️ {get_panel_title('P12')} (Dash Board Editer & Notice Configuration)")
            
            st.markdown("""
                <div style="background-color: #fcf8e3; border-left: 5px solid #f0ad4e; padding: 12px; border-radius: 4px; margin-bottom: 20px;">
                    📌 <b>प्रशासक निर्देश (Dash Board Control Room):</b> इस एकीकृत कंट्रोल रूम से आप होम स्क्रीन पर दिखने वाले <b>आधिकारिक डिजिटल सूचना पटल (Notice Board)</b> और <b>लैंडिंग स्क्रीन की थीम</b> दोनों को लाइव बदल सकते हैं।
                </div>
            """, unsafe_allow_html=True)
            
            if "pre_login_config" not in st.session_state or not isinstance(st.session_state.pre_login_config, dict):
                st.session_state.pre_login_config = load_pre_login_config()
                
            if role == "full_admin":
                st.info("🔓 **एडमिन कंट्रोल मोड सक्रिय:** आपके पास सूचना पटल और वेलकम डैशबोर्ड को संपादित करने का पूर्ण अधिकार है।")
                
                # --- Part 1: Official Notice Board Guidelines Customizer (Shifted From Panel 11) ---
                st.subheader("📢 Part 1: Official Notice Board Guidelines Customizer")
                with st.form(key="p12_integrated_notice_board_form"):
                    updated_notice_text = st.text_area(
                        "सूचना पटल टेक्स्ट (Enter Live Announcements Line by Line):", 
                        value=st.session_state.notice_text, 
                        height=180,
                        key="p12_integrated_notice_text_area"
                    )
                    publish_notice_btn = st.form_submit_button("🚀 Publish & Update Notice Live Now")
                    
                    if publish_notice_btn:
                        if updated_notice_text.strip() == "":
                            st.warning("⚠️ खाली नोटिस प्रकाशित नहीं किया जा सकता!")
                        else:
                            st.session_state.notice_text = updated_notice_text
                            save_notice_board(updated_notice_text)
                            st.success("🎉 कॉलेज डिजिटल सूचना पटल सफलतापूर्वक अपडेट हो गया!")
                            st.rerun()
                
                st.markdown("---")
                
                # --- Part 2: Landing Visual Configurations ---
                st.subheader("🖼️ Part 2: Header Elements & Branding Themes")
                with st.form(key="p12_landing_view_editor_form_secure"):
                    col_view1, col_view2 = st.columns(2)
                    with col_view1:
                        header_toggle = st.checkbox(
                            "Display Institutional Header Text Block", 
                            value=bool(st.session_state.pre_login_config.get("show_header_text", True))
                        )
                        mantra_text = st.text_input(
                            "Spiritual Invocation / Mantra Text:", 
                            value=str(st.session_state.pre_login_config.get("header_mantra", "ॐ श्री गुरवे नमः"))
                        )
                    with col_view2:
                        system_title_text = st.text_input(
                            "Main Gateway Application Title:", 
                            value=str(st.session_state.pre_login_config.get("system_title", "Permanent Shared Live Database System"))
                        )
                    
                    st.markdown("##### Notice Board Branding Colors")
                    col_theme1, col_theme2 = st.columns(2)
                    with col_theme1:
                        border_color = st.color_picker(
                            "Left Accent Border Color:",
                                                        value=str(st.session_state.pre_login_config.get("notice_board_border_color", "#FF5733"))
                        )
                    with col_theme2:
                        bg_color = st.color_picker(
                            "Container Background Surface Color:", 
                            value=str(st.session_state.pre_login_config.get("notice_board_bg_color", "#f9f9f9"))
                        )
                    
                    submit_settings = st.form_submit_button("💾 Apply & Save Landing View Settings Permanently", type="primary", use_container_width=True)
                    
                    if submit_settings:
                        updated_config = {
                            "show_header_text": header_toggle,
                            "header_mantra": mantra_text,
                            "system_title": system_title_text,
                            "notice_board_border_color": border_color,
                            "notice_board_bg_color": bg_color
                        }
                        st.session_state.pre_login_config = updated_config
                        save_pre_login_config(updated_config)
                        st.success("🎉 डैशबोर्ड विजुअल सेटिंग्स सफलतापूर्वक सेव हो गई हैं!")
                        st.rerun()
            else:
                st.warning("🔒 **रीड-ओनली मोड:** सुरक्षा कारणों से आपके पास इस लैंडिंग पेज कॉन्फ़िगरेशन और डिजिटल सूचना पटल में बदलाव करने का अधिकार नहीं है।")
                
                st.markdown("### 📋 Current Active Announcements Preview")
                formatted_preview = "".join([f"<li style='margin-bottom:8px;'>{line.strip()}</li>" for line in st.session_state.notice_text.split('\n') if line.strip()])
                st.markdown(f"""
                    <div style="background-color: #fffaf0; border: 1px solid #ffd1b3; padding: 15px; border-radius: 4px; margin-bottom:20px;">
                        <ul style="padding-left: 20px; color: #333;">{formatted_preview}</ul>
                    </div>
                """, unsafe_allow_html=True)

        # ----------------------------------------------------------------------
        # P13: PANEL MERGE MODULE (Database Smart Merge Room Only)
        # ----------------------------------------------------------------------
        elif current_panel_id == "P13":
            st.header(f"🔀 {get_panel_title('P13')} (Database Smart Merge Panel)")
            st.info("💡 बाहरी डेटाबेस को कस्टमाइज्ड एडमिशन स्कीमा के साथ कम्बाइन करने का मॉड्यूल यहाँ काम करता है। (Super-Admin Dropdown Customizer function has been moved to Panel 15 Admin Controls.)")

            uploaded_merge_file = st.file_uploader("मर्ज करने के लिए बाहरी डेटा फ़ाइल (.csv, .xlsx) चुनें:", type=["csv", "xlsx"])
            if uploaded_merge_file is not None:
                if st.button("Execute Safe Structural Merge", type="primary", use_container_width=True):
                    try:
                        if uploaded_merge_file.name.endswith('.csv'):
                            ext_df = pd.read_csv(uploaded_merge_file, dtype=str).fillna("")
                        else:
                            ext_df = pd.read_excel(uploaded_merge_file, dtype=str).fillna("")
                            
                        for col in DEFAULT_COLUMNS:
                            if col not in ext_df.columns:
                                ext_df[col] = ""
                                
                        cleaned_ext_df = ext_df[DEFAULT_COLUMNS].copy()
                        master_db = load_live_data()
                        combined_master = pd.concat([master_db, cleaned_ext_df], ignore_index=True)
                        save_live_data(combined_master)
                        st.success("🎉 डेटाबेस स्ट्रक्चरल मर्ज सफलतापूर्वक पूरा हुआ!")
                        st.rerun()
                    except Exception as merge_err:
                        st.error(f"मर्ज प्रक्रिया के दौरान तकनीकी त्रुटि: {merge_err}")

        # ----------------------------------------------------------------------
        # P14: PANEL VIEWER (INTEGRATED INDEX SYSTEM - Isolated Inspector Window)
        # ----------------------------------------------------------------------
        elif current_panel_id == "P14":
            st.header(f"👁️ {get_panel_title('P14')} (Multi-Panel Inspection Window)")

            panel_options_list = {
                "Panel 2: Admission View": ["Application Number", "Student Abc Id", "Student Name", "Father Name", "Mother Name", "Gender", "Date Of Birth", "Category", "Admission Category", "Degree", "Branch", "Minor Subjects", "Vocational Subjects", "MDC Subjects", "PW/Ap/CE Subjects", "Mobile Number", "Email", "Address", "Enrollment No", "Admssion & Enrollment Fees", "Scholarship Name", "Payment Date"],
                "Panel 3: Unique ID View": ["Application Number", "Student Name", "Father Name", "Unique ID"],
                "Panel 4: Roll No View": ["Application Number", "Unique ID", "Student Name", "Roll No."],
                "Panel 5: Enrollment View": ["Application Number", "Student Name", "Branch", "Enrollment No"],
                "Panel 6: Scholarship View": ["Application Number", "Unique ID", "Student Name", "Category", "Scholarship Name", "Scholarship Status"],
                "Panel 7: CCE Foil View": ["Roll No.", "Student Name", "Branch", "Status"],
                "Panel 8: CCE Record View": ["Application Number", "Roll No.", "Student Name", "Branch", "CCE Marks Obtained", "CCE Attendance Status"],
                "Panel 9: Promotion View": ["Application Number", "Roll No.", "Student Name", "Current Year", "Status", "Promotion Status"],
                "Panel 10: Result View": ["Application Number", "Roll No.", "Enrollment No", "Student Name", "Branch", "Marks Obtained", "Result Status", "Exam Remarks"],
                "Panel 12: Dash Board View": ["Admission Year", "Admission Session", "Student Name", "Status"]
            }

            st.subheader("📂 Select Panel Dashboard View")
            selected_panel_view = st.selectbox(
                "निरीक्षण करने के लिए पैनल सूची चुनें (Select Dashboard to Inspect):",
                options=list(panel_options_list.keys()),
                key="p14_panel_selector_dropdown_secure"
            )

            target_columns = panel_options_list[selected_panel_view]

            for c_col in target_columns:
                if c_col not in live_db.columns:
                    live_db[c_col] = ""

            st.markdown(f"### 📋 {selected_panel_view} - Isolated Inspection Records")
            
            col_search1, col_search2 = st.columns(2)
            with col_search1:
                search_target_col = st.selectbox("खोजने के लिए फ़ील्ड चुनें:", options=target_columns, key="p14_search_col_target_secure")
            with col_search2:
                search_query_text = st.text_input(f"'{search_target_col}' में प्रविष्टि खोजें:", key="p14_query_val_text_secure").strip()

            view_filtered_df = live_db.copy()
            if search_query_text != "":
                view_filtered_df = view_filtered_df[
                    view_filtered_df[search_target_col].astype(str).str.contains(search_query_text, case=False, na=False)
                ]

            st.write(f"वर्तमान ग्रिड में कुल उपलब्ध छात्र रिकॉर्ड संख्या: **{len(view_filtered_df)}**")

            final_render_cols = [col for col in target_columns if col in view_filtered_df.columns]
            
            if not view_filtered_df.empty:
                display_ready_df = view_filtered_df[final_render_cols].copy()
                display_ready_df.insert(0, "S. No", range(1, len(display_ready_df) + 1))

                st.dataframe(display_ready_df, use_container_width=True, hide_index=True)
                
                st.download_button(
                    label=f"📥 Download Selected Dashboard Report Snapshot (CSV)",
                    data=view_filtered_df[final_render_cols].to_csv(index=False).encode('utf-8'),
                    file_name=f"{selected_panel_view.replace(':', '').replace(' ', '_').lower()}_snapshot.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="p14_download_compiled_report_btn_secure"
                )
            else:
                st.warning("🔍 निर्दिष्ट खोज प्रविष्टि के आधार पर कोई रिकॉर्ड नहीं मिला।")

        # ----------------------------------------------------------------------
        # P15: SUPER-ADMIN CONTROL PANEL (System Configurations & Dropdown Customizer)
        # ----------------------------------------------------------------------
        elif current_panel_id == "P15":
            st.header(f"👑 {get_panel_title('P15')} (Super-Admin Control Center)")
            
            if role != "full_admin":
                st.error("🔒 सुरक्षा उल्लंघन: इस पैनल को एक्सेस करने के लिए आपके पास सुपर-एडमिन विशेषाधिकार होना अनिवार्य है।")
            else:
                st.markdown("""
                    <div style="background-color: #fce8e6; border-left: 5px solid #d93025; padding: 12px; border-radius: 4px; margin-bottom: 20px;">
                        🎯 <b>कंट्रोल रूम गाइड:</b> यहाँ से आप पूरे सिस्टम के मास्टर डेटा को रीसेट कर सकते हैं, बैकअप प्रबंधित कर सकते हैं, तथा <b>मास्टर ड्रॉपडाउन सूची (Dropdown Options)</b> को लाइव कस्टमाइज़ कर सकते हैं।
                    </div>
                """, unsafe_allow_html=True)
                
                # --- 🛠️ भाग 1: सुपर-एडमिन मास्टर ड्रॉपडाउन लिस्ट कस्टमाइज़र (Shifted From Merge Panel) ---
                st.subheader("⚙️ Super-Admin Master Dropdown List Customizer")
                st.markdown("पैनल 1 (Data Onboarding) में दिखने वाली तीनों स्क्रॉल सूचियों के विकल्पों को यहाँ से लाइव कस्टमाइज़ करें:")
                
                # वर्तमान ड्रॉपडाउन स्कीमा लोड करना (सुरक्षित सेशन स्टेट हैंडलिंग)
                if "p14_dropdown_schemas" in st.session_state and "p11_dropdown_schemas" not in st.session_state:
                    # बैकवर्ड कम्पेटिबिलिटी चेकर
                    st.session_state.p11_dropdown_schemas = st.session_state.p14_dropdown_schemas
                
                if "p11_dropdown_schemas" not in st.session_state:
                    st.session_state.p11_dropdown_schemas = {
                        "file_types": ["Admission List", "Counseling Data", "Direct Entry", "Management Quota"],
                        "academic_years": ["2024", "2025", "2026", "2027"],
                        "academic_sessions": ["July-Dec", "Jan-June"]
                    }
                
                # डेटा सिंक ब्रिज (Panel 1 के session state वेरिएबल p1_dropdown_schemas के साथ ऑटो-सिंक)
                st.session_state.p1_dropdown_schemas = st.session_state.p11_dropdown_schemas
                
                col_drop1, col_drop2, col_drop3 = st.columns(3)
                
                with col_drop1:
                    st.markdown("##### 📁 1. File Segments / Types")
                    edited_file_types = st.text_area(
                        "File Types (एक प्रति लाइन):",
                        value="\n".join(st.session_state.p11_dropdown_schemas["file_types"]),
                        height=150,
                        key="p15_custom_file_types_text"
                    )
                    
                with col_drop2:
                    st.markdown("##### 📆 2. Academic Years")
                    edited_years = st.text_area(
                        "Admission Years (एक प्रति लाइन):",
                        value="\n".join(st.session_state.p11_dropdown_schemas["academic_years"]),
                        height=150,
                        key="p15_custom_years_text"
                    )
                    
                with col_drop3:
                    st.markdown("##### ⏳ 3. Academic Sessions")
                    edited_sessions = st.text_area(
                        "Admission Sessions (एक प्रति लाइन):",
                        value="\n".join(st.session_state.p11_dropdown_schemas["academic_sessions"]),
                        height=150,
                        key="p15_custom_sessions_text"
                    )
                
                # ड्रॉपडाउन कस्टमाइज़र सेव बटन
                if st.button("💾 Apply & Update Master Dropdown Framework", type="primary", use_container_width=True, key="p15_save_dropdowns_btn"):
                    # खाली लाइनों को हटाकर लिस्ट तैयार करना
                    new_file_types = [line.strip() for line in edited_file_types.split("\n") if line.strip()]
                    new_years = [line.strip() for line in edited_years.split("\n") if line.strip()]
                    new_sessions = [line.strip() for line in edited_sessions.split("\n") if line.strip()]
                    
                    if not new_file_types or not new_years or not new_sessions:
                        st.error("❌ कोई भी ड्रॉपडाउन सूची पूरी तरह खाली नहीं छोड़ी जा सकती!")
                    else:
                        updated_schema = {
                            "file_types": new_file_types,
                            "academic_years": new_years,
                            "academic_sessions": new_sessions
                        }
                        # सेशन स्टेट अपडेट करना ताकि पूरे एप्लीकेशन में बदलाव तुरंत लागू हों
                        st.session_state.p11_dropdown_schemas = updated_schema
                        st.session_state.p1_dropdown_schemas = updated_schema
                        
                        # यदि आपके पास ड्रॉपडाउन सेटिंग्स को परमानेंट फ़ाइल में सेव करने का फ़ंक्शन है तो उसे यहाँ कॉल करें, जैसे:
                        # save_dropdown_config_to_disk(updated_schema)
                        
                        st.success("🎉 सफलता! मास्टर ड्रॉपडाउन सूचियाँ सफलतापूर्वक अपडेट हो गईं और Panel 1 के साथ सिंक हो गई हैं!")
                        st.rerun()
                
                st.markdown("---")
                
                # --- 🗄️ भाग 2: डेटाबेस और सिस्टम एडमिनिस्ट्रेशन (Database Maintenance Actions) ---
                st.subheader("🧹 System Database Maintenance & Emergency Actions")
                
                col_adm1, col_adm2 = st.columns(2)
                
                with col_adm1:
                    st.markdown("##### 📥 Master System Backup")
                    st.markdown("वर्तमान लाइव डेटाबेस की सभी टेबल्स और कस्टमाइज्ड स्कीमा प्रविष्टियों का बैकअप डाउनलोड करें।")
                    csv_data = live_db.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Emergency Live DB Backup (.csv)",
                        data=csv_data,
                        file_name=f"master_live_db_backup_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True,
                        key="p15_download_backup_btn"
                    )
                    
                with col_adm2:
                    st.markdown("##### 🚨 Emergency Database Reset")
                    st.markdown("<p style='color:red;'><b>चेतावनी:</b> यह एक्शन लाइव सी.एस.वी फ़ाइल के सभी छात्र रिकॉर्ड्स को तुरंत डिलीट कर देगा।</p>", unsafe_allow_html=True)
                    
                    confirm_reset = st.checkbox("हाँ, मैं डेटाबेस को पूरी तरह खाली करने की पुष्टि करता हूँ।", key="p15_confirm_reset_checkbox")
                    if st.button("💥 Reset & Wipe Out Live Database Now", type="secondary", use_container_width=True, disabled=not confirm_reset, key="p15_emergency_wipe_btn"):
                        try:
                            # कस्टमाइज्ड स्कीमा के साथ खाली डेटाफ़्रेम बनाना
                            empty_df = pd.DataFrame(columns=DEFAULT_COLUMNS)
                            save_live_data(empty_df)
                            st.success("🎉 मुख्य लाइव डेटाबेस (Master Live CSV) को पूरी तरह से रीसेट और खाली कर दिया गया है!")
                            st.rerun()
                        except Exception as reset_err:
                            st.error(f"रीसेट प्रक्रिया के दौरान तकनीकी समस्या आई: {reset_err}")









