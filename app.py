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

# 🎯 मास्टर कॉलम्स सूची (Subject ID को Subject के ठीक पहले लॉक किया गया है)
DEFAULT_COLUMNS = [
    "Admission Year", "Admission Session", "Eligibility Name", "Admission Application Number",
    "Admission Date", "Unique ID", "Roll No.", "Application Enrollment No.",
    "Enrollment No.", "Student Name", "Father Name", "Mother Name", "Date of Birth",
    "Category", "Subject Code", "Subject ID", "Subject", "Duration", "Mobile Number", "Email ID", "Address", "Status",
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

# 🛠️ हेल्पिंग हेल्पर फंक्शन: ड्यूशनरी मैपिंग के अनुसार रीयल-टाइम नाम रिप्लेसमेंट करना
def get_display_name(internal_col_name):
    return st.session_state.column_mappings.get(internal_col_name, internal_col_name)

# ==========================================================
# 🔒 मुख्य लॉगिन गेटवे (पैनल बाहर बिल्कुल नहीं दिखेंगे जब तक लॉगिन न हो)
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
# 🔑 लॉगिन होने के बाद एक्सेस होने वाले पैनल्स (Role-Based Access)
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
# 📝 STUDENT DATA ENTRY PANEL - (ONLY CODE MODULE)
# ----------------------------------------------------------------------
st.header("📝 Student Data Entry Panel")

entry_method = st.selectbox(
    "⚙️ डेटा एंट्री का माध्यम चुनें (Choose Entry Method):",
    options=["📁 CSV फ़ाइल बल्क अपलोड (Bulk CSV Upload)", "➕ नया छात्र मैनुअल फॉर्म (Manual Form Entry)"],
    key="standalone_entry_panel_selector"
)
st.markdown("---")

# --- माध्यम A: CSV फ़ाइल बल्क अपलोड ---
if entry_method == "📁 CSV फ़ाइल बल्क अपलोड (Bulk CSV Upload)":
    st.subheader("📁 CSV File Bulk Upload Engine")
    
    # एडमिन द्वारा सेट कस्टम नामों के साथ सैंपल प्रविष्टि फॉर्मेट डाउनलोड करने का विकल्प
    sample_df = pd.DataFrame(columns=DEFAULT_COLUMNS)
    sample_df_renamed = sample_df.rename(columns={c: get_display_name(c) for c in DEFAULT_COLUMNS})
    csv_sample = sample_df_renamed.to_csv(index=False).encode('utf-8')
    
    st.download_button(
        label="📥 डेटा प्रविष्टि फॉर्मेट डाउनलोड करें (Sample CSV)",
        data=csv_sample,
        file_name="student_entry_format.csv",
        mime="text/csv",
        use_container_width=True
    )
    st.markdown(" ")
    
    uploaded_file = st.file_uploader("अपनी स्टूडेंट डेटा CSV फ़ाइल चुनें और अपलोड करें:", type=["csv"])
    
    if uploaded_file is not None:
        try:
            uploaded_df = pd.read_csv(uploaded_file, dtype=str).fillna("")
            if st.button("Upload & Append CSV Data Now", use_container_width=True, type="primary"):
                
                # यदि यूज़र ने हेडर में कस्टम नामों वाली फ़ाइल अपलोड की है, तो उसे इंटरनल नाम में वापस मैप करें
                reverse_mapping = {get_display_name(k): k for k in DEFAULT_COLUMNS}
                uploaded_df = uploaded_df.rename(columns=reverse_mapping)
                
                # संरचनात्मक सत्यापन (Structural Validation)
                for col in DEFAULT_COLUMNS:
                    if col not in uploaded_df.columns:
                        uploaded_df[col] = ""
                
                cleaned_uploaded_df = uploaded_df[DEFAULT_COLUMNS].copy()
                current_db = load_live_data()
                
                updated_df = pd.concat([current_db, cleaned_uploaded_df], ignore_index=True)
                save_live_data(updated_df)
                st.success(f"✅ सफलतापूर्वक {len(cleaned_uploaded_df)} नए छात्र रिकॉर्ड्स लाइव डेटाबेस में जोड़ दिए गए हैं!")
                st.balloons()
        except Exception as e:
            st.error(f"❌ फ़ाइल प्रोसेस करने में त्रुटि (Error processing CSV): {e}")

# --- माध्यम B: नया छात्र मैनुअल फॉर्म प्रविष्टि ---
elif entry_method == "➕ नया छात्र मैनुअल फॉर्म (Manual Form Entry)":
    st.subheader("➕ नया छात्र मैन्युअल प्रविष्टि फॉर्म")
    
    with st.form(key="standalone_student_entry_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            admission_year = st.text_input(get_display_name("Admission Year"))
            eligibility_name = st.text_input(get_display_name("Eligibility Name"))
            admission_date = st.text_input(get_display_name("Admission Date"))
            roll_no = st.text_input(get_display_name("Roll No."))
            enrollment_no = st.text_input(get_display_name("Enrollment No."))
            f_name = st.text_input(get_display_name("Father Name"))
            dob = st.text_input(get_display_name("Date of Birth"))
            
            # 🎯 सटीक क्रम: सब्जेक्ट कोड और सब्जेक्ट आईडी का टेक्स्ट बॉक्स विषय (Subject) से पहले रखा गया है
            subject_code = st.text_input(get_display_name("Subject Code"), placeholder="उदा. C264")
            subject_id = st.text_input(get_display_name("Subject ID"), placeholder="उदा. SUB101")
            subject = st.text_input(get_display_name("Subject"), placeholder="उदा. B.A. LL.B.")
            
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
        
        submit_student = st.form_submit_button("Save Student Record to Live Database", type="primary", use_container_width=True)

    if submit_student:
        if s_name.strip() == "":
            st.error("❌ त्रुटि: कृपया 'Student Name' प्रविष्टि ज़रूर भरें।")
        else:
            new_row = {
                "Admission Year": admission_year, "Admission Session": admission_session, 
                "Eligibility Name": eligibility_name, "Admission Application Number": admission_app_no,
                "Admission Date": admission_date, "Unique ID": unique_id, "Roll No.": roll_no, 
                "Application Enrollment No.": app_enroll_no, "Enrollment No.": enrollment_no, 
                "Student Name": s_name, "Father Name": f_name, "Mother Name": m_name, "Date of Birth": dob, 
                "Category": category, "Subject Code": subject_code, "Subject ID": subject_id, "Subject": subject, "Duration": duration, 
                "Mobile Number": mobile, "Email ID": email, "Address": address, "Status": status_input, "Current Year": ""
            }
            
            current_db = load_live_data()
            updated_df = pd.concat([current_db, pd.DataFrame([new_row])], ignore_index=True)
            save_live_data(updated_df)
            st.success(f"✅ छात्र '{s_name}' का रिकॉर्ड डेटाबेस में सुरक्षित रूप से सहेज लिया गया है!")

    # ----------------------------------------------------------------------
# 👁️ STUDENT LIVE DATABASE LIST PANEL - STANDALONE VIEW MODALITY
# ----------------------------------------------------------------------
st.header("Student Live Database List (Viewer Mode)")

# Wrap layout with printable exclusion wrapper flags
st.markdown('<div class="print-hide">', unsafe_allow_html=True)

# Map core search structures dynamically matching custom administrative schema configs
search_options_map = {col: get_display_name(col) for col in DEFAULT_COLUMNS}

col_select, col_input = st.columns(2)

with col_select:
    selected_display_col = st.selectbox(
        "🔍 Choose Search Parameter Column:", 
        options=list(search_options_map.values()), 
        key="viewer_standalone_col_selector"
    )
    # Reverse trace mapped values to align search patterns precisely with the core back-end CSV columns
    selected_search_column = [k for k, v in search_options_map.items() if v == selected_display_col][0]

with col_input:
    search_query = st.text_input(
        f"Search inside '{selected_display_col}':", 
        key="viewer_standalone_query_input",
        placeholder="Type query to filter records..."
    )

st.markdown('</div>', unsafe_allow_html=True)

# Query String Evaluation Engine Execution
filtered_db = live_db.copy()
if search_query:
    filtered_db = filtered_db[filtered_db[selected_search_column].str.contains(search_query, case=False, na=False)]

# Present Analytical Summary Counter
st.metric(label="Total Matching Student Records Found", value=len(filtered_db))

if not filtered_db.empty:
    display_df = filtered_db.copy()
    
    # Map and rename database visualization outputs keeping Subject ID next to Subject Code fields
    display_df = display_df.rename(columns={c: get_display_name(c) for c in display_df.columns})
    display_df.insert(0, "S.No.", range(1, len(display_df) + 1))
    
    # Visual Interactive Grid Interface Render
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # Direct Print Optimization Layout and Download Block Controllers
    st.markdown('<div class="print-hide" style="margin-top: 15px;">', unsafe_allow_html=True)
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        st.download_button(
            label="📥 Download Data Sheet as CSV File", 
            data=filtered_db.to_csv(index=False).encode('utf-8'), 
            file_name="filtered_student_list.csv", 
            mime="text/csv", 
            use_container_width=True,
            key="viewer_standalone_export_action"
        )
        
    with col_btn2:
        st.markdown("""
            <button onclick="window.print()" style="width: 100%; background-color: #FF5733; color: white; border: none; padding: 0.55rem 1rem; border-radius: 0.5rem; cursor: pointer; font-weight: bold; font-size:15px; text-align: center; box-sizing: border-box;">🖨️ Open Native Landscape Print Engine</button>
        """, unsafe_allow_html=True)
        
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.warning("⚠️ No student records matched your specified search query criteria. Please refine your inputs.")

import streamlit as st
import pandas as pd
import os
import json

# Page configurations
st.set_page_config(layout="wide")

DB_FILE = "shared_student_database.csv"
MAP_FILE = "column_mapping_schema.json"

# 🎯 Master Reference Columns List
DEFAULT_COLUMNS = [
    "Admission Year", "Admission Session", "Eligibility Name", "Admission Application Number",
    "Admission Date", "Unique ID", "Roll No.", "Application Enrollment No.",
    "Enrollment No.", "Student Name", "Father Name", "Mother Name", "Date of Birth",
    "Category", "Subject Code", "Subject ID", "Subject", "Duration", "Mobile Number", "Email ID", "Address", "Status",
    "Current Year"
]

def load_live_data():
    if not os.path.exists(DB_FILE) or os.path.getsize(DB_FILE) == 0:
        return pd.DataFrame(columns=DEFAULT_COLUMNS)
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

def load_column_mappings():
    if os.path.exists(MAP_FILE):
        try:
            with open(MAP_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

if "column_mappings" not in st.session_state:
    st.session_state.column_mappings = load_column_mappings()

if "cce_foil_generated" not in st.session_state:
    st.session_state.cce_foil_generated = False

def get_display_name(internal_col_name):
    return st.session_state.column_mappings.get(internal_col_name, internal_col_name)

live_db = load_live_data()

# ----------------------------------------------------------------------
# 📝 3. COLLEGE CCE FOIL SHEET GENERATOR MODULE
# ----------------------------------------------------------------------
st.header("College CCE Foil Sheet Generator")
st.write("Institute of Law, Govt. Kamlaraja Girls Post-Graduate Autonomous College, Gwalior (M.P.)")

college_name = "GOVT. K.R.G. POST-GRADUATE AUTONOMOUS COLLEGE, GWALIOR (M.P.)"

if not live_db.empty:
    # --- PART 1: DROPDOWN SELECTIONS ---
    unique_subjects = sorted(list(set(live_db['Subject'].dropna().astype(str).str.strip())))
    unique_subjects = [sub for sub in unique_subjects if sub != ""]
    selected_subject = st.selectbox("📚 Select Subject (विषय चुनें):", options=["All Subjects"] + unique_subjects, key="cce_standalone_sub")

    year_sem_options = [
        "1 Semester", "2 Semester", "3 Semester", "4 Semester", "5 Semester", "6 Semester",
        "7 Semester", "8 Semester", "9 Semester", "10 Semester", "11 Semester", "12 Semester",
        "1 year", "2 year", "3 year", "4 year", "5 year", "6 year"
    ]
    
    def on_cce_param_change():
        st.session_state.cce_foil_generated = False

    chosen_option = st.selectbox("📆 Select Semester / Year:", year_sem_options, key="cce_standalone_year_sem", on_change=on_cce_param_change)

    # Evaluation mapping matrices
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

    # Preview processing grid data matching custom labels map
    st.write("📊 CCE Processing Student Grid View:")
    preview_db = live_db.copy()
    if selected_subject != "All Subjects":
        preview_db = preview_db[preview_db['Subject'].str.strip() == selected_subject]
    
    preview_render = preview_db[["Roll No.", "Student Name", "Subject Code", "Subject ID", "Subject", "Status", "Current Year"]].copy()
    preview_render = preview_render.rename(columns={c: get_display_name(c) for c in preview_render.columns})
    st.dataframe(preview_render, use_container_width=True, hide_index=True)

    if st.button("Generate CCE Foil Sheets Now", use_container_width=True, type="primary", key="cce_standalone_run_btn"):
        st.session_state.cce_foil_generated = True
        st.rerun()

    # --- PART 2: DATA PROCESSING ENGINE ---
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

            if selected_subject != "All Subjects" and student_sub != selected_subject: 
                continue
            if sub_code and sub_code.lower() != "nan" and detected_subject_code == "": 
                detected_subject_code = sub_code

            # EX-STUDENTS Cutoff Engine
            if status == "EX-STUDENT":
                is_ex_match = False
                gap_needed = int(target_year_text.split()[0])
                if gap_needed <= course_duration and adm_year == (max_year - gap_needed): 
                    is_ex_match = True
                if is_ex_match and roll and roll.lower() != "nan" and roll != "": 
                    ex_student_records.append(roll)
                continue

            # REGULAR Student validation with 1st Year Fallbacks
            if target_year_text in current_year_val and status == 'REGULAR':
                if not roll or roll.lower() == "nan" or roll == "":
                    if current_year_val == "1 year":
                        has_missing_roll_and_is_first_year_regular = True
                        regular_records.append(name if name else "[Unknown Name]")
                else: 
                    regular_records.append(roll)

        final_records_list = sorted(list(set(ex_student_records))) + sorted(list(set(regular_records)))

        st.markdown("---")
        st.subheader("⚙️ Processing Engine (Validating Student Eligibility)")
        st.info("🎯 Validation Analytics Summary:")
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1: st.metric("Valid Ex-Students (Prioritized First)", len(ex_student_records))
        with col_m2: st.metric("Valid Regular Students", len(regular_records))
        with col_m3: st.metric("Total Foil Records Captured", len(final_records_list))

        # --- PART 3: HTML FOIL GRID RENDERING ---
        if final_records_list:
            st.subheader("🖨️ Generated Visual CCE Foil Sheet")
            left_side_data = final_records_list[:30]
            right_side_data = final_records_list[30:60]
            dynamic_th_label = "Roll No. / Student Name" if has_missing_roll_and_is_first_year_regular else "Roll No."

            def generate_cce_html_block(items, start_idx, foil_label, has_data):
                if not has_data: 
                    return '<div class="foil-unit" style="border:none; background:transparent;"></div>'
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
                                    <tr><th style="border:1px solid black; padding:4px; width: 8%;">1</th><th style="border:1px solid black; padding:4px; width: 30%;" colspan="3">2</th></tr>
                                <tr><th style="border:1px solid black; padding:4px;" rowspan="2">Code No.</th><th style="border:1px solid black; padding:4px;" rowspan="2">{dynamic_th_label}</th><th style="border:1px solid black; padding:4px;" colspan="2">Marks Obtained</th></tr>
                                <tr><th style="border:1px solid black; padding:4px; width: 15%;">In Figures</th><th style="border:1px solid black; padding:4px; width: 45%;">In Words</th></tr>
                        """
                        # 1. डेटाबेस से प्राप्त वैध छात्र रिकॉर्ड्स को पंक्तियों (Rows) में जोड़ना
                        for idx_foil, item_val in enumerate(items, start=start_idx):
                            block += f"<tr><td style='border:1px solid black; padding:4px;'><b>{idx_foil}</b></td><td style='border:1px solid black; padding:4px;'>{item_val}</td><td style='border:1px solid black; padding:4px;'></td><td style='border:1px solid black; padding:4px;'></td></tr>"
                        
                        # 2. यदि छात्र 30 से कम हैं, तो फ़ॉर्मेट को बराबर रखने के लिए बची हुई खाली पंक्तियाँ (Blank Rows) जोड़ना
                        for k in range(len(items) + start_idx, 30 + start_idx):
                            block += "<tr><td style='border:1px solid black; padding:4px;'>&nbsp;</td><td style='border:1px solid black; padding:4px;'>&nbsp;</td><td style='border:1px solid black; padding:4px;'>&nbsp;</td><td style='border:1px solid black; padding:4px;'>&nbsp;</td></tr>"
                        
                        # 3. फ़ॉइल ब्लॉक के फुटर और परीक्षक के हस्ताक्षर क्षेत्र का संयोजन
                        block += f"""
                            </table>
                            <div class="note" style="font-size:10px; margin-top:10px;"><b>Note:</b> Roll Number and Marks awarded to the candidate may be entered under respective columns very carefully.</div>
                            <div class="footer-fields">Signature of Examiner......................................<br>Date: ___/___/2026</div>
                        </div>
                        """
                        return block

                    # लेफ्ट और राइट दोनों विज़ुअल ब्लॉक्स का निर्माण ट्रिगर करें
                    left_block_html = generate_cce_html_block(left_side_data, 1, "FOIL", True)
                    right_block_html = generate_cce_html_block(right_side_data, 31, "FOIL", len(right_side_data) > 0)

                    # प्रिटिंग मीडिया और फ़ॉन्ट को संतुलित करने के लिए CSS नियम
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
                    
                    # html2canvas स्क्रीनशॉट कैप्चर स्क्रिप्ट के साथ पूर्ण DOM संयोजन
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
                            <button onclick="downloadFoilAsPNG()" style="background:#4CAF50; color:white; border:none; padding:10px 20px; border-radius:5px; cursor:pointer; font-weight:bold; font-size:14px;">Download Foil in PNG File</button>
                        </div>
                        <div id="foil-capture-area">
                            {left_block_html}
                            {right_block_html}
                        </div>
                    </body>
                    </html>
                    """
                    st.components.v1.html(full_html, height=1600, scrolling=True)
                else:
                    st.error("इस फ़िल्टर के आधार पर कोई छात्र लाइव लिस्ट में नहीं मिला।")

# ----------------------------------------------------------------------
# 🛠️ 4. FULL ADMIN MANAGEMENT PANEL
# ----------------------------------------------------------------------
st.header("🛠️ Full Admin Management Panel")

# --- PART A: DYNAMIC COLUMN & TEXT BOX LABEL CUSTOMIZER ---
st.subheader("✏️ Dynamic Column & Text Box Label Customizer")
with st.expander("קॉलम और टेक्स्ट बॉक्स के नाम (Labels) बदलने के लिए यहाँ क्लिक करें", expanded=True):
    st.info("💡 यहाँ आप ओरिजिनल कॉलम नेम को हिंदी या किसी अन्य कस्टम नाम में बदल सकते हैं। यह ग्रिड और डेटा एंट्री फॉर्म दोनों जगह लागू होगा।")
    
    with st.form(key="standalone_admin_rename_form"):
        col_setup1, col_setup2 = st.columns(2)
        temp_mappings = {}
        
        for index, internal_name in enumerate(DEFAULT_COLUMNS):
            current_val = st.session_state.column_mappings.get(internal_name, internal_name)
            if index % 2 == 0:
                with col_setup1:
                    temp_mappings[internal_name] = st.text_input(f"Label for '{internal_name}':", value=current_val, key=f"ren_adm_{internal_name}")
            else:
                with col_setup2:
                    temp_mappings[internal_name] = st.text_input(f"Label for '{internal_name}':", value=current_val, key=f"ren_adm_{internal_name}")
                    
        if st.form_submit_button("Save Schema Labels Permanently", type="primary"):
            st.session_state.column_mappings = temp_mappings
            save_column_mappings(temp_mappings)
            st.success("✅ सभी कॉलम और इनपुट टेक्स्ट बॉक्स के नाम सफलतापूर्वक स्थायी रूप से अपडेट कर दिए गए हैं!")
            st.rerun()

st.markdown("---")

# --- PART B: GLOBAL PANEL VISIBILITY CONTROLLERS ---
st.subheader("🛡️ Global Panels Visibility Controller")
col_vis1, col_vis2, col_vis3, col_vis4 = st.columns(4)
with col_vis1:
    if st.button("👁️ Data Entry: Toggle", use_container_width=True, key="admin_vis_entry"):
        st.session_state.admin_hide_entry = not st.session_state.admin_hide_entry
        st.rerun()
with col_vis2:
    if st.button("👁️ Viewer Panel: Toggle", use_container_width=True, key="admin_vis_view"):
        st.session_state.admin_hide_viewer = not st.session_state.admin_hide_viewer
        st.rerun()
with col_vis3:
    if st.button("👁️ CCE Panel: Toggle", use_container_width=True, key="admin_vis_cce"):
        st.session_state.admin_hide_cce = not st.session_state.admin_hide_cce
        st.rerun()
with col_vis4:
    if st.button("👁️ Passwords: Toggle", use_container_width=True, key="admin_vis_cred"):
        st.session_state.admin_hide_cred_panel = not st.session_state.admin_hide_cred_panel
        st.rerun()

# --- PART C: USER PASSWORD MANAGEMENT RESET ENGINE ---
if not st.session_state.admin_hide_cred_panel:
    st.subheader("🔐 Change User Credentials System")
    with st.form(key="admin_credentials_form"):
        target_user = st.selectbox("किस यूजर का पासवर्ड बदलना चाहते हैं?", options=list(st.session_state.credentials.keys()))
        new_password = st.text_input("नया पासवर्ड दर्ज करें:", type="password")
        if st.form_submit_button("Update Password Now", type="primary"):
            if new_password.strip() == "": 
                st.error("❌ पासवर्ड खाली नहीं हो सकता।")
            else:
                st.session_state.credentials[target_user]["password"] = new_password
                save_credentials(st.session_state.credentials)
                st.success(f"✅ '{target_user}' का पासवर्ड सफलतापूर्वक अपडेट और सेव कर दिया गया है!")

st.markdown("---")

# --- PART D: INTERACTIVE REORDERING & COLUMN MATRIX CONTROLS ---
st.subheader("📊 Master Database List View & Advanced Controls")
col_ctrl1, col_ctrl2, col_ctrl3 = st.columns(3)
with col_ctrl1:
    if st.button("📝 एडिट टेक्स्ट फंक्शन ऑन/ऑफ करें", use_container_width=True, key="admin_toggle_text_edit"):
        st.session_state.admin_unhide_edit = not st.session_state.admin_unhide_edit
        st.rerun()
with col_ctrl2:
    if st.button("🔀 कॉलम मूव बटन्स ऑन/ऑफ करें", use_container_width=True, key="admin_toggle_col_shift"):
        st.session_state.admin_unhide_move = not st.session_state.admin_unhide_move
        st.rerun()
with col_ctrl3:
    lock_label = "🔒 लिस्ट लॉक करें" if not st.session_state.admin_lock_state else "🔓 लिस्ट अनलॉक करें"
    if st.button(lock_label, use_container_width=True, key="admin_toggle_lock"):
        st.session_state.admin_lock_state = not st.session_state.admin_lock_state
        st.rerun()

if st.session_state.admin_unhide_move and not st.session_state.admin_lock_state:
    if "Subject ID" not in st.session_state.admin_columns_order:
        st.session_state.admin_columns_order = DEFAULT_COLUMNS.copy()
        
    target_col = st.selectbox("मूव करने के लिए कॉलम चुनें:", options=st.session_state.admin_columns_order, key="admin_col_shift_box")
    c_left, c_right = st.columns(2)
    if c_left.button("⬅️ Shift Left", use_container_width=True, key="admin_shift_l_trigger"):
        idx = st.session_state.admin_columns_order.index(target_col)
        if idx > 0:
            st.session_state.admin_columns_order[idx], st.session_state.admin_columns_order[idx-1] = st.session_state.admin_columns_order[idx-1], st.session_state.admin_columns_order[idx]
            st.rerun()
    if c_right.button("➡️ Shift Right", use_container_width=True, key="admin_shift_r_trigger"):
        idx = st.session_state.admin_columns_order.index(target_col)
        if idx < len(st.session_state.admin_columns_order) - 1:
            st.session_state.admin_columns_order[idx], st.session_state.admin_columns_order[idx+1] = st.session_state.admin_columns_order[idx+1], st.session_state.admin_columns_order[idx]
            st.rerun()

if "Subject ID" not in st.session_state.admin_columns_order:
    st.session_state.admin_columns_order = DEFAULT_COLUMNS.copy()

ordered_db = live_db[st.session_state.admin_columns_order].copy()

# Apply mapped label customizer scheme across data view frames
ordered_db = ordered_db.rename(columns={c: get_display_name(c) for c in ordered_db.columns})
ordered_db.insert(0, "S.No.", range(1, len(ordered_db) + 1))

st.write(f"कुल मास्टर रिकॉर्ड संख्या: **{len(ordered_db)}**")

# --- PART E: LIVE RENDER MATRIX MODE (READ-ONLY VS DATA EDITOR) ---
if not st.session_state.admin_lock_state and st.session_state.admin_unhide_edit:
    st.warning("⚠️ लाइव डायरेक्ट टेक्स्ट संपादन सक्रिय है। ग्रिड में किया गया बदलाव सीधे CSV फ़ाइल में सुरक्षित सेव हो जाएगा।")
    edited_df = st.data_editor(
        ordered_db, 
        use_container_width=True,
                use_container_width=True, 
        disabled=["S.No.", get_display_name("Current Year")], 
        key="admin_live_editor_grid", 
        hide_index=True
    )
    clean_edited = edited_df.drop(columns=["S.No."])
    
    # 1. बदले हुए विज़ुअल नामों (Labels) को वापस बैकएंड के ओरिजिनल नामों के साथ मैप करना
    reverse_mapping = {get_display_name(k): k for k in st.session_state.admin_columns_order}
    
    # 2. डेटाबेस को सुरक्षित रूप से री-बिल्ड करने के लिए एक खाली डिक्शनरी संरचना
    synced_data = {col: [] for col in DEFAULT_COLUMNS}
    
    # 3. एडिटेड डेटा फ्रेम से लूप चलाकर ओरिजिनल कुंजियों (Keys) पर डेटा व्यवस्थित करना
    for _, row_edit in clean_edited.iterrows():
        for display_name_key in clean_edited.columns:
            internal_key = reverse_mapping.get(display_name_key, display_name_key)
            if internal_key in synced_data:
                synced_data[internal_key].append(row_edit[display_name_key])
    
    # 4. 'Current Year' को छोड़कर बाकी सारा डेटा मुख्य डेटाबेस एरे में सिंक करना
    for col_k in DEFAULT_COLUMNS:
        if col_k != "Current Year" and col_k in synced_data and len(synced_data[col_k]) == len(live_db):
            live_db[col_k] = synced_data[col_k]
            
    # 5. संशोधित डेटाबेस को CSV फ़ाइल में स्थायी सेव करना
    save_live_data(live_db)
else: 
    # यदि लिस्ट लॉक है, तो केवल रीड-ओनली डेटाफ्रेम दिखाना
    st.dataframe(ordered_db, use_container_width=True, hide_index=True)
        
    
