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

# 🔒 15 पैनल्स के हिसाब से 15 सेपरेटेड क्रेडेंशियल्स की मास्टर डिक्शनरी
DEFAULT_CREDENTIALS = {
    "admin": {"password": "admin15master", "role": "full_admin", "label": "👑 Super Admin (All 15 Panels Control)"},
    "p1_entry": {"password": "entry1123", "role": "p1_role", "label": "📝 P1: Student Data Onboarding Operator"},
    "p2_admission": {"password": "adm2123", "role": "p2_role", "label": "🎓 P2: Admission Control Manager"},
    "p3_enrollment": {"password": "enr3123", "role": "p3_role", "label": "📑 P3: University Enrollment Manager"},
    "p4_scholarship": {"password": "sch4123", "role": "p4_role", "label": "💰 P4: Portal & Scholarship Tracker"},
    "p5_result": {"password": "res5123", "role": "p5_role", "label": "📊 P5: Tabulation Register Exam Controller"},
    "p6_promotion": {"password": "pro6123", "role": "p6_role", "label": "📈 P6: Batch Progression Controller"},
    "p7_foil": {"password": "foil7123", "role": "p7_role", "label": "🖨️ P7: CCE Foil Sheet Generator"},
    "p8_cce_record": {"password": "cce8123", "role": "p8_role", "label": "📋 P8: Internal Assessment Ledger Entry"},
    "p9_extension": {"password": "ext9123", "role": "p9_role", "label": "📌 P9: Extension Ledger Room 1"},
    "p10_extension": {"password": "ext10123", "role": "p10_role", "label": "📌 P10: Extension Ledger Room 2"},
    "p11_extension": {"password": "ext11123", "role": "p11_role", "label": "📌 P11: Extension Ledger Room 3"},
    "p12_extension": {"password": "ext12123", "role": "p12_role", "label": "📌 P12: Extension Ledger Room 4"},
    "p13_merge": {"password": "mrg13123", "role": "p13_role", "label": "🔀 P13: External Database Smart Merge"},
    "p14_viewer": {"password": "view14123", "role": "p14_role", "label": "👁️ P14: Multi-Panel Inspection Window"}
}

# 🛠️ डिफ़ॉल्ट 15 पैनल्स की डिक्शनरी मैपिंग (P1 से P15)
DEFAULT_PANELS = {
    "P1": "Panal entry", "P2": "Panal admission", "P3": "Panal enrollment",
    "P4": "Panal scholarship", "P5": "Panal result", "P6": "Panal promotion",
    "P7": "Panal foil", "P8": "Panal cce record", "P9": "Panal P9 Extension",
    "P10": "Panal P10 Extension", "P11": "Panal P11 Extension", "P12": "Panal P12 Extension",
    "P13": "Panal merge", "P14": "Panal viewer", "P15": "Panel admin"
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
# 🛑 लॉगिन से पहले का ब्लॉक
# ==========================================================
if st.session_state.user_role is None:
    st.markdown("""
        <div class="notice-board">
            <div class="notice-title">📢 कॉलेज सूचना पटल (Official Notice Board)</div>
            <p>1. यह एक पूर्णतः सुरक्षित, लाइव क्लाउड स्टूडेंट डेटाबेस मैनेजमेंट सिस्टम है।</p>
            <p>2. डेटा प्रविष्टि, सुधार, स्कॉलरशिप वेरिफिकेशन या परीक्षा परिणाम अपडेट करने के लिए अधिकृत यूजर क्रेडेंशियल्स का उपयोग करें।</p>
            <p>3. बिना लॉगिन के डेटाबेस तक पहुँच पूर्णतः प्रतिबंधित है। किसी भी समस्या के लिए सुपर-एडमिन से संपर्क करें।</p>
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
# Phase 2: Post Authorized Panel Systems
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
        # P2: PANEL ADMISSION MODULE
        # ----------------------------------------------------------------------
        elif current_panel_id == "P2":
            st.header(f"🎓 {get_panel_title('P2')} (Admission Control & Verification)")
            if live_db.empty: 
                st.warning("⚠️ डेटाबेस वर्तमान में खाली है।")
            else:
                col_f1, col_f2, col_f3 = st.columns(3)
                with col_f1: 
                    selected_year = st.selectbox("Admission Year चुनें:", ["All"] + sorted(list(set(live_db["Admission Year"].dropna().astype(str)))))
                with col_f2: 
                    selected_session = st.selectbox("Admission Session चुनें:", ["All"] + sorted(list(set(live_db["Admission Session"].dropna().astype(str)))))
                with col_f3: 
                    selected_status = st.selectbox("Current Status चुनें:", ["All"] + sorted(list(set(live_db["Status"].dropna().astype(str)))))
                
                filtered_admission = live_db.copy()
                if selected_year != "All": 
                    filtered_admission = filtered_admission[filtered_admission["Admission Year"] == selected_year]
                if selected_session != "All": 
                    filtered_admission = filtered_admission[filtered_admission["Admission Session"] == selected_session]
                if selected_status != "All": 
                    filtered_admission = filtered_admission[filtered_admission["Status"] == selected_status]
                
                admission_cols = ["Admission Application Number", "Admission Year", "Admission Session", "Student Name", "Father Name", "Admission Date", "Status", "Unique ID"]
                display_cols = [c for c in admission_cols if c in filtered_admission.columns]
                render_df = filtered_admission[display_cols].copy()
                render_df.insert(0, "S.No.", range(1, len(render_df) + 1))
                
                edited_admission_df = st.data_editor(
                    render_df, 
                    use_container_width=True, 
                    disabled=["S.No.", "Student Name", "Father Name"], 
                    key="admission_live_editor", 
                    hide_index=True
                )
                
                if st.button("Save & Sync Admission Changes", type="primary", use_container_width=True):
                    clean_edited = edited_admission_df.drop(columns=["S.No."])
                    for _, row_edit in clean_edited.iterrows():
                        idx_matches = live_db[live_db["Admission Application Number"] == row_edit["Admission Application Number"]].index
                        if not idx_matches.empty:
                            for match_idx in idx_matches:
                                for c in clean_edited.columns: 
                                    live_db.at[match_idx, c] = row_edit[c]
                    save_live_data(live_db)
                    st.success("✅ एडमिशन डेटाबेस सफलतापूर्वक सिंक हो गया है!")
                    st.rerun()

        # ----------------------------------------------------------------------
        # P3: PANEL ENROLLMENT MODULE
        # ----------------------------------------------------------------------
        elif current_panel_id == "P3":
            st.header(f"📑 {get_panel_title('P3')} (University Enrollment Manager)")
            if live_db.empty: 
                st.warning("⚠️ डेटाबेस वर्तमान में खाली है।")
            else:
                selected_subject = st.selectbox("Subject (विषय) चुनें:", ["All"] + sorted(list(set(live_db["Subject"].dropna().astype(str)))))
                filtered_enrollment = live_db.copy()
                if selected_subject != "All": 
                    filtered_enrollment = filtered_enrollment[filtered_enrollment["Subject"] == selected_subject]
                
                enrollment_display_cols = ["Admission Application Number", "Student Name", "Father Name", "Subject", "Application Enrollment No.", "Enrollment No."]
                render_df = filtered_enrollment[enrollment_display_cols].copy()
                render_df.insert(0, "S.No.", range(1, len(render_df) + 1))
                
                edited_enrollment_df = st.data_editor(
                    render_df, 
                    use_container_width=True, 
                    disabled=["S.No.", "Admission Application Number", "Student Name", "Father Name", "Subject"], 
                    key="enrollment_live_editor", 
                    hide_index=True
                )
                
                if st.button("Save & Sync Enrollment Numbers", type="primary", use_container_width=True):
                    clean_edited = edited_enrollment_df.drop(columns=["S.No."])
                    for _, row_edit in clean_edited.iterrows():
                        idx_matches = live_db[live_db["Admission Application Number"] == row_edit["Admission Application Number"]].index
                        if not idx_matches.empty:
                            for match_idx in idx_matches:
                                live_db.at[match_idx, "Application Enrollment No."] = row_edit["Application Enrollment No."]
                                live_db.at[match_idx, "Enrollment No."] = row_edit["Enrollment No."]
                    save_live_data(live_db)
                    st.success("✅ विश्वविद्यालय नामांकन नंबर सफलतापूर्वक अपडेट हो गया है!")
                    st.rerun()

        # ----------------------------------------------------------------------
        # P4: PANEL SCHOLARSHIP MODULE
        # ----------------------------------------------------------------------
        elif current_panel_id == "P4":
            st.header(f"💰 {get_panel_title('P4')} (Portal & Category Matrix Control)")
            if "Scholarship Status" not in live_db.columns: 
                live_db["Scholarship Status"] = "Not Applied"
            
            if live_db.empty:
                st.warning("⚠️ डेटाबेस वर्तमान में खाली है। कृपया पहले Panel 1 (Entry) से छात्र लोड करें।")
            else:
                selected_category = st.selectbox("Category (वर्ग) चुनें:", ["All"] + sorted(list(set(live_db["Category"].dropna().astype(str)))))
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
                    st.success("✅ छात्रवृत्ति मैट्रिक्स सफलतापूर्वक अपडेट हो गया है!")
                    st.rerun()




