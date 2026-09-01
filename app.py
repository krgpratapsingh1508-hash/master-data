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
    .header-text h3 { margin: 0 !important; padding: 0 !important; color: #FF5733; }
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
            <h3>ॐ गुरुवर्य नमः</h3>
            <h1>Permanent Shared Live Database System</h1>
        </div>
    </div>
""", unsafe_allow_html=True)

DB_FILE = "shared_student_database.csv"
CRED_FILE = "user_credentials.json"
MAP_FILE = "column_mapping_schema.json"
PANEL_NAME_FILE = "panel_names_schema.json"

# 15 पैनल्स के हिसाब से 15 सेपरेटेड क्रेडेंशियल्स की मास्टर डिक्शनरी
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

# डिफ़ॉल्ट 15 पैनल्स की डिक्शनरी मैपिंग (P1 से P15)
DEFAULT_PANELS = {
    "P1": "Panal entry", "P2": "Panal admission", "P3": "Panal enrollment",
    "P4": "Panal scholarship", "P5": "Panal result", "P6": "Panal promotion",
    "P7": "Panal foil", "P8": "Panal cce record", "P9": "Panal P9 Extension",
    "P10": "Panal P10 Extension", "P11": "Panal P11 Extension", "P12": "Panal P12 Extension",
    "P13": "Panal merge", "P14": "Panal viewer", "P15": "Panel admin"
}

# मास्टर कॉलम्स सूची
DEFAULT_COLUMNS = [
    "Admission Year", "Admission Session", "Eligibility Name", "Admission Application Number",
    "Admission Date", "Unique ID", "Roll No.", "Application Enrollment No.",
    "Enrollment No.", "Student Name", "Father Name", "Mother Name", "Date of Birth",
    "Category", "Subject Code", "Subject", "Duration", "Mobile Number", "Email ID", "Address", "Status",
    "Current Year"
]

# डेटा लोडर्स और सेवर्स फंक्शन्स
def load_credentials():
    if os.path.exists(CRED_FILE):
        try:
            with open(CRED_FILE, "r") as f: return json.load(f)
        except: return DEFAULT_CREDENTIALS.copy()
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

# स्टेट मैनेजमेंट इनिशियलाइजेशन
if "credentials" not in st.session_state: st.session_state.credentials = load_credentials()
if "panel_names" not in st.session_state: st.session_state.panel_names = load_panel_names()
if "column_mappings" not in st.session_state: st.session_state.column_mappings = load_column_mappings()
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
# Phase 1: Login Block Control
# ==========================================================
if st.session_state.user_role is None:
    # नोटिस बोर्ड रेंडर स्ट्रक्चर
    st.markdown("""
        <div class="notice-board">
            <div class="notice-title">📢 कॉलेज सूचना पटल (Official Notice Board)</div>
            <p>1. यह एक पूर्णतः सुरक्षित, लाइव क्लाउड स्टूडेंट डेटाबेस मैनेजमेंट सिस्टम है।</p>
            <p>2. डेटा प्रविष्टि, सुधार, स्कॉलरशिप वेरिफिकेशन या परीक्षा परिणाम अपडेट करने के लिए अधिकृत यूजर क्रेडेंशियल्स का उपयोग करें।</p>
            <p>3. बिना लॉगिन के डेटाबेस तक पहुँच पूर्णतः प्रतिबंधित है। किसी भी समस्या के लिए सुपर-एडमिन से संपर्क करें।</p>
        </div>
    """, unsafe_allow_html=True)
    
    # लॉगिन विंडो ट्रिगर बटन
    if not st.session_state.show_login_form:
        if st.button("🔐 Click Here to Open Secure Login System", type="primary", use_container_width=True):
            st.session_state.show_login_form = True
            st.rerun()
            
    if st.session_state.show_login_form:
        st.markdown("---")
        st.subheader("🔒 Enter Secure Gateway Credentials")
        col_l1, col_l2 = st.columns(2)
        
        with col_l1:
            # स्क्रॉल सिलेक्शन बोर्ड ड्रॉपडाउन
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
    
    # हेड बार सेटिंग्स
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

    # क्रेडेंशियल्स के अनुसार अलग-अलग सेपरेटेड पैनल विज़िबिलिटी रूल्स
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

    # नेविгеटर मॉड्यूल लोड
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
            if live_db.empty: st.warning("⚠️ डेटाबेस वर्तमान में खाली है।")
            else:
                col_f1, col_f2, col_f3 = st.columns(3)
                with col_f1: selected_year = st.selectbox("Admission Year चुनें:", ["All"] + sorted(list(set(live_db["Admission Year"].dropna().astype(str)))))
                with col_f2: selected_session = st.selectbox("Admission Session चुनें:", ["All"] + sorted(list(set(live_db["Admission Session"].dropna().astype(str)))))
                with col_f3: selected_status = st.selectbox("Current Status चुनें:", ["All"] + sorted(list(set(live_db["Status"].dropna().astype(str)))))
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
                    st.success("✅ एडमिशन डेटाबेस सफलतापूर्वक सिंक हो गया है!")

        # ----------------------------------------------------------------------
        # P3: PANEL ENROLLMENT MODULE
        # ----------------------------------------------------------------------
        elif current_panel_id == "P3":
            st.header(f"📑 {get_panel_title('P3')} (University Enrollment Manager)")
            if live_db.empty: st.warning("⚠️ डेटाबेस वर्तमान में खाली है।")
            else:
                selected_subject = st.selectbox("Subject (विषय) चुनें:", ["All"] + sorted(list(set(live_db["Subject"].dropna().astype(str)))))
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
                    st.success("✅ विश्वविद्यालय नामांकन नंबर सफलतापूर्वक अपडेट हो गया है!")

                # ----------------------------------------------------------------------
        # P4: PANEL SCHOLARSHIP MODULE
        # ----------------------------------------------------------------------
        elif current_panel_id == "P4":
            st.header(f"💰 {get_panel_title('P4')} (Portal & Category Matrix Control)")
            
            # यदि डेटाबेस में 'Scholarship Status' कॉलम नहीं है, तो उसे इनिशियलाइज़ करें
            if "Scholarship Status" not in live_db.columns: 
                live_db["Scholarship Status"] = "Not Applied"
                
            if live_db.empty: 
                st.warning("⚠️ डेटाबेस वर्तमान में खाली है। कृपया पहले Panel 1 (Entry) के माध्यम से छात्रों का डेटा जोड़ें।")
            else:
                st.subheader("🔍 Filter Scholarship Candidates")
                col_f1, col_f2 = st.columns(2)
                
                with col_f1:
                    unique_categories = sorted(list(set(live_db["Category"].dropna().astype(str))))
                    selected_category = st.selectbox("Category (वर्ग) चुनें:", ["All"] + [cat for cat in unique_categories if cat.strip() != ""])
                    
                with col_f2:
                    unique_scholarship_status = ["All", "Not Applied", "Applied", "Sanctioned", "Disbursed", "Rejected"]
                    selected_sch_status = st.selectbox("Scholarship Status चुनें:", unique_scholarship_status)

                # डेटा फ़िल्टरिंग लॉजिक
                filtered_scholarship = live_db.copy()
                if selected_category != "All": 
                    filtered_scholarship = filtered_scholarship[filtered_scholarship["Category"] == selected_category]
                if selected_sch_status != "All": 
                    filtered_scholarship = filtered_scholarship[filtered_scholarship["Scholarship Status"] == selected_sch_status]

                st.write(f"फ़िल्टर के आधार पर कुल छात्र संख्या: **{len(filtered_scholarship)}**")

                # इंटरैक्टिव डेटा ग्रिड बोर्ड
                st.subheader("✏️ Track & Update Scholarship Verification Matrix")
                st.info("💡 नीचे दी गई ग्रिड में आप सीधे छात्रों का 'Scholarship Status' ड्रापडाउन मेनू से बदल सकते हैं।")

                scholarship_display_cols = ["Admission Application Number", "Unique ID", "Student Name", "Category", "Scholarship Status"]
                display_cols = [c for c in scholarship_display_cols if c in filtered_scholarship.columns]
                render_df = filtered_scholarship[display_cols].copy()
                render_df.insert(0, "S.No.", range(1, len(render_df) + 1))
                
                edited_scholarship_df = st.data_editor(
                    render_df, 
                    use_container_width=True, 
                    disabled=["S.No.", "Admission Application Number", "Unique ID", "Student Name", "Category"], 
                    column_config={
                        "Scholarship Status": st.column_config.SelectboxColumn(
                            "Scholarship Status", 
                            options=["Not Applied", "Applied", "Sanctioned", "Disbursed", "Rejected"],
                            required=True
                        )
                    }, 
                    key="scholarship_live_editor", 
                    hide_index=True
                )
                
                # डेटा सिंकिंग और मुख्य CSV में सुरक्षित सेविंग लॉजिक
                if st.button("Save & Sync Scholarship Matrix", type="primary", use_container_width=True):
                    try:
                        clean_edited = edited_scholarship_df.drop(columns=["S.No."])
                        for _, row_edit in clean_edited.iterrows():
                            idx_matches = live_db[live_db["Admission Application Number"] == row_edit["Admission Application Number"]].index
                            if not idx_matches.empty:
                                for match_idx in idx_matches:
                                    live_db.at[match_idx, "Scholarship Status"] = row_edit["Scholarship Status"]
                        
                        save_live_data(live_db)
                        st.success("✅ छात्रवृत्ति मैट्रिक्स (Scholarship Portal Status) सफलतापूर्वक सिंक और अपडेट हो गया है!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"डेटा अपडेट करने में तकनीकी त्रुटि आई: {e}")

                # त्वरित स्कॉलरशिप एनालिटिक्स समरी काउंटर्स
                st.markdown("---")
                st.subheader("📊 Category & Portal Summary Analytics")
                col_c1, col_c2, col_c3, col_c4 = st.columns(4)
                
                with col_c1:
                    st.metric("Total Students Registered", len(live_db))
                with col_c2:
                    applied_count = len(live_db[live_db["Scholarship Status"] == "Applied"])
                    st.metric("Applications Verification Pending", applied_count)
                with col_c3:
                    sanctioned_count = len(live_db[live_db["Scholarship Status"].isin(["Sanctioned", "Disbursed"])])
                    st.metric("Total Approved / Sanctioned", sanctioned_count)
                with col_c4:
                    reserved_count = len(live_db[live_db["Category"].str.upper().isin(["OBC", "SC", "ST"])])
                    st.metric("Total Eligible Reserved Category Candidates", reserved_count)
        # ----------------------------------------------------------------------
        # P5: PANEL RESULT MODULE
        # ----------------------------------------------------------------------
        elif current_panel_id == "P5":
            st.header(f"📊 {get_panel_title('P5')} (Tabulation Register & Exam Controller)")
            
            # यदि डेटाबेस में परिणाम से संबंधित डायनेमिक कॉलम्स नहीं हैं, तो उन्हें इनिशियलाइज़ करें
            result_dynamic_fields = ["Marks Obtained", "Result Status", "Exam Remarks"]
            for field in result_dynamic_fields:
                if field not in live_db.columns:
                    live_db[field] = ""

            if live_db.empty:
                st.warning("⚠️ डेटाबेस वर्तमान में खाली है। कृपया पहले Panel 1 (Entry) के माध्यम से छात्रों का डेटा जोड़ें।")
            else:
                st.subheader("🔍 Search & Filter Student Examination Records")
                col_f1, col_f2 = st.columns(2)
                
                with col_f1:
                    unique_subjects = sorted(list(set(live_db["Subject"].dropna().astype(str))))
                    selected_subject = st.selectbox("Subject (विषय) फ़िल्टर:", ["All"] + [sub for sub in unique_subjects if sub.strip() != ""])
                    
                with col_f2:
                    unique_result_status = ["All", "Pass", "Fail", "ATKT", "Withheld", "Absent", "Pending (Not Declared)"]
                    selected_res_status = st.selectbox("Result Status फ़िल्टर:", unique_result_status)

                # डेटा फ़िल्टरिंग लॉजिक
                filtered_result = live_db.copy()
                if selected_subject != "All":
                    filtered_result = filtered_result[filtered_result["Subject"] == selected_subject]
                    
                if selected_res_status != "All":
                    if selected_res_status == "Pending (Not Declared)":
                        filtered_result = filtered_result[filtered_result["Result Status"].str.strip() == ""]
                    else:
                        filtered_result = filtered_result[filtered_result["Result Status"] == selected_res_status]

                st.write(f"फ़िल्टर के आधार पर कुल छात्र संख्या: **{len(filtered_result)}**")

                # इंटरैक्टिव डेटा एडिटर ग्रिड
                st.subheader("✏️ Bulk Entry / Tabulation of Marks & Results Status")
                st.info("💡 नीचे दी गई ग्रिड में आप सीधे छात्रों के 'Marks Obtained', 'Result Status' और 'Exam Remarks' को प्रविष्ट कर सकते हैं।")

                result_display_cols = ["Admission Application Number", "Roll No.", "Enrollment No.", "Student Name", "Subject", "Marks Obtained", "Result Status", "Exam Remarks"]
                display_cols = [c for c in result_display_cols if c in filtered_result.columns]
                render_df = filtered_result[display_cols].copy()
                render_df.insert(0, "S.No.", range(1, len(render_df) + 1))

                edited_res_df = st.data_editor(
                    render_df,
                    use_container_width=True,
                    disabled=["S.No.", "Admission Application Number", "Roll No.", "Enrollment No.", "Student Name", "Subject"],
                    column_config={
                        "Marks Obtained": st.column_config.TextColumn(
                            "Marks Obtained",
                            help="छात्र द्वारा प्राप्त अंक प्रविष्ट करें (e.g., 78/100)",
                            max_chars=10
                        ),
                        "Result Status": st.column_config.SelectboxColumn(
                            "Result Status",
                            help="परीक्षा परिणाम की वर्तमान स्थिति चुनें",
                            options=["Pass", "Fail", "ATKT", "Withheld", "Absent"],
                            required=False,
                        ),
                        "Exam Remarks": st.column_config.TextColumn(
                            "Exam Remarks",
                            help="कोई विशेष टिप्पणी जैसे Grace, UFM आदि दर्ज करें"
                        )
                    },
                    key="result_live_editor",
                    hide_index=True
                )

                # डेटा सिंकिंग और मुख्य CSV में सुरक्षित सेविंग लॉजिक
                if st.button("Save & Sync Tabulation Register", type="primary", use_container_width=True):
                    try:
                        clean_edited = edited_res_df.drop(columns=["S.No."])
                        for _, row_edit in clean_edited.iterrows():
                            idx_matches = live_db[live_db["Admission Application Number"] == row_edit["Admission Application Number"]].index
                            if not idx_matches.empty:
                                for match_idx in idx_matches:
                                    live_db.at[match_idx, "Marks Obtained"] = row_edit["Marks Obtained"]
                                    live_db.at[match_idx, "Result Status"] = row_edit["Result Status"]
                                    live_db.at[match_idx, "Exam Remarks"] = row_edit["Exam Remarks"]

                        save_live_data(live_db)
                        st.success("✅ परीक्षा परिणाम पंजी (Tabulation Register) सफलतापूर्वक सिंक और अपडेट हो गई है!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"डेटा अपडेट करने में तकनीकी त्रुटि आई: {e}")

                # परिणाम आधारित एनालिटिक्स समरी काउंटर्स
                st.markdown("---")
                st.subheader("📊 Examination Result Analytics Summary")
                col_c1, col_c2, col_c3, col_c4 = st.columns(4)
                
                with col_c1:
                    st.metric("Total Students Appeared", len(live_db))
                with col_c2:
                    pass_count = len(live_db[live_db["Result Status"] == "Pass"])
                    st.metric("Total Passed Students", pass_count)
                with col_c3:
                    atkt_count = len(live_db[live_db["Result Status"] == "ATKT"])
                    st.metric("Students with ATKT/Backlog", atkt_count)
                with col_c4:
                    not_declared = len(live_db[live_db["Result Status"].str.strip() == ""])
                    st.metric("Pending Results (Filing Left)", not_declared)
        # ----------------------------------------------------------------------
        # P6: PANEL PROMOTION MODULE
        # ----------------------------------------------------------------------
        elif current_panel_id == "P6":
            st.header(f"📈 {get_panel_title('P6')} (Academic Year Batch Progression Control)")
            
            # यदि डेटाबेस में प्रमोशन से संबंधित डायनेमिक कॉलम नहीं है, तो उसे इनिशियलाइज़ करें
            if "Promotion Status" not in live_db.columns:
                live_db["Promotion Status"] = "Eligible"

            if live_db.empty:
                st.warning("⚠️ डेटाबेस वर्तमान में खाली है। कृपया पहले Panel 1 (Entry) के माध्यम से छात्रों का डेटा जोड़ें।")
            else:
                st.subheader("🔍 Filter & Process Batch Promotion")
                col_f1, col_f2 = st.columns(2)
                
                with col_f1:
                    unique_years = sorted(list(set(live_db["Current Year"].dropna().astype(str))))
                    selected_curr_year = st.selectbox("Current Year (वर्तमान शैक्षणिक वर्ष) फ़िल्टर:", ["All"] + [cy for cy in unique_years if cy.strip() != ""])
                    
                with col_f2:
                    unique_promo_status = ["All", "Eligible", "Promoted", "Detained (Year Back)", "Course Completed"]
                    selected_p_status = st.selectbox("Promotion Status फ़िल्टर:", unique_promo_status)

                # डेटा फ़िल्टरिंग लॉजिक
                filtered_promotion = live_db.copy()
                if selected_curr_year != "All":
                    filtered_promotion = filtered_promotion[filtered_promotion["Current Year"] == selected_curr_year]
                if selected_p_status != "All":
                    filtered_promotion = filtered_promotion[filtered_promotion["Promotion Status"] == selected_p_status]

                st.write(f"फ़िल्टर के आधार पर कुल छात्र संख्या: **{len(filtered_promotion)}**")

                # इंटरैक्टिव डेटा एडिटर ग्रिड
                st.subheader("✏️ Bulk Track & Update Batch Progression Status")
                st.info("💡 नीचे दी गई ग्रिड में आप प्रमोट होने वाले छात्रों का 'Promotion Status' और 'Status' फ़ील्ड अपडेट कर सकते हैं।")

                promotion_display_cols = ["Admission Application Number", "Roll No.", "Student Name", "Current Year", "Status", "Promotion Status"]
                display_cols = [c for c in promotion_display_cols if c in filtered_promotion.columns]
                render_df = filtered_promotion[display_cols].copy()
                render_df.insert(0, "S.No.", range(1, len(render_df) + 1))

                edited_promo_df = st.data_editor(
                    render_df,
                    use_container_width=True,
                    disabled=["S.No.", "Admission Application Number", "Roll No.", "Student Name", "Current Year"],
                    column_config={
                        "Status": st.column_config.SelectboxColumn(
                            "Academic Status",
                            help="छात्र का रेगुलर या एक्स-स्टूडेंट स्टेटस चुनें",
                            options=["Regular Student", "Regular", "EX-STUDENT", "Pass", "Pending"],
                            required=True,
                        ),
                        "Promotion Status": st.column_config.SelectboxColumn(
                            "Promotion Progress Status",
                            help="छात्र के प्रमोशन चक्र की वर्तमान स्थिति चुनें",
                            options=["Eligible", "Promoted", "Detained (Year Back)", "Course Completed"],
                            required=True,
                        )
                    },
                    key="promotion_live_editor",
                    hide_index=True
                )

                # डेटा सिंकिंग और मुख्य CSV में सुरक्षित सेविंग लॉजिक
                if st.button("Save & Sync Promotion Register", type="primary", use_container_width=True):
                    try:
                        clean_edited = edited_promo_df.drop(columns=["S.No."])
                        for _, row_edit in clean_edited.iterrows():
                            idx_matches = live_db[live_db["Admission Application Number"] == row_edit["Admission Application Number"]].index
                            if not idx_matches.empty:
                                for match_idx in idx_matches:
                                    live_db.at[match_idx, "Status"] = row_edit["Status"]
                                    live_db.at[match_idx, "Promotion Status"] = row_edit["Promotion Status"]

                        save_live_data(live_db)
                        st.success("✅ छात्र बैच प्रमोशन पंजी (Promotion Register) सफलतापूर्वक सिंक और अपडेट हो गई है!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"डेटा अपडेट करने में तकनीकी त्रुटि आई: {e}")

                # प्रमोशन आधारित एनालिटिक्स समरी काउंटर्स
                st.markdown("---")
                st.subheader("📊 Batch Progression Analytics Summary")
                col_c1, col_c2, col_c3, col_c4 = st.columns(4)
                
                with col_c1:
                    st.metric("Total Enrolled Batches", len(live_db))
                with col_c2:
                    promoted_count = len(live_db[live_db["Promotion Status"] == "Promoted"])
                    st.metric("Successfully Promoted (Next Class)", promoted_count)
                with col_c3:
                    detained_count = len(live_db[live_db["Promotion Status"] == "Detained (Year Back)"])
                    st.metric("Detained Students (Year Back)", detained_count)
                with col_c4:
                    eligible_count = len(live_db[live_db["Promotion Status"] == "Eligible"])
                    st.metric("Awaiting Progression Decision", eligible_count)
        # ----------------------------------------------------------------------
        # P7: PANEL FOIL SHEET GENERATOR MODULE
        # ----------------------------------------------------------------------
        elif current_panel_id == "P7":
            st.header(f"🖨️ {get_panel_title('P7')} (University CCE Foil Sheet Generator)")
            st.write("Institute of Law, Govt. Kamlaraja Girls Post-Graduate Autonomous College, Gwalior (M.P.)")

            college_name = "GOVT. K.R.G. POST-GRADUATE AUTONOMOUS COLLEGE, GWALIOR (M.P.)"

            if live_db.empty:
                st.warning("⚠️ डेटाबेस वर्तमान में खाली है। कृपया पहले Panel 1 (Entry) के माध्यम से छात्रों का डेटा जोड़ें।")
            else:
                unique_subjects = sorted(list(set(live_db['Subject'].dropna().astype(str).str.strip())))
                unique_subjects = [sub for sub in unique_subjects if sub != ""]
                selected_subject = st.selectbox("📚 Select Subject (विषय चुनें):", options=["All Subjects"] + unique_subjects, key="cce_sub")

                year_sem_options = [
                    "1 Semester", "2 Semester", "3 Semester", "4 Semester", "5 Semester", "6 Semester",
                    "7 Semester", "8 Semester", "9 Semester", "10 Semester", "11 Semester", "12 Semester",
                    "1 year", "2 year", "3 year", "4 year", "5 year", "6 year"
                ]
                
                def on_cce_param_change(): 
                    st.session_state.cce_foil_generated = False

                chosen_option = st.selectbox("📆 Select Semester / Year:", year_sem_options, key="cce_year_sem", on_change=on_cce_param_change)

                mapping_logic = {
                    "1 Semester": "1 year", "2 Semester": "1 year", "1 year": "1 year",
                    "3 Semester": "2 year", "4 Semester": "2 year", "2 year": "2 year",
                    "5 Semester": "3 year", "6 Semester": "3 year", "3 year": "3 year",
                    "7 Semester": "4 year", "8 Semester": "4 year", "4 year": "4 year",
                    "9 Semester": "5 year", "10 Semester": "5 year", "5 year": "5 year",
                    "11 Semester": "6 year", "12 Semester": "6 year", "6 year": "6 year"
                }
                target_year_text = mapping_logic[chosen_option]
                display_subject_heading = selected_subject.upper() if selected_subject != "All Subjects" else "STUDENT LIST"
                exam_info = f"Examination :- CCE                                             {display_subject_heading} {chosen_option.upper()}"

                st.subheader("📊 Live Candidates Verification Sheet")
                preview_db = live_db.copy()
                if selected_subject != "All Subjects":
                    preview_db = preview_db[preview_db['Subject'].str.strip() == selected_subject]
                
                preview_render = preview_db[["Roll No.", "Student Name", "Subject Code", "Subject", "Status", "Current Year"]].copy()
                st.dataframe(preview_render, use_container_width=True, hide_index=True)

                if st.button("Generate Foil Sheets Now", use_container_width=True, type="primary"):
                    st.session_state.cce_foil_generated = True
                    st.rerun()

                # --- foil processing database calculation engine ---
                if st.session_state.cce_foil_generated:
                    regular_records = []
                    ex_student_records = []
                    has_missing_roll_and_is_first_year_regular = False 
                    detected_subject_code = ""

                    years_series = pd.to_numeric(live_db["Admission Year"], errors='coerce')
                    max_year = int(years_series.max()) if not years_series.dropna().empty else 2026

                    for _, row in live_db.iterrows():
                        roll = str(row.get('Roll No.', '')).strip()
                        name = str(row.get('Student Name', '')).strip()
                        status = str(row.get('Status', '')).strip().upper()
                        current_year_val = str(row.get('Current Year', '')).strip().lower()
                        student_sub = str(row.get('Subject', '')).strip()
                        sub_code = str(row.get('Subject Code', '')).strip()
                        
                        try: adm_year = int(float(str(row.get('Admission Year', '0'))))
                        except: adm_year = 0
                        try: course_duration = int(float(str(row.get('Duration', '6'))))
                        except: course_duration = 6

                        if selected_subject != "All Subjects" and student_sub != selected_subject: continue
                        if sub_code and sub_code.lower() != "nan" and detected_subject_code == "": detected_subject_code = sub_code

                        if status == "EX-STUDENT":
                            is_ex_match = False
                            try: gap_needed = int(target_year_text.split()[0])
                            except: gap_needed = 1
                                
                            if gap_needed <= course_duration and adm_year == (max_year - gap_needed): is_ex_match = True
                            if is_ex_match and roll and roll.lower() != "nan" and roll != "": ex_student_records.append(roll)
                            continue

                        if status in ['REGULAR STUDENT', 'REGULAR']:
                            is_regular_year_match = False
                            clean_target_text = target_year_text.strip().lower()
                            
                            if clean_target_text in current_year_val or current_year_val in clean_target_text:
                                is_regular_year_match = True
                            elif current_year_val in ["", "ex-student", "nan"]:
                                calculated_gap = max_year - adm_year
                                if clean_target_text == "1 year" and calculated_gap == 0: is_regular_year_match = True
                                elif clean_target_text == "2 year" and calculated_gap == 1: is_regular_year_match = True
                                elif clean_target_text == "3 year" and calculated_gap == 2: is_regular_year_match = True
                                elif clean_target_text == "4 year" and calculated_gap == 3: is_regular_year_match = True
                                elif clean_target_text == "5 year" and calculated_gap == 4: is_regular_year_match = True
                                elif clean_target_text == "6 year" and calculated_gap == 5: is_regular_year_match = True

                            if is_regular_year_match:
                                if clean_target_text == "1 year" and (not roll or roll.lower() == "nan" or roll == ""):
                                    has_missing_roll_and_is_first_year_regular = True
                                    regular_records.append(name if name else "[Unknown Name]")
                                else:
                                    if roll and roll.lower() != "nan" and roll != "": regular_records.append(roll)
                    final_records_list = sorted(list(set(ex_student_records))) + sorted(list(set(regular_records)))

                    # --- print canvas renderer ---
                    if final_records_list:
                        st.subheader("🖨️ Generated Visual CCE Foil Sheets")
                        dynamic_th_label = "Roll No. / Student Name" if has_missing_roll_and_is_first_year_regular else "Roll No."

                        def generate_cce_html_block(items, start_idx, foil_label):
                            paper_code_display = f"Paper Code: <b>{detected_subject_code}</b>" if detected_subject_code else "Paper Code...................."
                            block = f"""
                            <div class="foil-unit">
                                <div class="top-fields"><div></div><div>{paper_code_display}</div></div>
                                <div class="top-fields" style="margin-top: 5px;"><div></div><div>Bundle No....................</div></div>
                                <div class="header-box">{college_name}</div>
                                <div class="sub-box exam-right">{exam_info}</div>
                                <div class="sub-box">Subject: {selected_subject if selected_subject != 'All Subjects' else '......................'} Paper.........................</div>
                                <div class="marks-info"><div>Max. Marks: ...................</div><div>Min. Pass Marks: ...................</div></div>
                                <div class="foil-title">{foil_label}</div>
                                <table style="width:100%; border-collapse:collapse; margin-top:10px;">
                                    <tr><th style="border:1px solid black; padding:4px; width: 8%;">1</th><th style="border:1px solid black; padding:4px; width: 30%;" colspan="3">2</th></tr>
                                    <tr><th style="border:1px solid black; padding:4px;" rowspan="2">Code No.</th><th style="border:1px solid black; padding:4px;" rowspan="2">{dynamic_th_label}</th><th style="border:1px solid black; padding:4px;" colspan="2">Marks Obtained</th></tr>
                                    <tr><th style="border:1px solid black; padding:4px; width: 15%;">In Figures</th><th style="border:1px solid black; padding:4px; width: 45%;">In Words</th></tr>
                            """
                            for idx_foil, item_val in enumerate(items, start=start_idx):
                                block += f"<tr><td style='border:1px solid black; padding:4px; text-align:center;'><b>{idx_foil}</b></td><td style='border:1px solid black; padding:4px;'>{item_val}</td><td style='border:1px solid black; padding:4px;'></td><td style='border:1px solid black; padding:4px;'></td></tr>"
                            # शीट को व्यवस्थित करने के लिए बची हुई 35 तक की खाली पंक्तियाँ जोड़ना
                            for k in range(len(items) + start_idx, 36 + start_idx):
                                block += "<tr><td style='border:1px solid black; padding:4px;'>&nbsp;</td><td style='border:1px solid black; padding:4px;'>&nbsp;</td><td style='border:1px solid black; padding:4px;'>&nbsp;</td><td style='border:1px solid black; padding:4px;'>&nbsp;</td></tr>"
                            
                            block += f"""
                                </table>
                                <div class="note" style="font-size:11px; margin-top:10px; line-height:1.3;">
                                    <b>Note:</b> Roll Number and Marks awarded to the candidate may be entered under respective columns very carefully. Marks and Roll Number should be legible. These may be checked again to ensure that no mistake remains.
                                </div>
                                <div class="footer-fields" style="margin-top:20px; font-weight:bold; font-size:13px; display:flex; justify-content:between;">
                                    <div>Date: ___/___/2026</div>
                                    <div style="text-align:right;">Signature of Examiner......................................</div>
                                </div>
                            </div>
                            """
                            return block

                        html_blocks_compiled = ""
                        chunk_size = 35
                        total_records = len(final_records_list)
                        chunks = [final_records_list[i:i + chunk_size] for i in range(0, total_records, chunk_size)]
                        
                        for index, chunk_data in enumerate(chunks):
                            start_num = (index * chunk_size) + 1
                            if index % 2 == 0:
                                html_blocks_compiled += '<div class="foil-row-wrapper">'
                            
                            html_blocks_compiled += generate_cce_html_block(chunk_data, start_num, f"FOIL - PAGE {index+1}")
                            
                            if index % 2 == 1 or index == len(chunks) - 1:
                                if index % 2 == 0 and index == len(chunks) - 1:
                                    html_blocks_compiled += '<div class="foil-unit" style="border:none; background:transparent;"></div>'
                                html_blocks_compiled += '</div>'

                        html_style = """
                        <style>
                        .foil-row-wrapper { 
                            display: flex; 
                            justify-content: space-between; 
                            gap: 20px; 
                            width: 1100px; 
                            margin: 0 auto 30px auto; 
                            background: white; 
                            page-break-after: always; 
                        }
                        .foil-unit { 
                            width: 49%; 
                            border: 1px solid black; 
                            padding: 15px; 
                            box-sizing: border-box; 
                            background: white; 
                        }
                        .top-fields { 
                            display: flex; 
                            justify-content: space-between; 
                            font-weight: bold; 
                            font-size: 13px; 
                        }
                        .header-box { 
                            text-align: center; 
                            border-top: 2px solid black; 
                            border-bottom: 2px solid black; 
                            padding: 6px 0; 
                    margin-top: 8px; 
                            font-weight: bold; 
                            font-size: 15px; 
                        }
                        .sub-box { 
                            border-bottom: 2px solid black; 
                            padding: 5px 0; 
                            font-size: 12px; 
                            font-weight: bold; 
                        }
                        .exam-right { 
                            text-align: right; 
                        }
                        .marks-info { 
                            display: flex; 
                            justify-content: space-between; 
                            padding: 5px 0; 
                            font-weight: bold; 
                            border-bottom: 2px solid black; 
                            font-size: 12px; 
                        }
                        .foil-title { 
                            text-align: center; 
                            font-weight: bold; 
                            font-size: 16px; 
                            margin: 10px 0; 
                        }
                        @media print { 
                            .print-hide { display: none !important; } 
                        }
                        </style>
                        """
                        
                        full_html = f"""
                        <html>
                        <head>{html_style}</head>
                        <body>
                            <div class="print-hide" style="text-align: center; margin-bottom: 20px;">
                                <button onclick="window.print()" style="background:#FF5733; color:white; border:none; padding:12px 25px; border-radius:5px; cursor:pointer; font-weight:bold; font-size:14px; box-shadow: 0px 4px 6px rgba(0,0,0,0.1);">
                                    🖨️ Direct Print All Foil Sheets
                                </button>
                            </div>
                            <div id="master-container">{html_blocks_compiled}</div>
                        </body>
                        </html>
                        """
                        st.components.v1.html(full_html, height=1500, scrolling=True)
                    else:
                        st.error("❌ चुने गए विषय और वर्ष के आधार पर कोई योग्य छात्र रिकॉर्ड नहीं मिला।")
        # ----------------------------------------------------------------------
        # P8: PANEL CCE RECORD MODULE
        # ----------------------------------------------------------------------
        elif current_panel_id == "P8":
            st.header(f"📋 {get_panel_title('P8')} (Internal Assessment Marks Ledger)")
            
            # Initialize dynamic fields for CCE records if they do not exist in the database
            cce_dynamic_fields = ["CCE Marks Obtained", "CCE Attendance Status"]
            for field in cce_dynamic_fields:
                if field not in live_db.columns:
                    live_db[field] = ""

            if live_db.empty:
                st.warning("⚠️ डेटाबेस वर्तमान में खाली है। कृपया पहले Panel 1 (Entry) के माध्यम से छात्रों का डेटा जोड़ें।")
            else:
                st.subheader("🔍 Filter Records for CCE Entry")
                col_f1, col_f2 = st.columns(2)
                
                with col_f1:
                    unique_subjects = sorted(list(set(live_db["Subject"].dropna().astype(str))))
                    selected_subject = st.selectbox("Subject (विषय) फ़िल्टर करें:", ["All"] + [sub for sub in unique_subjects if sub.strip() != ""])
                    
                with col_f2:
                    unique_cce_status = ["All Students", "Pending Marks Entry Only", "Marks Entered Already"]
                    selected_cce_filter = st.selectbox("CCE Entry Status फ़िल्टर:", unique_cce_status)

                # Data filtering logic execution
                filtered_cce = live_db.copy()
                if selected_subject != "All":
                    filtered_cce = filtered_cce[filtered_cce["Subject"] == selected_subject]
                    
                if selected_cce_filter == "Pending Marks Entry Only":
                    filtered_cce = filtered_cce[filtered_cce["CCE Marks Obtained"].str.strip() == ""]
                elif selected_cce_filter == "Marks Entered Already":
                    filtered_cce = filtered_cce[filtered_cce["CCE Marks Obtained"].str.strip() != ""]

                st.write(f"फ़िल्टर के आधार पर कुल छात्र संख्या: **{len(filtered_cce)}**")

                st.subheader("✏️ Bulk Entry Room: CCE Internal Continuous Marks Board")
                st.info("💡 नीचे दी गई ग्रिड में आप सीधे छात्रों के 'CCE Marks Obtained' (अंक) भर सकते हैं तथा उनका एब्सेंट/प्रेजेंट स्टेटस बदल सकते हैं।")

                # Arrangement of visible display columns for CCE entries
                cce_display_cols = ["Admission Application Number", "Roll No.", "Student Name", "Subject Code", "Subject", "CCE Marks Obtained", "CCE Attendance Status"]
                display_cols = [c for c in cce_display_cols if c in filtered_cce.columns]
                render_df = filtered_cce[display_cols].copy()
                render_df.insert(0, "S.No.", range(1, len(render_df) + 1))

                # Interactive data editor grid configuration
                edited_cce_df = st.data_editor(
                    render_df,
                    use_container_width=True,
                    disabled=["S.No.", "Admission Application Number", "Roll No.", "Student Name", "Subject Code", "Subject"],
                    column_config={
                        "CCE Marks Obtained": st.column_config.TextColumn(
                            "CCE Marks (Max 20/30)",
                            help="आंतरिक मूल्यांकन अंक दर्ज करें (e.g., 18)",
                            max_chars=5
                        ),
                        "CCE Attendance Status": st.column_config.SelectboxColumn(
                            "Attendance Status",
                            help="CCE परीक्षा के समय छात्र की उपस्थिति स्थिति चुनें",
                            options=["Present", "Absent", "Detained"],
                            required=False,
                        )
                    },
                    key="cce_record_live_editor",
                    hide_index=True
                )

                # Data synchronization and secure local CSV storage logic
                if st.button("Save & Sync CCE Assessment Ledger", type="primary", use_container_width=True):
                    try:
                        clean_edited = edited_cce_df.drop(columns=["S.No."])
                        for _, row_edit in clean_edited.iterrows():
                            idx_matches = live_db[live_db["Admission Application Number"] == row_edit["Admission Application Number"]].index
                            if not idx_matches.empty:
                                for match_idx in idx_matches:
                                    live_db.at[match_idx, "CCE Marks Obtained"] = row_edit["CCE Marks Obtained"]
                                    live_db.at[match_idx, "CCE Attendance Status"] = row_edit["CCE Attendance Status"]

                        save_live_data(live_db)
                        st.success("✅ सीसीई आंतरिक मूल्यांकन पंजी (CCE Assessment Register) सफलतापूर्वक मास्टर फ़ाइल में सेव हो गया है!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"डेटाबेस सिंक करने में त्रुटि उत्पन्न हुई: {e}")

                # CCE stats and analytics summary dashboard cards
                st.markdown("---")
                st.subheader("📊 CCE Assessment Analytics Dashboard")
                col_c1, col_c2, col_c3 = st.columns(3)
                
                with col_c1: 
                    st.metric("Total Students Eligible for CCE", len(live_db))
                with col_c2:
                    entered_count = len(live_db[live_db["CCE Marks Obtained"].str.strip() != ""])
                    st.metric("Total Marks Filed", entered_count)
                with col_c3:
                    absent_count = len(live_db[live_db["CCE Attendance Status"] == "Absent"])
                    st.metric("Total Absent Students in CCE", absent_count)
        # ----------------------------------------------------------------------
        # P9: PANEL P9 MODULE
        # ----------------------------------------------------------------------
        elif current_panel_id == "P9":
            st.header(f"📌 {get_panel_title('P9')} (Dynamic Extension Ledger Room 1)")

            # Initialize dynamic tracking columns if they do not exist in the database schema
            p9_dynamic_fields = ["P9 Record Status", "P9 Custom Remarks"]
            for field in p9_dynamic_fields:
                if field not in live_db.columns:
                    live_db[field] = ""

            if live_db.empty:
                st.warning("⚠️ डेटाबेस वर्तमान में खाली है। कृपया पहले Panel 1 (Entry) के माध्यम से छात्रों का डेटा जोड़ें।")
            else:
                st.subheader("🔍 Filter & Shortlist Candidates")
                col_f1, col_f2 = st.columns(2)
                
                with col_f1:
                    unique_subjects = sorted(list(set(live_db["Subject"].dropna().astype(str))))
                    selected_subject = st.selectbox("Subject (विषय) फ़िल्टर करें:", ["All"] + [sub for sub in unique_subjects if sub.strip() != ""], key="p9_sub_filter")
                    
                with col_f2:
                    unique_p9_status = ["All Students", "Pending Updates Only", "Processed / Verified Records"]
                    selected_p9_filter = st.selectbox("P9 Process Status फ़िल्टर:", unique_p9_status, key="p9_process_filter")

                # Filter execution
                filtered_p9 = live_db.copy()
                if selected_subject != "All":
                    filtered_p9 = filtered_p9[filtered_p9["Subject"] == selected_subject]
                    
                if selected_p9_filter == "Pending Updates Only":
                    filtered_p9 = filtered_p9[filtered_p9["P9 Record Status"].str.strip() == ""]
                elif selected_p9_filter == "Processed / Verified Records":
                    filtered_p9 = filtered_p9[filtered_p9["P9 Record Status"].str.strip() != ""]

                st.write(f"फ़िल्टर के आधार पर कुल छात्र संख्या: **{len(filtered_p9)}**")

                st.subheader("✏️ Bulk Entry Room: P9 Custom Operational Board")
                st.info("💡 नीचे दी गई ग्रिड में आप सीधे छात्रों का 'P9 Record Status' ड्रापडाउन मेनू से चुन सकते हैं और कस्टम रिमार्क्स टाइप कर सकते हैं।")

                p9_display_cols = ["Admission Application Number", "Roll No.", "Student Name", "Subject", "P9 Record Status", "P9 Custom Remarks"]
                display_cols = [c for c in p9_display_cols if c in filtered_p9.columns]
                render_df = filtered_p9[display_cols].copy()
                render_df.insert(0, "S.No.", range(1, len(render_df) + 1))

                edited_p9_df = st.data_editor(
                    render_df,
                    use_container_width=True,
                    disabled=["S.No.", "Admission Application Number", "Roll No.", "Student Name", "Subject"],
                    column_config={
                        "P9 Record Status": st.column_config.SelectboxColumn(
                            "Process Status",
                            help="इस छात्र के लिए P9 चक्र की वर्तमान स्थिति चुनें",
                            options=["Verified", "Pending", "Approved", "On Hold", "Rejected"],
                            required=False,
                        ),
                        "P9 Custom Remarks": st.column_config.TextColumn(
                            "Custom Logs / Remarks",
                            help="कोई विशेष प्रविष्टि या टिप्पणी यहाँ टाइप करें",
                            max_chars=100
                        )
                    },
                    key="p9_record_live_editor",
                    hide_index=True
                )

                if st.button("Save & Sync Panel 9 Records", type="primary", use_container_width=True):
                    try:
                        clean_edited = edited_p9_df.drop(columns=["S.No."])
                        for _, row_edit in clean_edited.iterrows():
                            idx_matches = live_db[live_db["Admission Application Number"] == row_edit["Admission Application Number"]].index
                            if not idx_matches.empty:
                                for match_idx in idx_matches:
                                    live_db.at[match_idx, "P9 Record Status"] = row_edit["P9 Record Status"]
                                    live_db.at[match_idx, "P9 Custom Remarks"] = row_edit["P9 Custom Remarks"]

                        save_live_data(live_db)
                        st.success("✅ Panel 9 का रिकॉर्ड लेजर सफलतापूर्वक मास्टर डेटाबेस फ़ाइल में सेव हो गया है!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"डेटाबेस सिंक करने में त्रुटि उत्पन्न हुई: {e}")

                st.markdown("---")
                st.subheader("📊 Panel P9 Operational Analytics")
                col_c1, col_c2, col_c3 = st.columns(3)
                with col_c1: st.metric("Total Students Available", len(live_db))
                with col_c2:
                    p9_processed = len(live_db[live_db["P9 Record Status"].str.strip() != ""])
                    st.metric("Processed Applications", p9_processed)
                with col_c3: st.metric("Awaiting Data Processing", len(live_db) - p9_processed)

        # ----------------------------------------------------------------------
        # P10: PANEL P10 MODULE
        # ----------------------------------------------------------------------
        elif current_panel_id == "P10":
            st.header(f"📌 {get_panel_title('P10')} (Dynamic Extension Ledger Room 2)")

            # Initialize dynamic tracking columns if they do not exist in the database schema
            p10_dynamic_fields = ["P10 Record Status", "P10 Custom Remarks"]
            for field in p10_dynamic_fields:
                if field not in live_db.columns:
                    live_db[field] = ""

            if live_db.empty:
                st.warning("⚠️ डेटाबेस वर्तमान में खाली है। कृपया पहले Panel 1 (Entry) के माध्यम से छात्रों का डेटा जोड़ें।")
            else:
                st.subheader("🔍 Filter & Shortlist Candidates")
                col_f1, col_f2 = st.columns(2)
                
                with col_f1:
                    unique_subjects = sorted(list(set(live_db["Subject"].dropna().astype(str))))
                    selected_subject = st.selectbox("Subject (विषय) फ़िल्टर करें:", ["All"] + [sub for sub in unique_subjects if sub.strip() != ""], key="p10_sub_filter")
                    
                with col_f2:
                    unique_p10_status = ["All Students", "Pending Updates Only", "Processed / Verified Records"]
                    selected_p10_filter = st.selectbox("P10 Process Status फ़िल्टर:", unique_p10_status, key="p10_process_filter")

                # Filter execution
                filtered_p10 = live_db.copy()
                if selected_subject != "All":
                    filtered_p10 = filtered_p10[filtered_p10["Subject"] == selected_subject]
                    
                if selected_p10_filter == "Pending Updates Only":
                    filtered_p10 = filtered_p10[filtered_p10["P10 Record Status"].str.strip() == ""]
                elif selected_p10_filter == "Processed / Verified Records":
                    filtered_p10 = filtered_p10[filtered_p10["P10 Record Status"].str.strip() != ""]

                st.write(f"फ़िल्टर के आधार पर कुल छात्र संख्या: **{len(filtered_p10)}**")

                st.subheader("✏️ Bulk Entry Room: P10 Custom Operational Board")
                st.info("💡 नीचे दी गई ग्रिड में आप सीधे छात्रों का 'P10 Record Status' ड्रापडाउन मेनू से चुन सकते हैं और कस्टम रिमार्क्स टाइप कर सकते हैं।")

                p10_display_cols = ["Admission Application Number", "Roll No.", "Student Name", "Subject", "P10 Record Status", "P10 Custom Remarks"]
                display_cols = [c for c in p10_display_cols if c in filtered_p10.columns]
                render_df = filtered_p10[display_cols].copy()
                render_df.insert(0, "S.No.", range(1, len(render_df) + 1))

                edited_p10_df = st.data_editor(
                    render_df,
                    use_container_width=True,
                    disabled=["S.No.", "Admission Application Number", "Roll No.", "Student Name", "Subject"],
                    column_config={
                        "P10 Record Status": st.column_config.SelectboxColumn(
                            "Process Status",
                            help="इस छात्र के लिए P10 चक्र की वर्तमान स्थिति चुनें",
                            options=["Verified", "Pending", "Approved", "On Hold", "Rejected"],
                            required=False,
                        ),
                        "P10 Custom Remarks": st.column_config.TextColumn(
                            "Custom Logs / Remarks",
                            help="कोई विशेष प्रविष्टि या टिप्पणी यहाँ टाइप करें",
                            max_chars=100
                        )
                    },
                    key="p10_record_live_editor",
                    hide_index=True
                )

                if st.button("Save & Sync Panel 10 Records", type="primary", use_container_width=True):
                    try:
                        clean_edited = edited_p10_df.drop(columns=["S.No."])
                        for _, row_edit in clean_edited.iterrows():
                            idx_matches = live_db[live_db["Admission Application Number"] == row_edit["Admission Application Number"]].index
                            if not idx_matches.empty:
                                for match_idx in idx_matches:
                                                                       live_db.at[match_idx, "P10 Custom Remarks"] = row_edit["P10 Custom Remarks"]

                        save_live_data(live_db)
                        st.success("✅ Panel 10 का रिकॉर्ड लेजर सफलतापूर्वक मास्टर डेटाबेस फ़ाइल में सेव हो गया है!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"डेटाबेस सिंक करने में त्रुटि उत्पन्न हुई: {e}")

                st.markdown("---")
                st.subheader("📊 Panel P10 Operational Analytics")
                col_c1, col_c2, col_c3 = st.columns(3)
                with col_c1: st.metric("Total Students Available", len(live_db))
                with col_c2:
                    p10_processed = len(live_db[live_db["P10 Record Status"].str.strip() != ""])
                    st.metric("Processed Applications", p10_processed)
                with col_c3: st.metric("Awaiting Data Processing", len(live_db) - p10_processed)

        # ----------------------------------------------------------------------
        # P11: PANEL P11 MODULE
        # ----------------------------------------------------------------------
        elif current_panel_id == "P11":
            st.header(f"📌 {get_panel_title('P11')} (Dynamic Extension Ledger Room 3)")

            # Initialize dynamic tracking columns if they do not exist in the database schema
            p11_dynamic_fields = ["P11 Record Status", "P11 Custom Remarks"]
            for field in p11_dynamic_fields:
                if field not in live_db.columns:
                    live_db[field] = ""


