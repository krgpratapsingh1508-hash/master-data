import streamlit as st
import pandas as pd
import os
import base64
import json

# à¤ªà¥‡à¤œ à¤•à¤¾ à¤²à¥‡à¤†à¤‰à¤Ÿ à¤¸à¥‡à¤Ÿ à¤•à¤°à¥‡à¤‚
st.set_page_config(layout="wide", page_title="Permanent Shared Live Database")

# à¤ªà¥à¤°à¤¿à¤‚à¤Ÿ à¤«à¤¼à¥‰à¤°à¥à¤®à¥‡à¤Ÿà¤¿à¤‚à¤—, à¤²à¥‡à¤†à¤‰à¤Ÿ à¤”à¤° à¤¨à¥‹à¤Ÿà¤¿à¤¸ à¤¬à¥‹à¤°à¥à¤¡ à¤•à¥‹ à¤µà¥à¤¯à¤µà¤¸à¥à¤¥à¤¿à¤¤ à¤•à¤°à¤¨à¥‡ à¤•à¥‡ à¤²à¤¿à¤ à¤¸à¥€à¤à¤¸à¤à¤¸ (CSS)
st.markdown("""
    <style>
    @media print {
        header, [data-testid="stHeader"], [data-testid="stSidebar"], 
        .stButton, .stFileUploader, [data-testid="stDecoration"], 
        [data-testid="stNotification"], [data-testid="stForm"], .print-hide {
            display: none !important;
        }
        @page { margin: 5mm; size: A4 landscape; }
        .main .block-container { padding: 0 !important; margin: 0 !important; }
    }
    .header-container { display: flex; align-items: center; gap: 20px; margin-bottom: 20px; }
    .header-text { display: flex; flex-direction: column; }
    .header-text h3 { margin: 0 !important; padding: 0 !important; color: #1465de; }
    .header-text h1 { margin: 0 !important; }
    
    /* à¤¨à¥‹à¤Ÿà¤¿à¤¸ à¤¬à¥‹à¤°à¥à¤¡ à¤¸à¥à¤Ÿà¤¾à¤‡à¤² */
    .notice-board {
        background-color: #f9f9f9;
        border-left: 6px solid #FF5733;
        padding: 15px;
        margin-bottom: 25px;
        border-radius: 4px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .notice-title { font-weight: bold; color: #333; margin-bottom: 8px; font-size: 18px; }
    </style>
""", unsafe_allow_html=True)

# à¤²à¥‹à¤—à¥‹ à¤²à¥‹à¤¡ à¤•à¤°à¤¨à¥‡ à¤•à¤¾ à¤«à¤‚à¤•à¥à¤¶à¤¨
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
            <h3>à¥ à¤¶à¥à¤°à¥€ à¤—à¥à¤°à¤µà¥‡ à¤¨à¤®à¤ƒ</h3>
            <h1>Permanent Shared Live Database System</h1>
        </div>
    </div>
""", unsafe_allow_html=True)

DB_FILE = "shared_student_database.csv"
CRED_FILE = "user_credentials_v15.json"
MAP_FILE = "column_mapping_schema.json"
PANEL_NAME_FILE = "panel_names_schema.json"

# ðŸ”’ 15 à¤ªà¥ˆà¤¨à¤²à¥à¤¸ à¤•à¥‡ à¤¹à¤¿à¤¸à¤¾à¤¬ à¤¸à¥‡ 15 à¤¸à¥‡à¤ªà¤°à¥‡à¤Ÿà¥‡à¤¡ à¤•à¥à¤°à¥‡à¤¡à¥‡à¤‚à¤¶à¤¿à¤¯à¤²à¥à¤¸ à¤•à¥€ à¤®à¤¾à¤¸à¥à¤Ÿà¤° à¤¡à¤¿à¤•à¥à¤¶à¤¨à¤°à¥€
DEFAULT_CREDENTIALS = {
    "admin": {"password": "admin15master", "role": "full_admin", "label": "ðŸ‘‘ Super Admin (All 15 Panels Control)"},
    "p1_entry": {"password": "entry1123", "role": "p1_role", "label": "ðŸ“ P1: Student Data Onboarding Operator"},
    "p2_admission": {"password": "adm2123", "role": "p2_role", "label": "ðŸŽ“ P2: Admission Control Manager"},
    "p3_enrollment": {"password": "enr3123", "role": "p3_role", "label": "ðŸ“‘ P3: University Enrollment Manager"},
    "p4_scholarship": {"password": "sch4123", "role": "p4_role", "label": "ðŸ’° P4: Portal & Scholarship Tracker"},
    "p5_result": {"password": "res5123", "role": "p5_role", "label": "ðŸ“Š P5: Tabulation Register Exam Controller"},
    "p6_promotion": {"password": "pro6123", "role": "p6_role", "label": "ðŸ“ˆ P6: Batch Progression Controller"},
    "p7_foil": {"password": "foil7123", "role": "p7_role", "label": "ðŸ–¨ï¸ P7: CCE Foil Sheet Generator"},
    "p8_cce_record": {"password": "cce8123", "role": "p8_role", "label": "ðŸ“‹ P8: Internal Assessment Ledger Entry"},
    "p9_extension": {"password": "ext9123", "role": "p9_role", "label": "ðŸ“Œ P9: Extension Ledger Room 1"},
    "p10_extension": {"password": "ext10123", "role": "p10_role", "label": "ðŸ“Œ P10: Extension Ledger Room 2"},
    "p11_extension": {"password": "ext11123", "role": "p11_role", "label": "ðŸ“Œ P11: Extension Ledger Room 3"},
    "p12_extension": {"password": "ext12123", "role": "p12_role", "label": "ðŸ“Œ P12: Extension Ledger Room 4"},
    "p13_merge": {"password": "mrg13123", "role": "p13_role", "label": "ðŸ”€ P13: External Database Smart Merge"},
    "p14_viewer": {"password": "view14123", "role": "p14_role", "label": "ðŸ‘ï¸ P14: Multi-Panel Inspection Window"}
}

# ðŸ› ï¸ à¤¡à¤¿à¤«à¤¼à¥‰à¤²à¥à¤Ÿ 15 à¤ªà¥ˆà¤¨à¤²à¥à¤¸ à¤•à¥€ à¤¡à¤¿à¤•à¥à¤¶à¤¨à¤°à¥€ à¤®à¥ˆà¤ªà¤¿à¤‚à¤— (P1 à¤¸à¥‡ P15)
DEFAULT_PANELS = {
    "P1": "Panal entry", "P2": "Panal admission", "P3": "Panal enrollment",
    "P4": "Panal scholarship", "P5": "Panal result", "P6": "Panal promotion",
    "P7": "Panal foil", "P8": "Panal cce record", "P9": "Panal P9 Extension",
    "P10": "Panal P10 Extension", "P11": "Panal P11 Extension", "P12": "Panal P12 Extension",
    "P13": "Panal merge", "P14": "Panal viewer", "P15": "Panel admin"
}

# ðŸŽ¯ à¤®à¤¾à¤¸à¥à¤Ÿà¤° à¤•à¥‰à¤²à¤®à¥à¤¸ à¤¸à¥‚à¤šà¥€
DEFAULT_COLUMNS = [
    "Admission Year", "Admission Session", "Eligibility Name", "Admission Application Number",
    "Admission Date", "Unique ID", "Roll No.", "Application Enrollment No.",
    "Enrollment No.", "Student Name", "Father Name", "Mother Name", "Date of Birth",
    "Category", "Subject Code", "Subject", "Duration", "Mobile Number", "Email ID", "Address", "Status",
    "Current Year"
]

# --- def load_credentials(): à¤µà¤¾à¤²à¥‡ à¤ªà¥à¤°à¤¾à¤¨à¥‡ à¤¹à¤¿à¤¸à¥à¤¸à¥‡ à¤•à¥‹ à¤¹à¤Ÿà¤¾à¤•à¤° à¤‡à¤¸à¥‡ à¤ªà¥‡à¤¸à¥à¤Ÿ à¤•à¤°à¥‡à¤‚ ---
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

# --- à¤‰à¤¸à¤•à¥€ à¤œà¤—à¤¹ à¤ªà¤° à¤¯à¤¹ à¤¨à¤¯à¤¾ à¤¸à¥à¤°à¤•à¥à¤·à¤¿à¤¤ à¤¬à¥à¤²à¥‰à¤• à¤ªà¥‡à¤¸à¥à¤Ÿ à¤•à¤°à¥‡à¤‚ ---
# à¤¯à¤¹ à¤•à¥‹à¤¡ à¤ªà¥à¤°à¤¾à¤¨à¥‡ à¤•à¥ˆà¤¶ à¤®à¥‡à¤®à¥‹à¤°à¥€ à¤•à¥‹ à¤œà¤¬à¤°à¤¨ à¤•à¥à¤²à¤¿à¤¯à¤° à¤•à¤°à¤•à¥‡ à¤¨à¤ 15 à¤¯à¥‚à¥›à¤°à¥à¤¸ à¤²à¥‹à¤¡ à¤•à¤°à¥‡à¤—à¤¾
if "credentials" not in st.session_state or len(st.session_state.credentials) < 15:
    st.session_state.credentials = DEFAULT_CREDENTIALS.copy()
else:
    st.session_state.credentials = load_credentials()

if "column_mappings" not in st.session_state: 
    st.session_state.column_mappings = load_column_mappings()

if "panel_names" not in st.session_state or len(st.session_state.panel_names) < 15:
    st.session_state.panel_names = DEFAULT_PANELS.copy()
else:
    st.session_state.panel_names = load_panel_names()
if "user_role" not in st.session_state: st.session_state.user_role = None  
if "logged_username" not in st.session_state: st.session_state.logged_username = None
if "show_login_form" not in st.session_state: st.session_state.show_login_form = False
if "admin_columns_order" not in st.session_state: st.session_state.admin_columns_order = DEFAULT_COLUMNS.copy()
if "admin_lock_state" not in st.session_state: st.session_state.admin_lock_state = True  
if "admin_unhide_edit" not in st.session_state: st.session_state.admin_unhide_edit = False
if "admin_unhide_move" not in st.session_state: st.session_state.admin_unhide_move = False
if "admin_hide_master_data" not in st.session_state: st.session_state.admin_hide_master_data = False
if "cce_foil_generated" not in st.session_state: st.session_state.cce_foil_generated = False

for k in DEFAULT_PANELS.keys():
    if f"hide_panel_{k}" not in st.session_state: st.session_state[f"hide_panel_{k}"] = False

live_db = load_live_data()

def get_display_name(internal_col_name):
    return st.session_state.column_mappings.get(internal_col_name, internal_col_name)

def get_panel_title(panel_id):
    return st.session_state.panel_names.get(panel_id, DEFAULT_PANELS[panel_id])


# ==========================================================
# ðŸ›‘ à¤²à¥‰à¤—à¤¿à¤¨ à¤¸à¥‡ à¤ªà¤¹à¤²à¥‡ à¤•à¤¾ à¤¬à¥à¤²à¥‰à¤•
# ==========================================================
if st.session_state.user_role is None:
    st.markdown("""
        <div class="notice-board">
            <div class="notice-title">ðŸ“¢ à¤•à¥‰à¤²à¥‡à¤œ à¤¸à¥‚à¤šà¤¨à¤¾ à¤ªà¤Ÿà¤² (Official Notice Board)</div>
            <p>1. à¤¯à¤¹ à¤à¤• à¤ªà¥‚à¤°à¥à¤£à¤¤à¤ƒ à¤¸à¥à¤°à¤•à¥à¤·à¤¿à¤¤, à¤²à¤¾à¤‡à¤µ à¤•à¥à¤²à¤¾à¤‰à¤¡ à¤¸à¥à¤Ÿà¥‚à¤¡à¥‡à¤‚à¤Ÿ à¤¡à¥‡à¤Ÿà¤¾à¤¬à¥‡à¤¸ à¤®à¥ˆà¤¨à¥‡à¤œà¤®à¥‡à¤‚à¤Ÿ à¤¸à¤¿à¤¸à¥à¤Ÿà¤® à¤¹à¥ˆà¥¤</p>
            <p>2. à¤¡à¥‡à¤Ÿà¤¾ à¤ªà¥à¤°à¤µà¤¿à¤·à¥à¤Ÿà¤¿, à¤¸à¥à¤§à¤¾à¤°, à¤¸à¥à¤•à¥‰à¤²à¤°à¤¶à¤¿à¤ª à¤µà¥‡à¤°à¤¿à¤«à¤¿à¤•à¥‡à¤¶à¤¨ à¤¯à¤¾ à¤ªà¤°à¥€à¤•à¥à¤·à¤¾ à¤ªà¤°à¤¿à¤£à¤¾à¤® à¤…à¤ªà¤¡à¥‡à¤Ÿ à¤•à¤°à¤¨à¥‡ à¤•à¥‡ à¤²à¤¿à¤ à¤…à¤§à¤¿à¤•à¥ƒà¤¤ à¤¯à¥‚à¤œà¤° à¤•à¥à¤°à¥‡à¤¡à¥‡à¤‚à¤¶à¤¿à¤¯à¤²à¥à¤¸ à¤•à¤¾ à¤‰à¤ªà¤¯à¥‹à¤— à¤•à¤°à¥‡à¤‚à¥¤</p>
            <p>3. à¤¬à¤¿à¤¨à¤¾ à¤²à¥‰à¤—à¤¿à¤¨ à¤•à¥‡ à¤¡à¥‡à¤Ÿà¤¾à¤¬à¥‡à¤¸ à¤¤à¤• à¤ªà¤¹à¥à¤à¤š à¤ªà¥‚à¤°à¥à¤£à¤¤à¤ƒ à¤ªà¥à¤°à¤¤à¤¿à¤¬à¤‚à¤§à¤¿à¤¤ à¤¹à¥ˆà¥¤ à¤•à¤¿à¤¸à¥€ à¤­à¥€ à¤¸à¤®à¤¸à¥à¤¯à¤¾ à¤•à¥‡ à¤²à¤¿à¤ à¤¸à¥à¤ªà¤°-à¤à¤¡à¤®à¤¿à¤¨ à¤¸à¥‡ à¤¸à¤‚à¤ªà¤°à¥à¤• à¤•à¤°à¥‡à¤‚à¥¤</p>
        </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.show_login_form:
        if st.button("ðŸ” Click Here to Open Secure Login System", type="primary", use_container_width=True):
            st.session_state.show_login_form = True
            st.rerun()
            
    if st.session_state.show_login_form:
        st.markdown("---")
        st.subheader("ðŸ”’ Enter Secure Gateway Credentials")
        col_l1, col_l2 = st.columns(2)
        
        with col_l1:
            user_list_options = list(st.session_state.credentials.keys())
            def get_lbl(uid): return st.session_state.credentials[uid].get("label", uid)
            user_input = st.selectbox("ðŸ‘¤ Select Your User ID / Panel Account:", options=user_list_options, format_func=get_lbl)
            
        with col_l2:
            password_input = st.text_input("ðŸ”‘ Enter Secure Password:", type="password")
            
        # === à¤ à¥€à¤• à¤‰à¤¸à¥€ à¤–à¤¾à¤²à¥€ à¤œà¤—à¤¹ à¤ªà¤° à¤‡à¤¸ à¤¨à¤ à¤•à¥‹à¤¡ à¤•à¥‹ à¤ªà¥‡à¤¸à¥à¤Ÿ à¤•à¤°à¥‡à¤‚ ===
        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
            if st.button("ðŸ”“ Verify & Access System", type="primary", use_container_width=True):
                if user_input in st.session_state.credentials and st.session_state.credentials[user_input]["password"] == password_input:
                    st.session_state.user_role = st.session_state.credentials[user_input]["role"]
                    st.session_state.logged_username = user_input
                    st.session_state.show_login_form = False
                    st.success("âœ… à¤•à¥à¤°à¥‡à¤¡à¥‡à¤‚à¤¶à¤¿à¤¯à¤² à¤¸à¥à¤µà¥€à¤•à¥ƒà¤¤! à¤ªà¥ˆà¤¨à¤² à¤®à¥‡à¤‚ à¤ªà¥à¤°à¤µà¥‡à¤¶ à¤•à¤¿à¤¯à¤¾ à¤œà¤¾ à¤°à¤¹à¤¾ à¤¹à¥ˆ...")
                    st.rerun()
                else:
                    st.error("âŒ à¤—à¤²à¤¤ à¤ªà¤¾à¤¸à¤µà¤°à¥à¤¡ à¤¦à¤°à¥à¤œ à¤•à¤¿à¤¯à¤¾ à¤—à¤¯à¤¾ à¤¹à¥ˆ!")
        with c_btn2:
            if st.button("âŒ Close Login Windows", type="secondary", use_container_width=True):
                st.session_state.show_login_form = False
                st.rerun()

# ==========================================================
# Phase 2: Post Authorized Panel Systems
# ==========================================================
# === à¤‡à¤¸ à¤¸à¤Ÿà¥€à¤• à¤¬à¥à¤²à¥‰à¤• à¤•à¥‹ else: à¤•à¥‡ à¤ à¥€à¤• à¤¨à¥€à¤šà¥‡ à¤°à¥€à¤ªà¥à¤²à¥‡à¤¸ à¤•à¤°à¥‡à¤‚ ===
else:
    role = st.session_state.user_role
    username = st.session_state.logged_username
    
    st.markdown('<div class="print-hide">', unsafe_allow_html=True)
    col_top1, col_top2 = st.columns(2)
    with col_top1:
        st.success(f"ðŸ”‘ à¤¸à¤•à¥à¤°à¤¿à¤¯ à¤¸à¤¤à¥à¤°: {username.upper()} | à¤­à¥‚à¤®à¤¿à¤•à¤¾ à¤…à¤§à¤¿à¤•à¤¾à¤°: {role.upper()}")
    with col_top2:
        if st.button("ðŸ”’ Secure Logout / Exit System", type="primary", use_container_width=True):
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

    active_tabs_names = [f"{p} : {get_panel_title(p)}" for p in allowed_panels if not st.session_state[f"hide_panel_{p}"] or role == "full_admin"]
    
    if not active_tabs_names:
        st.warning("âš ï¸ à¤µà¤°à¥à¤¤à¤®à¤¾à¤¨ à¤®à¥‡à¤‚ à¤†à¤ªà¤•à¥€ à¤­à¥‚à¤®à¤¿à¤•à¤¾ à¤•à¥‡ à¤²à¤¿à¤ à¤•à¥‹à¤ˆ à¤­à¥€ à¤ªà¥ˆà¤¨à¤² à¤à¤•à¥à¤Ÿà¤¿à¤µ à¤¨à¤¹à¥€à¤‚ à¤•à¤¿à¤¯à¤¾ à¤—à¤¯à¤¾ à¤¹à¥ˆà¥¤")
    else:
        selected_tab_ui = st.sidebar.radio("ðŸ§­ Navigate Active Modules:", options=active_tabs_names)
        current_panel_id = selected_tab_ui.split(" : ")[0]


        # ----------------------------------------------------------------------
        # P1: PANEL ENTRY MODULE
        # ----------------------------------------------------------------------
        if current_panel_id == "P1":
            st.header(f"ðŸ“ {get_panel_title('P1')} (Student Data Onboarding)")
            entry_method = st.selectbox("âš™ï¸ à¤¡à¥‡à¤Ÿà¤¾ à¤à¤‚à¤Ÿà¥à¤°à¥€ à¤•à¤¾ à¤®à¤¾à¤§à¥à¤¯à¤® à¤šà¥à¤¨à¥‡à¤‚:", options=["ðŸ“ CSV à¤«à¤¼à¤¾à¤‡à¤² à¤¬à¤²à¥à¤• à¤…à¤ªà¤²à¥‹à¤¡ (Bulk CSV Upload)", "âž• à¤¨à¤¯à¤¾ à¤›à¤¾à¤¤à¥à¤° à¤®à¥ˆà¤¨à¥à¤…à¤² à¤«à¥‰à¤°à¥à¤® (Manual Form Entry)"])
            if entry_method == "ðŸ“ CSV à¤«à¤¼à¤¾à¤‡à¤² à¤¬à¤²à¥à¤• à¤…à¤ªà¤²à¥‹à¤¡ (Bulk CSV Upload)":
                uploaded_file = st.file_uploader("CSV à¤«à¤¼à¤¾à¤‡à¤² à¤šà¥à¤¨à¥‡à¤‚", type=["csv"])
                if uploaded_file is not None:
                    if st.button("Upload CSV Now", type="primary", use_container_width=True):
                        try:
                            uploaded_df = pd.read_csv(uploaded_file, dtype=str).fillna("")
                            for col in DEFAULT_COLUMNS:
                                if col not in uploaded_df.columns: uploaded_df[col] = ""
                            cleaned_uploaded_df = uploaded_df[DEFAULT_COLUMNS].copy()
                            updated_df = pd.concat([load_live_data(), cleaned_uploaded_df], ignore_index=True)
                            save_live_data(updated_df)
                            st.success("âœ… CSV à¤¡à¥‡à¤Ÿà¤¾ à¤¸à¤«à¤²à¤¤à¤¾à¤ªà¥‚à¤°à¥à¤µà¤• à¤®à¥à¤–à¥à¤¯ à¤¡à¥‡à¤Ÿà¤¾à¤¬à¥‡à¤¸ à¤®à¥‡à¤‚ à¤…à¤ªà¤²à¥‹à¤¡ à¤¹à¥‹ à¤—à¤¯à¤¾ à¤¹à¥ˆ!")
                        except Exception as e: st.error(f"à¤¤à¥à¤°à¥à¤Ÿà¤¿: {e}")
            elif entry_method == "âž• à¤¨à¤¯à¤¾ à¤›à¤¾à¤¤à¥à¤° à¤®à¥ˆà¤¨à¥à¤…à¤² à¤«à¥‰à¤°à¥à¤® (Manual Form Entry)":
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
                    if s_name.strip() == "": st.warning("Student Name à¤­à¤°à¤¨à¤¾ à¤…à¤¨à¤¿à¤µà¤¾à¤°à¥à¤¯ à¤¹à¥ˆà¥¤")
                    else:
                        new_row = {c: "" for c in DEFAULT_COLUMNS}
                        new_row.update({"Admission Year": admission_year, "Admission Session": admission_session, "Eligibility Name": eligibility_name, "Admission Application Number": admission_app_no, "Admission Date": admission_date, "Unique ID": unique_id, "Roll No.": roll_no, "Application Enrollment No.": app_enroll_no, "Enrollment No.": enrollment_no, "Student Name": s_name, "Father Name": f_name, "Mother Name": m_name, "Date of Birth": dob, "Category": category, "Subject Code": subject_code, "Subject": subject, "Duration": duration, "Mobile Number": mobile, "Email ID": email, "Address": address, "Status": status_input})
                        updated_df = pd.concat([load_live_data(), pd.DataFrame([new_row])], ignore_index=True)
                        save_live_data(updated_df)
                        st.success("âœ… à¤¨à¤¯à¤¾ à¤›à¤¾à¤¤à¥à¤° à¤°à¤¿à¤•à¥‰à¤°à¥à¤¡ à¤¸à¥à¤°à¤•à¥à¤·à¤¿à¤¤ à¤¸à¥‡à¤µ à¤¹à¥‹ à¤—à¤¯à¤¾ à¤¹à¥ˆ!")

        # ----------------------------------------------------------------------
        # P1: PANEL ENTRY MODULE
        # ----------------------------------------------------------------------
        if current_panel_id == "P1":
            st.header(f"ðŸ“ {get_panel_title('P1')} (Student Data Onboarding)")
            entry_method = st.selectbox("âš™ï¸ à¤¡à¥‡à¤Ÿà¤¾ à¤à¤‚à¤Ÿà¥à¤°à¥€ à¤•à¤¾ à¤®à¤¾à¤§à¥à¤¯à¤® à¤šà¥à¤¨à¥‡à¤‚:", options=["ðŸ“ CSV à¤«à¤¼à¤¾à¤‡à¤² à¤¬à¤²à¥à¤• à¤…à¤ªà¤²à¥‹à¤¡ (Bulk CSV Upload)", "âž• à¤¨à¤¯à¤¾ à¤›à¤¾à¤¤à¥à¤° à¤®à¥ˆà¤¨à¥à¤…à¤² à¤«à¥‰à¤°à¥à¤® (Manual Form Entry)"])
            if entry_method == "ðŸ“ CSV à¤«à¤¼à¤¾à¤‡à¤² à¤¬à¤²à¥à¤• à¤…à¤ªà¤²à¥‹à¤¡ (Bulk CSV Upload)":
                uploaded_file = st.file_uploader("CSV à¤«à¤¼à¤¾à¤‡à¤² à¤šà¥à¤¨à¥‡à¤‚", type=["csv"])
                if uploaded_file is not None:
                    if st.button("Upload CSV Now", type="primary", use_container_width=True):
                        try:
                            uploaded_df = pd.read_csv(uploaded_file, dtype=str).fillna("")
                            for col in DEFAULT_COLUMNS:
                                if col not in uploaded_df.columns: uploaded_df[col] = ""
                            cleaned_uploaded_df = uploaded_df[DEFAULT_COLUMNS].copy()
                            updated_df = pd.concat([load_live_data(), cleaned_uploaded_df], ignore_index=True)
                            save_live_data(updated_df)
                            st.success("âœ… CSV à¤¡à¥‡à¤Ÿà¤¾ à¤¸à¤«à¤²à¤¤à¤¾à¤ªà¥‚à¤°à¥à¤µà¤• à¤®à¥à¤–à¥à¤¯ à¤¡à¥‡à¤Ÿà¤¾à¤¬à¥‡à¤¸ à¤®à¥‡à¤‚ à¤…à¤ªà¤²à¥‹à¤¡ à¤¹à¥‹ à¤—à¤¯à¤¾ à¤¹à¥ˆ!")
                        except Exception as e: st.error(f"à¤¤à¥à¤°à¥à¤Ÿà¤¿: {e}")
            elif entry_method == "âž• à¤¨à¤¯à¤¾ à¤›à¤¾à¤¤à¥à¤° à¤®à¥ˆà¤¨à¥à¤…à¤² à¤«à¥‰à¤°à¥à¤® (Manual Form Entry)":
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
                    if s_name.strip() == "": st.warning("Student Name à¤­à¤°à¤¨à¤¾ à¤…à¤¨à¤¿à¤µà¤¾à¤°à¥à¤¯ à¤¹à¥ˆà¥¤")
                    else:
                        new_row = {c: "" for c in DEFAULT_COLUMNS}
                        new_row.update({"Admission Year": admission_year, "Admission Session": admission_session, "Eligibility Name": eligibility_name, "Admission Application Number": admission_app_no, "Admission Date": admission_date, "Unique ID": unique_id, "Roll No.": roll_no, "Application Enrollment No.": app_enroll_no, "Enrollment No.": enrollment_no, "Student Name": s_name, "Father Name": f_name, "Mother Name": m_name, "Date of Birth": dob, "Category": category, "Subject Code": subject_code, "Subject": subject, "Duration": duration, "Mobile Number": mobile, "Email ID": email, "Address": address, "Status": status_input})
                        updated_df = pd.concat([load_live_data(), pd.DataFrame([new_row])], ignore_index=True)
                        save_live_data(updated_df)
                        st.success("âœ… à¤¨à¤¯à¤¾ à¤›à¤¾à¤¤à¥à¤° à¤°à¤¿à¤•à¥‰à¤°à¥à¤¡ à¤¸à¥à¤°à¤•à¥à¤·à¤¿à¤¤ à¤¸à¥‡à¤µ à¤¹à¥‹ à¤—à¤¯à¤¾ à¤¹à¥ˆ!")

        # ----------------------------------------------------------------------
        # P2: PANEL ADMISSION MODULE
        # ----------------------------------------------------------------------
        elif current_panel_id == "P2":
            st.header(f"ðŸŽ“ {get_panel_title('P2')} (Admission Control & Verification)")
            if live_db.empty: st.warning("âš ï¸ à¤¡à¥‡à¤Ÿà¤¾à¤¬à¥‡à¤¸ à¤µà¤°à¥à¤¤à¤®à¤¾à¤¨ à¤®à¥‡à¤‚ à¤–à¤¾à¤²à¥€ à¤¹à¥ˆà¥¤")
            else:
                col_f1, col_f2, col_f3 = st.columns(3)
                with col_f1: selected_year = st.selectbox("Admission Year à¤šà¥à¤¨à¥‡à¤‚:", ["All"] + sorted(list(set(live_db["Admission Year"].dropna().astype(str)))))
                with col_f2: selected_session = st.selectbox("Admission Session à¤šà¥à¤¨à¥‡à¤‚:", ["All"] + sorted(list(set(live_db["Admission Session"].dropna().astype(str)))))
                with col_f3: selected_status = st.selectbox("Current Status à¤šà¥à¤¨à¥‡à¤‚:", ["All"] + sorted(list(set(live_db["Status"].dropna().astype(str)))))
                filtered_admission = live_db.copy()
                if selected_year != "All": filtered_admission = filtered_admission[filtered_admission["Admission Year"] == selected_year]
                if selected_session != "All": filtered_admission = filtered_admission[filtered_admission["Admission Session"] == selected_session]
                if selected_status != "All": filtered_admission = filtered_admission[filtered_admission["Status"] == selected_status]
                
                admission_cols = ["Admission Application Number", "Admission Year", "Admission Session", "Student Name", "Father Name", "Admission Date", "Status", "Unique ID"]
                display_cols = [c for c in admission_cols if c in filtered_admission.columns]
                render_df = filtered_admission[display_cols].copy()
                render_df.insert(0, "S.No.", range(1, len(render_df) + 1))
                edited_admission_df = st.data_editor(render_df, use_container_width=True, disabled=["S.No.", "Student Name", "Father Name"], key="admission_live_editor", hide_index=True)
                if st.button("Save & Sync Admission Changes", type="primary", use_container_width=True):
                    clean_edited = edited_admission_df.drop(columns=["S.No."])
                    for _, row_edit in clean_edited.iterrows():
                        idx_matches = live_db[live_db["Admission Application Number"] == row_edit["Admission Application Number"]].index
                        if not idx_matches.empty:
                            for match_idx in idx_matches:
                                for c in clean_edited.columns: live_db.at[match_idx, c] = row_edit[c]
                    save_live_data(live_db)
                    st.success("âœ… à¤à¤¡à¤®à¤¿à¤¶à¤¨ à¤¡à¥‡à¤Ÿà¤¾à¤¬à¥‡à¤¸ à¤¸à¤«à¤²à¤¤à¤¾à¤ªà¥‚à¤°à¥à¤µà¤• à¤¸à¤¿à¤‚à¤• à¤¹à¥‹ à¤—à¤¯à¤¾ à¤¹à¥ˆ!")

        # ----------------------------------------------------------------------
        # P3: PANEL ENROLLMENT MODULE
        # ----------------------------------------------------------------------
        elif current_panel_id == "P3":
            st.header(f"ðŸ“‘ {get_panel_title('P3')} (University Enrollment Manager)")
            if live_db.empty: st.warning("âš ï¸ à¤¡à¥‡à¤Ÿà¤¾à¤¬à¥‡à¤¸ à¤µà¤°à¥à¤¤à¤®à¤¾à¤¨ à¤®à¥‡à¤‚ à¤–à¤¾à¤²à¥€ à¤¹à¥ˆà¥¤")
            else:
                selected_subject = st.selectbox("Subject (à¤µà¤¿à¤·à¤¯) à¤šà¥à¤¨à¥‡à¤‚:", ["All"] + sorted(list(set(live_db["Subject"].dropna().astype(str)))))
                filtered_enrollment = live_db.copy()
                if selected_subject != "All": filtered_enrollment = filtered_enrollment[filtered_enrollment["Subject"] == selected_subject]
                enrollment_display_cols = ["Admission Application Number", "Student Name", "Father Name", "Subject", "Application Enrollment No.", "Enrollment No."]
                render_df = filtered_enrollment[enrollment_display_cols].copy()
                render_df.insert(0, "S.No.", range(1, len(render_df) + 1))
                edited_enrollment_df = st.data_editor(render_df, use_container_width=True, disabled=["S.No.", "Admission Application Number", "Student Name", "Father Name", "Subject"], key="enrollment_live_editor", hide_index=True)
                if st.button("Save & Sync Enrollment Numbers", type="primary", use_container_width=True):
                    clean_edited = edited_enrollment_df.drop(columns=["S.No."])
                    for _, row_edit in clean_edited.iterrows():
                        idx_matches = live_db[live_db["Admission Application Number"] == row_edit["Admission Application Number"]].index
                        if not idx_matches.empty:
                            for match_idx in idx_matches:
                                live_db.at[match_idx, "Application Enrollment No."] = row_edit["Application Enrollment No."]
                                live_db.at[match_idx, "Enrollment No."] = row_edit["Enrollment No."]
                    save_live_data(live_db)
                    st.success("âœ… à¤µà¤¿à¤¶à¥à¤µà¤µà¤¿à¤¦à¥à¤¯à¤¾à¤²à¤¯ à¤¨à¤¾à¤®à¤¾à¤‚à¤•à¤¨ à¤¨à¤‚à¤¬à¤° à¤¸à¤«à¤²à¤¤à¤¾à¤ªà¥‚à¤°à¥à¤µà¤• à¤…à¤ªà¤¡à¥‡à¤Ÿ à¤¹à¥‹ à¤—à¤¯à¤¾ à¤¹à¥ˆ!")

                # ----------------------------------------------------------------------
        # P4: PANEL SCHOLARSHIP MODULE
        # ----------------------------------------------------------------------
        elif current_panel_id == "P4":
            st.header(f"ðŸ’° {get_panel_title('P4')} (Portal & Category Matrix Control)")
            if "Scholarship Status" not in live_db.columns: 
                live_db["Scholarship Status"] = "Not Applied"
            
            if live_db.empty:
                st.warning("âš ï¸ à¤¡à¥‡à¤Ÿà¤¾à¤¬à¥‡à¤¸ à¤µà¤°à¥à¤¤à¤®à¤¾à¤¨ à¤®à¥‡à¤‚ à¤–à¤¾à¤²à¥€ à¤¹à¥ˆà¥¤ à¤•à¥ƒà¤ªà¤¯à¤¾ à¤ªà¤¹à¤²à¥‡ Panel 1 (Entry) à¤¸à¥‡ à¤›à¤¾à¤¤à¥à¤° à¤²à¥‹à¤¡ à¤•à¤°à¥‡à¤‚à¥¤")
            else:
                selected_category = st.selectbox("Category (à¤µà¤°à¥à¤—) à¤šà¥à¤¨à¥‡à¤‚:", ["All"] + sorted(list(set(live_db["Category"].dropna().astype(str)))))
                filtered_scholarship = live_db.copy()
                if selected_category != "All": 
                    filtered_scholarship = filtered_scholarship[filtered_scholarship["Category"] == selected_category]
                
                render_df = filtered_scholarship[["Admission Application Number", "Unique ID", "Student Name", "Category", "Scholarship Status"]].copy()
                render_df.insert(0, "S.No.", range(1, len(render_df) + 1))
                
                edited_scholarship_df = st.data_editor(
                    render_df, 
                    use_container_width=True, 
                    disabled=["S.No.", "Admission Application Number", "Unique ID", "Student Name", "Category"], 
                    column_config={"Scholarship Status": st.column_config.SelectboxColumn("Scholarship Status", options=["Not Applied", "Applied", "Sanctioned", "Disbursed", "Rejected"])}, 
                    key="scholarship_live_editor", 
                    hide_index=True
                )
                if st.button("Save & Sync Scholarship Matrix", type="primary", use_container_width=True):
                    for _, row_edit in edited_scholarship_df.drop(columns=["S.No."]).iterrows():
                        idx_matches = live_db[live_db["Admission Application Number"] == row_edit["Admission Application Number"]].index
                        if not idx_matches.empty:
                            for match_idx in idx_matches:
                                live_db.at[match_idx, "Scholarship Status"] = row_edit["Scholarship Status"]
                    save_live_data(live_db)
                    st.success("âœ… à¤›à¤¾à¤¤à¥à¤°à¤µà¥ƒà¤¤à¥à¤¤à¤¿ à¤®à¥ˆà¤Ÿà¥à¤°à¤¿à¤•à¥à¤¸ à¤¸à¤«à¤²à¤¤à¤¾à¤ªà¥‚à¤°à¥à¤µà¤• à¤…à¤ªà¤¡à¥‡à¤Ÿ à¤¹à¥‹ à¤—à¤¯à¤¾ à¤¹à¥ˆ!")
                    st.rerun()

        # ----------------------------------------------------------------------
        # P5: PANEL RESULT MODULE
        # ----------------------------------------------------------------------
        elif current_panel_id == "P5":
            st.header(f"ðŸ“Š {get_panel_title('P5')} (Tabulation Register & Exam Controller)")
            for f in ["Marks Obtained", "Result Status", "Exam Remarks"]:
                if f not in live_db.columns: live_db[f] = ""
            
            if live_db.empty:
                st.warning("âš ï¸ à¤¡à¥‡à¤Ÿà¤¾à¤¬à¥‡à¤¸ à¤µà¤°à¥à¤¤à¤®à¤¾à¤¨ à¤®à¥‡à¤‚ à¤–à¤¾à¤²à¥€ à¤¹à¥ˆà¥¤")
            else:
                selected_sub = st.selectbox("Subject à¤«à¤¼à¤¿à¤²à¥à¤Ÿà¤°:", ["All"] + sorted(list(set(live_db["Subject"].dropna().astype(str)))))
                filtered_res = live_db.copy()
                if selected_sub != "All": 
                    filtered_res = filtered_res[filtered_res["Subject"] == selected_sub]
                
                render_df = filtered_res[["Admission Application Number", "Roll No.", "Enrollment No.", "Student Name", "Subject", "Marks Obtained", "Result Status", "Exam Remarks"]].copy()
                render_df.insert(0, "S.No.", range(1, len(render_df) + 1))
                
                edited_res = st.data_editor(
                    render_df, 
                    use_container_width=True, 
                    disabled=["S.No.", "Admission Application Number", "Roll No.", "Enrollment No.", "Student Name", "Subject"], 
                    column_config={"Result Status": st.column_config.SelectboxColumn("Result Status", options=["Pass", "Fail", "ATKT", "Withheld", "Absent"])}, 
                    key="result_live_editor", 
                    hide_index=True
                )
                if st.button("Save & Sync Tabulation Register", type="primary", use_container_width=True):
                    for _, r_edit in edited_res.drop(columns=["S.No."]).iterrows():
                        idx_matches = live_db[live_db["Admission Application Number"] == r_edit["Admission Application Number"]].index
                        if not idx_matches.empty:
                            for match_idx in idx_matches:
                                for c in ["Marks Obtained", "Result Status", "Exam Remarks"]: 
                                    live_db.at[match_idx, c] = r_edit[c]
                    save_live_data(live_db)
                    st.success("âœ… à¤ªà¤°à¥€à¤•à¥à¤·à¤¾ à¤ªà¤°à¤¿à¤£à¤¾à¤® à¤ªà¤‚à¤œà¥€ à¤¸à¤«à¤²à¤¤à¤¾à¤ªà¥‚à¤°à¥à¤µà¤• à¤¸à¤¿à¤‚à¤• à¤¹à¥‹ à¤—à¤ˆ à¤¹à¥ˆ!")
                    st.rerun()

        # ----------------------------------------------------------------------
        # P6: PANEL PROMOTION MODULE
        # ----------------------------------------------------------------------
        elif current_panel_id == "P6":
            st.header(f"ðŸ“ˆ {get_panel_title('P6')} (Academic Year Batch Progression Control)")
            if "Promotion Status" not in live_db.columns: 
                live_db["Promotion Status"] = "Eligible"
            
            if live_db.empty:
                st.warning("âš ï¸ à¤¡à¥‡à¤Ÿà¤¾à¤¬à¥‡à¤¸ à¤µà¤°à¥à¤¤à¤®à¤¾à¤¨ à¤®à¥‡à¤‚ à¤–à¤¾à¤²à¥€ à¤¹à¥ˆà¥¤")
            else:
                render_df = live_db[["Admission Application Number", "Roll No.", "Student Name", "Current Year", "Status", "Promotion Status"]].copy()
                render_df.insert(0, "S.No.", range(1, len(render_df) + 1))
                
                edited_promo = st.data_editor(
                    render_df, 
                    use_container_width=True, 
                    disabled=["S.No.", "Admission Application Number", "Roll No.", "Student Name", "Current Year"], 
                    column_config={"Status": st.column_config.SelectboxColumn("Status", options=["Regular", "EX-STUDENT", "Pass", "Pending"]), "Promotion Status": st.column_config.SelectboxColumn("Promotion Status", options=["Eligible", "Promoted", "Detained (Year Back)", "Course Completed"])}, 
                    key="promotion_live_editor", 
                    hide_index=True
                )
                if st.button("Save & Sync Promotion Register", type="primary", use_container_width=True):
                    for _, r_edit in edited_promo.drop(columns=["S.No."]).iterrows():
                        idx_matches = live_db[live_db["Admission Application Number"] == r_edit["Admission Application Number"]].index
                        if not idx_matches.empty:
                            for match_idx in idx_matches:
                                live_db.at[match_idx, "Status"] = r_edit["Status"]
                                live_db.at[match_idx, "Promotion Status"] = r_edit["Promotion Status"]
                    save_live_data(live_db)
                    st.success("âœ… à¤›à¤¾à¤¤à¥à¤° à¤¬à¥ˆà¤š à¤ªà¥à¤°à¤®à¥‹à¤¶à¤¨ à¤ªà¤‚à¤œà¥€ à¤¸à¤«à¤²à¤¤à¤¾à¤ªà¥‚à¤°à¥à¤µà¤• à¤…à¤ªà¤¡à¥‡à¤Ÿ à¤¹à¥‹ à¤—à¤ˆ à¤¹à¥ˆ!")
                    st.rerun()

        # ----------------------------------------------------------------------
        # P7: PANEL FOIL SHEET GENERATOR MODULE
        # ----------------------------------------------------------------------
        elif current_panel_id == "P7":
            st.header(f"ðŸ–¨ï¸ {get_panel_title('P7')} (University CCE Foil Sheet Generator)")
            college_name = "GOVT. K.R.G. POST-GRADUATE AUTONOMOUS COLLEGE, GWALIOR (M.P.)"
            
            if live_db.empty:
                st.warning("âš ï¸ à¤¡à¥‡à¤Ÿà¤¾à¤¬à¥‡à¤¸ à¤µà¤°à¥à¤¤à¤®à¤¾à¤¨ à¤®à¥‡à¤‚ à¤–à¤¾à¤²à¥€ à¤¹à¥ˆà¥¤")
            else:
                unique_subjects = sorted(list(set(live_db['Subject'].dropna().astype(str).str.strip())))
                selected_subject = st.selectbox("ðŸ“š Select Subject:", options=["All Subjects"] + [s for s in unique_subjects if s != ""], key="cce_sub")
                chosen_option = st.selectbox("ðŸ“† Select Semester / Year:", ["1 Semester", "2 Semester", "1 year", "2 year", "3 year", "4 year"])
                if st.button("Generate Foil Sheets Now", use_container_width=True, type="primary"):
                    st.session_state.cce_foil_generated = True
                if st.session_state.cce_foil_generated:
                    st.success("Foil Sheet Canvas Generated Below Ready for Verification.")

               # ----------------------------------------------------------------------
        # P8: PANEL CCE RECORD MODULE
        # ----------------------------------------------------------------------
        elif current_panel_id == "P8":
            st.header(f"ðŸ“‹ {get_panel_title('P8')} (Internal Assessment Marks Ledger)")
            for f in ["CCE Marks Obtained", "CCE Attendance Status"]:
                if f not in live_db.columns: live_db[f] = ""
            
            if live_db.empty:
                st.warning("âš ï¸ à¤¡à¥‡à¤Ÿà¤¾à¤¬à¥‡à¤¸ à¤µà¤°à¥à¤¤à¤®à¤¾à¤¨ à¤®à¥‡à¤‚ à¤–à¤¾à¤²à¥€ à¤¹à¥ˆà¥¤")
            else:
                render_df = live_db[["Admission Application Number", "Roll No.", "Student Name", "Subject", "CCE Marks Obtained", "CCE Attendance Status"]].copy()
                render_df.insert(0, "S.No.", range(1, len(render_df) + 1))
                
                edited_cce = st.data_editor(
                    render_df, 
                    use_container_width=True, 
                    disabled=["S.No.", "Admission Application Number", "Roll No.", "Student Name", "Subject"], 
                    column_config={"CCE Attendance Status": st.column_config.SelectboxColumn("CCE Attendance Status", options=["Present", "Absent", "Detained"])}, 
                    key="cce_record_live_editor", 
                    hide_index=True
                )
                if st.button("Save & Sync CCE Assessment Ledger", type="primary", use_container_width=True):
                    for _, r_edit in edited_cce.drop(columns=["S.No."]).iterrows():
                        idx_matches = live_db[live_db["Admission Application Number"] == r_edit["Admission Application Number"]].index
                        if not idx_matches.empty:
                            for match_idx in idx_matches:
                                live_db.at[match_idx, "CCE Marks Obtained"] = r_edit["CCE Marks Obtained"]
                                live_db.at[match_idx, "CCE Attendance Status"] = r_edit["CCE Attendance Status"]
                    save_live_data(live_db)
                    st.success("âœ… à¤¸à¥€à¤¸à¥€à¤ˆ à¤†à¤‚à¤¤à¤°à¤¿à¤• à¤®à¥‚à¤²à¥à¤¯à¤¾à¤‚à¤•à¤¨ à¤ªà¤‚à¤œà¥€ à¤¸à¤«à¤²à¤¤à¤¾à¤ªà¥‚à¤°à¥à¤µà¤• à¤¸à¥‡à¤µ à¤¹à¥‹ à¤—à¤ˆ à¤¹à¥ˆ!")
                    st.rerun()

        # ----------------------------------------------------------------------
        # P9 to P12: DYNAMIC EXTENSION LEDGERS
        # ----------------------------------------------------------------------
        elif current_panel_id in ["P9", "P10", "P11", "P12"]:
            st.header(f"ðŸ“Œ {get_panel_title(current_panel_id)} (Dynamic Extension Ledger Room)")
            p_status_col = f"{current_panel_id} Record Status"
            p_remark_col = f"{current_panel_id} Custom Remarks"
            for f in [p_status_col, p_remark_col]:
                if f not in live_db.columns: live_db[f] = ""
            
            if live_db.empty:
                st.warning("âš ï¸ à¤¡à¥‡à¤Ÿà¤¾à¤¬à¥‡à¤¸ à¤µà¤°à¥à¤¤à¤®à¤¾à¤¨ à¤®à¥‡à¤‚ à¤–à¤¾à¤²à¥€ à¤¹à¥ˆà¥¤")
            else:
                render_df = live_db[["Admission Application Number", "Roll No.", "Student Name", "Subject", p_status_col, p_remark_col]].copy()
                render_df.insert(0, "S.No.", range(1, len(render_df) + 1))
                
                edited_ext = st.data_editor(
                    render_df, 
                    use_container_width=True, 
                    disabled=["S.No.", "Admission Application Number", "Roll No.", "Student Name", "Subject"], 
                    column_config={p_status_col: st.column_config.SelectboxColumn("Status", options=["Verified", "Pending", "Approved", "On Hold"])}, 
                    key=f"{current_panel_id}_live_editor", 
                    hide_index=True
                )
                if st.button(f"Save & Sync {current_panel_id} Records", type="primary", use_container_width=True):
                    for _, r_edit in edited_ext.drop(columns=["S.No."]).iterrows():
                        idx_matches = live_db[live_db["Admission Application Number"] == r_edit["Admission Application Number"]].index
                        if not idx_matches.empty:
                            for match_idx in idx_matches:
                                live_db.at[match_idx, p_status_col] = r_edit[p_status_col]
                                live_db.at[match_idx, p_remark_col] = r_edit[p_remark_col]
                    save_live_data(live_db)
                    st.success(f"âœ… {get_panel_title(current_panel_id)} à¤•à¤¾ à¤°à¤¿à¤•à¥‰à¤°à¥à¤¡ à¤¸à¤«à¤²à¤¤à¤¾à¤ªà¥‚à¤°à¥à¤µà¤• à¤…à¤ªà¤¡à¥‡à¤Ÿ à¤¹à¥‹ à¤—à¤¯à¤¾ à¤¹à¥ˆ!")
                    st.rerun()

        # ----------------------------------------------------------------------
        # P13: MERGE PANEL MODULE
        # ----------------------------------------------------------------------
        elif current_panel_id == "P13":
            st.header(f"ðŸ”€ {get_panel_title('P13')} (Database Smart Merge Panel)")
            uploaded_merge_file = st.file_uploader("à¤®à¤°à¥à¤œ à¤•à¤°à¤¨à¥‡ à¤•à¥‡ à¤²à¤¿à¤ à¤¨à¤ˆ CSV à¤«à¤¼à¤¾à¤‡à¤² à¤šà¥à¤¨à¥‡à¤‚:", type=["csv"])
            if uploaded_merge_file is not None:
                incoming_df = pd.read_csv(uploaded_merge_file, dtype=str).fillna("")
                st.dataframe(incoming_df.head(3), use_container_width=True)
                merge_key = st.selectbox("ðŸ”‘ Unique Key à¤šà¥à¤¨à¥‡à¤‚:", options=["Admission Application Number", "Unique ID", "Roll No."])
                if st.button("Execute Smart Database Merge Now", type="primary", use_container_width=True):
                    st.success("âœ… à¤¡à¥‡à¤Ÿà¤¾à¤¬à¥‡à¤¸ à¤¸à¤«à¤²à¤¤à¤¾à¤ªà¥‚à¤°à¥à¤µà¤• à¤®à¤°à¥à¤œ à¤¹à¥‹ à¤—à¤¯à¤¾!")

                # ----------------------------------------------------------------------
        # P14: PANEL VIEWER (INTEGRATED INDEX SYSTEM)
        # ----------------------------------------------------------------------
        elif current_panel_id == "P14":
            st.header(f"ðŸ‘ï¸ {get_panel_title('P14')} (Multi-Panel Inspection Window)")

            panel_options_list = {
                "Panel 2: Panal admission": ["Admission Application Number", "Student Name", "Admission Year", "Admission Session", "Admission Date", "Status"],
                "Panel 3: Panal enrollment": ["Admission Application Number", "Student Name", "Subject", "Application Enrollment No.", "Enrollment No."],
                "Panel 4: Panal scholarship": ["Admission Application Number", "Student Name", "Category", "Scholarship Status"],
                "Panel 5: Panal result": ["Roll No.", "Enrollment No.", "Student Name", "Subject", "Marks Obtained", "Result Status", "Exam Remarks"],
                "Panel 6: Panal promotion": ["Roll No.", "Student Name", "Current Year", "Status", "Promotion Status"],
                "Panel 7: Panal foil": ["Roll No.", "Student Name", "Subject Code", "Subject", "Status"],
                "Panel 8: Panal cce record": ["Admission Application Number", "Roll No.", "Student Name", "Subject", "CCE Marks Obtained", "CCE Attendance Status"],
                "Panel 9: Panal P9 (Extension 1)": ["Admission Application Number", "Student Name", "P9 Record Status", "P9 Custom Remarks"],
                "Panel 10: Panal P10 (Extension 2)": ["Admission Application Number", "Student Name", "P10 Record Status", "P10 Custom Remarks"],
                "Panel 11: Panal P11 (Extension 3)": ["Admission Application Number", "Student Name", "P11 Record Status", "P11 Custom Remarks"],
                "Panel 12: Panal P12 (Extension 4)": ["Admission Application Number", "Student Name", "P12 Record Status", "P12 Custom Remarks"],
                "Panel 13: Database Smart Merge": ["Admission Year", "Admission Application Number", "Unique ID", "Roll No.", "Enrollment No.", "Student Name"]
            }

            st.subheader("ðŸ“‚ Select Panel Dashboard View")
            selected_panel_view = st.selectbox(
                "à¤¨à¤¿à¤°à¥€à¤•à¥à¤·à¤£ à¤•à¤°à¤¨à¥‡ à¤•à¥‡ à¤²à¤¿à¤ à¤ªà¥ˆà¤¨à¤² à¤¸à¥‚à¤šà¥€ (P2 à¤¸à¥‡ P13) à¤šà¥à¤¨à¥‡à¤‚:",
                options=list(panel_options_list.keys())
            )

            target_columns = panel_options_list[selected_panel_view]

            for c_col in target_columns:
                if c_col not in live_db.columns:
                    live_db[c_col] = ""

            st.markdown(f"### ðŸ“‹ {selected_panel_view} - Records Table")
            
            col_search1, col_search2 = st.columns(2)
            with col_search1:
                search_target_col = st.selectbox("à¤–à¥‹à¤œà¤¨à¥‡ à¤•à¥‡ à¤²à¤¿à¤ à¤«à¤¼à¥€à¤²à¥à¤¡ à¤šà¥à¤¨à¥‡à¤‚:", options=target_columns, key="p14_search_col")
            with col_search2:
                search_query_text = st.text_input(f"'{search_target_col}' à¤®à¥‡à¤‚ à¤ªà¥à¤°à¤µà¤¿à¤·à¥à¤Ÿà¤¿ à¤–à¥‹à¤œà¥‡à¤‚:", key="p14_query_val")

            view_filtered_df = live_db.copy()
            if search_query_text.strip() != "":
                view_filtered_df = view_filtered_df[
                    view_filtered_df[search_target_col].astype(str).str.contains(search_query_text, case=False, na=False)
                ]

            st.write(f"à¤µà¤°à¥à¤¤à¤®à¤¾à¤¨ à¤—à¥à¤°à¤¿à¤¡ à¤®à¥‡à¤‚ à¤•à¥à¤² à¤‰à¤ªà¤²à¤¬à¥à¤§ à¤›à¤¾à¤¤à¥à¤° à¤°à¤¿à¤•à¥‰à¤°à¥à¤¡ à¤¸à¤‚à¤–à¥à¤¯à¤¾: **{len(view_filtered_df)}**")

            final_render_cols = [col for col in target_columns if col in view_filtered_df.columns]
            
            if not view_filtered_df.empty:
                display_ready_df = view_filtered_df[final_render_cols].copy()
                display_ready_df.insert(0, "S.No.", range(1, len(display_ready_df) + 1))
                
                st.dataframe(
                    display_ready_df,
                    use_container_width=True,
                    hide_index=True
                )
                
                st.download_button(
                    label=f"ðŸ“¥ Download Report (CSV)",
                    data=view_filtered_df[final_render_cols].to_csv(index=False).encode('utf-8'),
                    file_name=f"{selected_panel_view.replace(' ', '_').lower()}_report.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                st.warning("ðŸ” à¤¨à¤¿à¤°à¥à¤¦à¤¿à¤·à¥à¤Ÿ à¤–à¥‹à¤œ à¤ªà¥à¤°à¤µà¤¿à¤·à¥à¤Ÿà¤¿ à¤•à¥‡ à¤†à¤§à¤¾à¤° à¤ªà¤° à¤•à¥‹à¤ˆ à¤°à¤¿à¤•à¥‰à¤°à¥à¤¡ à¤¨à¤¹à¥€à¤‚ à¤®à¤¿à¤²à¤¾à¥¤")

                # ----------------------------------------------------------------------
        # P15: PANEL ADMIN (15 PANELS SUPREME ENGINE & SEARCH FIX)
        # ----------------------------------------------------------------------
        elif current_panel_id == "P15":
            st.header(f"ðŸ› ï¸ {get_panel_title('P15')} (Full Super-Admin Control Command)")
            
            st.subheader("âœï¸ Dynamic 15 Panels Name & Label Customizer")
            with st.expander("15 à¤ªà¥ˆà¤¨à¤²à¥à¤¸ à¤•à¥‡ à¤¨à¤¾à¤® (App Titles) à¤à¤¡à¤¿à¤Ÿ à¤•à¤°à¤¨à¥‡ à¤•à¥‡ à¤²à¤¿à¤ à¤¯à¤¹à¤¾à¤ à¤•à¥à¤²à¤¿à¤• à¤•à¤°à¥‡à¤‚", expanded=False):
                with st.form(key="panel_rename_matrix_form"):
                    p_setup1, p_setup2 = st.columns(2)
                    temp_panel_mappings = {}
                    for idx, p_key in enumerate(DEFAULT_PANELS.keys()):
                        current_panel_name = st.session_state.panel_names.get(p_key, DEFAULT_PANELS[p_key])
                        if idx % 2 == 0:
                            with p_setup1: temp_panel_mappings[p_key] = st.text_input(f"Name for {p_key}:", value=current_panel_name, key=f"p_ren_{p_key}")
                        else:
                            with p_setup2: temp_panel_mappings[p_key] = st.text_input(f"Name for {p_key}:", value=current_panel_name, key=f"p_ren_{p_key}")
                    if st.form_submit_button("Save All 15 Panel Titles Permanently", type="primary"):
                        st.session_state.panel_names = temp_panel_mappings
                        save_panel_names(temp_panel_mappings)
                        st.success("âœ… à¤¸à¤­à¥€ 15 à¤ªà¥ˆà¤¨à¤²à¥à¤¸ à¤•à¥‡ à¤¨à¤¾à¤® à¤…à¤ªà¤¡à¥‡à¤Ÿ à¤¹à¥‹ à¤—à¤ à¤¹à¥ˆà¤‚!")
                        st.rerun()

            st.subheader("ðŸ›¡ï¸ Global 15 Panels Visibility Toggle Switch Board")
            # === à¤ à¥€à¤• à¤‰à¤¸à¥€ à¤–à¤¾à¤²à¥€ à¤œà¤—à¤¹ à¤ªà¤° à¤‡à¤¸ à¤¨à¤ à¤•à¥‹à¤¡ à¤•à¥‹ à¤ªà¥‡à¤¸à¥à¤Ÿ à¤•à¤°à¥‡à¤‚ ===
            vis_tabs = st.tabs(["ðŸ”’ Panels P1 - P7 Control", "ðŸ”’ Panels P8 - P15 Control"])
            
            # à¤ªà¤¹à¤²à¥‡ à¤Ÿà¥ˆà¤¬ (Index 0) à¤•à¥‡ à¤²à¤¿à¤ à¤µà¤¿à¤œà¤¼à¤¿à¤¬à¤¿à¤²à¤¿à¤Ÿà¥€ à¤¬à¤Ÿà¤¨à¥à¤¸
            with vis_tabs[0]:
                c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
                for i, p_key in enumerate(["P1", "P2", "P3", "P4", "P5", "P6", "P7"]):
                    with [c1, c2, c3, c4, c5, c6, c7][i]:
                        status_lbl = "ðŸ™ˆ Hidden" if st.session_state[f"hide_panel_{p_key}"] else "ðŸ‘€ Active"
                        if st.button(f"{p_key}\n({status_lbl})", use_container_width=True, key=f"btn_v_{p_key}"):
                            st.session_state[f"hide_panel_{p_key}"] = not st.session_state[f"hide_panel_{p_key}"]
                            st.rerun()
                            
            # à¤¦à¥‚à¤¸à¤°à¥‡ à¤Ÿà¥ˆà¤¬ (Index 1) à¤•à¥‡ à¤²à¤¿à¤ à¤µà¤¿à¤œà¤¼à¤¿à¤¬à¤¿à¤²à¤¿à¤Ÿà¥€ à¤¬à¤Ÿà¤¨à¥à¤¸
            with vis_tabs[1]:
                c8, c9, c10, c11, c12, c13, c14, c15 = st.columns(8)
                for i, p_key in enumerate(["P8", "P9", "P10", "P11", "P12", "P13", "P14", "P15"]):
                    with [c8, c9, c10, c11, c12, c13, c14, c15][i]:
                        status_lbl = "ðŸ™ˆ Hidden" if st.session_state[f"hide_panel_{p_key}"] else "ðŸ‘€ Active"
                        if st.button(f"{p_key}\n({status_lbl})", use_container_width=True, key=f"btn_v_{p_key}"):
                            st.session_state[f"hide_panel_{p_key}"] = not st.session_state[f"hide_panel_{p_key}"]
                            st.rerun()

            st.markdown("---")
            st.subheader("ðŸ“Š Master Database List View & Advanced Operational Controls")
            
            col_ctrl1, col_ctrl2, col_ctrl3 = st.columns(3)
            with col_ctrl1:
                lbl_edit = "ðŸ‘€ à¤à¤¡à¤¿à¤Ÿ à¤Ÿà¥‡à¤•à¥à¤¸à¥à¤Ÿ FUNCTION: active" if st.session_state.admin_unhide_edit else "ðŸ™ˆ à¤à¤¡à¤¿à¤Ÿ à¤Ÿà¥‡à¤•à¥à¤¸à¥à¤Ÿ FUNCTION: hidden"
                if st.button(lbl_edit, use_container_width=True):
                    st.session_state.admin_unhide_edit = not st.session_state.admin_unhide_edit
                    st.rerun()
            with col_ctrl2:
                lbl_move = "ðŸ‘€ à¤•à¥‰à¤²à¤® à¤®à¥‚à¤µ à¤¬à¤Ÿà¤¨à¥à¤¸: active" if st.session_state.admin_unhide_move else "ðŸ™ˆ à¤•à¥‰à¤²à¤® à¤®à¥‚à¤µ à¤¬à¤Ÿà¤¨à¥à¤¸: hidden"
                if st.button(lbl_move, use_container_width=True):
                    st.session_state.admin_unhide_move = not st.session_state.admin_unhide_move
                    st.rerun()
            with col_ctrl3:
                lock_label = "ðŸ”’ à¤²à¤¿à¤¸à¥à¤Ÿ à¤²à¥‰à¤• à¤•à¤°à¥‡à¤‚ (Locked)" if st.session_state.admin_lock_state else "ðŸ”“ à¤²à¤¿à¤¸à¥à¤Ÿ à¤…à¤¨à¤²à¥‰à¤• à¤•à¤°à¥‡à¤‚ (Editable)"
                if st.button(lock_label, use_container_width=True, type="primary" if not st.session_state.admin_lock_state else "secondary"):
                    st.session_state.admin_lock_state = not st.session_state.admin_lock_state
                    st.rerun()

            if st.session_state.admin_unhide_move and not st.session_state.admin_lock_state:
                st.info("ðŸ”€ à¤•à¥‰à¤²à¤® à¤•à¤¾ à¤•à¥à¤°à¤® à¤¬à¤¦à¤²à¤¨à¥‡ à¤•à¥‡ à¤²à¤¿à¤ à¤¸à¥‡à¤²à¥‡à¤•à¥à¤Ÿ à¤•à¤°à¥‡à¤‚:")
                target_col = st.selectbox("à¤®à¥‚à¤µ à¤•à¤°à¤¨à¥‡ à¤•à¥‡ à¤²à¤¿à¤ à¤•à¥‰à¤²à¤® à¤šà¥à¤¨à¥‡à¤‚:", options=st.session_state.admin_columns_order)
                c_left, c_right = st.columns(2)
                
                if c_left.button("â¬…ï¸ Shift Left", use_container_width=True):
                    idx = st.session_state.admin_columns_order.index(target_col)
                    if idx > 0:
                        st.session_state.admin_columns_order[idx], st.session_state.admin_columns_order[idx-1] = st.session_state.admin_columns_order[idx-1], st.session_state.admin_columns_order[idx]
                        st.rerun()
                        
                if c_right.button("âž¡ï¸ Shift Right", use_container_width=True):
                    idx = st.session_state.admin_columns_order.index(target_col)
                    if idx < len(st.session_state.admin_columns_order) - 1:
                        st.session_state.admin_columns_order[idx], st.session_state.admin_columns_order[idx+1] = st.session_state.admin_columns_order[idx+1], st.session_state.admin_columns_order[idx]
                        st.rerun()

            render_columns = [col for col in st.session_state.admin_columns_order if col in live_db.columns]
            ordered_db = live_db[render_columns].copy()
            ordered_db_display = ordered_db.rename(columns={c: get_display_name(c) for c in ordered_db.columns})
            ordered_db_display.insert(0, "S.No.", range(1, len(ordered_db_display) + 1))

            st.write(f"à¤¡à¥‡à¤Ÿà¤¾à¤¬à¥‡à¤¸ à¤®à¥‡à¤‚ à¤•à¥à¤² à¤²à¤¾à¤‡à¤µ à¤°à¤¿à¤•à¥‰à¤°à¥à¤¡ à¤¸à¤‚à¤–à¥à¤¯à¤¾: **{len(ordered_db_display)}**")

            if not st.session_state.admin_lock_state and st.session_state.admin_unhide_edit:
                st.warning("âš ï¸ à¤²à¤¾à¤‡à¤µ à¤¸à¤‚à¤ªà¤¾à¤¦à¤¨ (Live Editing Matrix Mode) à¤¸à¤•à¥à¤°à¤¿à¤¯ à¤¹à¥ˆà¥¤")
                edited_df = st.data_editor(ordered_db_display, use_container_width=True, disabled=["S.No."], num_rows="dynamic", key="admin_live_editor_grid", hide_index=True)
                
                if st.button("Save & Sync Matrix Changes", type="primary", use_container_width=True):
                    try:
                        clean_edited = edited_df.drop(columns=["S.No."])
                        reverse_mapping = {}
                        for orig_col in render_columns:
                            disp_name = get_display_name(orig_col)
                            reverse_mapping[disp_name] = orig_col
                        
                        synced_data = {col: [] for col in DEFAULT_COLUMNS}
                        for extra_col in live_db.columns:
                            if extra_col not in synced_data: synced_data[extra_col] = []

                        for _, row_edit in clean_edited.iterrows():
                            for display_name_key in clean_edited.columns:
                                internal_key = reverse_mapping.get(display_name_key, display_name_key)
                                if internal_key in synced_data:
                                    synced_data[internal_key].append(row_edit[display_name_key])
                        
                        max_len = max(len(lst) for lst in synced_data.values()) if synced_data.values() else 0
                        for k_key in synced_data.keys():
                            while len(synced_data[k_key]) < max_len: synced_data[k_key].append("")
                                
                        new_live_db = pd.DataFrame(synced_data)
                        save_live_data(new_live_db)
                        st.success("ðŸŽ‰ à¤¸à¤‚à¤ªà¥‚à¤°à¥à¤£ à¤®à¤¾à¤¸à¥à¤Ÿà¤° à¤¡à¥‡à¤Ÿà¤¾à¤¬à¥‡à¤¸ à¤¸à¤«à¤²à¤¤à¤¾à¤ªà¥‚à¤°à¥à¤µà¤• à¤¸à¤¿à¤‚à¤• à¤”à¤° à¤…à¤ªà¤¡à¥‡à¤Ÿ à¤•à¤° à¤¦à¤¿à¤¯à¤¾ à¤—à¤¯à¤¾ à¤¹à¥ˆ!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"à¤¡à¥‡à¤Ÿà¤¾ à¤¸à¤¿à¤‚à¤•à¥à¤°à¥‹à¤¨à¤¾à¤‡à¤œà¤¼à¥‡à¤¶à¤¨ à¤šà¤•à¥à¤° à¤®à¥‡à¤‚ à¤¤à¤•à¤¨à¥€à¤•à¥€ à¤¸à¤®à¤¸à¥à¤¯à¤¾ à¤†à¤ˆ: {e}")
            else:
                st.dataframe(ordered_db_display, use_container_width=True, hide_index=True)
