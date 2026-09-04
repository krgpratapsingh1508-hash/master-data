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
STAGE_FILE = "merge_stage_database.csv"  # 🆕 P1 से आने वाले डेटा के लिए अस्थाई स्टेजिंग फ़ाइल
CRED_FILE = "user_credentials_v15.json"
MAP_FILE = "column_mapping_schema.json"
PANEL_NAME_FILE = "panel_names_schema.json"
NOTICE_FILE = "notice_board_schema.json"
PRE_LOGIN_CONFIG_FILE = "pre_login_view_config.json"
DYNAMIC_LISTS_FILE = "p1_dynamic_lists_schema.json"

# डिफ़ॉल्ट कॉन्फ़िगरेशन बैकअप डिक्शनरी
DEFAULT_PRE_LOGIN_CONFIG = {
    "show_header_text": True,
    "header_mantra": "ॐ श्री गुरवे नमः",
    "system_title": "Permanent Shared Live Database System",
    "notice_board_border_color": "#FF5733",
    "notice_board_bg_color": "#f9f9f9"
}

DEFAULT_DYNAMIC_LISTS = {
    "file_types": [
        "admission file", "admission fee file", "unique id file", 
        "roll no file", "enrollment file", "promotion file", "result file"
    ],
    "academic_years": [str(year) for year in range(2014, 2027)],
    "academic_sessions": [f"{year}-{str(year+1)[2:]}" for year in range(2014, 2027)]
}

DEFAULT_NOTICE = (
    "1. यह एक पूर्णतः सुरक्षित, लाइव क्लाउड स्टूडेंट डेटाबेस मैनेजमेंट सिस्टम है।\n"
    "2. डेटा प्रविष्टि, सुधार, स्कॉलरशिप वेरिफिकेशन या परीक्षा परिणाम अपडेट करने के लिए अधिकृत यूजर क्रेडेंशियल्स का उपयोग करें।\n"
    "3. बिना लॉगिन के डेटाबेस तक पहुँच पूर्णतः प्रतिबंधित है। किसी भी समस्या के लिए सुपर-एडमिन से संपर्क करें।"
)

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
    "p13_merge": {"password": "mrg13123", "role": "p13_role", "label": "🔀 P13: Merge & Approve Panel"},
    "p14_viewer": {"password": "view14123", "role": "p14_role", "label": "👁️ P14: Multi-Panel Inspection Window"}
}

DEFAULT_PANELS = {
    "P1": "Panal entry", "P2": "Admission panel", "P3": "Unique ID panel",
    "P4": "Roll No. panel", "P5": "Enrollment panel", "P6": "Scholarship panel",
    "P7": "CCE panel", "P8": "Promotion panel", "P9": "Result panel",
    "P10": "Register panel", "P11": "notice board info", "P12": "📢 Desk Board Editer",
    "P13": "🔀 Merge & Approve Panel", "P14": "Panal viewer", "P15": "Panel admin"
}

DEFAULT_COLUMNS = [
    "Admission Year", "Admission Session", "Eligibility Name", "Admission Application Number",
    "Admission Date", "Unique ID", "Roll No.", "Application Enrollment No.",
    "Enrollment No.", "Student Name", "Father Name", "Mother Name", "Date of Birth",
    "Category", "Subject Code", "Subject", "Duration", "Mobile Number", "Email ID", "Address", "Status",
    "Current Year", "Application Number", "Student Abc Id", "Gender", "Admission Category", "Degree",
    "Branch", "Minor Subjects", "Vocational Subjects", "MDC Subjects", "PW/Ap/CE Subjects",
    "Admssion & Enrollment Fees", "Scholarship Name", "Payment Date", "Target Panel Visibility" # 🆕 नया कॉलम ट्रैकिंग के लिए
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

# 🆕 स्टेजिंग फ़ाइल मैनेजमेंट फ़ंक्शंस
def load_stage_data():
    if not os.path.exists(STAGE_FILE) or os.path.getsize(STAGE_FILE) == 0:
        return pd.DataFrame(columns=DEFAULT_COLUMNS + ["Uploaded File Name"])
    try:
        df = pd.read_csv(STAGE_FILE, dtype=str)
        return df.fillna("").reset_index(drop=True)
    except:
        return pd.DataFrame(columns=DEFAULT_COLUMNS + ["Uploaded File Name"])

def save_stage_data(df_to_save):
    df_to_save.fillna("").astype(str).to_csv(STAGE_FILE, index=False)

def get_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as image_file:
            return f"data:image/png;base64,{base64.b64encode(image_file.read()).decode()}"
    return ""

# ==========================================================
# 🧠 स्टेप 3: सेशन स्टेट वेरिएबल्स इनिशियलाइज़ेशन
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
if "cce_foil_generated" not in st.session_state: st.session_state.cce_foil_generated = False

# 🆕 फ़ाइल अपलोडर को खाली करने के लिए काउंटर (P1 ऑटो-क्लियर मैकेनिज्म हेतु)
if "uploader_key_counter" not in st.session_state:
    st.session_state.uploader_key_counter = 0

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
# 🧭步 6: पोस्ट-लॉगिन वर्कस्पेस और पैनल राउटिंग इंजन
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
    elif role == "p1_role": allowed_panels = ["P1"]
    elif role == "p2_role": allowed_panels = ["P2"]
    elif role == "p3_role": allowed_panels = ["P3"]
    elif role == "p4_role": allowed_panels = ["P4"]
    elif role == "p5_role": allowed_panels = ["P5"]
    elif role == "p6_role": allowed_panels = ["P6"]
    elif role == "p7_role": allowed_panels = ["P7"]
    elif role == "p8_role": allowed_panels = ["P8"]
    elif role == "p9_role": allowed_panels = ["P9"]
    elif role == "p10_role": allowed_panels = ["P10"]
    elif role == "p11_role": allowed_panels = ["P11"]
    elif role == "p12_role": allowed_panels = ["P12"]
    elif role == "p13_role": allowed_panels = ["P13"]
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
            
            # 📁 बल्क फ़ाइल अपलोड सब-सिस्टम (Modified for Multiple CSV & XLSX Upload)
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

                if (p1_file_type == "-- चुनें --" or p1_admission_year == "-- चुनें --" or p1_admission_session == "-- चुनें --"):
                    st.info("💡 कृपया फ़ाइल अपलोड विंडो खोलने के लिए ऊपर दिए गए तीनों विकल्पों (File Segment, Year और Session) का चयन करें।")
                else:
                    st.success(f"✅ कॉन्फ़िगरेशन锁: **{p1_file_type.upper()}** | वर्ष: **{p1_admission_year}** | सत्र: **{p1_admission_session}**")
                    
                    uploader_unique_key = f"p1_bulk_uploader_widget_run_{st.session_state.get('uploader_key_counter', 0)}"
                    
                    # 🆕 यहाँ accept_multiple_files=True किया गया है ताकि CSV और XLSX दोनों एक साथ अपलोड हो सकें
                    uploaded_files = st.file_uploader(
                        f"अपलोड करने के लिए '{p1_file_type}' की फ़ाइलें चुनें (अधिकतम 5):", 
                        type=["csv", "xlsx", "xls"],
                        accept_multiple_files=True,
                        key=uploader_unique_key
                    )
                    
                    if uploaded_files:
                        if len(uploaded_files) > 5:
                            st.warning("⚠️ कृपया एक बार में केवल 1 से 5 फ़ाइलें ही अपलोड करें।")
                        
                        if st.button("Upload & Send to System Database Now", type="primary", use_container_width=True):
                            try:
                                success_count = 0
                                current_stage_db = load_stage_data()
                                all_new_dfs = [current_stage_db]
                                
                                # 🔄 लूप चलाकर एक-एक करके सभी फ़ाइलों को रीड (Read) करना
                                for uploaded_file in uploaded_files:
                                    if uploaded_file.name.endswith('.csv'):
                                        uploaded_df = pd.read_csv(uploaded_file, dtype=str).fillna("")
                                    elif uploaded_file.name.endswith('.xlsx'):
                                        uploaded_df = pd.read_excel(uploaded_file, engine='openpyxl', dtype=str).fillna("")
                                    elif uploaded_file.name.endswith('.xls'):
                                        try:
                                            uploaded_df = pd.read_excel(uploaded_file, engine='xlrd', dtype=str).fillna("")
                                        except:
                                            uploaded_file.seek(0) 
                                            html_tables = pd.read_html(uploaded_file)
                                            uploaded_df = html_tables[0].astype(str).fillna("") if html_tables else pd.DataFrame()
                                    
                                    if uploaded_df.empty:
                                        st.error(f"❌ फ़ाइल '{uploaded_file.name}' के अंदर कोई मान्य डेटा नहीं मिला।")
                                        continue

                                    uploaded_df = uploaded_df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
                                    
                                    for col in DEFAULT_COLUMNS:
                                        if col not in uploaded_df.columns: 
                                            uploaded_df[col] = ""
                                    
                                    uploaded_df["Admission Year"] = p1_admission_year
                                    uploaded_df["Admission Session"] = p1_admission_session
                                    uploaded_df["Target Panel Visibility"] = "Pending Approval"
                                    
                                    if "Uploaded File Type" not in uploaded_df.columns:
                                        uploaded_df["Uploaded File Type"] = p1_file_type
                                    
                                    cleaned_uploaded_df = uploaded_df[DEFAULT_COLUMNS].copy()
                                    cleaned_uploaded_df["Uploaded File Name"] = uploaded_file.name
                                    
                                    all_new_dfs.append(cleaned_uploaded_df)
                                    success_count += 1
                                
                                # 🛑 सभी फ़ाइलों के डेटा को जोड़कर स्टेजिंग CSV में सुरक्षित करना
                                if success_count > 0:
                                    updated_stage_df = pd.concat(all_new_dfs, ignore_index=True)
                                    save_stage_data(updated_stage_df)
                                    
                                    st.session_state.uploader_key_counter += 1
                                    
                                    st.success(f"🎉 कुल {success_count} फ़ाइलें (CSV/XLSX) सफलतापूर्वक 'merge & approve panel' में भेज दी गई हैं!")
                                    st.balloons()
                                    st.rerun()
                            except Exception as e: 
                                st.error(f"फ़ाइल प्रोसेसिंग चक्र में तकनीकी त्रुटि आई: {e}")
                                
            # ----------------------------------------------------------------------
            # ➕ नया छात्र मैनुअल फॉर्म सब-सिस्टम (Manual Entry Routing Layer)
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
                        payment_date = st.text_input("Payment Date (DD-MM-YYYY)")
                    
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
                            "Status": "Regular Student", "Current Year": "1", "Target Panel Visibility": "Pending Approval"
                        })
                        new_df = pd.DataFrame([new_row])
                        new_df["Uploaded File Name"] = "Manual Form Entry"
                        
                        # Route manual entries directly to merge stage room 
                        updated_stage_df = pd.concat([load_stage_data(), new_df], ignore_index=True)
                        save_stage_data(updated_stage_df)
                        st.success("🎉 Record successfully sent in merge & approve panel!")
                        st.rerun()

        # ----------------------------------------------------------------------
        # P2: PANEL ADMISSION MODULE (Displays Only Content Explicitly Approved for P2)
        # ----------------------------------------------------------------------
        elif current_panel_id == "P2":
            st.header(f"🎓 {get_panel_title('P2')} (Admission Control & Payment Tracker)")
            
            # 🔍 Isolated Firewall Query Filter Rule
            p2_authorized_db = live_db[live_db["Target Panel Visibility"] == "P2"].copy()
            
            if p2_authorized_db.empty: 
                st.warning("⚠️ डेटाबेस वर्तमान में खाली है या इस पैनल के लिए कोई अधिकृत स्वीकृत (Approved) डेटा उपलब्ध नहीं है।")
            else:
                st.subheader("📆 Filter Records By Payment Date Range")
                use_date_filter = st.checkbox("Enable Date Range Filter (तिथि सीमा फ़िल्टर सक्रिय करें)", value=False, key="p2_enable_date_filter_secure")
                
                admission_display_db = p2_authorized_db.copy()
                
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
                
                admission_fixed_cols = [
    "Application Number", "Student Abc Id", "Student Name", "Father Name", 
    "Mother Name", "Gender", "Date Of Birth", "Category", "Admission Category", 
    "Degree", "Branch", "Minor Subjects", "Vocational Subjects", "MDC Subjects", 
    "PW/Ap/CE Subjects", "Mobile Number", "Email", "Address", "Enrollment No", 
    "Admission & Enrollment Fees", "Scholarship Name", "Payment Date"
]
                
                for target_col in admission_fixed_cols:
                    if target_col not in admission_display_db.columns:
                        admission_display_db[target_col] = ""
                
                if role == "full_admin":
                    st.subheader("⚙️ Select Columns for View, Print & Export (Admin Only)")
                    available_to_select = [c for c in live_db.columns if c in DEFAULT_COLUMNS]
                    selected_columns_to_show = st.multiselect(
                        "ग्रिड में प्रदर्शित करने के लिए कॉलम्स चुनें / हटाएँ:",
                        options=available_to_select,
                        default=[c for c in admission_fixed_cols if c in available_to_select],
                        key="p2_admin_multiselect"
                    )
                else:
                    selected_columns_to_show = admission_fixed_cols
                
                if not selected_columns_to_show:
                    st.warning("⚠️ कृपया ग्रिड प्रदर्शित करने के लिए कम से कम एक कॉलम चुनें।")
                else:
                    render_df = admission_display_db[selected_columns_to_show].copy()
                    render_df.insert(0, "S. No.", range(1, len(render_df) + 1))
                    
                    st.write(f"📊 ग्रिड में लोड छात्र रिकॉर्ड्स की संख्या: **{len(render_df)}**")
                    
                    if role == "full_admin":
                        disabled_cols = ["S. No.", "Application Number", "Student Name", "Father Name"]
                        st.info("🔓 **प्रशासक मोड:** आपके पास ग्रिड डेटा को एडिट और सिंक करने की अनुमति है।")
                    else:
                        disabled_cols = [c for c in render_df.columns]
                        st.warning("🔒 **रीड-ओनली मोड:** सुरक्षा कारणों से आपके पास इस ग्रिड में बदलाव करने का अधिकार नहीं है।")
                    
                    edited_admission_df = st.data_editor(
                        render_df, 
                        use_container_width=True, 
                        disabled=disabled_cols,
                        key="admission_live_editor_grid_p2_secure_engine", 
                        hide_index=True
                    )
                    
                    if role == "full_admin":
                        if st.button("Save Changes to Live Database", type="primary", use_container_width=True, key="p2_save_secure_btn"):
                            try:
                                clean_edited = edited_admission_df.drop(columns=["S. No."], errors="ignore")
                                for _, row_edit in clean_edited.iterrows():
                                    target_app_num = str(row_edit["Application Number"]).strip()
                                    idx_matches = live_db[live_db["Application Number"].astype(str).str.strip() == target_app_num].index
                                    
                                    if not idx_matches.empty:
                                        for match_idx in idx_matches:
                                            for col in clean_edited.columns:
                                                if col in live_db.columns and col not in ["Application Number", "Student Name", "Father Name"]:
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
                            export_clean_df = edited_admission_df.drop(columns=["S. No."], errors="ignore")
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
        # P3: PANEL UNIQUE ID MODULE (Displays Only Content Approved for P3)
        # ----------------------------------------------------------------------
        elif current_panel_id == "P3":
            st.header(f"🆔 {get_panel_title('P3')} (Student Unique ID Mapping Engine)")
            
            # 🔍 Isolated Firewall Query Filter Rule: केवल P3 के लिए अप्रूव्ड डेटा ही यहाँ दिखेगा
            p3_authorized_db = live_db[live_db["Target Panel Visibility"] == "P3"].copy()
            
            if p3_authorized_db.empty: 
                st.warning("⚠️ इस पैनल के लिए कोई अधिकृत स्वीकृत (Approved) डेटा उपलब्ध नहीं है। कृपया P13 पैनल से डेटा अप्रूव करें।")
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
                
                # सेंट्रल रिपॉजिटरी से फ़िल्टर मैच करना
                unique_filter_df = p3_authorized_db.copy()
                if search_query != "":
                    unique_filter_df = unique_filter_df[
                        unique_filter_df[search_field].astype(str).str.contains(search_query, case=False, na=False)
                    ]
                
                # केवल यूनिक आईडी पैनल के लिए निश्चित कॉलम्स की सूची
                unique_fixed_cols = [
    "Admission Year", "Admission Session", "HIGHER EDU ID", "Unique ID", 
    "FULL NAME", "FATHER NAME", "MOTHER NAME", "DATE OF BIRTH", "CATEGORY", 
    "Drgree", "MAJOR SUB", "MINOR SUB", "OPEN-ELECTIVE SUB", "VOCATIONAL SUB", "PROJECT WORK"
]
                
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
            
            # 🔍 Isolated Firewall Query Filter Rule: Only show records explicitly routed to P4
            p4_authorized_db = live_db[live_db["Target Panel Visibility"] == "P4"].copy()
            
            if p4_authorized_db.empty: 
                st.warning("⚠️ इस पैनल के लिए कोई अधिकृत स्वीकृत (Approved) डेटा उपलब्ध नहीं है। कृपया P13 पैनल से डेटा अप्रूव करें।")
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
                
                roll_filter_df = p4_authorized_db.copy()
                if roll_search_query != "":
                    roll_filter_df = roll_filter_df[
                        roll_filter_df[roll_search_field].astype(str).str.contains(roll_search_query, case=False, na=False)
                    ]
                
                roll_fixed_cols = [
    "Admission Year", "Admission Session", "HIGHER EDU ID", "Roll No.", 
    "FULL NAME", "FATHER NAME", "MOTHER NAME", "DATE OF BIRTH", "CATEGORY", 
    "Drgree", "MAJOR SUB", "MINOR SUB", "OPEN-ELECTIVE SUB", "VOCATIONAL SUB", "PROJECT WORK"
]
                
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
            
            # 🔍 Isolated Firewall Query Filter Rule: Only show records explicitly approved for P5
            p5_authorized_db = live_db[live_db["Target Panel Visibility"] == "P5"].copy()
            
            if p5_authorized_db.empty: 
                st.warning("⚠️ इस पैनल के लिए कोई अधिकृत स्वीकृत (Approved) डेटा उपलब्ध नहीं है। कृपया पहले P13 (Merge Panel) से डेटा को इस पैनल पर असाइन कर अप्रूव करें।")
            else:
                st.markdown("""
                    <div style="background-color: #fff9e6; border-left: 5px solid #ffc107; padding: 10px; border-radius: 4px; margin-bottom: 15px;">
                        📌 <b>ऑपरेटर निर्देश:</b> इस ग्रिड में विश्वविद्यालय नामांकन (Enrollment No) से संबंधित डेटा प्रदर्शित है। सुरक्षा नियमों के अनुसार केवल सुपर एडमिन ही इसमें बदलाव कर सकता है।
                    </div>
                """, unsafe_allow_html=True)
                
                # यूनीक शाखाओं (Branch) की सूची निकालकर फ़िल्टर तैयार करना
                available_subjects = ["All"] + sorted(list(set(p5_authorized_db["Branch"].dropna().astype(str).str.strip())))
                selected_subject = st.selectbox("Branch (शाखा) फ़िल्टर चुनें:", options=available_subjects, key="p5_subject_filter_secure_select")
                
                # फ़िल्टर के आधार पर डेटा को अलग करना
                filtered_enrollment = p5_authorized_db.copy()
                if selected_subject != "All": 
                    filtered_enrollment = filtered_enrollment[filtered_enrollment["Branch"].str.strip() == selected_subject]
                
                # 🎛️ केवल एनरोलमेंट पैनल के लिए मान्य निश्चित कॉलम्स की सूची (As Per Custom Layout)
                enrollment_fixed_cols = [
    "Admission Year", "Admission Session", "application_no", "enroll_no", 
    "Name", "gender", "father_name", "dob", "category", "mob_no", "collegename", 
    "coursename", "branchname", "branchmode", "status", "session", "univ_or_board"
]
                
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
                    st.info("🔓 **एडमिन कंट्रोल मोड:** आपके पास विश्वविद्यालय नामांकन संख्या (Enrollment No) एडिट और सिंक करने का पूर्ण अधिकार है।")
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
            
            # Ensure the tracking column fallback layout exists inside master mapping fields
            if "Scholarship Status" not in live_db.columns: 
                live_db["Scholarship Status"] = "Not Applied"
                
            # 🔍 Isolated Firewall Query Filter Rule: Only fetch records explicitly approved for P6
            p6_authorized_db = live_db[live_db["Target Panel Visibility"] == "P6"].copy()
            
            if p6_authorized_db.empty:
                st.warning("⚠️ इस पैनल के लिए कोई अधिकृत स्वीकृत (Approved) डेटा उपलब्ध नहीं है। कृपया पहले P13 (Merge Panel) से डेटा को इस पैनल पर असाइन कर अप्रूव करें।")
            else:
                st.markdown("""
                    <div style="background-color: #f4fbf7; border-left: 5px solid #2e7d32; padding: 10px; border-radius: 4px; margin-bottom: 15px;">
                        📌 <b>ऑपरेटर निर्देश:</b> इस ग्रिड में छात्रवृत्ति प्रोग्रेस (Scholarship Status) से संबंधित डेटा प्रदर्शित है। सुरक्षा नियमों के अनुसार केवल सुपर एडमिन ही इसमें बदलाव कर सकता है।
                    </div>
                """, unsafe_allow_html=True)
                
                # यूनीक श्रेणियों (Category) की सूची निकालकर फ़िल्टर तैयार करना
                available_categories = ["All"] + sorted(list(set(p6_authorized_db["Category"].dropna().astype(str).str.strip())))
                selected_category = st.selectbox("Category (वर्ग) फ़िल्टर चुनें:", options=available_categories, key="p6_category_filter_secure_select_box")
                
                # फ़िल्टर के आधार पर डेटा को अलग करना
                filtered_scholarship = p6_authorized_db.copy()
                if selected_category != "All": 
                    filtered_scholarship = filtered_scholarship[filtered_scholarship["Category"].str.strip() == selected_category]
                
                # 🎛️ केवल स्कॉलरशिप पैनल के लिए मान्य निश्चित कॉलम्स की सूची (As Per Custom Layout)
                scholarship_fixed_cols = [
    "Admission Year", "Admission Session", "Eligibility Name", "Admission Application Number", 
    "Admission Date", "Unique Id", "Roll No.", "Application Enrollment No.", "Student Name", 
    "Father Name", "Mother Name", "Date Of Birth", "Category", "Subject", "Duretion", 
    "Mobile Number", "Email Id", "Address", "Year", "Status"
]
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

        # ======================================================================
        # P7: PANEL FOIL SHEET GENERATOR MODULE (All 3 Formats Fully Fixed)
        # ======================================================================
        elif current_panel_id == "P7":
            st.header(f"🖨️ {get_panel_title('P7')} (University CCE Foil Sheet Generator)")
            
            # मास्टर डेटाबेस से P7 के लिए स्वीकृत डेटा फ़िल्टर करें
            p7_authorized_db = live_db.copy()

            if p7_authorized_db.empty: 
                st.warning("⚠️ इस पैनल के लिए कोई अधिकृत स्वीकृत (Approved) डेटा उपलब्ध नहीं है। कृपया पहले P13 (Merge Panel) से डेटा को इस पैनल पर असाइन करें।")
            else:
                # फ़ॉर्मेट 2 के लिए अंकों को शब्दों में बदलने का यूटिलिटी फ़ंक्शन
                def marks_to_words(val_str):
                    val_clean = str(val_str).strip().upper()
                    if val_clean in ["A", "ABS", "ABSENT", "2 AB", "2AB"]: return "Absent"
                    try:
                        num = int(float(val_str))
                        words = {
                            0: "zero", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five",
                            6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten",
                            11: "eleven", 12: "twelve", 13: "thirteen", 14: "fourteen", 15: "fifteen",
                            16: "sixteen", 17: "seventeen", 18: "eighteen", 19: "nineteen", 20: "twenty"
                        }
                        return words.get(num, str(num))
                    except: return str(val_str)

                st.markdown('<div class="print-hide">', unsafe_allow_html=True)
                st.subheader("⚙️ Foil Sheet Generation Parameters")
                
                col_p7_1, col_p7_2 = st.columns(2)
                with col_p7_1:
                    foil_format_type = st.selectbox(
                        "📄 CCE Foil फ़ॉर्मेट चुनें:",
                        options=[
                            "Blank Foil (Side-by-Side List)", 
                            "CCE Mark Entry (Detailed Marks View)", 
                            "CCE List (Internal Evaluation - Multi Paper)"
                        ],
                        key="p7_foil_format_selection"
                    )
                with col_p7_2:
                    unique_subjects = sorted(list(set(p7_authorized_db['Branch'].dropna().astype(str).str.strip()))) if 'Branch' in p7_authorized_db.columns else sorted(list(set(p7_authorized_db['Subject'].dropna().astype(str).str.strip())))
                    selected_subject = st.selectbox(
                        "📚 Select Branch Name / Subject:", 
                        options=["All Branches"] + [s for s in unique_subjects if s != ""], 
                        key="cce_p7_sub_secure_engine"
                    )
                
                col_p7_3, col_p7_4 = st.columns(2)
                with col_p7_3:
                    chosen_option = st.selectbox(
                        "📆 Select Semester / Year Scope:",
                        options=["1 Semester", "2 Semester", "1 Year", "2 Year", "3 Year", "Fourth Semester", "6th SEMESTER"],
                        key="cce_p7_sem_secure_engine"
                    )
                with col_p7_4:
                    max_marks = st.text_input("Maximum Marks:", value="20")

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
                    
                    requested_columns = [
                        "Admission Year", "Admission Session", "Eligibility Name", "Admission Application Number", 
                        "Admission Date", "Unique ID", "Roll No.", "Application Enrollment No.", "Enrollment No.", 
                        "Student Name", "Father Name", "Mother Name", "Date of Birth", "Category", "Subject", 
                        "Duration", "Mobile Number", "Email ID", "Address", "Current Year", "Status"
                    ]
                    
                    multi_paper_cols = ["P-1", "P-2", "P-3", "P-4", "P-5", "P-6", "CCE-I", "CCE-II", "CCE-III", "Total Marks"]
                    for col_mark in multi_paper_cols:
                        if col_mark not in p7_authorized_db.columns:
                            p7_authorized_db[col_mark] = ""
                    
                    foil_filter_df = p7_authorized_db.copy()
                    # ✅ नया मैकेनिज्म: आपके फ़ॉर्मेट के कॉलम्स को लाइव डेटाबेस के कॉलम से जोड़ना
column_mapping_fixes = {
    "Unique Id": "Unique ID", "Student Abc Id": "Unique ID", 
    "Date Of Birth": "Date of Birth", "Duretion": "Duration", 
    "Email Id": "Email ID", "Year": "Current Year"
}

# लाइव डेटाबेस के डेटा को आपके दिए गए फ़ॉर्मेट के नामों में कॉपी करना
if not foil_filter_df.empty:
    if "Application Number" in foil_filter_df.columns:
        foil_filter_df["HIGHER EDU ID"] = foil_filter_df["Application Number"]
        foil_filter_df["application_no"] = foil_filter_df["Application Number"]
    if "Student Name" in foil_filter_df.columns:
        foil_filter_df["FULL NAME"] = foil_filter_df["Student Name"]
        foil_filter_df["Name"] = foil_filter_df["Student Name"]
    if "Father Name" in foil_filter_df.columns:
        foil_filter_df["FATHER NAME"] = foil_filter_df["Father Name"]
        foil_filter_df["father_name"] = foil_filter_df["Father Name"]
    if "Mother Name" in foil_filter_df.columns:
        foil_filter_df["MOTHER NAME"] = foil_filter_df["Mother Name"]
    if "Date of Birth" in foil_filter_df.columns:
        foil_filter_df["DATE OF BIRTH"] = foil_filter_df["Date of Birth"]
        foil_filter_df["dob"] = foil_filter_df["Date of Birth"]
    if "Category" in foil_filter_df.columns:
        foil_filter_df["CATEGORY"] = foil_filter_df["Category"]
        foil_filter_df["category"] = foil_filter_df["Category"]
    if "Degree" in foil_filter_df.columns:
        foil_filter_df["Drgree"] = foil_filter_df["Degree"]
    if "Branch" in foil_filter_df.columns:
        foil_filter_df["MAJOR SUB"] = foil_filter_df["Branch"]
    if "Minor Subjects" in foil_filter_df.columns:
        foil_filter_df["MINOR SUB"] = foil_filter_df["Minor Subjects"]
    if "Vocational Subjects" in foil_filter_df.columns:
        foil_filter_df["VOCATIONAL SUB"] = foil_filter_df["Vocational Subjects"]
    if "MDC Subjects" in foil_filter_df.columns:
        foil_filter_df["OPEN-ELECTIVE SUB"] = foil_filter_df["MDC Subjects"]
    if "PW/Ap/CE Subjects" in foil_filter_df.columns:
        foil_filter_df["PROJECT WORK"] = foil_filter_df["PW/Ap/CE Subjects"]
    
    # This line has been correctly realigned (4 spaces back)
    foil_filter_df = foil_filter_df.rename(columns=column_mapping_fixes) 
                    for essential_col in requested_columns:
                        if essential_col not in foil_filter_df.columns: 
                            foil_filter_df[essential_col] = ""
                    
                    if selected_subject != "All Branches": 
                        if "Branch" in foil_filter_df.columns:
                            foil_filter_df = foil_filter_df[foil_filter_df["Branch"].astype(str).str.strip() == selected_subject]
                        elif "Subject" in foil_filter_df.columns:
                            foil_filter_df = foil_filter_df[foil_filter_df["Subject"].astype(str).str.strip() == selected_subject]
                    
                    records_list = foil_filter_df.reset_index(drop=True).to_dict(orient="records")
                    total_records = len(records_list)

                    if total_records == 0:
                        st.warning("🔍 चयनित मापदंडों के आधार पर मास्टर डेटाबेस में कोई छात्र रिकॉर्ड नहीं मिला।")
                    else:
                        # ----------------------------------------------------------------------
                        # फ़ॉर्मेट 1: BLANK FOIL (साइड-बाय-साइड लेआउट)
                        # ----------------------------------------------------------------------
                        if foil_format_type == "Blank Foil (Side-by-Side List)":
                            left_records = records_list[:31]
                            right_records = records_list[31:62]
                            
                            def render_single_foil_block(start_sno, data_subset):
                                html_chunk = f"""
                                <div style="width: 49%; border: 1px solid #333; padding: 10px; background-color: #fff; font-family: Arial, sans-serif; box-sizing: border-box;">
                                    <div style="display: flex; justify-content: space-between; font-size: 11px; font-weight: bold; margin-bottom: 5px;">
                                        <span>Paper Code...................</span>
                                        <span>Bundle No...................</span>
                                    </div>
                                    <div style="text-align: center; border-bottom: 2px solid #000; padding-bottom: 3px; margin-bottom: 5px;">
                                        <h2 style="margin: 0; font-size: 13px; font-weight: bold;">GOVT. K.R.G. POST-GRADUATE AUTONOMOUS COLLEGE,</h2>
                                        <h2 style="margin: 2px 0 0 0; font-size: 13px; font-weight: bold;">GWALIOR (M.P.)</h2>
                                    </div>
                                    <div style="display: flex; justify-content: space-between; font-size: 11px; font-weight: bold; border-bottom: 1px dashed #333; padding-bottom: 3px; margin-bottom: 5px;">
                                        <span>Examination :- CCE</span>
                                        <span>{chosen_option.upper()}</span>
                                    </div>
                                    <div style="font-size: 11px; font-weight: bold; border-bottom: 1px dashed #333; padding-bottom: 3px; margin-bottom: 5px; display: flex; justify-content: space-between;">
                                        <span>Subject: {selected_subject.upper()}</span>
                                        <span>Paper: ...................................</span>
                                    </div>
                                    <div style="display: flex; justify-content: space-between; font-size: 11px; font-weight: bold; border-bottom: 2px double #000; padding-bottom: 3px; margin-bottom: 3px;">
                                        <span>Maximum Marks: {max_marks}</span>
                                        <span>Minimum Pass Marks: .................</span>
                                    </div>
                                    <div style="text-align: center; font-weight: bold; font-size: 12px; margin-bottom: 5px; letter-spacing: 2px;">FOIL</div>
                                    <table style="width: 100%; border-collapse: collapse; font-size: 10px; text-align: center; margin-bottom: 10px;">
                                        <thead>
                                            <tr>
                                                <th colspan="2" style="border: 1px solid #000; padding: 2px; width: 40%; font-size: 10px;">1</th>
                                                <th colspan="2" style="border: 1px solid #000; padding: 2px; width: 60%; font-size: 10px;">2</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                """
                                
                                for idx, row in enumerate(records_list):
                                    c1 = str(row.get("CCE-I", "")).strip()
                                    c2 = str(row.get("CCE-II", "")).strip()
                                    c3 = str(row.get("CCE-III", "")).strip()
                                    tot = str(row.get("Total Marks", "")).strip()
                                    words_val = marks_to_words(tot) if tot else ""
                                    
                                    mark_entry_html += f"""
                                            <tr>
                                                <td style="border: 1px solid #000; padding: 5px; font-weight: bold;">{idx + 1}</td>
                                                <td style="border: 1px solid #000; padding: 5px; font-family: monospace; font-size: 12px;">{row.get("Roll No.", "")}</td>
                                                <td style="border: 1px solid #000; padding: 5px;">{c1 if c1 else "&nbsp;"}</td>
                                                <td style="border: 1px solid #000; padding: 5px;">{c2 if c2 else "&nbsp;"}</td>
                                                <td style="border: 1px solid #000; padding: 5px;">{c3 if c3 else "&nbsp;"}</td>
                                                <td style="border: 1px solid #000; padding: 5px; font-weight: bold;">{tot if tot else "&nbsp;"}</td>
                                                <td style="border: 1px solid #000; padding: 5px; text-align: left; padding-left: 10px;">{words_val}</td>
                                            </tr>
                                    """
                                    
                                mark_entry_html += """
                                        </tbody>
                                    </table>
                                </div>
                                """
                                st.markdown(mark_entry_html, unsafe_allow_html=True)

                        # ----------------------------------------------------------------------
                        # फ़ॉर्मेट 2: CCE MARK ENTRY (इमेज 2 के अनुसार विस्तृत मार्क्स लेआउट)
                        # ----------------------------------------------------------------------
                        elif foil_format_type == "CCE Mark Entry (Detailed Marks View)":
                            mark_entry_html = f"""
                            <div style="width: 100%; max-width: 850px; margin: 0 auto; border: 1px solid #000; padding: 15px; background-color: #fff; font-family: Arial, sans-serif; box-sizing: border-box;">
                                <div style="text-align: center; border-bottom: 1px solid #000; padding-bottom: 5px; margin-bottom: 5px; font-weight: bold; font-size: 13px;">
                                    GOVT. K.R.G. POST-GRADUATE (AUTO.) COLLEGE, GWALIOR (M.P.)
                                </div>
                                <div style="display: flex; justify-content: space-between; font-size: 12px; font-weight: bold; padding: 3px 0;">
                                    <span>Examination: {chosen_option.upper()}</span>
                                </div>
                                <div style="font-size: 12px; font-weight: bold; padding: 3px 0; border-bottom: 1px solid #000; margin-bottom: 5px;">
                                    Subject: {selected_subject.upper()}
                                </div>
                                <div style="text-align: center; font-weight: bold; font-size: 13px; margin-bottom: 5px; letter-spacing: 1px;">FOIL</div>
                                
                                <table style="width: 100%; border-collapse: collapse; font-size: 11px; text-align: center;">
                                    <thead>
                                        <tr>
                                            <th style="border: 1px solid #000; padding: 5px; width: 12%;">1</th>
                                            <th colspan="5" style="border: 1px solid #000; padding: 5px; width: 88%;">2</th>
                                        </tr>
                                        <tr>
                                            <th rowspan="2" style="border: 1px solid #000; padding: 5px;">Code No.</th>
                                            <th rowspan="2" style="border: 1px solid #000; padding: 5px; width: 18%;">Roll No.</th>
                                            <th colspan="4" style="border: 1px solid #000; padding: 4px;">Marks Obtained</th>
                                        </tr>
                                        <tr>
                                            <th style="border: 1px solid #000; padding: 4px; width: 12%;">CCE-I</th>
                                            <th style="border: 1px solid #000; padding: 4px; width: 12%;">CCE-II</th>
                                            <th style="border: 1px solid #000; padding: 4px; width: 12%;">CCE-III</th>
                                            <th style="border: 1px solid #000; padding: 4px; width: 12%;">Total</th>
                                            <th style="border: 1px solid #000; padding: 4px; width: 34%;">In Words</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                            """
                            
                            for idx, row in enumerate(records_list):
                                c1 = str(row.get("CCE-I", "")).strip()
                                c2 = str(row.get("CCE-II", "")).strip()
                                c3 = str(row.get("CCE-III", "")).strip()
                                tot = str(row.get("Total Marks", "")).strip()
                                words_val = marks_to_words(tot) if tot else ""
                                
                                mark_entry_html += f"""
                                        <tr>
                                            <td style="border: 1px solid #000; padding: 5px; font-weight: bold;">{idx + 1}</td>
                                            <td style="border: 1px solid #000; padding: 5px; font-family: monospace; font-size: 12px;">{row.get("Roll No.", "")}</td>
                                            <td style="border: 1px solid #000; padding: 5px;">{c1 if c1 else "&nbsp;"}</td>
                                            <td style="border: 1px solid #000; padding: 5px;">{c2 if c2 else "&nbsp;"}</td>
                                            <td style="border: 1px solid #000; padding: 5px;">{c3 if c3 else "&nbsp;"}</td>
                                            <td style="border: 1px solid #000; padding: 5px; font-weight: bold;">{tot if tot else "&nbsp;"}</td>
                                            <td style="border: 1px solid #000; padding: 5px; text-align: left; padding-left: 10px;">{words_val}</td>
                                        </tr>
                                """
                                
                            mark_entry_html += """
                                    </tbody>
                                </table>
                            </div>
                            """
                            st.markdown(mark_entry_html, unsafe_allow_html=True)

                        # ----------------------------------------------------------------------
                        # फ़ॉर्मेट 3: CCE LIST INTERNAL EVALUATION (इमेज 3 के अनुसार मल्टी-पेपर लेआउट)
                        # ----------------------------------------------------------------------
                        elif foil_format_type == "CCE List (Internal Evaluation - Multi Paper)":
                            multi_paper_html = f"""
                            <div style="width: 100%; max-width: 950px; margin: 0 auto; border: 1px solid #000; padding: 15px; background-color: #fff; font-family: Arial, sans-serif; box-sizing: border-box;">
                                <div style="text-align: center; font-weight: bold; font-size: 14px; margin-bottom: 4px;">
                                    GOVT. K.R.G. POST-GRADUATE AUTONOMOUS COLLEGE, GWALIOR (M.P.)
                                </div>
                                <div style="text-align: center; font-weight: bold; font-size: 13px; margin-bottom: 4px;">
                                    Examination: {chosen_option.upper()}
                                </div>
                                <div style="text-align: center; font-weight: bold; font-size: 13px; margin-bottom: 4px; border-bottom: 1px solid #000; padding-bottom: 5px;">
                                    CCE List (Internal Evaluation)
                                </div>
                                <div style="text-align: center; font-weight: bold; font-size: 14px; margin-top: 5px; margin-bottom: 10px; letter-spacing: 2px;">
                                    FOIL
                                </div>
                                
                                <table style="width: 100%; border-collapse: collapse; font-size: 11px; text-align: center; table-layout: fixed;">
                                    <thead>
                                        <tr style="font-weight: bold;">
                                            <th style="border: 1px solid #000; padding: 6px; width: 6%;">S. No.</th>
                                            <th style="border: 1px solid #000; padding: 6px; width: 12%;">Roll No.</th>
                                            <th style="border: 1px solid #000; padding: 6px; width: 22%; text-align: left;">Name</th>
                                            <th style="border: 1px solid #000; padding: 6px; width: 22%; text-align: left;">Father Name</th>
                                            <th style="border: 1px solid #000; padding: 6px; width: 7%;">P-1</th>
                                            <th style="border: 1px solid #000; padding: 6px; width: 7%;">P-2</th>
                                            <th style="border: 1px solid #000; padding: 6px; width: 7%;">P-3</th>
                                            <th style="border: 1px solid #000; padding: 6px; width: 7%;">P-4</th>
                                            <th style="border: 1px solid #000; padding: 6px; width: 7%;">P-5</th>
                                            <th style="border: 1px solid #000; padding: 6px; width: 7%;">P-6</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                            """
                            
                            for idx, row in enumerate(records_list):
                                s_name = str(row.get("Student Name", "")).upper()
                                f_name = str(row.get("Father Name", "")).upper()
                                r_num = str(row.get("Roll No.", ""))
                                
                                p1 = str(row.get("P-1", "")).strip()
                                p2 = str(row.get("P-2", "")).strip()
                                p3 = str(row.get("P-3", "")).strip()
                                p4 = str(row.get("P-4", "")).strip()
                                p5 = str(row.get("P-5", "")).strip()
                                p6 = str(row.get("P-6", "")).strip()
                                
                                multi_paper_html += f"""
                                        <tr>
                                            <td style="border: 1px solid #000; padding: 5px; font-weight: bold;">{idx + 1}</td>
                                            <td style="border: 1px solid #000; padding: 5px; font-family: monospace; font-size: 11px;">{r_num}</td>
                                            <td style="border: 1px solid #000; padding: 5px; text-align: left; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{s_name}</td>
                                            <td style="border: 1px solid #000; padding: 5px; text-align: left; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{f_name}</td>
                                            <td style="border: 1px solid #000; padding: 5px;">{p1 if p1 else "&nbsp;"}</td>
                                            <td style="border: 1px solid #000; padding: 5px;">{p2 if p2 else "&nbsp;"}</td>
                                            <td style="border: 1px solid #000; padding: 5px;">{p3 if p3 else "&nbsp;"}</td>
                                            <td style="border: 1px solid #000; padding: 5px;">{p4 if p4 else "&nbsp;"}</td>
                                            <td style="border: 1px solid #000; padding: 5px;">{p5 if p5 else "&nbsp;"}</td>
                                            <td style="border: 1px solid #000; padding: 5px;">{p6 if p6 else "&nbsp;"}</td>
                                        </tr>
                                """
                                
                            multi_paper_html += """
                                    </tbody>
                                </table>
                            </div>
                            """
                            st.markdown(multi_paper_html, unsafe_allow_html=True)

        # ----------------------------------------------------------------------
        # P8: PANEL CCE RECORD MODULE (Internal Assessment Ledger Entry - Isolated View)
        # ----------------------------------------------------------------------
        elif current_panel_id == "P8":
            st.header(f"📋 {get_panel_title('P8')} (Internal Assessment Marks Ledger)")
            
            for f in ["CCE Marks Obtained", "CCE Attendance Status"]:
                if f not in live_db.columns: 
                    live_db[f] = ""
            
            # 🔍 Isolated Firewall Query Filter Rule: Only fetch records explicitly approved for P8
            p8_authorized_db = live_db[live_db["Target Panel Visibility"] == "P8"].copy()
            
            if p8_authorized_db.empty:
                st.warning("⚠️ इस पैनल के लिए कोई अधिकृत स्वीकृत (Approved) डेटा उपलब्ध नहीं है। कृपया पहले P13 (Merge Panel) से डेटा को इस पैनल पर असाइन कर अप्रूव करें।")
            else:
                st.markdown("""
                    <div style="background-color: #f1f8e9; border-left: 5px solid #558b2f; padding: 10px; border-radius: 4px; margin-bottom: 15px;">
                        📌 <b>ऑपरेटर निर्देश:</b> इस ग्रिड में आंतरिक मूल्यांकन अंक (CCE Marks) से संबंधित डेटा प्रदर्शित है। सुरक्षा नियमों के अनुसार केवल सुपर एडमिन ही इसमें बदलाव कर सकता है।
                    </div>
                """, unsafe_allow_html=True)
                
                available_subjects = ["All"] + sorted(list(set(p8_authorized_db["Branch"].dropna().astype(str).str.strip())))
                selected_sub = st.selectbox("Branch (शाखा) फ़िल्टर चुनें:", options=available_subjects, key="p8_subject_filter_secure_engine")
                
                filtered_cce = p8_authorized_db.copy()
                if selected_sub != "All": 
                    filtered_cce = filtered_cce[filtered_cce["Branch"].str.strip() == selected_sub]
                
                cce_fixed_cols = [
    "Admission Year", "Admission Session", "Eligibility Name", "Admission Application Number", 
    "Admission Date", "Unique Id", "Roll No.", "Application Enrollment No.", "Student Name", 
    "Father Name", "Mother Name", "Date Of Birth", "Category", "Subject", "Duretion", 
    "Mobile Number", "Email Id", "Address", "Year", "Status"
]
                
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
                
            # 🔍 Isolated Firewall Query Filter Rule: Only fetch records explicitly approved for P9
            p9_authorized_db = live_db[live_db["Target Panel Visibility"] == "P9"].copy()
            
            if p9_authorized_db.empty: 
                st.warning("⚠️ इस पैनल के लिए कोई अधिकृत स्वीकृत (Approved) डेटा उपलब्ध नहीं है। कृपया पहले P13 (Merge Panel) से डेटा को इस पैनल पर असाइन कर अप्रूव करें।")
            else:
                st.markdown("""
                    <div style="background-color: #f7f9fa; border-left: 5px solid #0288d1; padding: 10px; border-radius: 4px; margin-bottom: 15px;">
                        📌 <b>ऑपरेटर निर्देश:</b> इस ग्रिड में बैच प्रमोशन (Batch Progression) से संबंधित डेटा प्रदर्शित है। सुरक्षा नियमों के अनुसार केवल सुपर एडमिन ही इसमें बदलाव कर सकता है।
                    </div>
                """, unsafe_allow_html=True)
                
                available_years = ["All"] + sorted(list(set(p9_authorized_db["Current Year"].dropna().astype(str).str.strip())))
                selected_year = st.selectbox("Current Year (वर्तमान वर्ष) फ़िल्टर चुनें:", options=available_years, key="p9_year_filter_secure_engine")
                
                filtered_promo = p9_authorized_db.copy()
                if selected_year != "All": 
                    filtered_promo = filtered_promo[filtered_promo["Current Year"].str.strip() == selected_year]
                
                promotion_fixed_cols = [
    "Admission Year", "Admission Session", "Applicant ID", "Roll No.", "Enroll No.", 
    "Student Name", "Father Name", "Mother Name", "Caste", "Mob No.", "Subject", "Year", "Result"
]
                
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
            
            # 🔍 Isolated Firewall Query Filter Rule: Only fetch records explicitly approved for P10
            p10_authorized_db = live_db[live_db["Target Panel Visibility"] == "P10"].copy()
            
            if p10_authorized_db.empty: 
                st.warning("⚠️ इस पैनल के लिए कोई अधिकृत स्वीकृत (Approved) डेटा उपलब्ध नहीं है। कृपया पहले P13 (Merge Panel) से डेटा को इस पैनल पर असाइन कर अप्रूव करें।")
            else:
                st.markdown("""
                    <div style="background-color: #f3e5f5; border-left: 5px solid #8e24aa; padding: 10px; border-radius: 4px; margin-bottom: 15px;">
                        📌 <b>ऑपरेटर निर्देश:</b> इस ग्रिड में परीक्षा परिणाम (Exam Result) से संबंधित डेटा प्रदर्शित है। सुरक्षा नियमों के अनुसार केवल सुपर एडमिन ही इसमें बदलाव कर सकता है।
                    </div>
                """, unsafe_allow_html=True)
                
                available_subjects = ["All"] + sorted(list(set(p10_authorized_db["Branch"].dropna().astype(str).str.strip())))
                selected_sub = st.selectbox("Branch (शाखा) फ़िल्टर चुनें:", options=available_subjects, key="p10_subject_filter_secure_engine")
                
                filtered_res = p10_authorized_db.copy()
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
                    st.info("🔓 **एडमिन कंट्रोल मोड:** आपके पास परीक्षा परिणाम पंजी (Tabulation Register) एडमिट और सिंक करने का पूर्ण अधिकार है।")
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
        # P11: SYSTEM INFORMER BLOCK (Official Campus Notice Board Window)
        # ----------------------------------------------------------------------
        elif current_panel_id == "P11":
            st.header(f"📢 {get_panel_title('P11')} (Institutional Announcements Desk)")
            
            st.markdown("""
                <div style="background-color: #fffaf0; border-left: 5px solid #ff9800; padding: 12px; border-radius: 4px; margin-bottom: 20px;">
                    ℹ️ <b>आधिकारिक डिजिटल सूचना पटल (Read-Only Matrix):</b> इस पैनल पर वर्तमान सत्र में सक्रिय प्रशासनिक एवं अकादमिक घोषणाएं प्रदर्शित हैं। 
                    सुरक्षा एवं डेटा अखंडता प्रोटोकॉल के अनुसार, इसमें लाइव संशोधन करने का अधिकार केवल सुपर एडमिन (पैनल 12/15) के पास है।
                </div>
            """, unsafe_allow_html=True)
            
            # Formatted list parser system to display line-by-line active guidelines cleanly
            if st.session_state.notice_text.strip() == "":
                st.info("💡 वर्तमान में सूचना पटल पर कोई नया नोटिस या घोषणा उपलब्ध नहीं है।")
            else:
                st.markdown("### 📋 Current Active Announcements Board")
                
                # Split raw multiline notice configurations into clean scannable list item fragments
                formatted_preview = "".join([
                    f"<li style='margin-bottom:12px; font-size:15px; color:#222; line-height:1.6;'>{line.strip()}</li>" 
                    for line in st.session_state.notice_text.split('\n') if line.strip()
                ])
                
                st.markdown(f"""
                    <div style="background-color: #ffffff; border: 1px solid #e0e0e0; padding: 20px; border-radius: 6px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom:20px;">
                        <ul style="padding-left: 20px; margin: 0;">{formatted_preview}</ul>
                    </div>
                """, unsafe_allow_html=True)
                
            # Quick Action Framework Layer
            st.markdown("---")
            st.caption("🔒 Security Status: Encrypted Session | Access Control Level: Read-Only Operator Mode")

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
                
                # --- Part 1: Official Notice Board Guidelines Customizer ---
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

        # ======================================================================
        # P13: 🔀 MERGE & APPROVE PANEL (Complete Integrated Routing System)
        # ======================================================================
        elif current_panel_id == "P13":
            st.header(f"🔀 {get_panel_title('P13')} (Live Multi-Column Merge Verification & Routing Room)")
            
            # स्टेजिंग कतार और मुख्य लाइव डेटाबेस लोड करें
            stage_db = load_stage_data()
            master_db_lookup = load_live_data()
            
            if stage_db.empty:
                st.success("🟢 शानदार! स्टेजिंग कतार पूर्णतः खाली है। पैनल 1 से भेजी गयी सभी फाइलें प्रोसेस की जा चुकी हैं।")
            else:
                st.markdown("""
                    <div style="background-color: #f0f7ff; border-left: 5px solid #1465de; padding: 12px; border-radius: 4px; margin-bottom: 20px;">
                        🎯 <b>कन्फर्मेशन मर्ज गाइड:</b> पहले वह पैनल (Main File) चुनें जिसका डेटा बदलना है, फिर स्टेजिंग से नई फ़ाइल (Anya File) चुनकर लाइव मैचिंग चेक करें। यदि मर्ज नहीं करना है तो सीधे अप्रूव करें।
                    </div>
                """, unsafe_allow_html=True)
                
                # ----------------------------------------------------------------------
                # 👑 स्टेप 1: MAIN FILE (पैनल से डेटा का चयन और लाइव प्रीव्यू)
                # ----------------------------------------------------------------------
                st.subheader("👑 Step 1: Select Main File Panel")
                panel_options_map = {
                    "Panel 2: Admission View": "P2", "Panel 3: Unique ID View": "P3",
                    "Panel 4: Roll No View": "P4", "Panel 5: Enrollment View": "P5",
                    "Panel 6: Scholarship View": "P6", "Panel 8: CCE Record View": "P8",
                    "Panel 10: Result View": "P10"
                }
                
                selected_main_panel_lbl = st.selectbox(
                    "निरीक्षण और अपडेट करने के लिए मुख्य पैनल (Main File Source) चुनें:",
                    options=list(panel_options_map.keys()),
                    key="p13_main_panel_dropdown"
                )
                target_main_panel_id = panel_options_map[selected_main_panel_lbl]
                
                # मुख्य डेटाबेस से केवल इसी पैनल का स्वीकृत डेटा निकालें
                main_file_db = master_db_lookup[master_db_lookup["Target Panel Visibility"] == target_main_panel_id].copy()
                
                st.write(f"📊 **Main File (Approved DB):** `{selected_main_panel_lbl}` | वर्तमान रिकॉर्ड्स संख्या: `{len(main_file_db)}`")
                if not main_file_db.empty:
                    with st.expander("👁️ मुख्य फ़ाइल (Main File) का पूरा लाइव डेटा देखें", expanded=False):
                        st.dataframe(main_file_db[[c for c in ["Admission Year", "Application Number", "Student Name", "Father Name", "Branch"] if c in main_file_db.columns]], use_container_width=True)
                else:
                    st.warning("⚠️ इस चयनित पैनल में वर्तमान में कोई स्वीकृत डेटा उपलब्ध नहीं है।")

                # ----------------------------------------------------------------------
                # 📄 स्टेप 2: ANYA FILE (स्टेजिंग कतार से नई फ़ाइल का चयन)
                # ----------------------------------------------------------------------
                st.markdown("---")
                st.subheader("📄 Step 2: Select Anya File (New Uploaded Staging File)")
                distinct_files = list(stage_db["Uploaded File Name"].unique())
                
                selected_anya_file = st.selectbox(
                    "स्टेजिंग कतार से वह नई फ़ाइल चुनें जिससे डेटा खींचना है (या सीधे अप्रूव करने के लिए छोड़ें):", 
                    options=["-- कोई अन्य फ़ाइल नहीं चुनें --"] + distinct_files,
                    key="p13_anya_file_select_v3"
                )

                # ----------------------------------------------------------------------
                # 🚀 केस ए: बिना मर्ज किए सीधे अप्रूव करने का मैकेनिज्म (Direct Approve Window)
                # ----------------------------------------------------------------------
                if selected_anya_file == "-- कोई अन्य फ़ाइल नहीं चुनें --":
                    st.markdown("---")
                    st.subheader("🚀 बिना मर्ज किए सीधे अप्रूव करें (Direct Approval Window)")
                    
                    # 🛑 फिक्स: पूरी लिस्ट पास करने के बजाय कतार की पहली फ़ाइल का नाम (स्ट्रिंग) निकालें
                    direct_target_file_name = distinct_files[0] if distinct_files else ""
                    
                    if not direct_target_file_name:
                        st.warning("कतार में कोई फ़ाइल उपलब्ध नहीं है।")
                    else:
                        file_subset_direct = stage_db[stage_db["Uploaded File Name"] == direct_target_file_name].copy()
                        st.info(f"💡 वर्तमान में स्टेजिंग कतार की फ़ाइल '**{direct_target_file_name}**' को इसके मूल रूप में सीधे किसी भी वर्किंग पैनल पर भेजने के लिए नीचे सेटिंग्स चुनें।")
                        
                        col_dir1, col_dir2 = st.columns(2)
                        with col_dir1:
                            direct_routing_panel = st.selectbox(
                                "📌 इस फ़ाइल को किस विशिष्ट वर्किंग पैनल पर विज़िबल करना है?",
                                options=[
                                    "P2 : Panal admission / Control Tracker",
                                    "P3 : Panal unique / ID Engine",
                                    "P4 : Panal roll / Number Allocation",
                                    "P5 : Panal enrollment / Permanent Manager",
                                    "P6 : Panal scholarship / Matrix Tracker",
                                    "P8 : Panal CCE Record Ledger",
                                    "P10 : Panal Result Tabulation Register"
                                ],
                                key="p13_direct_panel_routing_dropdown"
                            )
                            parsed_direct_panel_id = direct_routing_panel.split(" : ")[0].strip()
                            
                        with col_dir2:
                            st.write("")
                            st.write("")
                            direct_approve_btn = st.button("🚀 सीधे अप्रूव करें (Direct Approve & Sync)", type="primary", use_container_width=True, key="p13_direct_approve_btn")
                        
                        # गलत फाइल हटाने का विकल्प डायरेक्ट विंडो में भी
                        with st.expander("⚠️ डेंजर ज़ोन: इस फ़ाइल को स्टेजिंग से हटाएं (बिना अप्रूव किए)", expanded=False):
                            confirm_delete_dir = st.checkbox("हाँ, मैं इस फ़ाइल को पूरी तरह कतार से हटाना चाहता हूँ।", key="confirm_delete_dir_key")
                            if st.button("🗑️ इस फ़ाइल को डिलीट करें", type="primary", use_container_width=True, disabled=not confirm_delete_dir):
                                updated_stage_db = stage_db[stage_db["Uploaded File Name"] != direct_target_file_name]
                                save_stage_data(updated_stage_db)
                                st.error(f"💥 फ़ाइल '{direct_target_file_name}' हटा दी गई!")
                                st.rerun()

                        if direct_approve_btn:
                            try:
                                # 1. इस फ़ाइल के अंदर 'Target Panel Visibility' का टैग सेट करना
                                file_subset_direct["Target Panel Visibility"] = parsed_direct_panel_id
                                
                                # 2. सुनिश्चित करें कि सभी डिफॉल्ट मास्टर कॉलम्स मौजूद हों
                                for col in DEFAULT_COLUMNS:
                                    if col not in file_subset_direct.columns:
                                        file_subset_direct[col] = ""
                                        
                                # 3. यदि मुख्य डेटाबेस में पहले से इस पैनल का कोई डेटा है, तो उसे हटाकर फ्रेश ओवरराइट करना
                                remaining_master_db_dir = master_db_lookup[master_db_lookup["Target Panel Visibility"] != parsed_direct_panel_id].copy()
                                
                                # 4. मास्टर लाइव डेटाबेस में नया डेटा जोड़कर सेव करना
                                final_direct_master = pd.concat([remaining_master_db_dir, file_subset_direct[DEFAULT_COLUMNS]], ignore_index=True)
                                save_live_data(final_direct_master)
                                
                                # 5. स्टेजिंग कतार (Staging Queue) से इस फ़ाइल को सुरक्षित तरीके से हटा देना
                                remaining_stage_db_dir = stage_db[stage_db["Uploaded File Name"] != direct_target_file_name]
                                save_stage_data(remaining_stage_db_dir)
                                
                                st.success(f"🎉 शत-प्रतिशत सफलता! आपकी फ़ाइल बिना किसी बदलाव के सीधे स्वीकृत होकर {parsed_direct_panel_id} पैनल पर लाइव हो चुकी है!")
                                st.balloons()
                                st.rerun()
                            except Exception as dir_err:
                                st.error(f"सीधे अप्रूवल चक्र के दौरान तकनीकी समस्या आई: {dir_err}")

                # ----------------------------------------------------------------------
                # 🔍 केस बी: जब यूजर मर्ज करने के लिए स्टेजिंग से कोई ANYA FILE सेलेक्ट करता है
                # ----------------------------------------------------------------------
                else:
                    anya_file_subset = stage_db[stage_db["Uploaded File Name"] == selected_anya_file].copy()
                    st.write(f"📦 **Anya File (Staging Column Source):** `{selected_anya_file}` | छात्र रिकॉर्ड्स: `{len(anya_file_subset)}`")

                    with st.expander("⚠️ डेंजर ज़ोन: गलत फ़ाइल को स्टेजिंग से हटाएं", expanded=False):
                        st.warning(f"क्या आप निश्चित रूप से फ़ाइल '**{selected_anya_file}**' को स्टेजिंग कतार से हटाना चाहते हैं?")
                        confirm_delete = st.checkbox("हाँ, मैं इस फ़ाइल को डिलीट करना चाहता हूँ।", key="confirm_delete_v3")
                        if st.button("🗑️ परमानेंटली डिलीट करें", type="primary", use_container_width=True, disabled=not confirm_delete):
                            updated_stage_db = stage_db[stage_db["Uploaded File Name"] != selected_anya_file]
                            save_stage_data(updated_stage_db)
                            st.error(f"💥 फ़ाइल '{selected_anya_file}' हटा दी गई!")
                            st.rerun()

                    st.markdown("---")
                    st.subheader("🔍 Step 3: Configure Matching & 4-Columns Data Retrieval")
                    
                    if main_file_db.empty:
                        st.info("💡 अन्य फ़ाइल से मर्ज करने के लिए मुख्य पैनल में कम से कम एक डेटा रिकॉर्ड होना आवश्यक है।")
                    else:
                        col_m1, col_m2 = st.columns(2)
                        with col_m1:
                            main_match_key = st.selectbox(
                                "Main File का मैचिंग कॉलम चुनें (जैसे Application Number):",
                                options=list(main_file_db.columns),
                                key="xl_main_match_key_v3"
                            )
                        with col_m2:
                            anya_match_key = st.selectbox(
                                "Anya File का मैचिंग कॉलम चुनें (जैसे Application Number):",
                                options=list(anya_file_subset.columns),
                                key="xl_anya_match_key_v3"
                            )
                            
                        anya_return_cols = st.multiselect(
                            "Anya File के वे कॉलम्स चुनें जिनका डेटा Main File में भरना है (जैसे B, C, D कॉलम्स):",
                            options=[c for c in anya_file_subset.columns if c not in ["Uploaded File Name", "Target Panel Visibility"]],
                            default=[c for c in ["Student Name", "Father Name", "Mother Name", "Roll No."] if c in anya_file_subset.columns],
                            key="xl_anya_return_cols_v3"
                        )

                        # ----------------------------------------------------------------------
                        # 👁️ लाइव मर्ज प्रीव्यू इंजन
                        # ----------------------------------------------------------------------
                        if anya_return_cols:
                            try:
                                main_file_db[main_match_key] = main_file_db[main_match_key].astype(str).str.strip()
                                anya_file_subset[anya_match_key] = anya_file_subset[anya_match_key].astype(str).str.strip()
                                
                                anya_clean = anya_file_subset[[anya_match_key] + [c for c in anya_return_cols if c != anya_match_key]].copy().drop_duplicates(subset=[anya_match_key])
                                
                                preview_merged = pd.merge(
                                    main_file_db,
                                    anya_clean,
                                    left_on=main_match_key,
                                    right_on=anya_match_key,
                                    how='left',
                                    suffixes=('', '_new_data')
                                )
                                
                                for col in anya_return_cols:
                                    new_col_name = f"{col}_new_data" if f"{col}_new_data" in preview_merged.columns else col
                                    if new_col_name in preview_merged.columns:
                                        preview_merged[col] = preview_merged[new_col_name].fillna(preview_merged[col]).astype(str)
                                
                                if main_match_key in preview_merged.columns:
                                    if f"{main_match_key}_new_data" in preview_merged.columns:
                                        preview_merged[main_match_key] = preview_merged[main_match_key].fillna(preview_merged[f"{main_match_key}_new_data"])
                                
                                keep_preview_cols = [c for c in preview_merged.columns if not c.endswith('_new_data') and c != f"{anya_match_key}_y"]
                                final_preview_df = preview_merged[keep_preview_cols].copy()
                                
                                if main_match_key not in final_preview_df.columns and f"{main_match_key}_x" in final_preview_df.columns:
                                    final_preview_df = final_preview_df.rename(columns={f"{main_match_key}_x": main_match_key})
                                
                                st.markdown("#### 📈 Live Merge Preview (जांचें कि सही मर्ज है या नहीं)")
                                st.caption("नीचे दी गई तालिका दिखा रही है कि अप्रूव करने पर मेन फ़ाइल में डेटा किस प्रकार अपडेट होकर सेव होगा:")
                                
                                preview_display_cols = list(set(["Admission Year", main_match_key, "Student Name", "Father Name", "Target Panel Visibility"] + anya_return_cols))
                                st.dataframe(final_preview_df[[c for c in preview_display_cols if c in final_preview_df.columns]], use_container_width=True)
                                
                                # ----------------------------------------------------------------------
                                # 🚀 फाइनल अप्रूवल और रो ओवरराइटिंग सेटिंग्स
                                # ----------------------------------------------------------------------
                                st.markdown("---")
                                st.subheader("🚀 Step 4: Finalize & Precision Approve")
                                
                                col_app1, col_app2 = st.columns(2)
                                with col_app1:
                                    target_routing_panel = st.selectbox(
                                        "📌 इस स्वीकृत डेटा को किस वर्किंग पैनल पर विज़िबल रखना है?",
                                        options=[
                                            "P2 : Panal admission / Control Tracker",
                                            "P3 : Panal unique / ID Engine",
                                            "P4 : Panal roll / Number Allocation",
                                            "P5 : Panal enrollment / Permanent Manager",
                                            "P6 : Panal scholarship / Matrix Tracker",
                                            "P8 : Panal CCE Record Ledger",
                                            "P10 : Panal Result Tabulation Register"
                                        ],
                                        key="p13_target_panel_routing_dropdown_v3"
                                    )
                                    parsed_panel_id = target_routing_panel.split(" : ")[0].strip()
                                    
                                with col_app2:
                                    st.write("")
                                    st.write("")
                                    approve_action_btn = st.button("🚀 Approve & Update Selected Data Rows", type="primary", use_container_width=True, key="p13_final_approve_btn_v3")
                                
                                if approve_action_btn:
                                    final_preview_df["Target Panel Visibility"] = parsed_panel_id
                                    
                                    remaining_master_db = master_db_lookup[master_db_lookup["Target Panel Visibility"] != parsed_panel_id].copy()
                                    
                                    if main_match_key not in final_preview_df.columns and f"{main_match_key}_from_master" in final_preview_df.columns:
                                        final_preview_df[main_match_key] = final_preview_df[f"{main_match_key}_from_master"]
                                    
                                    for col in DEFAULT_COLUMNS:
                                        if col not in final_preview_df.columns:
                                            final_preview_df[col] = ""
                                            
                                    final_updated_master_db = pd.concat([remaining_master_db, final_preview_df[DEFAULT_COLUMNS]], ignore_index=True)
                                    save_live_data(final_updated_master_db)
                                    
                                    remaining_stage_db = stage_db[stage_db["Uploaded File Name"] != selected_anya_file]
                                    save_stage_data(remaining_stage_db)
                                    
                                    st.success(f"🎉 शत-प्रतिशत सफलता! Anya फ़ाइल का डेटा मुख्य फ़ाइल में सही जगह अपडेट होकर और मैचिंग कॉलम के साथ {parsed_panel_id} पर लाइव हो चुका है!")
                                    st.balloons()
                                    st.rerun()
                                    
                            except Exception as merge_err:
                                st.error(f"लाइव मर्ज वेरिफिकेशन के दौरान तकनीकी समस्या आई: {merge_err}")
                        else:
                            st.info("💡 कृपया प्रीव्यू और अपडेट इंजन को सक्रिय करने के लिए Step 3 से कम से कम एक रिटर्न कॉलम ज़रूर चुनें।")

        # ----------------------------------------------------------------------
        # P14: PANEL VIEWER (INTEGRATED INDEX SYSTEM - Isolated Inspector Window)
        # ----------------------------------------------------------------------
        elif current_panel_id == "P14":
            st.header(f"👁️ {get_panel_title('P14')} (Multi-Panel Inspection Window)")

            # Isolated structural views defined per functional panel assignment 
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

            # Map the clean panel ID string from the user dropdown selection selection
            panel_id_map = {
                "Panel 2: Admission View": "P2", "Panel 3: Unique ID View": "P3",
                "Panel 4: Roll No View": "P4", "Panel 5: Enrollment View": "P5",
                "Panel 6: Scholarship View": "P6", "Panel 7: CCE Foil View": "P7",
                "Panel 8: CCE Record View": "P8", "Panel 9: Promotion View": "P9",
                "Panel 10: Result View": "P10", "Panel 12: Dash Board View": "P12"
            }
            target_panel_id = panel_id_map[selected_panel_view]
            target_columns = panel_options_list[selected_panel_view]

            # 🔍 Isolated Firewall Query Rule: Filter centralized records matching the target visibility token
            view_filtered_db = live_db[live_db["Target Panel Visibility"] == target_panel_id].copy()

            for c_col in target_columns:
                if c_col not in view_filtered_db.columns:
                    view_filtered_db[c_col] = ""

            st.markdown(f"### 📋 {selected_panel_view} - Isolated Inspection Records")
            
            col_search1, col_search2 = st.columns(2)
            with col_search1:
                search_target_col = st.selectbox("खोजने के लिए फ़ील्ड चुनें:", options=target_columns, key="p14_search_col_target_secure")
            with col_search2:
                search_query_text = st.text_input(f"'{search_target_col}' में प्रविष्टि खोजें:", key="p14_query_val_text_secure").strip()

            if search_query_text != "":
                view_filtered_db = view_filtered_db[
                    view_filtered_db[search_target_col].astype(str).str.contains(search_query_text, case=False, na=False)
                ]

            st.write(f"वर्तमान ग्रिड में कुल उपलब्ध स्वीकृत छात्र रिकॉर्ड संख्या: **{len(view_filtered_db)}**")

            final_render_cols = [col for col in target_columns if col in view_filtered_db.columns]
            
            if not view_filtered_db.empty:
                display_ready_df = view_filtered_db[final_render_cols].copy()
                display_ready_df.insert(0, "S. No", range(1, len(display_ready_df) + 1))

                st.dataframe(display_ready_df, use_container_width=True, hide_index=True)
                
                st.download_button(
                    label=f"📥 Download Selected Dashboard Report Snapshot (CSV)",
                    data=view_filtered_db[final_render_cols].to_csv(index=False).encode('utf-8'),
                    file_name=f"{selected_panel_view.replace(':', '').replace(' ', '_').lower()}_snapshot.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="p14_download_compiled_report_btn_secure"
                )
            else:
                st.warning("🔍 निर्दिष्ट खोज प्रविष्टि या स्वीकृत पैनल विज़िबिलिटी के आधार पर कोई रिकॉर्ड नहीं मिला।")

        # ----------------------------------------------------------------------
        # P15: PANEL ADMIN (15 PANELS SUPREME ENGINE & NOTICE BOARD MANAGER)
        # ----------------------------------------------------------------------
        elif current_panel_id == "P15":
            st.header(f"🛠️ {get_panel_title('P15')} (Full Super-Admin Control Command)")
            
            # 📢 Live Notice Board Manager Panel Area
            st.subheader("📢 Live Notice Board Manager")
            with st.expander("कॉलेज सूचना पटल (Official Notice Board) की गाइडलाइंस एडिट करें", expanded=True):
                with st.form(key="p15_global_notice_form_final_secure"):
                    updated_notice_input = st.text_area(
                        "सूचना पटल की पंक्तियाँ लिखें (प्रत्येक नई लाइन मुख्य पेज पर एक नया पॉइंट बनेगी):",
                        value=st.session_state.notice_text,
                        height=150,
                        key="p15_notice_text_area_input_final_secure"
                    )
                    if st.form_submit_button("Publish & Save Notice Board Permanently", type="primary", use_container_width=True):
                        st.session_state.notice_text = updated_notice_input
                        save_notice_board(updated_notice_input)
                        st.success("🎉 कॉलेज सूचना पटल सफलतापूर्वक अपडेट हो गया है! यह बिना लॉगिन वाले होम पेज पर लाइव दिखाई देगा।")
                        st.rerun()

            st.markdown("---")
            st.subheader("✏️ Dynamic 15 Panels Name & Label Customizer")
            with st.expander("15 पैनल्स के नाम (App Titles) एडिट करने के लिए यहाँ क्लिक करें", expanded=False):
                with st.form(key="p15_panel_rename_matrix_form_final_secure"):
                    p_setup1, p_setup2 = st.columns(2)
                    temp_panel_mappings = {}
                    for idx, p_key in enumerate(DEFAULT_PANELS.keys()):
                        current_panel_name = st.session_state.panel_names.get(p_key, DEFAULT_PANELS[p_key])
                        if idx % 2 == 0:
                            with p_setup1: 
                                temp_panel_mappings[p_key] = st.text_input(f"Name for {p_key}:", value=current_panel_name, key=f"p15_ren_final_{p_key}")
                        else:
                            with p_setup2: 
                                temp_panel_mappings[p_key] = st.text_input(f"Name for {p_key}:", value=current_panel_name, key=f"p15_ren_final_{p_key}")
                    
                    if st.form_submit_button("Save All 15 Panel Titles Permanently", type="primary", use_container_width=True):
                        st.session_state.panel_names = temp_panel_mappings
                        save_panel_names(temp_panel_mappings)
                        st.success("✅ सभी 15 पैनल्स के नाम अपडेट हो गए हैं!")
                        st.rerun()

            st.markdown("---")
            st.subheader("🛡️ Global 15 Panels Visibility Toggle Switch Board")
            vis_tabs = st.tabs(["🔒 Panels P1 - P7 Control", "🔒 Panels P8 - P15 Control"])
            
            # Visibility Panel Controllers Layer for P1 - P7
            with vis_tabs[0]:
                c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
                panels_p1_p7 = ["P1", "P2", "P3", "P4", "P5", "P6", "P7"]
                cols_p1_p7 = [c1, c2, c3, c4, c5, c6, c7]
                for i, p_key in enumerate(panels_p1_p7):
                    with cols_p1_p7[i]:
                        status_lbl = "🙈 Hidden" if st.session_state.get(f"hide_panel_{p_key}", False) else "👀 Active"
                        if st.button(f"{p_key}\n({status_lbl})", use_container_width=True, key=f"p15_btn_v_final_{p_key}"):
                            st.session_state[f"hide_panel_{p_key}"] = not st.session_state.get(f"hide_panel_{p_key}", False)
                            st.rerun()
                            
            # Visibility Panel Controllers Layer for P8 - P15
            with vis_tabs[1]:
                c8, c9, c10, c11, c12, c13, c14, c15 = st.columns(8)
                panels_p8_p15 = ["P8", "P9", "P10", "P11", "P12", "P13", "P14", "P15"]
                cols_p8_p15 = [c8, c9, c10, c11, c12, c13, c14, c15]
                for i, p_key in enumerate(panels_p8_p15):
                    with cols_p8_p15[i]:
                        status_lbl = "🙈 Hidden" if st.session_state.get(f"hide_panel_{p_key}", False) else "👀 Active"
                        if st.button(f"{p_key}\n({status_lbl})", use_container_width=True, key=f"p15_btn_v_final_{p_key}"):
                            st.session_state[f"hide_panel_{p_key}"] = not st.session_state.get(f"hide_panel_{p_key}", False)
                            st.rerun()

            # ⚙️ सुपर-एडमिन मास्टर ड्रॉपडाउन लिस्ट कस्टमाइज़र
            st.markdown("---")
            st.subheader("⚙️ Super-Admin Master Dropdown List Customizer")
            st.markdown("पैनल 1 (Data Onboarding) में दिखने वाली तीनों स्क्रॉल सूचियों के विकल्पों को यहाँ से लाइव कस्टमाइज़ करें:")
            
            if "p11_dropdown_schemas" not in st.session_state:
                if "p14_dropdown_schemas" in st.session_state:
                    st.session_state.p11_dropdown_schemas = st.session_state.p14_dropdown_schemas
                else:
                    st.session_state.p11_dropdown_schemas = {
                        "file_types": ["Admission List", "Unique ID List", "Roll No. List", "Enrollment List", "Promotion List", "Result List"],
                        "academic_years": ["2024", "2025", "2026", "2027"],
                        "academic_sessions": ["2024-25", "2025-26", "2026-27", "2027-28"]
                    }
            
            st.session_state.p1_dropdown_schemas = st.session_state.p11_dropdown_schemas
            
            col_drop1, col_drop2, col_drop3 = st.columns(3)
            with col_drop1:
                st.markdown("##### 📁 1. File Segments / Types")
                edited_file_types = st.text_area("File Types (एक प्रति लाइन):", value="\n".join(st.session_state.p11_dropdown_schemas["file_types"]), height=140, key="p15_custom_file_types_text")
            with col_drop2:
                st.markdown("##### 📆 2. Academic Years")
                edited_years = st.text_area("Admission Years (एक प्रति लाइन):", value="\n".join(st.session_state.p11_dropdown_schemas["academic_years"]), height=140, key="p15_custom_years_text")
            with col_drop3:
                st.markdown("##### ⏳ 3. Academic Sessions")
                edited_sessions = st.text_area("Admission Sessions (एक प्रति line):", value="\n".join(st.session_state.p11_dropdown_schemas["academic_sessions"]), height=140, key="p15_custom_sessions_text")
            
            if st.button("💾 Apply & Update Master Dropdown Framework", type="primary", use_container_width=True, key="p15_save_dropdowns_btn"):
                # ... (आपका पुराना ड्रॉपडाउन सेव करने वाला कोड यहाँ ख़त्म होगा)
                st.rerun()

            # ======================================================================
            # 🔐 न्यू मॉड्यूल: सुरक्षित मास्टर CSV/XLSX फ़ाइल ओवरराइट अपलोडर (Fixed Auto Lock)
            # ======================================================================
            st.markdown("---")
            st.subheader("⚠️ Advanced Action: Dangerous Master File Overwrite Uploader (CSV / XLSX)")
            st.warning("यह एक अत्यंत संवेदनशील विकल्प है। यहाँ नई फ़ाइल अपलोड करने पर वर्तमान का पूरा लाइव डेटाबेस (`shared_student_database.csv`) स्थायी रूप से मिट जाएगा और नई फ़ाइल का डेटा नया मास्टर बन जाएगा।")
            
            # ऑटो-रीसेट ट्रिगर काउंटर स्टेट जो विजेट को रीबूट करेगा
            if "p15_uploader_reset_counter" not in st.session_state:
                st.session_state.p15_uploader_reset_counter = 0

            with st.expander("🔑 सुरक्षित मास्टर फ़ाइल अपलोड गेटवे खोलें", expanded=False):
                col_up_pass, col_up_file = st.columns(2)
                
                with col_up_pass:
                    # काउंटर को की (Key) के साथ जोड़कर डायनेमिक बनाया गया है ताकि एरर न आए
                    uploader_secure_password = st.text_input(
                        "🛡️ फ़ाइल अपलोडर स्पेशल पासवर्ड दर्ज करें:", 
                        type="password", 
                        key=f"p15_master_pass_widget_run_{st.session_state.p15_uploader_reset_counter}"
                    )
                
                with col_up_file:
                    is_password_correct = (uploader_secure_password == "admin@upload15")
                    
                    uploaded_master_file = st.file_uploader(
                        "सिस्टम में ओवरराइट करने के लिए मास्टर फ़ाइल चुनें (CSV / XLSX / XLS):", 
                        type=["csv", "xlsx", "xls"],
                        key=f"p15_master_file_widget_run_{st.session_state.p15_uploader_reset_counter}",
                        disabled=not is_password_correct
                    )
                
                if uploader_secure_password and not is_password_correct:
                    st.error("❌ गलत फ़ाइल अपलोडर पासवर्ड! अपलोड ब्लॉक लॉक है।")
                elif is_password_correct:
                    st.success("🔓 पासवर्ड सत्यापित! आप फ़ाइल अपलोड कर सकते हैं।")
                    
                    if uploaded_master_file is not None:
                        st.info(f"📁ं चयनित फ़ाइल: `{uploaded_master_file.name}` प्रोसेस होने के लिए तैयार है।")
                        
                        confirm_overwrite_checkbox = st.checkbox(
                            "मैं प्रमाणित करता हूँ कि मैं पुराना मास्टर डेटा डिलीट करके इस नई फ़ाइल को लाइव डेटाबेस बनाना चाहता हूँ।",
                            key=f"p15_master_chk_run_{st.session_state.p15_uploader_reset_counter}"
                        )
                        
                        if st.button("💥 FORCE OVERWRITE COMPLETE MASTER DATABASE NOW", type="primary", use_container_width=True, disabled=not confirm_overwrite_checkbox):
                            try:
                                if uploaded_master_file.name.endswith('.csv'):
                                    raw_uploaded_df = pd.read_csv(uploaded_master_file, dtype=str).fillna("")
                                elif uploaded_master_file.name.endswith('.xlsx'):
                                    raw_uploaded_df = pd.read_excel(uploaded_master_file, engine='openpyxl', dtype=str).fillna("")
                                elif uploaded_master_file.name.endswith('.xls'):
                                    try:
                                        raw_uploaded_df = pd.read_excel(uploaded_master_file, engine='xlsrd', dtype=str).fillna("")
                                    except:
                                        uploaded_master_file.seek(0)
                                        html_tables = pd.read_html(uploaded_master_file)
                                        raw_uploaded_df = html_tables[0].astype(str).fillna("") if html_tables else pd.DataFrame()
                                
                                if raw_uploaded_df.empty:
                                    st.error("❌ अपलोडेड फ़ाइल के अंदर कोई मान्य डेटा नहीं मिला।")
                                else:
                                    raw_uploaded_df = raw_uploaded_df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
                                    
                                    for col in DEFAULT_COLUMNS:
                                        if col not in raw_uploaded_df.columns:
                                            raw_uploaded_df[col] = ""
                                    
                                    if "Target Panel Visibility" not in raw_uploaded_df.columns or raw_uploaded_df["Target Panel Visibility"].eq("").all():
                                        raw_uploaded_df["Target Panel Visibility"] = "P2"
                                    
                                    finalized_uploaded_master = raw_uploaded_df[DEFAULT_COLUMNS].copy()
                                    save_live_data(finalized_uploaded_master)
                                    
                                    # 🔒 सुरक्षित रीसेट मैकेनिज्म: काउंटर बदलते ही विजेट फ्रेश रीबूट हो जाएगा और पुराना डेटा मिट जाएगा
                                    st.session_state.p15_uploader_reset_counter += 1
                                    
                                    st.success(f"🎉 शत-प्रतिशत सफलता! `{uploaded_master_file.name}` को नया लाइव मास्टर डेटाबेस बना दिया गया है। गेटवे को सुरक्षित लॉक कर दिया गया है।")
                                    st.balloons()
                                    st.rerun()
                                    
                            except Exception as upload_err:
                                st.error(f"मास्टर फ़ाइल डेटा प्रोसेसिंग चक्र में तकनीकी खराबी आई: {upload_err}")

            # ----------------------------------------------------------------------
            # यहाँ से आपका पुराना कोड वापस शुरू हो जाएगा:
            # ----------------------------------------------------------------------
            st.markdown("---")
            st.subheader("📊 Master Database List View & Advanced Operational Controls")
            
            # Action Toggles Column Layout
            col_ctrl1, col_ctrl2, col_ctrl3 = st.columns(3)
            with col_ctrl3:
                lock_label = "🔒 लिस्ट लॉक करें (Locked)" if st.session_state.admin_lock_state else "🔓 लिस्ट अनलॉक करें (Editable)"
                if st.button(lock_label, use_container_width=True, type="primary" if not st.session_state.admin_lock_state else "secondary", key="p15_lock_toggle_master_btn_final"):
                    st.session_state.admin_lock_state = not st.session_state.admin_lock_state
                    st.rerun()

            with col_ctrl1:
                lbl_edit = "👀 एडमिट टेक्स्ट FUNCTION: active" if st.session_state.admin_unhide_edit else "🙈 एडमिट टेक्स्ट FUNCTION: hidden"
                if st.button(lbl_edit, use_container_width=True, disabled=st.session_state.admin_lock_state, key="p15_edit_toggle_master_btn_final"):
                    st.session_state.admin_unhide_edit = not st.session_state.admin_unhide_edit
                    st.rerun()

            with col_ctrl2:
                lbl_move = "👀 कॉलम मूव बटन्स: active" if st.session_state.admin_unhide_move else "🙈 कॉलम मूव बटन्स: hidden"
                if st.button(lbl_move, use_container_width=True, key="p15_move_toggle_master_btn_final"):
                    st.session_state.admin_unhide_move = not st.session_state.admin_unhide_move
                    st.rerun()

            # Column shift parameters handler layer
            if st.session_state.admin_unhide_move:
                st.info("🔀 कॉलम का क्रम बदलने के लिए सेलेक्ट करें (Select Column to Shift):")
                target_col = st.selectbox("मूव करने के लिए कॉलम चुनें:", options=st.session_state.admin_columns_order, key="p15_column_shifter_select_box_final")
                c_left, c_right = st.columns(2)
                
                if c_left.button("⬅️ Shift Left", use_container_width=True, key="p15_shift_left_master_btn_final"):
                    idx = st.session_state.admin_columns_order.index(target_col)
                    if idx > 0:
                        st.session_state.admin_columns_order[idx], st.session_state.admin_columns_order[idx-1] = st.session_state.admin_columns_order[idx-1], st.session_state.admin_columns_order[idx]
                        st.rerun()
                        
                if c_right.button("➡️ Shift Right", use_container_width=True, key="p15_shift_right_master_btn_final"):
                    idx = st.session_state.admin_columns_order.index(target_col)
                    if idx < len(st.session_state.admin_columns_order) - 1:
                        st.session_state.admin_columns_order[idx], st.session_state.admin_columns_order[idx+1] = st.session_state.admin_columns_order[idx+1], st.session_state.admin_columns_order[idx]
                        st.rerun()

            # फ़ील्ड्स और ऑर्डर्स मैपिंग
            render_columns = [col for col in st.session_state.admin_columns_order if col in live_db.columns]
            ordered_db = live_db[render_columns].copy()
            ordered_db_display = ordered_db.rename(columns={c: get_display_name(c) for c in ordered_db.columns})
            ordered_db_display.insert(0, "S.No.", range(1, len(ordered_db_display) + 1))

            st.markdown(f"**📈 मुख्य लाइव डेटाबेस रिकॉर्ड्स की कुल संख्या:** `{len(ordered_db_display)}`")
            
            if ordered_db_display.empty:
                st.warning("💡 वर्तमान में मास्टर डेटाबेस पूरी तरह खाली है। कृपया पहले Panel 1 से नया डेटा लोड करें।")
            else:
                if st.session_state.admin_lock_state:
                    # लॉक मोड: केवल डेटा व्यू करने के लिए (Read-Only)
                    st.dataframe(ordered_db_display, use_container_width=True, hide_index=True)
                else:
                    # अनलॉक मोड: ग्रिड एडिटिंग और रो डिलीट करने के लिए एक्टिवेट
                    st.info("🔓 **एडिट और डिलीट मोड सक्रिय:** आप सेल पर डबल-क्लिक करके डेटा बदल सकते हैं। किसी रो को सिलेक्ट कर कीबोर्ड से Delete बटन दबाकर रो हटा सकते हैं।")
                    
                    disabled_fields = ["S.No."]
                    # यदि 'एडमिट टेक्स्ट FUNCTION' चालू नहीं (hidden) है, तो संवेदनशील कॉलम्स लॉक रहेंगे
                    if not st.session_state.admin_unhide_edit:
                        disabled_fields.extend([get_display_name("Application Number"), get_display_name("Student Name"), get_display_name("Father Name")])
                        
                    edited_master_db = st.data_editor(
                        ordered_db_display,
                        use_container_width=True,
                        disabled=disabled_fields,
                        hide_index=True,
                        num_rows="dynamic", # डायनेमिक रो डिलीट विकल्प सक्रिय
                        key="p15_supreme_master_live_editor_grid"
                    )
                    
                    if st.button("💾 Save Grid Changes to Master CSV File", type="primary", use_container_width=True, key="p15_save_master_csv_btn"):
                        try:
                            clean_edited_master = edited_master_db.drop(columns=["S.No."], errors="ignore")
                            
                            # मूल स्कीमा नामों में वापस रिवर्स मैप करना
                            display_to_orig_map = {get_display_name(c): c for c in live_db.columns}
                            clean_edited_master = clean_edited_master.rename(columns=display_to_orig_map)
                            
                            # मुख्य डेटाबेस फ़ाइल को सिंक और सुरक्षित सेव करना
                            save_live_data(clean_edited_master)
                            st.success("🎉 संपूर्ण मास्टर चेंजेस लाइव डेटाबेस फ़ाइल में सुरक्षित अपडेट हो गए हैं!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"डेटाबेस अपडेट चक्र में तकनीकी समस्या आई: {e}")
