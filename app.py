import streamlit as st
import pandas as pd
import requests
import json

# पेज का लेआउट सेट करें (चौड़ा व्यू)
st.set_page_config(layout="wide")

# सिर्फ डेटा तालिका को प्रिंट करने के लिए स्पेशल CSS कोड (प्रिंट के समय बाकी सब छिप जाएगा)
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

st.title("Permanent Google Sheets Linked Database")

# आपका Google Script Web App URL
API_URL = "https://google.com"

DEFAULT_COLUMNS = [
    "S. No.", "Admission No.", "Eligibility", "Unique ID", "Roll No.", 
    "Application No.", "Enrollment No.", "Student Name", "Father Name",
    "Mother Name", "Date of Birth", "Category", "Subject", 
    "Duration", "Mobile No.", "Email ID", "Address"
]

# फॉर्म खाली करने के लिए विशेष ट्रिगर स्टेट
if "reset_trigger" not in st.session_state:
    st.session_state.reset_trigger = False

# गूगल शीट से हमेशा एकदम नया लाइव डेटा लोड करने का फंक्शन (सभी डिवाइस के लिए समान)
def load_live_data_from_cloud():
    try:
        response = requests.get(API_URL, timeout=12)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                headers = data
                rows = data[1:]
                if rows:
                    df = pd.DataFrame(rows, columns=headers)
                    return df.loc[:, ~df.columns.duplicated()].reset_index(drop=True)
    except:
        pass
    return pd.DataFrame(columns=DEFAULT_COLUMNS)

# गूगल शीट में डेटा भेजने का फंक्शन
def save_to_google(df_to_save):
    try:
        df_clean = df_to_save.loc[:, ~df_to_save.columns.duplicated()].reset_index(drop=True)
        headers = df_clean.columns.tolist()
        rows = df_clean.fillna("").astype(str).values.tolist()
        full_data = [headers] + rows
        
        with st.spinner("क्लाウド डेटाबेस (Google Sheets) को सभी डिवाइस के लिए अपडेट किया जा रहा है..."):
            response = requests.post(API_URL, data=json.dumps(full_data), headers={"Content-Type": "application/json"}, timeout=15)
            if response.status_code == 200:
                return True
    except Exception as e:
        st.error(f"सिंक एरर: {e}")
    return False

# हर बार पेज लोड होने पर सीधे गूगल शीट से ताजा डेटा लाएं (लोकल स्टेट पर निर्भरता खत्म)
live_db = load_live_data_from_cloud()

for col in DEFAULT_COLUMNS:
    if col not in live_db.columns:
        live_db[col] = ""

# --- सेक्शन 1: CSV फ़ाइल अपलोड ---
st.markdown('<div element-to-hide="true">', unsafe_allow_html=True)
st.header("📁 CSV File Se Bulk Data Upload Karein")
uploaded_file = st.file_uploader("CSV फ़ाइल चुनें", type=["csv"])

if uploaded_file is not None:
    try:
        uploaded_df = pd.read_csv(uploaded_file)
        uploaded_df = uploaded_df.loc[:, ~uploaded_df.columns.duplicated()].reset_index(drop=True)
        
        if st.button("Upload CSV", type="primary"):
            df_current_clean = live_db.reset_index(drop=True)
            uploaded_df_clean = uploaded_df.reset_index(drop=True)
            updated_df = pd.concat([df_current_clean, uploaded_df_clean], ignore_index=True)
            
            if save_to_google(updated_df):
                st.success("CSV डेटा सफलतापूर्वक सभी डिवाइस के लिए अपडेट कर दिया गया है!")
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
        
        # दोबारा गूगल शीट से सबसे ताजा डेटा लेकर ही नया रो जोड़ेंगे
        fresh_db = load_live_data_from_cloud()
        df_current_clean = fresh_db.reset_index(drop=True)
        updated_df = pd.concat([df_current_clean, pd.DataFrame([new_row])], ignore_index=True)
        
        if save_to_google(updated_df):
            st.session_state.reset_trigger = True  # टाइपिंग बॉक्स खाली करें
            st.success("डेटा सफलतापूर्वक जुड़ गया है और सभी डिवाइसेज पर अपडेट हो गया है!")
            st.rerun()
st.markdown('</div>', unsafe_allow_html=True)


# --- सेक्शन 3 और 4: लाइव स्टूडेंट डेटाबेस तालिका और डिलीट सिस्टम ---
st.header("📊 Live Student Database")

if st.button("🔄 तुरंत नया डेटा रीफ्रेश करें"):
    st.rerun()

if not live_db.empty and len(live_db) > 0:
    display_df = live_db.copy().reset_index(drop=True)
    display_df.insert(0, "Delete स्टूडेंट", False)
    display_df.index = display_df.index + 1
    display_df.index.name = "S. No."

    edited_df = st.data_editor(
        display_df,
        hide_index=False,
        column_config={"Delete स्टूडेंट": st.column_config.CheckboxColumn("Delete स्टूडेंट", help="डेटा डिलीट करने के लिए टिक करें", default=False)},
        disabled=[col for col in display_df.columns if col != "Delete स्टूडेंट"],
        use_container_width=True
    )

    selected_rows = edited_df[edited_df["Delete स्टूडेंट"] == True]

    if len(selected_rows) > 0:
        st.markdown('<div element-to-hide="true">', unsafe_allow_html=True)
        st.warning(f"आपने {len(selected_rows)} स्टूडेंट को डिलीट करने के लिए चुना है।")
        if st.button("🗑️ चयनित स्टूडेंट का डेटा डिलीट करें", type="primary"):
            indices_to_drop = [int(idx) - 1 for idx in selected_rows.index]
            
            # डिलीट करने से पहले बिल्कुल नया क्लाउड डेटा लें ताकि कोई क्लैश न हो
            fresh_db = load_live_data_from_cloud()
            df_current_clean = fresh_db.reset_index(drop=True)
            updated_df = df_current_clean.drop(index=indices_to_drop).reset_index(drop=True)
            
            if save_to_google(updated_df):
                st.success("डेटा हमेशा के लिए डिलीट हो गया और सभी डिवाइसेज से हट गया है!")
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("डेटाबेस अभी खाली है।")


# --- SECTION 5: प्रिंट और डाउनलोड विकल्प ---
st.markdown('<div element-to-hide="true">', unsafe_allow_html=True)
st.header("📥 Actions")
action_col1, action_col2 = st.columns(2)
with action_col1:
    csv_data = live_db.to_csv(index=False).encode('utf-8')
    st.download_button(label="Download Database as CSV", data=csv_data, file_name="student_database.csv", mime="text/csv", use_container_width=True)
