import streamlit as st
import pandas as pd
import os
import base64

# पेज का लेआउट सेट करें
st.set_page_config(layout="wide")

# प्रिंट फ़ॉर्मेटिंग और लेआउट को व्यवस्थित करने के लिए CSS
st.markdown("""
    <style>
    @media print {
        [data-testid="stHeader"], div[element-to-hide="true"], .stButton, .stFileUploader, header, footer, [data-testid="stForm"] {
            display: none !important;
        }
        .main .block-container { padding-top: 0px !important; padding-bottom: 0px !important; }
    }
    .header-container {
        display: flex;
        align-items: center;
        gap: 20px;
        margin-bottom: 20px;
    }
    .header-text {
        display: flex;
        flex-direction: column;
    }
    .header-text h3 {
        margin: 0 !important;
        padding: 0 !important;
        color: #FF5733;
    }
    .header-text h1 {
        margin: 0 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- लोगो/इमेज को लोड करने के लिए फंक्शन (Base64 रूपांतरण) ---
def get_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode()
            return f"data:image/png;base64,{encoded}"
    return ""

IMAGE_PATH = "logo pratap.png"
img_base64 = get_image_base64(IMAGE_PATH)

# --- शीर्ष अनुभाग (Header Section) ---
if img_base64:
    st.markdown(f"""
        <div class="header-container">
            <img src="{img_base64}" width="90" style="border-radius: 10px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);"/>
            <div class="header-text">
                <h3>ॐ गुरुवर्य नमः</h3>
                <h1>Permanent Shared Live Database</h1>
            </div>
        </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
        <div class="header-container">
            <div class="header-text">
                <h3>ॐ गुरुवर्य नमः</h3>
                <h1>Permanent Shared Live Database</h1>
            </div>
        </div>
    """, unsafe_allow_html=True)

# डेटाबेस फ़ाइल पाथ
DB_FILE = "shared_student_database.csv"

# 🔑 3-स्तरीय सुरक्षा क्रेडेंशियल्स सेटिंग्स
CREDENTIALS = {
    "entry": {"password": "entry123", "role": "data_entry"},
    "viewer": {"password": "viewer123", "role": "list_viewer"},
    "admin": {"password": "admin123", "role": "full_admin"}
}

DEFAULT_COLUMNS = [
    "Eligibility", "Unique ID", "Roll No.", 
    "Application No.", "Enrollment No.", "Student Name", "Father Name",
    "Mother Name", "Date of Birth", "Category", "Subject", 
    "Duration", "Mobile No.", "Email ID", "Address", "Status"
]

ELIGIBILITY_OPTIONS = ["None", "U.G.", "P.G."]
DURATION_OPTIONS = ["None", "1 Year", "2 Year", "3 Year", "4 Year", "5 Year", "6 Year"]
STATUS_OPTIONS = ["Active", "Pending", "Pass", "Inactive"]

# फ़ाइल से डेटा लोड करने का मजबूत फंक्शन
def load_live_data():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE, dtype=str)
            for col in DEFAULT_COLUMNS:
                if col not in df.columns:
                    df[col] = ""
            return df[DEFAULT_COLUMNS].fillna("").reset_index(drop=True)
        except:
            pass
    return pd.DataFrame(columns=DEFAULT_COLUMNS)

# फ़ाइल में डेटा पक्का सुरक्षित करने का फंक्शन
def save_live_data(df_to_save):
    df_to_save.fillna("").astype(str).to_csv(DB_FILE, index=False)

# मेमोरी स्टेट्स सेटअप (Session States)
if "user_role" not in st.session_state:
    st.session_state.user_role = None  
if "upload_success" not in st.session_state:
    st.session_state.upload_success = False
if "save_success" not in st.session_state:
    st.session_state.save_success = False
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False
if "column_move_mode" not in st.session_state:
    st.session_state.column_move_mode = False
if "current_column_order" not in st.session_state:
    st.session_state.current_column_order = DEFAULT_COLUMNS.copy()
if "select_all_checked" not in st.session_state:
    st.session_state.select_all_checked = False

# सीधे परमानेंट स्टोरेज से लाइव डेटा लोड करें
live_db = load_live_data()

# --- मुख्य लॉगिन गेटवे ---
if st.session_state.user_role is None:
    st.markdown("---")
    st.subheader("🔒 Multi-User Secure Login Gateway")
    
    with st.form(key="secure_login_form"):
        user_input = st.selectbox("Username (भूमिका) चुनें:", options=list(CREDENTIALS.keys()))
        password_input = st.text_input("Password दर्ज करें:", type="password")
        login_submit = st.form_submit_button("Secure Login", use_container_width=True, type="primary")
        
    if login_submit:
        if user_input in CREDENTIALS and CREDENTIALS[user_input]["password"] == password_input:
            st.session_state.user_role = CREDENTIALS[user_input]["role"]
            st.session_state.upload_success = False
            st.session_state.save_success = False
            st.session_state.edit_mode = False
            st.session_state.column_move_mode = False
            st.success(f"✅ लॉगिन सफल! भूमिका: {st.session_state.user_role.upper()}")
            st.rerun()
        else:
            st.error("❌ गलत पासवर्ड! कृपया सही पासवर्ड दर्ज करें।")

# --- यदि लॉगिन सफल हो चुका है, तो रोल के हिसाब से सिस्टम खोलें ---
if st.session_state.user_role is not None:
    
    # यूनिवर्सल लॉगआउट बटन
    if st.button("🔒 मुख्य लॉगआउट (Exit Secure System)", type="primary", use_container_width=True):
        st.session_state.user_role = None
        st.session_state.upload_success = False
        st.session_state.save_success = False
        st.session_state.edit_mode = False
        st.session_state.column_move_mode = False
        st.rerun()

    st.markdown("---")
    
    # क्रेडेंशियल कंडीशन्स वेरिएबल्स
    is_entry_only = (st.session_state.user_role == "data_entry")
    is_viewer_only = (st.session_state.user_role == "list_viewer")
    is_admin = (st.session_state.user_role == "full_admin")

    # ==========================================
    # 🛠️ भाग 1: डेटा एंट्री और फ़ाइल अपलोड (केवल entry के लिए - Admin और Viewer से बंद)
    # ==========================================
    if is_entry_only:
        st.header("📁 CSV File Bulk Upload")
        uploaded_file = st.file_uploader("CSV फ़ाइल चुनें", type=["csv"])
        if uploaded_file is not None:
            try:
                uploaded_df = pd.read_csv(uploaded_file, dtype=str).fillna("")
                if st.button("Upload CSV Now"):
                    if "Admission No." in uploaded_df.columns:
                        uploaded_df = uploaded_df.drop(columns=["Admission No."])
                    current_db = load_live_data()
                    if current_db.empty:
                        updated_df = uploaded_df
                    else:
                        updated_df = pd.concat([current_db, uploaded_df], ignore_index=True)
                    save_live_data(updated_df)
                    st.session_state.upload_success = True
                    st.session_state.save_success = False
                    st.rerun()
            except Exception as e:
                st.error(f"त्रुटि: {e}")

        if st.session_state.upload_success:
            st.success("✅ Data Complete upload")

        st.markdown("---")

        st.header("➕ Naya Student Data Add Karein")
        with st.form(key="student_add_form", clear_on_submit=True):
            eligibility = st.selectbox("Eligibility", ELIGIBILITY_OPTIONS)
            unique_id = st.text_input("Unique ID")
            roll_no = st.text_input("Roll No.")
            application_no = st.text_input("Application No.")
            enr_no = st.text_input("Enrollment No.")
            s_name = st.text_input("Student Name")
            f_name = st.text_input("Father Name")
            m_name = st.text_input("Mother Name")
            dob = st.text_input("Date of Birth")
            category = st.text_input("Category")
            subject = st.text_input("Subject")
            duration = st.selectbox("Duration", DURATION_OPTIONS)
            mobile = st.text_input("Mobile No.")
            email = st.text_input("Email ID")
            address = st.text_input("Address")
            status_input = st.selectbox("Status", STATUS_OPTIONS)
            submit_student = st.form_submit_button("Save Student Data", type="primary", use_container_width=True)

        if submit_student:
            if s_name.strip() == "":
                st.warning("कृपया कम से कम Student Name ज़रूर भरें।")
            else:
                new_row = {
                    "Eligibility": eligibility, "Unique ID": unique_id, "Roll No.": roll_no,
                    "Application No.": application_no, "Enrollment No.": enr_no, "Student Name": s_name, "Father Name": f_name,
                    "Mother Name": m_name, "Date of Birth": dob, "Category": category, "Subject": subject,
                    "Duration": duration, "Mobile No.": mobile, "Email ID": email, "Address": address, "Status": status_input
                }
                current_db = load_live_data()
                if current_db.empty:
                    updated_df = pd.DataFrame([new_row])
                else:
                    updated_df = pd.concat([current_db, pd.DataFrame([new_row])], ignore_index=True)
                save_live_data(updated_df)
                st.session_state.save_success = True
                st.session_state.upload_success = False
                st.rerun()

        if st.session_state.save_success:
            st.success("✅ data save successfully")
            st.session_state.save_success = False

    # ==========================================
    # 📊 भाग 2: छात्र सूची प्रदर्शन (केवल viewer और admin पासवर्ड में ही खुलेगा)
    # ==========================================
    if is_viewer_only or is_admin:
        st.header("📊 Live Student Database Table")
        
        fresh_db = load_live_data()
        
        safe_order = [c for c in st.session_state.current_column_order if c in DEFAULT_COLUMNS]
        
