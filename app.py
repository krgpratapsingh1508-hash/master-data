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
    # 📁 1. DATA ENTRY ROLE (नए 20 कॉलम्स और ऑटो-क्लियर फ़ीचर के साथ)
    # ==========================================
    if role == "data_entry":
        st.header("📝 Student Data Entry Panel")
        
        # 🔄 स्मार्ट ऑटो-हाइड ट्रिगर ड्रॉपडाउन
        entry_method = st.selectbox(
            "⚙️ डेटा एंट्री का माध्यम चुनें (Choose Entry Method):",
            options=["📁 CSV फ़ाइल बल्क अपलोड (Bulk CSV Upload)", "➕ नया छात्र मैनुअल फॉर्म (Manual Form Entry)"]
        )
        st.markdown("---")

        # ----------------------------------------
        # माध्यम ए: केवल CSV अपलोडर दिखेगा (मैनुअल फॉर्म हाइड रहेगा)
        # ----------------------------------------
        if entry_method == "📁 CSV फ़ाइल बल्क अपलोड (Bulk CSV Upload)":
            st.subheader("📁 CSV File Bulk Upload")
            
            # ऑटो-क्लियर के लिए डायनामिक की (Key) का उपयोग
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
                        # 🎯 1. केवल वही कॉलम्स चुनें जो आपके नए सूची में तय हैं (DEFAULT_COLUMNS)
                        for col in DEFAULT_COLUMNS:
                            if col not in uploaded_df.columns:
                                uploaded_df[col] = ""
                        
                        # 🎯 2. फ़ाइल से फालतू कॉलम्स को हटाकर नए क्रम में व्यवस्थित करना
                        cleaned_uploaded_df = uploaded_df[DEFAULT_COLUMNS].copy()
                        
                        current_db = load_live_data()
                        
                        # 🎯 3. डेटाबेस में कतारों को सुरक्षित रूप से मर्ज करना
                        if current_db.empty:
                            updated_df = cleaned_uploaded_df
                        else:
                            updated_df = pd.concat([current_db, cleaned_uploaded_df], ignore_index=True)
                        
                        save_live_data(updated_df)
                        
                        # 🎯 फ़ाइल को डैशबोर्ड से तुरंत हटाने और स्क्रीन साफ करने का लॉजिक
                        st.session_state.upload_success = True
                        st.session_state.save_success = False
                        st.session_state.csv_uploader_id += 1  # आईडी बदलते ही uploader रीसेट
                        st.rerun()
                except Exception as e:
                    st.error(f"त्रुटि: {e}")

            if st.session_state.upload_success:
                st.success("✅ CSV Data Filtered & Successfully Uploaded!")
                st.session_state.upload_success = False

        # ----------------------------------------
        # माध्यम बी: केवल मैनुअल फॉर्म दिखेगा (CSV अपलोडर हाइड रहेगा)
        # ----------------------------------------
        elif entry_method == "➕ नया छात्र मैनुअल फॉर्म (Manual Form Entry)":
            st.subheader("➕ Naya Student Data Add Karein")
            
            with st.form(key="student_add_form", clear_on_submit=True):
                # आपके नए 20 कस्टमाइज्ड इनपुट फ़ील्ड्स
                admission_year = st.text_input("Admission Year (प्रवेश वर्ष)")
                admission_session = st.text_input("Admission Session (सत्र)")
                eligibility_name = st.text_input("Eligibility Name (योग्यता का नाम)")
                admission_app_no = st.text_input("Admission Application Number (आवेदन संख्या)")
                admission_date = st.text_input("Admission Date (प्रवेश तिथि)")
                unique_id = st.text_input("Unique ID (आधार या स्कॉलर नंबर)")
                roll_no = st.text_input("Roll No. (रोल नंबर)")
                app_enroll_no = st.text_input("Application Enrollment No. (एप्लिकेशन नामांकन संख्या)")
                enrollment_no = st.text_input("Enrollment No. (स्थायी नामांकन संख्या)")
                s_name = st.text_input("Student Name (छात्र का नाम)")
                f_name = st.text_input("Father Name (पिता का नाम)")
                m_name = st.text_input("Mother Name (माता का नाम)")
                dob = st.text_input("Date of Birth (जन्म तिथि)")
                category = st.selectbox("Category (कैटेगरी)", ["General", "OBC", "SC", "ST"])
                subject = st.text_input("Subject (विषय/स्ट्रीम)")
                duration = st.text_input("Duration (कोर्स की अवधि)")
                mobile = st.text_input("Mobile Number (मोबाइल नंबर)")
                email = st.text_input("Email ID (ईमेल आईडी)")
                address = st.text_input("Address (पता)")
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
                        "Email ID": email, "Address": address, "Status": status_input
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
                st.success("✅ Student data save successfully")
                st.session_state.save_success = False
                
    # ==========================================
    # 👁️ 2. LIST VIEWER ROLE (सुरक्षित और एरर-फ्री व्यूअर मोड)
    # ==========================================
    elif role == "list_viewer":
        st.header("Student Live Database List (Viewer Mode)")
        
        st.markdown('<div class="print-hide">', unsafe_allow_html=True)
        visibility_label = "Unhide Student List" if not st.session_state.list_visibility_state else "Hide Student List"
        if st.button(visibility_label, use_container_width=True, type="secondary"):
            st.session_state.list_visibility_state = not st.session_state.list_visibility_state
            st.rerun()
            
        search_query = st.text_input("Student Name ya Roll No. darj karke khojein:")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 🎯 यदि लिस्ट को हाइड (Hide) किया गया है
        if not st.session_state.list_visibility_state:
            st.info("Student list ko varpamaan me chhupaya gaya hai. Dekhne ke liye upar Unhide button dabayein.")
        else:
            filtered_db = live_db.copy()
            if search_query:
                filtered_db = filtered_db[
                    filtered_db["Student Name"].str.contains(search_query, case=False, na=False) |
                    filtered_db["Roll No."].str.contains(search_query, case=False, na=False)
                ]
            st.write(f"Kul Student Record: **{len(filtered_db)}**")
            
            # यदि सर्च रिकॉर्ड या डेटाबेस खाली नहीं है
            if not filtered_db.empty:
                # 🎯 S.No. को 1 से सुव्यवस्थित तरीके से सेट करना बिना रो को आगे-पीछे किए
                filtered_db.insert(0, "S.No.", range(1, len(filtered_db) + 1))
                
                # सुरक्षित रीड-ओनली टेबल व्यू (Viewer के लिए कॉलम हमेशा फिक्स और लॉक रहेंगे)
                st.dataframe(filtered_db, use_container_width=True, hide_index=True)
                
                # स्वच्छ डाउनलोड फ़ाइल तैयार करना (बिना S.No. के)
                clean_download_df = filtered_db.drop(columns=["S.No."])
                
                # --- 🛠️ बटन अनुभाग (3 विशिष्ट बटन्स का पैनल - एरर फ्री) ---
                st.markdown('<div class="print-hide">', unsafe_allow_html=True)
                col_btn1, col_btn2, col_btn3 = st.columns(3)
                
                with col_btn1:
                    # बटन 1: डायरेक्ट CSV फाइल डाउनलोड
                    csv_buffer = clean_download_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download Student List (CSV)", 
                        data=csv_buffer, 
                        file_name="student_database_list.csv", 
                        mime="text/csv", 
                        use_container_width=True
                    )
                    
                with col_btn2:
                    # बटन 2: जावास्क्रिप्ट आधारित डायरेक्ट Landscape PDF जनरेटर (बिना प्रिंटर की ज़रूरत के)
                    columns_json = list(clean_download_df.columns)
                    rows_json = clean_download_df.values.tolist()
                    
                    pdf_script = f"""
                    <script src="https://cloudflare.com"></script>
                    <script src="https://cloudflare.com"></script>
                    <script>
                    function generateLandscapePDF() {{
                        const {{ jsPDF }} = window.jspdf;
                        const doc = new jsPDF('l', 'mm', 'a4');
                        
                        doc.text("Permanent Shared Live Database - Student List", 14, 15);
                        
                        const columns = {columns_json};
                        const rows = {rows_json};
                        
                        doc.autoTable({{
                            head: [columns],
                            body: rows,
                            startY: 22,
                            styles: {{ fontSize: 7, cellPadding: 1.5 }},
                            theme: 'grid'
                        }});
                        
                        doc.save('student_list_landscape.pdf');
                    }}
                    </script>
                    <button onclick="generateLandscapePDF()" style="
                        width: 100%; 
                        background-color: #4CAF50; 
                        color: white; 
                        border: none; 
                        padding: 0.5rem 1rem; 
                        border-radius: 0.5rem; 
                        cursor: pointer; 
                        font-weight: 500; 
                        line-height: 1.6; 
                        text-align: center; 
                        box-sizing: border-box;
                    ">Direct Landscape PDF Download</button>
                    """
                    st.markdown(pdf_script, unsafe_allow_html=True)
                    
                with col_btn3:
                    # बटन 3: सीधे हार्डवेयर प्रिंटर पर प्रिंट भेजने या ब्राउज़र प्रिंट डायलॉग खोलने का बटन
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
                
    # ==========================================
    # 📝 3. CCE HANDLER ROLE (डेटाबेस सूची और एरर-फ्री Foil Sheet जनरेटर)
    # ==========================================
    elif role == "cce_handler":
        st.header("College CCE Foil Sheet Generator & Live Database")
        st.markdown("---")

        # --- स्टेट मैनेजमेंट ट्रिगर ---
        if "cce_foil_generated" not in st.session_state:
            st.session_state.cce_foil_generated = False

        # बटन क्लिक को स्थायी रखने के लिए फंक्शन
        def click_foil_button():
            st.session_state.cce_foil_generated = True

        # ----------------------------------------
        # प्ररूप 1: CCE Foil Sheet जनरेटर (बटन क्लिक पर लोड होगा)
        # ----------------------------------------
        st.subheader("Part 1: College CCE Foil Sheets (Landscape View)")
        st.write("Institute of Law, Govt. Kamlaraja Girls Post-Graduate Autonomous College, Gwalior (M.P.)")
        
        if not live_db.empty:
            semesters = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
            
            # सेमेस्टर बदलते ही पुरानी फ़ॉइल हाइड करने के लिए ऑन-चेंज लॉजिक
            def reset_foil_state():
                st.session_state.cce_foil_generated = False

            target_sem = st.selectbox("Kaun sa Semester chahiye?", semesters, key="cce_sem_box", on_change=reset_foil_state)

            sem_to_year_num = {
                "1": "1", "2": "1", "3": "2", "4": "2", "5": "3",
                "6": "3", "7": "4", "8": "4", "9": "5", "10": "5"
            }
            target_num = sem_to_year_num[target_sem]

            college_name = "GOVT. K.R.G. POST-GRADUATE AUTONOMOUS COLLEGE, GWALIOR (M.P.)"
            exam_info = f"Examination :- CCE                                             B.A. LL.B. {target_sem}th SEMESTER"

            # सुधरा हुआ जनरेट बटन (यह क्लिक स्टेट को मेमोरी में लॉक रखेगा)
            st.button("Generate CCE Foil Sheets Now", use_container_width=True, type="primary", key="generate_foil_btn", on_click=click_foil_button)

            if st.session_state.cce_foil_generated:
                roll_numbers = []
                for _, row in live_db.iterrows():
                    roll = str(row.get('Roll No.', row.get('Roll No', ''))).strip()
                    student_year = str(row.get('Duration', row.get('year', row.get('Year', '')))).strip().lower()
                    status = str(row.get('Status', row.get('STATUS', ''))).strip().upper()
                    row_sem = str(row.get('Semester', row.get('SEMESTER', row.get('sem', '')))).strip()
                    
                    if not roll or roll == "nan" or roll == "":
                        continue
                    if target_num in student_year and ('REGULAR' in status or 'ACTIVE' in status):
                        roll_numbers.append(roll)
                    elif 'EX-STUDENT' in status or 'EX' in status:
                        if row_sem == target_sem or target_num in student_year or not row_sem:
                            roll_numbers.append(roll)

                roll_numbers = sorted(list(set(roll_numbers)))

                if roll_numbers:
                    st.success(f"Total {len(roll_numbers)} students mile hain. Niche aapka format ready hai.")
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
                            <table>
                                <tr><th class="col-header-num" style="width: 8%;">1</th><th class="col-header-num" style="width: 30%;" colspan="3">2</th></tr>
                                <tr><th rowspan="2">Code No.</th><th rowspan="2">Roll No.</th><th colspan="2">Marks Obtained</th></tr>
                                <tr><th style="width: 15%;">In Figures</th><th style="width: 45%;">In Words</th></tr>
                        """
                        for idx_foil, r_foil in enumerate(rolls, start=start_idx):
                            block += f"<tr><td><b>{idx_foil}</b></td><td>{r_foil}</td><td></td><td></td></tr>"
                        current_len = len(rolls)
                        if current_len < 30:
                            for k in range(current_len + start_idx, 30 + start_idx):
                                block += "<tr><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>"
                        block += f"""
                            </table>
                            <div class="note"><b>Note:</b> Roll Number and Marks awarded to the candidate may be entered under respective columns very carefully. Marks and Roll Number should be legible. These may be checked again to ensure that no mistake remains.</div>
                            <div class="footer-fields">
                                Signature of Examiner...............................................................<br>
                                Name of Examiner.....................................................................<br>
                                ....................................................................................................<br>
                                <div style="display: flex; justify-content: space-between; margin-top: 5px;"><div>Place.......................................................</div><div>Date: ___/___/2026</div></div>
                            </div>
                        </div>
                        """
                        return block

                    full_html = f"""<!DOCTYPE html>
                    <html>
                    <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; background: white; margin: 0; padding: 5px; width: 100%; max-width: 1100px; margin: auto; }}
                        .print-action-area {{ text-align: center; margin-bottom: 20px; }}
                        .action-btn {{ background-color: #2e7d32; border: none; color: white; padding: 12px 30px; text-align: center; text-decoration: none; display: inline-block; font-size: 15px; font-weight: bold; border-radius: 5px; cursor: pointer; box-shadow: 0 2px 4px rgba(0,0,0,0.2); }}
                        .action-btn:hover {{ background-color: #1b5e20; }}
                        .flex-container {{ display: flex; justify-content: space-between; gap: 20px; width: 100%; }}
                        .foil-unit {{ width: 49%; border: 1px solid black; padding: 12px; box-sizing: border-box; background: white; page-break-inside: avoid; }}
                        .top-fields {{ display: flex; justify-content: space-between; font-weight: bold; font-size: 13px; }}
                        .header-box {{ text-align: center; border-top: 2px solid black; border-bottom: 2px solid black; padding: 6px 0; margin-top: 8px; font-weight: bold; font-size: 16px; }}
                        .sub-box {{ border-bottom: 2px solid black; padding: 5px 0; font-size: 12px; font-weight: bold; }}
                        .exam-right {{ text-align: right; }}
                        .marks-info {{ display: flex; justify-content: space-between; padding: 5px 0; font-weight: bold; border-bottom: 2px solid black; font-size: 12px; }}
                        .footer-fields {{ margin-top: 15px; font-size: 12px; font-weight: bold; line-height: 1.8; }}
                        @media print {{ body {{ max-width: 100%; padding: 0; }} .flex-container {{ gap: 10px; }} .print-action-area {{ display: none !important; }} }}
                    </style>
                    </head>
                    <body>
                        <div class="print-action-area"><button class="action-btn" onclick="window.print()">Print Only Foils (Landscape)</button></div>
                        <div class="flex-container">
                            {generate_cce_html_block(left_side_rolls, 1, "FOIL", True)}
                            {generate_cce_html_block(right_side_rolls, 31, "FOIL", len(right_side_rolls) > 0)}
                        </div>
                    </body>
                    </html>
                    """
                    st.components.v1.html(full_html, height=1550, scrolling=False)
                else:
                    st.error("Is Semester ka koi data live list me nahi mila.")
        else:
            st.error("Live database file khali hai.")

        # ----------------------------------------
        # प्ररूप 2: छात्र लाइव सूची देखें (सुरक्षित ग्रिड व्यू + 3 बटन्स)
        # ----------------------------------------
        st.markdown("---")
        st.subheader("Part 2: Students Live Database & Downloads")
        
        st.markdown('<div class="print-hide">', unsafe_allow_html=True)
        visibility_label = "Unhide Student List" if not st.session_state.list_visibility_state else "Hide Student List"
        if st.button(visibility_label, use_container_width=True, type="secondary", key="cce_hide_btn"):
            
    # ==========================================
    # 🛠️ 4. FULL ADMIN ROLE (पूरी तरह फिक्स्ड और सुरक्षित एडमिन कमांड सेंटर)
    # ==========================================
    elif role == "full_admin":
        st.header("Student Live Database List (Admin)")
        
        st.markdown('<div class="print-hide">', unsafe_allow_html=True)
        # लिस्ट को पूरी तरह हाइड / अनहाइड करने का मास्टर बटन
        visibility_label = "Unhide Student List" if not st.session_state.list_visibility_state else "Hide Student List"
        if st.button(visibility_label, use_container_width=True, type="secondary"):
            st.session_state.list_visibility_state = not st.session_state.list_visibility_state
            st.rerun()
        search_query = st.text_input("Student Name ya Roll No. darj karke khojein:")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # यदि लिस्ट को हाइड (Hide) किया गया है
        if not st.session_state.list_visibility_state:
            st.info("Student list ko varpamaan me chhupaya gaya hai. Dekhne ke liye upar Unhide button dabayein.")
            
        else:
            filtered_db = live_db.copy()
            if search_query:
                filtered_db = filtered_db[
                    filtered_db["Student Name"].str.contains(search_query, case=False, na=False) |
                    filtered_db["Roll No."].str.contains(search_query, case=False, na=False)
                ]
            st.write(f"Kul Student Record: **{len(filtered_db)}**")
            
            if not filtered_db.empty:
                st.markdown('<div class="print-hide">### Advanced Admin Command Center</div>', unsafe_allow_html=True)
                
                # मास्टर लॉक / अनलॉक बटन (यह हमेशा स्क्रीन पर रहेगा)
                st.markdown('<div class="print-hide">', unsafe_allow_html=True)
                if st.session_state.admin_lock_state:
                    if st.button("Unlock List (Admin button aur editing chalu karein)", type="primary", use_container_width=True):
                        st.session_state.admin_lock_state = False
                        st.rerun()
                else:
                    if st.button("Lock List (Sabhi admin buttons ko chhupayein aur surakshit karein)", type="secondary", use_container_width=True):
                        st.session_state.admin_lock_state = True
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
                
                # वर्तमान निर्धारित कॉलम ऑर्डर के अनुसार डेटा तैयार करें
                ordered_db = filtered_db[st.session_state.admin_columns_order].copy()
                ordered_db.insert(0, "S.No.", range(1, len(ordered_db) + 1))
                
                # यदि एडमिन पैनल UNLOCK है, तो ही कंट्रोल्स और ऑल सिलेक्ट दिखाएं
                if not st.session_state.admin_lock_state:
                    st.markdown('<div class="print-hide">', unsafe_allow_html=True)
                    target_col = st.selectbox("Aage-piche khiskane ke liye column chunein:", options=st.session_state.admin_columns_order)
                    
                    c_left, c_right = st.columns(2)
                    if c_left.button("Column Shift Left", use_container_width=True):
                        idx = st.session_state.admin_columns_order.index(target_col)
                        if idx > 0:
                            st.session_state.admin_columns_order[idx], st.session_state.admin_columns_order[idx-1] = st.session_state.admin_columns_order[idx-1], st.session_state.admin_columns_order[idx]
                            st.rerun()
                    if c_right.button("Column Shift Right", use_container_width=True):
                        idx = st.session_state.admin_columns_order.index(target_col)
                        if idx < len(st.session_state.admin_columns_order) - 1:
                            st.session_state.admin_columns_order[idx], st.session_state.admin_columns_order[idx+1] = st.session_state.admin_columns_order[idx+1], st.session_state.admin_columns_order[idx]
                            st.rerun()
                    
                    select_all = st.checkbox("Select All Rows (Sabhi row ko ek sath chunein)")
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # सिलेक्ट कॉलम इन्सर्ट करें
                    ordered_db.insert(0, "Select", select_all)
                    
                    # डेटा एडिटर (टेक्स्ट डायरेक्ट एडिट हो सकता है यहाँ)
                    edited_df = st.data_editor(
                        ordered_db,
                        use_container_width=True,
                        disabled=[col for col in ordered_db.columns if col == "Select"],
                        key="advanced_admin_unlocked_editor",
                        hide_index=True
                    )
                    
                    # लाइव एडिटर टेक्स्ट मॉडिफिकेशन सिंक करना
                    clean_edited = edited_df.drop(columns=["Select", "S.No."])
                    for col in clean_edited.columns:
                        live_db.loc[filtered_db.index, col] = clean_edited[col].values
                    save_live_data(live_db)
                    
                    selected_rows = edited_df[edited_df["Select"] == True]
                    
                    st.markdown('<div class="print-hide">', unsafe_allow_html=True)
                    st.info(f"Chayanit row ki sankhya: **{len(selected_rows)}**")
                    if len(selected_rows) > 0:
                        if st.button("Delete Selected Rows (Chayanit row delete karein)", type="primary", use_container_width=True):
                            indices_to_drop = filtered_db.index[[int(s_no) - 1 for s_no in selected_rows["S.No."]]]
                            live_db = live_db.drop(indices_to_drop).reset_index(drop=True)
                            save_live_data(live_db)
                            st.success("Chayanit row safaltapurvak hata di gayi hain!")
                            st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # यदि एडमिन पैनल LOCK है, तो साधारण ग्रिड दिखाएं (कंट्रोल्स छिपे रहेंगे)
                else:
                    st.dataframe(ordered_db, use_container_width=True, hide_index=True)
            else:
                st.warning("Record match nahi hua.")
