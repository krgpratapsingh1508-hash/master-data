import streamlit as st
import pandas as pd

# पेज का लेआउट सेट करें (चौड़ा व्यू)
st.set_page_config(layout="wide")

# 1. डेटा स्टोरेज (Session State का उपयोग करके, ताकि पेज रीफ्रेश होने पर डेटा न उड़े)
if "student_db" not in st.session_state:
    # शुरुआती खाली डेटाबेस (कॉलम के नाम आपके इमेज के अनुसार हैं)
    columns = [
        "Admission No.", "Eligibility", "Unique ID", "Roll No.", 
        "Application No.", "Enrollment No.", "Student Name", "Father Name",
        "Mother Name", "Date of Birth", "Category", "Subject", 
        "Duration", "Mobile No.", "Email ID", "Address"
    ]
    st.session_state.student_db = pd.DataFrame(columns=columns)

# मुख्य टाइटल
st.title("Student Database Portal")

# --- सेक्शन 1: CSV फ़ाइल से बल्क डेटा अपलोड करें ---
st.header("📁 CSV File Se Bulk Data Upload Karein")
uploaded_file = st.file_uploader("CSV फ़ाइल चुनें", type=["csv"])

if uploaded_file is not None:
    try:
        # CSV फ़ाइल को पढ़ें
        uploaded_df = pd.read_csv(uploaded_file)
        
        # 'Upload CSV' बटन दबाने पर डेटा जोड़ें
        if st.button("Upload CSV", type="primary"):
            # अपलोड किए गए डेटा को मौजूदा डेटाबेस में मिलाएं
            st.session_state.student_db = pd.concat([st.session_state.student_db, uploaded_df], ignore_index=True)
            st.success("CSV डेटा सफलतापूर्वक जोड़ दिया गया है!")
    except Exception as e:
        st.error(f"फ़ाइल पढ़ने में त्रुटि: {e}")


# --- सेक्शन 2: नया स्टूडेंट डेटा मैनुअली ऐड करें ---
st.header("➕ Naya Student Data Add Karein")

# 4x4 ग्रिड (कॉलम) में इनपुट फ़ील्ड्स व्यवस्थित करना
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

# 'Save Student Data' बटन
if st.button("Save Student Data", use_container_width=True):
    # नया डेटा रो (Row) तैयार करें
    new_data = {
        "Admission No.": adm_no, "Eligibility": eligibility, "Unique ID": unique_id, "Roll No.": roll_no,
        "Application No.": app_no, "Enrollment No.": enr_no, "Student Name": s_name, "Father Name": f_name,
        "Mother Name": m_name, "Date of Birth": dob, "Category": category, "Subject": subject,
        "Duration": duration, "Mobile No.": mobile, "Email ID": email, "Address": address
    }
    
    # डेटाबेस में जोड़ें
    st.session_state.student_db = pd.concat([st.session_state.student_db, pd.DataFrame([new_data])], ignore_index=True)
    st.success("नया स्टूडेंट डेटा सुरक्षित कर लिया गया है!")


# --- सेक्शन 3: लाइव स्टूडेंट डेटाबेस तालिका ---
st.header("📊 Live Student Database")

# इंडेक्स (S. No.) को 1 से शुरू करने के लिए व्यवस्थित करना
display_df = st.session_state.student_db.copy()
display_df.index = display_df.index + 1
display_df.index.name = "S. No."

# टेबल प्रदर्शित करें
st.dataframe(display_df, use_container_width=True)


# --- सेक्शन 4: प्रिंट और डाउनलोड विकल्प ---
st.header("📥 Actions")
action_col1, action_col2 = st.columns(2)

with action_col1:
    # CSV डाउनलोड बटन
    csv_data = st.session_state.student_db.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Database as CSV",
        data=csv_data,
        file_name="student_database.csv",
        mime="text/csv",
        use_container_width=True
    )

with action_col2:
    # प्रिंट करने के लिए आसान जावास्क्रिप्ट ट्रिक बटन
    st.markdown(
        '<button onclick="window.print()" style="width:100%; height:38px; background-color:#ff4b4b; color:white; border:none; border-radius:4px; cursor:pointer;">Print Page / Save as PDF</button>', 
        unsafe_allow_html=True
    )