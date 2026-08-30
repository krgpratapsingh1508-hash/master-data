import streamlit as st
import pandas as pd
import os
import base64

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

# 🔑 4-स्तरीय सुरक्षा क्रेडेंशियल्स सेटिंग्स
CREDENTIALS = {
    "entry": {"password": "entry123", "role": "data_entry"},
    "viewer": {"password": "viewer123", "role": "list_viewer"},
    "cce": {"password": "cce123", "role": "cce_handler"},
    "admin": {"password": "admin123", "role": "full_admin"}
}

# 🎯 कॉलम्स की मास्टर सूची
DEFAULT_COLUMNS = [
    "Admission Year", "Admission Session", "Eligibility Name", "Admission Application Number",
    "Admission Date", "Unique ID", "Roll No.", "Application Enrollment No.",
    "Enrollment No.", "Student Name", "Father Name", "Mother Name", "Date of Birth",
    "Category", "Subject", "Duration", "Mobile Number", "Email ID", "Address", "Status",
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

# ==========================================================
# 🔒 मुख्य लॉगिन गेटवे (इसके बाहर कुछ नहीं दिखेगा)
# ==========================================================
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

# ==========================================================
# 🔑 लॉगिन के बाद का मुख्य सिस्टम (केवल पासवर्ड डालने पर एक्टिव होगा)
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

    # --------------------------------------------------
    # 📁 A. DATA ENTRY PANEL (Role: data_entry या full_admin)
    # --------------------------------------------------
    if role in ["data_entry", "full_admin"]:
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

            uploaded_file = st.file_uploader("CSV फ़ाइल चुनें", type=["csv"], key=f"csv_uploader_{st.session_state.csv_uploader_id}")
            if uploaded_file is not None:
                try:
                    uploaded_df = pd.read_csv(uploaded_file, dtype=str).fillna("")
                    if st.button("Upload CSV Now", use_container_width=True, type="primary"):
                        for col in DEFAULT_COLUMNS:
                            if col not in uploaded_df.columns:
                                uploaded_df[col] = ""
                        cleaned_uploaded_df = uploaded_df[DEFAULT_COLUMNS].copy()
                        current_db = load_live_data()
                        if current_db.empty:
                            updated_df = cleaned_uploaded_df
                        else:
                            updated_df = pd.concat([current_db, cleaned_uploaded_df], ignore_index=True)
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
                col1, col2 = st.columns(2)
                with col1:
                    admission_year = st.text_input("Admission Year (प्रवेश वर्ष)")
                    eligibility_name = st.text_input("Eligibility Name (योग्यता का नाम)")
                    admission_date = st.text_input("Admission Date (प्रवेश तिथि)")
                    roll_no = st.text_input("Roll No. (रोल नंबर)")
                    enrollment_no = st.text_input("Enrollment No. (स्थायी नामांकन संख्या)")
                    f_name = st.text_input("Father Name (पिता का नाम)")
                    dob = st.text_input("Date of Birth (जन्म तिथि)")
                    subject = st.text_input("Subject (विषय/स्ट्रीम)")
                    mobile = st.text_input("Mobile Number (मोबाइल नंबर)")
                    address = st.text_input("Address (पता)")
                with col2:
                    admission_session = st.text_input("Admission Session (सत्र)")
                    admission_app_no = st.text_input("Admission Application Number (आवेदन संख्या)")
                    unique_id = st.text_input("Unique ID (आधार या स्कॉलर नंबर)")
                    app_enroll_no = st.text_input("Application Enrollment No. (एप्लिकेशन नामांकन संख्या)")
                    s_name = st.text_input("Student Name (छात्र का नाम)")
                    
