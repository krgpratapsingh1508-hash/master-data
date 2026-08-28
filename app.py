import streamlit as st
import pandas as pd
import os

# पेज का लेआउट सेट करें
st.set_page_config(layout="wide")

# प्रिंट फ़ॉर्मेटिंग के लिए CSS
st.markdown("""
    <style>
    @media print {
        [data-testid="stHeader"], div[element-to-hide="true"], .stButton, .stFileUploader, header, footer, [data-testid="stForm"] {
            display: none !important;
        }
        .main .block-container { padding-top: 0px !important; padding-bottom: 0px !important; }
    }
    </style>
""", unsafe_allow_html=True)

st.title("Permanent Shared Live Database")

# डेटाबेस फ़ाइल पाथ
DB_FILE = "shared_student_database.csv"

# 🔑 सुरक्षा सेटिंग्स
CORRECT_USERNAME = "admin"
CORRECT_PASSWORD = "admin123"
LIST_PASSWORD = "list789"

DEFAULT_COLUMNS = [
    "Eligibility", "Unique ID", "Roll No.", 
    "Application No.", "Enrollment No.", "Student Name", "Father Name",
    "Mother Name", "Date of Birth", "Category", "Subject", 
    "Duration", "Mobile No.", "Email ID", "Address", "Status"
]

ELIGIBILITY_OPTIONS = ["None", "U.G.", "P.G."]
DURATION_OPTIONS = ["None", "1 Year", "2 Year", "3 Year", "4 Year", "5 Year", "6 Year"]
STATUS_OPTIONS = ["Active", "Pending", "Pass", "Inactive"]

# डेटा लोड करने का फंक्शन
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

# डेटा सेव करने का फंक्शन
def save_live_data(df_to_save):
    df_to_save.fillna("").astype(str).to_csv(DB_FILE, index=False)

# मेमोरी स्टेट्स सेटअप
if "select_all_state" not in st.session_state:
    st.session_state.select_all_state = False
if "database_unlocked" not in st.session_state:
    st.session_state.database_unlocked = False
if "list_unlocked" not in st.session_state:
    st.session_state.list_unlocked = False
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False

live_db = load_live_data()

# --- मुख्य लॉगिन सिस्टम ---
if not st.session_state.database_unlocked:
    st.subheader("🔒 Admin Login")
    user_input = st.text_input("Username:")
    password_input = st.text_input("Password:", type="password")
    if st.button("Login", type="primary", use_container_width=True):
        if user_input == CORRECT_USERNAME and password_input == CORRECT_PASSWORD:
            st.session_state.database_unlocked = True
            st.rerun()
        else:
            st.error("गलत यूज़रनेम या पासवर्ड!")

# --- लॉगिन होने के बाद का मुख्य पैनल ---
if st.session_state.database_unlocked:
    
    # मुख्य लॉगआउट बटन (फाइल एग्जिट करने के लिए)
    if st.button("🔒 मुख्य लॉगआउट (Exit File)", type="primary", use_container_width=True):
        st.session_state.database_unlocked = False
        st.session_state.list_unlocked = False
        st.session_state.edit_mode = False
        st.session_state.select_all_state = False
        st.rerun()

    st.markdown("---")
    
    # 📁 बल्क डेटा अपलोड सेक्शन
    st.header("📁 CSV File Bulk Upload")
    uploaded_file = st.file_uploader("CSV फ़ाइल चुनें", type=["csv"])
    if uploaded_file is not None:
        try:
            uploaded_df = pd.read_csv(uploaded_file, dtype=str).fillna("")
            if st.button("Upload CSV Now"):
                if "Admission No." in uploaded_df.columns:
                    uploaded_df = uploaded_df.drop(columns=["Admission No."])
                updated_df = pd.concat([live_db, uploaded_df], ignore_index=True)
                save_live_data(updated_df)
                st.success("डेटा जोड़ दिया गया है!")
                st.rerun()
        except Exception as e:
            st.error(f"त्रुटि: {e}")

    st.markdown("---")

    # ➕ मैनुअल डेटा एंट्री सेक्शन
    st.header("➕ Naya Student Data Add Karein")
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

    if st.button("Save Student Data", type="primary", use_container_width=True):
        if s_name.strip() == "":
            st.warning("कृपया Student Name ज़रूर भरें।")
        else:
            new_row = {
                "Eligibility": eligibility, "Unique ID": unique_id, "Roll No.": roll_no,
                "Application No.": application_no, "Enrollment No.": enr_no, "Student Name": s_name, "Father Name": f_name,
                "Mother Name": m_name, "Date of Birth": dob, "Category": category, "Subject": subject,
                "Duration": duration, "Mobile No.": mobile, "Email ID": email, "Address": address, "Status": status_input
            }
            fresh_db = load_live_data()
            updated_df = pd.concat([fresh_db, pd.DataFrame([new_row])], ignore_index=True)
            save_live_data(updated_df)
            st.success("डेटा हमेशा के लिए सेव हो गया है!")
            st.rerun()

    st.markdown("---")

    # 📊 डेटा लिस्ट लॉक और प्रोटेक्शन सेक्शन
    st.header("📊 Live Student Database")
    if not st.session_state.list_unlocked:
        list_pass = st.text_input("⚠️ छात्र सूची (Data List) देखने के लिए पासवर्ड डालें:", type="password")
        if st.button("डेटा लिस्ट अनलॉक करें", use_container_width=True):
            if list_pass == LIST_PASSWORD:
                st.session_state.list_unlocked = True
                st.rerun()
            else:
                st.error("गलत लिस्ट पासवर्ड!")

    # --- लिस्ट अनलॉक होने के बाद तालिका दृश्य ---
    if st.session_state.list_unlocked:
        if not live_db.empty and len(live_db) > 0:
            display_df = live_db.copy().reset_index(drop=True)
            
            # एक्शन बटन्स की सीधी लिस्ट
            if st.button("⬜ सब सेलेक्ट / अन-सेलेक्ट करें", use_container_width=True):
                st.session_state.select_all_state = not st.session_state.select_all_state
                st.rerun()
                
            csv_data = live_db.to_csv(index=False).encode('utf-8')
            st.download_button(label="💾 CSV डाउनलोड करें", data=csv_data, file_name="student_database.csv", mime="text/csv", use_container_width=True)
            
            if st.button("🖨️ लिस्ट प्रिंट करें", use_container_width=True):
                st.markdown("""<script>window.print();</script>""", unsafe_allow_html=True)
                
            if st.button("🔒 सिर्फ लिस्ट लॉक करें", use_container_width=True):
                st.session_state.list_unlocked = False
                st.session_state.edit_mode = False
                st.rerun()

            st.markdown("---")

            # तालिका डेटा सेटिंग्स
            display_df.insert(0, "Delete स्टूडेंट", st.session_state.select_all_state)
            display_df.index = display_df.index + 1
            display_df.index.name = "S. No."

            column_configuration = {
                "Delete स्टूडेंट": st.column_config.CheckboxColumn("Delete स्टूडेंट"),
                "Eligibility": st.column_config.SelectboxColumn("Eligibility", options=ELIGIBILITY_OPTIONS, required=True),
                "Duration": st.column_config.SelectboxColumn("Duration", options=DURATION_OPTIONS, required=True),
                "Status": st.column_config.SelectboxColumn("Status", options=STATUS_OPTIONS, required=True)
            }

            if st.session_state.edit_mode:
                disabled_cols = ["Delete स्टूडेंट"]
                st.info("📝 एडिट मोड एक्टिव है!")
            else:
                disabled_cols = [col for col in display_df.columns if col != "Delete स्टूडेंट"]

            edited_df = st.data_editor(
                display_df,
                hide_index=False,
                column_config=column_configuration,
                disabled=disabled_cols,
                use_container_width=True
            )

            # लिस्ट कंट्रोल बटन्स
            if st.button("📝 पूरी लिस्ट एडिट करें (Edit Mode)", use_container_width=True):
                st.session_state.edit_mode = True
                st.rerun()
                    
            if st.button("💾 डेटा लॉक और सेव करें (Save Changes)", use_container_width=True):
                final_df = edited_df.copy()
                final_df = final_df[final_df["Delete स्टूडेंट"] == False]
                if "Delete स्टूडेंट" in final_df.columns:
                    final_df = final_df.drop(columns=["Delete student", "Delete स्टूडेंट"], errors="ignore")
                save_live_data(final_df)
                st.session_state.edit_mode = False
                st.session_state.select_all_state = False
                st.session_state.list_unlocked = True
                st.success("बदलाव सेव हो गए हैं!")
                st.rerun()
        else:
            st.info("डेटाबेस अभी खाली है।")
                
