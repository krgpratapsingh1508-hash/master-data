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
        [data-testid="stHeader"], div[element-to-hide="true"], .stButton, .stFileUploader, header, footer, [data-testid="stForm"], .print-hide {
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
    # 📁 1. DATA ENTRY ROLE (स्मार्ट ऑटो-क्लियर और ऑटो-हाइड के साथ)
    # ==========================================
    if role == "data_entry":
        st.header("📝 Student Data Entry Panel")
        
        # 🔄 स्मार्ट ऑटो-हाइड ट्रिगर ड्रॉपडाउन (स्विच बटन की तरह काम करेगा)
        entry_method = st.selectbox(
            "⚙️ डेटा एंट्री का माध्यम चुनें (Choose Entry Method):",
            options=["📁 CSV फ़ाइल बल्क अपलोड (Bulk CSV Upload)", "➕ नया छात्र मैनुअल फॉर्म (Manual Form Entry)"]
        )
        st.markdown("---")

        # ----------------------------------------
        # माध्यम ए: केवल CSV अपलोड दिखेगा (मैनुअल फॉर्म हाइड रहेगा)
        # ----------------------------------------
        if entry_method == "📁 CSV फ़ाइल बल्क अपलोड (Bulk CSV Upload)":
            st.subheader("📁 CSV File Bulk Upload")
            
            # 🎯 ऑटो-क्लियर के लिए डायनामिक की (Key) का उपयोग
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
                        if "Admission No." in uploaded_df.columns:
                            uploaded_df = uploaded_df.drop(columns=["Admission No."])
                        current_db = load_live_data()
                        updated_df = uploaded_df if current_db.empty else pd.concat([current_db, uploaded_df], ignore_index=True)
                        save_live_data(updated_df)
                        
                        # 🎯 फ़ाइल को डैशबोर्ड से तुरंत हटाने और स्क्रीन साफ करने का लॉजिक
                        st.session_state.upload_success = True
                        st.session_state.save_success = False
                        st.session_state.csv_uploader_id += 1  # आईडी बदलते ही पुराना अपलोडर स्वतः रीसेट हो जाएगा
                        st.rerun()
                except Exception as e:
                    st.error(f"त्रुटि: {e}")

            if st.session_state.upload_success:
                st.success("✅ CSV Data Complete upload")
                st.session_state.upload_success = False

        # ----------------------------------------
        # माध्यम बी: केवल मैनुअल फॉर्म दिखेगा (CSV अपलोडर हाइड रहेगा)
        # ----------------------------------------
        elif entry_method == "➕ नया छात्र मैनुअल फॉर्म (Manual Form Entry)":
            st.subheader("➕ Naya Student Data Add Karein")
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
                st.success("✅ Student data save successfully")
                st.session_state.save_success = False
    # ==========================================
    # 👁️ 2. LIST VIEWER ROLE (CSV, Landscape PDF और Direct Print बटन्स के साथ)
    # ==========================================
    elif role == "list_viewer":
        st.header("📊 Student Live Database List (Viewer Mode)")
        
        st.markdown('<div class="print-hide">', unsafe_allow_html=True)
        # 👁️ लिस्ट को पूरी तरह हाइड / अनहाइड करने का मास्टर बटन
        visibility_label = "👁️ Unhide Student List" if not st.session_state.list_visibility_state else "🙈 Hide Student List"
        if st.button(visibility_label, use_container_width=True, type="secondary"):
            st.session_state.list_visibility_state = not st.session_state.list_visibility_state
            st.rerun()
            
        search_query = st.text_input("🔍 Student Name या Roll No. दर्ज करके खोजें:")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 🎯 यदि लिस्ट को हाइड (Hide) किया गया है
        if not st.session_state.list_visibility_state:
            st.info("🔒 छात्र सूची को वर्तमान में छुपाया (Hide) गया है। देखने के लिए ऊपर 'Unhide' बटन दबाएं।")
            
        else:
            filtered_db = live_db.copy()
            if search_query:
                filtered_db = filtered_db[
                    filtered_db["Student Name"].str.contains(search_query, case=False, na=False) |
                    filtered_db["Roll No."].str.contains(search_query, case=False, na=False)
                ]
            st.write(f"📋 कुल छात्र रिकॉर्ड: **{len(filtered_db)}**")
            
            # यदि सर्च रिकॉर्ड या डेटाबेस खाली नहीं है
            if not filtered_db.empty:
                # 🎯 S.No. को 1 से सुव्यवस्थित तरीके से सेट करना
                filtered_db.insert(0, "S.No.", range(1, len(filtered_db) + 1))
                
                # सुरक्षित रीड-ओनली टेबल व्यू
                st.dataframe(filtered_db, use_container_width=True, hide_index=True)
                
                # स्वच्छ डाउनलोड फ़ाइल तैयार करना (बिना S.No. के)
                clean_download_df = filtered_db.drop(columns=["S.No."])
                
                # --- 🛠️ बटन अनुभाग (3 अलग-अलग बटन्स का पैनल) ---
                st.markdown('<div class="print-hide">', unsafe_allow_html=True)
                col_btn1, col_btn2, col_btn3 = st.columns(3)
                
                with col_btn1:
                    # बटन 1: डायरेक्ट CSV फाइल डाउनलोड
                    csv_buffer = clean_download_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 डाउनलोड छात्र सूची (CSV)", 
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
                        const doc = new jsPDF('l', 'mm', 'a4'); // 'l' का मतलब Landscape (चौड़ा पन्ना) है
                        
                        doc.text("Permanent Shared Live Database - Student List", 14, 15);
                        
                        const columns = {columns_json};
                        const rows = {rows_json};
                        
                        doc.autoTable({{
                            head: [columns],
                            body: rows,
                            startY: 22,
                            styles: {{ fontSize: 7, cellPadding: 1.5 }},
                            headStyles: {{ fillColor: [255, 87, 51] }}, // संस्थान का नारंगी थीम कलर
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
                    ">📄 डायरेक्ट Landscape PDF डाउनलोड करें</button>
                    """
                    st.markdown(pdf_script, unsafe_allow_html=True)
                    
                with col_btn3:
                    # बटन 3: सीधे हार्डवेयर प्रिंटर पर प्रिंट निकालने का बटन
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
                        ">🖨️ सीधे प्रिंट निकालें (Direct Print)</button>
                    """, unsafe_allow_html=True)
                    
                st.markdown('</div>', unsafe_allow_html=True)
                
            else:
                st.warning("⚠️ रिकॉर्ड मैच नहीं हुआ।")

    # ==========================================
    # 🛠️ 3. FULL ADMIN ROLE (पूरी तरह फिक्स्ड विदाउट इंडेंटेशन एरर)
    # ==========================================
    elif role == "full_admin":
        st.header("📊 Student Live Database List (Admin)")
        
        st.markdown('<div class="print-hide">', unsafe_allow_html=True)
        # 👁️ लिस्ट को पूरी तरह हाइड / अनहाइड करने का मास्टर बटन
        visibility_label = "👁️ Unhide Student List" if not st.session_state.list_visibility_state else "🙈 Hide Student List"
        if st.button(visibility_label, use_container_width=True, type="secondary"):
            st.session_state.list_visibility_state = not st.session_state.list_visibility_state
            st.rerun()
            
        search_query = st.text_input("🔍 Student Name या Roll No. दर्ज करके खोजें:")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 🎯 यदि लिस्ट को हाइड (Hide) किया गया है
        if not st.session_state.list_visibility_state:
            st.info("🔒 छात्र सूची को वर्तमान में छुपाया (Hide) गया है। देखने के लिए ऊपर 'Unhide' बटन दबाएं।")
            
        else:
            filtered_db = live_db.copy()
            if search_query:
                filtered_db = filtered_db[
                    filtered_db["Student Name"].str.contains(search_query, case=False, na=False) |
                    filtered_db["Roll No."].str.contains(search_query, case=False, na=False)
                ]
            st.write(f"📋 कुल छात्र रिकॉर्ड: **{len(filtered_db)}**")
            
            # यदि सर्च रिकॉर्ड या डेटाबेस खाली नहीं है
            if not filtered_db.empty:
                st.markdown('<div class="print-hide">### 🛠️ Advanced Admin Command Center</div>', unsafe_allow_html=True)
                
                # 🔒 मास्टर लॉक / अनलॉक बटन (यह हमेशा स्क्रीन पर रहेगा)
                st.markdown('<div class="print-hide">', unsafe_allow_html=True)
                if st.session_state.admin_lock_state:
                    if st.button("🔓 Unlock List (एडमिन बटन और एडिटिंग चालू करें)", type="primary", use_container_width=True):
                        st.session_state.admin_lock_state = False
                        st.rerun()
                else:
                    if st.button("🔒 Lock List (सभी एडमिन बटन्स को छुपाएं और सुरक्षित करें)", type="secondary", use_container_width=True):
                        st.session_state.admin_lock_state = True
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
                
                # वर्तमान निर्धारित कॉलम ऑर्डर के अनुसार डेटा रेंडर करना
                ordered_db = filtered_db[st.session_state.admin_columns_order].copy()
                ordered_db.insert(0, "S.No.", range(1, len(ordered_db) + 1))
                download_df = filtered_db.copy()
                
                # 🎯 यदि एडमिन पैनल UNLOCK है, तभी सारे कंट्रोल्स और ऑल सिलेक्ट प्रकट करें
                if not st.session_state.admin_lock_state:
                    st.markdown('<div class="print-hide">', unsafe_allow_html=True)
                    target_col = st.selectbox("आगे-पीछे खिसकाने के लिए कॉलम चुनें:", options=st.session_state.admin_columns_order)
                    
                    c_left, c_right = st.columns(2)
                    if c_left.button("⬅️ Column Shift Left", use_container_width=True):
                        idx = st.session_state.admin_columns_order.index(target_col)
                        if idx > 0:
                            st.session_state.admin_columns_order[idx], st.session_state.admin_columns_order[idx-1] = st.session_state.admin_columns_order[idx-1], st.session_state.admin_columns_order[idx]
                            st.rerun()
                    if c_right.button("➡️ Column Shift Right", use_container_width=True):
                        idx = st.session_state.admin_columns_order.index(target_col)
                        if idx < len(st.session_state.admin_columns_order) - 1:
                            st.session_state.admin_columns_order[idx], st.session_state.admin_columns_order[idx+1] = st.session_state.admin_columns_order[idx+1], st.session_state.admin_columns_order[idx]
                            st.rerun()
                    
                    select_all = st.checkbox("✅ Select All Rows (सभी रो को एक साथ चुनें)")
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # सिलेक्ट कॉलम इन्सर्ट करें
                    ordered_db.insert(0, "Select", select_all)
                    
                    # डेटा एडिटर (यहाँ सीधे डबल क्लिक करके लाइव टेक्स्ट एडिट किया जा सकता है)
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
                    st.info(f"🎯 चयनित रो की संख्या: **{len(selected_rows)}**")
                    if len(selected_rows) > 0:
                        if st.button("🗑️ Delete Selected Rows (चयनित रो डिलीट करें)", type="primary", use_container_width=True):
                            indices_to_drop = filtered_db.index[[int(s_no) - 1 for s_no in selected_rows["S.No."]]]
                            live_db = live_db.drop(indices_to_drop).reset_index(drop=True)
                            save_live_data(live_db)
                            st.success("🗑️ चयनित रो सफलतापूर्वक हटा दी गई हैं!")
                            st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                    download_df = edited_df.drop(columns=["Select", "S.No."]) if "Select" in edited_df.columns else edited_df.drop(columns=["S.No."])
                
                # 🎯 यदि एडमिन पैनल LOCK है, तो सारे बटन छिप जाएंगे लेकिन तालिका स्क्रीन पर हमेशा दिखेगी
                else:
                    st.dataframe(ordered_db, use_container_width=True, hide_index=True)
                    download_df = filtered_db.copy()
                
                # कॉमन डाउनलोड और प्रिंट बटन्स पैनल
                st.markdown('<div class="print-hide">', unsafe_allow_html=True)
                col_btn1, col_btn2 = st.columns(2)
                if "S.No." in download_df.columns:
                    download_df = download_df.drop(columns=["S.No."])
                csv_buffer = download_df.to_csv(index=False).encode('utf-8')
                
                col_btn1.download_button(label="📥 डाउनलोड छात्र सूची (CSV)", data=csv_buffer, file_name="student_database_list.csv", mime="text/csv", use_container_width=True)
                col_btn2.markdown('<button onclick="window.print()" style="width: 100%; background-color: #FF5733; color: white; border: none; padding: 0.5rem 1rem; border-radius: 0.5rem; cursor: pointer; font-weight: 500; line-height: 1.6; text-align: center; box-sizing: border-box;">🖨️ प्रिंट या PDF बनाएं</button>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
            else:
                st.warning("⚠️ रिकॉर्ड मैच नहीं हुआ।")
                
