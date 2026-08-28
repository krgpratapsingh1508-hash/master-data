import streamlit as st
import pandas as pd
import os

# पेज का लेआउट सेट करें (चौड़ा व्यू)
st.set_page_config(layout="wide")

# सिर्फ डेटा तालिका को प्रिंट करने के लिए और बटनों को मोबाइल पर भी जबरदस्ती अगल-बगल रखने के लिए CSS
st.markdown("""
    <style>
    @media print {
        [data-testid="stHeader"], div[element-to-hide="true"], .stButton, .stFileUploader, header, footer, [data-testid="stForm"] {
            display: none !important;
        }
        .main .block-container { padding-top: 0px !important; padding-bottom: 0px !important; }
    }
    
    /* 🛠️ मोबाइल और कंप्यूटर दोनों पर एक्शन बटनों को एक ही लाइन में रखने का अचूक कोड */
    .action-container {
        display: flex !important;
        flex-direction: row !important;
        justify-content: space-between !important;
        gap: 10px !important;
        width: 100% !important;
    }
    .action-container > div {
        flex: 1 !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("Permanent Shared Live Database")

# डेटा को सुरक्षित रखने के लिए लोकल फ़ाइल पाथ
DB_FILE = "shared_student_database.csv"

# 🔑 यहाँ अपना मनपसंद यूज़रनेम और पासवर्ड सेट करें
CORRECT_USERNAME = "admin"
CORRECT_PASSWORD = "admin123"

DEFAULT_COLUMNS = [
    "Eligibility", "Unique ID", "Roll No.", 
    "Application No.", "Enrollment No.", "Student Name", "Father Name",
    "Mother Name", "Date of Birth", "Category", "Subject", 
    "Duration", "Mobile No.", "Email ID", "Address", "Status"
]

# ड्रॉपडाउन के लिए विकल्प (Options) डेफिनिशन
ELIGIBILITY_OPTIONS = ["None", "U.G.", "P.G."]
DURATION_OPTIONS = ["None", "1 Year", "2 Year", "3 Year", "4 Year", "5 Year", "6 Year"]
STATUS_OPTIONS = ["Active", "Pending", "Pass", "Inactive"]

# फ़ाइल से डेटा लोड करने का मजबूत फंक्शन (सभी डिवाइसेज के लिए)
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

# मेमोरी स्टेट्स (Session States) को सेट करें
if "select_all_state" not in st.session_state:
    st.session_state.select_all_state = False

if "database_unlocked" not in st.session_state:
    st.session_state.database_unlocked = False

if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False

# सीधे परमानेंट स्टोरेज से लाइव डेटा लोड करें
live_db = load_live_data()


# --- लॉगिन फॉर्म (यूज़रनेम और पासवर्ड दोनों) ---
if not st.session_state.database_unlocked:
    st.markdown("---")
    st.subheader("🔒 Admin Login Required")
    
    with st.form(key="login_form"):
        user_input = st.text_input("Username दर्ज करें:")
        password_input = st.text_input("Password दर्ज करें:", type="password")
        login_submit = st.form_submit_button("Login करें", use_container_width=True, type="primary")
        
    if login_submit:
        if user_input == CORRECT_USERNAME and password_input == CORRECT_PASSWORD:
            st.session_state.database_unlocked = True
            st.success("✅ लॉगिन सफल! डेटाबेस अनलॉक हो गया है।")
            st.rerun()
        else:
            st.error("❌ गलत यूज़रनेम या पासवर्ड! कृपया सही क्रेडेंशियल्स दर्ज करें।")


# --- यदि डेटाबेस अनलॉक है, तभी नीचे का पूरा सिस्टम (अपलोड, फॉर्म, टेबल) दिखेगा ---
if st.session_state.database_unlocked:

    # --- सेक्शन 1: CSV फ़ाइल से बल्क डेटा अपलोड करें ---
    st.markdown('<div element-to-hide="true">', unsafe_allow_html=True)
    st.header("📁 CSV File Se Bulk Data Upload Karein")
    uploaded_file = st.file_uploader("CSV फ़ाइल चुनें", type=["csv"])

    if uploaded_file is not None:
        try:
            uploaded_df = pd.read_csv(uploaded_file, dtype=str).fillna("")
            if st.button("Upload CSV", type="primary"):
                if "Admission No." in uploaded_df.columns:
                    uploaded_df = uploaded_df.drop(columns=["Admission No."])
                updated_df = pd.concat([live_db, uploaded_df], ignore_index=True)
                save_live_data(updated_df)
                st.success("CSV डेटा सफलतापूर्वक डेटाबेस में जोड़ दिया गया है!")
                st.rerun()
        except Exception as e:
            st.error(f"CSV फ़ाइल पढ़ने में त्रुटि: {e}")
    st.markdown('</div>', unsafe_allow_html=True)


    # --- सेक्शन 2: नया स्टूडेंट डेटा मैनुअली ऐड करें ---
    st.markdown('<div element-to-hide="true">', unsafe_allow_html=True)
    st.header("➕ Naya Student Data Add Karein")

    with st.form(key="student_form", clear_on_submit=True):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            eligibility = st.selectbox("Eligibility", ELIGIBILITY_OPTIONS)
            enr_no = st.text_input("Enrollment No.")
            m_name = st.text_input("Mother Name")
            duration = st.selectbox("Duration", DURATION_OPTIONS)
        with col2:
            unique_id = st.text_input("Unique ID")
            dob = st.text_input("Date of Birth")
            mobile = st.text_input("Mobile No.")
            email = st.text_input("Email ID")
        with col3:
            roll_no = st.text_input("Roll No.")
            category = st.text_input("Category")
            subject = st.text_input("Subject")
            address = st.text_input("Address")
        with col4:
            application_no = st.text_input("Application No.")
            s_name = st.text_input("Student Name")
            f_name = st.text_input("Father Name")
            status_input = st.selectbox("Status", STATUS_OPTIONS)

        submit_button = st.form_submit_button("Save Student Data", use_container_width=True, type="primary")

    if submit_button:
        if s_name.strip() == "":
            st.warning("कृपया कम से कम Student Name ज़रूर भरें।")
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
            st.success("डेटा सफलतापूर्वक हमेशा के लिए सेव हो गया है!")
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


    # --- सेक्शन 3: लाइव स्टूडेंट डेटाबेस तालिका ---
    st.header("📊 Live Student Database")

    if not live_db.empty and len(live_db) > 0:
        display_df = live_db.copy().reset_index(drop=True)
        
        # --- एक्शन बटन रो (Row): 4 बटन्स बिल्कुल सटीक स्पेसिंग के साथ ---
        st.markdown('<div element-to-hide="true">', unsafe_allow_html=True)
        act_col1, act_col2, act_col3, act_col4 = st.columns(4)
        
        with act_col1:
            btn_label = "⬜ सब सेलेक्ट करें" if not st.session_state.select_all_state else "⬛ सभी अन-सेलेक्ट करें"
            if st.button(btn_label, use_container_width=True):
                st.session_state.select_all_state = not st.session_state.select_all_state
                st.rerun()
                
        with act_col2:
            csv_data = live_db.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="💾 CSV डाउनलोड करें",
                data=csv_data,
                file_name="student_database_export.csv",
                mime="text/csv",
                use_container_width=True,
                type="secondary"
            )
            
        with act_col3:
            if st.button("🖨️ लिस्ट प्रिंट करें", use_container_width=True, type="secondary"):
                st.markdown("""<script>window.print();</script>""", unsafe_allow_html=True)
            
        with act_col4:
            if st.button("🔒 लॉगआउट करें", use_container_width=True, type="primary"):
                st.session_state.database_unlocked = False
                st.session_state.edit_mode = False
                st.session_state.select_all_state = False
                st.rerun()
                
        st.markdown('</div>', unsafe_allow_html=True)

        # तालिका सेटअप
        display_df.insert(0, "Delete स्टूडेंट", st.session_state.select_all_state)
        display_df.index = display_df.index + 1
        display_df.index.name = "S. No."

        column_configuration = {
            "Delete स्टूडेंट": st.column_config.CheckboxColumn("Delete स्टूडेंट", help="डेटा डिलीट करने के लिए टिक करें"),
            "Eligibility": st.column_config.SelectboxColumn("Eligibility", options=ELIGIBILITY_OPTIONS, required=True),
            "Duration": st.column_config.SelectboxColumn("Duration", options=DURATION_OPTIONS, required=True),
            "Status": st.column_config.SelectboxColumn("Status", options=STATUS_OPTIONS, required=True)
        }

        if st.session_state.edit_mode:
            disabled_cols = ["Delete स्टूडेंट"]
            st.info("📝 एडमिट मोड एक्टिव है! तालिका में सीधे बदलाव कर सकते हैं।")
        else:
            disabled_cols = [col for col in display_df.columns if col != "Delete Student" and col != "Delete स्टूडेंट"]

        edited_df = st.data_editor(
            display_df,
            hide_index=False,
            column_config=column_configuration,
            disabled=disabled_cols,
            use_container_width=True
        )

        # --- एडिट और सेव बटन्स ---
        st.markdown('<div element-to-hide="true">', unsafe_allow_html=True)
        col_ed1, col_ed2 = st.columns(2)
                 
