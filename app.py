import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# पेज का लेआउट सेट करें
st.set_page_config(layout="wide")

st.title("Permanent Google Sheets Linked Database")

# आपकी असली गूगल शीट का लिंक
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1Uoeucj2Ayi8mpvBe4T5LlVII_o2PyJg_OrvPxWjIf68/edit?usp=sharing"

# गूगल शीट से कनेक्शन स्थापित करना
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # लाइव डेटा लोड करें (ttl=0 का मतलब हर बार ताजा डेटा आएगा, पुराना कैश नहीं दिखेगा)
    df_current = conn.read(spreadsheet=GOOGLE_SHEET_URL, ttl=0)
except Exception as e:
    st.error(f"Google Sheet से कनेक्ट करने में समस्या: {e}")
    # बैकअप खाली ढांचा अगर शीट लोड न हो
    columns = [
        "Admission No.", "Eligibility", "Unique ID", "Roll No.", 
        "Application No.", "Enrollment No.", "Student Name", "Father Name",
        "Mother Name", "Date of Birth", "Category", "Subject", 
        "Duration", "Mobile No.", "Email ID", "Address"
    ]
    df_current = pd.DataFrame(columns=columns)

# अगर शीट पूरी तरह खाली है तो उसे सही कॉलम नाम दें
if df_current.empty or len(df_current.columns) < 2:
    df_current = pd.DataFrame(columns=[
        "Admission No.", "Eligibility", "Unique ID", "Roll No.", 
        "Application No.", "Enrollment No.", "Student Name", "Father Name",
        "Mother Name", "Date of Birth", "Category", "Subject", 
        "Duration", "Mobile No.", "Email ID", "Address"
    ])

# --- सेक्शन 1: CSV फ़ाइल से बल्क डेटा अपलोड करें ---
st.header("📁 CSV File Se Bulk Data Upload Karein")
uploaded_file = st.file_uploader("CSV फ़ाइल चुनें", type=["csv"])

if uploaded_file is not None:
    try:
        uploaded_df = pd.read_csv(uploaded_file)
        if st.button("Upload CSV", type="primary"):
            # नया डेटा मौजूदा डेटा में जोड़ें
            updated_df = pd.concat([df_current, uploaded_df], ignore_index=True)
            # गूगल शीट में अपडेट करें
            conn.update(spreadsheet=GOOGLE_SHEET_URL, data=updated_df)
            st.success("CSV डेटा सफलतापूर्वक Google Sheet में सेव हो गया है!")
            st.rerun()
    except Exception as e:
        st.error(f"CSV फ़ाइल पढ़ने में त्रुटि: {e}")


# --- SECTION 2: नया स्टूडेंट डेटा मैनुअली ऐड करें ---
st.header("➕ Naya Student Data Add Karein")

col1, col2, col3, col4 = st.columns(4)

with col1:
    adm_no = st.text_input("Admission No.")
    app_no = st.text_input("Application No.")
    m_name = st.text_input("Mother Name")
    duration = st.text_input("Duration")

with col2:
    eligibility = st.text_input("Eligibility")
    enr_no = st.text_input("Enrollment No.")
    dob = st.text_input("Date of Birth")
    mobile = st.text_input("Mobile No.")

with col3:
    unique_id = st.text_input("Unique ID")
    s_name = st.text_input("Student Name")
    category = st.text_input("Category")
    email = st.text_input("Email ID")

with col4:
    roll_no = st.text_input("Roll No.")
    f_name = st.text_input("Father Name")
    subject = st.text_input("Subject")
    address = st.text_input("Address")

if st.button("Save Student Data", use_container_width=True):
    if s_name.strip() == "":
        st.warning("कृपया कम से कम Student Name ज़रूर भरें।")
    else:
        # नया डेटा रो (Row) तैयार करें
        new_row = {
            "Admission No.": adm_no, "Eligibility": eligibility, "Unique ID": unique_id, "Roll No.": roll_no,
            "Application No.": app_no, "Enrollment No.": enr_no, "Student Name": s_name, "Father Name": f_name,
            "Mother Name": m_name, "Date of Birth": dob, "Category": category, "Subject": subject,
            "Duration": duration, "Mobile No.": mobile, "Email ID": email, "Address": address
        }
        
        # नए रो को मौजूदा डेटाफ़्रेम में जोड़ें
        updated_df = pd.concat([df_current, pd.DataFrame([new_row])], ignore_index=True)
        # गूगल शीट में परमानेंट राइट (Write) करें
        conn.update(spreadsheet=GOOGLE_SHEET_URL, data=updated_df)
        st.success("डेटा स्थायी रूप से आपकी Google Sheet में सेव हो गया है!")
        st.rerun()


# --- सेक्शन 3: डेटा डिलीट करने का विकल्प ---
st.header("🗑️ Delete Student Data")
if not df_current.empty and "Student Name" in df_current.columns:
    # डिलीट करने के लिए छात्रों की सूची (Index नंबर के साथ ताकि सही छात्र डिलीट हो)
    student_list = df_current.apply(lambda row: f"Index {row.name} | {row['Student Name']} (Roll: {row['Roll No.']})", axis=1).tolist()
    selected_student_string = st.selectbox("डिलीट करने के लिए स्टूडेंट चुनें:", ["-- चुनें --"] + student_list)
    
    if selected_student_string != "-- चुनें --":
        # चुनी गई स्ट्रिंग से इंडेक्स नंबर निकालना
        selected_idx = int(selected_student_string.split(" | ")[0].split(" ")[1])
        
        if st.button("चयनित स्टूडेंट का डेटा डिलीट करें", type="primary"):
            # उस इंडेक्स वाली रो को ड्रॉप करें
            updated_df = df_current.drop(index=selected_idx).reset_index(drop=True)
            # गूगल शीट को अपडेट करें
            conn.update(spreadsheet=GOOGLE_SHEET_URL, data=updated_df)
            st.success("डेटा Google Sheet से हमेशा के लिए डिलीट कर दिया गया है!")
            st.rerun()
else:
    st.info("डेटाबेस अभी खाली है।")


# --- सेक्शन 4: लाइव स्टूडेंट डेटाबेस तालिका ---
st.header("📊 Live Student Database (Google Sheets)")

if not df_current.empty:
    display_df = df_current.copy()
    display_df.index = display_df.index + 1
    display_df.index.name = "S. No."
    st.dataframe(display_df, use_container_width=True)
else:
    st.write("दिखाने के लिए कोई डेटा उपलब्ध नहीं है।")


# --- सेक्शन 5: प्रिंट और डाउनलोड विकल्प ---
st.header("📥 Actions")
action_col1, action_col2 = st.columns(2)

with action_col1:
    if not df_current.empty:
        csv_data = df_current.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Database as CSV",
            data=csv_data,
            file_name="student_database.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.button("Download Database as CSV", disabled=True, use_container_width=True)

with action_col2:
    st.markdown(
        '<button onclick="window.print()" style="width:100%; height:38px; background-color:#ff4b4b; color:white; border:none; border-radius:4px; cursor:pointer;">Print Page / Save as PDF</button>', 
        unsafe_allow_html=True
    )
