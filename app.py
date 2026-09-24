import streamlit as st
import pandas as pd
import os
import re
import io
import json
import time
from datetime import datetime

# ==========================================================
# ⚙️ STEP 1: PAGE CONFIG
# ==========================================================
st.set_page_config(layout="wide", page_title="Department Approval & Assignment System")

# ==========================================================
# 📁 FILE PATHS (Permanent Local Storage)
# ==========================================================
DB_FILE = "approval_workflow_database.csv"
CRED_FILE = "approval_workflow_credentials.json"
DEPT_FILE = "approval_workflow_departments.json"
FACULTY_FILE = "approval_workflow_faculty.csv"

# ==========================================================
# 🧾 COLUMN SCHEMA
# (Business columns — jitne columns chahiye utne yahan add/remove kiye ja sakte hain.
#  Print/Export ke waqt inme se koi bhi columns chune ja sakte hain — us par koi restriction nahi.)
# ==========================================================
DEFAULT_COLUMNS = [
    "Admission Year", "Admission Session", "Eligibility Name", "Admission Application Number",
    "Admission Date", "Unique ID", "Roll No.", "Application Enrollment No.",
    "Enrollment No.", "Student Name", "Father Name", "Mother Name", "Date of Birth",
    "Category", "Subject Code", "Subject", "Duration", "Mobile Number", "Email ID", "Address", "Status2",
    "Current Year", "Student Abc Id", "Gender", "Admission Category", "Degree",
    "Branch", "Minor Subjects", "Vocational Subjects", "MDC Subjects", "PW/Ap/CE Subjects",
    "Admission & Enrollment Fees", "Scholarship Name", "Remarks"
]

# System / workflow columns — inhe app khud manage karti hai, user in par bharosa kare
SYSTEM_COLUMNS = ["Status", "Assigned Department", "Submitted By", "Submitted On", "Approved By", "Approved On"]
ALL_COLUMNS = DEFAULT_COLUMNS + SYSTEM_COLUMNS

DEFAULT_DEPARTMENTS = ["Examination Department", "Accounts Department", "Scholarship Department", "Registrar Office"]

DEFAULT_CREDENTIALS = {
    "admin": {"password": "admin123", "role": "admin", "label": "👑 Super Admin (P1–P6 Full Control)"}
}

# ==========================================================
# 📦 STEP 2: LOAD / SAVE HELPERS
# ==========================================================

def load_db():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE, dtype=str).fillna("")
        except Exception:
            df = pd.DataFrame(columns=ALL_COLUMNS)
    else:
        df = pd.DataFrame(columns=ALL_COLUMNS)
    for c in ALL_COLUMNS:
        if c not in df.columns:
            df[c] = ""
    return df[ALL_COLUMNS]


def save_db(df):
    df.to_csv(DB_FILE, index=False)


def load_credentials():
    if os.path.exists(CRED_FILE):
        try:
            with open(CRED_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return dict(DEFAULT_CREDENTIALS)


def save_credentials(creds):
    with open(CRED_FILE, "w", encoding="utf-8") as f:
        json.dump(creds, f, ensure_ascii=False, indent=4)


def load_departments():
    if os.path.exists(DEPT_FILE):
        try:
            with open(DEPT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return list(DEFAULT_DEPARTMENTS)


def save_departments(depts):
    with open(DEPT_FILE, "w", encoding="utf-8") as f:
        json.dump(depts, f, ensure_ascii=False, indent=4)


FACULTY_COLUMNS = ["Department", "Faculty Name", "Designation", "Mobile Number", "Number of Students"]


def load_faculty():
    if os.path.exists(FACULTY_FILE):
        try:
            df = pd.read_csv(FACULTY_FILE, dtype=str).fillna("")
        except Exception:
            df = pd.DataFrame(columns=FACULTY_COLUMNS)
    else:
        df = pd.DataFrame(columns=FACULTY_COLUMNS)
    for c in FACULTY_COLUMNS:
        if c not in df.columns:
            df[c] = ""
    return df[FACULTY_COLUMNS]


def save_faculty(df):
    df.to_csv(FACULTY_FILE, index=False)


# ==========================================================
# 🔄 UNIVERSAL UPLOAD CONVERTER (P1 style): CSV / XLSX / असली-पुराना XLS /
# Excel-XML / HTML "fake xls" — सब कुछ एक साफ़ DataFrame में
# फ़ाइल का असली type extension से नहीं, अंदर के content (signature) से पहचाना जाता है।
# ==========================================================

def _clean_raw_table(raw):
    """खाली rows/columns हटाओ, ऊपर के title-rows छोड़ो, सही header row ढूंढो।"""
    raw = raw.fillna("").astype(str).apply(lambda col: col.str.strip())
    raw = raw.loc[:, (raw != "").any(axis=0)]
    raw = raw.loc[(raw != "").any(axis=1)].reset_index(drop=True)
    if raw.empty:
        return pd.DataFrame()
    counts = (raw != "").sum(axis=1)
    hdr = int(counts[counts >= max(1, counts.max() * 0.5)].index[0])
    header = [h if h else f"Unnamed_{i}" for i, h in enumerate(raw.iloc[hdr].tolist())]
    body = raw.iloc[hdr + 1:].reset_index(drop=True)
    body.columns = header
    return body


def _best_frame(frames):
    """कई sheets/tables में से सबसे ज़्यादा data वाली चुनो।"""
    best, best_cells = pd.DataFrame(), 0
    for f in frames:
        cleaned = _clean_raw_table(f)
        cells = cleaned.shape[0] * cleaned.shape[1]
        if cells > best_cells:
            best, best_cells = cleaned, cells
    return best


_UPLOAD_DIAG = {"info": ""}


def _decode_text(raw):
    for enc in ("utf-8-sig", "utf-16", "cp1252", "latin-1"):
        try:
            return raw.decode(enc), enc
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1", errors="ignore"), "latin-1"


def _parse_spreadsheetml(text):
    """Excel 2003 'XML Spreadsheet' (.xls नाम से save हुई XML फ़ाइल)।"""
    import xml.etree.ElementTree as ET
    root = ET.fromstring(text.encode("utf-8"))
    frames = []
    for ws in root.iter():
        if ws.tag.split("}")[-1] != "Worksheet":
            continue
        rows = []
        for row in ws.iter():
            if row.tag.split("}")[-1] != "Row":
                continue
            cells = []
            for cell in row:
                if cell.tag.split("}")[-1] != "Cell":
                    continue
                idx = None
                for k, v in cell.attrib.items():
                    if k.split("}")[-1] == "Index":
                        idx = int(v)
                if idx:
                    cells += [""] * (idx - 1 - len(cells))
                data = next((d for d in cell if d.tag.split("}")[-1] == "Data"), None)
                cells.append("".join(data.itertext()) if data is not None else "")
            rows.append(cells)
        if rows:
            width = max(len(r) for r in rows)
            frames.append(pd.DataFrame([r + [""] * (width - len(r)) for r in rows]))
    return frames


def _parse_delimited_text(raw):
    text, enc = _decode_text(raw)
    first = "\n".join(text.splitlines()[:20])
    seps = {"\t": first.count("\t"), ",": first.count(","), ";": first.count(";"), "|": first.count("|")}
    sep = max(seps, key=seps.get)
    df_t = pd.read_csv(io.StringIO(text), sep=sep, engine="python", dtype=str,
                        header=None, on_bad_lines="skip")
    return [df_t]


def read_uploaded_table(uploaded_file):
    """CSV/XLSX/असली पुराना XLS/Excel-XML/HTML "fake xls" — किसी भी फ़ॉर्मेट की फ़ाइल को
    एक साफ़ DataFrame (सब text) में बदलता है। कई college/university software 'Excel' export
    करते वक़्त असल में xlsx, या HTML table, या XML file को ही .xls नाम दे देते हैं —
    इसलिए extension पर भरोसा करने के बजाय फ़ाइल के असली binary content से type पहचाना जाता है।
    """
    name = uploaded_file.name.lower()
    raw = uploaded_file.getvalue()

    if name.endswith(".csv"):
        for enc in ("utf-8-sig", "cp1252", "latin-1"):
            try:
                df = pd.read_csv(io.BytesIO(raw), dtype=str, encoding=enc).fillna("")
                if not df.empty:
                    return df
            except UnicodeDecodeError:
                continue
            except pd.errors.EmptyDataError:
                return pd.DataFrame()
        return pd.DataFrame()

    if not name.endswith((".xlsx", ".xls", ".xlsm")):
        return pd.DataFrame()

    head = raw[:8192].lstrip()
    head_l = head.lower()
    frames, kind = [], "unknown"
    try:
        if raw[:4] == b"PK\x03\x04":                                          # असली .xlsx
            kind = "xlsx"
            frames = list(pd.read_excel(io.BytesIO(raw), engine="openpyxl", dtype=str,
                                         header=None, sheet_name=None).values())
        elif raw[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":                   # असली पुराना .xls
            kind = "xls"
            try:
                frames = list(pd.read_excel(io.BytesIO(raw), engine="xlrd", dtype=str,
                                             header=None, sheet_name=None).values())
            except ImportError:
                raise ValueError(
                    "यह पुराने फ़ॉर्मेट (.xls) की असली Excel फ़ाइल है, इसे पढ़ने के लिए सर्वर पर "
                    "'xlrd' पैकेज इंस्टॉल होना ज़रूरी है (pip install xlrd)।"
                )
        elif b"urn:schemas-microsoft-com:office:spreadsheet" in raw[:8192]:    # Excel 2003 XML
            kind = "spreadsheetml-xml"
            frames = _parse_spreadsheetml(_decode_text(raw)[0])
        elif head_l.startswith(b"<") or b"<table" in head_l:                  # HTML वाली "fake xls"
            kind = "html"
            text = _decode_text(raw)[0]
            for t in pd.read_html(io.StringIO(text)):
                if not isinstance(t.columns, pd.RangeIndex):
                    hdr_row = [str(c[-1] if isinstance(c, tuple) else c) for c in t.columns]
                    t = pd.concat([pd.DataFrame([hdr_row]),
                                   t.set_axis(range(t.shape[1]), axis=1).astype(str)], ignore_index=True)
                frames.append(t)
        else:                                                                  # plain CSV/TSV text
            kind = "text"
            frames = _parse_delimited_text(raw)
    except Exception as parse_err:
        _UPLOAD_DIAG["info"] = f"type={kind}, size={len(raw)} bytes, parse error: {parse_err}"
        raise ValueError(
            f"फ़ाइल पढ़ने में समस्या (पहचाना गया type: {kind}): {parse_err}. कृपया फ़ाइल को Excel/किसी "
            f"भी spreadsheet software में खोलकर 'Save As' → .xlsx फ़ॉर्मेट में दोबारा Save करें।"
        )

    df_x = _best_frame(frames)
    preview = raw[:120].decode("latin-1", errors="replace").replace("\n", " ").replace("\r", " ")
    _UPLOAD_DIAG["info"] = (f"type={kind}, size={len(raw)} bytes, sheets/tables={len(frames)}, "
                             f"rows x cols after cleanup={df_x.shape}, file start: {preview!r}")
    return df_x


# ==========================================================
# 🧠 SMART COLUMN MATCHING: अपलोड फ़ाइल के headers अलग-अलग तरीकों से लिखे हो सकते
# हैं (जैसे "DOB", "Email", "Mobile No", "Scholarship") — इन्हें सही internal
# column नाम से automatically match करके डेटा गायब होने से बचाता है।
# ==========================================================

def _normalize_col_name(name):
    return re.sub(r"[^a-z0-9]", "", str(name).strip().lower())


MANUAL_COLUMN_ALIASES = {
    "enrollmentno": "Enrollment No.", "enrollmentnumber": "Enrollment No.",
    "enrollmentnum": "Enrollment No.", "universityenrollmentno": "Enrollment No.",
    "applicationenrollmentno": "Application Enrollment No.",
    "dob": "Date of Birth", "dateofbirth": "Date of Birth", "birthdate": "Date of Birth",
    "email": "Email ID", "emailid": "Email ID", "emailaddress": "Email ID", "mailid": "Email ID",
    "mobile": "Mobile Number", "mobileno": "Mobile Number", "mobilenumber": "Mobile Number",
    "phone": "Mobile Number", "phonenumber": "Mobile Number", "contactno": "Mobile Number",
    "scholarship": "Scholarship Name", "scholarshipname": "Scholarship Name",
    "scholarshiptitle": "Scholarship Name",
    "rollno": "Roll No.", "rollnumber": "Roll No.",
    "studentname": "Student Name", "name": "Student Name",
    "fathername": "Father Name", "mothername": "Mother Name",
    "applicationno": "Admission Application Number", "applicationnumber": "Admission Application Number",
    "admissionno": "Admission Application Number", "admissionapplicationno": "Admission Application Number",
    "uniqueid": "Unique ID", "abcid": "Student Abc Id", "studentabcid": "Student Abc Id",
    "admissiondate": "Admission Date", "admissionyear": "Admission Year",
    "admissionsession": "Admission Session", "subjectcode": "Subject Code",
    "currentyear": "Current Year", "admissioncategory": "Admission Category",
    "paymentdate": "Admission Date",
}


def smart_align_columns(df):
    normalized_lookup = {}
    for internal_col in DEFAULT_COLUMNS:
        normalized_lookup[_normalize_col_name(internal_col)] = internal_col
    for alias_key, alias_target in MANUAL_COLUMN_ALIASES.items():
        normalized_lookup.setdefault(alias_key, alias_target)

    rename_map = {}
    for col in df.columns:
        if col in DEFAULT_COLUMNS:
            continue
        key = _normalize_col_name(col)
        if key in normalized_lookup:
            target = normalized_lookup[key]
            if target in df.columns:
                continue
            rename_map[col] = target
    if rename_map:
        df = df.rename(columns=rename_map)
    return df


# ==========================================================
# 🔐 SESSION STATE INIT
# ==========================================================
if "user_role" not in st.session_state:
    st.session_state.user_role = None
if "username" not in st.session_state:
    st.session_state.username = None
if "user_department" not in st.session_state:
    st.session_state.user_department = None
if "credentials" not in st.session_state:
    st.session_state.credentials = load_credentials()
if "departments" not in st.session_state:
    st.session_state.departments = load_departments()

# ==========================================================
# 🎨 STEP 3: THEME CSS (Navy + Gold institutional theme)
# ==========================================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@500;600;700&family=Inter:wght@400;500;600;700&display=swap');

    :root {
        --pg-navy: #0F2A4A;
        --pg-navy-light: #1D4A7A;
        --pg-gold: #C9973F;
        --pg-gold-dark: #A97A25;
        --pg-bg: #F5F7FA;
        --pg-surface: #FFFFFF;
        --pg-border: #DCE3EC;
        --pg-text: #1B2430;
    }

    [data-testid="stAppViewContainer"], .main, body {
        background: var(--pg-bg) !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
        color: var(--pg-text) !important;
    }
    [data-testid="stHeader"] { background: transparent !important; }
    .block-container { padding-top: 2rem !important; }

    h1, h2, h3, h4 {
        font-family: 'Poppins', 'Inter', sans-serif !important;
        color: var(--pg-navy) !important;
        font-weight: 600 !important;
    }
    .stMarkdown h1, .stMarkdown h2, div[data-testid="stHeadingWithActionElements"] h1,
    div[data-testid="stHeadingWithActionElements"] h2 {
        display: inline-block; padding-bottom: 6px;
        border-bottom: 3px solid var(--pg-gold); margin-bottom: 16px !important;
    }

    .stButton > button, .stDownloadButton > button {
        border-radius: 8px !important; font-weight: 600 !important;
        padding: 0.55rem 1.2rem !important;
        transition: transform 0.12s ease, box-shadow 0.12s ease !important;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--pg-navy) 0%, var(--pg-navy-light) 100%) !important;
        border: none !important; color: #fff !important;
    }
    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 4px 14px rgba(15,42,74,0.30) !important; transform: translateY(-1px);
    }
    .stButton > button[kind="secondary"] {
        background: var(--pg-surface) !important; color: var(--pg-navy) !important;
        border: 1.5px solid var(--pg-navy) !important;
    }
    .stButton > button[kind="secondary"]:hover { background: #EEF2F8 !important; }
    .stDownloadButton > button {
        background: linear-gradient(135deg, var(--pg-gold-dark) 0%, var(--pg-gold) 100%) !important;
        color: #fff !important; border: none !important;
    }
    .stDownloadButton > button:hover {
        box-shadow: 0 4px 14px rgba(201,151,63,0.38) !important; transform: translateY(-1px);
    }

    div[data-testid="stDataFrame"], div[data-testid="stDataEditor"] {
        border: 1px solid var(--pg-border) !important; border-radius: 10px !important;
        overflow: hidden !important; box-shadow: 0 1px 4px rgba(15,42,74,0.07) !important;
    }
    div[data-testid="stDataFrame"] [role="columnheader"],
    div[data-testid="stDataEditor"] [role="columnheader"] {
        background: var(--pg-navy) !important; color: #fff !important; font-weight: 600 !important;
    }

    div[data-testid="stAlert"] { border-radius: 8px !important; border-left-width: 5px !important; }

    .stTextInput input, .stNumberInput input, .stTextArea textarea,
    .stSelectbox div[data-baseweb="select"] > div {
        border-radius: 6px !important; border-color: var(--pg-border) !important;
    }
    .stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
        border-color: var(--pg-gold) !important; box-shadow: 0 0 0 1px var(--pg-gold) !important;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0F2A4A 0%, #0A1E33 100%) !important;
        border-right: 1px solid #0A1E33 !important;
    }
    [data-testid="stSidebar"] * { color: #F2F5FA !important; }
    [data-testid="stSidebar"] hr { border-top: 1px solid rgba(255,255,255,0.15) !important; }
    [data-testid="stSidebar"] label[data-testid="stWidgetLabel"] p {
        font-family: 'Poppins','Inter',sans-serif !important;
        font-size: 16px !important; font-weight: 700 !important;
        color: #E9C989 !important; letter-spacing: 0.2px;
        padding-bottom: 10px !important; margin-bottom: 4px !important;
        border-bottom: 2px solid rgba(233,201,137,0.35);
    }
    [data-testid="stSidebar"] div[role="radiogroup"] {
        display: flex !important; flex-direction: column !important; gap: 7px !important; margin-top: 6px !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] label {
        background: rgba(255,255,255,0.06) !important; border: 1px solid rgba(255,255,255,0.14) !important;
        border-radius: 9px !important; padding: 11px 14px !important; margin: 0 !important; width: 100% !important;
        transition: background 0.15s ease, border-color 0.15s ease, transform 0.1s ease !important; cursor: pointer !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        background: rgba(201,151,63,0.18) !important; border-color: #C9973F !important; transform: translateX(2px);
    }
    [data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
        background: linear-gradient(135deg, #C9973F 0%, #A97A25 100%) !important;
        border-color: #E9C989 !important; box-shadow: 0 2px 8px rgba(0,0,0,0.25) !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p {
        color: #0F2A4A !important; font-weight: 700 !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child { display: none !important; }

    @media print {
        header, [data-testid="stHeader"], [data-testid="stSidebar"], [data-testid="stDecoration"],
        [data-testid="stNotification"], [data-testid="stForm"], .print-hide, iframe,
        div.element-container:has(> div[data-testid="stDataFrame"]) { display: none !important; }
        .print-only-container { display: block !important; }
        .print-only-container table {
            display: table !important; width: 100% !important; border-collapse: collapse !important;
            font-family: Arial, sans-serif !important; font-size: 11px !important; color: #000 !important;
        }
        .print-only-container th { background-color: #f2f2f2 !important; border: 1px solid #111 !important; padding: 6px !important; font-weight: bold !important; text-align: center !important; }
        .print-only-container td { border: 1px solid #111 !important; padding: 5px !important; text-align: left !important; }
        @page { margin: 8mm; size: A4 landscape; }
    }
    .print-only-container { display: none; }
    </style>
""", unsafe_allow_html=True)

# ==========================================================
# 🛑 STEP 4: LOGIN GATEWAY
# ==========================================================
if st.session_state.user_role is None:
    header_html = """
    <div style="display:flex; align-items:center; gap:20px; margin-bottom:20px; font-family:'Poppins','Inter',sans-serif;
        background: linear-gradient(135deg, #FFFFFF 0%, #F5F7FA 100%); border: 1px solid #DCE3EC; border-radius: 12px; padding: 16px 20px;">
        <div style="flex-shrink:0; width:70px; height:70px; display:flex; align-items:center; justify-content:center;
            border-radius:10px; box-shadow:0 4px 12px rgba(15,42,74,0.18); border:2px solid #C9973F;">
            <h1 style="margin:0;">🏛️</h1>
        </div>
        <div style="display:flex; flex-direction:column; justify-content:center;">
            <h1 style="margin:0 !important; padding:0 !important; color:#0F2A4A; font-size:30px; font-weight:700; border:none !important;">
                Department Approval &amp; Assignment System</h1>
            <h3 style="margin:2px 0 0 0 !important; padding:0 !important; color:#A97A25; font-weight:600 !important; font-size:15px;">
                Entry → Approval → Department-wise Distribution</h3>
        </div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)

    login_col, _ = st.columns([1, 1.4])
    with login_col:
        st.subheader("🔐 Login")
        with st.form("login_form"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", type="primary", use_container_width=True)
        if submitted:
            creds = st.session_state.credentials
            entry = creds.get(u.strip())
            if entry and entry.get("password") == p:
                st.session_state.user_role = entry.get("role")
                st.session_state.username = u.strip()
                st.session_state.user_department = entry.get("department")
                st.success(f"स्वागत है, {u.strip()}!")
                time.sleep(0.4)
                st.rerun()
            else:
                st.error("❌ गलत Username या Password। कृपया दोबारा कोशिश करें।")
        st.caption("Default admin login → **admin / admin123** (पहली बार login करने के बाद P6 → Admin Panel से password बदल लें)")
    st.stop()

# ==========================================================
# 🧭 STEP 5: SIDEBAR NAVIGATION
# ==========================================================
role = st.session_state.user_role
username = st.session_state.username
user_dept = st.session_state.user_department

with st.sidebar:
    st.markdown(f"### 👤 {username}")
    st.caption(st.session_state.credentials.get(username, {}).get("label", role))
    st.markdown("---")
    if role == "admin":
        panel_options = [
            "P1 — Entry & Upload",
            "P2 — Approve List",
            "P3 — Approved List",
            "P4 — Department Panel",
            "P5 — Print Panel",
            "P6 — Admin Panel",
        ]
    else:
        panel_options = ["P4 — My Department List"]
    choice = st.radio("Navigate Panels", panel_options, label_visibility="visible")
    st.markdown("---")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.user_role = None
        st.session_state.username = None
        st.session_state.user_department = None
        st.rerun()

db = load_db()

# ==========================================================
# 📝 P1 — ENTRY & UPLOAD  (Admin only)
# ==========================================================
if choice == "P1 — Entry & Upload":
    st.header("📝 P1 — Data Entry & Upload")
    mode = st.radio("तरीका चुनें", ["✍️ Single Entry (Form)", "📤 Bulk Upload (CSV/Excel)"], horizontal=True)

    if mode == "✍️ Single Entry (Form)":
        with st.form("single_entry_form"):
            st.caption("नीचे जितने columns भरने हैं भरें — बाकी खाली छोड़ सकते हैं।")
            values = {}
            cols = st.columns(3)
            for i, col_name in enumerate(DEFAULT_COLUMNS):
                with cols[i % 3]:
                    values[col_name] = st.text_input(col_name, key=f"p1_field_{col_name}")
            submit_entry = st.form_submit_button("➕ Submit for Approval", type="primary", use_container_width=True)
        if submit_entry:
            if not any(str(v).strip() for v in values.values()):
                st.warning("⚠️ कृपया कम से कम एक फ़ील्ड भरें।")
            else:
                new_row = {c: "" for c in ALL_COLUMNS}
                new_row.update(values)
                new_row["Status"] = "Pending"
                new_row["Submitted By"] = username
                new_row["Submitted On"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                db = pd.concat([db, pd.DataFrame([new_row])], ignore_index=True)
                save_db(db)
                st.success("✅ Entry सफलतापूर्वक Submit हुई — अब यह P2 (Approve List) में Admin approval के लिए दिखेगी।")
                st.balloons()

    else:
        st.info("CSV या Excel (.csv/.xlsx/.xls) फ़ाइलें अपलोड करें — एक साथ कई फ़ाइलें भी चुन सकते हैं। "
                "मिलते-जुलते नाम वाले कॉलम (जैसे DOB, Email, Mobile No) अपने आप सही जगह मैच हो जाएंगे — बाकी खाली रहेंगे।")

        oc1, oc2 = st.columns(2)
        with oc1:
            p1_common_year = st.text_input("Admission Year (सभी rows पर लागू करें, वैकल्पिक)", key="p1_common_year")
        with oc2:
            p1_common_session = st.text_input("Admission Session (सभी rows पर लागू करें, वैकल्पिक)", key="p1_common_session")
        st.caption("ऊपर की दो फ़ील्ड सिर्फ़ उन्हीं rows में भरी जाएंगी जहाँ फ़ाइल में यह कॉलम पहले से खाली है।")

        up_files = st.file_uploader("फ़ाइलें चुनें", type=["csv", "xlsx", "xls"], accept_multiple_files=True)

        if up_files:
            all_new_rows = []
            for up_file in up_files:
                try:
                    raw_df = read_uploaded_table(up_file)
                except Exception as e:
                    st.error(f"❌ '{up_file.name}' पढ़ने में समस्या: {e}")
                    continue

                if raw_df.empty:
                    st.error(f"❌ '{up_file.name}' में कोई मान्य डेटा नहीं मिला या फ़ॉर्मेट पढ़ा नहीं जा सका।")
                    if _UPLOAD_DIAG["info"]:
                        st.caption(f"🔎 Diagnostic: {_UPLOAD_DIAG['info']}")
                    continue

                raw_df = smart_align_columns(raw_df)
                with st.expander(f"👁️ '{up_file.name}' — {raw_df.shape[0]} rows, {raw_df.shape[1]} columns (Preview)"):
                    st.dataframe(raw_df.head(20), use_container_width=True)

                aligned = pd.DataFrame(columns=ALL_COLUMNS)
                for c in DEFAULT_COLUMNS:
                    aligned[c] = raw_df[c] if c in raw_df.columns else ""
                if p1_common_year.strip():
                    aligned.loc[aligned["Admission Year"].astype(str).str.strip() == "", "Admission Year"] = p1_common_year.strip()
                if p1_common_session.strip():
                    aligned.loc[aligned["Admission Session"].astype(str).str.strip() == "", "Admission Session"] = p1_common_session.strip()
                aligned["Status"] = "Pending"
                aligned["Assigned Department"] = ""
                aligned["Submitted By"] = username
                aligned["Submitted On"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                aligned["Approved By"] = ""
                aligned["Approved On"] = ""
                all_new_rows.append(aligned)

            if all_new_rows:
                total_rows = sum(len(a) for a in all_new_rows)
                st.success(f"✅ कुल {len(all_new_rows)} फ़ाइलों से {total_rows} rows पढ़ ली गई हैं — नीचे बटन दबाकर पक्का जोड़ें।")
                if st.button(f"📥 इन सभी {total_rows} Rows को Pending List में जोड़ें", type="primary"):
                    db = pd.concat([db] + all_new_rows, ignore_index=True)
                    save_db(db)
                    st.success(f"🎉 {total_rows} rows जोड़ दी गई हैं — अब P2 में Approval के लिए उपलब्ध हैं।")
                    st.balloons()
                    st.rerun()

# ==========================================================
# ✅ P2 — APPROVE LIST  (Admin only)
# ==========================================================
elif choice == "P2 — Approve List":
    st.header("✅ P2 — Pending List (Approve Karein)")
    pending = db[db["Status"] == "Pending"].copy()
    if pending.empty:
        st.info("📭 फ़िलहाल कोई Pending entry नहीं है।")
    else:
        st.caption(f"कुल {len(pending)} entries Approval का इंतज़ार कर रही हैं।")

        # ---- पूरी List एक साथ Approve करें ----
        st.markdown("### 🚀 पूरी List एक साथ Approve करें")
        st.caption("नीचे एक Department चुनें — पूरी Pending List उसी Department को Assign होकर Approve हो जाएगी।")
        bulk_c1, bulk_c2 = st.columns([2, 1])
        with bulk_c1:
            bulk_dept = st.selectbox("सभी Entries इस Department में भेजें", st.session_state.departments, key="p2_bulk_dept")
        with bulk_c2:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            approve_all_clicked = st.button(f"✅ पूरी List ({len(pending)}) Approve करें", type="primary", use_container_width=True)
        if approve_all_clicked:
            for i in pending.index:
                db.at[i, "Status"] = "Approved"
                db.at[i, "Assigned Department"] = bulk_dept
                db.at[i, "Approved By"] = username
                db.at[i, "Approved On"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            save_db(db)
            st.success(f"🎉 पूरी List ({len(pending)} entries) Approve होकर '{bulk_dept}' को भेज दी गई है।")
            st.balloons()
            st.rerun()

        st.markdown("---")
        st.markdown("### 🖊️ या हर Entry को अलग-अलग Department देकर Approve करें")
        select_all = st.checkbox("☑️ सभी entries Select करें", key="p2_select_all")
        pending.insert(0, "Select", select_all)
        dept_options = st.session_state.departments
        display_cols = ["Select", "Student Name", "Father Name", "Mobile Number", "Assigned Department", "Submitted By", "Submitted On"]
        display_cols = [c for c in display_cols if c in pending.columns]
        edited = st.data_editor(
            pending[display_cols],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Select": st.column_config.CheckboxColumn("Select"),
                "Assigned Department": st.column_config.SelectboxColumn("Assign to Department", options=dept_options, required=False),
            },
            key=f"p2_approve_editor_{select_all}",
        )
        with st.expander("🔍 पूरी row details देखें (सभी columns)"):
            st.dataframe(pending.drop(columns=["Select"]), use_container_width=True)

        if st.button("✅ चुनी गई Entries Approve करें", type="primary"):
            selected_idx = edited[edited["Select"] == True].index
            if len(selected_idx) == 0:
                st.warning("⚠️ पहले कम से कम एक entry Select करें।")
            else:
                missing_dept = [i for i in selected_idx if not str(edited.loc[i, "Assigned Department"]).strip()]
                if missing_dept:
                    st.error("❌ Approve करने से पहले हर चुनी गई entry के लिए एक Department चुनना ज़रूरी है।")
                else:
                    for i in selected_idx:
                        db.at[i, "Status"] = "Approved"
                        db.at[i, "Assigned Department"] = edited.loc[i, "Assigned Department"]
                        db.at[i, "Approved By"] = username
                        db.at[i, "Approved On"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                    save_db(db)
                    st.success(f"🎉 {len(selected_idx)} entries Approve होकर संबंधित Department को भेज दी गई हैं।")
                    st.balloons()
                    st.rerun()

# ==========================================================
# 📋 P3 — APPROVED LIST
# ==========================================================
elif choice == "P3 — Approved List":
    st.header("📋 P3 — Approved List (सभी Departments)")
    approved = db[db["Status"] == "Approved"].copy()
    if approved.empty:
        st.info("📭 अभी तक कोई entry Approve नहीं हुई है।")
    else:
        f_col1, f_col2 = st.columns([1, 2])
        with f_col1:
            dept_filter = st.selectbox("Department से फ़िल्टर करें", ["सभी"] + st.session_state.departments)
        with f_col2:
            search = st.text_input("🔎 Student Name / Roll No. / Unique ID से खोजें")

        view = approved.copy()
        if dept_filter != "सभी":
            view = view[view["Assigned Department"] == dept_filter]
        if search.strip():
            s = search.strip().lower()
            mask = view.apply(lambda r: s in " ".join(str(v).lower() for v in r.values), axis=1)
            view = view[mask]

        st.caption(f"कुल {len(view)} Approved records मिले।")
        st.dataframe(view, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("🖨️ Export / Print")
        chosen_cols = st.multiselect("Print/Export के लिए Columns चुनें", ALL_COLUMNS,
                                      default=["Student Name", "Father Name", "Roll No.", "Subject", "Assigned Department", "Status"])
        if chosen_cols:
            print_df = view[chosen_cols]
            d_col1, d_col2 = st.columns(2)
            with d_col1:
                st.download_button("⬇️ CSV Download करें", print_df.to_csv(index=False).encode("utf-8-sig"),
                                    file_name="approved_list.csv", mime="text/csv", use_container_width=True)
            with d_col2:
                if st.button("🖨️ Print View तैयार करें", use_container_width=True):
                    table_html = print_df.to_html(index=False, escape=True)
                    st.markdown(f'<div class="print-only-container">{table_html}</div>', unsafe_allow_html=True)
                    st.info("Print view नीचे तैयार है — अब Browser से Ctrl+P / Cmd+P दबाएँ (सिर्फ़ यह टेबल print होगी)।")
                    st.markdown(f'<div class="print-hide">{print_df.to_html(index=False, escape=True)}</div>', unsafe_allow_html=True)

# ==========================================================
# 🏢 P4 — DEPARTMENT PANEL
# ==========================================================
elif choice in ("P4 — Department Panel", "P4 — My Department List"):
    st.header("🏢 P4 — Department-wise List")
    approved = db[db["Status"] == "Approved"].copy()
    faculty_db = load_faculty()

    if role == "admin":
        with st.expander("📤 Department – Faculty Mapping अपलोड/अपडेट करें"):
            st.caption("Excel/CSV फ़ाइल अपलोड करें जिसमें 'Department' (या 'Allotted Class') और 'Faculty Name' "
                       "(या 'Name of Guardians Tutors') कॉलम हों — जैसे 'LIST OF GUARDIANS TUTORS' शीट में होता है "
                       "(S.N., Name of Guardians Tutors, Allotted Class, Number of Student)। "
                       "Designation, Mobile Number वैकल्पिक हैं। नई फ़ाइल पुरानी mapping को replace कर देगी।")
            fac_file = st.file_uploader("Faculty List फ़ाइल चुनें", type=["csv", "xlsx", "xls"], key="fac_upload")
            if fac_file is not None:
                try:
                    fac_raw = read_uploaded_table(fac_file)
                except Exception as e:
                    st.error(f"❌ फ़ाइल पढ़ने में समस्या: {e}")
                    fac_raw = pd.DataFrame()

                if not fac_raw.empty:
                    fac_rename = {}
                    for col in fac_raw.columns:
                        key = re.sub(r"[^a-z0-9]", "", str(col).strip().lower())
                        if key in ("department", "dept", "departmentname", "allottedclass",
                                   "class", "allottedclassname"):
                            fac_rename[col] = "Department"
                        elif key in ("facultyname", "faculty", "teachername", "mentorname",
                                     "tutorname", "guardiantutorname", "nameofguardianstutors",
                                     "nameofguardiantutor", "guardianstutors", "guardiantutors",
                                     "nameofguardian"):
                            fac_rename[col] = "Faculty Name"
                        elif key in ("designation", "post", "role"):
                            fac_rename[col] = "Designation"
                        elif key in ("mobilenumber", "mobileno", "mobile", "phone",
                                     "phonenumber", "contactno"):
                            fac_rename[col] = "Mobile Number"
                        elif key in ("numberofstudent", "numberofstudents", "totalstudents",
                                     "studentcount", "noofstudents", "nostudents"):
                            fac_rename[col] = "Number of Students"
                    fac_raw = fac_raw.rename(columns=fac_rename)

                    if "Department" not in fac_raw.columns or "Faculty Name" not in fac_raw.columns:
                        st.error("❌ फ़ाइल में 'Department' (या 'Allotted Class') और 'Faculty Name' "
                                 "(या 'Name of Guardians Tutors') — ये दोनों कॉलम ज़रूर होने चाहिए।")
                    else:
                        st.dataframe(fac_raw.head(20), use_container_width=True)
                        if st.button("💾 Faculty Mapping Save करें", type="primary"):
                            aligned_fac = pd.DataFrame(columns=FACULTY_COLUMNS)
                            for c in FACULTY_COLUMNS:
                                aligned_fac[c] = fac_raw[c] if c in fac_raw.columns else ""
                            aligned_fac = aligned_fac[aligned_fac["Department"].astype(str).str.strip() != ""]
                            save_faculty(aligned_fac)
                            st.success(f"✅ {len(aligned_fac)} Faculty entries save हो गई हैं।")
                            st.rerun()
                elif fac_file is not None:
                    st.error("❌ फ़ाइल में कोई मान्य डेटा नहीं मिला।")

            if not faculty_db.empty:
                st.markdown("**मौजूदा Faculty Mapping:**")
                st.dataframe(faculty_db, use_container_width=True, hide_index=True)

    if role == "admin":
        target_dept = st.selectbox("Department चुनें", st.session_state.departments)
    else:
        target_dept = user_dept
        st.caption(f"आप लॉगिन हैं: **{target_dept}** — आपको सिर्फ़ इसी Department को Assign की गई entries दिखेंगी।")

    dept_faculty = faculty_db[faculty_db["Department"] == target_dept]
    if not dept_faculty.empty:
        for _, frow in dept_faculty.iterrows():
            line = f"👩‍🏫 **{frow['Faculty Name']}**"
            if str(frow.get("Designation", "")).strip():
                line += f" ({frow['Designation']})"
            if str(frow.get("Mobile Number", "")).strip():
                line += f" — 📱 {frow['Mobile Number']}"
            if str(frow.get("Number of Students", "")).strip():
                line += f" — 👥 {frow['Number of Students']} Students"
            st.info(line)
    else:
        st.caption("ℹ️ इस Department के लिए अभी कोई Faculty mapping उपलब्ध नहीं है (ऊपर 'Department – Faculty Mapping' से अपलोड करें)।")

    dept_view = approved[approved["Assigned Department"] == target_dept]
    st.subheader(f"📂 {target_dept} — कुल {len(dept_view)} Students")
    if dept_view.empty:
        st.info("📭 इस Department को अभी तक कोई entry Assign नहीं हुई है।")
    else:
        st.dataframe(dept_view, use_container_width=True, hide_index=True)
        st.download_button(f"⬇️ {target_dept} की List Download करें",
                            dept_view.to_csv(index=False).encode("utf-8-sig"),
                            file_name=f"{target_dept.replace(' ', '_')}_list.csv", mime="text/csv")

# ==========================================================
# 🖨️ P5 — PRINT PANEL  (Admin only)
# ==========================================================
elif choice == "P5 — Print Panel":
    st.header("🖨️ P5 — Print Panel")
    st.caption("यहाँ से आप किसी भी List को अपने college के letterhead-style header के साथ खूबसूरती से Print कर सकते हैं।")

    # ---- Print Header Customizer (3 lines + Guardian Tutor info row) ----
    st.subheader("📝 Print Header Customizer")
    _ph_defaults = {
        "ph_line1": "GOVERNMENT KAMLARAJA GIRLS POST GRADUATE (AUTO.) COLLEGE, GWALIOR",
        "ph_size1": 20, "ph_color1": "#0F2A4A",
        "ph_line2": "B.Com. FIRST YEAR (SESSION: 2025-26)",
        "ph_size2": 16, "ph_color2": "#0F2A4A",
        "ph_line3": "Mentor/Guardian Tutor List, Major Subject - Commerce",
        "ph_size3": 14, "ph_color3": "#A97A25",
        "ph_guardian_name": "", "ph_guardian_mobile": "",
    }
    for _k, _v in _ph_defaults.items():
        if _k not in st.session_state:
            st.session_state[_k] = _v

    st.session_state.ph_line1 = st.text_input("Header Line 1 (College Name)", value=st.session_state.ph_line1)
    l1a, l1b = st.columns(2)
    with l1a:
        st.session_state.ph_size1 = st.slider("Line 1 Font Size (px)", 12, 40, st.session_state.ph_size1)
    with l1b:
        st.session_state.ph_color1 = st.color_picker("Line 1 Color", st.session_state.ph_color1)

    ph_c1, ph_c2 = st.columns(2)
    with ph_c1:
        st.session_state.ph_line2 = st.text_input("Header Line 2 (Course & Session)", value=st.session_state.ph_line2)
        s2a, s2b = st.columns(2)
        with s2a:
            st.session_state.ph_size2 = st.slider("Line 2 Font Size (px)", 8, 30, st.session_state.ph_size2)
        with s2b:
            st.session_state.ph_color2 = st.color_picker("Line 2 Color", st.session_state.ph_color2)
    with ph_c2:
        st.session_state.ph_line3 = st.text_input("Header Line 3 (List Title / Subject)", value=st.session_state.ph_line3)
        s3a, s3b = st.columns(2)
        with s3a:
            st.session_state.ph_size3 = st.slider("Line 3 Font Size (px)", 8, 30, st.session_state.ph_size3)
        with s3b:
            st.session_state.ph_color3 = st.color_picker("Line 3 Color", st.session_state.ph_color3)

    g_c1, g_c2 = st.columns(2)
    with g_c1:
        st.session_state.ph_guardian_name = st.text_input("Name of Guardian Tutor (खाली छोड़ें तो print में हाथ से लिखने की जगह खाली रहेगी)", value=st.session_state.ph_guardian_name)
    with g_c2:
        st.session_state.ph_guardian_mobile = st.text_input("Mobile No (Guardian Tutor)", value=st.session_state.ph_guardian_mobile)

    _blank_line = "&nbsp;" * 22

    def _build_header_html(font_family):
        guardian_val = st.session_state.ph_guardian_name.strip() or _blank_line
        mobile_val = st.session_state.ph_guardian_mobile.strip() or _blank_line
        return f"""
        <div style="text-align:center; font-family:{font_family};">
            <div style="font-weight:700; font-size:{st.session_state.ph_size1}px; color:{st.session_state.ph_color1};">
                {st.session_state.ph_line1 or "&nbsp;"}
            </div>
            <div style="font-weight:700; font-size:{st.session_state.ph_size2}px; color:{st.session_state.ph_color2}; margin-top:4px;">
                {st.session_state.ph_line2 or "&nbsp;"}
            </div>
            <div style="font-weight:600; font-size:{st.session_state.ph_size3}px; color:{st.session_state.ph_color3}; margin-top:4px;">
                {st.session_state.ph_line3 or "&nbsp;"}
            </div>
            <div style="display:flex; justify-content:space-between; margin-top:12px; font-size:14px; text-align:left;">
                <div>Name of Guardian Tutor - <b>{guardian_val}</b></div>
                <div>Mobile No- <b>{mobile_val}</b></div>
            </div>
        </div>
        """

    st.markdown(
        f"""<div style="border:1px solid var(--pg-border); border-radius:10px; padding:14px 18px;
            background:var(--pg-surface); margin-top:6px;">{_build_header_html("'Poppins','Inter',sans-serif")}</div>""",
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # ---- Data selection ----
    st.subheader("📂 Data चुनें")
    d_col1, d_col2, d_col3 = st.columns([1, 1, 2])
    with d_col1:
        status_choice = st.selectbox("Status", ["Approved", "Pending", "सभी"])
    with d_col2:
        if role == "admin":
            dept_choice = st.selectbox("Department", ["सभी"] + st.session_state.departments)
        else:
            dept_choice = user_dept
            st.caption(f"Department: **{user_dept}**")
    with d_col3:
        pp_search = st.text_input("🔎 Student Name / Roll No. / Unique ID से खोजें", key="pp_search")

    pp_view = db.copy()
    if status_choice != "सभी":
        pp_view = pp_view[pp_view["Status"] == status_choice]
    if role != "admin":
        pp_view = pp_view[pp_view["Assigned Department"] == user_dept]
    elif dept_choice != "सभी":
        pp_view = pp_view[pp_view["Assigned Department"] == dept_choice]
    if pp_search.strip():
        s = pp_search.strip().lower()
        pp_view = pp_view[pp_view.apply(lambda r: s in " ".join(str(v).lower() for v in r.values), axis=1)]

    st.caption(f"कुल {len(pp_view)} records मिले।")

    # प्रिंट में दिखने वाले कॉलम-लेबल (असली internal column names वही रहते हैं)
    PRINT_LABEL_OVERRIDES = {"Student Name": "Full Name", "Mobile Number": "Mob. No."}

    if pp_view.empty:
        st.info("📭 चुने गए Filters से कोई record नहीं मिला।")
    else:
        default_print_cols = [c for c in ["Unique ID", "Student Name", "Father Name", "Mobile Number"] if c in ALL_COLUMNS]
        pp_cols = st.multiselect(
            "Print के लिए Columns चुनें (S.No अपने आप जुड़ जाएगा)", ALL_COLUMNS,
            default=default_print_cols,
            key="pp_cols",
        )
        if pp_cols:
            pp_print_df = pp_view[pp_cols].reset_index(drop=True)
            pp_print_df.insert(0, "S.No", range(1, len(pp_print_df) + 1))
            preview_df = pp_print_df.rename(columns=PRINT_LABEL_OVERRIDES)

            st.markdown("---")
            st.subheader("👁️ Preview")
            st.dataframe(preview_df, use_container_width=True, hide_index=True)

            st.markdown("---")
            st.subheader("🖨️ Print / Export")
            pr_col1, pr_col2 = st.columns(2)
            with pr_col1:
                st.download_button(
                    "⬇️ CSV Download करें",
                    preview_df.to_csv(index=False).encode("utf-8-sig"),
                    file_name="print_panel_list.csv", mime="text/csv", use_container_width=True,
                )
            with pr_col2:
                do_print = st.button("🖨️ Print View तैयार करें", type="primary", use_container_width=True)

            if do_print:
                table_html = preview_df.to_html(index=False, escape=True)
                header_html = f'<div style="margin-bottom:10px;">{_build_header_html("Arial, sans-serif")}<hr style="border:none; border-top:2px solid {st.session_state.ph_color1}; margin-top:10px;"></div>'
                st.markdown(f'<div class="print-only-container">{header_html}{table_html}</div>', unsafe_allow_html=True)
                st.info("Print view नीचे तैयार है — अब Browser से Ctrl+P / Cmd+P दबाएँ (सिर्फ़ header + यह टेबल print होगी)।")
                st.markdown(f'<div class="print-hide">{header_html}{table_html}</div>', unsafe_allow_html=True)
        else:
            st.warning("⚠️ Print करने के लिए कम से कम एक Column चुनें।")

# ==========================================================
# 🛠️ P6 — ADMIN PANEL  (Admin only)
# ==========================================================
elif choice == "P6 — Admin Panel":
    st.header("🛠️ P6 — Admin Panel")

    tab_dash, tab_users, tab_depts, tab_data = st.tabs(
        ["📊 Dashboard", "👤 Users / Credentials", "🏢 Departments", "🗄️ Database"]
    )

    with tab_dash:
        c1, c2, c3 = st.columns(3)
        c1.metric("कुल Records", len(db))
        c2.metric("Pending", int((db["Status"] == "Pending").sum()))
        c3.metric("Approved", int((db["Status"] == "Approved").sum()))
        if not db.empty:
            st.markdown("**Department-wise Approved Count:**")
            dept_counts = db[db["Status"] == "Approved"]["Assigned Department"].value_counts()
            st.dataframe(dept_counts.rename_axis("Department").reset_index(name="Count"), use_container_width=True, hide_index=True)

    with tab_users:
        st.subheader("मौजूदा Users")
        creds = st.session_state.credentials
        users_table = pd.DataFrame([
            {"Username": u, "Role": v.get("role"), "Department": v.get("department", "-"), "Label": v.get("label", "")}
            for u, v in creds.items()
        ])
        st.dataframe(users_table, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("**➕ नया Department User बनाएँ**")
        with st.form("new_user_form"):
            nu_col1, nu_col2 = st.columns(2)
            with nu_col1:
                new_username = st.text_input("Username")
                new_password = st.text_input("Password")
            with nu_col2:
                new_dept = st.selectbox("Department", st.session_state.departments)
                new_label = st.text_input("Display Label (optional)", value="")
            add_user_btn = st.form_submit_button("➕ User जोड़ें", type="primary")
        if add_user_btn:
            if not new_username.strip() or not new_password.strip():
                st.warning("⚠️ Username और Password दोनों भरना ज़रूरी है।")
            elif new_username.strip() in creds:
                st.error("❌ यह Username पहले से मौजूद है।")
            else:
                creds[new_username.strip()] = {
                    "password": new_password,
                    "role": "department",
                    "department": new_dept,
                    "label": new_label.strip() or f"🏢 {new_dept}",
                }
                st.session_state.credentials = creds
                save_credentials(creds)
                st.success(f"✅ User '{new_username.strip()}' बन गया — यह सिर्फ़ '{new_dept}' का P4 देख पाएगा।")
                st.rerun()

        st.markdown("---")
        st.markdown("**🗑️ User हटाएँ**")
        deletable_users = [u for u in creds.keys() if u != "admin"]
        if deletable_users:
            del_user = st.selectbox("हटाने के लिए User चुनें", deletable_users)
            if st.button("🗑️ Delete User", type="secondary"):
                creds.pop(del_user, None)
                st.session_state.credentials = creds
                save_credentials(creds)
                st.success(f"🗑️ User '{del_user}' हटा दिया गया।")
                st.rerun()
        else:
            st.caption("कोई अतिरिक्त User नहीं है (Admin नहीं हटाया जा सकता)।")

        st.markdown("---")
        st.markdown("**🔑 Admin Password बदलें**")
        with st.form("change_admin_pw"):
            cur_pw = st.text_input("Current Password", type="password")
            new_pw = st.text_input("New Password", type="password")
            change_btn = st.form_submit_button("Password अपडेट करें", type="primary")
        if change_btn:
            if creds.get("admin", {}).get("password") != cur_pw:
                st.error("❌ Current Password ग़लत है।")
            elif not new_pw.strip():
                st.warning("⚠️ नया Password खाली नहीं हो सकता।")
            else:
                creds["admin"]["password"] = new_pw
                st.session_state.credentials = creds
                save_credentials(creds)
                st.success("✅ Admin Password अपडेट हो गया।")

    with tab_depts:
        st.subheader("Departments की List")
        depts = st.session_state.departments
        st.dataframe(pd.DataFrame({"Department": depts}), use_container_width=True, hide_index=True)
        add_col, del_col = st.columns(2)
        with add_col:
            new_dept_name = st.text_input("नया Department नाम")
            if st.button("➕ Department जोड़ें", type="primary"):
                if new_dept_name.strip() and new_dept_name.strip() not in depts:
                    depts.append(new_dept_name.strip())
                    st.session_state.departments = depts
                    save_departments(depts)
                    st.success(f"✅ '{new_dept_name.strip()}' जोड़ दिया गया।")
                    st.rerun()
                else:
                    st.warning("⚠️ नाम खाली है या पहले से मौजूद है।")
        with del_col:
            if depts:
                rm_dept = st.selectbox("Department हटाएँ", depts, key="rm_dept_select")
                if st.button("🗑️ हटाएँ", type="secondary"):
                    depts.remove(rm_dept)
                    st.session_state.departments = depts
                    save_departments(depts)
                    st.success(f"🗑️ '{rm_dept}' हटा दिया गया।")
                    st.rerun()

    with tab_data:
        st.subheader("पूरा Database")
        st.dataframe(db, use_container_width=True, hide_index=True)
        st.download_button("⬇️ पूरा Database Backup (CSV) Download करें",
                            db.to_csv(index=False).encode("utf-8-sig"),
                            file_name="full_database_backup.csv", mime="text/csv")
