import streamlit as st
import pandas as pd
import os
import base64

# पेज का लेआउट सेट करें
st.set_page_config(layout="wide")

# --- 🎯 डायरेक्ट टेक्स्ट फ़ाइल डाउनलोड बटन (वेबसाइट से ही डाउनलोड करने के लिए) ---
def get_code_download_link():
    try:
        with open("app.py", "r", encoding="utf-8") as f:
            code_content = f.read()
        b64 = base64.b64encode(code_content.encode()).decode()
        return f'<a href="data:file/text;base64,{b64}" download="app.py" style="text-decoration:none;"><button style="width:100%; background-color:#2e7d32; color:white; border:none; padding:0.75rem; border-radius:0.5rem; font-weight:bold; cursor:pointer; margin-bottom:20px;">📥 Download Core app.py Text File (यहाँ क्लिक करके सीधा कोड डाउनलोड करें)</button></a>'
    except:
        return ""

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

# 🎯 डाउनलोड बटन को वेबसाइट के सबसे ऊपर स्क्रीन पर रेंडर करना
dl_link_html = get_code_download_link()
if dl_link_html:
    st.markdown(dl_link_html, unsafe_allow_html=True)

DB_FILE = "shared_student_database.csv"

# 🔑 4-स्तरीय सुरक्षा क्रेडेंशियल्स सेटिंग्स
CREDENTIALS = {
    "entry": {"password": "entry123", "role": "data_entry"},
    "viewer": {"password": "viewer123", "role": "list_viewer"},
    "cce": {"password": "cce123", "role": "cce_handler"},
    "admin": {"password": "admin123", "role": "full_admin"}
}

# 🎯 आपके द्वारा दिए गए बिल्कुल नए 20 कॉलम्स की मास्टर सूची
DEFAULT_COLUMNS = [
    "Admission Year", "Admission Session", "Eligibility Name", "Admission Application Number",
    "Admission Date", "Unique ID", "Roll No.", "Application Enrollment No.",
    "Enrollment No.", "Student Name", "Father Name", "Mother Name", "Date of Birth",
    "Category", "Subject", "Duration", "Mobile Number", "Email ID", "Address", "Status"
]

# डेटा लोड फंक्शन
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
        return df.fillna("").reset_index(drop=True)
    except:
        return pd.DataFrame(columns=DEFAULT_COLUMNS)

def save_live_data(df_to_save):
    df_to_save.fillna("").astype(str).to_csv(DB_FILE, index=False)

# स्टेट मैनेजमेंट सेटअप
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
if "list_visibility_state" not in st.session_state:
    st.session_state.list_visibility_state = True  
if "cce_foil_generated" not in st.session_state:
    st.session_state.cce_foil_generated = False

live_db = load_live_data()

# --- मुख्य लॉगिन गेटवे ---
if st.session_state.user_role is None:
    st.markdown("---")
    st.subheader("🔒 Multi-User Secure Login Gateway")
    user_input = st.selectbox("Username (भूमिका) चुनें:", options=list(CREDENTIALS.keys()))
    password_input = st.text_input("Password दर्ज करें:", type="password")
    
    if st.button("Secure Login", use_container_width=True, type="primary"):
        if user_input in CREDENTIALS and CREDENTIALS[user_input]["password"] == password_input:
            st.session_state.user_role = CREDENTIALS[user_input]["role"]
            st.session_state.upload_success = False
            st.session_state.save_success = False
            st.session_state.admin_lock_state = True  
            st.session_state.list_visibility_state = True  
            st.session_state.cce_foil_generated = False
            st.success("✅ लॉगिन सफल!")
            st.rerun()
        else:
            st.error("❌ गलत पासवर्ड!")

# --- लॉगिन के बाद का सिस्टम ---
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

    # ==========================================
    # 📁 1. DATA ENTRY ROLE
    # ==========================================
    if role == "data_entry":
        st.header("📝 Student Data Entry Panel")
        
        entry_method = st.selectbox(
            "⚙️ डेटा एंट्री का माध्यम चुनें (Choose Entry Method):",
            options=["📁 CSV फ़ाइल बल्क अपलोड (Bulk CSV Upload)", "➕ नया छात्र मैनुअल फॉर्म (Manual Form Entry)"]
        )
        st.markdown("---")

        if entry_method == "📁 CSV फ़ाइल बल्क अपलोड (Bulk CSV Upload)":
            st.subheader("📁 CSV File Bulk Upload")
            
            if "csv_uploader_id" not in st.session_state:
                st.session_state.csv_uploader_id = 100

            uploaded_file = st.file_uploader(
                "CSV फ़ाइल चुनें", 
                type=["csv"], 
                key=f"csv_uploader_{st.session_state.csv_uploader_id}"
            )
            
            if uploaded_file is not None:
                try:
                    uploaded_df = pd.read_csv(uploaded_file, dtype=str).fillna("")
                    if st.button("Upload CSV Now", use_container_width=True, type="primary"):
                        for col in DEFAULT_COLUMNS:
                            if col not in uploaded_df.columns:
                                uploaded_df[col] = ""
                        cleaned_uploaded_df = uploaded_df[DEFAULT_COLUMNS].copy()
                        
                        current_db = load_live_data()
                        updated_df = cleaned_uploaded_df if current_db.empty else pd.concat([current_db, cleaned_uploaded_df], ignore_index=True)
                        save_live_data(updated_df)
                        
                        st.session_state.upload_success = True
                        st.session_state.save_success = False
                        st.session_state.csv_uploader_id += 1  
                        st.rerun()
                except Exception as e:
                    st.error(f"त्रुटि: {e}")

            if st.session_state.upload_success:
                st.success("✅ CSV Data Filtered & Successfully Uploaded!")
                st.session_state.upload_success = False

        elif entry_method == "➕ नया छात्र मैनुअल फॉर्म (Manual Form Entry)":
            st.subheader("➕ Naya Student Data Add Karein")
            with st.form(key="student_add_form", clear_on_submit=True):
                admission_year = st.text_input("Admission Year")
                admission_session = st.text_input("Admission Session")
                eligibility_name = st.text_input("Eligibility Name")
                admission_app_no = st.text_input("Admission Application Number")
                admission_date = st.text_input("Admission Date")
                unique_id = st.text_input("Unique ID")
                roll_no = st.text_input("Roll No.")
                app_enroll_no = st.text_input("Application Enrollment No.")
                enrollment_no = st.text_input("Enrollment No.")
                s_name = st.text_input("Student Name")
                f_name = st.text_input("Father Name")
                m_name = st.text_input("Mother Name")
                dob = st.text_input("Date of Birth")
                category = st.selectbox("Category", ["General", "OBC", "SC", "ST"])
                subject = st.text_input("Subject")
                duration = st.text_input("Duration")
                mobile = st.text_input("Mobile Number")
                email = st.text_input("Email ID")
                address = st.text_input("Address")
                status_input = st.selectbox("Status", ["Active", "Pending", "Pass", "Inactive"])
                submit_student = st.form_submit_button("Save Student Data", type="primary", use_container_width=True)

            if submit_student:
                if s_name.strip() == "":
