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
if "show_login_panel" not in st.session_state: st.session_state.show_login_panel = True

live_db = load_live_data()

# 🛠️ हेल्पिंग हेल्पर फंक्शन: डिक्शनरी मैपिंग के अनुसार रीयल-टाइम नाम रिप्लेसमेंट करना
def get_display_name(internal_col_name):
    return st.session_state.column_mappings.get(internal_col_name, internal_col_name)

# ==========================================================
# 🔒 लॉगिन गेटवे
# ==========================================================
if st.session_state.user_role is None:
    st.markdown("---")
    col_login_btn, _ = st.columns(2)
    with col_login_btn:
        login_btn_label = "🔓 Hide Login Panel" if st.session_state.show_login_panel else "🔒 Open Login Panel"
        if st.button(login_btn_label, use_container_width=True, type="secondary", key="global_login_toggle_btn"):
            st.session_state.show_login_panel = not st.session_state.show_login_panel
            st.rerun()

    if st.session_state.show_login_panel:
        st.subheader("🔒 Multi-User Secure Login Gateway")
        user_input = st.selectbox("Username (भूमिका) चुनें:", options=list(st.session_state.credentials.keys()))
        password_input = st.text_input("Password दर्ज करें:", type="password")
        
        if st.button("Secure Login", use_container_width=True, type="primary"):
            if user_input in st.session_state.credentials and st.session_state.credentials[user_input]["password"] == password_input:
                st.session_state.user_role = st.session_state.credentials[user_input]["role"]
                st.session_state.show_login_panel = False
                st.success("✅ लॉगिन सफल!")
                st.rerun()
            else:
                st.error("❌ गलत पासवर्ड!")

# ==========================================================
# 🔑 लॉगिन ऑथेंटिकेटेड सिस्टम
# ==========================================================
else:
    st.markdown('<div class="print-hide">', unsafe_allow_html=True)
    if st.button("🔒 मुख्य लॉगआउट (Exit Secure System)", type="primary", use_container_width=True):
        st.session_state.user_role = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    role = st.session_state.user_role
    st.info(f"🔑 वर्तमान सत्र भूमिका: **{role.upper()}**")
    st.markdown("---")

# ----------------------------------------------------------------------
# 📝 STUDENT DATA ENTRY PANEL (ONLY CODE MODULE)
# ----------------------------------------------------------------------
st.header("📝 Student Data Entry Panel")

entry_method = st.selectbox(
    "⚙️ डेटा एंट्री का माध्यम चुनें (Choose Entry Method):",
    options=["📁 CSV फ़ाइल बल्क अपलोड (Bulk CSV Upload)", "➕ नया छात्र मैनुअल फॉर्म (Manual Form Entry)"],
    key="standalone_entry_method_selector"
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

# --- माध्यम B: नया छात्र मैनुअल फॉर्म एंट्री ---
elif entry_method == "➕ नया छात्र मैनुअल फॉर्म (Manual Form Entry)":
    st.subheader("➕ नया छात्र मैन्युअल प्रविष्टि फॉर्म")
    
    with st.form(key="standalone_student_add_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            admission_year = st.text_input(get_display_name("Admission Year"))
            eligibility_name = st.text_input(get_display_name("Eligibility Name"))
            admission_date = st.text_input(get_display_name("Admission Date"))
            roll_no = st.text_input(get_display_name("Roll No."))
            enrollment_no = st.text_input(get_display_name("Enrollment No."))
            f_name = st.text_input(get_display_name("Father Name"))
            dob = st.text_input(get_display_name("Date of Birth"))
            
            # 🎯 सटीक क्रम: सब्जेक्ट टेक्स्ट बॉक्स से ठीक पहले सब्जेक्ट कोड और सब्जेक्ट आईडी बॉक्स
            subject_code = st.text_input(get_display_name("Subject Code"), placeholder="उदा. C264")
            subject_id = st.text_input(get_display_name("Subject ID"), placeholder="उदा. B.A.LL.B.1")
            subject = st.text_input(get_display_name("Subject"), placeholder="उदा. B.A. LL.B. (Law with Arts)")
            
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
            
