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

# 🔑 सुरक्षा क्रेडेंशियल्स - इसे सेशन स्टेट में रखा है ताकि एडमिन इसे बदल सके
if "credentials" not in st.session_state:
    st.session_state.credentials = {
        "entry": {"password": "entry123", "role": "data_entry"},
        "viewer": {"password": "viewer123", "role": "list_viewer"},
        "cce": {"password": "cce123", "role": "cce_handler"},
        "admin": {"password": "admin123", "role": "full_admin"}
    }

# 🎯 बिल्कुल नए 20+1 कॉलम्स की मास्टर सूची
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
if "admin_unhide_edit" not in st.session_state:
    st.session_state.admin_unhide_edit = False
if "admin_unhide_move" not in st.session_state:
    st.session_state.admin_unhide_move = False
if "cce_foil_generated" not in st.session_state:
    st.session_state.cce_foil_generated = False

live_db = load_live_data()

# ==========================================================
# 🔒 मुख्य लॉगिन गेटवे (इसके बाहर कुछ नहीं दिखेगा)
# ==========================================================
if st.session_state.user_role is None:
    st.markdown("---")
    st.subheader("🔒 Multi-User Secure Login Gateway")
    user_input = st.selectbox("Username (भूमिका) चुनें:", options=list(st.session_state.credentials.keys()))
    password_input = st.text_input("Password दर्ज करें:", type="password")
    
    if st.button("Secure Login", use_container_width=True, type="primary"):
        if user_input in st.session_state.credentials and st.session_state.credentials[user_input]["password"] == password_input:
            st.session_state.user_role = st.session_state.credentials[user_input]["role"]
            st.session_state.upload_success = False
            st.session_state.save_success = False
            st.session_state.admin_lock_state = True  
            st.session_state.admin_unhide_edit = False
            st.session_state.admin_unhide_move = False
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
    # 📁 1. DATA ENTRY PANEL (Role: data_entry या full_admin)
    # 🎯 आवश्यकता 1: इसमें केवल शुद्ध डेटा एंट्री का ही साधन रहेगा
    # --------------------------------------------------
    if role in ["data_entry", "full_admin"]:
        st.header("📝 Student Data Entry Panel")
        
        # 🔄 स्मार्ट ऑटो-हाइड ट्रिगर ड्रॉपडाउन
        entry_method = st.selectbox(
            "⚙️ डेटा एंट्री का माध्यम चुनें (Choose Entry Method):",
            options=["📁 CSV फ़ाइल बल्क अपलोड (Bulk CSV Upload)", "➕ नया छात्र मैनुअल फॉर्म (Manual Form Entry)"],
            key="data_entry_method_selector"
        )
        st.markdown("---")

        # ----------------------------------------
        # माध्यम ए: केवल CSV अपलोडर (मैनुअल फॉर्म पूरी तरह हाइड)
        # ----------------------------------------
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
                    
                    if st.button("Upload CSV Now", use_container_width=True, type="primary", key="csv_upload_submit_btn"):
                        # 🎯 1. केवल वही कॉलम्स सुनिश्चित करें जो मास्टर सूची में हैं
                        for col in DEFAULT_COLUMNS:
                            if col not in uploaded_df.columns:
                                uploaded_df[col] = ""
                        
                        # 🎯 2. फ़ाइल से फालतू कॉलम्स को हटाकर व्यवस्थित करना
                        cleaned_uploaded_df = uploaded_df[DEFAULT_COLUMNS].copy()
                        
                        current_db = load_live_data()
                        
                        # 🎯 3. डेटाबेस में कतारों को सुरक्षित रूप से मर्ज करना
                        if current_db.empty:
                            updated_df = cleaned_uploaded_df
                        else:
                            updated_df = pd.concat([current_db, cleaned_uploaded_df], ignore_index=True)
                        
                        save_live_data(updated_df)
                        
                        # स्क्रीन रिफ्रेश और अपलोड सक्सेस स्टेट क्लीनअप
                        st.session_state.upload_success = True
                        st.session_state.csv_uploader_id += 1  # uploader रीसेट ट्रिगर
                        st.rerun()
                except Exception as e:
                    st.error(f"त्रुटि: {e}")

            if st.session_state.upload_success:
                st.success("✅ CSV Data Filtered & Successfully Uploaded!")
                st.session_state.upload_success = False

        # ----------------------------------------
        # माध्यम बी: केवल मैनुअल फॉर्म (CSV अपलोडर पूरी तरह हाइड)
        # ----------------------------------------
        elif entry_method == "➕ नया छात्र मैनुअल फॉर्म (Manual Form Entry)":
            st.subheader("➕ Naya Student Data Add Karein")
            
            with st.form(key="student_add_form", clear_on_submit=True):
                # 2-कॉलम ग्रिड लेआउट
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
                    m_name = st.text_input("Mother Name (माता का नाम)")
                    category = st.selectbox("Category (कैटेगरी)", ["General", "OBC", "SC", "ST"])
                    duration = st.text_input("Duration (कोर्स की अवधि)")
                    email = st.text_input("Email ID (ईमेल आईडी)")
                    status_input = st.selectbox("Status (स्थिति)", ["Active", "Pending", "Pass", "Inactive"])
                
                submit_student = st.form_submit_button("Save Student Data", type="primary", use_container_width=True)

            if submit_student:
                if s_name.strip() == "":
                    st.warning("कृपया कम से कम Student Name ज़रूर भरें।")
                else:
                    new_row = {
                        "Admission Year": admission_year, "Admission Session": admission_session, 
                        "Eligibility Name": eligibility_name, "Admission Application Number": admission_app_no,
                        "Admission Date": admission_date, "Unique ID": unique_id, "Roll No.": roll_no, 
                        "Application Enrollment No.": app_enroll_no, "Enrollment No.": enrollment_no, 
                        "Student Name": s_name, "Father Name": f_name, "Mother Name": m_name, "Date of Birth": dob, 
                        "Category": category, "Subject": subject, "Duration": duration, "Mobile Number": mobile, 
                        "Email ID": email, "Address": address, "Status": status_input, 
                        "Current Year": ""  # बैकएंड गणना के लिए खाली, लोड होने पर स्वतः फिल होगा
                    }
                    current_db = load_live_data()
                    if current_db.empty:
                        updated_df = pd.DataFrame([new_row])
                    else:
                        updated_df = pd.concat([current_db, pd.DataFrame([new_row])], ignore_index=True)
                    
                    save_live_data(updated_df)
                    st.session_state.save_success = True
                    st.rerun()

            if st.session_state.save_success:
                st.success("✅ Student data saved successfully")
                st.session_state.save_success = False

    # --------------------------------------------------
    # 👁️ 2. LIST VIEWER PANEL (Role: list_viewer या full_admin)
    # 🎯 आवश्यकता 2: पहले कॉलम स्क्रॉल करके चुनें, फिर टाइप करें, CSV और प्रिंट बटन रहेगा
    # --------------------------------------------------
    if role in ["list_viewer", "full_admin"]:
        st.header("Student Live Database List (Viewer Mode)")
        st.markdown('<div class="print-hide">', unsafe_allow_html=True)
        
        # 1. पहले कॉलम नाम स्क्रॉल/सेलेक्ट करने का ड्रॉपडाउन
        selected_search_column = st.selectbox(
            "🔍 किस कॉलम में सर्च करना चाहते हैं? कॉलम चुनें (Select Column to Search):", 
            options=DEFAULT_COLUMNS, 
            key="viewer_panel_column_selector"
        )
        
        # 2. चुने गए कॉलम के आधार पर टाइप करने का सर्च बार
        search_query = st.text_input(
            f"'{selected_search_column}' के अंदर सर्च करने के लिए टाइप करें:", 
            key="viewer_panel_search_query_input"
        )
        st.markdown('</div>', unsafe_allow_html=True)

        filtered_db = live_db.copy()
        
        # सर्च बार फ़िल्टर लॉजिक (पूरी रो को निकालने के लिए)
        if search_query:
            filtered_db = filtered_db[
                filtered_db[selected_search_column].str.contains(search_query, case=False, na=False)
            ]
            
        st.write(f"Kul Student Record: **{len(filtered_db)}**")
        
        if not filtered_db.empty:
            # S.No. को 1 से सुव्यवस्थित सेट करना
            display_df = filtered_db.copy()
            display_df.insert(0, "S.No.", range(1, len(display_df) + 1))
            
            # सुरक्षित रीड-ओनली तालिका दृश्य (पूरी रो शो होगी)
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            # --- 🛠️ बटन्स (केवल CSV डाउनलोड और डायरेक्ट प्रिंटर कमांड) ---
            st.markdown('<div class="print-hide">', unsafe_allow_html=True)
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                # बटन ए: केवल CSV डाउनलोड करने का विकल्प
                csv_buffer = filtered_db.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download Student List (CSV)", 
                    data=csv_buffer, 
                    file_name="student_database_list.csv", 
                    mime="text/csv", 
                    use_container_width=True, 
                    key="viewer_panel_csv_download_action"
                )
                
            with col_btn2:
                # बटन बी: सीधे हार्डवेयर प्रिंटर पर भेजने का डायरेक्ट प्रिंट कमांड
                st.markdown("""
                    <button onclick="window.print()" style="
                        width: 100%; 
                        background-color: #FF5733; 
                        color: white; 
                        border: none; 
                        padding: 0.5rem 1rem; 
                        border-radius: 0.5rem; 
                        cursor: pointer; 
                        font-weight: 500; 
                        line-height: 1.6; 
                        text-align: center; 
                        box-sizing: border-box;
                    ">Direct Print</button>
                """, unsafe_allow_html=True)
                
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.warning("Record match nahi hua.")

    # --------------------------------------------------
    # 📝 3. CCE HANDLER PANEL (Role: cce_handler या full_admin)
    # 🎯 आवश्यकता 3: केवल CCE Foil जेनरेटर सिस्टम, प्रिंट बटन और PNG इमेज डाउनलोड सिस्टम
    # --------------------------------------------------
    if role in ["cce_handler", "full_admin"]:
        st.header("College CCE Foil Sheet Generator")
        st.write("Institute of Law, Govt. Kamlaraja Girls Post-Graduate Autonomous College, Gwalior (M.P.)")

        if not live_db.empty:
            semesters = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
            def reset_foil_state():
                st.session_state.cce_foil_generated = False

            target_sem = st.selectbox("Kaun sa Semester chahiye?", semesters, key="cce_sem_box", on_change=reset_foil_state)
            sem_to_year_text = {"1": "1 year", "2": "1 year", "3": "2 year", "4": "2 year", "5": "3 year", "6": "3 year", "7": "4 year", "8": "4 year", "9": "5 year", "10": "5 year"}
            target_year_text = sem_to_year_text[target_sem]

            college_name = "GOVT. K.R.G. POST-GRADUATE AUTONOMOUS COLLEGE, GWALIOR (M.P.)"
            exam_info = f"Examination :- CCE                                             B.A. LL.B. {target_sem}th SEMESTER"

            if st.button("Generate CCE Foil Sheets Now", use_container_width=True, type="primary", key="generate_foil_btn"):
                st.session_state.cce_foil_generated = True

            if st.session_state.cce_foil_generated:
                roll_numbers = []
                for _, row in live_db.iterrows():
                    roll = str(row.get('Roll No.', row.get('Roll No', ''))).strip()
                    status = str(row.get('Status', row.get('STATUS', ''))).strip().upper()
                    current_year_val = str(row.get('Current Year', '')).strip().lower()
                    if not roll or roll == "nan" or roll == "":
                        continue
                    if target_year_text in current_year_val and ('REGULAR' in status or 'ACTIVE' in status):
                        roll_numbers.append(roll)
                    elif 'EX-STUDENT' in current_year_val or 'EX-STUDENT' in status or 'EX' in status:
                        if target_year_text in current_year_val:
                            roll_numbers.append(roll)

                roll_numbers = sorted(list(set(roll_numbers)))

                if roll_numbers:
                    st.success(f"Total {len(roll_numbers)} students mile hain.")
                    left_side_rolls = roll_numbers[:30]
                    right_side_rolls = roll_numbers[30:60]

                    def generate_cce_html_block(rolls, start_idx, foil_label, has_data):
                        if not has_data:
                            return '<div class="foil-unit" style="border:none; background:transparent;"></div>'
                        block = f"""
                        <div class="foil-unit">
                            <div class="top-fields"><div></div><div>Paper Code....................</div></div>
                            <div class="top-fields" style="margin-top: 5px;"><div></div><div>Bundle No....................</div></div>
                            <div class="header-box">{college_name}</div>
                            <div class="sub-box exam-right">{exam_info}</div>
                            <div class="sub-box">Subject.................................................... Paper.........................</div>
                            <div class="marks-info"><div>Max. Marks: ...................</div><div>Min. Pass Marks: ...................</div></div>
                            <div class="foil-title">{foil_label}</div>
                            <table style="width:100%; border-collapse:collapse; margin-top:10px;">
                                <tr><th style="border:1px solid black; padding:4px;" style="width: 8%;">1</th><th style="border:1px solid black; padding:4px;" style="width: 30%;" colspan="3">2</th></tr>
                                <tr><th style="border:1px solid black; padding:4px;" rowspan="2">Code No.</th><th style="border:1px solid black; padding:4px;" rowspan="2">Roll No.</th><th style="border:1px solid black; padding:4px;" colspan="2">Marks Obtained</th></tr>
                                <tr><th style="border:1px solid black; padding:4px; width: 15%;">In Figures</th><th style="border:1px solid black; padding:4px; width: 45%;">In Words</th></tr>
                        """
                        for idx_foil, r_foil in enumerate(rolls, start=start_idx):
                            block += f"<tr><td style='border:1px solid black; padding:4px;'><b>{idx_foil}</b></td><td style='border:1px solid black; padding:4px;'>{r_foil}</td><td style='border:1px solid black; padding:4px;'></td><td style='border:1px solid black; padding:4px;'></td></tr>"
                        current_len = len(rolls)
                        if current_len < 30:
                            for k in range(current_len + start_idx, 30 + start_idx):
                                block += "<tr><td style='border:1px solid black; padding:4px;'>&nbsp;</td><td style='border:1px solid black; padding:4px;'>&nbsp;</td><td style='border:1px solid black; padding:4px;'>&nbsp;</td><td style='border:1px solid black; padding:4px;'>&nbsp;</td></tr>"
                        block += f"""
                            </table>
                            <div class="note" style="font-size:10px; margin-top:10px;"><b>Note:</b> Roll Number and Marks awarded to the candidate may be entered under respective columns very carefully.</div>
                            <div class="footer-fields">Signature of Examiner......................................<br>Date: ___/___/2026</div>
                        </div>
                        """
                        return block

                    left_block_html = generate_cce_html_block(left_side_rolls, 1, "FOIL", True)
                    right_block_html = generate_cce_html_block(right_side_rolls, 31, "FOIL", len(right_side_rolls) > 0)

                    html_style = """
                    <style>
                        #foil-capture-area { display: flex; justify-content: space-between; gap: 20px; width: 1100px; padding: 15px; background: white; margin: auto; }
                        .foil-unit { width: 49%; border: 1px solid black; padding: 12px; box-sizing: border-box; background: white; }
                        .top-fields { display: flex; justify-content: space-between; font-weight: bold; font-size: 13px; }
                        .header-box { text-align: center; border-top: 2px solid black; border-bottom: 2px solid black; padding: 6px 0; margin-top: 8px; font-weight: bold; font-size: 16px; }
                        .sub-box { border-bottom: 2px solid black; padding: 5px 0; font-size: 12px; font-weight: bold; }
                        .exam-right { text-align: right; }
                        .marks-info { display: flex; justify-content: space-between; padding: 5px 0; font-weight: bold; border-bottom: 2px solid black; font-size: 12px; }
                        .foil-title { text-align: center; font-weight: bold; font-size: 16px; margin: 10px 0; }
                        .footer-fields { margin-top: 15px; font-size: 12px; font-weight: bold; }
                    </style>
                    """
                    
                    full_html = f"""
                    <html>
                    <head>
                        {html_style}
                        <script src="https://cloudflare.com"></script>
                        <script>
                        function downloadFoilAsPNG() {{
                            const element = document.getElementById("foil-capture-area");
                            html2canvas(element, {{ scale: 2 }}).then(canvas => {{
                                let link = document.createElement("a");
                                link.download = "cce_foil_sheet.png";
                                link.href = canvas.toDataURL("image/png");
                                link.click();
                            }});
                        }}
                        </script>
                    </head>
                    <body>
                        <div class="print-hide" style="text-align: center; margin-bottom: 15px; display:flex; gap:20px; justify-content:center;">
                            <button onclick="window.print()" style="background:#FF5733; color:white; border:none; padding:10px 20px; border-radius:5px; cursor:pointer; font-weight:bold;">Direct Print Only Foil</button>
                            <button onclick="downloadFoilAsPNG()" style="background:#4CAF50; color:white; border:none; padding:10px 20px; border-radius:5px; cursor:pointer; font-weight:bold;">Download File in PNG File</button>
                        </div>
                        <div id="foil-capture-area">
                            {left_block_html}
                            {right_block_html}
                        </div>
                    </body>
                    </html>
                    """
                    st.components.v1.html(full_html, height=1600, scrolling=True)
                else:
                    st.error("Is Semester ka koi data live list me nahi mila.")
        else:
            st.error("Live database file khali hai.")

    # --------------------------------------------------
    # 🛠️ 4. FULL ADMIN ROLE PANEL (Role: केवल full_admin)
    # 🎯 आवश्यकता 4: क्रेडेंशियल्स बदलना, लिस्ट शो, कंट्रोल्स को अनहाइड करने के बटन्स (टेक्स्ट एडिट, कॉलम शिफ्ट, लॉक/अनलॉक)
    # --------------------------------------------------
    if role == "full_admin":
        st.header("🛠️ Full Admin Management Panel")
        
        # 🔑 पार्ट ए: यूजरनेम और पासवर्ड बदलने का पावर
        st.subheader("🔐 Change User Credentials System")
        with st.form(key="credentials_change_form"):
            target_user = st.selectbox("किस यूजर का क्रेडेंशियल बदलना चाहते हैं?", options=list(st.session_state.credentials.keys()))
            new_password = st.text_input("नया पासवर्ड दर्ज करें:", type="password")
            submit_cred = st.form_submit_button("Update Password Now", type="primary")
            
            if submit_cred:
                if new_password.strip() == "":
                    st.error("पासवर्ड खाली नहीं हो सकता।")
                else:
                    st.session_state.credentials[target_user]["password"] = new_password
                    st.success(f"✅ '{target_user}' का पासवर्ड सफलतापूर्वक अपडेट हो गया है!")

        st.markdown("---")
        st.subheader("📊 Master Database List View & Advanced Controls")
        
        # 🎯 कंट्रोल बटन्स का पैनल (फंक्शंस को अनहाइड करने के लिए)
        col_ctrl1, col_ctrl2, col_ctrl3 = st.columns(3)
        with col_ctrl1:
            if st.button("📝 एडिट टेक्स्ट फ़ंक्शन अनहाइड/हाइड करें", use_container_width=True, key="admin_btn_unhide_text_edit"):
                st.session_state.admin_unhide_edit = not st.session_state.admin_unhide_edit
                st.rerun()
        with col_ctrl2:
            if st.button("🔀 कॉलम मूव बटन्स अनहाइड/हाइड करें", use_container_width=True, key="admin_btn_unhide_column_move"):
                st.session_state.admin_unhide_move = not st.session_state.admin_unhide_move
                st.rerun()
        with col_ctrl3:
            lock_label = "🔒 लिस्ट लॉक करें" if not st.session_state.admin_lock_state else "🔓 लिस्ट अनलॉक करें"
            if st.button(lock_label, use_container_width=True, key="admin_btn_toggle_lock_state"):
                st.session_state.admin_lock_state = not st.session_state.admin_lock_state
                st.rerun()

        # 🔀 कॉलम खिसकाने के मूव बटन्स (यदि बटन अनहाइड किया गया हो)
        if st.session_state.admin_unhide_move:
            st.info("🔄 कॉलम मूव कंट्रोल्स एक्टिव हैं:")
            target_col = st.selectbox("मूव करने के लिए कॉलम चुनें:", options=st.session_state.admin_columns_order, key="admin_col_shift_select")
            c_left, c_right = st.columns(2)
            
            if c_left.button("⬅️ सिलेक्ट कॉलम लेफ्ट (Shift Left)", use_container_width=True, key="admin_shift_left_trigger"):
                idx = st.session_state.admin_columns_order.index(target_col)
                if idx > 0:
                    st.session_state.admin_columns_order[idx], st.session_state.admin_columns_order[idx-1] = st.session_state.admin_columns_order[idx-1], st.session_state.admin_columns_order[idx]
                    st.rerun()
                    
            if c_right.button("➡️ सिलेक्ट कॉलम राइट (Shift Right)", use_container_width=True, key="admin_shift_right_trigger"):
                idx = st.session_state.admin_columns_order.index(target_col)
                if idx < len(st.session_state.admin_columns_order) - 1:
                    st.session_state.admin_columns_order[idx], st.session_state.admin_columns_order[idx+1] = st.session_state.admin_columns_order[idx+1], st.session_state.admin_columns_order[idx]
                    st.rerun()

        # वर्तमान कॉलम ऑर्डर की मैपिंग तैयार करना
        ordered_db = live_db[st.session_state.admin_columns_order].copy()
        ordered_db.insert(0, "S.No.", range(1, len(ordered_db) + 1))
        
        st.write(f"कुल रिकॉर्ड संख्या: **{len(ordered_db)}**")
        
        # 📝 स्थिति 1: जब लिस्ट अनलॉक है और टेक्स्ट एडिट फ़ंक्शन अनहाइड है (डायरेक्ट लाइव टेक्स्ट एडिटिंग)
        if not st.session_state.admin_lock_state and st.session_state.admin_unhide_edit:
            st.warning("⚠️ लाइव डायरेक्ट टेक्स्ट संपादन सक्रिय है। ग्रिड में किया गया बदलाव सीधे सेव हो जाएगा।")
            edited_df = st.data_editor(
                ordered_db,
                use_container_width=True,
                disabled=["S.No.", "Current Year"],
                key="admin_live_data_editor",
                hide_index=True
            )
            # परिवर्तनों को मूल डेटाबेस में सुरक्षित वापस सिंक करें
            clean_edited = edited_df.drop(columns=["S.No."])
            for col in clean_edited.columns:
                if col != "Current Year":
                    live_db[col] = clean_edited[col].values
            save_live_data(live_db)
            
        # 🔒 स्थिति 2: जब लिस्ट लॉक हो या टेक्स्ट एडिट फ़ंक्शन हाइड हो (साधारण रीड-ओनली व्यू)
        else:
            st.dataframe(ordered_db, use_container_width=True, hide_index=True)
        
