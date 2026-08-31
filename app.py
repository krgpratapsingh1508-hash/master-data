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

# 🔒 क्रेडेंशियल्स लोड और सेव करने के लिए फंक्शन्स
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

if "credentials" not in st.session_state:
    st.session_state.credentials = load_credentials()

# 🎯 कॉलम्स की मास्टर सूची (Subject Code को Subject के ठीक लेफ्ट साइड में रखा गया है)
DEFAULT_COLUMNS = [
    "Admission Year", "Admission Session", "Eligibility Name", "Admission Application Number",
    "Admission Date", "Unique ID", "Roll No.", "Application Enrollment No.",
    "Enrollment No.", "Student Name", "Father Name", "Mother Name", "Date of Birth",
    "Category", "Subject Code", "Subject", "Duration", "Mobile Number", "Email ID", "Address", "Status",
    "Current Year"
]

# डेटा लोड फंक्शन (ऑटोमैटिक करंट ईयर कैलकुलेशन लॉजिक के साथ)
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
                max_year: "1 year",
                max_year - 1: "2 year",
                max_year - 2: "3 year",
                max_year - 3: "4 year",
                max_year - 4: "5 year",
                max_year - 5: "6 year"
            }
            df["Current Year"] = years_series.map(mapping).fillna("EX-STUDENT")
        else:
            df["Current Year"] = "EX-STUDENT"
            
        return df.fillna("").reset_index(drop=True)
    except:
        return pd.DataFrame(columns=DEFAULT_COLUMNS)

def save_live_data(df_to_save):
    df_to_save.fillna("").astype(str).to_csv(DB_FILE, index=False)

# ==========================================
# ⚙️ स्टेट मैनेजमेंट सेटअप
# ==========================================
if "user_role" not in st.session_state:
    st.session_state.user_role = None  
if "upload_success" not in st.session_state:
    st.session_state.upload_success = False
if "save_success" not in st.session_state:
    st.session_state.save_success = False
if "admin_columns_order" not in st.session_state:
    st.session_state.admin_columns_order = DEFAULT_COLUMNS.copy()
if "admin_lock_state" not in st.session_state:
    st.session_state.admin_lock_state = True  
if "admin_unhide_edit" not in st.session_state:
    st.session_state.admin_unhide_edit = False
if "admin_unhide_move" not in st.session_state:
    st.session_state.admin_unhide_move = False
if "cce_foil_generated" not in st.session_state:
    st.session_state.cce_foil_generated = False

if "admin_hide_entry" not in st.session_state:
    st.session_state.admin_hide_entry = False
if "admin_hide_viewer" not in st.session_state:
    st.session_state.admin_hide_viewer = False
if "admin_hide_cce" not in st.session_state:
    st.session_state.admin_hide_cce = False
if "admin_hide_cred_panel" not in st.session_state:
    st.session_state.admin_hide_cred_panel = False

if "show_login_panel" not in st.session_state:
    st.session_state.show_login_panel = False

live_db = load_live_data()

# ==========================================================
# 🔒 मुख्य लॉगिन गेटवे (फिक्स 2 कॉलम लेआउट)
# ==========================================================
if st.session_state.user_role is None:
    st.markdown("---")
    
    col_login_btn, _ = st.columns(2)
    with col_login_btn:
        login_btn_label = "🔓 Hide Login" if st.session_state.show_login_panel else "🔒 Login"
        if st.button(login_btn_label, use_container_width=True, key="global_login_toggle_btn"):
            st.session_state.show_login_panel = not st.session_state.show_login_panel
            st.rerun()

    if st.session_state.show_login_panel:
        st.subheader("🔒 Multi-User Secure Login Gateway")
        user_input = st.selectbox("Username (भूमिका) चुनें:", options=list(st.session_state.credentials.keys()))
        password_input = st.text_input("Password दर्ज करें:", type="password")
        
        if st.button("Secure Login", use_container_width=True, type="primary"):
            if user_input in st.session_state.credentials and st.session_state.credentials[user_input]["password"] == password_input:
                st.session_state.user_role = st.session_state.credentials[user_input]["role"]
                st.session_state.upload_success = False
                st.session_state.save_success = False
                st.session_state.admin_lock_state = True  
                st.session_state.admin_unhide_edit = False
                st.session_state.admin_unhide_move = False
                st.session_state.cce_foil_generated = False
                st.session_state.show_login_panel = False
                st.success("✅ लॉगिन सफल!")
                st.rerun()
            else:
                st.error("❌ गलत पासवर्ड!")

# ==========================================================
# 🔑 लॉगिन के बाद का मुख्य सिस्टम
# ==========================================================
else:
    st.markdown('<div class="print-hide">', unsafe_allow_html=True)
    if st.button("🔒 मुख्य लॉगआउट (Exit Secure System)", type="primary", use_container_width=True):
        st.session_state.user_role = None
        st.session_state.upload_success = False
        st.session_state.save_success = False
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    role = st.session_state.user_role
    st.info(f"🔑 वर्तमान सत्र भूमिका: **{role.upper()}**")

# ----------------------------------------------------------------------
# 📝 STUDENT DATA ENTRY PANEL UI
# ----------------------------------------------------------------------
st.header("📝 Student Data Entry Panel")

entry_method = st.selectbox(
    "⚙️ डेटा एंट्री का माध्यम चुनें (Choose Entry Method):",
    options=["📁 CSV फ़ाइल बल्क अपलोड (Bulk CSV Upload)", "➕ नया छात्र मैनुअल फॉर्म (Manual Form Entry)"],
    key="data_entry_method_selector"
)
st.markdown("---")

# --- माध्यम A: CSV फ़ाइल बल्क अपलोड ---
if entry_method == "📁 CSV फ़ाइल बल्क अपलोड (Bulk CSV Upload)":
    st.subheader("📁 CSV File Bulk Upload Engine")
    
    # सैंपल फ़ाइल डाउनलोड करने का विकल्प
    sample_df = pd.DataFrame(columns=DEFAULT_COLUMNS)
    csv_sample = sample_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 डाउनलोड करें डेटा प्रविष्टि फॉर्मेट (Sample CSV)",
        data=csv_sample,
        file_name="student_entry_format.csv",
        mime="text/csv"
    )
    
    uploaded_file = st.file_uploader("अपनी स्टूडेंट डेटा CSV फ़ाइल अपलोड करें:", type=["csv"])
    
    if uploaded_file is not None:
        try:
            uploaded_df = pd.read_csv(uploaded_file, dtype=str).fillna("")
            if st.button("Upload & Append CSV Data Now", use_container_width=True, type="primary"):
                # संरचनात्मक संरेखण और सत्यापन
                for col in DEFAULT_COLUMNS:
                    if col not in uploaded_df.columns:
                        uploaded_df[col] = ""
                
                cleaned_uploaded_df = uploaded_df[DEFAULT_COLUMNS].copy()
                current_db = load_live_data()
                
                updated_df = pd.concat([current_db, cleaned_uploaded_df], ignore_index=True)
                save_live_data(updated_df)
                st.success(f"✅ सफलतापूर्वक {len(cleaned_uploaded_df)} नए रिकॉर्ड्स डेटाबेस में जोड़ दिए गए हैं!")
                st.balloons()
        except Exception as e:
            st.error(f"❌ फ़ाइल प्रोसेस करने में त्रुटि: {e}")

# --- माध्यम B: नया छात्र मैनुअल फॉर्म एंट्री ---
elif entry_method == "➕ नया छात्र मैनुअल फॉर्म (Manual Form Entry)":
    st.subheader("➕ नया छात्र मैन्युअल प्रविष्टि फॉर्म")
    
    with st.form(key="standalone_student_add_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            admission_year = st.text_input("Admission Year (प्रवेश वर्ष)*", placeholder="उदा. 2026")
            eligibility_name = st.text_input("Eligibility Name (योग्यता का नाम)", placeholder="उदा. 12th / UG Pass")
            admission_date = st.text_input("Admission Date (प्रवेश तिथि)", placeholder="DD-MM-YYYY")
            roll_no = st.text_input("Roll No. (रोल नंबर)")
            enrollment_no = st.text_input("Enrollment No. (स्थायी नामांकन संख्या)")
            f_name = st.text_input("Father Name (पिता का नाम)*")
            dob = st.text_input("Date of Birth (जन्म तिथि)", placeholder="DD-MM-YYYY")
            subject_code = st.text_input("Subject Code (विषय कोड)*", placeholder="उदा. LLL1")
            subject = st.text_input("Subject (विषय/स्ट्रीम)*", placeholder="उदा. LL.B. / BA LL.B.")
            mobile = st.text_input("Mobile Number (मोबाइल नंबर)")
        with col2:
            admission_session = st.text_input("Admission Session (सत्र)", placeholder="उदा. 2026-27")
            admission_app_no = st.text_input("Admission Application Number (आवेदन संख्या)")
            unique_id = st.text_input("Unique ID (आधार या स्कॉलर नंबर)")
            app_enroll_no = st.text_input("Application Enrollment No. (एप्लिकेशन नामांकन संख्या)")
            s_name = st.text_input("Student Name (छात्र का नाम)*")
            m_name = st.text_input("Mother Name (माता का नाम)")
            category = st.selectbox("Category (कैटेगरी)", ["General", "OBC", "SC", "ST"])
            duration = st.text_input("Duration (कोर्स की अवधि - वर्ष में)", placeholder="उदा. 3 या 5")
            email = st.text_input("Email ID (ईमेल आईडी)")
            address = st.text_input("Address (पता)")
            status_input = st.selectbox("Status (स्थिति)", ["Regular", "Pending", "Pass", "Inactive", "EX-STUDENT"])
        
        submit_student = st.form_submit_button("Save Student Record to Live Database", type="primary", use_container_width=True)

    if submit_student:
        if s_name.strip() == "" or admission_year.strip() == "":
            st.error("❌ त्रुटि: कृपया अनिवार्य क्षेत्र (Student Name और Admission Year) अवश्य भरें।")
        else:
            new_row = {
                "Admission Year": admission_year, "Admission Session": admission_session, 
                "Eligibility Name": eligibility_name, "Admission Application Number": admission_app_no,
                "Admission Date": admission_date, "Unique ID": unique_id, "Roll No.": roll_no, 
                "Application Enrollment No.": app_enroll_no, "Enrollment No.": enrollment_no, 
                "Student Name": s_name, "Father Name": f_name, "Mother Name": m_name, "Date of Birth": dob, 
                "Category": category, "Subject Code": subject_code, "Subject": subject, "Duration": duration, 
                "Mobile Number": mobile, "Email ID": email, "Address": address, "Status": status_input, "Current Year": ""
            }
            
            current_db = load_live_data()
            updated_df = pd.concat([current_db, pd.DataFrame([new_row])], ignore_index=True)
            save_live_data(updated_df)
            st.success(f"✅ छात्र '{s_name}' का रिकॉर्ड डेटाबेस में सुरक्षित रूप से सहेज लिया गया है!")

# ----------------------------------------------------------------------
# 👁️ STUDENT LIVE DATABASE LIST PANEL (VIEWER MODE)
# ----------------------------------------------------------------------
st.header("Student Live Database List (Viewer Mode)")

# स्क्रीन पर प्रिंट के समय इनपुट बॉक्स को छिपाने के लिए सीएसएस क्लास wrapper
st.markdown('<div class="print-hide">', unsafe_allow_html=True)

col_select, col_input = st.columns([1, 2])

with col_select:
    selected_search_column = st.selectbox(
        "🔍 किस कॉलम में सर्च करना चाहते हैं?", 
        options=DEFAULT_COLUMNS, 
        key="viewer_standalone_column_selector"
    )

with col_input:
    search_query = st.text_input(
        f"'{selected_search_column}' के अंदर खोजने के लिए टाइप करें:", 
        key="viewer_standalone_search_input",
        placeholder="यहाँ टाइप करें..."
    )

st.markdown('</div>', unsafe_allow_html=True)

# सर्च फ़िल्टर इंजन
filtered_db = live_db.copy()
if search_query:
    filtered_db = filtered_db[filtered_db[selected_search_column].str.contains(search_query, case=False, na=False)]

# कुल रिकॉर्ड काउंटर
st.metric(label="कुल छात्र रिकॉर्ड संख्या (Total Student Records)", value=len(filtered_db))

if not filtered_db.empty:
    display_df = filtered_db.copy()
    # सीरियल नंबर (S.No.) को सबसे पहले कॉलम पर इंसर्ट करें
    display_df.insert(0, "S.No.", range(1, len(display_df) + 1))
    
    # ग्रिड डेटा रेंडरिंग (Subject Code और Subject क्रम के अनुसार लॉक हैं)
    st.dataframe(
        display_df, 
        use_container_width=True, 
        hide_index=True
    )
    
    # एक्सपोर्ट और डायरेक्ट प्रिंट यूटिलिटी बार
    st.markdown('<div class="print-hide" style="margin-top: 20px;">', unsafe_allow_html=True)
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        csv_buffer = filtered_db.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Student List (CSV File)", 
            data=csv_buffer, 
            file_name="student_database_list.csv", 
            mime="text/csv", 
            use_container_width=True, 
            key="viewer_standalone_csv_download"
        )
        
    with col_btn2:
        st.markdown("""
            <button onclick="window.print()" style="width: 100%; background-color: #FF5733; color: white; border: none; padding: 0.55rem 1rem; border-radius: 0.5rem; cursor: pointer; font-weight: bold; font-size: 16px; text-align: center; box-sizing: border-box; transition: 0.3s;">🖨️ Direct Print Student List</button>
        """, unsafe_allow_html=True)
        
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.warning("⚠️ आपके द्वारा खोजा गया रिकॉर्ड मैच नहीं हुआ। कृपया कोई दूसरा कीवर्ड टाइप करें।")

# ----------------------------------------------------------------------
# 📝 CCE HANDLER PANEL (PART 1 - SELECTIONS & FILTERING GRID)
# ----------------------------------------------------------------------
st.header("College CCE Foil Sheet Generator")
st.write("Institute of Law, Govt. Kamlaraja Girls Post-Graduate Autonomous College, Gwalior (M.P.)")

if not live_db.empty:
    # 1. डायनेमिक सब्जेक्ट स्क्रॉल लिस्ट (Dropdown Filter)
    unique_subjects = sorted(list(set(live_db['Subject'].dropna().astype(str).str.strip())))
    unique_subjects = [sub for sub in unique_subjects if sub != ""]
    selected_subject = st.selectbox(
        "📚 Select Subject (विषय चुनें):", 
        options=["All Subjects"] + unique_subjects, 
        key="cce_part1_subject_filter"
    )

    # 2. सेमेस्टर और ईयर स्क्रॉल लिस्ट (1-12 Sem & 1-6 Year Selection)
    year_sem_options = [
        "1 Semester", "2 Semester", "3 Semester", "4 Semester", "5 Semester", "6 Semester",
        "7 Semester", "8 Semester", "9 Semester", "10 Semester", "11 Semester", "12 Semester",
        "1 year", "2 year", "3 year", "4 year", "5 year", "6 year"
    ]
    
    # यदि चयन बदलता है तो फ़ॉइल रेंडरिंग स्टेट को रिसेट करने का फंक्शन
    def reset_foil_state():
        st.session_state.cce_foil_generated = False

    chosen_option = st.selectbox(
        "📆 Select Semester / Year (सेमेस्टर या वर्ष चुनें):", 
        year_sem_options, 
        key="cce_part1_year_sem_box", 
        on_change=reset_foil_state
    )

    # 3. बैकएंड इवैल्यूएशन ईयर मैपिंग लॉजिक (यह पार्ट 2 के लिए आवश्यक टारगेट इयर तय करता है)
    mapping_logic = {
        "1 Semester": "1 year", "2 Semester": "1 year", "1 year": "1 year",
        "3 Semester": "2 year", "4 Semester": "2 year", "2 year": "2 year",
        "5 Semester": "3 year", "6 Semester": "3 year", "3 year": "3 year",
        "7 Semester": "4 year", "8 Semester": "4 year", "4 year": "4 year",
        "9 Semester": "5 year", "10 Semester": "5 year", "5 year": "5 year",
        "11 Semester": "6 year", "12 Semester": "6 year", "6 year": "6 year"
    }
    target_year_text = mapping_logic[chosen_option]

    # 4. लाइव छात्र प्रीव्यू ग्रिड जनरेशन (फ़िल्टर के आधार पर लाइव मिलान)
    st.markdown("---")
    st.subheader("📊 CCE Processing Student Grid View (Preview)")
    
    preview_db = live_db.copy()
    if selected_subject != "All Subjects":
        preview_db = preview_db[preview_db['Subject'].str.strip() == selected_subject]
    
    # संबंधित महत्वपूर्ण कॉलम्स का रीयल-टाइम डेटा ग्रिड दिखाएं
    st.dataframe(
        preview_db[["Roll No.", "Student Name", "Subject Code", "Subject", "Status", "Current Year"]], 
        use_container_width=True, 
        hide_index=True
    )

    # 5. पार्ट 2 और 3 को ट्रिगर करने के लिए सबमिशन बटन
    if st.button("Proceed to Generate CCE Foil Sheets", use_container_width=True, type="primary", key="cce_part1_submit_btn"):
        st.session_state.cce_foil_generated = True
        st.success(f"✅ चयन लॉक हो गया है: {selected_subject} ({chosen_option})। डेटा प्रोसेसिंग इंजन एक्टिवेटेड।")

else:
    st.error("⚠️ लाइव डेटाबेस फ़ाइल खाली है या लोड नहीं हो पा रही है। कृपया पहले डेटा एंट्री पैनल से रिकॉर्ड्स जोड़ें।")

# सुनिश्चित करें कि पार्ट 1 में 'Proceed' बटन दबाने के बाद ही यह इंजन रन हो
if "cce_foil_generated" in st.session_state and st.session_state.cce_foil_generated:
    st.markdown("---")
    st.subheader("⚙️ Processing Engine (Validating Student Eligibility)")

    # प्रोसेसिंग एरे और वेरिएबल्स को इनिशियलाइज़ करें
    regular_records = []
    ex_student_records = []
    has_missing_roll_and_is_first_year_regular = False 
    detected_subject_code = ""

    # 1. डेटाबेस में मौजूद अधिकतम प्रवेश वर्ष का ऑटोमैटिक कैलकुलेशन
    years_series = pd.to_numeric(live_db["Admission Year"], errors='coerce')
    max_year = int(years_series.max()) if not years_series.dropna().empty else 2026

    # 2. मुख्य फ़िल्टरिंग और कटऑफ वैलिडेशन लूप
    for _, row in live_db.iterrows():
        roll = str(row.get('Roll No.', '')).strip()
        name = str(row.get('Student Name', '')).strip()
        status = str(row.get('Status', '')).strip().upper()
        current_year_val = str(row.get('Current Year', '')).strip().lower()
        student_sub = str(row.get('Subject', '')).strip()
        sub_code = str(row.get('Subject Code', '')).strip()
        adm_year_str = str(row.get('Admission Year', '')).strip()
        duration_str = str(row.get('Duration', '')).strip()
        
        # इंटीजर में सुरक्षित कन्वर्शन
        try: adm_year = int(float(adm_year_str))
        except: adm_year = 0

        try: course_duration = int(float(duration_str))
        except: course_duration = 6

        # विषय (Subject) फ़िल्टर
        if selected_subject != "All Subjects" and student_sub != selected_subject:
            continue
            
        # सब्जेक्ट कोड ऑटो-डिटेक्ट करें
        if sub_code and sub_code.lower() != "nan" and detected_subject_code == "":
            detected_subject_code = sub_code

        # ------------------------------------------------------------------
        # लॉजिक A: EX-STUDENTS के लिए डायनेमिक कटऑफ वैलिडेशन
        # ------------------------------------------------------------------
        if status == "EX-STUDENT":
            is_ex_match = False
            gap_needed = 0
            
            if target_year_text == "1 year": gap_needed = 1
            elif target_year_text == "2 year": gap_needed = 2
            elif target_year_text == "3 year": gap_needed = 3
            elif target_year_text == "4 year": gap_needed = 4
            elif target_year_text == "5 year": gap_needed = 5
            elif target_year_text == "6 year": gap_needed = 6
            
            if gap_needed <= course_duration and adm_year == (max_year - gap_needed):
                is_ex_match = True
            
            if is_ex_match and roll and roll.lower() != "nan" and roll != "":
                ex_student_records.append(roll)
            continue

        # ------------------------------------------------------------------
        # लॉजिक B: REGULAR छात्रों के लिए वैलिडेशन (1st Year फॉलबैक के साथ)
        # ------------------------------------------------------------------
        if target_year_text in current_year_val and status == 'REGULAR':
            if not roll or roll.lower() == "nan" or roll == "":
                if current_year_val == "1 year":
                    display_identifier = name if name else "[Unknown Name]"
                    has_missing_roll_and_is_first_year_regular = True
                    regular_records.append(display_identifier)
            else:
                regular_records.append(roll)

    # 3. डुप्लिकेट्स हटाकर एक्स-स्टूडेंट्स को प्राथमिकता क्रम में रखें
    ex_student_records = sorted(list(set(ex_student_records)))
    regular_records = sorted(list(set(regular_records)))
    final_records_list = ex_student_records + regular_records

    # 4. यूआई स्क्रीन पर समरी डैशबोर्ड डिस्प्ले करें
    st.info("🎯 Validation Analytics Summary:")
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1: st.metric("Valid Ex-Students (Prioritized)", len(ex_student_records))
    with col_m2: st.metric("Valid Regular Students", len(regular_records))
    with col_m3: st.metric("Total Records Captured", len(final_records_list))

    if not final_records_list:
        st.error("❌ इस फ़िल्टर मानदंड के आधार पर लाइव डेटाबेस में कोई भी योग्य छात्र रिकॉर्ड नहीं मिला।")
else:
    st.warning("⏳ कृपया ऊपर Part 1 में मानदंडों का चयन करके 'Proceed' बटन दबाएं।")

# नोट: यह पार्ट मानकर चलता है कि Part 1 और Part 2 सफलतापूर्वक रन हो चुके हैं,
# और 'final_records_list', 'detected_subject_code', 'has_missing_roll_and_is_first_year_regular',
# 'college_name', 'exam_info', 'selected_subject' जैसे वेरिएबल्स मेमोरी में उपलब्ध हैं।

if "cce_foil_generated" in st.session_state and st.session_state.cce_foil_generated:
    # जांचें कि क्या पिछले इंजन (Part 2) से कोई छात्र रिकॉर्ड प्राप्त हुआ है
    if 'final_records_list' in locals() and final_records_list:
        st.markdown("---")
        st.subheader("🖨️ Generated Visual CCE Foil Sheet")
        
        # 1. डेटा को लेफ्ट और राइट साइड के लिए 30-30 रिकॉर्ड्स के दो कॉलम्स में विभाजित करें
        left_side_data = final_records_list[:30]
        right_side_data = final_records_list[30:60]

        # 2. प्रथम वर्ष के अपवाद (Roll No Missing) होने पर डायनेमिक कॉलम हेडर लेबल सेट करें
        dynamic_th_label = "Roll No. / Student Name" if has_missing_roll_and_is_first_year_regular else "Roll No."

        # 3. सिंगल फ़ॉइल ब्लॉक (HTML Component) जनरेट करने का फंक्शन
        def generate_cce_html_block(items, start_idx, foil_label, has_data):
            if not has_data:
                return '<div class="foil-unit" style="border:none; background:transparent;"></div>'
            
            # पेपर कोड डिस्प्ले सेट करें
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
            
            # डेटाबेस से प्राप्त रिकॉर्ड्स को टेबल रोज़ (Rows) में जोड़ें
            for idx_foil, item_val in enumerate(items, start=start_idx):
                block += f"<tr><td style='border:1px solid black; padding:4px;'><b>{idx_foil}</b></td><td style='border:1px solid black; padding:4px;'>{item_val}</td><td style='border:1px solid black; padding:4px;'></td><td style='border:1px solid black; padding:4px;'></td></tr>"
            
            # यदि रिकॉर्ड्स 30 से कम हैं, तो खाली रोज़ (Blank Rows) भरकर टेबल का ढांचा पूरा करें
            current_len = len(items)
            if current_len < 30:
                for k in range(current_len + start_idx, 30 + start_idx):
                    block += "<tr><td style='border:1px solid black; padding:4px;'>&nbsp;</td><td style='border:1px solid black; padding:4px;'>&nbsp;</td><td style='border:1px solid black; padding:4px;'>&nbsp;</td><td style='border:1px solid black; padding:4px;'>&nbsp;</td></tr>"
            
            block += f"""
                </table>
                <div class="note" style="font-size:10px; margin-top:10px;"><b>Note:</b> Roll Number and Marks awarded to the candidate may be entered under respective columns very carefully.</div>
                <div class="footer-fields">Signature of Examiner......................................<br>Date: ___/___/2026</div>
            </div>
            """
            return block

        # 4. लेफ्ट और राइट दोनों ब्लॉक्स का HTML तैयार करें
        left_block_html = generate_cce_html_block(left_side_data, 1, "FOIL", True)
        right_block_html = generate_cce_html_block(right_side_data, 31, "FOIL", len(right_side_data) > 0)

        # 5. प्रिटिंग मीडिया और लेआउट को स्थिर रखने के लिए आंतरिक CSS स्टाइल
        html_style = """
        <style>
            #foil-capture-area { display: flex; justify-content: space-between; gap: 20px; width: 1100px; padding: 15px; background: white; margin: auto; }
            .foil-unit { width: 49%; border: 1px solid black; padding: 12px; box-sizing: border-box; background: white; }
            .top-fields { display: flex; justify-content: space-between; font-weight: bold; font-size: 13px; }
            .header-box { text-align: center; border-top: 2px solid black; border-bottom: 2px solid black; padding: 6px 0; margin-top: 8px; font-weight: bold; font-size: 16px; }
            .sub-box { border-bottom: 2px solid black; padding: 5px 0; font-size: 12px; font-weight: bold; }
            .exam-right { text-align: right; }
            .marks-info { display: flex; justify-content: space-between; padding: 5px 0; font-weight: bold; border-bottom: 2px solid black; font-size: 12px; }
            .foil-title { text-align: center; font-weight: bold; font-size: 16px; margin: 10px 0; }
            .footer-fields { margin-top: 15px; font-size: 12px; font-weight: bold; }
            @media print { .print-hide { display: none !important; } }
        </style>
        """
        
        # 6. स्क्रीनशॉट कैप्चर स्क्रिप्ट (html2canvas) के साथ पूर्ण DOM संयोजन
        full_html = f"""
        <html>
        <head>
            {html_style}
            <script src="https://cloudflare.com"></script>
            <script>
            function downloadFoilAsPNG() {{
                const element = document.getElementById("foil-capture-area");
                html2canvas(element, {{ scale: 2 }}).then(canvas => {{
                    let link = document.createElement("a");
                    link.download = "cce_foil_sheet.png";
                    link.href = canvas.toDataURL("image/png");
                    link.click();
                }});
            }}
            </script>
        </head>
        <body>
            <div class="print-hide" style="text-align: center; margin-bottom: 15px; display:flex; gap:20px; justify-content:center;">
                <button onclick="window.print()" style="background:#FF5733; color:white; border:none; padding:10px 20px; border-radius:5px; cursor:pointer; font-weight:bold; font-size:14px;">Direct Print Only Foil</button>
                <button onclick="downloadFoilAsPNG()" style="background:#4CAF50; color:white; border:none; padding:10px 20px; border-radius:5px; cursor:pointer; font-weight:bold; font-size:14px;">Download File in PNG File</button>
            </div>
            <div id="foil-capture-area">
                {left_block_html}
                {right_block_html}
            </div>
        </body>
        </html>
        """
        
        # 7. स्ट्रीमलिट कॉम्पोनेंट में कस्टमाइज्ड HTML रेंडर करें
        st.components.v1.html(full_html, height=1600, scrolling=True)
        
    else:
        st.warning("⚠️ रेंडरिंग के लिए कोई वैध छात्र सूची उपलब्ध नहीं है। कृपया Part 2 इंजन का आउटपुट चेक करें।")

# ----------------------------------------------------------------------
# 🛠️ 4. FULL ADMIN ROLE PANEL
# ----------------------------------------------------------------------
st.header("🛠️ Full Admin Management Panel")

# --- PART A: GLOBAL PANEL VISIBILITY CONTROLLERS ---
st.subheader("🛡️ Global Panels Visibility Controller")
col_vis1, col_vis2, col_vis3, col_vis4 = st.columns(4)

with col_vis1:
    entry_btn_label = "👁️ Data Entry: UNHIDDEN" if not st.session_state.admin_hide_entry else "🙈 Data Entry: HIDDEN"
    if st.button(entry_btn_label, use_container_width=True, key="admin_standalone_toggle_entry"):
        st.session_state.admin_hide_entry = not st.session_state.admin_hide_entry
        st.rerun()
        
with col_vis2:
    viewer_btn_label = "👁️ Viewer Panel: UNHIDDEN" if not st.session_state.admin_hide_viewer else "🙈 Viewer Panel: HIDDEN"
    if st.button(viewer_btn_label, use_container_width=True, key="admin_standalone_toggle_viewer"):
        st.session_state.admin_hide_viewer = not st.session_state.admin_hide_viewer
        st.rerun()
        
with col_vis3:
    cce_btn_label = "👁️ CCE Panel: UNHIDDEN" if not st.session_state.admin_hide_cce else "🙈 CCE Panel: HIDDEN"
    if st.button(cce_btn_label, use_container_width=True, key="admin_standalone_toggle_cce"):
        st.session_state.admin_hide_cce = not st.session_state.admin_hide_cce
        st.rerun()

with col_vis4:
    cred_btn_label = "👁️ Passwords: UNHIDDEN" if not st.session_state.admin_hide_cred_panel else "🙈 Passwords: HIDDEN"
    if st.button(cred_btn_label, use_container_width=True, key="admin_standalone_toggle_cred"):
        st.session_state.admin_hide_cred_panel = not st.session_state.admin_hide_cred_panel
        st.rerun()

st.markdown("---")

# --- PART B: PERSISTENT PASSWORD RESET MANAGEMENT SYSTEM ---
if not st.session_state.admin_hide_cred_panel:
    st.subheader("🔐 Change User Credentials System")
    with st.form(key="admin_standalone_cred_form"):
        target_user = st.selectbox("किस यूजर का पासवर्ड बदलना चाहते हैं?", options=list(st.session_state.credentials.keys()))
        new_password = st.text_input("नया पासवर्ड दर्ज करें:", type="password")
        submit_cred = st.form_submit_button("Update Password Now", type="primary")
        
        if submit_cred:
            if new_password.strip() == "":
                st.error("❌ पासवर्ड खाली नहीं हो सकता।")
            else:
                st.session_state.credentials[target_user]["password"] = new_password
                save_credentials(st.session_state.credentials)
                st.success(f"✅ '{target_user}' का पासवर्ड सफलतापूर्वक अपडेट और सेव कर दिया गया है!")
    st.markdown("---")

# --- PART C: ADVANCED DATA CONTROLS AND SCHEMA MATRIX ---
st.subheader("📊 Master Database List View & Advanced Controls")

col_ctrl1, col_ctrl2, col_ctrl3 = st.columns(3)
with col_ctrl1:
    edit_label = "📝 हाइड करें लाइव डायरेक्ट प्रविष्टि" if st.session_state.admin_unhide_edit else "📝 अनहाइड करें लाइव डायरेक्ट प्रविष्टि"
    if st.button(edit_label, use_container_width=True, key="admin_standalone_unhide_text_edit"):
        st.session_state.admin_unhide_edit = not st.session_state.admin_unhide_edit
        st.rerun()
with col_ctrl2:
    move_label = "🔀 हाइड करें कॉलम मूव कंट्रोल्स" if st.session_state.admin_unhide_move else "🔀 अनहाइड करें कॉलम मूव कंट्रोल्स"
    if st.button(move_label, use_container_width=True, key="admin_standalone_unhide_column_move"):
        st.session_state.admin_unhide_move = not st.session_state.admin_unhide_move
        st.rerun()
with col_ctrl3:
    lock_label = "🔒 लिस्ट लॉक करें" if not st.session_state.admin_lock_state else "🔓 लिस्ट अनलॉक करें"
    if st.button(lock_label, use_container_width=True, key="admin_standalone_toggle_lock_state"):
        st.session_state.admin_lock_state = not st.session_state.admin_lock_state
        st.rerun()

# --- PART D: INTERACTIVE COLUMN REORDERING ENGINE (LOCK PROTECTED) ---
if st.session_state.admin_unhide_move:
    if st.session_state.admin_lock_state:
        st.error("⚠️ लिस्ट वर्तमान में लॉक है! कॉलम बदलने के लिए पहले ऊपर दिए गए बटन से 'लिस्ट अनलॉक' करें।")
    else:
        st.info("🔄 कॉलम मूव कंट्रोल्स एक्टिव हैं:")
        target_col = st.selectbox("मूव करने के लिए कॉलम चुनें:", options=st.session_state.admin_columns_order, key="admin_standalone_col_shift_select")
        col_move_left, col_move_right = st.columns(2)
        
        if col_move_left.button("⬅️ शिफ्ट लेफ्ट (Shift Left)", use_container_width=True, key="admin_standalone_shift_left"):
            idx = st.session_state.admin_columns_order.index(target_col)
            if idx > 0:
                st.session_state.admin_columns_order[idx], st.session_state.admin_columns_order[idx-1] = st.session_state.admin_columns_order[idx-1], st.session_state.admin_columns_order[idx]
                st.rerun()
                
        if col_move_right.button("➡️ शिफ्ट राइट (Shift Right)", use_container_width=True, key="admin_standalone_shift_right"):
            idx = st.session_state.admin_columns_order.index(target_col)
            if idx < len(st.session_state.admin_columns_order) - 1:
                st.session_state.admin_columns_order[idx], st.session_state.admin_columns_order[idx+1] = st.session_state.admin_columns_order[idx+1], st.session_state.admin_columns_order[idx]
                st.rerun()

# डेटा मैपिंग सुनिश्चित करना
ordered_db = live_db[st.session_state.admin_columns_order].copy()
ordered_db.insert(0, "S.No.", range(1, len(ordered_db) + 1))

st.write(f"कुल मास्टर रिकॉर्ड संख्या: **{len(ordered_db)}**")

# --- PART E: CHOOSE RENDER MATRIX MODE (READ-ONLY VS LIVE DATA EDITOR) ---
if not st.session_state.admin_lock_state and st.session_state.admin_unhide_edit:
    st.warning("⚠️ लाइव डायरेक्ट टेक्स्ट संपादन सक्रिय है। ग्रिड में किया गया बदलाव सीधे CSV फ़ाइल में स्थायी सेव हो जाएगा।")
    edited_df = st.data_editor(
        ordered_db,
        use_container_width=True,
        disabled=["S.No.", "Current Year"],
        key="admin_standalone_live_data_editor",
        hide_index=True
    )
    # संपादन के बाद डेटाबेस सिंक लॉजिक
    clean_edited = edited_df.drop(columns=["S.No."])
    for col in clean_edited.columns:
        if col != "Current Year":
            live_db[col] = clean_edited[col].values
    save_live_data(live_db)
    
else:
    st.dataframe(ordered_db, use_container_width=True, hide_index=True)
    
