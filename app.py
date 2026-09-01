import streamlit as st
import pandas as pd
import os
import base64
import json

# पेज का लेआउट सेट करें
st.set_page_config(layout="wide", page_title="Permanent Shared Live Database")

# प्रिंट फ़ॉर्मेटिंग, लेआउट और नोटिस बोर्ड को व्यवस्थित करने के लिए सीएसएस (CSS)
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
    
    /* नोटिस बोर्ड स्टाइल */
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
            <h3>ॐ श्री गुरवे नमः</h3>
            <h1>Permanent Shared Live Database System</h1>
        </div>
    </div>
""", unsafe_allow_html=True)

DB_FILE = "shared_student_database.csv"
CRED_FILE = "user_credentials_v15.json"
MAP_FILE = "column_mapping_schema.json"
PANEL_NAME_FILE = "panel_names_schema.json"
NOTICE_FILE = "notice_board_schema.json"

# डिफ़ॉल्ट कॉलेज नोटिस 
DEFAULT_NOTICE = (
    "1. यह एक पूर्णतः सुरक्षित, लाइव क्लाउड स्टूडेंट डेटाबेस मैनेजमेंट सिस्टम है।\n"
    "2. डेटा प्रविष्टि, सुधार, स्कॉलरशिप वेरिफिकेशन या परीक्षा परिणाम अपडेट करने के लिए अधिकृत यूजर क्रेडेंशियल्स का उपयोग करें।\n"
    "3. बिना लॉगिन के डेटाबेस तक पहुँच पूर्णतः प्रतिबंधित है। किसी भी समस्या के लिए सुपर-एडमिन से संपर्क करें।"
)

# 🔒 आपके द्वारा कस्टमाइज़ की गई 15 पैनल्स की नई सूची और उनके क्रेडेंशियल्स
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
    "p12_login_view": {"password": "view12123", "role": "p12_role", "label": "🛠️ P12: Pre-Login View Configurator"},
    "p13_merge": {"password": "mrg13123", "role": "p13_role", "label": "🔀 P13: External Database Smart Merge"},
    "p14_viewer": {"password": "view14123", "role": "p14_role", "label": "👁️ P14: Multi-Panel Inspection Window"}
}

# 🛠️ आपके द्वारा प्रदान की गई नई नेविगेशन मैपिंग (P1 से P15)
DEFAULT_PANELS = {
    "P1": "Panal entry", 
    "P2": "Panal admission", 
    "P3": "Panal unique",
    "P4": "Panal roll", 
    "P5": "Panal enrollment", 
    "P6": "Panal scholarship",
    "P7": "Panal foil", 
    "P8": "Panal cce record", 
    "P9": "Panal promotion",
    "P10": "Panal result", 
    "P11": "notice board edit", 
    "P12": "login karne se phle jo view dikha hai use edit karne ka",
    "P13": "Panal merge", 
    "P14": "Panal viewer", 
    "P15": "Panel admin"
}

# 🎯 मास्टर कॉलम्स सूची
DEFAULT_COLUMNS = [
    "Admission Year", "Admission Session", "Eligibility Name", "Admission Application Number",
    "Admission Date", "Unique ID", "Roll No.", "Application Enrollment No.",
    "Enrollment No.", "Student Name", "Father Name", "Mother Name", "Date of Birth",
    "Category", "Subject Code", "Subject", "Duration", "Mobile Number", "Email ID", "Address", "Status",
    "Current Year"
]

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

for k in DEFAULT_PANELS.keys():
    if f"hide_panel_{k}" not in st.session_state: st.session_state[f"hide_panel_{k}"] = False

live_db = load_live_data()

def get_display_name(internal_col_name):
    return st.session_state.column_mappings.get(internal_col_name, internal_col_name)

def get_panel_title(panel_id):
    return st.session_state.panel_names.get(panel_id, DEFAULT_PANELS[panel_id])


# ==========================================================
# 🛑 लॉगिन से पहले का ब्लॉक (Complete Pre-Login Block)
# ==========================================================
if st.session_state.user_role is None:
    # सूचना पटल की पंक्तियों को तोड़कर HTML लिस्ट फॉर्मेट में रेंडर करना
    formatted_notice = "".join([f"<p>{line.strip()}</p>" for line in st.session_state.notice_text.split('\n') if line.strip()])
    
    st.markdown(f"""
        <div class="notice-board">
            <div class="notice-title">📢 कॉलेज सूचना पटल (Official Notice Board)</div>
            {formatted_notice}
        </div>
    """, unsafe_allow_html=True)
    
        # लॉगिन विंडो खोलने का बटन नियंत्रण
    if not st.session_state.show_login_form:
        if st.button("🔐 Click Here to Open Secure Login System", type="primary", use_container_width=True):
            st.session_state.show_login_form = True
            st.rerun()
            
    # लॉगिन फॉर्म एक्टिव होने पर रेंडर होने वाला ब्लॉक
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
            
        # इंटरफ़ेस एक्शन बटन्स (प्रवेश और बंद करें)
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
# Phase 2: Post Authorized Panel Systems (Complete Block)
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

    active_tabs_names = [f"{p} : {get_panel_title(p)}" for p in allowed_panels if not st.session_state[f"hide_panel_{p}"] or role == "full_admin"]
    
    if not active_tabs_names:
        st.warning("⚠️ वर्तमान में आपकी भूमिका के लिए कोई भी पैनल एक्टिव नहीं किया गया है।")
    else:
        selected_tab_ui = st.sidebar.radio("🧭 Navigate Active Modules:", options=active_tabs_names)
        current_panel_id = selected_tab_ui.split(" : ")[0]

        # ----------------------------------------------------------------------
        # P1: PANEL ENTRY MODULE
        # ----------------------------------------------------------------------
        if current_panel_id == "P1":
            st.header(f"📝 {get_panel_title('P1')} (Student Data Onboarding)")
            entry_method = st.selectbox("⚙️ डेटा एंट्री का माध्यम चुनें:", options=["📁 CSV फ़ाइल बल्क अपलोड (Bulk CSV Upload)", "➕ नया छात्र मैनुअल फॉर्म (Manual Form Entry)"])
            if entry_method == "📁 CSV फ़ाइल बल्क अपलोड (Bulk CSV Upload)":
                uploaded_file = st.file_uploader("CSV फ़ाइल चुनें", type=["csv"])
                if uploaded_file is not None:
                    if st.button("Upload CSV Now", type="primary", use_container_width=True):
                        try:
                            uploaded_df = pd.read_csv(uploaded_file, dtype=str).fillna("")
                            for col in DEFAULT_COLUMNS:
                                if col not in uploaded_df.columns: uploaded_df[col] = ""
                            cleaned_uploaded_df = uploaded_df[DEFAULT_COLUMNS].copy()
                            updated_df = pd.concat([load_live_data(), cleaned_uploaded_df], ignore_index=True)
                            save_live_data(updated_df)
                            st.success("✅ CSV डेटा सफलतापूर्वक मुख्य डेटाबेस में अपलोड हो गया है!")
                        except Exception as e: st.error(f"त्रुटि: {e}")
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
                    if s_name.strip() == "": st.warning("Student Name भरना अनिवार्य है।")
                    else:
                        new_row = {c: "" for c in DEFAULT_COLUMNS}
                        new_row.update({"Admission Year": admission_year, "Admission Session": admission_session, "Eligibility Name": eligibility_name, "Admission Application Number": admission_app_no, "Admission Date": admission_date, "Unique ID": unique_id, "Roll No.": roll_no, "Application Enrollment No.": app_enroll_no, "Enrollment No.": enrollment_no, "Student Name": s_name, "Father Name": f_name, "Mother Name": m_name, "Date of Birth": dob, "Category": category, "Subject Code": subject_code, "Subject": subject, "Duration": duration, "Mobile Number": mobile, "Email ID": email, "Address": address, "Status": status_input})
                        updated_df = pd.concat([load_live_data(), pd.DataFrame([new_row])], ignore_index=True)
                        save_live_data(updated_df)
                        st.success("✅ नया छात्र रिकॉर्ड सुरक्षित सेव हो गया है!")

                # ----------------------------------------------------------------------
        # P2: PANEL ADMISSION MODULE (Admission Control & Verification)
        # ----------------------------------------------------------------------
        elif current_panel_id == "P2":
            st.header(f"🎓 {get_panel_title('P2')} (Admission Control & Verification)")
            
            if live_db.empty: 
                st.warning("⚠️ डेटाबेस वर्तमान में खाली है। कृपया पहले Panel 1 (Entry) से छात्र लोड करें।")
            else:
                # 🛠️ Interactive Filtration Workspace Layout Row
                col_f1, col_f2, col_f3 = st.columns(3)
                with col_f1: 
                    selected_year = st.selectbox(
                        "Admission Year चुनें:", 
                        options=["All"] + sorted(list(set(live_db["Admission Year"].dropna().astype(str).str.strip())))
                    )
                with col_f2: 
                    selected_session = st.selectbox(
                        "Admission Session चुनें:", 
                        options=["All"] + sorted(list(set(live_db["Admission Session"].dropna().astype(str).str.strip())))
                    )
                with col_f3: 
                    selected_status = st.selectbox(
                        "Current Status चुनें:", 
                        options=["All"] + sorted(list(set(live_db["Status"].dropna().astype(str).str.strip())))
                    )
                
                # Apply isolated filtration rules onto database layout array clone
                filtered_admission = live_db.copy()
                if selected_year != "All": 
                    filtered_admission = filtered_admission[filtered_admission["Admission Year"] == selected_year]
                if selected_session != "All": 
                    filtered_admission = filtered_admission[filtered_admission["Admission Session"] == selected_session]
                if selected_status != "All": 
                    filtered_admission = filtered_admission[filtered_admission["Status"] == selected_status]
                
                # Specific architecture rules mapping for Panel 2 operators view layout
                admission_cols = [
                    "Admission Application Number", "Admission Year", "Admission Session", 
                    "Student Name", "Father Name", "Admission Date", "Status", "Unique ID"
                ]
                
                # Auto-initialize array properties if they do not match schema memory profiles
                for target_col in admission_cols:
                    if target_col not in filtered_admission.columns:
                        filtered_admission[target_col] = ""
                        
                # Extract clean target frame layout structure and inject row serial indicators
                render_df = filtered_admission[admission_cols].copy()
                render_df.insert(0, "S.No.", range(1, len(render_df) + 1))
                
                # 📊 Interactive Live Data Transaction Spreadsheet Container
                edited_admission_df = st.data_editor(
                    render_df, 
                    use_container_width=True, 
                    disabled=["S.No.", "Student Name", "Father Name"], 
                    column_config={
                        "Status": st.column_config.SelectboxColumn(
                            "Status", 
                            options=["Regular Student", "Regular", "Pending", "Pass", "EX-STUDENT"],
                            required=True
                        )
                    },
                    key="admission_live_editor_grid_p2", 
                    hide_index=True
                )
                
                # Database live file synchronization operations pipeline trigger
                if st.button("Save & Sync Admission Changes", type="primary", use_container_width=True, key="p2_save_btn"):
                    try:
                        clean_edited = edited_admission_df.drop(columns=["S.No."])
                        
                        # Route transactional modifications back into live state memory mapping
                        for _, row_edit in clean_edited.iterrows():
                            target_app_num = str(row_edit["Admission Application Number"]).strip()
                            
                            # Fetch relative alignment sequence indices based on Key matching
                            idx_matches = live_db[live_db["Admission Application Number"].astype(str).str.strip() == target_app_num].index
                            
                            if not idx_matches.empty:
                                for match_idx in idx_matches:
                                    # Sync allowable editable property structures safely
                                    live_db.at[match_idx, "Admission Year"] = str(row_edit["Admission Year"])
                                    live_db.at[match_idx, "Admission Session"] = str(row_edit["Admission Session"])
                                    live_db.at[match_idx, "Admission Date"] = str(row_edit["Admission Date"])
                                    live_db.at[match_idx, "Status"] = str(row_edit["Status"])
                                    live_db.at[match_idx, "Unique ID"] = str(row_edit["Unique ID"])
                        
                        # Commit updated runtime data mutations directly into database storage file
                        save_live_data(live_db)
                        st.success("🎉 एडमिशन डेटाबेस सफलतापूर्वक मुख्य डेटाबेस (Live CSV) में सिंक और सुरक्षित कर दिया गया है!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"डेटाबेस सिंक्रोनाइज़ेशन चक्र में तकनीकी समस्या आई: {e}")

        # ----------------------------------------------------------------------
        # P3: PANEL UNIQUE ID MODULE (Student Unique ID Mapping)
        # ----------------------------------------------------------------------
        elif current_panel_id == "P3":
            st.header(f"🆔 {get_panel_title('P3')} (Student Unique ID Mapping Engine)")
            
            if live_db.empty: 
                st.warning("⚠️ डेटाबेस वर्तमान में खाली है। कृपया पहले Panel 1 (Entry) से छात्र डेटा लोड करें।")
            else:
                st.markdown("""
                    <div style="background-color: #f0f7ff; border-left: 5px solid #1465de; padding: 10px; border-radius: 4px; margin-bottom: 15px;">
                        📌 <b>ऑपरेटर निर्देश:</b> इस ग्रिड का उपयोग करके केवल छात्रों की <b>Unique ID</b> प्रविष्टियों को सिंक करें। छात्र का नाम, पिता का नाम और आवेदन नंबर सुरक्षा कारणों से लॉक हैं।
                    </div>
                """, unsafe_allow_html=True)
                
                # 🔍 Real-time Search Filter Sub-system
                col_s1, col_s2 = st.columns(2)
                with col_s1:
                    search_field = st.selectbox("खोजने का माध्यम चुनें (Search By):", ["Student Name", "Admission Application Number", "Father Name"], key="p3_search_field")
                with col_s2:
                    search_query = st.text_input(f"यहाँ {search_field} दर्ज करें:", key="p3_search_query").strip()
                
                # Apply dynamic string matching filter to keep runtime workspace clean
                unique_filter_df = live_db.copy()
                if search_query != "":
                    unique_filter_df = unique_filter_df[
                        unique_filter_df[search_field].astype(str).str.contains(search_query, case=False, na=False)
                    ]
                
                # Define specific structural column mapping constraints for Panel 3
                unique_cols = ["Admission Application Number", "Student Name", "Father Name", "Unique ID"]
                
                # Auto-verify column integrity inside current system dataframe mapping array
                for col in unique_cols:
                    if col not in unique_filter_df.columns:
                        unique_filter_df[col] = ""
                
                # Format localized output frame canvas layout and inject incremental serial counters
                render_df = unique_filter_df[unique_cols].copy()
                render_df.insert(0, "S.No.", range(1, len(render_df) + 1))
                
                st.write(f"ग्रिड में प्रदर्शित कुल छात्र रिकॉर्ड संख्या (Matching Records): **{len(render_df)}**")
                
                # 📊 Transactional Isolated Read/Write Grid Spreadsheet Container
                edited_unique_df = st.data_editor(
                    render_df, 
                    use_container_width=True, 
                    disabled=["S.No.", "Admission Application Number", "Student Name", "Father Name"], 
                    column_config={
                        "Unique ID": st.column_config.TextColumn(
                            "Unique ID (Permanent Tracking Key)",
                            help="संस्था द्वारा निर्धारित स्थायी विशिष्ट पहचान पत्र संख्या दर्ज करें",
                            required=True
                        )
                    },
                    key="unique_live_editor_grid_p3", 
                    hide_index=True
                )
                
                # Live master database serialization file updates trigger
                if st.button("Save & Sync Unique IDs", type="primary", use_container_width=True, key="p3_save_btn"):
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
        # P4: PANEL ROLL NO MODULE (University Roll Number Allocation)
        # ----------------------------------------------------------------------
        elif current_panel_id == "P4":
            st.header(f"🔢 {get_panel_title('P4')} (University Roll Number Allocation Engine)")
            
            if live_db.empty: 
                st.warning("⚠️ डेटाबेस वर्तमान में खाली है। कृपया पहले Panel 1 (Entry) से छात्र डेटा लोड करें।")
            else:
                st.markdown("""
                    <div style="background-color: #f7f9fa; border-left: 5px solid #28a745; padding: 10px; border-radius: 4px; margin-bottom: 15px;">
                        📌 <b>ऑपरेटर निर्देश:</b> इस ग्रिड का उपयोग करके विश्वविद्यालय द्वारा जारी <b>Roll No.</b> प्रविष्टियों को अपडेट करें। त्रुटियों से बचने के लिए नाम और विशिष्ट पहचान पत्र संख्या (Unique ID) को लॉक किया गया है।
                    </div>
                """, unsafe_allow_html=True)
                
                # 🔍 Real-time Local Filtering Sub-system
                col_r1, col_r2 = st.columns(2)
                with col_r1:
                    roll_search_field = st.selectbox("खोजने का माध्यम चुनें (Filter By):", ["Student Name", "Unique ID", "Admission Application Number"], key="p4_search_field")
                with col_r2:
                    roll_search_query = st.text_input(f"यहाँ {roll_search_field} प्रविष्टि खोजें:", key="p4_search_query").strip()
                
                # Apply dynamic string matching filter onto target schema copy array
                roll_filter_df = live_db.copy()
                if roll_search_query != "":
                    roll_filter_df = roll_filter_df[
                        roll_filter_df[roll_search_field].astype(str).str.contains(roll_search_query, case=False, na=False)
                    ]
                
                # Define specific column mapping constraints layout configurations for Panel 4
                roll_cols = ["Admission Application Number", "Unique ID", "Student Name", "Roll No."]
                
                # Verify structure uniform constraints prior to grid binding operations
                for col in roll_cols:
                    if col not in roll_filter_df.columns:
                        roll_filter_df[col] = ""
                
                # Extract targeted frame layouts and inject visual row sequence indicators
                render_df = roll_filter_df[roll_cols].copy()
                render_df.insert(0, "S.No.", range(1, len(render_df) + 1))
                
                st.write(f"ग्रिड में प्रदर्शित कुल मैचिंग छात्र रिकॉर्ड संख्या (Active Matrix Records): **{len(render_df)}**")
                
                # 📊 Transactional Isolated Read/Write Grid Spreadsheet Container
                edited_roll_df = st.data_editor(
                    render_df, 
                    use_container_width=True, 
                    disabled=["S.No.", "Admission Application Number", "Unique ID", "Student Name"], 
                    column_config={
                        "Roll No.": st.column_config.TextColumn(
                            "University Roll No.",
                            help="विश्वविद्यालय द्वारा आवंटित आधिकारिक परीक्षा रोल नंबर दर्ज करें",
                            required=True
                        )
                    },
                    key="roll_live_editor_grid_p4", 
                    hide_index=True
                )
                
                # Live master structural updates compilation file write pipeline trigger
                if st.button("Save & Sync Roll Numbers", type="primary", use_container_width=True, key="p4_save_btn"):
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
        # P5: PANEL ENROLLMENT MODULE (University Enrollment Manager)
        # ----------------------------------------------------------------------
        elif current_panel_id == "P5":
            st.header(f"📑 {get_panel_title('P5')} (University Enrollment Manager)")
            
            if live_db.empty: 
                st.warning("⚠️ डेटाबेस वर्तमान में खाली है। कृपया पहले Panel 1 (Entry) से छात्र लोड करें।")
            else:
                st.markdown("""
                    <div style="background-color: #fff9e6; border-left: 5px solid #ffc107; padding: 10px; border-radius: 4px; margin-bottom: 15px;">
                        📌 <b>ऑपरेटर निर्देश:</b> इस ग्रिड का उपयोग करके विश्वविद्यालय <b>Application Enrollment No.</b> और <b>Enrollment No.</b> प्रविष्टियों को अपडेट करें। विषय (Subject) के आधार पर डेटा को फ़िल्टर किया जा सकता है।
                    </div>
                """, unsafe_allow_html=True)
                
                # यूनीक विषयों (Subjects) की सूची निकालकर फ़िल्टर तैयार करना
                available_subjects = ["All"] + sorted(list(set(live_db["Subject"].dropna().astype(str).str.strip())))
                selected_subject = st.selectbox("Subject (विषय) फ़िल्टर चुनें:", options=available_subjects, key="p5_subject_filter_select")
                
                # फ़िल्टर के आधार पर डेटा को अलग करना
                filtered_enrollment = live_db.copy()
                if selected_subject != "All": 
                    filtered_enrollment = filtered_enrollment[filtered_enrollment["Subject"].str.strip() == selected_subject]
                
                # प्रदर्शित किए जाने वाले आवश्यक कॉलम्स की सूची
                enrollment_display_cols = ["Admission Application Number", "Student Name", "Father Name", "Subject", "Application Enrollment No.", "Enrollment No."]
                
                # सुनिश्चित करना कि सभी लक्षित कॉलम्स डेटाफ़्रेम में मौजूद हों
                for col in enrollment_display_cols:
                    if col not in filtered_enrollment.columns:
                        filtered_enrollment[col] = ""
                        
                # रेंडर टेबल तैयार करना और क्रम संख्या (S.No.) जोड़ना
                render_df = filtered_enrollment[enrollment_display_cols].copy()
                render_df.insert(0, "S.No.", range(1, len(render_df) + 1))
                
                st.write(f"ग्रिड में प्रदर्शित कुल छात्र रिकॉर्ड संख्या (Active Enrollment Records): **{len(render_df)}**")
                
                # डेटा एडिटर ग्रिड जहाँ केवल नामांकन संख्या ही एडिट की जा सकती है
                edited_enrollment_df = st.data_editor(
                    render_df, 
                    use_container_width=True, 
                    disabled=["S.No.", "Admission Application Number", "Student Name", "Father Name", "Subject"], 
                    column_config={
                        "Application Enrollment No.": st.column_config.TextColumn("Application Enrollment No.", help="विश्वविद्यालय आवेदन पंजीकरण संख्या दर्ज करें"),
                        "Enrollment No.": st.column_config.TextColumn("University Enrollment No.", help="विश्वविद्यालय द्वारा आवंटित स्थायी नामांकन संख्या दर्ज करें")
                    },
                    key="enrollment_live_editor_grid_p5", 
                    hide_index=True
                )
                
                # डेटाबेस में लाइव सिंक करने का बटन
                if st.button("Save & Sync Enrollment Numbers", type="primary", use_container_width=True, key="p5_save_btn"):
                    try:
                        clean_edited = edited_enrollment_df.drop(columns=["S.No."])
                        enroll_sync_counter = 0
                        
                        # प्रत्येक एडिट की गई रो को मुख्य डेटाबेस (live_db) से सिंक करना
                        for _, row_edit in clean_edited.iterrows():
                            app_num = str(row_edit["Admission Application Number"]).strip()
                            
                            # 'Admission Application Number' के आधार पर इंडेक्स मैच खोजना
                            idx_matches = live_db[live_db["Admission Application Number"].astype(str).str.strip() == app_num].index
                            
                            if not idx_matches.empty:
                                for match_idx in idx_matches:
                                    live_db.at[match_idx, "Application Enrollment No."] = str(row_edit["Application Enrollment No."])
                                    live_db.at[match_idx, "Enrollment No."] = str(row_edit["Enrollment No."])
                                    enroll_sync_counter += 1
                        
                        # लाइव सी.एस.वी फ़ाइल में डेटा सुरक्षित सेव करना
                        save_live_data(live_db)
                        st.success(f"🎉 सफलता! कुल {enroll_sync_counter} छात्र रिकॉर्ड्स का विश्वविद्यालय नामांकन नंबर मुख्य डेटाबेस (Live CSV) में सिंक और अपडेट हो गया है!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"डेटा सिंक्रोनाइज़ेशन चक्र में तकनीकी समस्या आई: {e}")

        # ----------------------------------------------------------------------
        # P6: PANEL SCHOLARSHIP MODULE (Portal & Scholarship Tracker)
        # ----------------------------------------------------------------------
        elif current_panel_id == "P6":
            st.header(f"💰 {get_panel_title('P6')} (Portal & Category Matrix Control)")
            
            # Ensure specialized tracking property fields exist inside live memory arrays
            if "Scholarship Status" not in live_db.columns: 
                live_db["Scholarship Status"] = "Not Applied"
            
            if live_db.empty:
                st.warning("⚠️ डेटाबेस वर्तमान में खाली है। कृपया पहले Panel 1 (Entry) से छात्र डेटा लोड करें।")
            else:
                st.markdown("""
                    <div style="background-color: #f4fbf7; border-left: 5px solid #2e7d32; padding: 10px; border-radius: 4px; margin-bottom: 15px;">
                        📌 <b>ऑपरेटर निर्देश:</b> इस ग्रिड का उपयोग करके श्रेणीवार छात्रवृत्ति आवेदन स्थिति (<b>Scholarship Status</b>) अपडेट करें। विज़ुअलाइज़ेशन फ़िल्टर का उपयोग करके विशिष्ट वर्गों का चयन किया जा सकता है।
                    </div>
                """, unsafe_allow_html=True)
                
                # यूनीक श्रेणियों (Category जैसे General, OBC, SC, ST) की सूची निकालकर फ़िल्टर तैयार करना
                available_categories = ["All"] + sorted(list(set(live_db["Category"].dropna().astype(str).str.strip())))
                selected_category = st.selectbox("Category (वर्ग) फ़िल्टर चुनें:", options=available_categories, key="p6_category_filter_select")
                
                # फ़िल्टर के आधार पर डेटा को अलग करना
                filtered_scholarship = live_db.copy()
                if selected_category != "All": 
                    filtered_scholarship = filtered_scholarship[filtered_scholarship["Category"].str.strip() == selected_category]
                
                # प्रदर्शित किए जाने वाले आवश्यक कॉलम्स की सूची
                scholarship_display_cols = ["Admission Application Number", "Unique ID", "Student Name", "Category", "Scholarship Status"]
                
                # सुनिश्चित करना कि सभी लक्षित कॉलम्स डेटाफ़्रेम में मौजूद हों
                for col in scholarship_display_cols:
                    if col not in filtered_scholarship.columns:
                        filtered_scholarship[col] = ""
                
                # रेंडर टेबल तैयार करना और क्रम संख्या (S.No.) जोड़ना
                render_df = filtered_scholarship[scholarship_display_cols].copy()
                render_df.insert(0, "S.No.", range(1, len(render_df) + 1))
                
                st.write(f"ग्रिड में प्रदर्शित कुल सक्रिय रिकॉर्ड संख्या (Active Matrix Profiles): **{len(render_df)}**")
                
                # डेटा एडिटर ग्रिड जहाँ केवल छात्रवृत्ति स्टेटस ही एडिट किया जा सकता है
                edited_scholarship_df = st.data_editor(
                    render_df, 
                    use_container_width=True, 
                    disabled=["S.No.", "Admission Application Number", "Unique ID", "Student Name", "Category"], 
                    column_config={
                        "Scholarship Status": st.column_config.SelectboxColumn(
                            "Scholarship Status", 
                            options=["Not Applied", "Applied", "Sanctioned", "Disbursed", "Rejected"],
                            required=True,
                            help="छात्र के वर्तमान पोर्टल वेरिफिकेशन प्रोग्रेस स्टेटस का चयन करें"
                        )
                    }, 
                    key="scholarship_live_editor_grid_p6", 
                    hide_index=True
                )
                
                # डेटाबेस में लाइव सिंक करने का बटन
                if st.button("Save & Sync Scholarship Matrix", type="primary", use_container_width=True, key="p6_save_btn"):
                    try:
                        clean_edited = edited_scholarship_df.drop(columns=["S.No."])
                        scholarship_sync_counter = 0
                        
                        # प्रत्येक एडिट की गई रो को मुख्य डेटाबेस (live_db) से सिंक करना
                        for _, row_edit in clean_edited.iterrows():
                            app_num = str(row_edit["Admission Application Number"]).strip()
                            
                            # 'Admission Application Number' के आधार पर इंडेक्स मैच खोजना
                            idx_matches = live_db[live_db["Admission Application Number"].astype(str).str.strip() == app_num].index
                            
                            if not idx_matches.empty:
                                for match_idx in idx_matches:
                                    live_db.at[match_idx, "Scholarship Status"] = str(row_edit["Scholarship Status"])
                                    scholarship_sync_counter += 1
                        
                        # लाइव सी.एस.वी फ़ाइल में डेटा सुरक्षित सेव करना
                        save_live_data(live_db)
                        st.success(f"🎉 सफलता! कुल {scholarship_sync_counter} छात्र रिकॉर्ड्स का छात्रवृत्ति ट्रैकिंग मैट्रिक्स मुख्य डेटाबेस (Live CSV) में सिंक और सुरक्षित कर दिया गया है!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"डेटा सिंक्रोनाइज़ेशन चक्र में तकनीकी समस्या आई: {e}")

        # ----------------------------------------------------------------------
        # P7: PANEL FOIL SHEET GENERATOR MODULE (University CCE Foil Sheet Generator)
        # ----------------------------------------------------------------------
        elif current_panel_id == "P7":
            st.header(f"🖨️ {get_panel_title('P7')} (University CCE Foil Sheet Generator)")
            
            # संस्था का नाम (विश्वविद्यालय/कॉलेज का मानक नाम)
            college_name = "GOVT. K.R.G. POST-GRADUATE AUTONOMOUS COLLEGE, GWALIOR (M.P.)"
            
            if live_db.empty:
                st.warning("⚠️ मास्टर डेटाबेस वर्तमान में खाली है। कृपया पहले Panel 1 (Entry) से छात्र लोड करें।")
            else:
                # प्रिंट छुपाने वाले इनपुट कंट्रोल्स बॉक्स
                st.markdown('<div class="print-hide">', unsafe_allow_html=True)
                st.subheader("⚙️ Foil Sheet Generation Parameters")
                col_p7_1, col_p7_2 = st.columns(2)
                
                with col_p7_1:
                    # डेटाबेस से यूनीक विषयों की लिस्ट निकालकर क्लीन करना
                    unique_subjects = sorted(list(set(live_db['Subject'].dropna().astype(str).str.strip())))
                    selected_subject = st.selectbox(
                        "📚 Select Subject Name:", 
                        options=["All Subjects"] + [s for s in unique_subjects if s != ""], 
                        key="cce_p7_sub"
                    )
                with col_p7_2:
                    # सेमेस्टर या वार्षिक विकल्प चुनना
                    chosen_option = st.selectbox(
                        "📆 Select Semester / Year:", 
                        options=["1 Semester", "2 Semester", "3 Semester", "4 Semester", "1 Year", "2 Year", "3 Year"],
                        key="cce_p7_sem"
                    )
                
                # जनरेट और प्रिंट बटन्स का पैनल
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if st.button("🔄 Generate Foil Sheets Canvas Now", use_container_width=True, type="primary", key="p7_generate_canvas_btn"):
                        st.session_state.cce_foil_generated = True
                with btn_col2:
                    # केवल तभी दिखाई देगा जब फॉयल शीट जनरेट हो चुकी हो
                    if st.session_state.get('cce_foil_generated', False):
                        st.markdown("""
                            <button onclick="window.print()" style="width:100%; height:38px; background-color:#28a745; color:white; border:none; border-radius:4px; font-weight:bold; cursor:pointer;">
                                🖨️ Direct Print / Save as PDF (A4 Landscape)
                            </button>
                        """, unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True) # print-hide div समाप्त
                
                # ----------------------------------------------------------------------
                # फॉयल शीट कैनवास रेंडरिंग इंजन
                # ----------------------------------------------------------------------
                if st.session_state.get('cce_foil_generated', False):
                    st.markdown("---")
                    
                    # विषय के आधार पर डेटा को फ़िल्टर करना
                    foil_filter_df = live_db.copy()
                    if selected_subject != "All Subjects":
                        foil_filter_df = foil_filter_df[foil_filter_df["Subject"].astype(str).str.strip() == selected_subject]
                    
                    if foil_filter_df.empty:
                        st.warning("🔍 चयनित मापदंडों के आधार पर कोई छात्र रिकॉर्ड नहीं मिला।")
                    else:
                        # सुनिश्चित करना कि आवश्यक कॉलम्स जैसे CCE Marks और Roll No मौजूद हों
                        for essential_col in ["Roll No.", "Student Name", "CCE Marks Obtained", "CCE Attendance Status"]:
                            if essential_col not in foil_filter_df.columns:
                                foil_filter_df[essential_col] = ""
                        
                        # फॉयल शीट का संस्थागत हेडर (HTML/CSS)
                        st.markdown(f"""
                            <div style="text-align: center; font-family: Arial, sans-serif; margin-top: 10px;">
                                <h2 style="margin: 0; color: #111; font-size: 22px; font-weight: bold;">{college_name}</h2>
                                <h3 style="margin: 5px 0; font-size: 16px; font-weight: normal; letter-spacing: 1px;">
                                    CONSOLIDATED CCE FOIL SHEET (INTERNAL ASSESSMENT REGISTER)
                                </h3>
                                <div style="display: flex; justify-content: space-between; margin: 15px auto; width: 95%; font-weight: bold; font-size: 14px; border-bottom: 2px solid #333; padding-bottom: 8px;">
                                    <span>📚 SUBJECT: {selected_subject.upper()}</span>
                                    <span>📆 TERM: {chosen_option.upper()}</span>
                                    <span>📊 TOTAL STUDENTS: {len(foil_filter_df)}</span>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # विश्वविद्यालय प्रारूप के अनुसार कस्टमाइज्ड प्रिंट टेबल डेटा तैयार करना
                        foil_print_table = []
                        for idx, row in foil_filter_df.reset_index(drop=True).iterrows():
                            # यदि छात्र अनुपस्थित है, तो नंबर की जगह ABSENT दिखाएं
                            att_status = str(row["CCE Attendance Status"]).strip().upper()
                            display_marks = "ABSENT" if att_status in ["ABSENT", "A", "ABS"] else str(row["CCE Marks Obtained"])
                            if display_marks == "" or display_marks == "nan":
                                display_marks = "-"
                                
                            foil_print_table.append({
                                "S.No.": idx + 1,
                                "University Roll No.": row["Roll No."],
                                "Student Name": row["Student Name"],
                                "Max Marks": "20",  # सीसीई का डिफ़ॉल्ट मैक्सिमम मार्क्स
                                "Marks Obtained (In Figures)": display_marks,
                                "Examiner Signature / Verification": ""
                            })
                            
                        # स्ट्रीमलिट डेटाफ़्रेम के बजाय शुद्ध प्रिंट-फ्रेंडली HTML टेबल रेंडर करना
                        table_html = """
                        <table style="width: 100%; border-collapse: collapse; font-family: Arial, sans-serif; font-size: 13px; margin-top: 10px;">
                            <thead>
                                <tr style="background-color: #f2f2f2; text-align: center;">
                                    <th style="border: 1px solid #333; padding: 8px; width: 6%;">S.No.</th>
                                    <th style="border: 1px solid #333; padding: 8px; width: 18%;">University Roll No.</th>
                                    <th style="border: 1px solid #333; padding: 8px; width: 30%;">Student Name</th>
                                    <th style="border: 1px solid #333; padding: 8px; width: 10%;">Max Marks</th>
                                    <th style="border: 1px solid #333; padding: 8px; width: 18%;">Marks Obtained (Figures)</th>
                                    <th style="border: 1px solid #333; padding: 8px; width: 18%;">Signature Verification</th>
                                </tr>
                            </thead>
                            <tbody>
                        """
                        
                        for row in foil_print_table:
                            table_html += f"""
                                <tr style="text-align: center;">
                                    <td style="border: 1px solid #333; padding: 6px; font-weight: bold;">{row['S.No.']}</td>
                                    <td style="border: 1px solid #333; padding: 6px; font-family: monospace; font-size: 14px;">{row['University Roll No.']}</td>
                                    <td style="border: 1px solid #333; padding: 6px; text-align: left; padding-left: 15px;">{row['Student Name']}</td>
                                    <td style="border: 1px solid #333; padding: 6px; color: #555;">{row['Max Marks']}</td>
                                    <td style="border: 1px solid #333; padding: 6px; font-weight: bold; font-size: 14px;">{row['Marks Obtained (In Figures)']}</td>
                                    <td style="border: 1px solid #333; padding: 6px; color: #ccc; font-style: italic;">________________</td>
                                </tr>
                            """
                            
                        table_html += """
                            </tbody>
                        </table>
                        """
                        
                        # फॉयल शीट के नीचे परीक्षा नियंत्रक (Controller of Exams) के हस्ताक्षर का ब्लॉक
                        footer_html = """
                        <div style="margin-top: 50px; display: flex; justify-content: space-between; padding: 0 30px; font-family: Arial, sans-serif; font-size: 14px; font-weight: bold;">
                            <div style="text-align: center;">
                                <br><br>
                                                                <span>-------------------------------------</span><br>
                                <span>Internal Examiner Signature</span>
                            </div>
                            <div style="text-align: center;">
                                <br><br>
                                <span>-------------------------------------</span><br>
                                <span>External Verification Authority</span>
                            </div>
                            <div style="text-align: center;">
                                <br><br>
                                <span>-------------------------------------</span><br>
                                <span>Exam Controller / HOD Seal</span>
                            </div>
                        </div>
                        """
                        
                        # पूरे कैनवास (HTML तालिका और फुटर) को स्क्रीन पर रेंडर करना
                        st.markdown(table_html, unsafe_allow_html=True)
                        st.markdown(footer_html, unsafe_allow_html=True)

        # ----------------------------------------------------------------------
        # P8: PANEL CCE RECORD MODULE
        # ----------------------------------------------------------------------
        elif current_panel_id == "P8":
            st.header(f"📋 {get_panel_title('P8')} (Internal Assessment Marks Ledger)")
            for f in ["CCE Marks Obtained", "CCE Attendance Status"]:
                if f not in live_db.columns: live_db[f] = ""
            if live_db.empty: st.warning("⚠️ डेटाबेस वर्तमान में खाली है।")
            else:
                available_subjects = ["All"] + sorted(list(set(live_db["Subject"].dropna().astype(str).str.strip())))
                selected_sub = st.selectbox("Subject फ़िल्टर चुनें:", options=available_subjects, key="p8_subject_filter")
                filtered_cce = live_db.copy()
                if selected_sub != "All": filtered_cce = filtered_cce[filtered_cce["Subject"].str.strip() == selected_sub]
                
                cce_display_cols = ["Admission Application Number", "Roll No.", "Student Name", "Subject", "CCE Marks Obtained", "CCE Attendance Status"]
                render_df = filtered_cce[cce_display_cols].copy()
                render_df.insert(0, "S.No.", range(1, len(render_df) + 1))
                
                edited_cce = st.data_editor(render_df, use_container_width=True, disabled=["S.No.", "Admission Application Number", "Roll No.", "Student Name", "Subject"], column_config={"CCE Attendance Status": st.column_config.SelectboxColumn("CCE Attendance Status", options=["Present", "Absent", "Detained"], required=True)}, key="cce_record_live_editor", hide_index=True)
                if st.button("Save & Sync CCE Assessment Ledger", type="primary", use_container_width=True, key="p8_save_btn"):
                    for _, r_edit in edited_cce.drop(columns=["S.No."]).iterrows():
                        idx_matches = live_db[live_db["Admission Application Number"] == r_edit["Admission Application Number"]].index
                        if not idx_matches.empty:
                            for idx in idx_matches:
                                live_db.at[idx, "CCE Marks Obtained"] = r_edit["CCE Marks Obtained"]
                                live_db.at[idx, "CCE Attendance Status"] = r_edit["CCE Attendance Status"]
                    save_live_data(live_db)
                    st.success("🎉 सीसीई आंतरिक मूल्यांकन पंजी सफलतापूर्वक अपडेट हो गई!")
                    st.rerun()

        # ----------------------------------------------------------------------
        # P9: PANEL PROMOTION MODULE
        # ----------------------------------------------------------------------
        elif current_panel_id == "P9":
            st.header(f"📈 {get_panel_title('P9')} (Academic Year Batch Progression Control)")
            if "Promotion Status" not in live_db.columns: live_db["Promotion Status"] = "Eligible"
            if live_db.empty: st.warning("⚠️ डेटाबेस वर्तमान में खाली है।")
            else:
                available_years = ["All"] + sorted(list(set(live_db["Current Year"].dropna().astype(str).str.strip())))
                selected_year = st.selectbox("Current Year फ़िल्टर चुनें:", options=available_years, key="p9_year_filter")
                filtered_promo = live_db.copy()
                if selected_year != "All": filtered_promo = filtered_promo[filtered_promo["Current Year"].str.strip() == selected_year]
                
                promotion_display_cols = ["Admission Application Number", "Roll No.", "Student Name", "Current Year", "Status", "Promotion Status"]
                render_df = filtered_promo[promotion_display_cols].copy()
                render_df.insert(0, "S.No.", range(1, len(render_df) + 1))
                
                edited_promo = st.data_editor(render_df, use_container_width=True, disabled=["S.No.", "Admission Application Number", "Roll No.", "Student Name", "Current Year"], column_config={"Status": st.column_config.SelectboxColumn("Status", options=["Regular", "EX-STUDENT", "Pass", "Pending"], required=True), "Promotion Status": st.column_config.SelectboxColumn("Promotion Status", options=["Eligible", "Promoted", "Detained (Year Back)", "Course Completed"], required=True)}, key="promotion_live_editor", hide_index=True)
                if st.button("Save & Sync Promotion Register", type="primary", use_container_width=True, key="p9_save_btn"):
                    for _, r_edit in edited_promo.drop(columns=["S.No."]).iterrows():
                        idx_matches = live_db[live_db["Admission Application Number"] == r_edit["Admission Application Number"]].index
                        if not idx_matches.empty:
                            for idx in idx_matches:
                                live_db.at[idx, "Status"] = r_edit["Status"]
                                live_db.at[idx, "Promotion Status"] = r_edit["Promotion Status"]
                    save_live_data(live_db)
                    st.success("🎉 छात्र बैच प्रमोशन पंजी सफलतापूर्वक अपडेट हो गई!")
                    st.rerun()

        # ----------------------------------------------------------------------
        # P10: PANEL RESULT MODULE
        # ----------------------------------------------------------------------
        elif current_panel_id == "P10":
            st.header(f"📊 {get_panel_title('P10')} (Tabulation Register & Exam Controller)")
            for f in ["Marks Obtained", "Result Status", "Exam Remarks"]:
                if f not in live_db.columns: live_db[f] = ""
            if live_db.empty: st.warning("⚠️ डेटाबेस वर्तमान में खाली है।")
            else:
                available_subjects = ["All"] + sorted(list(set(live_db["Subject"].dropna().astype(str).str.strip())))
                selected_sub = st.selectbox("Subject फ़िल्टर चुनें:", options=available_subjects, key="p10_subject_filter")
                filtered_res = live_db.copy()
                if selected_sub != "All": filtered_res = filtered_res[filtered_res["Subject"].str.strip() == selected_sub]
                
                result_display_cols = ["Admission Application Number", "Roll No.", "Enrollment No.", "Student Name", "Subject", "Marks Obtained", "Result Status", "Exam Remarks"]
                render_df = filtered_res[result_display_cols].copy()
                render_df.insert(0, "S.No.", range(1, len(render_df) + 1))
                
                edited_res = st.data_editor(render_df, use_container_width=True, disabled=["S.No.", "Admission Application Number", "Roll No.", "Enrollment No.", "Student Name", "Subject"], column_config={"Result Status": st.column_config.SelectboxColumn("Result Status", options=["Pass", "Fail", "ATKT", "Withheld", "Absent"], required=True)}, key="result_live_editor", hide_index=True)
                if st.button("Save & Sync Tabulation Register", type="primary", use_container_width=True, key="p10_save_btn"):
                    for _, r_edit in edited_res.drop(columns=["S.No."]).iterrows():
                        idx_matches = live_db[live_db["Admission Application Number"] == r_edit["Admission Application Number"]].index
                        if not idx_matches.empty:
                            for idx in idx_matches:
                                live_db.at[idx, "Marks Obtained"] = r_edit["Marks Obtained"]
                                live_db.at[idx, "Result Status"] = r_edit["Result Status"]
                                live_db.at[idx, "Exam Remarks"] = r_edit["Exam Remarks"]
                    save_live_data(live_db)
                    st.success("🎉 परीक्षा परिणाम पंजी सफलतापूर्वक लाइव डेटाबेस में सिंक हो गई!")
                    st.rerun()

        # ----------------------------------------------------------------------
        # P11: NOTICE BOARD EDIT MODULE
        # ----------------------------------------------------------------------
        elif current_panel_id == "P11":
            st.header(f"📢 {get_panel_title('P11')} (Official Notice Board Customizer)")
            with st.form(key="p11_notice_form"):
                updated_notice = st.text_area("होम स्क्रीन के लिए सूचना पटल टेक्स्ट लिखें:", value=st.session_state.notice_text, height=200)
                if st.form_submit_button("Publish Notice Live Now", type="primary", use_container_width=True):
                    st.session_state.notice_text = updated_notice
                    save_notice_board(updated_notice)
                    st.success("🎉 कॉलेज सूचना पटल सफलतापूर्वक अपडेट हो गया है!")
                    st.rerun()

        # ----------------------------------------------------------------------
               # ----------------------------------------------------------------------
        # P12: PRE-LOGIN VIEW CUSTOMIZER MODULE
        # ----------------------------------------------------------------------
        elif current_panel_id == "P12":
            st.header(f"⚙️ {get_panel_title('P12')} (Pre-Login Landing Screen Editor)")
            
            st.markdown("""
                <div style="background-color: #fcf8e3; border-left: 5px solid #f0ad4e; padding: 12px; border-radius: 4px; margin-bottom: 20px;">
                    📌 <b>प्रशासक निर्देश:</b> इस कंट्रोल रूम का उपयोग करके आप बिना लॉगिन किए दिखने वाले वेलकम पेज, आध्यात्मिक हेडर मंत्र, सिस्टम टाइटल और नोटिस बोर्ड की स्टाइलिंग थीम को लाइव बदल सकते हैं।
                </div>
            """, unsafe_allow_html=True)
            
            # Form setup for capturing structural metadata transformations safely
            with st.form(key="p12_landing_view_editor_form"):
                st.subheader("🖼️ Header Elements Configuration")
                
                col_view1, col_view2 = st.columns(2)
                with col_view1:
                    header_toggle = st.checkbox(
                        "शो हेडर टेक्स्ट (Display Institutional Header text block)", 
                        value=st.session_state.pre_login_config.get("show_header_text", True)
                    )
                    mantra_text = st.text_input(
                        "शीर्ष मंत्र टेक्स्ट (Spiritual Invocation / Mantra text):", 
                        value=st.session_state.pre_login_config.get("header_mantra", "ॐ श्री गुरवे नमः")
                    )
                with col_view2:
                    system_title_text = st.text_input(
                        "सिस्टम का मुख्य नाम (Main Gateway Application Title):", 
                        value=st.session_state.pre_login_config.get("system_title", "Permanent Shared Live Database System")
                    )
                
                st.markdown("---")
                st.subheader("🎨 Notice Board Branding & Themes (Official Notice Board Style)")
                
                col_theme1, col_theme2 = st.columns(2)
                with col_theme1:
                    border_color = st.color_picker(
                        "नोटिस बोर्ड लेफ्ट बॉर्डर हाइलाइट रंग (Left accent boundary border color):", 
                        value=st.session_state.pre_login_config.get("notice_board_border_color", "#FF5733")
                    )
                with col_theme2:
                    bg_color = st.color_picker(
                        "नोटिस बोर्ड बैकग्राउंड शेड रंग (Container surface background hex color):", 
                        value=st.session_state.pre_login_config.get("notice_board_bg_color", "#f9f9f9")
                    )
                
                # Execution confirmation action trigger layer
                st.markdown("<br>", unsafe_allow_html=True)
                submit_settings = st.form_submit_button(
                    "💾 Apply & Save Landing View Settings Permanently", 
                    type="primary", 
                    use_container_width=True
                )
                
                if submit_settings:
                    # Update local runtime workspace dictionary context elements
                    updated_config = {
                        "show_header_text": header_toggle,
                        "header_mantra": mantra_text,
                        "system_title": system_title_text,
                        "notice_board_border_color": border_color,
                        "notice_board_bg_color": bg_color
                    }
                    
                    st.session_state.pre_login_config = updated_config
                    save_pre_login_config(updated_config)
                    
                    st.success("🎉 वेलकम व्यू सेटिंग्स सफलतापूर्वक सेव हो गई हैं! अब बिना लॉगिन वाले मुख्य होम पेज पर ये बदलाव लाइव काम करेंगे।")
                    st.rerun()

        # ----------------------------------------------------------------------
        # P13: PANEL MERGE MODULE (Database Smart Merge Panel)
        # ----------------------------------------------------------------------
        elif current_panel_id == "P13":
            st.header(f"🔀 {get_panel_title('P13')} (Database Smart Merge Panel)")
            
            st.markdown("""
                <div style="background-color: #f4fbf7; border-left: 5px solid #2e7d32; padding: 12px; border-radius: 4px; margin-bottom: 20px;">
                    📌 <b>ऑपरेटर निर्देश (Smart Merge Instructions):</b> यह मॉड्यूल आपको बाहरी एक्सेल/CSV फ़ाइल को मुख्य लाइव डेटाबेस में मिलाने की अनुमति देता है। 
                    चुनी गई <b>Unique Key</b> (जैसे Admission Application Number, Unique ID, या Roll No.) के आधार पर सिस्टम डेटाबेस की मैचिंग रोज़ (Rows) को स्वचालित रूप से ढूंढकर नए और पुराने कॉलम्स अपडेट कर देगा।
                </div>
            """, unsafe_allow_html=True)
            
            # File uploader widget container interface layer targeting source files
            uploaded_merge_file = st.file_uploader(
                "मर्ज करने के लिए नई CSV फ़ाइल का चयन करें (Select CSV File to Merge):", 
                type=["csv"], 
                key="p13_csv_uploader_widget"
            )
            
            if uploaded_merge_file is not None:
                try:
                    # Parse raw file text stream inputs into pandas dataframe using string datatype to preserve formatting
                    incoming_df = pd.read_csv(uploaded_merge_file, dtype=str).fillna("")
                    
                    st.markdown("### 📋 Incoming Dataset Preview (First 3 Rows)")
                    st.dataframe(incoming_df.head(3), use_container_width=True, hide_index=True)
                    
                    # Available identification metrics setup mapping definitions
                    merge_options = ["Admission Application Number", "Unique ID", "Roll No."]
                    valid_keys = [col for col in merge_options if col in incoming_df.columns and col in live_db.columns]
                    
                    if not valid_keys:
                        st.error("❌ त्रुटि: अपलोड की गई CSV फ़ाइल में मिलान के लिए 'Admission Application Number', 'Unique ID', या 'Roll No.' में से कम से कम एक की (Key) कॉलम होना अनिवार्य है!")
                    else:
                        col_m1, col_m2 = st.columns(2)
                        with col_m1:
                            merge_key = st.selectbox(
                                "🔑 मिलान के लिए Unique Identifier Key चुनें:", 
                                options=valid_keys, 
                                key="p13_selected_merge_key_dropdown"
                            )
                        with col_m2:
                            st.info(f"रो-मैपिंग मिलान फ़ील्ड: **{merge_key}**")
                            
                        # Smart merge execution logic validation trigger button
                        if st.button("Execute Smart Database Merge Now", type="primary", use_container_width=True, key="p13_execute_merge_btn"):
                            with st.spinner("मास्टर डेटाबेस संकलन और लिंकिंग प्रक्रिया चल रही है, कृपया प्रतीक्षा करें..."):
                                
                                # Clean tracking keys from both DataFrames to ensure precise row matching
                                live_db[merge_key] = live_db[merge_key].astype(str).str.strip()
                                incoming_df[merge_key] = incoming_df[merge_key].astype(str).str.strip()
                                
                                merge_counter = 0
                                new_columns_added = []
                                
                                # Scan structural fields array blocks present in incoming sheet but missing from master layout schema
                                for col in incoming_df.columns:
                                    if col not in live_db.columns:
                                        live_db[col] = ""
                                        new_columns_added.append(col)
                                
                                # Iterative sequence loop traversing lines inside source input frame matrix arrays
                                for _, row_incoming in incoming_df.iterrows():
                                    incoming_key_val = str(row_incoming[merge_key]).strip()
                                    
                                    # Skip current operation cycle if primary indexing string token is blank
                                    if incoming_key_val == "":
                                        continue
                                        
                                    # Query alignment match pointer locations across repository structures
                                    idx_matches = live_db[live_db[merge_key] == incoming_key_val].index
                                    
                                    if not idx_matches.empty:
                                        merge_counter += 1
                                        for match_idx in idx_matches:
                                            # Safely pass specific parameters down into active cell rows, excluding index itself
                                            for col in incoming_df.columns:
                                                if col != merge_key:
                                                    live_db.at[match_idx, col] = str(row_incoming[col]).strip()
                                
                                # Commit finalized active structures updates back down into permanent physical storage mapping CSV
                                save_live_data(live_db)
                                
                                # Visual summaries display compilation feedback panels layout
                                st.success(f"🎉 Smart Database Merge ऑपरेशन सफलतापूर्वक पूरा हुआ!")
                                
                                col_res1, col_res2 = st.columns(2)
                                with col_res1:
                                    st.metric(label="सफलतापूर्वक अपडेटेड छात्र पंक्तियाँ (Matched Rows Updated)", value=merge_counter)
                                with col_res2:
                                    st.metric(label="कुल कॉलम्स की संख्या (Total Schema Columns Now)", value=len(live_db.columns))
                                    
                                if new_columns_added:
                                    st.info(f"🆕 <b>डेटाबेस स्कीमा में जुड़े नए डायनेमिक कॉलम्स:</b> {', '.join([f'<i>{c}</i>' for c in new_columns_added])}", icon="ℹ️")
                                
                                # Clear workspace execution parameters state cache tracking flags
                                st.rerun()
                                
                except Exception as e:
                    st.error(f"डेटाबेस कंपाइलेशन और मर्जिंग चक्र में अनपेक्षित तकनीकी त्रुटि आई: {e}")

                          # ----------------------------------------------------------------------
        # P14: PANEL VIEWER (INTEGRATED INDEX SYSTEM)
        # ----------------------------------------------------------------------
        elif current_panel_id == "P14":
            st.header(f"👁️ {get_panel_title('P14')} (Multi-Panel Inspection Window)")

            # Master dictionary mapping each panel to its designated columns layout framework
            panel_options_list = {
                "Panel 2: Admission View": ["Admission Application Number", "Student Name", "Admission Year", "Admission Session", "Admission Date", "Status"],
                "Panel 3: Unique ID View": ["Admission Application Number", "Student Name", "Father Name", "Unique ID"],
                "Panel 4: Roll No View": ["Admission Application Number", "Unique ID", "Student Name", "Roll No."],
                "Panel 5: Enrollment View": ["Admission Application Number", "Student Name", "Subject", "Application Enrollment No.", "Enrollment No."],
                "Panel 6: Scholarship View": ["Admission Application Number", "Unique ID", "Student Name", "Category", "Scholarship Status"],
                "Panel 7: CCE Foil View": ["Roll No.", "Student Name", "Subject Code", "Subject", "Status"],
                "Panel 8: CCE Record View": ["Admission Application Number", "Roll No.", "Student Name", "Subject", "CCE Marks Obtained", "CCE Attendance Status"],
                "Panel 9: Promotion View": ["Admission Application Number", "Roll No.", "Student Name", "Current Year", "Status", "Promotion Status"],
                "Panel 10: Result View": ["Admission Application Number", "Roll No.", "Enrollment No.", "Student Name", "Subject", "Marks Obtained", "Result Status", "Exam Remarks"],
                "Panel 11: Notice Board View": ["Admission Application Number", "Student Name", "Status"],
                "Panel 12: Landing Configuration View": ["Admission Year", "Admission Session", "Student Name", "Status"],
                "Panel 13: Database Smart Merge View": ["Admission Year", "Admission Application Number", "Unique ID", "Roll No.", "Enrollment No.", "Student Name"]
            }

            st.subheader("📂 Select Panel Dashboard View")
            selected_panel_view = st.selectbox(
                "निरीक्षण करने के लिए पैनल सूची (P2 से P13) चुनें (Select Dashboard to Inspect):",
                options=list(panel_options_list.keys()),
                key="p14_panel_selector_dropdown"
            )

            # Retrieve targeted schema properties matching user selection mapping profiles
            target_columns = panel_options_list[selected_panel_view]

            # Enforce schema uniform layout by auto-initializing missing value data fields 
            for c_col in target_columns:
                if c_col not in live_db.columns:
                    live_db[c_col] = ""

            st.markdown(f"### 📋 {selected_panel_view} - Active Transactions Grid")
            
            # Interactive metadata text query filtration split row controls
            col_search1, col_search2 = st.columns(2)
            with col_search1:
                search_target_col = st.selectbox(
                    "खोजने के लिए फ़ील्ड चुनें (Search Column Filter):", 
                    options=target_columns, 
                    key="p14_search_col_target_dropdown"
                )
            with col_search2:
                search_query_text = st.text_input(
                    f"'{search_target_col}' में प्रविष्टि खोजें (Type Search Query):", 
                    key="p14_query_val_text_input"
                ).strip()

            # Clone operational source array blocks to keep cache clear of data degradation
            view_filtered_df = live_db.copy()
            if search_query_text != "":
                view_filtered_df = view_filtered_df[
                    view_filtered_df[search_target_col].astype(str).str.contains(search_query_text, case=False, na=False)
                ]

            st.write(f"वर्तमान ग्रिड में कुल उपलब्ध छात्र रिकॉर्ड संख्या (Total Matching Student Records): **{len(view_filtered_df)}**")

            # Isolate matching framework variables prior to rendering grid transformations
            final_render_cols = [col for col in target_columns if col in view_filtered_df.columns]
            
            if not view_filtered_df.empty:
                # Extract clean targeting segments properties copy profiles array
                display_ready_df = view_filtered_df[final_render_cols].copy()
                
                # Apply localized display label text conversions configured via admin mapping schemas
                display_ready_df = display_ready_df.rename(columns={c: get_display_name(c) for c in display_ready_df.columns})
                display_ready_df.insert(0, "S.No.", range(1, len(display_ready_df) + 1))
                
                # Render structured final lookup spreadsheet framework canvas onto viewport
                st.dataframe(
                    display_ready_df,
                    use_container_width=True,
                    hide_index=True
                )
                
                # 📥 Localized platform download compilation transactional trigger layer
                st.download_button(
                    label=f"📥 Download Selected Dashboard Report ({selected_panel_view.split(':')[0]} Snapshot CSV)",
                    data=view_filtered_df[final_render_cols].to_csv(index=False).encode('utf-8'),
                    file_name=f"{selected_panel_view.split(':')[0].replace(' ', '_').lower()}_inspection_report.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="p14_download_compiled_report_btn"
                )
            else:
                st.warning("🔍 निर्दिष्ट खोज प्रविष्टि के आधार पर कोई रिकॉर्ड नहीं मिला। (No records found matching specified target filters.)")


        # ----------------------------------------------------------------------
        # P15: PANEL ADMIN (15 PANELS SUPREME ENGINE & NOTICE BOARD MANAGER)
        # ----------------------------------------------------------------------
        elif current_panel_id == "P15":
            st.header(f"🛠️ {get_panel_title('P15')} (Full Super-Admin Control Command)")
            
            # 📢 Live Notice Board Manager Panel Area
            st.subheader("📢 Live Notice Board Manager")
            with st.expander("कॉलेज सूचना पटल (Official Notice Board) की गाइडलाइंस एडिट करें", expanded=True):
                with st.form(key="p15_notice_board_edit_form"):
                    updated_notice_input = st.text_area(
                        "सूचना पटल की पंक्तियाँ लिखें (प्रत्येक नई लाइन मुख्य पेज पर एक नया पॉइंट बनेगी):",
                        value=st.session_state.notice_text,
                        height=150,
                        key="p15_notice_text_area_input"
                    )
                    if st.form_submit_button("Publish & Save Notice Board Permanently", type="primary", use_container_width=True):
                        st.session_state.notice_text = updated_notice_input
                        save_notice_board(updated_notice_input)
                        st.success("🎉 कॉलेज सूचना पटल सफलतापूर्वक अपडेट हो गया है! यह बिना लॉगिन वाले होम पेज पर लाइव दिखाई देगा।")
                        st.rerun()

            st.markdown("---")
            st.subheader("✏️ Dynamic 15 Panels Name & Label Customizer")
            with st.expander("15 पैनल्स के नाम (App Titles) एडिट करने के लिए यहाँ क्लिक करें", expanded=False):
                with st.form(key="p15_panel_rename_matrix_form"):
                    p_setup1, p_setup2 = st.columns(2)
                    temp_panel_mappings = {}
                    for idx, p_key in enumerate(DEFAULT_PANELS.keys()):
                        current_panel_name = st.session_state.panel_names.get(p_key, DEFAULT_PANELS[p_key])
                        if idx % 2 == 0:
                            with p_setup1: 
                                temp_panel_mappings[p_key] = st.text_input(f"Name for {p_key}:", value=current_panel_name, key=f"p15_ren_{p_key}")
                        else:
                            with p_setup2: 
                                temp_panel_mappings[p_key] = st.text_input(f"Name for {p_key}:", value=current_panel_name, key=f"p15_ren_{p_key}")
                    
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
                        status_lbl = "🙈 Hidden" if st.session_state[f"hide_panel_{p_key}"] else "👀 Active"
                        if st.button(f"{p_key}\n({status_lbl})", use_container_width=True, key=f"p15_btn_v_{p_key}"):
                            st.session_state[f"hide_panel_{p_key}"] = not st.session_state[f"hide_panel_{p_key}"]
                            st.rerun()
                            
            # Visibility Panel Controllers Layer for P8 - P15
            with vis_tabs[1]:
                c8, c9, c10, c11, c12, c13, c14, c15 = st.columns(8)
                panels_p8_p15 = ["P8", "P9", "P10", "P11", "P12", "P13", "P14", "P15"]
                cols_p8_p15 = [c8, c9, c10, c11, c12, c13, c14, c15]
                for i, p_key in enumerate(panels_p8_p15):
                    with cols_p8_p15[i]:
                        status_lbl = "🙈 Hidden" if st.session_state[f"hide_panel_{p_key}"] else "👀 Active"
                        if st.button(f"{p_key}\n({status_lbl})", use_container_width=True, key=f"p15_btn_v_{p_key}"):
                            st.session_state[f"hide_panel_{p_key}"] = not st.session_state[f"hide_panel_{p_key}"]
                            st.rerun()

            st.markdown("---")
            st.subheader("📊 Master Database List View & Advanced Operational Controls")
            
            # Action Toggles Column Layout
            col_ctrl1, col_ctrl2, col_ctrl3 = st.columns(3)
            with col_ctrl1:
                lbl_edit = "👀 एडिट टेक्स्ट FUNCTION: active" if st.session_state.admin_unhide_edit else "🙈 एडिट टेक्स्ट FUNCTION: hidden"
                if st.button(lbl_edit, use_container_width=True, key="p15_edit_toggle_master_btn"):
                    st.session_state.admin_unhide_edit = not st.session_state.admin_unhide_edit
                    st.rerun()
            with col_ctrl2:
                lbl_move = "👀 कॉलम मूव बटन्स: active" if st.session_state.admin_unhide_move else "🙈 कॉलम मूव बटन्स: hidden"
                if st.button(lbl_move, use_container_width=True, key="p15_move_toggle_master_btn"):
                    st.session_state.admin_unhide_move = not st.session_state.admin_unhide_move
                    st.rerun()
            with col_ctrl3:
                lock_label = "🔒 लिस्ट लॉक करें (Locked)" if st.session_state.admin_lock_state else "🔓 लिस्ट अनलॉक करें (Editable)"
                if st.button(lock_label, use_container_width=True, type="primary" if not st.session_state.admin_lock_state else "secondary", key="p15_lock_toggle_master_btn"):
                    st.session_state.admin_lock_state = not st.session_state.admin_lock_state
                    st.rerun()

            # Dynamic Row/Column Order Shifting Controller Engine Block
            if st.session_state.admin_unhide_move and not st.session_state.admin_lock_state:
                st.info("🔀 कॉलम का क्रम बदलने के लिए सेलेक्ट करें (Select Column to Shift):")
                target_col = st.selectbox("मूव करने के लिए कॉलम चुनें:", options=st.session_state.admin_columns_order, key="p15_column_shifter_select_box")
                c_left, c_right = st.columns(2)
                
                if c_left.button("⬅️ Shift Left", use_container_width=True, key="p15_shift_left_master_btn"):
                    idx = st.session_state.admin_columns_order.index(target_col)
                    if idx > 0:
                        st.session_state.admin_columns_order[idx], st.session_state.admin_columns_order[idx-1] = st.session_state.admin_columns_order[idx-1], st.session_state.admin_columns_order[idx]
                        st.rerun()
                        
                if c_right.button("➡️ Shift Right", use_container_width=True, key="p15_shift_right_master_btn"):
                    idx = st.session_state.admin_columns_order.index(target_col)
                    if idx < len(st.session_state.admin_columns_order) - 1:
                        st.session_state.admin_columns_order[idx], st.session_state.admin_columns_order[idx+1] = st.session_state.admin_columns_order[idx+1], st.session_state.admin_columns_order[idx]
                        st.rerun()

            # Filtering layout fields based on targeted admin sorting preferences
            render_columns = [col for col in st.session_state.admin_columns_order if col in live_db.columns]
            ordered_db = live_db[render_columns].copy()
            ordered_db_display = ordered_db.rename(columns={c: get_display_name(c) for c in ordered_db.columns})
            ordered_db_display.insert(0, "S.No.", range(1, len(ordered_db_display) + 1))

            st.write(f"डेटाबेस में कुल लाइव रिकॉर्ड संख्या (Total Live Database Records): **{len(ordered_db_display)}**")

            # Active live-edit schema matrix processing vs read-only data grid views
            if not st.session_state.admin_lock_state and st.session_state.admin_unhide_edit:
                st.warning("⚠️ लाइव संपादन (Live Editing Matrix Mode) सक्रिय है।")
                edited_df = st.data_editor(
                    ordered_db_display, 
                    use_container_width=True, 
                    disabled=["S.No."], 
                    num_rows="dynamic", 
                    key="p15_admin_live_editor_grid_container", 
                    hide_index=True
                )
                
                if st.button("Save & Sync Matrix Changes", type="primary", use_container_width=True, key="p15_save_matrix_master_btn"):
                    try:
                        clean_edited = edited_df.drop(columns=["S.No."])
                        reverse_mapping = {get_display_name(c): c for c in render_columns}
                        
                        synced_data = {col: [] for col in DEFAULT_COLUMNS}
                        for extra_col in live_db.columns:
                            if extra_col not in synced_data: 
                                synced_data[extra_col] = []

                        for _, row_edit in clean_edited.iterrows():
                            for display_name_key in clean_edited.columns:
                                internal_key = reverse_mapping.get(display_name_key, display_name_key)
                                if internal_key in synced_data:
                                    synced_data[internal_key].append(row_edit[display_name_key])

                        # Cleanly aligned with your database synchronization mapping rules
                        max_len = max(len(lst) for lst in synced_data.values()) if synced_data.values() else 0
                        for k_key in synced_data.keys():
                            while len(synced_data[k_key]) < max_len: 
                                synced_data[k_key].append("")
                                
                        new_live_db = pd.DataFrame(synced_data)
                        save_live_data(new_live_db)
                        st.success("🎉 संपूर्ण मास्टर डेटाबेस सफलतापूर्वक सिंक और अपडेट कर दिया गया है!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"डेटा सिंक्रोनाइज़ेशन चक्र में तकनीकी समस्या आई: {e}")
            else:
                st.dataframe(ordered_db_display, use_container_width=True, hide_index=True)
                
