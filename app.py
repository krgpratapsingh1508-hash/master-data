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

if "credentials" not in st.session_state:
    st.session_state.credentials = load_credentials()

# मास्टर कॉलम्स सूची
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
if "show_login_panel" not in st.session_state: st.session_state.show_login_panel = True

live_db = load_live_data()

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
                    admission_year = st.text_input("Admission Year (प्रवेश वर्ष)")
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
                    
