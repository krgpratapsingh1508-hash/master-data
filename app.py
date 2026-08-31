import streamlit as st
import pandas as pd
import os
import base64
import json

# पेज का लेआउट सेट करें
st.set_page_config(layout="wide")

# प्रिंट फ़ॉर्मेटिंग, लेआउट और नोटिस अलर्ट को व्यवस्थित करने के लिए सीएसएस (CSS)
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
    .notice-box {
        background-color: #FDF2F2;
        border-left: 5px solid #F05252;
        padding: 15px;
        border-radius: 4px;
        margin: 10px 0;
        color: #9B1C1C;
        font-weight: bold;
    }
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
NOTICE_FILE = "admin_notice_log.json"

# 🔒 क्रेडेंशियल्स डिफ़ॉल्ट डेटा
DEFAULT_CREDENTIALS = {
    "entry": {"password": "entry123", "role": "data_entry"},
    "viewer": {"password": "viewer123", "role": "list_viewer"},
    "foil": {"password": "foil123", "role": "cce_handler"},
    "admin": {"password": "admin123", "role": "full_admin"}
}

def load_credentials():
    if os.path.exists(CRED_FILE):
        try:
            with open(CRED_FILE, "r") as f: return json.load(f)
        except: return DEFAULT_CREDENTIALS.copy()
    else:
        with open(CRED_FILE, "w") as f: json.dump(DEFAULT_CREDENTIALS, f)
        return DEFAULT_CREDENTIALS.copy()

def save_credentials(creds):
    with open(CRED_FILE, "w") as f: json.dump(creds, f)

# 🔄 डायनेमिक कॉलम मैपिंग लोडर और सेवर
def load_column_mappings():
    if os.path.exists(MAP_FILE):
        try:
            with open(MAP_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: return {}
    return {}

def save_column_mappings(mapping_dict):
    with open(MAP_FILE, "w", encoding="utf-8") as f: json.dump(mapping_dict, f, ensure_ascii=False, indent=4)

# 📢 नोटिस लोडर और सेवर इंजन
def load_admin_notice():
    if os.path.exists(NOTICE_FILE):
        try:
            with open(NOTICE_FILE, "r", encoding="utf-8") as f: return json.load(f).get("notice", "")
        except: return ""
    return ""

def save_admin_notice(text):
    with open(NOTICE_FILE, "w", encoding="utf-8") as f: json.dump({"notice": text}, f, ensure_ascii=False, indent=4)

if "credentials" not in st.session_state: st.session_state.credentials = load_credentials()
if "column_mappings" not in st.session_state: st.session_state.column_mappings = load_column_mappings()
if "admin_notice_text" not in st.session_state: st.session_state.admin_notice_text = load_admin_notice()

# 🎯 मास्टर कॉलम्स सूची
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
            if col not in df.columns: df[col] = ""
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
if "admin_columns_order" not in st.session_state: st.session_state.admin_columns_order = DEFAULT_COLUMNS.copy()
if "admin_lock_state" not in st.session_state: st.session_state.admin_lock_state = True  
if "admin_unhide_edit" not in st.session_state: st.session_state.admin_unhide_edit = False
if "admin_unhide_move" not in st.session_state: st.session_state.admin_unhide_move = False
if "cce_foil_generated" not in st.session_state: st.session_state.cce_foil_generated = False
if "cce_sub" not in st.session_state: st.session_state.cce_sub = "All Subjects"

# 🛠️ सुरक्षा नियंत्रण वेरिएबल्स का नया नामकरण (5-Layer Naming Alignment)
if "lock_panel_1" not in st.session_state: st.session_state.lock_panel_1 = False
if "lock_panel_2" not in st.session_state: st.session_state.lock_panel_2 = False
if "lock_panel_3" not in st.session_state: st.session_state.lock_panel_3 = False
if "lock_panel_4" not in st.session_state: st.session_state.lock_panel_4 = False
if "lock_panel_5" not in st.session_state: st.session_state.lock_panel_5 = False # Admin self-lock filter backup
if "admin_hide_viewer" not in st.session_state: st.session_state.admin_hide_viewer = False
if "admin_hide_cred_panel" not in st.session_state: st.session_state.admin_hide_cred_panel = False

# मास्टर लेयर स्टेट कंट्रोलर्स
if "master_lock_original_four" not in st.session_state: st.session_state.master_lock_original_four = True  
if "master_hide_triple_lock_system" not in st.session_state: st.session_state.master_hide_triple_lock_system = False
if "master_hide_notice_manager" not in st.session_state: st.session_state.master_hide_notice_manager = True

live_db = load_live_data()

def get_display_name(internal_col_name):
    return st.session_state.column_mappings.get(internal_col_name, internal_col_name)

# 🛠️ सुरक्षा डिस्प्ले अलर्ट हेल्पर (Locked Panels Notice)
def show_panel_notice_if_locked(panel_title):
    st.header(panel_title)
    if st.session_state.admin_notice_text:
        st.markdown(f'<div class="notice-box">📢 NOTICE BY ADMIN: {st.session_state.admin_notice_text}</div>', unsafe_allow_html=True)
    else:
        st.error("🔒 यह पैनल वर्तमान में मुख्य व्यवस्थापक (Admin) द्वारा लॉक किया गया है।")
    st.markdown("---")

# ==========================================================
# 🔒 सिक्योर लॉगिन गेटवे (स्क्रॉल सिस्टम इनेबल्ड)
# ==========================================================
if st.session_state.user_role is None:
    st.markdown("---")
    st.subheader("🔒 Multi-User Secure Login Gateway")
    
    user_input = st.selectbox("Username (भूमिका) चुनें:", options=list(st.session_state.credentials.keys()))
    password_input = st.text_input("Password दर्ज करें:", type="password")
    
    if st.button("Secure Login", use_container_width=True, type="primary"):
        if user_input in st.session_state.credentials and st.session_state.credentials[user_input]["password"] == password_input:
            st.session_state.user_role = st.session_state.credentials[user_input]["role"]
            st.success("✅ लॉगिन सफल!")
            st.rerun()
        else:
            st.error("❌ गलत पासवर्ड दर्ज किया गया है!")

else:
    st.markdown('<div class="print-hide">', unsafe_allow_html=True)
    if st.button("🔒 मुख्य लॉगआउट (Exit Secure System)", type="primary", use_container_width=True):
        st.session_state.user_role = None
        st.session_state.cce_foil_generated = False
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    role = st.session_state.user_role
    st.info(f"🔑 वर्तमान सत्र भूमिका: **{role.upper()}**")
    st.markdown("---")

      # ----------------------------------------------------------------------
    # 📝 PANEL 1: ENTRY PANEL - (Student Data Entry Logic)
    # ----------------------------------------------------------------------
    if role in ["data_entry", "full_admin"]:
        # यदि एडमिन ने पैनल 1 को लॉक (Hide Lock) किया है, तो लाइव नोटिस अलर्ट दिखेगा
        if st.session_state.lock_panel_1:
            show_panel_notice_if_locked("📝 Panel 1: Entry Panel")
        else:
            st.header("📝 Panel 1: Entry Panel")
            entry_method = st.selectbox(
                "⚙️ डेटा एंट्री का माध्यम चुनें:",
                options=["📁 CSV फ़ाइल बल्क अपलोड (Bulk CSV Upload)", "➕ नया छात्र मैनुअल फॉर्म (Manual Form Entry)"]
            )
            
            # माध्यम 1: बल्क सीएसवी अपलोड इंजन
            if entry_method == "📁 CSV फ़ाइल बल्क अपलोड (Bulk CSV Upload)":
                uploaded_file = st.file_uploader("CSV फ़ाइल चुनें", type=["csv"], key="panel1_bulk_csv")
                if uploaded_file is not None and st.button("Upload CSV Now", type="primary", key="panel1_bulk_btn"):
                    try:
                        uploaded_df = pd.read_csv(uploaded_file, dtype=str).fillna("")
                        for col in DEFAULT_COLUMNS:
                            if col not in uploaded_df.columns: 
                                uploaded_df[col] = ""
                        cleaned_uploaded_df = uploaded_df[DEFAULT_COLUMNS].copy()
                        updated_df = pd.concat([load_live_data(), cleaned_uploaded_df], ignore_index=True)
                        save_live_data(updated_df)
                        st.success("✅ CSV डेटा सफलतापूर्वक अपलोड हो गया!")
                        st.rerun()
                    except Exception as e: 
                        st.error(f"त्रुटि: {e}")

            # माध्यम 2: सिक्योर मैनुअल फॉर्म एंट्री मैट्रिक्स
            elif entry_method == "➕ नया छात्र मैनुअल फॉर्म (Manual Form Entry)":
                with st.form(key="student_add_form_panel1", clear_on_submit=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        admission_year = st.text_input(get_display_name("Admission Year"))
                        eligibility_name = st.text_input(get_display_name("Eligibility Name"))
                        admission_date = st.text_input(get_display_name("Admission Date"))
                        roll_no = st.text_input(get_display_name("Roll No."))
                        enrollment_no = st.text_input(get_display_name("Enrollment No."))
                        f_name = st.text_input(get_display_name("Father Name"))
                        dob = st.text_input(get_display_name("Date of Birth"))
                        subject_code = st.text_input(get_display_name("Subject Code"))
                        subject = st.text_input(get_display_name("Subject"))
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
                        status_input = st.selectbox(get_display_name("Status"), ["Regular Student", "Regular", "Pending", "Pass", "EX-STUDENT"])
                    
                    submit_student = st.form_submit_button("Save Student Data", type="primary")

                # डेटाबेस कमिट लॉजिक इंजन
                if submit_student:
                    if s_name.strip() == "": 
                        st.warning("Student Name भरना आवश्यक है।")
                    else:
                        new_row = {
                            "Admission Year": admission_year, "Admission Session": admission_session, "Eligibility Name": eligibility_name,
                            "Admission Application Number": admission_app_no, "Admission Date": admission_date, "Unique ID": unique_id,
                            "Roll No.": roll_no, "Application Enrollment No.": app_enroll_no, "Enrollment No.": enrollment_no,
                            "Student Name": s_name, "Father Name": f_name, "Mother Name": m_name, "Date of Birth": dob,
                            "Category": category, "Subject Code": subject_code, "Subject": subject, "Duration": duration,
                            "Mobile Number": mobile, "Email ID": email, "Address": address, "Status": status_input, "Current Year": ""
                        }
                        updated_df = pd.concat([load_live_data(), pd.DataFrame([new_row])], ignore_index=True)
                        save_live_data(updated_df)
                        st.success("✅ डेटा सुरक्षित सेव हुआ!")
                        st.rerun()
            st.markdown("---")

    # ----------------------------------------------------------------------
    # 🎓 PANEL 2: ADMISSION PANEL - (4-Step Comprehensive Pipeline)
    # ----------------------------------------------------------------------
    if role in ["full_admin"]:
        # यदि एडमिन ने पैनल 2 को लॉक (Hide Lock) किया है, तो लाइव नोटिस अलर्ट दिखेगा
        if st.session_state.lock_panel_2:
            show_panel_notice_if_locked("🎓 Panel 2: Admission Panel")
        else:
            st.header("🎓 Panel 2: Admission Panel")
            st.info("🎯 नए सत्र की प्रवेश प्रक्रिया प्रबंधन एवं एडवांस्ड डेटा मिलान तंत्र")
            
            # ==============================================================
            # 1️⃣ STEP 1: मैन्युअल छात्र एंट्री टेक्स्ट बॉक्स (Manual Entry Box)
            # ==============================================================
            st.subheader("1️⃣ मैन्युअल छात्र पंजीकरण फॉर्म (Manual Entry Box)")
            with st.form(key="admission_manual_entry_form_p2", clear_on_submit=True):
                col_adm1, col_adm2 = st.columns(2)
                with col_adm1:
                    adm_app = st.text_input("Admission Application Number (आवेदन क्रमांक)*")
                    adm_name = st.text_input("Student Name (छात्र का नाम)*")
                    adm_sub = st.text_input("Subject (विषय/कोर्स)")
                with col_adm2:
                    adm_yr = st.text_input("Admission Year (प्रवेश वर्ष)", value="2026")
                    adm_sess = st.text_input("Admission Session (सत्र)", value="2026-27")
                    adm_stat = st.selectbox("Status (स्थिति)", ["Pending", "Regular", "Pass"])
                
                submit_adm_manual = st.form_submit_button("➕ मास्टर सूची में जोड़ें", type="primary")
                
            if submit_adm_manual:
                if adm_app.strip() == "" or adm_name.strip() == "":
                    st.error("❌ Application Number और Student Name भरना अनिवार्य है।")
                else:
                    new_r = {col: "" for col in DEFAULT_COLUMNS}
                    new_r["Admission Application Number"] = adm_app.strip()
                    new_r["Student Name"] = adm_name.strip()
                    new_r["Subject"] = adm_sub.strip()
                    new_r["Admission Year"] = adm_yr.strip()
                    new_r["Admission Session"] = adm_sess.strip()
                    new_r["Status"] = adm_stat
                    
                    updated_db = pd.concat([load_live_data(), pd.DataFrame([new_r])], ignore_index=True)
                    save_live_data(updated_db)
                    st.success("✅ छात्र का डेटा सफलतापूर्वक मास्टर सूची में दर्ज कर लिया गया है!")
                    st.rerun()

            st.markdown("---")

            # ==============================================================
            # 2️⃣ STEP 2: बल्क एडमिशन फाइल अपलोडर (Upload File)
            # ==============================================================
            st.subheader("2️⃣ बल्क एडमिशन CSV फ़ाइल अपलोडर (Upload File)")
            uploaded_adm = st.file_uploader("प्रवेशित छात्रों की मूल CSV फ़ाइल यहाँ अपलोड करें:", type=["csv"], key="adm_bulk_p2")
            
            if uploaded_adm is not None:
                if st.button("📁 मूल फ़ाइल डेटाबेस में सिंक करें", key="sync_bulk_p2_btn"):
                    try:
                        up_df = pd.read_csv(uploaded_adm, dtype=str).fillna("")
                        for c in DEFAULT_COLUMNS:
                            if c not in up_df.columns:
                                up_df[c] = ""
                        cleaned_uploaded_df = up_df[DEFAULT_COLUMNS].copy()
                        updated_db = pd.concat([load_live_data(), cleaned_uploaded_df], ignore_index=True)
                        save_live_data(updated_db)
                        st.success(f"✅ सफल! {len(cleaned_uploaded_df)} छात्रों का रिकॉर्ड मास्टर डेटाबेस में जोड़ा गया।")
                        st.rerun()
                    except Exception as e:
                        st.error(f"⚠️ फ़ाइल प्रोसेसिंग त्रुटि: {e}")

            st.markdown("---")

            # ==============================================================
            # 3️⃣ STEP 3: लाइव एडमिशन ग्रिड सूची (Display List View)
            # ==============================================================
            st.subheader("3️⃣ लाइव प्रवेशित छात्र डेटाबेस सूची (Display List)")
            current_live_db = load_live_data()
            
            if not current_live_db.empty:
                disp_df = current_live_db.copy()
                disp_df = disp_df.rename(columns={c: get_display_name(c) for c in disp_df.columns})
                disp_df.insert(0, "S.No.", range(1, len(disp_df) + 1))
                st.dataframe(disp_df, use_container_width=True, hide_index=True)
            else:
                st.warning("⚠️ वर्तमान में लाइव छात्र डेटाबेस सूची पूरी तरह खाली है।")

            st.markdown("---")

            # ==============================================================
            # 4️⃣ STEP 4: एडवांस्ड 2nd लिस्ट डेटा मिलान एवं खाली बॉक्स फिलर इंजन
            # ==============================================================
            st.subheader("4️⃣ एडवांस्ड द्वितीय (2nd) फ़ाइल मिलान एवं खाली स्थान पूरक यंत्र")
            sec_file = st.file_uploader("🔍 मिलान करने के लिए द्वितीय (2nd) CSV फ़ाइल चुनें:", type=["csv"], key="adm_sec_p2")
            
            if sec_file is not None and not current_live_db.empty:
                try:
                    sec_df = pd.read_csv(sec_file, dtype=str).fillna("")
                    
                    c_m1, c_m2, c_m3 = st.columns(3)
                    with c_m1:
                        m_key = st.selectbox("🔗 मास्टर सूची का मिलान कॉलम (ID) चुनें:", options=DEFAULT_COLUMNS, index=3, key="m_key_p2")
                    with c_m2:
                        s_key = st.selectbox("🎯 2nd फ़ाइल का मिलान कॉलम (ID) चुनें:", options=list(sec_df.columns), key="s_key_p2")
                    with c_m3:
                        target_update_col = st.selectbox("✏️ 2nd फ़ाइल से कौन सा कॉलम खाली जगह में भरना है?", options=DEFAULT_COLUMNS, index=6, key="target_col_p2")

                    if st.button("⚡ मिलान प्रक्रिया शुरू करें", type="primary", key="start_cross_match_p2_btn"):
                        m_df = current_live_db.copy()
                        sec_map = dict(zip(sec_df[s_key].astype(str).str.strip(), sec_df[target_update_col].astype(str).str.strip()))
                        succ = 0
                        
                        for idx, row in m_df.iterrows():
                            val = str(row.get(m_key, '')).strip()
                            t_val = str(row.get(target_update_col, '')).strip()
                            
                            # यदि मास्टर लिस्ट में वह कॉलम खाली या 'nan' है, और 2nd फाइल में डेटा है, तभी भरें
                            if t_val in ["", "nan"] and val in sec_map and sec_map[val]:
                                m_df.at[idx, target_update_col] = sec_map[val]
                                succ += 1
                                
                        if succ > 0:
                            save_live_data(m_df)
                            st.success(f"🎉 सफल! कुल **{succ}** खाली रोज़ (Rows) का मिलान सफल रहा और उनका '{target_update_col}' डेटा ऑटो-अपडेट कर दिया गया है।")
                            st.rerun()
                        else:
                            st.warning("⚠️ मिलान समाप्त! कोई भी ऐसा नया डेटा नहीं मिला जो मास्टर लिस्ट के खाली बॉक्स में भरा जा सके।")
                except Exception as e:
                    st.error(f"❌ डेटा मिलान इंजन में खराबी: {e}")
            elif sec_file is not None and current_live_db.empty:
                st.error("❌ मिलान प्रक्रिया शुरू करने के लिए मास्टर डेटाबेस में पहले से डेटा होना अनिवार्य है।")
                
            st.markdown("---")

    # ----------------------------------------------------------------------
    # 📊 PANEL 3: CCE REPORT PANEL - (Foil Data Stream Integrated)
    # ----------------------------------------------------------------------
    if role in ["full_admin"]:
        # यदि एडमिन ने पैनल 3 को लॉक (Hide Lock) किया है, तो लाइव नोटिस अलर्ट दिखेगा
        if st.session_state.lock_panel_3:
            show_panel_notice_if_locked("📊 Panel 3: CCE Report Panel")
        else:
            st.header("📊 Panel 3: CCE Report Panel")
            st.info("📊 छात्र आंतरिक मूल्यांकन एवं फॉइल शीट (Foil Sheet Records) लाइव सिंक ग्रिड")
            
            # 1. मास्टर डेटाबेस का व्यू लोड करें
            st.subheader("📋 मास्टर इवैल्यूएशन लॉग (Master Evaluation Log)")
            current_live_db = load_live_data()
            
            if not current_live_db.empty:
                cce_record_view = current_live_db[["Unique ID", "Roll No.", "Student Name", "Subject Code", "Subject", "Status"]].copy()
                cce_record_view = cce_record_view.rename(columns={c: get_display_name(c) for c in cce_record_view.columns})
                cce_record_view.insert(0, "S.No.", range(1, len(cce_record_view) + 1))
                st.dataframe(cce_record_view, use_container_width=True, hide_index=True)
            else:
                st.warning("मास्टर मूल्यांकन डेटाबेस अभी खाली है।")
                
            st.markdown("---")
            
            # 2. ⚡ फ़ीचर: फॉइल पैनल (Panel 4) के फिल्टर किए गए डेटा को यहाँ भी प्रदर्शित करना
            st.subheader("🖨️ फॉइल शीट प्रोसेसिंग डेटा स्ट्रीम (Foil Panel Live Stream)")
            
            # चेक करें कि क्या फॉइल पैनल पर यूज़र ने 'Generate Foil Sheets Now' बटन दबाया है और डेटा मौजूद है
            if st.session_state.get("cce_foil_generated", False) and not current_live_db.empty:
                st.success("✅ फॉइल इंजन से लाइव डेटा सफलतापूर्वक प्राप्त हुआ। वर्तमान सत्र की एलिजिबल रोल नंबर सूची नीचे प्रदर्शित है:")
                
                # फॉइल प्रोसेसिंग इंजन के लॉजिक को बैकएंड पर चलाकर सीधे ग्रिड सिंक करना
                foil_stream_db = current_live_db.copy()
                
                # फॉइल पैनल पर चुने गए विषय (Subject) के आधार पर फ़िल्टर करें
                selected_sub_stream = st.session_state.get("cce_sub", "All Subjects")
                if selected_sub_stream != "All Subjects":
                    foil_stream_db = foil_stream_db[foil_stream_db['Subject'].str.strip() == selected_sub_stream]
                
                # केवल रोल नंबर और विषय की प्रासंगिक जानकारी ग्रिड में प्रस्तुत करें
                foil_render_stream = foil_stream_db[["Roll No.", "Student Name", "Subject Code", "Subject", "Status", "Current Year"]].copy()
                foil_render_stream = foil_render_stream.rename(columns={c: get_display_name(c) for c in foil_render_stream.columns})
                foil_render_stream.insert(0, "Foil S.No.", range(1, len(foil_render_stream) + 1))
                
                # फॉइल का हुक डेटा रेंडर करें
                st.dataframe(foil_render_stream, use_container_width=True, hide_index=True)
            else:
                st.info("💡 सूचना: जब फॉइल पैनल (Panel 4) पर जाकर छात्र सूची जनरेट की जाएगी, तब उस विशिष्ट विषय की अंतिम फॉइल डेटा शीट ऑटोमैटिकली यहाँ भी सिंक होकर दिखने लगेगी।")
            
            st.markdown("---")

    # ----------------------------------------------------------------------
    # 🖨️ PANEL 4: FOIL PANEL - (Foil Sheet Generator Logic)
    # ----------------------------------------------------------------------
    if role in ["cce_handler", "full_admin"]:
        # यदि एडमिन ने पैनल 4 को लॉक (Hide Lock) किया है, तो लाइव नोटिस अलर्ट दिखेगा
        if st.session_state.lock_panel_4:
            show_panel_notice_if_locked("🖨️ Panel 4: Foil Panel")
        else:
            st.header("🖨️ Panel 4: Foil Panel")
            st.write("Institute of Law, Govt. Kamlaraja Girls Post-Graduate Autonomous College, Gwalior (M.P.)")
            college_name = "GOVT. K.R.G. POST-GRADUATE AUTONOMOUS COLLEGE, GWALIOR (M.P.)"

            if not live_db.empty:
                unique_subjects = sorted(list(set(live_db['Subject'].dropna().astype(str).str.strip())))
                unique_subjects = [sub for sub in unique_subjects if sub != ""]
                selected_subject = st.selectbox("📚 Select Subject (विषय चुनें):", options=["All Subjects"] + unique_subjects, key="cce_sub_input")
                st.session_state.cce_sub = selected_subject

                year_sem_options = [
                    "1 Semester", "2 Semester", "3 Semester", "4 Semester", "5 Semester", "6 Semester",
                    "7 Semester", "8 Semester", "9 Semester", "10 Semester", "11 Semester", "12 Semester",
                    "1 year", "2 year", "3 year", "4 year", "5 year", "6 year"
                ]
                
                def on_cce_param_change(): 
                    st.session_state.cce_foil_generated = False
                
                chosen_option = st.selectbox("📆 Select Semester / Year:", year_sem_options, key="cce_year_sem", on_change=on_cce_param_change)

                mapping_logic = {
                    "1 Semester": "1 year", "2 Semester": "1 year", "1 year": "1 year",
                    "3 Semester": "2 year", "4 Semester": "2 year", "2 year": "2 year",
                    "5 Semester": "3 year", "6 Semester": "3 year", "3 year": "3 year",
                    "7 Semester": "4 year", "8 Semester": "4 year", "4 year": "4 year",
                    "9 Semester": "5 year", "10 Semester": "5 year", "5 year": "5 year",
                    "11 Semester": "6 year", "12 Semester": "6 year", "6 year": "6 year"
                }
                target_year_text = mapping_logic[chosen_option]
                display_subject_heading = selected_subject.upper() if selected_subject != "All Subjects" else "STUDENT LIST"
                exam_info = f"Examination :- CCE                                             {display_subject_heading} {chosen_option.upper()}"

                st.write("📊 Foil Processing Student Grid View:")
                preview_db = live_db.copy()
                if selected_subject != "All Subjects":
                    preview_db = preview_db[preview_db['Subject'].str.strip() == selected_subject]
                
                preview_render = preview_db[["Roll No.", "Student Name", "Subject Code", "Subject", "Status", "Current Year"]].copy()
                preview_render = preview_render.rename(columns={c: get_display_name(c) for c in preview_render.columns})
                st.dataframe(preview_render, use_container_width=True, hide_index=True)

                if st.button("Generate Foil Sheets Now", use_container_width=True, type="primary", key="gen_foil_p4_btn"):
                    st.session_state.cce_foil_generated = True
                    st.rerun()

                if st.session_state.cce_foil_generated:
                    regular_records = []
                    ex_student_records = []
                    has_missing_roll_and_is_first_year_regular = False 
                    detected_subject_code = ""
                    years_series = pd.to_numeric(live_db["Admission Year"], errors='coerce')
                    max_year = int(years_series.max()) if not years_series.dropna().empty else 2026

                    for _, row in live_db.iterrows():
                        roll = str(row.get('Roll No.', '')).strip()
                        name = str(row.get('Student Name', '')).strip()
                        status = str(row.get('Status', '')).strip().upper()
                        current_year_val = str(row.get('Current Year', '')).strip().lower()
                        student_sub = str(row.get('Subject', '')).strip()
                        sub_code = str(row.get('Subject Code', '')).strip()
                        try: adm_year = int(float(str(row.get('Admission Year', '0'))))
                        except: adm_year = 0
                        try: course_duration = int(float(str(row.get('Duration', '6'))))
                        except: course_duration = 6

                        if selected_subject != "All Subjects" and student_sub != selected_subject: continue
                        if sub_code and sub_code.lower() != "nan" and detected_subject_code == "": detected_subject_code = sub_code

                        if status == "EX-STUDENT":
                            is_ex_match = False
                            try: gap_needed = int(target_year_text.split()[0])
                            except: gap_needed = 1
                            if gap_needed <= course_duration and adm_year == (max_year - gap_needed): is_ex_match = True
                            if is_ex_match and roll and roll.lower() != "nan" and roll != "": ex_student_records.append(roll)
                            continue

                        if status in ['REGULAR STUDENT', 'REGULAR']:
                            is_regular_year_match = False
                            clean_target_text = target_year_text.strip().lower()
                            if clean_target_text in current_year_val or current_year_val in clean_target_text: is_regular_year_match = True
                            elif current_year_val in ["", "ex-student", "nan"]:
                                calculated_gap = max_year - adm_year
                                if clean_target_text == "1 year" and calculated_gap == 0: is_regular_year_match = True
                                elif clean_target_text == "2 year" and calculated_gap == 1: is_regular_year_match = True
                                elif clean_target_text == "3 year" and calculated_gap == 2: is_regular_year_match = True

                            if is_regular_year_match:
                                if clean_target_text == "1 year" and (not roll or roll.lower() == "nan" or roll == ""):
                                    has_missing_roll_and_is_first_year_regular = True
                                    regular_records.append(name if name else "[Unknown Name]")
                                else:
                                    if roll and roll.lower() != "nan" and roll != "": regular_records.append(roll)

                    final_records_list = sorted(list(set(ex_student_records))) + sorted(list(set(regular_records)))

                    st.markdown("---")
                    st.subheader("⚙️ Processing Engine (Validating Student Eligibility)")
                    col_m1, col_m2, col_m3 = st.columns(3)
                    with col_m1: st.metric("Valid Ex-Students (Prioritized)", len(ex_student_records))
                    with col_m2: st.metric("Valid Regular Students", len(regular_records))
                    with col_m3: st.metric("Total Records Captured", len(final_records_list))

                    if final_records_list:
                        st.subheader("🖨️ Generated Visual Foil Sheets")
                        dynamic_th_label = "Roll No. / Student Name" if has_missing_roll_and_is_first_year_regular else "Roll No."

                        def generate_cce_html_block(items, start_idx, foil_label):
                            paper_code_display = f"Paper Code: <b>{detected_subject_code}</b>" if detected_subject_code else "Paper Code...................."
                            block = f"""
                            <div class="foil-unit">
                                <div class="top-fields"><div></div><div>{paper_code_display}</div></div>
                                <div class="top-fields" style="margin-top: 5px;"><div></div><div>Bundle No....................</div></div>
                                <div class="header-box">{college_name}</div>
                                <div class="sub-box exam-right">{exam_info}</div>
                                <div class="sub-box">Subject: {selected_subject if selected_subject != 'All Subjects' else '......................'} Paper.........................</div>
                                <div class="marks-info"><div>Max. Marks: ...................</div><div>Min. Pass Marks: ...................</div></div>
                                <div class="foil-title">{foil_label}</div>
                                <table style="width:100%; border-collapse:collapse; margin-top:10px;">
                                    <tr><th style="border:1px solid black; padding:4px; width: 8%;">1</th><th style="border:1px solid black; padding:4px; width: 30%;" colspan="3">2</th></tr>
                                    <tr><th style="border:1px solid black; padding:4px;" rowspan="2">Code No.</th><th style="border:1px solid black; padding:4px;" rowspan="2">{dynamic_th_label}</th><th style="border:1px solid black; padding:4px;" colspan="2">Marks Obtained</th></tr>
                               <tr><th style="border:1px solid black; padding:4px; width: 15%;">In Figures</th><th style="border:1px solid black; padding:4px; width: 45%;">In Words</th></tr>
                            """
                                                    # 1. डेटाबेस से प्राप्त वैध छात्र रिकॉर्ड्स को पंक्तियों (Rows) में जोड़ना
                        for idx_foil, item_val in enumerate(items, start=start_idx):
                            block += f"<tr><td style='border:1px solid black; padding:4px;'><b>{idx_foil}</b></td><td style='border:1px solid black; padding:4px;'>{item_val}</td><td style='border:1px solid black; padding:4px;'></td><td style='border:1px solid black; padding:4px;'></td></tr>"
                        
                        # 2. यदि छात्र 35 से कम हैं, तो फ़ॉर्मेट को बराबर रखने के लिए बची हुई खाली पंक्तियाँ (Blank Rows) जोड़ना
                        for k in range(len(items) + start_idx, 35 + start_idx):
                            block += "<tr><td style='border:1px solid black; padding:4px;'>&nbsp;</td><td style='border:1px solid black; padding:4px;'>&nbsp;</td><td style='border:1px solid black; padding:4px;'>&nbsp;</td><td style='border:1px solid black; padding:4px;'>&nbsp;</td></tr>"
                        
                        # 3. फ़ॉइल ब्लॉक के फुटर और परीक्षक के हस्ताक्षर क्षेत्र का संयोजन
                        block += f"""</table><div class="note" style="font-size:10px; margin-top:10px;"><b>Note:</b> Roll Number and Marks awarded carefully. legible and no mistake remains.</div><div class="footer-fields">Signature of Examiner......................................<br>Date: ___/___/2026</div></div>"""
                        return block

                    # 4. असीमित सब-ब्लॉक डिकम्प्रेशन और चंकिंग इंजन (35-35 रिकॉर्ड्स का विभाजन)
                    html_blocks_compiled = ""
                    chunk_size = 35
                    chunks = [final_records_list[i:i + chunk_size] for i in range(0, len(final_records_list), chunk_size)]
                    for index, chunk_data in enumerate(chunks):
                        start_num = (index * chunk_size) + 1
                        if index % 2 == 0: html_blocks_compiled += '<div class="foil-row-wrapper">'
                        html_blocks_compiled += generate_cce_html_block(chunk_data, start_num, f"FOIL - PAGE {index+1}")
                        if index % 2 == 1 or index == len(chunks) - 1:
                            if index % 2 == 0 and index == len(chunks) - 1:
                                html_blocks_compiled += '<div class="foil-unit" style="border:none; background:transparent;"></div>'
                            html_blocks_compiled += '</div>'

                    # 5. डायनेमिक रिस्पॉन्सिव स्टाइल और प्रिंट मीडिया मार्जिन सेटिंग्स
                    html_style = """<style>.foil-row-wrapper { display: flex; justify-content: space-between; gap: 20px; width: 1100px; margin: 0 auto 30px auto; background: white; page-break-after: always; }.foil-unit { width: 49%; border: 1px solid black; padding: 12px; box-sizing: border-box; background: white; }.top-fields { display: flex; justify-content: space-between; font-weight: bold; font-size: 13px; }.header-box { text-align: center; border-top: 2px solid black; border-bottom: 2px solid black; padding: 6px 0; margin-top: 8px; font-weight: bold; font-size: 16px; }.sub-box { border-bottom: 2px solid black; padding: 5px 0; font-size: 12px; font-weight: bold; }.exam-right { text-align: right; }.marks-info { display: flex; justify-content: space-between; padding: 5px 0; font-weight: bold; border-bottom: 2px solid black; font-size: 12px; }.foil-title { text-align: center; font-weight: bold; font-size: 16px; margin: 10px 0; }.footer-fields { margin-top: 15px; font-size: 12px; font-weight: bold; }@media print { .print-hide { display: none !important; } }</style>"""
                    
                    # 6. html2canvas स्क्रिप्ट के साथ मल्टी-पेज पीएनजी एक्सपोर्टर इंजन
                    full_html = f"""<html><head>{html_style}<script src="https://cloudflare.com"></script><script>function downloadAllFoilsAsPNG() {{ const elements = document.getElementsByClassName("foil-row-wrapper"); for(let i=0; i<elements.length; i++) {{ html2canvas(elements[i], {{ scale: 2 }}).then(canvas => {{ let link = document.createElement("a"); link.download = "foil_sheet_page_" + (i+1) + ".png"; link.href = canvas.toDataURL("image/png"); link.click(); }}); }} }}</script></head><body><div class="print-hide" style="text-align: center; margin-bottom: 15px; display:flex; gap:20px; justify-content:center;"><button onclick="window.print()" style="background:#FF5733; color:white; border:none; padding:10px 20px; border-radius:5px; cursor:pointer; font-weight:bold;">Direct Print All Sheets</button><button onclick="downloadAllFoilsAsPNG()" style="background:#4CAF50; color:white; border:none; padding:10px 20px; border-radius:5px; cursor:pointer; font-weight:bold;">Download All Pages in PNG</button></div><div id="master-container">{html_blocks_compiled}</div></body></html>"""
                    st.components.v1.html(full_html, height=1600, scrolling=True)
                else:
                    st.error("कोई छात्र रिकॉर्ड नहीं मिला।")
        st.markdown("---")

    # ----------------------------------------------------------------------
    # 🛠️ PANEL 5: ADMIN PANEL - (Notice & 5-Layer Security System)
    # ----------------------------------------------------------------------
    if role == "full_admin":
        st.header("🛠️ Panel 5: Admin Panel")
        st.subheader("🛡️ Global Panels Visibility Controller")
        
        # 🟢 मुख्य 3 मास्टर बटन्स ग्रिड (3 Main Master Buttons Grid)
        col_master1, col_master2, col_master3 = st.columns(3)
        
        with col_master1:
            lbl_btn1 = "A) 🔓 Global Buttons: UNLOCKED" if not st.session_state.master_lock_original_four else "A) 🔒 Global Buttons: LOCKED"
            if st.button(lbl_btn1, use_container_width=True, key="m_btn_lock_1_p5"):
                st.session_state.master_lock_original_four = not st.session_state.master_lock_original_four
                st.rerun()
                
        with col_master2:
            lbl_btn2 = "B) 👁️ 5-Layer Secure Panel: SHOW" if st.session_state.master_hide_triple_lock_system else "B) 🔒 5-Layer Secure Panel: HIDE"
            if st.button(lbl_btn2, use_container_width=True, key="m_btn_lock_2_p5"):
                st.session_state.master_hide_triple_lock_system = not st.session_state.master_hide_triple_lock_system
                st.rerun()

        with col_master3:
            # 📢 तीसरा मास्टर बटन: जो एडमिन नोटिस क्रिएटर फ़ॉर्म को हाइड/अनहाइड करता है
            lbl_btn3 = "C) 👁️ Notice Panel Control: SHOW" if st.session_state.master_hide_notice_manager else "C) 🔒 Notice Panel Control: HIDE"
            if st.button(lbl_btn3, use_container_width=True, key="m_btn_lock_3_p5"):
                st.session_state.master_hide_notice_manager = not st.session_state.master_hide_notice_manager
                st.rerun()

        # ------------------------------------------------------------------
        # 📢 मास्टर बटन C कंपोनेंट: लाइव नोटिस एडिटर और सेवर लॉजिक (Save & Lock)
        # ------------------------------------------------------------------
        if not st.session_state.master_hide_notice_manager or st.session_state.admin_notice_text != "":
            st.subheader("📢 Broadcast System (Lock Security Notices)")
            with st.form(key="admin_live_notice_form_p5"):
                typed_notice = st.text_area("लॉक पैनल्स पर प्रदर्शित करने हेतु सूचना टाइप करें:", value=st.session_state.admin_notice_text)
                col_n1, col_n2 = st.columns(2)
                with col_n1:
                    save_notice_btn = st.form_submit_button("💾 Save & Lock Notice Text", type="primary", use_container_width=True)
                with col_n2:
                    clear_notice_btn = st.form_submit_button("🗑️ Clear Notice Text", use_container_width=True)

            if save_notice_btn:
                st.session_state.admin_notice_text = typed_notice
                save_admin_notice(typed_notice)
                st.success("✅ नोटिस लॉक व क्लाउड पर सुरक्षित सेव हुआ!")
                st.rerun()

            if clear_notice_btn:
                st.session_state.admin_notice_text = ""
                save_admin_notice("")
                st.success("🗑️ नोटिस सफलतापूर्वक क्लियर कर दिया गया है!")
                st.rerun()

        # ------------------------------------------------------------------
        # 🔘 मास्टर बटन A कंपोनेंट: व्यक्तिगत कस्टमाइज़ेशन बटन्स
        # ------------------------------------------------------------------
        if not st.session_state.master_lock_original_four:
            st.info("🔓 व्यक्तिगत कस्टमाइज़ेशन बटन्स सक्रिय हैं:")
            col_vis1, col_vis2, col_vis3, col_vis4 = st.columns(4)
            with col_vis1:
                if st.button("Panel 1 (Entry): Toggle", use_container_width=True, key="t_btn1_p5"):
                    st.session_state.lock_panel_1 = not st.session_state.lock_panel_1
                    st.rerun()
            with col_vis2:
                if st.button("Viewer Panel: Toggle", use_container_width=True, key="t_btn2_p5"):
                    st.session_state.admin_hide_viewer = not st.session_state.admin_hide_viewer
                    st.rerun()
            with col_vis3:
                if st.button("Panel 4 (Foil): Toggle", use_container_width=True, key="t_btn3_p5"):
                    st.session_state.lock_panel_4 = not st.session_state.lock_panel_4
                    st.rerun()
            with col_vis4:
                if st.button("👁️ Passwords Panel: Toggle", use_container_width=True, key="t_btn4_p5"):
                    st.session_state.admin_hide_cred_panel = not st.session_state.admin_hide_cred_panel
                    st.rerun()

        # ------------------------------------------------------------------
        # 🔒 मास्टर बटन B कंपोनेंट: (5-Layer Naming Logic Filters Grid)
        # ------------------------------------------------------------------
        if not st.session_state.master_hide_triple_lock_system:
            st.markdown("##### 🔒 Secure 5-Layer Password-Group Lock / Unlock Filters")
            col_l1, col_l2, col_l3, col_l4, col_l5 = st.columns(5)
            
            with col_l1:
                l1_lbl = "Panel 1 (Entry) 🔓" if not st.session_state.lock_panel_1 else "Panel 1 (Entry) 🔒"
                if st.button(l1_lbl, use_container_width=True, key="l_p1_btn"):
                    st.session_state.lock_panel_1 = not st.session_state.lock_panel_1
                    st.rerun()
            with col_l2:
                l2_lbl = "Viewer Panel 🔓" if not st.session_state.admin_hide_viewer else "Viewer Panel 🔒"
                if st.button(l2_lbl, use_container_width=True, key="l_view_btn"):
                    st.session_state.admin_hide_viewer = not st.session_state.admin_hide_viewer
                    st.rerun()
            with col_l3:
                l3_lbl = "Panel 2 (Admission) 🔓" if not st.session_state.lock_panel_2 else "Panel 2 (Admission) 🔒"
                if st.button(l3_lbl, use_container_width=True, key="l_p2_btn"):
                    st.session_state.lock_panel_2 = not st.session_state.lock_panel_2
                    st.rerun()
            with col_l4:
                l4_lbl = "Panel 3 (CCE Report) 🔓" if not st.session_state.lock_panel_3 else "Panel 3 (CCE Report) 🔒"
                if st.button(l4_lbl, use_container_width=True, key="l_p3_btn"):
                    st.session_state.lock_panel_3 = not st.session_state.lock_panel_3
                    st.rerun()
            with col_l5:
                l5_lbl = "Panel 4 (Foil) 🔓" if not st.session_state.lock_panel_4 else "Panel 4 (Foil) 🔒"
                if st.button(l5_lbl, use_container_width=True, key="l_p4_btn"):
                    st.session_state.lock_panel_4 = not st.session_state.lock_panel_4
                    st.rerun()

        # 🔐 क्रेडेंशियल एडिटर सिस्टम (यूज़रनेम और पासवर्ड दोनों मॉडिफायर इनेबल्ड)
        if not st.session_state.admin_hide_cred_panel:
            st.subheader("🔐 Change User Credentials System")
            with st.form(key="cred_change_form_p5"):
                sel_account = st.selectbox("संशोधन के लिए खाता चुनें:", options=list(st.session_state.credentials.keys()))
                new_user_name = st.text_input("नया Username:", value=sel_account).strip()
                new_pass_word = st.text_input("नया Password:", type="password")
                if st.form_submit_button("Update Credentials Permanently", type="primary"):
                    if new_pass_word.strip() == "" or new_user_name == "": 
                        st.error("यूज़रनेम/पासवर्ड खाली नहीं हो सकता।")
                    else:
                        acc_role = st.session_state.credentials[sel_account]["role"]
                        if new_user_name != sel_account:
                            st.session_state.credentials[new_user_name] = {"password": new_pass_word, "role": acc_role}
                            del st.session_state.credentials[sel_account]
                        else: 
                            st.session_state.credentials[sel_account]["password"] = new_pass_word
                        save_credentials(st.session_state.credentials)
                        st.success("✅ क्रेडेंशियल्स स्थायी रूप से अपडेट हुए!")
                        st.rerun()

        # ✏️ लेबल्स कस्टमाइज़र एक्सपैंडर
        st.subheader("✏️ Dynamic Column & Text Box Label Customizer")
        with st.expander("कॉलम और टेक्स्ट बॉक्स के नाम (Labels) बदलने के लिए यहाँ क्लिक करें", expanded=False):
            with st.form(key="col_rename_matrix_form_p5"):
                col_setup1, col_setup2 = st.columns(2)
                temp_mappings = {}
                for index, internal_name in enumerate(DEFAULT_COLUMNS):
                    current_val = st.session_state.column_mappings.get(internal_name, internal_name)
                    if index % 2 == 0:
                        with col_setup1: temp_mappings[internal_name] = st.text_input(f"Label for '{internal_name}':", value=current_val, key=f"ren_{internal_name}_p5")
                    else:
                        with col_setup2: temp_mappings[internal_name] = st.text_input(f"Label for '{internal_name}':", value=current_val, key=f"ren_{internal_name}_p5")
                if st.form_submit_button("Save Schema Labels Permanently", type="primary"):
                    st.session_state.column_mappings = temp_mappings
                    save_column_mappings(temp_mappings)
                    st.success("✅ लेबल्स स्थायी रूप से सुरक्षित अपडेट हुए!")
                    st.rerun()

        # 📊 मास्टर डेटाबेस लाइव ग्रिड व्यूअर 
        st.subheader("📊 Master Database List View & Advanced Controls")
        col_ctrl1, col_ctrl2, col_ctrl3 = st.columns(3)
        with col_ctrl1:
            if st.button("📝 एडिट टेक्स्ट फंक्शन ऑन/ऑफ करें", use_container_width=True, key="edit_text_p5"):
                st.session_state.admin_unhide_edit = not st.session_state.admin_unhide_edit
                                st.rerun()
        with col_ctrl2:
            if st.button("🔀 कॉलम मूव बटन्स ऑन/ऑफ करें", use_container_width=True, key="move_cols_p5"):
                st.session_state.admin_unhide_move = not st.session_state.admin_unhide_move
                st.rerun()
        with col_ctrl3:
            lock_label = "🔒 लिस्ट लॉक करें" if not st.session_state.admin_lock_state else "🔓 लिस्ट अनलॉक करें"
            if st.button(lock_label, use_container_width=True, key="lock_list_p5"):
                st.session_state.admin_lock_state = not st.session_state.admin_lock_state
                st.rerun()

        # 🔀 कॉलम शिफ्टिंग लॉजिक (लिस्ट अनलॉक होने पर सक्रिय)
        if st.session_state.admin_unhide_move and not st.session_state.admin_lock_state:
            target_col = st.selectbox("मूव करने के लिए कॉलम चुनें:", options=st.session_state.admin_columns_order, key="move_sel_p5")
            c_left, c_right = st.columns(2)
            if c_left.button("⬅️ Shift Left", use_container_width=True, key="shift_l_p5"):
                idx = st.session_state.admin_columns_order.index(target_col)
                if idx > 0:
                    st.session_state.admin_columns_order[idx], st.session_state.admin_columns_order[idx-1] = st.session_state.admin_columns_order[idx-1], st.session_state.admin_columns_order[idx]
                    st.rerun()
            if c_right.button("➡️ Shift Right", use_container_width=True, key="shift_r_p5"):
                idx = st.session_state.admin_columns_order.index(target_col)
                if idx < len(st.session_state.admin_columns_order) - 1:
                    st.session_state.admin_columns_order[idx], st.session_state.admin_columns_order[idx+1] = st.session_state.admin_columns_order[idx+1], st.session_state.admin_columns_order[idx]
                    st.rerun()

        # डेटा तैयार करना और रेंडर सेटिंग्स
        ordered_db = live_db[st.session_state.admin_columns_order].copy()
        ordered_db = ordered_db.rename(columns={c: get_display_name(c) for c in ordered_db.columns})
        ordered_db.insert(0, "S.No.", range(1, len(ordered_db) + 1))

        st.write(f"कुल मास्टर रिकॉर्ड संख्या: **{len(ordered_db)}**")

        # 📝 लाइव एडिटिंग और डायनेमिक डेटा सिंक्रोनाइज़ेशन लॉजिक
        if not st.session_state.admin_lock_state and st.session_state.admin_unhide_edit:
            st.warning("⚠️ लाइव संपादन सक्रिय है।")
            col_act1, col_act2 = st.columns(2)
            if col_act1.button("✅ Select All Rows", use_container_width=True, key="sel_all_p5"): 
                st.session_state["admin_select_all_active"] = True
            confirm_delete = col_act2.button("🗑️ Delete Selected Rows", use_container_width=True, type="primary", key="del_rows_p5")

            # लाइव डेटा एडिटर मैट्रिक्स विजेट
            edited_df = st.data_editor(
                ordered_db, 
                use_container_width=True, 
                disabled=["S.No.", get_display_name("Current Year")], 
                num_rows="dynamic", 
                key="admin_live_editor_grid_p5", 
                hide_index=True
            )
            clean_edited = edited_df.drop(columns=["S.No."])
            reverse_mapping = {get_display_name(k): k for k in st.session_state.admin_columns_order}
            
            # पूर्णतः डेटाबेस रीसेट / डिलीट ऑल लॉजिक
            if confirm_delete and st.session_state.get("admin_select_all_active", False):
                st.session_state["admin_select_all_active"] = False
                save_live_data(pd.DataFrame(columns=DEFAULT_COLUMNS))
                st.success("🔥 डेटाबेस रीसेट सफल!")
                st.rerun()
            
            # रो (Row) लेवल सिंकिंग मैकेनिज्म
            synced_data = {col: [] for col in DEFAULT_COLUMNS}
            for _, row_edit in clean_edited.iterrows():
                for d_name in clean_edited.columns:
                    i_key = reverse_mapping.get(d_name, d_name)
                    if i_key in synced_data: 
                        synced_data[i_key].append(row_edit[d_name])
            
            new_live_db = pd.DataFrame(synced_data)
            
            # रिकॉर्ड संख्या बदलने या संपादन पूरा होने पर क्लाउड CSV में कमिट करना
            if len(new_live_db) != len(live_db) or confirm_delete:
                save_live_data(new_live_db)
                st.success("✅ लाइव मास्टर डेटाबेस सिंक सफल!")
                st.rerun()
        else: 
            # रीड-ओनली डेटा डिस्प्ले मोड
            st.dataframe(ordered_db, use_container_width=True, hide_index=True)
            
        

                                
            
            
