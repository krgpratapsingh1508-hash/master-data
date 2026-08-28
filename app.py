import streamlit as st
import pandas as pd
import sqlite3

# पेज का लेआउट सेट करें
st.set_page_config(layout="wide")

# --- डेटाबेस सेटअप (SQLite) ---
# यह आपके कंप्यूटर में 'students.db' नाम की परमानेंट फ़ाइल बना देगा
DB_FILE = "students.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admission_no TEXT, eligibility TEXT, unique_id TEXT, roll_no TEXT,
            application_no TEXT, enrollment_no TEXT, student_name TEXT, father_name TEXT,
            mother_name TEXT, dob TEXT, category TEXT, subject TEXT,
            duration TEXT, mobile TEXT, email TEXT, address TEXT
        )
    ''')
    conn.commit()
    conn.close()

# डेटाबेस लोड करना
init_db()

# डेटाबेस से डेटा पढ़ने का फंक्शन
def fetch_data():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM students", conn)
    conn.close()
    return df

# मुख्य टाइटल
st.title("Permanent Student Database Portal")

# --- सेक्शन 1: CSV फ़ाइल से बल्क डेटा अपलोड करें ---
st.header("📁 CSV File Se Bulk Data Upload Karein")
uploaded_file = st.file_uploader("CSV फ़ाइल चुनें", type=["csv"])

if uploaded_file is not None:
    try:
        uploaded_df = pd.read_csv(uploaded_file)
        if st.button("Upload CSV", type="primary"):
            conn = sqlite3.connect(DB_FILE)
            # CSV के कॉलम नामों को डेटाबेस के कॉलम से मैच कराने के लिए रीनेम करें (यदि ज़रूरी हो)
            # यहाँ माना गया है कि CSV के कॉलम नाम और नीचे दिए फॉर्म के नाम एक जैसे हैं
            db_columns = [
                "admission_no", "eligibility", "unique_id", "roll_no",
                "application_no", "enrollment_no", "student_name", "father_name",
                "mother_name", "dob", "category", "subject",
                "duration", "mobile", "email", "address"
            ]
            
            # यदि CSV में कम या ज़्यादा कॉलम हैं तो उसे व्यवस्थित करें
            for col in db_columns:
                if col not in uploaded_df.columns:
                    uploaded_df[col] = ""
                    
            final_upload_df = uploaded_df[db_columns]
            final_upload_df.to_sql("students", conn, if_exists="append", index=False)
            conn.close()
            st.success("CSV डेटा स्थायी रूप से डेटाबेस में जोड़ दिया गया है!")
            st.rerun() # पेज रीफ्रेश करें ताकि डेटा तुरंत दिखे
    except Exception as e:
        st.error(f"फ़ाइल अपलोड करने में खराबी: {e}")


# --- सेक्शन 2: नया स्टूडेंट डेटा मैनुअली ऐड करें ---
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
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO students (
                admission_no, eligibility, unique_id, roll_no,
                application_no, enrollment_no, student_name, father_name,
                mother_name, dob, category, subject,
                duration, mobile, email, address
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (adm_no, eligibility, unique_id, roll_no, app_no, enr_no, s_name, f_name, m_name, dob, category, subject, duration, mobile, email, address))
        conn.commit()
        conn.close()
        st.success("डेटा सुरक्षित रूप से सेव हो गया है!")
        st.rerun()


# --- डेटाबेस लोड करें ---
df_current = fetch_data()


# --- सेक्शन 3: डेटा डिलीट करने का विकल्प ---
st.header("🗑️ Delete Student Data")
if not df_current.empty:
    # डिलीट करने के लिए छात्र चुनने का ड्रॉपडाउन (ID और Name के साथ)
    student_list = df_current.apply(lambda row: f"ID: {row['id']} | {row['student_name']} (Roll: {row['roll_no']})", axis=1).tolist()
    selected_student_string = st.selectbox("डिलीट करने के लिए स्टूडेंट चुनें:", ["-- चुनें --"] + student_list)
    
    if selected_student_string != "-- चुनें --":
        # चुनी गई स्ट्रिंग से ID निकालना
        selected_id = int(selected_student_string.split(" | ")[0].split(": ")[1])
        
        if st.button("चयनित स्टूडेंट का डेटा डिलीट करें", type="primary"):
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM students WHERE id = ?", (selected_id,))
            conn.commit()
            conn.close()
            st.success("डेटा सफलतापूर्वक डिलीट कर दिया गया है!")
            st.rerun()
else:
    st.info("डेटाबेस अभी खाली है।")


# --- सेक्शन 4: लाइव स्टूडेंट डेटाबेस तालिका ---
st.header("📊 Live Student Database")

if not df_current.empty:
    # कॉलम के नाम यूज़र इंटरफ़ेस के लिए सुंदर बनाना
    display_df = df_current.copy()
    display_df.columns = [
        "S. No. (DB ID)", "Admission No.", "Eligibility", "Unique ID", "Roll No.", 
        "Application No.", "Enrollment No.", "Student Name", "Father Name",
        "Mother Name", "Date of Birth", "Category", "Subject", 
        "Duration", "Mobile No.", "Email ID", "Address"
    ]
    st.dataframe(display_df, use_container_width=True, hide_index=True)
else:
    st.write("दिखाने के लिए कोई डेटा उपलब्ध नहीं है।")


# --- सेक्शन 5: प्रिंट और डाउनलोड विकल्प ---
st.header("📥 Actions")
action_col1, action_col2 = st.columns(2)

with action_col1:
    if not df_current.empty:
        # डाउनलोड के लिए क्लीन CSV फाइल (बिना आंतरिक ID के)
        download_df = df_current.drop(columns=["id"])
        csv_data = download_df.to_csv(index=False).encode('utf-8')
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
