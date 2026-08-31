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

    # ----------------------------------------------------------------------
    # 📝 3. COLLEGE CCE FOIL SHEET GENERATOR - (Role: cce_handler, full_admin)
    # ----------------------------------------------------------------------
    if role in ["cce_handler", "full_admin"] and not st.session_state.admin_hide_cce:
        st.header("College CCE Foil Sheet Generator")
        st.write("Institute of Law, Govt. Kamlaraja Girls Post-Graduate Autonomous College, Gwalior (M.P.)")

        college_name = "GOVT. K.R.G. POST-GRADUATE AUTONOMOUS COLLEGE, GWALIOR (M.P.)"

        if not live_db.empty:
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

            st.write("📊 CCE Processing Student Grid View:")
            preview_db = live_db.copy()
            if selected_subject != "All Subjects":
                preview_db = preview_db[preview_db['Subject'].str.strip() == selected_subject]
            
            preview_render = preview_db[["Roll No.", "Student Name", "Subject Code", "Subject", "Status", "Current Year"]].copy()
            preview_render = preview_render.rename(columns={c: get_display_name(c) for c in preview_render.columns})
            st.dataframe(preview_render, use_container_width=True, hide_index=True)

            if st.button("Generate CCE Foil Sheets Now", use_container_width=True, type="primary"):
                st.session_state.cce_foil_generated = True
                st.rerun()

            # --- डेटा प्रोसेसिंग इंजन ---
            if st.session_state.cce_foil_generated:
                regular_records = []
                ex_student_records = []
                has_missing_roll_and_is_first_year_regular = False 
                detected_subject_code = ""

                # डेटाबेस में मौजूद अधिकतम प्रवेश वर्ष का पता लगाएं
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

                    # 🎯 चरण 1: विषय (Subject) नाम मैच करें
                    if selected_subject != "All Subjects" and student_sub != selected_subject: continue
                    if sub_code and sub_code.lower() != "nan" and detected_subject_code == "": detected_subject_code = sub_code

                    # लॉजिक A: EX-STUDENTS के लिए डायनेमिक कटऑफ वैलिडेशन
                    if status == "EX-STUDENT":
                        is_ex_match = False
                        try:
                            gap_needed = int(target_year_text.split()[0])
                        except:
                            gap_needed = 1
                            
                        if gap_needed <= course_duration and adm_year == (max_year - gap_needed): is_ex_match = True
                        if is_ex_match and roll and roll.lower() != "nan" and roll != "": ex_student_records.append(roll)
                        continue

                    # लॉजिक B: REGULAR छात्रों के लिए नया सटीक कंडीशन इंजन
                    if status == 'Regular Student':
                        # 🎯 चरण 2: विषय मैच होने के बाद 'Current Year' कॉलम में वर्ष (Year) मैच करें
                        if target_year_text.lower() in current_year_val:
                            # 🎯 चरण 3: यदि 1 year का छात्र है और रोल नंबर कॉलम खाली है, तो छात्र का नाम (Student Name) लें
                            if target_year_text.lower() == "1 year" and (not roll or roll.lower() == "nan" or roll == ""):
                                has_missing_roll_and_is_first_year_regular = True
                                regular_records.append(name if name else "[Unknown Name]")
                            else:
                                # बाकी सभी स्थितियों में केवल रोल नंबर लें
                                if roll and roll.lower() != "nan" and roll != "":
                                    regular_records.append(roll)

                final_records_list = sorted(list(set(ex_student_records))) + sorted(list(set(regular_records)))

                st.markdown("---")
                st.subheader("⚙️ Processing Engine (Validating Student Eligibility)")
                st.info("🎯 Validation Analytics Summary:")
                col_m1, col_m2, col_m3 = st.columns(3)
                with col_m1: st.metric("Valid Ex-Students (Prioritized)", len(ex_student_records))
                with col_m2: st.metric("Valid Regular Students", len(regular_records))
                with col_m3: st.metric("Total Records Captured", len(final_records_list))

                # --- HTML फ़ॉइल शीट रेंडरिंग इंजन ---
                if final_records_list:
                    st.subheader("🖨️ Generated Visual CCE Foil Sheet")
                    left_side_data = final_records_list[:30]
                    right_side_data = final_records_list[30:60]
                    dynamic_th_label = "Roll No. / Student Name" if has_missing_roll_and_is_first_year_regular else "Roll No."

                    def generate_cce_html_block(items, start_idx, foil_label, has_data):
                        if not has_data: return '<div class="foil-unit" style="border:none; background:transparent;"></div>'
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
                            block += f"<tr><td style='border:1px solid black; padding:4px;'><b>{idx_foil}</b></td><td style='border:1px solid black; padding:4px;'>{item_val}</td><td style='border:1px solid black; padding:4px;'></td><td style='border:1px solid black; padding:4px;'></td></tr>"
                        for k in range(len(items) + start_idx, 30 + start_idx):
                            block += "<tr><td style='border:1px solid black; padding:4px;'>&nbsp;</td><td style='border:1px solid black; padding:4px;'>&nbsp;</td><td style='border:1px solid black; padding:4px;'>&nbsp;</td><td style='border:1px solid black; padding:4px;'>&nbsp;</td></tr>"
                        block += f"""</table><div class="note" style="font-size:10px; margin-top:10px;"><b>Note:</b> Entered carefully.</div><div class="footer-fields">Signature of Examiner......................................<br>Date: ___/___/2026</div></div>"""
                        return block

                    left_block_html = generate_cce_html_block(left_side_data, 1, "FOIL", True)
                    right_block_html = generate_cce_html_block(right_side_data, 31, "FOIL", len(right_side_data) > 0)

                    html_style = """<style>#foil-capture-area { display: flex; justify-content: space-between; gap: 20px; width: 1100px; padding: 15px; background: white; margin: auto; }.foil-unit { width: 49%; border: 1px solid black; padding: 12px; box-sizing: border-box; background: white; }.top-fields { display: flex; justify-content: space-between; font-weight: bold; font-size: 13px; }.header-box { text-align: center; border-top: 2px solid black; border-bottom: 2px solid black; padding: 6px 0; margin-top: 8px; font-weight: bold; font-size: 16px; }.sub-box { border-bottom: 2px solid black; padding: 5px 0; font-size: 12px; font-weight: bold; }.exam-right { text-align: right; }.marks-info { display: flex; justify-content: space-between; padding: 5px 0; font-weight: bold; border-bottom: 2px solid black; font-size: 12px; }.foil-title { text-align: center; font-weight: bold; font-size: 16px; margin: 10px 0; }.footer-fields { margin-top: 15px; font-size: 12px; font-weight: bold; }@media print { .print-hide { display: none !important; } }</style>"""
                    full_html = f"""<html><head>{html_style}<script src="https://cloudflare.com"></script><script>function downloadFoilAsPNG() {{ const element = document.getElementById("foil-capture-area"); html2canvas(element, {{ scale: 2 }}).then(canvas => {{ let link = document.createElement("a"); link.download = "cce_foil_sheet.png"; link.href = canvas.toDataURL("image/png"); link.click(); }}); }}</script></head><body><div class="print-hide" style="text-align: center; margin-bottom: 15px; display:flex; gap:20px; justify-content:center;"><button onclick="window.print()" style="background:#FF5733; color:white; border:none; padding:10px 20px; border-radius:5px; cursor:pointer; font-weight:bold;">Direct Print Only Foil</button><button onclick="downloadFoilAsPNG()" style="background:#4CAF50; color:white; border:none; padding:10px 20px; border-radius:5px; cursor:pointer; font-weight:bold;">Download File in PNG File</button></div><div id="foil-capture-area">{left_block_html}{right_block_html}</div></body></html>"""
                    st.components.v1.html(full_html, height=1600, scrolling=True)
                else: st.error("कोई छात्र रिकॉर्ड नहीं मिला।")
        st.markdown("---")
