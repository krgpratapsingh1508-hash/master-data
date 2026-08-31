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
PANEL_NAME_FILE = "panel_names_schema.json"

# 🔒 क्रेडेंशियल्स डिफ़ॉल्ट डेटा
DEFAULT_CREDENTIALS = {
    "entry": {"password": "entry123", "role": "data_entry"},
    "viewer": {"password": "viewer123", "role": "list_viewer"},
    "cce": {"password": "cce123", "role": "cce_handler"},
    "admin": {"password": "admin123", "role": "full_admin"}
}

# 🛠️ डिफ़ॉल्ट 15 पैनल्स की डिक्शनरी मैपिंग (P1 से P15)
DEFAULT_PANELS = {
    "P1": "Panal entry",
    "P2": "Panal admission",
    "P3": "Panal enrollment",
    "P4": "Panal scholarship",
    "P5": "Panal result",
    "P6": "Panal promotion",
    "P7": "Panal foil",
    "P8": "Panal cce record",
    "P9": "Panal P9 Placeholder",
    "P10": "Panal P10 Placeholder",
    "P11": "Panal P11 Placeholder",
    "P12": "Panal P12 Placeholder",
    "P13": "Panal P13 Placeholder",
    "P14": "Panal viewer",
    "P15": "Panel admin"
}

def load_credentials():
    if os.path.exists(CRED_FILE):
        try:
            with open(CRED_FILE, "r") as f: return json.load(f)
        except: return DEFAULT_CREDENTIALS.copy()
    else:
        with open(CRED_FILE, "w") as f: json.dump(DEFAULT_CREDENTIALS, f)
        return DEFAULT_CREDENTIALS.copy()

def save_credentials(creds):
    with open(CRED_FILE, "w") as f: json.dump(creds, f)

def load_column_mappings():
    if os.path.exists(MAP_FILE):
        try:
            with open(MAP_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: return {}
    return {}

def save_column_mappings(mapping_dict):
    with open(MAP_FILE, "w", encoding="utf-8") as f:
        json.dump(mapping_dict, f, ensure_ascii=False, indent=4)

# 🔄 डायनेमिक पैनल नेम लोडर और सेवर
def load_panel_names():
    if os.path.exists(PANEL_NAME_FILE):
        try:
            with open(PANEL_NAME_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: return DEFAULT_PANELS.copy()
    return DEFAULT_PANELS.copy()

def save_panel_names(panel_dict):
    with open(PANEL_NAME_FILE, "w", encoding="utf-8") as f:
        json.dump(panel_dict, f, ensure_ascii=False, indent=4)

if "credentials" not in st.session_state: st.session_state.credentials = load_credentials()
if "column_mappings" not in st.session_state: st.session_state.column_mappings = load_column_mappings()
if "panel_names" not in st.session_state: st.session_state.panel_names = load_panel_names()

# 🎯 मास्टर कॉलम्स सूची
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
            if col not in df.columns: df[col] = ""
                
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
if "admin_columns_order" not in st.session_state: st.session_state.admin_columns_order = DEFAULT_COLUMNS.copy()
if "admin_lock_state" not in st.session_state: st.session_state.admin_lock_state = True  
if "admin_unhide_edit" not in st.session_state: st.session_state.admin_unhide_edit = False
if "admin_unhide_move" not in st.session_state: st.session_state.admin_unhide_move = False
if "cce_foil_generated" not in st.session_state: st.session_state.cce_foil_generated = False

# 🛠️ 15 पैनल्स की विज़िबिलिटी को स्वतंत्र रूप से कंट्रोल करने वाले फ्लैग्स
for k in DEFAULT_PANELS.keys():
    state_key = f"hide_panel_{k}"
    if state_key not in st.session_state: st.session_state[state_key] = False

if "admin_hide_cred_panel" not in st.session_state: st.session_state.admin_hide_cred_panel = False
if "admin_hide_master_data" not in st.session_state: st.session_state.admin_hide_master_data = False
if "admin_hide_data_toggle_btn" not in st.session_state: st.session_state.admin_hide_data_toggle_btn = False

live_db = load_live_data()

# 🛠️ हेल्पर फंक्शन
def get_display_name(internal_col_name):
    return st.session_state.column_mappings.get(internal_col_name, internal_col_name)

def get_panel_title(panel_id):
    return st.session_state.panel_names.get(panel_id, DEFAULT_PANELS[panel_id])

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
# 🔑 लॉगिन अधिकृत सत्र
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
# 📝 P1: PANEL ENTRY MODULE
# ----------------------------------------------------------------------
st.header("📝 Panal Entry (Student Data Onboarding)")

entry_method = st.selectbox(
    "⚙️ डेटा एंट्री का माध्यम चुनें:",
    options=["📁 CSV फ़ाइल बल्क अपलोड (Bulk CSV Upload)", "➕ नया छात्र मैनुअल फॉर्म (Manual Form Entry)"]
)

if entry_method == "📁 CSV फ़ाइल बल्क अपलोड (Bulk CSV Upload)":
    uploaded_file = st.file_uploader("CSV फ़ाइल चुनें", type=["csv"])
    if uploaded_file is not None:
        if st.button("Upload CSV Now", type="primary", use_container_width=True):
            try:
                uploaded_df = pd.read_csv(uploaded_file, dtype=str).fillna("")
                # मिसिंग कॉलम को खाली स्ट्रिंग के साथ जोड़ना
                for col in DEFAULT_COLUMNS:
                    if col not in uploaded_df.columns: uploaded_df[col] = ""
                
                cleaned_uploaded_df = uploaded_df[DEFAULT_COLUMNS].copy()
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
            st.success("✅ नया छात्र रिकॉर्ड सफलतापूर्वक 'shared_student_database.csv' में सुरक्षित सेव हो गया है!")

st.markdown("---")
# वर्तमान में सेव डेटा का एक त्वरित काउंट प्रीव्यू
current_db = load_live_data()
st.metric(label="डेटाबेस में कुल सुरक्षित छात्र रिकॉर्ड्स", value=len(current_db))

# ----------------------------------------------------------------------
# 🎓 P2: PANEL ADMISSION MODULE
# ----------------------------------------------------------------------
st.header("🎓 Panal Admission (Admission Control & Verification)")

live_db = load_live_data()

if live_db.empty:
    st.warning("⚠️ डेटाबेस वर्तमान में खाली है। कृपया पहले Panel 1 (Entry) के माध्यम से छात्रों का डेटा जोड़ें।")
else:
    # एडमिशन फ़िल्टरेशन टूल्स
    st.subheader("🔍 Filter Admission Records")
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        unique_years = sorted(list(set(live_db["Admission Year"].dropna().astype(str))))
        selected_year = st.selectbox("Admission Year चुनें:", ["All"] + [y for y in unique_years if y != ""])
    with col_f2:
        unique_sessions = sorted(list(set(live_db["Admission Session"].dropna().astype(str))))
        selected_session = st.selectbox("Admission Session चुनें:", ["All"] + [s for s in unique_sessions if s != ""])
    with col_f3:
        unique_status = sorted(list(set(live_db["Status"].dropna().astype(str))))
        selected_status = st.selectbox("Current Status चुनें:", ["All"] + [st_val for st_val in unique_status if st_val != ""])

    # डेटा फ़िल्टर करना
    filtered_admission = live_db.copy()
    if selected_year != "All":
        filtered_admission = filtered_admission[filtered_admission["Admission Year"] == selected_year]
    if selected_session != "All":
        filtered_admission = filtered_admission[filtered_admission["Admission Session"] == selected_session]
    if selected_status != "All":
        filtered_admission = filtered_admission[filtered_admission["Status"] == selected_status]

    st.write(f"फ़िल्टर किए गए कुल एडमिशन रिकॉर्ड: **{len(filtered_admission)}**")

    # 🔄 एडमिशन स्टेटस अपडेट और वेरिफिकेशन काउंटर
    st.subheader("📝 Bulk Update Admission Status & Application Details")
    st.info("💡 नीचे दी गई ग्रिड में आप सीधे Admission Date, Application Number या Status (जैसे Regular, Pending) को संपादित (Edit) कर सकते हैं।")

    # एडमिशन से संबंधित महत्वपूर्ण कॉलम्स को एडिटर में प्रदर्शित करना
    admission_cols = [
        "Admission Application Number", "Admission Year", "Admission Session", 
        "Student Name", "Father Name", "Admission Date", "Status", "Unique ID"
    ]
    
    # सुनिश्चित करें कि ग्रिड में केवल वही कॉलम्स दिखें जो उपलब्ध हैं
    display_cols = [c for c in admission_cols if c in filtered_admission.columns]
    render_df = filtered_admission[display_cols].copy()
    render_df.insert(0, "S.No.", range(1, len(render_df) + 1))

    # इंटरैक्टिव डेटा एडिटर ग्रिड
    edited_admission_df = st.data_editor(
        render_df,
        use_container_width=True,
        disabled=["S.No.", "Student Name", "Father Name"], # छात्र का नाम और पिता का नाम लॉक रहेगा
        key="admission_live_editor",
        hide_index=True
    )

    if st.button("Save & Sync Admission Changes", type="primary", use_container_width=True):
        try:
            # एडिटर से प्राप्त क्लीन डेटा (S.No. हटाकर)
            clean_edited = edited_admission_df.drop(columns=["S.No."])
            
            # मुख्य डेटाबेस इंडेक्स मिलान तकनीक द्वारा अपडेट करना
            for _, row_edit in clean_edited.iterrows():
                unique_app_no = row_edit["Admission Application Number"]
                
                # 'Admission Application Number' के आधार पर मुख्य डेटाबेस में रो ढूंढना
                idx_matches = live_db[live_db["Admission Application Number"] == unique_app_no].index
                
                if not idx_matches.empty:
                    match_idx = idx_matches[0]
                    # संपादन योग्य फ़ील्ड्स को मुख्य डेटाबेस में सिंक करना
                    live_db.at[match_idx, "Admission Date"] = row_edit["Admission Date"]
                    live_db.at[match_idx, "Status"] = row_edit["Status"]
                    live_db.at[match_idx, "Unique ID"] = row_edit["Unique ID"]
                    live_db.at[match_idx, "Admission Year"] = row_edit["Admission Year"]
                    live_db.at[match_idx, "Admission Session"] = row_edit["Admission Session"]

            save_live_data(live_db)
            st.success("✅ एडमिशन डेटाबेस सफलतापूर्वक सिंक और अपडेट कर दिया गया है!")
            st.rerun()
        except Exception as e:
            st.error(f"डेटा सुरक्षित करने में त्रुटि: {e}")

st.markdown("---")
# त्वरित एडमिशन एनालिटिक्स समरी काउंटर
if not live_db.empty and "Status" in live_db.columns:
    st.subheader("📊 Admission Analytics Summary")
    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1:
        st.metric("Total Admissions Registered", len(live_db))
    with col_c2:
        regular_count = len(live_db[live_db["Status"].str.upper().isin(["REGULAR", "REGULAR STUDENT"])])
        st.metric("Confirmed Regular Students", regular_count)
    with col_c3:
        pending_count = len(live_db[live_db["Status"].str.upper() == "PENDING"])
        st.metric("Pending Verification Applications", pending_count)

# ----------------------------------------------------------------------
# 📑 P3: PANEL ENROLLMENT MODULE
# ----------------------------------------------------------------------
st.header("📑 Panal Enrollment (University Enrollment Manager)")

# डेटाबेस लोड करें
live_db = load_live_data()

if live_db.empty:
    st.warning("⚠️ डेटाबेस वर्तमान में खाली है। कृपया पहले Panel 1 (Entry) के माध्यम से छात्रों का डेटा जोड़ें।")
else:
    # एनरोलमेंट स्पेसिफिक क्विक फिल्टर्स
    st.subheader("🔍 Filter Enrollment Records")
    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        unique_subjects = sorted(list(set(live_db["Subject"].dropna().astype(str))))
        selected_subject = st.selectbox("Subject (विषय) चुनें:", ["All"] + [sub for sub in unique_subjects if sub.strip() != ""])
        
    with col_f2:
        enroll_filter_type = st.selectbox(
            "Enrollment Status फ़िल्टर:",
            options=["All Students", "Missing Enrollment Number Only (सिर्फ खाली एनरोलमेंट वाले)", "Allocated Enrollment Number Only"]
        )

    # डेटा फ़िल्टरिंग लॉजिक
    filtered_enrollment = live_db.copy()
    
    if selected_subject != "All":
        filtered_enrollment = filtered_enrollment[filtered_enrollment["Subject"] == selected_subject]
        
    if enroll_filter_type == "Missing Enrollment Number Only (सिर्फ खाली एनरोलमेंट वाले)":
        filtered_enrollment = filtered_enrollment[
            (filtered_enrollment["Enrollment No."].str.strip() == "") | 
            (filtered_enrollment["Enrollment No."].isna()) |
            (filtered_enrollment["Enrollment No."].str.lower() == "nan")
        ]
    elif enroll_filter_type == "Allocated Enrollment Number Only":
        filtered_enrollment = filtered_enrollment[
            (filtered_enrollment["Enrollment No."].str.strip() != "") & 
            (~filtered_enrollment["Enrollment No."].isna()) &
            (filtered_enrollment["Enrollment No."].str.lower() != "nan")
        ]

    st.write(f"फ़िल्टर के आधार पर कुल रिकॉर्ड्स की संख्या: **{len(filtered_enrollment)}**")

    # 🔄 लाइव डेटा एडिटर ग्रिड मॉड्यूल
    st.subheader("✏️ Bulk Entry / Update University Enrollment Details")
    st.info("💡 नीचे दी गई ग्रिड में आप सीधे 'Application Enrollment No.' और 'Enrollment No.' टाइप करके भर सकते हैं।")

    # एनरोलमेंट के लिए जरूरी चुनिंदा कॉलम्स का सेट
    enrollment_display_cols = [
        "Admission Application Number", "Student Name", "Father Name", 
        "Subject", "Application Enrollment No.", "Enrollment No."
    ]
    
    display_cols = [c for c in enrollment_display_cols if c in filtered_enrollment.columns]
    render_df = filtered_enrollment[display_cols].copy()
    render_df.insert(0, "S.No.", range(1, len(render_df) + 1))

    # इंटरैक्टिव डेटा एडिटर ग्रिड चालू करना
    edited_enrollment_df = st.data_editor(
        render_df,
        use_container_width=True,
        disabled=["S.No.", "Admission Application Number", "Student Name", "Father Name", "Subject"], # मूल विवरण लॉक रहेंगे
        key="enrollment_live_editor",
        hide_index=True
    )

    if st.button("Save & Sync Enrollment Numbers", type="primary", use_container_width=True):
        try:
            clean_edited = edited_enrollment_df.drop(columns=["S.No."])
            
            # सिंकिंग प्रक्रिया के लिए मास्टर लूप
            for _, row_edit in clean_edited.iterrows():
                unique_app_no = str(row_edit["Admission Application Number"]).strip()
                
                # मुख्य डेटाबेस में उस विशिष्ट पंक्ति (Row) का इंडेक्स सर्च करना
                idx_matches = live_db[live_db["Admission Application Number"].astype(str).str.strip() == unique_app_no].index
                
                if not idx_matches.empty:
                    for match_idx in idx_matches:
                        # एनरोलमेंट फ़ील्ड्स को मास्टर सिंक में असाइन करना
                        live_db.at[match_idx, "Application Enrollment No."] = str(row_edit["Application Enrollment No."]).strip()
                        live_db.at[match_idx, "Enrollment No."] = str(row_edit["Enrollment No."]).strip()

            save_live_data(live_db)
            st.success("✅ विश्वविद्यालय नामांकन नंबर (Enrollment Database) सफलतापूर्वक सिंक और अपडेट हो गया है!")
            st.rerun()
        except Exception as e:
            st.error(f"डेटा अपडेट करने में तकनीकी त्रुटि आई: {e}")

st.markdown("---")
# एनरोलमेंट ट्रैकिंग स्टेटिस्टिक्स काउंटर्स
if not live_db.empty:
    st.subheader("📊 Enrollment Analytics Overview")
    col_c1, col_c2, col_c3 = st.columns(3)
    
    with col_c1:
        st.metric("Total Students in Database", len(live_db))
    with col_c2:
        allocated_count = len(live_db[
            (live_db["Enrollment No."].str.strip() != "") & 
            (live_db["Enrollment No."].str.lower() != "nan") &
            (~live_db["Enrollment No."].isna())
        ])
        st.metric("Total Enrolled Students (नंबर जारी हुआ)", allocated_count)
    with col_c3:
        pending_enroll = len(live_db) - allocated_count
        st.metric("Pending Enrollment Allocation (शेष छात्र)", pending_enroll)

# ----------------------------------------------------------------------
# 💰 P4: PANEL SCHOLARSHIP MODULE
# ----------------------------------------------------------------------
st.header("💰 Panal Scholarship (Portal & Category Matrix Control)")

# डेटाबेस लोड करें
live_db = load_live_data()

# यदि डेटाबेस में 'Scholarship Status' कॉलम नहीं है, तो उसे डायनेमिकली इनिशियलाइज़ करें
if "Scholarship Status" not in live_db.columns:
    live_db["Scholarship Status"] = "Not Applied"

if live_db.empty:
    st.warning("⚠️ डेटाबेस वर्तमान में खाली है। कृपया पहले Panel 1 (Entry) के माध्यम से छात्रों का डेटा जोड़ें।")
else:
    # स्कॉलरशिप फ़िल्टरेशन टूल्स
    st.subheader("🔍 Filter Scholarship Candidates")
    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        # कैटेगरी आधारित शॉर्टिंग (स्कॉलरशिप आमतौर पर रिजर्व्ड कैटेगरी के लिए ट्रैक होती है)
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

    st.write(f"फ़िल्टर के आधार पर योग्य छात्र संख्या: **{len(filtered_scholarship)}**")

    # 🔄 लाइव डेटा एडिटर ग्रिड मॉड्यूल
    st.subheader("✏️ Track & Update Scholarship Verification Matrix")
    st.info("💡 नीचे दी गई ग्रिड में आप सीधे छात्रों का 'Scholarship Status' ड्रापडाउन मेनू से बदल सकते हैं।")

    # स्कॉलरशिप ट्रैकिंग के लिए जरूरी डिस्प्ले कॉलम्स
    scholarship_display_cols = [
        "Admission Application Number", "Unique ID", "Student Name", 
        "Category", "Mobile Number", "Scholarship Status"
    ]
    
    display_cols = [c for c in scholarship_display_cols if c in filtered_scholarship.columns]
    render_df = filtered_scholarship[display_cols].copy()
    render_df.insert(0, "S.No.", range(1, len(render_df) + 1))

    # इंटरैक्टिव डेटा एडिटर ग्रिड कॉन्फ़िगरेशन
    edited_scholarship_df = st.data_editor(
        render_df,
        use_container_width=True,
        disabled=["S.No.", "Admission Application Number", "Unique ID", "Student Name", "Category", "Mobile Number"], # केवल स्टेटस एडिट होगा
        column_config={
            "Scholarship Status": st.column_config.SelectboxColumn(
                "Scholarship Status",
                help="छात्रवृत्ति की वर्तमान स्थिति चुनें",
                options=["Not Applied", "Applied", "Sanctioned", "Disbursed", "Rejected"],
                required=True,
            )
        },
        key="scholarship_live_editor",
        hide_index=True
    )

    if st.button("Save & Sync Scholarship Matrix", type="primary", use_container_width=True):
        try:
            clean_edited = edited_scholarship_df.drop(columns=["S.No."])
            
            # डेटाबेस अपडेशन के लिए की-मैपिंग लूप
            for _, row_edit in clean_edited.iterrows():
                unique_app_no = str(row_edit["Admission Application Number"]).strip()
                
                # मुख्य डेटाबेस में रो का इंडेक्स सर्च करना
                idx_matches = live_db[live_db["Admission Application Number"].astype(str).str.strip() == unique_app_no].index
                
                if not idx_matches.empty:
                    for match_idx in idx_matches:
                        live_db.at[match_idx, "Scholarship Status"] = str(row_edit["Scholarship Status"]).strip()

            save_live_data(live_db)
            st.success("✅ छात्रवृत्ति मैट्रिक्स (Scholarship Portal Status) सफलतापूर्वक सिंक और अपडेट हो गया है!")
            st.rerun()
        except Exception as e:
            st.error(f"डेटा अपडेट करने में तकनीकी त्रुटि आई: {e}")

st.markdown("---")
# स्कॉलरशिप कैटेगरी आधारित एनालिटिक्स समरी
if not live_db.empty:
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
        # सामान्य वर्ग को छोड़कर आरक्षित श्रेणी की गणना
        reserved_count = len(live_db[live_db["Category"].str.upper().isin(["OBC", "SC", "ST"])])
        st.metric("Total Eligible Reserved Category Candidates", reserved_count)

# ----------------------------------------------------------------------
# 📊 P5: PANEL RESULT MODULE
# ----------------------------------------------------------------------
st.header("📊 Panal Result (Tabulation Register & Exam Controller)")

# डेटाबेस लोड करें
live_db = load_live_data()

# यदि डेटाबेस में परिणाम से संबंधित डायनेमिक कॉलम्स नहीं हैं, तो उन्हें इनिशियलाइज़ करें
result_dynamic_fields = ["Marks Obtained", "Result Status", "Exam Remarks"]
for field in result_dynamic_fields:
    if field not in live_db.columns:
        live_db[field] = ""

if live_db.empty:
    st.warning("⚠️ डेटाबेस वर्तमान में खाली है। कृपया पहले Panel 1 (Entry) के माध्यम से छात्रों का डेटा जोड़ें।")
else:
    # परिणाम फ़िल्टरेशन टूल्स
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

    # 🔄 लाइव डेटा एडिटर ग्रिड मॉड्यूल
    st.subheader("✏️ Bulk Entry / Tabulation of Marks & Results Status")
    st.info("💡 नीचे दी गई ग्रिड में आप सीधे छात्रों के 'Marks Obtained', 'Result Status' और 'Exam Remarks' को प्रविष्ट कर सकते हैं।")

    # परिणाम ट्रैकिंग के लिए प्रदर्शित किए जाने वाले चुनिंदा कॉलम्स
    result_display_cols = [
        "Admission Application Number", "Roll No.", "Enrollment No.", 
        "Student Name", "Subject", "Marks Obtained", "Result Status", "Exam Remarks"
    ]
    
    display_cols = [c for c in result_display_cols if c in filtered_result.columns]
    render_df = filtered_result[display_cols].copy()
    render_df.insert(0, "S.No.", range(1, len(render_df) + 1))

    # इंटरैक्टिव डेटा एडिटर ग्रिड कॉन्फ़िगरेशन
    edited_result_df = st.data_editor(
        render_df,
        use_container_width=True,
        disabled=["S.No.", "Admission Application Number", "Roll No.", "Enrollment No.", "Student Name", "Subject"], # मूल विवरणी लॉक रहेगी
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

    if st.button("Save & Sync Tabulation Register", type="primary", use_container_width=True):
        try:
            clean_edited = edited_result_df.drop(columns=["S.No."])
            
            # डेटाबेस अपडेशन के लिए की-मैपिंग लूप
            for _, row_edit in clean_edited.iterrows():
                unique_app_no = str(row_edit["Admission Application Number"]).strip()
                
                # मुख्य डेटाबेस में रो का इंडेक्स सर्च करना
                idx_matches = live_db[live_db["Admission Application Number"].astype(str).str.strip() == unique_app_no].index
                
                if not idx_matches.empty:
                    for match_idx in idx_matches:
                        live_db.at[match_idx, "Marks Obtained"] = str(row_edit["Marks Obtained"]).strip()
                        live_db.at[match_idx, "Result Status"] = str(row_edit["Result Status"]).strip()
                        live_db.at[match_idx, "Exam Remarks"] = str(row_edit["Exam Remarks"]).strip()

            save_live_data(live_db)
            st.success("✅ परीक्षा परिणाम पंजी (Tabulation Register) सफलतापूर्वक सिंक और अपडेट हो गई है!")
            st.rerun()
        except Exception as e:
            st.error(f"डेटा अपडेट करने में तकनीकी त्रुटि आई: {e}")

st.markdown("---")
# परिणाम आधारित एनालिटिक्स समरी
if not live_db.empty:
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
# 📈 P6: PANEL PROMOTION MODULE
# ----------------------------------------------------------------------
st.header("📈 Panal Promotion (Academic Year Batch Progression Control)")

# डेटाबेस लोड करें
live_db = load_live_data()

# यदि डेटाबेस में प्रमोशन से संबंधित डायनेमिक कॉलम नहीं है, तो इनिशियलाइज़ करें
if "Promotion Status" not in live_db.columns:
    live_db["Promotion Status"] = "Eligible"

if live_db.empty:
    st.warning("⚠️ डेटाबेस वर्तमान में खाली है। कृपया पहले Panel 1 (Entry) के माध्यम से छात्रों का डेटा जोड़ें।")
else:
    # प्रमोशन फ़िल्टरेशन टूल्स
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

    # 🔄 लाइव डेटा एडिटर ग्रिड मॉड्यूल
    st.subheader("✏️ Bulk Track & Update Batch Progression Status")
    st.info("💡 नीचे दी गई ग्रिड में आप प्रमोट होने वाले छात्रों का 'Promotion Status' और 'Status' फ़ील्ड अपडेट कर सकते हैं।")

    # प्रमोशन ट्रैकिंग के लिए प्रदर्शित किए जाने वाले चुनिंदा कॉलम्स
    promotion_display_cols = [
        "Admission Application Number", "Roll No.", "Student Name", 
        "Current Year", "Status", "Promotion Status"
    ]
    
    display_cols = [c for c in promotion_display_cols if c in filtered_promotion.columns]
    render_df = filtered_promotion[display_cols].copy()
    render_df.insert(0, "S.No.", range(1, len(render_df) + 1))

    # इंटरैक्टिव डेटा एडिटर ग्रिड कॉन्फ़िगरेशन
    edited_promotion_df = st.data_editor(
        render_df,
        use_container_width=True,
        disabled=["S.No.", "Admission Application Number", "Roll No.", "Student Name", "Current Year"], # मूल विवरणी लॉक रहेगी
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

    if st.button("Save & Sync Promotion Register", type="primary", use_container_width=True):
        try:
            clean_edited = edited_promotion_df.drop(columns=["S.No."])
            
            # मास्टर डेटाबेस सिंकिंग लूप
            for _, row_edit in clean_edited.iterrows():
                unique_app_no = str(row_edit["Admission Application Number"]).strip()
                
                # मुख्य डेटाबेस में रो का इंडेक्स सर्च करना
                idx_matches = live_db[live_db["Admission Application Number"].astype(str).str.strip() == unique_app_no].index
                
                if not idx_matches.empty:
                    for match_idx in idx_matches:
                        live_db.at[match_idx, "Status"] = str(row_edit["Status"]).strip()
                        live_db.at[match_idx, "Promotion Status"] = str(row_edit["Promotion Status"]).strip()

            save_live_data(live_db)
            st.success("✅ छात्र बैच प्रमोशन पंजी (Promotion Register) सफलतापूर्वक सिंक और अपडेट हो गई है!")
            st.rerun()
        except Exception as e:
            st.error(f"डेटा अपडेट करने में तकनीकी त्रुटि आई: {e}")

st.markdown("---")
# प्रमोशन आधारित एनालिटिक्स समरी काउंटर्स
if not live_db.empty:
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
# 🖨️ P7: PANEL FOIL SHEET GENERATOR MODULE
# ----------------------------------------------------------------------
st.header("🖨️ Panal Foil (University CCE Foil Sheet Generator)")
st.write("Institute of Law, Govt. Kamlaraja Girls Post-Graduate Autonomous College, Gwalior (M.P.)")

college_name = "GOVT. K.R.G. POST-GRADUATE AUTONOMOUS COLLEGE, GWALIOR (M.P.)"
live_db = load_live_data()

if live_db.empty:
    st.warning("⚠️ डेटाबेस वर्तमान में खाली है। कृपया पहले Panel 1 (Entry) के माध्यम से छात्रों का डेटा जोड़ें।")
else:
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

        st.subheader("📊 Live Candidates Verification Sheet")
        preview_db = live_db.copy()
        if selected_subject != "All Subjects":
            preview_db = preview_db[preview_db['Subject'].str.strip() == selected_subject]
        
        preview_render = preview_db[["Roll No.", "Student Name", "Subject Code", "Subject", "Status", "Current Year"]].copy()
        st.dataframe(preview_render, use_container_width=True, hide_index=True)

        if st.button("Generate Foil Sheets Now", use_container_width=True, type="primary"):
            st.session_state.cce_foil_generated = True
            st.rerun()

        # --- डेटा इवैल्यूएशन प्रोसेसिंग इंजन ---
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

                # EX-STUDENT क्राइटेरिया वेलिडेशन
                if status == "EX-STUDENT":
                    is_ex_match = False
                    try: gap_needed = int(target_year_text.split())
                    except: gap_needed = 1
                        
                    if gap_needed <= course_duration and adm_year == (max_year - gap_needed): is_ex_match = True
                    if is_ex_match and roll and roll.lower() != "nan" and roll != "": ex_student_records.append(roll)
                    continue

                # REGULAR STUDENT / REGULAR वेलिडेशन लॉजिक
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

            # --- डिजिटल फ़ॉइल कैनवास जनरेटर इंजन ---
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
                    
                    # वास्तविक छात्र डेटा भरना
                    for idx_foil, item_val in enumerate(items, start=start_idx):
                        block += f"<tr><td style='border:1px solid black; padding:4px; text-align:center;'><b>{idx_foil}</b></td><td style='border:1px solid black; padding:4px;'>{item_val}</td><td style='border:1px solid black; padding:4px;'></td><td style='border:1px solid black; padding:4px;'></td></tr>"
                    
                    # शीट को व्यवस्थित करने के लिए बची हुई ३५ तक की खाली पंक्तियाँ जोड़ना
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
# 📋 P8: PANEL CCE RECORD MODULE
# ----------------------------------------------------------------------
st.header("📋 Panal CCE Record (Internal Assessment Marks Ledger)")

# डेटाबेस लोड करें
live_db = load_live_data()

# यदि डेटाबेस में CCE रिकॉर्ड से संबंधित आवश्यक डायनेमिक कॉलम नहीं हैं, तो उन्हें इनिशियलाइज़ करें
cce_dynamic_fields = ["CCE Marks Obtained", "CCE Attendance Status"]
for field in cce_dynamic_fields:
    if field not in live_db.columns:
        live_db[field] = ""

if live_db.empty:
    st.warning("⚠️ डेटाबेस वर्तमान में खाली है। कृपया पहले Panel 1 (Entry) के माध्यम से छात्रों का डेटा जोड़ें।")
else:
    # सीसीई रिकॉर्ड्स विशिष्ट फ़िल्टरेशन पैनल
    st.subheader("🔍 Filter Records for CCE Entry")
    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        unique_subjects = sorted(list(set(live_db["Subject"].dropna().astype(str))))
        selected_subject = st.selectbox("Subject (विषय) फ़िल्टर करें:", ["All"] + [sub for sub in unique_subjects if sub.strip() != ""])
        
    with col_f2:
        unique_cce_status = ["All Students", "Pending Marks Entry Only (जिनके मार्क्स खाली हैं)", "Marks Entered Already"]
        selected_cce_filter = st.selectbox("CCE Entry Status फ़िल्टर:", unique_cce_status)

    # डेटा फ़िल्टरिंग लॉजिक निष्पादन
    filtered_cce = live_db.copy()
    
    if selected_subject != "All":
        filtered_cce = filtered_cce[filtered_cce["Subject"] == selected_subject]
        
    if selected_cce_filter == "Pending Marks Entry Only (जिनके मार्क्स खाली हैं)":
        filtered_cce = filtered_cce[filtered_cce["CCE Marks Obtained"].str.strip() == ""]
    elif selected_cce_filter == "Marks Entered Already":
        filtered_cce = filtered_cce[filtered_cce["CCE Marks Obtained"].str.strip() != ""]

    st.write(f"फ़िल्टर के आधार पर कुल छात्र संख्या: **{len(filtered_cce)}**")

    # 🔄 लाइव डेटा एडिटर ग्रिड मॉड्यूल
    st.subheader("✏️ Bulk Entry Room: CCE Internal Continuous Marks Board")
    st.info("💡 नीचे दी गई ग्रिड में आप सीधे छात्रों के 'CCE Marks Obtained' (अंक) भर सकते हैं तथा उनका एब्सेंट/प्रेजेंट स्टेटस बदल सकते हैं।")

    # सीसीई प्रविष्टि हेतु विशिष्ट डिस्प्ले कॉलम्स का अरेंजमेंट
    cce_display_cols = [
        "Admission Application Number", "Roll No.", "Student Name", 
        "Subject Code", "Subject", "CCE Marks Obtained", "CCE Attendance Status"
    ]
    
    display_cols = [c for c in cce_display_cols if c in filtered_cce.columns]
    render_df = filtered_cce[display_cols].copy()
    render_df.insert(0, "S.No.", range(1, len(render_df) + 1))

    # इंटरैक्टिव डेटा एडिटर ग्रिड कॉन्फ़िगरेशन
    edited_cce_df = st.data_editor(
        render_df,
        use_container_width=True,
        disabled=["S.No.", "Admission Application Number", "Roll No.", "Student Name", "Subject Code", "Subject"], # मास्टर विवरण लॉक रहेंगे
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

    if st.button("Save & Sync CCE Assessment Ledger", type="primary", use_container_width=True):
        try:
            clean_edited = edited_cce_df.drop(columns=["S.No."])
            
            # मुख्य डेटाबेस इंडेक्स सिंक्रोनाइज़ेशन लूप
            for _, row_edit in clean_edited.iterrows():
                unique_app_no = str(row_edit["Admission Application Number"]).strip()
                
                # मुख्य डेटाबेस में उस पंक्ति का इंडेक्स खोजना
                idx_matches = live_db[live_db["Admission Application Number"].astype(str).str.strip() == unique_app_no].index
                
                if not idx_matches.empty:
                    for match_idx in idx_matches:
                        live_db.at[match_idx, "CCE Marks Obtained"] = str(row_edit["CCE Marks Obtained"]).strip()
                        live_db.at[match_idx, "CCE Attendance Status"] = str(row_edit["CCE Attendance Status"]).strip()

            save_live_data(live_db)
            st.success("✅ सीसीई आंतरिक मूल्यांकन पंजी (CCE Assessment Register) सफलतापूर्वक मास्टर फ़ाइल में सेव हो गई है!")
            st.rerun()
        except Exception as e:
            st.error(f"डेटाबेस सिंक करने में त्रुटि उत्पन्न हुई: {e}")

st.markdown("---")
# सीसीई रिकॉर्ड्स सांख्यिकी और समरी कार्ड्स
if not live_db.empty:
    st.subheader("📊 CCE Assessment Analytics Dashboard")
    col_c1, col_c2, col_c3 = st.columns(3)
    
    with col_c1:
        st.metric("Total Students Eligible for CCE", len(live_db))
    with col_c2:
        entered_count = len(live_db[live_db["CCE Marks Obtained"].str.strip() != ""])
        st.metric("Total Marks Filed (प्रविष्टियाँ पूर्ण)", entered_count)
    with col_c3:
        absent_count = len(live_db[live_db["CCE Attendance Status"] == "Absent"])
        st.metric("Total Absent Students in CCE", absent_count)

# ----------------------------------------------------------------------
# 📌 P9: PANEL 9 MODULE
# ----------------------------------------------------------------------
st.header("📌 Panal P9 (Dynamic Extension Ledger Room)")

# डेटाबेस लोड करें
live_db = load_live_data()

# यदि डेटाबेस में P9 से संबंधित डायनेमिक कॉलम नहीं हैं, तो उन्हें इनिशियलाइज़ करें
p9_dynamic_fields = ["P9 Record Status", "P9 Custom Remarks"]
for field in p9_dynamic_fields:
    if field not in live_db.columns:
        live_db[field] = ""

if live_db.empty:
    st.warning("⚠️ डेटाबेस वर्तमान में खाली है। कृपया पहले Panel 1 (Entry) के माध्यम से छात्रों का डेटा जोड़ें।")
else:
    # पैनल फ़िल्टरेशन टूल्स
    st.subheader("🔍 Filter & Shortlist Candidates")
    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        unique_subjects = sorted(list(set(live_db["Subject"].dropna().astype(str))))
        selected_subject = st.selectbox("Subject (विषय) फ़िल्टर करें:", ["All"] + [sub for sub in unique_subjects if sub.strip() != ""])
        
    with col_f2:
        unique_p9_status = ["All Students", "Pending Updates Only (विवरण खाली है)", "Verified / Updated Records"]
        selected_p9_filter = st.selectbox("P9 Process Status फ़िल्टर:", unique_p9_status)

    # डेटा फ़िल्टरिंग लॉजिक निष्पादन
    filtered_p9 = live_db.copy()
    
    if selected_subject != "All":
        filtered_p9 = filtered_p9[filtered_p9["Subject"] == selected_subject]
        
    if selected_p9_filter == "Pending Updates Only (विवरण खाली है)":
        filtered_p9 = filtered_p9[filtered_p9["P9 Record Status"].str.strip() == ""]
    elif selected_p9_filter == "Verified / Updated Records":
        filtered_p9 = filtered_p9[filtered_p9["P9 Record Status"].str.strip() != ""]

    st.write(f"फ़िल्टर के आधार पर कुल छात्र संख्या: **{len(filtered_p9)}**")

    # 🔄 लाइव डेटा एडिटर ग्रिड मॉड्यूल
    st.subheader("✏️ Bulk Entry Room: P9 Custom Operational Board")
    st.info("💡 नीचे दी गई ग्रिड में आप सीधे छात्रों का 'P9 Record Status' ड्रापडाउन मेनू से चुन सकते हैं और कस्टम रिमार्क्स टाइप कर सकते हैं।")

    # प्रविष्टि हेतु विशिष्ट डिस्प्ले कॉलम्स का अरेंजमेंट
    p9_display_cols = [
        "Admission Application Number", "Roll No.", "Student Name", 
        "Subject", "P9 Record Status", "P9 Custom Remarks"
    ]
    
    display_cols = [c for c in p9_display_cols if c in filtered_p9.columns]
    render_df = filtered_p9[display_cols].copy()
    render_df.insert(0, "S.No.", range(1, len(render_df) + 1))

    # इंटरैक्टिव डेटा एडिटर ग्रिड कॉन्फ़िगरेशन
    edited_p9_df = st.data_editor(
        render_df,
        use_container_width=True,
        disabled=["S.No.", "Admission Application Number", "Roll No.", "Student Name", "Subject"], # मास्टर विवरण लॉक रहेंगे
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
            
            # मुख्य डेटाबेस इंडेक्स सिंक्रोनाइज़ेशन लूप
            for _, row_edit in clean_edited.iterrows():
                unique_app_no = str(row_edit["Admission Application Number"]).strip()
                
                # मुख्य डेटाबेस में उस पंक्ति का इंडेक्स खोजना
                idx_matches = live_db[live_db["Admission Application Number"].astype(str).str.strip() == unique_app_no].index
                
                if not idx_matches.empty:
                    for match_idx in idx_matches:
                        live_db.at[match_idx, "P9 Record Status"] = str(row_edit["P9 Record Status"]).strip()
                        live_db.at[match_idx, "P9 Custom Remarks"] = str(row_edit["P9 Custom Remarks"]).strip()

            save_live_data(live_db)
            st.success("✅ Panel 9 का रिकॉर्ड लेजर सफलतापूर्वक मास्टर डेटाबेस फ़ाइल में सेव हो गया है!")
            st.rerun()
        except Exception as e:
            st.error(f"डेटाबेस सिंक करने में त्रुटि उत्पन्न हुई: {e}")

st.markdown("---")
# P9 रिकॉर्ड्स सांख्यिकी और समरी कार्ड्स
if not live_db.empty:
    st.subheader("📊 Panel P9 Operational Analytics")
    col_c1, col_c2, col_c3 = st.columns(3)
    
    with col_c1:
        st.metric("Total Students Available", len(live_db))
    with col_c2:
        entered_count = len(live_db[live_db["P9 Record Status"].str.strip() != ""])
        st.metric("Processed Applications (प्रविष्टियाँ पूर्ण)", entered_count)
    with col_c3:
        pending_count = len(live_db) - entered_count
        st.metric("Awaiting Data Processing", pending_count)

# ----------------------------------------------------------------------
# 📌 P10: PANEL 10 MODULE
# ----------------------------------------------------------------------
st.header("📌 Panal P10 (Dynamic Extension Ledger Room 2)")

live_db = load_live_data()

# यदि डेटाबेस में P10 से संबंधित डायनेमिक कॉलम नहीं हैं, तो उन्हें इनिशियलाइज़ करें
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
        selected_subject = st.selectbox("Subject (विषय) फ़िल्टर करें:", ["All"] + [sub for sub in unique_subjects if sub.strip() != ""], key="p10_sub")
        
    with col_f2:
        unique_p10_status = ["All Students", "Pending Updates Only (विवरण खाली है)", "Verified / Updated Records"]
        selected_p10_filter = st.selectbox("P10 Process Status फ़िल्टर:", unique_p10_status, key="p10_filter")

    filtered_p10 = live_db.copy()
    if selected_subject != "All":
        filtered_p10 = filtered_p10[filtered_p10["Subject"] == selected_subject]
        
    if selected_p10_filter == "Pending Updates Only (विवरण खाली है)":
        filtered_p10 = filtered_p10[filtered_p10["P10 Record Status"].str.strip() == ""]
    elif selected_p10_filter == "Verified / Updated Records":
        filtered_p10 = filtered_p10[filtered_p10["P10 Record Status"].str.strip() != ""]

    st.write(f"फ़िल्टर के आधार पर कुल छात्र संख्या: **{len(filtered_p10)}**")

    st.subheader("✏️ Bulk Entry Room: P10 Custom Operational Board")
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
                options=["Verified", "Pending", "Approved", "On Hold", "Rejected"],
                required=False,
            ),
            "P10 Custom Remarks": st.column_config.TextColumn("Custom Logs / Remarks", max_chars=100)
        },
        key="p10_record_live_editor",
        hide_index=True
    )

    if st.button("Save & Sync Panel 10 Records", type="primary", use_container_width=True):
        try:
            clean_edited = edited_p10_df.drop(columns=["S.No."])
            for _, row_edit in clean_edited.iterrows():
                unique_app_no = str(row_edit["Admission Application Number"]).strip()
                idx_matches = live_db[live_db["Admission Application Number"].astype(str).str.strip() == unique_app_no].index
                if not idx_matches.empty:
                    for match_idx in idx_matches:
                        live_db.at[match_idx, "P10 Record Status"] = str(row_edit["P10 Record Status"]).strip()
                        live_db.at[match_idx, "P10 Custom Remarks"] = str(row_edit["P10 Custom Remarks"]).strip()
            save_live_data(live_db)
            st.success("✅ Panel 10 का रिकॉर्ड लेजर सफलतापूर्वक मास्टर डेटाबेस फ़ाइल में सेव हो गया है!")
            st.rerun()
        except Exception as e:
            st.error(f"डेटाबेस सिंक करने में त्रुटि उत्पन्न हुई: {e}")

st.markdown("---")
if not live_db.empty:
    st.subheader("📊 Panel P10 Operational Analytics")
    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1: st.metric("Total Students Available", len(live_db))
    with col_c2:
        entered_count = len(live_db[live_db["P10 Record Status"].str.strip() != ""])
        st.metric("Processed Applications", entered_count)
    with col_c3: st.metric("Awaiting Data Processing", len(live_db) - entered_count)

# ----------------------------------------------------------------------
# 📌 P11: PANEL 11 MODULE
# ----------------------------------------------------------------------
st.header("📌 Panal P11 (Dynamic Extension Ledger Room 3)")

live_db = load_live_data()

# यदि डेटाबेस में P11 से संबंधित डायनेमिक कॉलम नहीं हैं, तो उन्हें इनिशियलाइज़ करें
p11_dynamic_fields = ["P11 Record Status", "P11 Custom Remarks"]
for field in p11_dynamic_fields:
    if field not in live_db.columns:
        live_db[field] = ""

if live_db.empty:
    st.warning("⚠️ डेटाबेस वर्तमान में खाली है। कृपया पहले Panel 1 (Entry) के माध्यम से छात्रों का डेटा जोड़ें।")
else:
    st.subheader("🔍 Filter & Shortlist Candidates")
    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        unique_subjects = sorted(list(set(live_db["Subject"].dropna().astype(str))))
        selected_subject = st.selectbox("Subject (विषय) फ़िल्टर करें:", ["All"] + [sub for sub in unique_subjects if sub.strip() != ""], key="p11_sub")
        
    with col_f2:
        unique_p11_status = ["All Students", "Pending Updates Only (विवरण खाली है)", "Verified / Updated Records"]
        selected_p11_filter = st.selectbox("P11 Process Status फ़िल्टर:", unique_p11_status, key="p11_filter")

    filtered_p11 = live_db.copy()
    if selected_subject != "All":
        filtered_p11 = filtered_p11[filtered_p11["Subject"] == selected_subject]
        
    if selected_p11_filter == "Pending Updates Only (विवरण खाली है)":
        filtered_p11 = filtered_p11[filtered_p11["P11 Record Status"].str.strip() == ""]
    elif selected_p11_filter == "Verified / Updated Records":
        filtered_p11 = filtered_p11[filtered_p11["P11 Record Status"].str.strip() != ""]

    st.write(f"फ़िल्टर के आधार पर कुल छात्र संख्या: **{len(filtered_p11)}**")

    st.subheader("✏️ Bulk Entry Room: P11 Custom Operational Board")
    p11_display_cols = ["Admission Application Number", "Roll No.", "Student Name", "Subject", "P11 Record Status", "P11 Custom Remarks"]
    display_cols = [c for c in p11_display_cols if c in filtered_p11.columns]
    render_df = filtered_p11[display_cols].copy()
    render_df.insert(0, "S.No.", range(1, len(render_df) + 1))

    edited_p11_df = st.data_editor(
        render_df,
        use_container_width=True,
        disabled=["S.No.", "Admission Application Number", "Roll No.", "Student Name", "Subject"],
        column_config={
            "P11 Record Status": st.column_config.SelectboxColumn(
                "Process Status",
                options=["Verified", "Pending", "Approved", "On Hold", "Rejected"],
                required=False,
            ),
            "P11 Custom Remarks": st.column_config.TextColumn("Custom Logs / Remarks", max_chars=100)
        },
        key="p11_record_live_editor",
        hide_index=True
    )

    if st.button("Save & Sync Panel 11 Records", type="primary", use_container_width=True):
        try:
            clean_edited = edited_p11_df.drop(columns=["S.No."])
            for _, row_edit in clean_edited.iterrows():
                unique_app_no = str(row_edit["Admission Application Number"]).strip()
                idx_matches = live_db[live_db["Admission Application Number"].astype(str).str.strip() == unique_app_no].index
                if not idx_matches.empty:
                    for match_idx in idx_matches:
                        live_db.at[match_idx, "P11 Record Status"] = str(row_edit["P11 Record Status"]).strip()
                        live_db.at[match_idx, "P11 Custom Remarks"] = str(row_edit["P11 Custom Remarks"]).strip()
            save_live_data(live_db)
            st.success("✅ Panel 11 का रिकॉर्ड लेजर सफलतापूर्वक मास्टर डेटाबेस फ़ाइल में सेव हो गया है!")
            st.rerun()
        except Exception as e:
            st.error(f"डेटाबेस सिंक करने में त्रुटि उत्पन्न हुई: {e}")

st.markdown("---")
if not live_db.empty:
    st.subheader("📊 Panel P11 Operational Analytics")
    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1: st.metric("Total Students Available", len(live_db))
    with col_c2:
        entered_count = len(live_db[live_db["P11 Record Status"].str.strip() != ""])
        st.metric("Processed Applications", entered_count)
    with col_c3: st.metric("Awaiting Data Processing", len(live_db) - entered_count)

# ----------------------------------------------------------------------
# 📌 P12: PANEL 12 MODULE
# ----------------------------------------------------------------------
st.header("📌 Panal P12 (Dynamic Extension Ledger Room 4)")

live_db = load_live_data()

# यदि डेटाबेस में P12 से संबंधित डायनेमिक कॉलम नहीं हैं, तो उन्हें इनिशियलाइज़ करें
p12_dynamic_fields = ["P12 Record Status", "P12 Custom Remarks"]
for field in p12_dynamic_fields:
    if field not in live_db.columns:
        live_db[field] = ""

if live_db.empty:
    st.warning("⚠️ डेटाबेस वर्तमान में खाली है। कृपया पहले Panel 1 (Entry) के माध्यम से छात्रों का डेटा जोड़ें।")
else:
    st.subheader("🔍 Filter & Shortlist Candidates")
    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        unique_subjects = sorted(list(set(live_db["Subject"].dropna().astype(str))))
        selected_subject = st.selectbox("Subject (विषय) फ़िल्टर करें:", ["All"] + [sub for sub in unique_subjects if sub.strip() != ""], key="p12_sub")
        
    with col_f2:
        unique_p12_status = ["All Students", "Pending Updates Only (विवरण खाली है)", "Verified / Updated Records"]
        selected_p12_filter = st.selectbox("P12 Process Status फ़िल्टर:", unique_p12_status, key="p12_filter")

    filtered_p12 = live_db.copy()
    if selected_subject != "All":
        filtered_p12 = filtered_p12[filtered_p12["Subject"] == selected_subject]
        
    if selected_p12_filter == "Pending Updates Only (विवरण खाली है)":
        filtered_p12 = filtered_p12[filtered_p12["P12 Record Status"].str.strip() == ""]
    elif selected_p12_filter == "Verified / Updated Records":
        filtered_p12 = filtered_p12[filtered_p12["P12 Record Status"].str.strip() != ""]

    st.write(f"फ़िल्टर के आधार पर कुल छात्र संख्या: **{len(filtered_p12)}**")

    st.subheader("✏️ Bulk Entry Room: P12 Custom Operational Board")
    p12_display_cols = ["Admission Application Number", "Roll No.", "Student Name", "Subject", "P12 Record Status", "P12 Custom Remarks"]
    display_cols = [c for c in p12_display_cols if c in filtered_p12.columns]
    render_df = filtered_p12[display_cols].copy()
    render_df.insert(0, "S.No.", range(1, len(render_df) + 1))

    edited_p12_df = st.data_editor(
        render_df,
        use_container_width=True,
        disabled=["S.No.", "Admission Application Number", "Roll No.", "Student Name", "Subject"],
        column_config={
            "P12 Record Status": st.column_config.SelectboxColumn(
                "Process Status",
                options=["Verified", "Pending", "Approved", "On Hold", "Rejected"],
                required=False,
            ),
            "P12 Custom Remarks": st.column_config.TextColumn("Custom Logs / Remarks", max_chars=100)
        },
        key="p12_record_live_editor",
        hide_index=True
    )

    if st.button("Save & Sync Panel 12 Records", type="primary", use_container_width=True):
        try:
            clean_edited = edited_p12_df.drop(columns=["S.No."])
            for _, row_edit in clean_edited.iterrows():
                unique_app_no = str(row_edit["Admission Application Number"]).strip()
                idx_matches = live_db[live_db["Admission Application Number"].astype(str).str.strip() == unique_app_no].index
                if not idx_matches.empty:
                    for match_idx in idx_matches:
                        live_db.at[match_idx, "P12 Record Status"] = str(row_edit["P12 Record Status"]).strip()
                        live_db.at[match_idx, "P12 Custom Remarks"] = str(row_edit["P12 Custom Remarks"]).strip()
            save_live_data(live_db)
            st.success("✅ Panel 12 का रिकॉर्ड लेजर सफलतापूर्वक मास्टर डेटाबेस फ़ाइल में सेव हो गया है!")
            st.rerun()
        except Exception as e:
            st.error(f"डेटाबेस सिंक करने में त्रुटि उत्पन्न हुई: {e}")

st.markdown("---")
if not live_db.empty:
    st.subheader("📊 Panel P12 Operational Analytics")
    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1: st.metric("Total Students Available", len(live_db))
    with col_c2:
        entered_count = len(live_db[live_db["P12 Record Status"].str.strip() != ""])
        st.metric("Processed Applications", entered_count)
    with col_c3: st.metric("Awaiting Data Processing", len(live_db) - entered_count)

# ----------------------------------------------------------------------
# 🔀 P13: MERGE PANEL MODULE
# ----------------------------------------------------------------------
st.header("🔀 Panal P13: Database Smart Merge Panel")
st.info("💡 इस पैनल के माध्यम से आप किसी भी अन्य बाहरी CSV डेटाबेस फ़ाइल को वर्तमान मास्टर डेटाबेस में सुरक्षित रूप से मर्ज कर सकते हैं।")

live_db = load_live_data()

# 1. फ़ाइल अपलोडर
uploaded_merge_file = st.file_uploader("मर्ज करने के लिए नई CSV फ़ाइल चुनें:", type=["csv"])

if uploaded_merge_file is not None:
    try:
        # अपलोड की गई फ़ाइल को रीड करें
        incoming_df = pd.read_csv(uploaded_merge_file, dtype=str).fillna("")
        st.success("✅ बाहरी फ़ाइल सफलतापूर्वक रीड कर ली गई है!")
        
        st.subheader("📋 अपलोड की गई फ़ाइल का पूर्वावलोकन (Preview)")
        st.dataframe(incoming_df.head(5), use_container_width=True)
        
        st.markdown("---")
        st.subheader("⚙️ मर्जिंग और मैपिंग कॉन्फ़िगरेशन")
        
        # डुप्लीकेट चेकिंग के लिए मुख्य चाबी (Key Column) का चयन
        merge_key = st.selectbox(
            "🔑 डुप्लीकेट रिकॉर्ड्स की पहचान करने के लिए मुख्य कॉलम (Unique Key) चुनें:",
            options=["Admission Application Number", "Unique ID", "Roll No.", "Enrollment No."]
        )
        
        conflict_strategy = st.radio(
            "🛡️ यदि डेटाबेस में समान रिकॉर्ड (Duplicate Entry) मिलता है, तो क्या करें?",
            options=["Overwrite Existing Data (पुराने डेटा को नए से बदलें)", "Ignore New Records (मास्टर डेटा को सुरक्षित रखें, नया छोड़ दें)"],
            horizontal=True
        )

        st.markdown("#### 🔗 कॉलम मैपिंग मैट्रिक्स")
        st.caption("यदि बाहरी फ़ाइल के कॉलम का नाम अलग है, तो नीचे दिए गए बॉक्स से मिलान करें:")
        
        mapped_columns_dict = {}
        col_setup1, col_setup2 = st.columns(2)
        
        # डायनेमिक कॉलम मैपरेटर इंटरफ़ेस
        incoming_columns_list = ["-- Leave Empty / Don't Merge --"] + list(incoming_df.columns)
        
        for idx, master_col in enumerate(DEFAULT_COLUMNS):
            # डिफ़ॉल्ट रूप से अगर नाम मैच करता है तो उसे ऑटो-सेलेक्ट करें
            default_idx = incoming_columns_list.index(master_col) if master_col in incoming_columns_list else 0
            
            if idx % 2 == 0:
                with col_setup1:
                    selected_incoming_col = st.selectbox(f"Map Master '{master_col}' to:", options=incoming_columns_list, index=default_idx, key=f"map_{master_col}")
            else:
                with col_setup2:
                    selected_incoming_col = st.selectbox(f"Map Master '{master_col}' to:", options=incoming_columns_list, index=default_idx, key=f"map_{master_col}")
            
            if selected_incoming_col != "-- Leave Empty / Don't Merge --":
                mapped_columns_dict[master_col] = selected_incoming_col

        # 🚀 मर्जिंग एक्शन बटन
        if st.button("Execute Smart Database Merge Now", type="primary", use_container_width=True):
            with st.spinner("डेटाबेस मर्ज किया जा रहा है..."):
                # टेम्परेरी डेटाफ़्रेम जिसमें केवल मैप्ड कॉलम्स होंगे
                processed_incoming_data = pd.DataFrame(columns=DEFAULT_COLUMNS)
                
                # बाहरी फ़ाइल के डेटा को मास्टर फॉर्मेट में ढालना
                for master_col, incoming_col in mapped_columns_dict.items():
                    processed_incoming_data[master_col] = incoming_df[incoming_col]
                
                # बचे हुए मिसिंग कॉलम्स को खाली स्ट्रिंग से भरना
                for master_col in DEFAULT_COLUMNS:
                    if master_col not in processed_incoming_data.columns:
                        processed_incoming_data[master_col] = ""
                
                # मर्जिंग प्रोसेस एक्सेक्यूशन
                records_updated = 0
                records_added = 0
                
                # स्ट्रिंग क्लीनिंग
                live_db[merge_key] = live_db[merge_key].astype(str).str.strip()
                processed_incoming_data[merge_key] = processed_incoming_data[merge_key].astype(str).str.strip()
                
                for _, row_incoming in processed_incoming_data.iterrows():
                    key_value = row_incoming[merge_key]
                    
                    if key_value == "" or key_value.lower() == "nan":
                        # बिना चाबी के रिकॉर्ड को सीधे अंत में जोड़ें
                        live_db = pd.concat([live_db, pd.DataFrame([row_incoming])], ignore_index=True)
                        records_added += 1
                        continue
                    
                    # मुख्य डेटाबेस में मिलान खोजना
                    match_indices = live_db[live_db[merge_key] == key_value].index
                    
                    if not match_indices.empty:
                        if conflict_strategy == "Overwrite Existing Data (पुराने डेटा को नए से बदलें)":
                            for match_idx in match_indices:
                                for col in DEFAULT_COLUMNS:
                                    if row_incoming[col] != "":
                                        live_db.at[match_idx, col] = row_incoming[col]
                            records_updated += 1
                    else:
                        # अगर रिकॉर्ड नया है तो जोड़ें
                        live_db = pd.concat([live_db, pd.DataFrame([row_incoming])], ignore_index=True)
                        records_added += 1
                
                # सेव और रिफ्रेश
                save_live_data(live_db)
                st.success(f"🎉 डेटाबेस सफलतापूर्वक मर्ज हो गया! **{records_added}** नए रिकॉर्ड जोड़े गए और **{records_updated}** पुराने रिकॉर्ड अपडेट किए गए।")
                st.rerun()
                
    except Exception as e:
        st.error(f"मर्जिंग प्रक्रिया में त्रुटि: {e}")

st.markdown("---")
# मर्जिंग स्टेटिस्टिक्स काउंटर्स
if not live_db.empty:
    st.subheader("📊 Merge Panel Database Metrics")
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.metric("Total Records in Live Database", len(live_db))
    with col_m2:
        st.metric("Master Engine Tracked Columns", len(DEFAULT_COLUMNS))

# ----------------------------------------------------------------------
# 👁️ P14: PANEL VIEWER (INTEGRATED INDEX SYSTEM)
# ----------------------------------------------------------------------
st.header("👁️ Panal Viewer (Multi-Panel Inspection Window)")

live_db = load_live_data()

if live_db.empty:
    st.warning("⚠️ डेटाबेस वर्तमान में खाली है। कृपया पहले डेटाबेस में छात्रों का रिकॉर्ड लोड करें।")
else:
    # 📑 P2 से P13 तक के पैनल्स का विज़ुअल लिस्ट इंडेक्स मैपर
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

    # 🗂️ मुख्य ड्रॉपडाउन: यूज़र को P2 से P13 तक चुनने की आज़ादी देता है
    st.subheader("📂 Select Panel Dashboard View")
    selected_panel_view = st.selectbox(
        "निरीक्षण करने के लिए पैनल सूची (P2 से P13) चुनें:",
        options=list(panel_options_list.keys())
    )

    # चुने गए पैनल के आधार पर विशिष्ट कॉलम प्राप्त करना
    target_columns = panel_options_list[selected_panel_view]

    # सुनिश्चित करें कि डायनेमिक स्कॉलरशिप/रिजल्ट/सीसीई वाले नए कॉलम डेटाफ़्रेम में अस्थायी रूप से सिंक हों ताकि एरर न आए
    for c_col in target_columns:
        if c_col not in live_db.columns:
            live_db[c_col] = ""

    st.markdown(f"### 📋 {selected_panel_view} - Records Table")
    
    # 🔍 सर्चिंग मैकेनिज्म (चुने गए पैनल के कॉलम्स के आधार पर)
    col_search1, col_search2 = st.columns([1, 2])
    with col_search1:
        search_target_col = st.selectbox("खोजने के लिए फ़ील्ड चुनें:", options=target_columns, key="p14_search_col")
    with col_search2:
        search_query_text = st.text_input(f"'{search_target_col}' में प्रविष्टि खोजें:", key="p14_query_val")

    # फ़िल्टरिंग प्रक्रिया चालू करना
    view_filtered_df = live_db.copy()
    
    if search_query_text.strip() != "":
        view_filtered_df = view_filtered_df[
            view_filtered_df[search_target_col].astype(str).str.contains(search_query_text, case=False, na=False)
        ]

    st.write(f"वर्तमान ग्रिड में कुल उपलब्ध छात्र रिकॉर्ड संख्या: **{len(view_filtered_df)}**")

    # 📊 फ़िल्टर डेटा ग्रिड का प्रदर्शन (Viewer Mode - Lock Grid)
    final_render_cols = [col for col in target_columns if col in view_filtered_df.columns]
    
    if not view_filtered_df.empty:
        display_ready_df = view_filtered_df[final_render_cols].copy()
        display_ready_df.insert(0, "S.No.", range(1, len(display_ready_df) + 1))
        
        # सिर्फ़ डेटा देखने के लिए (Non-Editable Grid)
        st.dataframe(
            display_ready_df,
            use_container_width=True,
            hide_index=True
        )
        
        # 💾 क्विक डाउनलोड विकल्प
        st.download_button(
            label=f"📥 Download {selected_panel_view.split(':')[0]} Report (CSV)",
            data=view_filtered_df[final_render_cols].to_csv(index=False).encode('utf-8'),
            file_name=f"{selected_panel_view.replace(' ', '_').lower()}_report.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.warning("🔍 निर्दिष्ट खोज प्रविष्टि के आधार पर कोई रिकॉर्ड नहीं मिला।")

# ----------------------------------------------------------------------
# 🛠️ P15: PANEL ADMIN CODE BLOCK
# ----------------------------------------------------------------------
st.header(f"🛠️ {get_panel_title('P15')} (Full Super-Admin Control Command)")

# 👑 1. 15 पैनल्स का नाम बदलने की पॉवर (Dynamic Panel Name Customizer)
st.subheader("✏️ Dynamic 15 Panels Name & Label Customizer")
with st.expander("15 पैनल्स के नाम (App Titles) एडिट करने के लिए यहाँ क्लिक करें", expanded=False):
    st.info("💡 यहाँ से बदला गया नाम तुरंत पूरे सिस्टम के इंटरफ़ेस और बटनों पर लागू हो जाएगा।")
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
            st.success("✅ सभी 15 पैनल्स के नए नाम लाइव डेटाबेस स्कीमा में सुरक्षित सेव हो गए हैं!")
            st.rerun()

# 🛡️ 2. ग्लोबल पैनल्स विज़िबिलिटी कंट्रोलर (15 बटन की व्यवस्था)
st.subheader("🛡️ Global 15 Panels Visibility Toggle Switch Board")
st.caption("💡 नीचे दिए गए बटनों पर क्लिक करके आप संबंधित पैनल को यूजर स्क्रीन से छुपा (Hide) या दिखा (Unhide) सकते हैं:")

# दो अलग-अलग टैब्स में 15 बटना व्यवस्थित करना ताकि स्क्रीन साफ दिखे
vis_tabs = st.tabs(["🔒 Panels P1 - P7 Control", "🔒 Panels P8 - P15 Control"])

with vis_tabs[0]:
    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
    panels_batch_1 = ["P1", "P2", "P3", "P4", "P5", "P6", "P7"]
    for i, p_key in enumerate(panels_batch_1):
        with [c1, c2, c3, c4, c5, c6, c7][i]:
            status_lbl = "❌ Hidden" if st.session_state[f"hide_panel_{p_key}"] else "👁️ Active"
            if st.button(f"{p_key}\n({status_lbl})", use_container_width=True, key=f"btn_v_{p_key}", type="secondary" if st.session_state[f"hide_panel_{p_key}"] else "primary"):
                st.session_state[f"hide_panel_{p_key}"] = not st.session_state[f"hide_panel_{p_key}"]
                st.rerun()
                
with vis_tabs[1]:
    c8, c9, c10, c11, c12, c13, c14, c15 = st.columns(8)
    panels_batch_2 = ["P8", "P9", "P10", "P11", "P12", "P13", "P14", "P15"]
    for i, p_key in enumerate(panels_batch_2):
        with [c8, c9, c10, c11, c12, c13, c14, c15][i]:
            status_lbl = "❌ Hidden" if st.session_state[f"hide_panel_{p_key}"] else "👁️ Active"
            if st.button(f"{p_key}\n({status_lbl})", use_container_width=True, key=f"btn_v_{p_key}", type="secondary" if st.session_state[f"hide_panel_{p_key}"] else "primary"):
                st.session_state[f"hide_panel_{p_key}"] = not st.session_state[f"hide_panel_{p_key}"]
                st.rerun()

# 📊 3. मास्टर डेटाबेस कंट्रोल्स और लाइव ग्रेड एडिटर
st.markdown("---")
st.subheader("📊 Master Database List View & Advanced Operational Controls")

# मुख्य मास्टर डेटा हाइड/अनहाइड टॉगल बटन
lbl_data_toggle = "🔓 Master Data Matrix: Hide" if not st.session_state.admin_hide_master_data else "👁️ Master Data Matrix: Unhide"
if st.button(lbl_data_toggle, use_container_width=True, key="data_toggle", type="secondary"):
    st.session_state.admin_hide_master_data = not st.session_state.admin_hide_master_data
    st.rerun()

col_ctrl1, col_ctrl2, col_ctrl3 = st.columns(3)
with col_ctrl1:
    if st.button("📝 एडिट टेक्स्ट फंक्शन (On/Off)", use_container_width=True):
        st.session_state.admin_unhide_edit = not st.session_state.admin_unhide_edit
        st.rerun()
with col_ctrl2:
    if st.button("🔀 कॉलम मूव बटन्स (On/Off)", use_container_width=True):
        st.session_state.admin_unhide_move = not st.session_state.admin_unhide_move
        st.rerun()
with col_ctrl3:
    lock_label = "🔒 लिस्ट लॉक करें (Locked)" if st.session_state.admin_lock_state else "🔓 लिस्ट अनलॉक करें (Editable)"
    if st.button(lock_label, use_container_width=True, type="primary" if not st.session_state.admin_lock_state else "secondary"):
        st.session_state.admin_lock_state = not st.session_state.admin_lock_state
        st.rerun()

# कॉलम मूविंग मैकेनिज्म लॉजिक
if st.session_state.admin_unhide_move and not st.session_state.admin_lock_state:
    st.info("🔀 कॉलम का क्रम बदलने के लिए सेलेक्ट करें:")
    target_col = st.selectbox("मूव करने के लिए कॉलम चुनें:", options=st.session_state.admin_columns_order)
    c_left, c_right = st.columns(2)
    if c_left.button("⬅️ Shift Left", use_container_width=True):
        idx = st.session_state.admin_columns_order.index(target_col)
        if idx > 0:
            st.session_state.admin_columns_order[idx], st.session_state.admin_columns_order[idx-1] = st.session_state.admin_columns_order[idx-1], st.session_state.admin_columns_order[idx]
            st.rerun()
    if             if c_right.button("➡️ Shift Right", use_container_width=True):
                idx = st.session_state.admin_columns_order.index(target_col)
                if idx < len(st.session_state.admin_columns_order) - 1:
                    st.session_state.admin_columns_order[idx], st.session_state.admin_columns_order[idx+1] = st.session_state.admin_columns_order[idx+1], st.session_state.admin_columns_order[idx]
                    st.rerun()

        # 🔒 डेटा रेंडरिंग ब्लॉक (यह 'Master Data Display Button' की स्टेट पर निर्भर करता है)
        if st.session_state.admin_hide_master_data:
            st.warning("🔒 एडमिन डेटा सुरक्षा के कारण वर्तमान में मास्टर सूची (Grid) हिडन (Hidden) की गई है। डेटा देखने के लिए ऊपर Unhide बटन दबाएं।")
        else:
            # सुनिश्चित करें कि डायनेमिक कॉलम भी रेंडर आर्डर सूची में सिंक रहें
            render_columns = [col for col in st.session_state.admin_columns_order if col in live_db.columns]
            ordered_db = live_db[render_columns].copy()
            ordered_db = ordered_db.rename(columns={c: get_display_name(c) for c in ordered_db.columns})
            ordered_db.insert(0, "S.No.", range(1, len(ordered_db) + 1))

            st.write(f"डेटाबेस में कुल लाइव रिकॉर्ड संख्या: **{len(ordered_db)}**")

            # 🔄 लाइव डेटा संपादन/डिलीट मोड (Matrix Mode)
            if not st.session_state.admin_lock_state and st.session_state.admin_unhide_edit:
                st.warning("⚠️ लाइव संपादन (Live Editing Matrix Mode) सक्रिय है। आप पंक्तियाँ जोड़, एडिट या डिलीट कर सकते हैं।")
                
                edited_df = st.data_editor(
                    ordered_db, 
                    use_container_width=True, 
                    disabled=["S.No."], 
                    num_rows="dynamic", 
                    key="admin_live_editor_grid", 
                    hide_index=True
                )
                
                if st.button("Save & Sync Matrix Changes", type="primary", use_container_width=True):
                    try:
                        clean_edited = edited_df.drop(columns=["S.No."])
                        reverse_mapping = {get_display_name(k): k for k in render_columns}
                        
                        # डिक्शनरी री-बिल्डर इंजन जो डेटाबेस स्ट्रक्चर को बनाए रखता है
                        synced_data = {col: [] for col in DEFAULT_COLUMNS}
                        
                        # मुख्य डेटाबेस के अन्य सभी एडिशनल डायनेमिक कॉलम्स को भी इसमें जोड़ें
                        for col in live_db.columns:
                            if col not in synced_data:
                                synced_data[col] = []

                        for _, row_edit in clean_edited.iterrows():
                            for display_name_key in clean_edited.columns:
                                internal_key = reverse_mapping.get(display_name_key, display_name_key)
                                if internal_key in synced_data: 
                                    synced_data[internal_key].append(row_edit[display_name_key])
                        
                        new_live_db = pd.DataFrame(synced_data)
                        save_live_data(new_live_db)
                        st.success("✅ संपूर्ण मास्टर डेटाबेस सफलतापूर्वक सिंक और अपडेट कर दिया गया है!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"डेटा सिंक्रोनाइज़ेशन चक्र में तकनीकी समस्या आई: {e}")
            else:
                # नॉर्मल व्यू मोड (Non-Editable Grid View)
                st.dataframe(ordered_db, use_container_width=True, hide_index=True)

