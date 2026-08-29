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
CREDENTIALS = {
    "entry": {"password": "entry123", "role": "data_entry"},
    "viewer": {"password": "viewer123", "role": "list_viewer"},
    "admin": {"password": "admin123", "role": "full_admin"}
}

DEFAULT_COLUMNS = [
    "Eligibility", "Unique ID", "Roll No.", "Application No.", "Enrollment No.", 
    "Student Name", "Father Name", "Mother Name", "Date of Birth", "Category", 
    "Subject", "Duration", "Mobile No.", "Email ID", "Address", "Status"
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
        return df[DEFAULT_COLUMNS].fillna("").reset_index(drop=True)
    except:
        return pd.DataFrame(columns=DEFAULT_COLUMNS)

def save_live_data(df_to_save):
    df_to_save.fillna("").astype(str).to_csv(DB_FILE, index=False)

if "user_role" not in st.session_state:
    st.session_state.user_role = None  
if "upload_success" not in st.session_state:
    st.session_state.upload_success = False
if "save_success" not in st.session_state:
    st.session_state.save_success = False

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
            st.success("✅ लॉगिन सफल!")
            st.rerun()
        else:
            st.error("❌ गलत पासवर्ड!")

# --- लॉगिन के बाद का सिस्टम ---
else:
    if st.button("🔒 मुख्य लॉगआउट (Exit Secure System)", type="primary", use_container_width=True):
        st.session_state.user_role = None
        st.session_state.upload_success = False
        st.session_state.save_success = False
        st.rerun()

    st.markdown("---")
    role = st.session_state.user_role

    # ==========================================
    # DATA ENTRY ROLE
    # ==========================================
    if role == "data_entry":
        st.header("📁 CSV File Bulk Upload")
        uploaded_file = st.file_uploader("CSV फ़ाइल चुनें", type=["csv"])
        if uploaded_file is not None:
            try:
                uploaded_df = pd.read_csv(uploaded_file, dtype=str).fillna("")
                if st.button("Upload CSV Now"):
                    if "Admission No." in uploaded_df.columns:
                        uploaded_df = uploaded_df.drop(columns=["Admission No."])
                    current_db = load_live_data()
                    updated_df = uploaded_df if current_db.empty else pd.concat([current_db, uploaded_df], ignore_index=True)
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
            eligibility = st.selectbox("Eligibility", ["None", "U.G.", "P.G."])
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
            duration = st.selectbox("Duration", ["None", "1 Year", "2 Year", "3 Year", "4 Year", "5 Year", "6 Year"])
            mobile = st.text_input("Mobile No.")
            email = st.text_input("Email ID")
            address = st.text_input("Address")
            status_input = st.selectbox("Status", ["Active", "Pending", "Pass", "Inactive"])
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
                updated_df = pd.DataFrame([new_row]) if current_db.empty else pd.concat([current_db, pd.DataFrame([new_row])], ignore_index=True)
                save_live_data(updated_df)
                st.session_state.save_success = True
                st.session_state.upload_success = False
                st.rerun()

        if st.session_state.save_success:
            st.success("✅ data save successfully")
            st.session_state.save_success = False

    # ==========================================
    # VIEWER & ADMIN ROLES
    # ==========================================
    if role in ["list_viewer", "full_admin"]:
        st.header("📊 Student Live Database List")
        search_query = st.text_input("🔍 Student Name या Roll No. दर्ज करके खोजें:")
        
        filtered_db = live_db.copy()
        if search_query:
            filtered_db = filtered_db[
                filtered_db["Student Name"].str.contains(search_query, case=False, na=False) |
                filtered_db["Roll No."].str.contains(search_query, case=False, na=False)
            ]
            
        st.write(f"📋 कुल छात्र रिकॉर्ड: **{len(filtered_db)}**")
        
        if not filtered_db.empty:
            # सीरियल नंबर को 1 से शुरू करने का लॉजिक
            filtered_db.index = filtered_db.index + 1
            
            # डाउनलोड के लिए डेटा फ्रेम पहले से ही तैयार कर लें ताकि एरर न आए
            download_df = filtered_db.copy()
            
            # केवल Admin के लिए एडवांस्ड 'All Select' और 'Bulk Action' फीचर
            if role == "full_admin":
                st.markdown("### 🛠️ Admin Control Panel")
                select_all = st.checkbox("✅ Select All Students (सभी छात्रों को एक साथ चुनें)")
                
                if select_all:
                    filtered_db.insert(0, "Select", True)
                else:
                    filtered_db.insert(0, "Select", False)
                
                # स्ट्रीमलिट डेटा एडिटर रेंडर करें
                edited_df = st.data_editor(filtered_db, use_container_width=True, disabled=[col for col in filtered_db.columns if col != "Select"])
                
                # डाउनलोड के लिए 'Select' कॉलम को क्लीन करें
                if "Select" in edited_df.columns:
                    download_df = edited_df.drop(columns=["Select"])
                
                selected_rows = edited_df[edited_df["Select"] == True]
                st.info(f"🎯 चुने गए छात्र रिकॉर्ड्स की संख्या: **{len(selected_rows)}**")
                
                if len(selected_rows) > 0:
                    col1, col2 = st.columns(2)
                    with col1:
                        new_status = st.selectbox("चयनित छात्रों का नया Status बदलें:", ["Active", "Pending", "Pass", "Inactive"])
                        
