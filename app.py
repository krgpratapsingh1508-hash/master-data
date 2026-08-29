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

# ==========================================
# 🛠️ फ़ंक्शन: डेटा टेबल और बटन रेंडरर (एरर-फ्री क्लोजर)
# ==========================================
def render_data_table(filtered_db, role):
    filtered_db.insert(0, "S.No.", range(1, len(filtered_db) + 1))
    download_df = filtered_db.copy()
    global live_db
    
    # --- FULL ADMIN मोड लॉजिक ---
    if role == "full_admin":
        st.markdown('<div class="print-hide">### 🛠️ Advanced Admin Command Center</div>', unsafe_allow_html=True)
        
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
        
        if not st.session_state.admin_lock_state:
            st.markdown('<div class="print-hide">', unsafe_allow_html=True)
            target_col = st.selectbox("आगे-पीछे खिसकाने के लिए कॉलम चुनें (Select Column):", options=st.session_state.admin_columns_order)
            
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
            
            ordered_db = filtered_db[st.session_state.admin_columns_order].copy()
            ordered_db.insert(0, "S.No.", range(1, len(ordered_db) + 1))
            ordered_db.insert(0, "Select", select_all)
            
            edited_df = st.data_editor(
                ordered_db,
                use_container_width=True,
                disabled=[col for col in ordered_db.columns if col == "Select"],
                key="advanced_admin_unlocked_editor",
                hide_index=True
            )
            
            clean_edited = edited_df.drop(columns=["Select", "S.No."])
            for col in clean_edited.columns:
                live_db.loc[filtered_db.index - 1, col] = clean_edited[col].values
            save_live_data(live_db)
            
            selected_rows = edited_df[edited_df["Select"] == True]
            
            st.markdown('<div class="print-hide">', unsafe_allow_html=True)
            st.info(f"🎯 चयनित रो की संख्या: **{len(selected_rows)}**")
            if len(selected_rows) > 0:
                if st.button("🗑️ Delete Selected Rows (चयनित रो डिलीट करें)", type="primary", use_container_width=True):
                    indices_to_drop = filtered_db.index[[int(s_no) - 1 for s_no in selected_rows["S.No."]]] - 1
                    live_db = live_db.drop(indices_to_drop).reset_index(drop=True)
                    save_live_data(live_db)
                    st.success("🗑️ चयनित रो सफलतापूर्वक हटा दी गई हैं!")
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            download_df = edited_df.drop(columns=["Select", "S.No."]) if "Select" in edited_df.columns else edited_df.drop(columns=["S.No."])
        else:
            locked_admin_db = filtered_db[st.session_state.admin_columns_order].copy()
            locked_admin_db.insert(0, "S.No.", range(1, len(locked_admin_db) + 1))
            st.dataframe(locked_admin_db, use_container_width=True, hide_index=True)
            download_df = filtered_db.copy()
            
    # --- LIST VIEWER मोड ---
    else:
        viewer_db = filtered_db.copy()
        viewer_db.insert(0, "S.No.", range(1, len(viewer_db) + 1))
        st.dataframe(viewer_db, use_container_width=True, hide_index=True)
        download_df = filtered_db.copy()
        
    # --- एक्शन बटन्स पैनल ---
    st.markdown('<div class="print-hide">', unsafe_allow_html=True)
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if "S.No." in download_df.columns:
            download_df = download_df.drop(columns=["S.No."])
        csv_buffer = download_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 डाउनलोड छात्र सूची (Download as CSV)",
            data=csv_buffer,
            file_name="student_database_list.csv",
            mime="text/csv",
            use_container_width=True
        )
    with col_btn2:
        st.markdown("""
            <button onclick="window.print()" style="
                width: 100%; background-color: #FF5733; color: white; border: none;
                padding: 0.5rem 1rem; border-radius: 0.5rem; cursor: pointer;
                font-weight: 500; line-height: 1.6; text-align: center; box-sizing: border-box;
            ">🖨️ प्रिंट या PDF बनाएं (Print / Save as PDF)</button>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# --- लॉगिन गेटवे चेक ---
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
            
