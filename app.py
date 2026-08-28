import streamlit as st
import pandas as pd
import os

# पेज का लेआउट सेट करें (चौड़ा व्यू)
st.set_page_config(layout="wide")

# सिर्फ डेटा तालिका को प्रिंट करने के लिए स्पेशल CSS कोड
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

# डेटा को सुरक्षित रखने के लिए लोकल फ़ाइल पाथ
DB_FILE = "shared_student_database.csv"

# 🔑 यहाँ अपना मनपसंद पासवर्ड सेट करें (अभी 'admin123' है)
CORRECT_PASSWORD = "admin123"

DEFAULT_COLUMNS = [
    "Admission No.", "Eligibility", "Unique ID", "Roll No.", 
    "Application No.", "Enrollment No.", "Student Name", "Father Name",
    "Mother Name", "Date of Birth", "Category", "Subject", 
    "Duration", "Mobile No.", "Email ID", "Address"
]

# फ़ाइल से डेटा लोड करने का मजबूत फंक्शन (सभी डिवाइसेज के लिए)
def load_live_data():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE, dtype=str)
            # खाली या गलत कॉलम्स को ठीक करें
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

# फॉर्म खाली करने और ऑल-सेलेक्ट के लिए स्टेट्स सेट करें
if "reset_trigger" not in st.session_state:
    st.session_state.reset_trigger = False

if "select_all_state" not in st.session_state:
    st.session_state.select_all_state = False

# सीधे परमानेंट स्टोरेज से लाइव डेटा लोड करें
live_db = load_live_data()

# --- सेक्शन 1: CSV फ़ाइल से बल्क डेटा अपलोड करें ---
st.markdown('<div element-to-hide="true">', unsafe_allow_html=True)
st.header("📁 CSV File Se Bulk Data Upload Karein")
uploaded_file = st.file_uploader("CSV फ़ाइल चुनें", type=["csv"])

if uploaded_file is not None:
    try:
        uploaded_df = pd.read_csv(uploaded_file, dtype=str).fillna("")
        if st.button("Upload CSV", type="primary"):
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

v_adm = "" if st.session_state.reset_trigger else st.session_state.get("adm", "")
v_app = "" if st.session_state.reset_trigger else st.session_state.get("app", "")
v_m_nm = "" if st.session_state.reset_trigger else st.session_state.get("m_nm", "")
v_dur = "" if st.session_state.reset_trigger else st.session_state.get("dur", "")
v_elig = "" if st.session_state.reset_trigger else st.session_state.get("elig", "")
v_enr = "" if st.session_state.reset_trigger else st.session_state.get("enr", "")
v_dob = "" if st.session_state.reset_trigger else st.session_state.get("dob", "")
v_mob = "" if st.session_state.reset_trigger else st.session_state.get("mob", "")
v_uniq = "" if st.session_state.reset_trigger else st.session_state.get("uniq", "")
v_st_nm = "" if st.session_state.reset_trigger else st.session_state.get("st_nm", "")
v_cat = "" if st.session_state.reset_trigger else st.session_state.get("cat", "")
v_eml = "" if st.session_state.reset_trigger else st.session_state.get("eml", "")
v_roll = "" if st.session_state.reset_trigger else st.session_state.get("roll", "")
v_f_nm = "" if st.session_state.reset_trigger else st.session_state.get("f_nm", "")
v_sub = "" if st.session_state.reset_trigger else st.session_state.get("sub", "")
v_adr = "" if st.session_state.reset_trigger else st.session_state.get("adr", "")

st.session_state.reset_trigger = False

with st.form(key="student_form", clear_on_submit=False):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        adm_no = st.text_input("Admission No.", value=v_adm, key="adm")
        app_no = st.text_input("Application No.", value=v_app, key="app")
        m_name = st.text_input("Mother Name", value=v_m_nm, key="m_nm")
        duration = st.text_input("Duration", value=v_dur, key="dur")
    with col2:
        eligibility = st.text_input("Eligibility", value=v_elig, key="elig")
        enr_no = st.text_input("Enrollment No.", value=v_enr, key="enr")
        dob = st.text_input("Date of Birth", value=v_dob, key="dob")
        mobile = st.text_input("Mobile No.", value=v_mob, key="mob")
    with col3:
        unique_id = st.text_input("Unique ID", value=v_uniq, key="uniq")
        s_name = st.text_input("Student Name", value=v_st_nm, key="st_nm")
        category = st.text_input("Category", value=v_cat, key="cat")
        email = st.text_input("Email ID", value=v_eml, key="eml")
    with col4:
        roll_no = st.text_input("Roll No.", value=v_roll, key="roll")
        f_name = st.text_input("Father Name", value=v_f_nm, key="f_nm")
        subject = st.text_input("Subject", value=v_sub, key="sub")
        address = st.text_input("Address", value=v_adr, key="adr")

    submit_button = st.form_submit_button("Save Student Data", use_container_width=True, type="primary")

if submit_button:
    if s_name.strip() == "":
        st.warning("कृपया कम से कम Student Name ज़रूर भरें।")
    else:
        new_row = {
            "Admission No.": adm_no, "Eligibility": eligibility, "Unique ID": unique_id, "Roll No.": roll_no,
            "Application No.": app_no, "Enrollment No.": enr_no, "Student Name": s_name, "Father Name": f_name,
            "Mother Name": m_name, "Date of Birth": dob, "Category": category, "Subject": subject,
            "Duration": duration, "Mobile No.": mobile, "Email ID": email, "Address": address
        }
        
        fresh_db = load_live_data()
        updated_df = pd.concat([fresh_db, pd.DataFrame([new_row])], ignore_index=True)
        
        save_live_data(updated_df)
        st.session_state.reset_trigger = True  # टाइपिंग बॉक्स खाली करें
        st.success("डेटा सफलतापूर्वक हमेशा के लिए सेव हो गया है!")
        st.rerun()
st.markdown('</div>', unsafe_allow_html=True)


# --- पासवर्ड इनपुट बॉक्स लॉजिक ---
st.markdown("---")
st.markdown('<div element-to-hide="true">', unsafe_allow_html=True)
user_password = st.text_input("🔒 नीचे का लाइव डेटाबेस देखने के लिए पासवर्ड दर्ज करें:", type="password")
st.markdown('</div>', unsafe_allow_html=True)


# गलत पासवर्ड होने पर तुरंत वार्निंग (बिना स्पेसिंग एरर वाले डायरेक्ट मोड में)
if user_password != "" and user_password != CORRECT_PASSWORD:
    st.markdown('<div element-to-hide="true">', unsafe_allow_html=True)
    st.error("❌ गलत पासवर्ड! कृपया सही पासवर्ड दर्ज करें।")
    st.markdown('</div>', unsafe_allow_html=True)


# यदि पासवर्ड बिल्कुल सही है, तो डेटाबेस और डाउनलोड सेक्शन अनलॉक करें
if user_password == CORRECT_PASSWORD:

    # --- लाइव स्टूडेंट डेटाबेस तालिका और डिलीट सिस्टम ---
    st.header("📊 Live Student Database")

    if not live_db.empty and len(live_db) > 0:
        display_df = live_db.copy().reset_index(drop=True)
        
        st.markdown('<div element-to-hide="true">', unsafe_allow_html=True)
        btn_label = "⬜ सब सेलेक्ट करें (Select All)" if not st.session_state.select_all_state else "⬛ सभी अन-सेलेक्ट करें (Deselect All)"
        if st.button(btn_label):
            st.session_state.select_all_state = not st.session_state.select_all_state
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        display_df.insert(0, "Delete स्टूडेंट", st.session_state.select_all_state)
        display_df.index = display_df.index + 1
        display_df.index.name = "S. No."

        edited_df = st.data_editor(
            display_df,
            hide_index=False,
            column_config={"Delete स्टूडेंट": st.column_config.CheckboxColumn("Delete स्टूडेंट", help="डेटा डिलीट करने के लिए टिक करें")},
            disabled=[col for col in display_df.columns if col != "Delete student" and col != "Delete स्टूडेंट"],
            use_container_width=True
        )

        selected_rows = edited_df[edited_df["Delete स्टूडेंट"] == True]

        if len(selected_rows) > 0:
            st.markdown('<div element-to-hide="true">', unsafe_allow_html=True)
            st.warning(f"आपने {len(selected_rows)} स्टूडेंट को डिलीट करने के लिए चुना है।")
            if st.button("🗑️ चयनित स्टूडेंट का डेटा डिलीट करें", type="primary"):
                indices_to_drop = [int(idx) - 1 for idx in selected_rows.index]
                
                fresh_db = load_live_data()
                updated_df = fresh_db.drop(index=indices_to_drop).reset_index(drop=True)
                
                save_live_data(updated_df)
                st.session_state.select_all_state = False  # डिलीट के बाद स्टेट रिसेट करें
                st.success("डेटा डेटाबेस और सभी डिवाइसेज से हटा दिया गया है!")
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            
    if live_db.empty or len(live_db) == 0:
        st.info("डेटाबेस अभी खाली है। नया स्टूडेंट जोड़कर शुरुआत करें।")


    # --- SECTION 5: प्रिंट और डाउनलोड विकल्प ---
    st.markdown('<div element-to-hide="true">', unsafe_allow_html=True)
    st.header("📥 Actions")
    
    csv_data = live_db.to_csv(index=False).encode('utf-8')
    st.download_button(label="Download Database as CSV", data=csv_data, file_name="student_database.csv", mime="text/csv", use_container_width=True)
        
