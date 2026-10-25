import streamlit as st
import pandas as pd
import os
import re
import base64
import json
import io
import time
import re as _re_notice_link  # 🟢 Notice Board me URL detect karke clickable link banane ke liye
import html as _html_escape_lib  # 🟢 Notice text ko safely HTML-escape karne ke liye
import requests  # 🟢 P10 naam-transliteration (Google Input Tools) ke liye
import streamlit.components.v1 as components  # 🟢 यह लाइन यहाँ नीचे जोड़नी है

# 🟢 P10 प्रिंट ट्रांसलेशन फीचर के लिए लाइब्रेरी (अगर इंस्टॉल नहीं है तो feature अपने आप डिसेबल हो जाएगा)
try:
    from deep_translator import GoogleTranslator
    TRANSLATOR_AVAILABLE = True
except Exception:
    TRANSLATOR_AVAILABLE = False

# ==========================================================
# ⚙️ स्टेप 1: पेज का लेआउट सेट करें और डिफ़ॉल्ट थीम्स बनाएं
# ==========================================================
st.set_page_config(layout="wide", page_title="Permanent Shared Live Database")

# ==========================================================
# 🔄 UNIVERSAL UPLOAD CONVERTER: XLS / XLSX  ->  CSV  ->  DataFrame
# Kisi bhi panel me file upload ho: agar Excel (.xls/.xlsx) hai to pehle use
# CSV me convert kiya jata hai, fir bilkul CSV ki tarah hi aage process hota hai.
# ==========================================================
def _clean_raw_table(raw):
    """Khali rows/columns hatao, upar ke title-rows chhodo, sahi header row dhundo."""
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
    """Kai sheets/tables me se sabse zyada data wali chuno."""
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
    """Excel 2003 'XML Spreadsheet' (.xls naam se save hui XML file)."""
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
            cells, col = [], 0
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


def convert_excel_to_csv_bytes(uploaded_file):
    """XLS / XLSX (ya asal me HTML / XML / text wali .xls) ko CSV bytes me badalta hai.
    File ka type extension se nahi, andar ke content se pehchana jata hai."""
    raw = uploaded_file.getvalue()
    head = raw[:4096].lstrip()
    head_l = head.lower()
    frames, kind = [], "unknown"
    try:
        if raw[:4] == b"PK\x03\x04":                                   # asli .xlsx
            kind = "xlsx"
            frames = list(pd.read_excel(io.BytesIO(raw), engine="openpyxl", dtype=str,
                                        header=None, sheet_name=None).values())
        elif raw[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":            # asli .xls (Excel 97-2003)
            kind = "xls"
            frames = list(pd.read_excel(io.BytesIO(raw), engine="xlrd", dtype=str,
                                        header=None, sheet_name=None).values())
        elif b"urn:schemas-microsoft-com:office:spreadsheet" in raw[:8192]:   # Excel 2003 XML
            kind = "spreadsheetml-xml"
            frames = _parse_spreadsheetml(_decode_text(raw)[0])
        elif head_l.startswith(b"<") or b"<table" in head_l:          # HTML wali "fake xls"
            kind = "html"
            text = _decode_text(raw)[0]
            for t in pd.read_html(io.StringIO(text)):
                if not isinstance(t.columns, pd.RangeIndex):
                    hdr_row = [str(c[-1] if isinstance(c, tuple) else c) for c in t.columns]
                    t = pd.concat([pd.DataFrame([hdr_row]),
                                   t.set_axis(range(t.shape[1]), axis=1).astype(str)], ignore_index=True)
                frames.append(t)
        else:                                                          # CSV / TSV text
            kind = "text"
            frames = _parse_delimited_text(raw)
    except Exception as parse_err:
        _UPLOAD_DIAG["info"] = f"type={kind}, size={len(raw)} bytes, parse error: {parse_err}"
        raise
    df_x = _best_frame(frames)
    preview = raw[:120].decode("latin-1", errors="replace").replace("\n", " ").replace("\r", " ")
    _UPLOAD_DIAG["info"] = (f"type={kind}, size={len(raw)} bytes, sheets/tables={len(frames)}, "
                            f"rows x cols after cleanup={df_x.shape}, file start: {preview!r}")
    if df_x.empty:
        return b""
    df_x = df_x.replace(r"\s00:00:00$", "", regex=True)
    return df_x.to_csv(index=False).encode("utf-8-sig")


def dataframe_to_excel_bytes(df_out, sheet_name="Sheet1"):
    """DataFrame ko formatted .xlsx (bold header, auto column width, freeze row) bytes me badalta hai."""
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df_out.to_excel(writer, index=False, sheet_name=sheet_name[:31])
        ws = writer.sheets[sheet_name[:31]]
        for idx, col_name in enumerate(df_out.columns, start=1):
            head_cell = ws.cell(row=1, column=idx)
            head_cell.font = Font(bold=True)
            head_cell.fill = PatternFill("solid", fgColor="F2F2F2")
            head_cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            longest = max([len(str(col_name))] + [len(str(v)) for v in df_out.iloc[:, idx - 1].head(500)])
            ws.column_dimensions[get_column_letter(idx)].width = min(max(longest + 2, 8), 45)
        ws.freeze_panes = "A2"
    return buf.getvalue()


def make_password_protected_zip(file_bytes, inner_filename, password):
    """
    Diye gaye file bytes (e.g. .xlsx) ko ek AES-256 password-protected .zip me
    daal kar bytes return karta hai. Extract karte waqt sahi password na daalne par
    extraction fail ho jaata hai — yeh genuinely enforce hota hai (real, tested
    encryption; Excel-native 'open password' jaisi buggy library nahi).
    Requires: pyzipper (requirements.txt me `pyzipper` add karein).
    """
    import pyzipper
    zip_buf = io.BytesIO()
    with pyzipper.AESZipFile(
        zip_buf, "w",
        compression=pyzipper.ZIP_DEFLATED,
        encryption=pyzipper.WZ_AES
    ) as zf:
        zf.setpassword(password.encode("utf-8"))
        zf.writestr(inner_filename, file_bytes)
    return zip_buf.getvalue()


def read_uploaded_file_as_csv_df(uploaded_file):
    """CSV / XLS / XLSX kuch bhi ho -> (convert to CSV if needed) -> DataFrame (sab text)."""
    name = uploaded_file.name.lower()
    if name.endswith((".xlsx", ".xls")):
        csv_bytes = convert_excel_to_csv_bytes(uploaded_file)
    else:
        csv_bytes = uploaded_file.getvalue()
    if not csv_bytes.strip():
        return pd.DataFrame()
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return pd.read_csv(io.BytesIO(csv_bytes), dtype=str, encoding=enc).fillna("")
        except UnicodeDecodeError:
            continue
        except pd.errors.EmptyDataError:
            return pd.DataFrame()
    return pd.DataFrame()


# ==========================================================
# 🎨 PRINT HEADER STYLE — P2 "Print Header Text Customizer" ke liye
# Har header line ka Font Size (px) aur Colour yahin se control hota hai.
# Neeche ke DEFAULT wahi hain jo pehle CSS me fixed the (look pehle jaisa hi rahega).
# ==========================================================
PRINT_HEADER_LINES = [
    # (key,   css_class,       label,                 default_px, default_colour, extra_css)
    ("l1",   "h-line-1",    "1. कॉलेज का नाम",       18, "#E82D0A", "font-weight: bold; margin-bottom: 5px;"),
    ("ugpg", "h-line-ugpg", "2. UG / PG",             18, "#A97A25", "font-weight: bold; margin-bottom: 5px; letter-spacing: 0.3px;"),
    ("l2",   "h-line-2",    "3. रिपोर्ट का टाइटल",    18, "#333333", "font-weight: bold; margin-bottom: 5px;"),
    ("l3",   "h-line-3",    "4. Session / Subject",   16, "#555555", "font-style: italic;"),
    ("l4",   "h-line-4",    "5. Filter Value",        16, "#0F2A4A", "font-style: italic; margin-top: 3px;"),
]
PRINT_HEADER_MIN_PX = 8
PRINT_HEADER_MAX_PX = 60


def _hdr_style_key(line_key, field):
    return f"p2_hdr_style_{line_key}_{field}"


def get_print_header_styles():
    """Har header line ka (font_px, colour) session_state se padhta hai; na mile ya galat ho to default."""
    styles = {}
    for key, _cls, _label, d_px, d_color, _extra in PRINT_HEADER_LINES:
        try:
            px = int(st.session_state.get(_hdr_style_key(key, "size"), d_px))
        except (TypeError, ValueError):
            px = d_px
        px = max(PRINT_HEADER_MIN_PX, min(px, PRINT_HEADER_MAX_PX))
        color = str(st.session_state.get(_hdr_style_key(key, "color"), d_color))
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", color):
            color = d_color
        styles[key] = (px, color)
    return styles


def build_print_header_css():
    """Print HTML ke <style> me lagane ke liye .h-line-* ki CSS string banata hai."""
    styles = get_print_header_styles()
    css = []
    for key, css_class, _label, _d_px, _d_color, extra in PRINT_HEADER_LINES:
        px, color = styles[key]
        css.append(f".{css_class} {{ font-size: {px}px; color: {color}; {extra} }}")
    return "\n".join(css)


def render_print_header_style_controls():
    """Text boxes ke neeche har line ke liye Font Size + Colour ke controls dikhata hai.
    🆕 Ab isme do naye cheezein hain:
    1. 🔒 Lock/Unlock Button — jab Lock ho, to koi bhi galti se Font Size/Colour badal
       nahi sakta (sabhi number_input/color_picker/reset button disable ho jaate hain).
    2. 👁️ Live Preview — screen par turant dikha deta hai ki chuna hua Size/Colour print
       me kaisa dikhega, taaki bina print kiye hi confirm ho jaaye ki setting kaam kar rahi hai."""
    if "p2_hdr_style_locked" not in st.session_state:
        st.session_state.p2_hdr_style_locked = False

    def _reset_header_styles():
        for _k, *_rest in PRINT_HEADER_LINES:
            st.session_state.pop(_hdr_style_key(_k, "size"), None)
            st.session_state.pop(_hdr_style_key(_k, "color"), None)

    lock_col1, lock_col2 = st.columns([5, 2])
    with lock_col1:
        st.markdown("**🎨 हर हेडर लाइन का Font Size (px) और Colour**")
    with lock_col2:
        is_locked_now = st.session_state.p2_hdr_style_locked
        lock_btn_label = "🔒 Locked — खोलने हेतु क्लिक करें" if is_locked_now else "🔓 Unlocked — लॉक हेतु क्लिक करें"
        if st.button(lock_btn_label, key="p2_hdr_style_lock_toggle_btn", use_container_width=True,
                     type="secondary" if is_locked_now else "primary"):
            st.session_state.p2_hdr_style_locked = not is_locked_now
            st.rerun()

    is_locked = st.session_state.p2_hdr_style_locked
    if is_locked:
        st.caption("🔒 **सेटिंग्स लॉक हैं** — गलती से Font Size/Colour नहीं बदल सकते। बदलने के लिए पहले ऊपर वाला बटन दबाकर Unlock करें।")

    cols = st.columns(len(PRINT_HEADER_LINES))
    for col, (key, css_class, label, d_px, d_color, extra) in zip(cols, PRINT_HEADER_LINES):
        with col:
            st.number_input(f"{label} — Font Size (px)", min_value=PRINT_HEADER_MIN_PX,
                            max_value=PRINT_HEADER_MAX_PX, value=d_px, step=1,
                            key=_hdr_style_key(key, "size"), disabled=is_locked)
            st.color_picker(f"{label} — Colour", value=d_color, key=_hdr_style_key(key, "color"),
                             disabled=is_locked)

    # 👁️ Live Preview: yahi par turant dikha do ki Print me yeh size/colour kaisa dikhega —
    # print kiye bina hi turant confirm ho jaayega ki setting effect kar rahi hai.
    st.markdown("**👁️ Live Preview (यह असली Print जैसा ही दिखेगा):**")
    current_styles = get_print_header_styles()
    preview_html = ('<div style="border:1px dashed #C9973F; border-radius:6px; padding:10px 14px; '
                     'background:#fff; text-align:center;">')
    for key, css_class, label, d_px, d_color, extra in PRINT_HEADER_LINES:
        px, color = current_styles[key]
        preview_html += f'<div style="font-size:{px}px; color:{color}; {extra}">{label} — नमूना टेक्स्ट (Sample)</div>'
    preview_html += "</div>"
    st.markdown(preview_html, unsafe_allow_html=True)

    st.button("↩️ Font Size / Colour Default पर वापस", key="p2_hdr_style_reset_btn",
              on_click=_reset_header_styles, disabled=is_locked)


# डेटा स्टोरेज फ़ाइलों के पाथ और नाम परिभाषा
DB_FILE = "shared_student_database.csv"
STAGE_FILE = "merge_stage_database.csv"
CRED_FILE = "user_credentials_v15.json"
MAP_FILE = "column_mapping_schema.json"
PANEL_NAME_FILE = "panel_names_schema.json"
TWIN_MAP_FILE = "twin_column_mapping_schema.json"

# 🔒 P11: PERMANENT FIXED COLUMN MAPPINGS (हमेशा सक्रिय रहेंगी, चाहे JSON फ़ाइल रीसेट/डिलीट क्यों न हो जाए)
# 🟢 इसमें बदलाव किए बिना ये 2 मैपिंग हर बार ऐप स्टार्ट होने पर अपने आप लागू (enforce) हो जाएँगी:
#    1. Application Number  ↔  Admission Application Number
#    2. Payment Date        ↔  Admission Date
PERMANENT_TWIN_MAPPINGS = {
    "Application Number": "Admission Application Number",
    "Payment Date": "Admission Date"
}

# 🙈 P15: सिर्फ़ P15 की Master Grid से छुपाई जाने वाली कॉलम्स (permanent, code-level hide)
# 🟢 ध्यान दें: ये सिर्फ P15 की लिस्ट/ग्रिड से hide होती हैं — असली डेटा, P1 फॉर्म, और
# P11 वाला Twin-Sync इंजन (जो इन्हीं कॉलम्स को "Admission Application Number" /
# "Admission Date" से सिंक करता है) पूरी तरह सुरक्षित और सामान्य रूप से काम करता रहेगा।
P15_HIDDEN_GRID_COLUMNS = ["Application Number", "Payment Date"]
PRE_LOGIN_CONFIG_FILE = "pre_login_view_config.json"
DYNAMIC_LISTS_FILE = "p1_dynamic_lists_schema.json"

# 🟢 ADD THIS MISSING LINE HERE:
NOTICE_FILE = "notice_board_schema.json" 

# 🟢 P12 SYLLABUS MANAGER: subject-wise syllabus (file ya link) yahin store hoga
SYLLABUS_FILE = "subject_syllabus_schema.json"
SYLLABUS_UPLOAD_DIR = "syllabus_uploads"
# 🟢 Syllabus ke liye Year options — app me baaki jagah (P7/P10 etc.) jo standard Year
# labels use hote hain (1st Year, 2nd Year...) wahi yahan bhi use kar rahe hain, taaki
# poori app me Year ka matlab hamesha ek jaisa rahe.
SYLLABUS_YEAR_OPTIONS = ["1st Year", "2nd Year", "3rd Year", "4th Year", "5th Year", "6th Year"]
# 🟢 नया: PG (Post-Graduate) जैसे कोर्सेज़ के लिए Semester-wise Syllabus विकल्प — जैसे 2 Year का
# PG कोर्स हो to 4 Semester (1st Sem. से 4th Sem.) बनते हैं। P10 पैनल में जो Semester labels
# already इस्तेमाल होते हैं, वही यहाँ भी इस्तेमाल कर रहे हैं ताकि पूरी app में नाम एक जैसे रहें।
SYLLABUS_SEM_OPTIONS = [
    "1st Sem.", "2nd Sem.", "3rd Sem.", "4th Sem.", "5th Sem.", "6th Sem.",
    "7th Sem.", "8th Sem.", "9th Sem.", "10th Sem.", "11th Sem.", "12th Sem."
]

# डिफ़ॉल्ट कॉन्फ़िगरेशन बैकअप डिक्शनरी
DEFAULT_PRE_LOGIN_CONFIG = {
    "show_header_text": True,
    "header_mantra": "ॐ श्री गुरवे नमः",
    "system_title": "Permanent Shared Live Database System",
    "header_mantra_font_size": 24,   # 🟢 Mantra line ka font size (px)
    "header_title_font_size": 32,    # 🟢 Main title line ka font size (px)
    "notice_board_border_color": "#FF5733",
    "notice_board_bg_color": "#f9f9f9",
    "logo_width": 110,
    "logo_height": 110,
    "logo_fit_mode": "contain"
}

DEFAULT_DYNAMIC_LISTS = {
    "file_types": [
        "admission file", "admission fee file", "unique id file", 
        "roll no file", "enrollment file", "promotion file", "result file"
    ],
    "academic_years": [str(year) for year in range(2014, 2027)],
    "academic_sessions": [f"{year}-{str(year+1)[2:]}" for year in range(2014, 2027)]
}

DEFAULT_NOTICE = (
    "1. यह एक पूर्णतः सुरक्षित, लाइव क्लाउड स्टूडेंट डेटाबेस मैनेजमेंट सिस्टम है।\n"
    "2. डेटा प्रविष्टि, सुधार, स्कॉलरशिप वेरिफिकेशन या परीक्षा परिणाम अपडेट करने के लिए अधिकृत यूजर क्रेडेंशियल्स का उपयोग करें।\n"
    "3. बिना लॉगिन के डेटाबेस तक पहुँच पूर्णतः प्रतिबंधित है। किसी भी समस्या के लिए सुपर-एडमिन से संपर्क करें।"
)

DEFAULT_CREDENTIALS = {
    "admin": {"password": "admin15master", "role": "full_admin", "label": "👑 Super Admin (All 15 Panels Control)"},
    "p1_entry": {"password": "entry1123", "role": "p1_role", "label": "📝 P1: Student Data Onboarding Operator"},
    "p2_admission": {"password": "adm2123", "role": "p2_role", "label": "🎓 P2: Admission Control Manager"},
    "p3_unique": {"password": "uniq3123", "role": "p3_role", "label": "🆔 P3: Unique ID Assignment Manager"},
    "p4_roll": {"password": "roll4123", "role": "p4_role", "label": "🔢 P4: Roll Number Allocation Manager"},
    "p5_enrollment": {"password": "enr5123", "role": "p5_role", "label": "📑 P5: University Enrollment Manager"},
    "p6_scholarship": {"password": "sch6123", "role": "p6_role", "label": "💰 P6: Portal & Scholarship Tracker"},
    "p7_cce": {"password": "cce7123", "role": "p7_role", "label": "🖨️ P7: CCE panel & Foil Sheet Generator"},
    "p8_promotion": {"password": "pro8123", "role": "p8_role", "label": "📈 P8: Promotion panel Batch progression"},
    "p9_result": {"password": "res9123", "role": "p9_role", "label": "📊 P9: Result panel Exam Controller"},
    "p10_register": {"password": "reg10123", "role": "p10_role", "label": "📋 P10: Register panel Permanent Registry"},
    "p11_notice": {"password": "not11123", "role": "p11_role", "label": "📢 P11: System Informer Block"},
    "p12_login_view": {"password": "view12123", "role": "p12_role", "label": "📚 P12: Subject Syllabus Manager"},
    "p13_merge": {"password": "mrg13123", "role": "p13_role", "label": "🔀 P13: Merge & Approve Panel"},
    "p14_viewer": {"password": "view14123", "role": "p14_role", "label": "👁️ P14: Multi-Panel Inspection Window"}
}

DEFAULT_PANELS = {
    "P1": "Panal entry", "P2": "Admission panel", "P3": "Unique ID panel",
    "P4": "Roll No. panel", "P5": "Enrollment panel", "P6": "Scholarship panel",
    "P7": "CCE panel", "P8": "Promotion panel", "P9": "Result panel",
    "P10": "Register panel", "P11": "notice board info", "P12": "📚 Subject Syllabus Manager",
    "P13": "🔀 Merge & Approve Panel", "P14": "Panal viewer", "P15": "Panel admin"
}

DEFAULT_COLUMNS = [
    "Admission Year", "Admission Session", "Eligibility Name", "Admission Application Number",
    "Admission Date", "Unique ID", "Roll No.", "Application Enrollment No.",
    "Enrollment No.", "Student Name", "Father Name", "Mother Name", "Date of Birth",
    "Category", "Subject Code", "Subject", "Duration", "Mobile Number", "Email ID", "Address", "Status",
    "Current Year", "Application Number", "Student Abc Id", "Gender", "Admission Category", "Degree",
    "Branch", "Minor Subjects", "Vocational Subjects", "MDC Subjects", "PW/Ap/CE Subjects",
    "Admssion & Enrollment Fees", "Scholarship Name", "Payment Date", "Target Panel Visibility",
    "CCE Marks Obtained", "CCE Attendance Status", "Promotion Status", "Marks Obtained", "Result Status", "Exam Remarks",
    "Document Submit Status"
]

# ==========================================================
# 🧩 P3: UG/PG CHECKING APP (app__75_.py) — पूरा कोड इसी फ़ाइल में
#    (नीचे सहायक क्लासेस + _run_p3_ug_pg_app() फ़ंक्शन; P3 पैनल इसे चलाता है)
# ==========================================================
class _P3SubAppStop(BaseException):
    """Sub-app ke st.stop() ko sirf P3 tak rokne ke liye (poora app.py na ruke)."""

class _P3LazySidebar:
    """Sub-app ka sidebar P3 ke upar ek box me dikhta hai (app.py ke apne sidebar me gadbad na ho)."""
    def __init__(self):
        object.__setattr__(self, "_box", None)
    def _get(self):
        if object.__getattribute__(self, "_box") is None:
            object.__setattr__(self, "_box", st.container(border=True))
        return object.__getattribute__(self, "_box")
    def __getattr__(self, name):
        return getattr(self._get(), name)
    def __enter__(self):
        return self._get().__enter__()
    def __exit__(self, *a):
        return self._get().__exit__(*a)

class _P3StProxy:
    """Asli streamlit module ko chhue bina sub-app ke st.dataframe/markdown/title... badalne ke liye."""
    def __init__(self, real, over):
        object.__setattr__(self, "_real", real)
        object.__setattr__(self, "_over", over)
    def __getattr__(self, name):
        over = object.__getattribute__(self, "_over")
        if name in over:
            return over[name]
        return getattr(object.__getattribute__(self, "_real"), name)
    def __setattr__(self, name, value):
        object.__getattribute__(self, "_over")[name] = value

def _p3_stop():
    raise _P3SubAppStop()


def _run_p3_ug_pg_app(st):
    """P3 panel: app__75_.py (UG/PG checking app) ka poora code. `st` yahan ek proxy hai (neeche P3 branch dekhein),
    isliye is app ke st.dataframe/st.markdown/st.title... wale design-badlav sirf P3 ke andar lagte hain."""
    import pandas as pd
    import sqlite3
    import json
    import io
    import os
    import hashlib
    import xml.etree.ElementTree as ET
    from html.parser import HTMLParser
    import streamlit.components.v1 as components
    import html as _html
    import re as _re


    # =========================================================================
    # 📋 लिस्ट / टेबल डिज़ाइन: जिन लिस्ट में अपना रंग नहीं है उनमें एक-एक छोड़कर हल्की धारीदार (zebra) रो
    # (जिन टेबल में लाल/नीले/हरे रंग पहले से हैं, उन्हें बिल्कुल नहीं छेड़ा जाता)
    # =========================================================================
    _orig_st_dataframe = st.dataframe

    def _zebra_rows(d):
        out = pd.DataFrame("", index=d.index, columns=d.columns)
        out.iloc[1::2, :] = "background-color: #f4f7fd"
        return out

    def _designed_dataframe(data=None, *args, **kwargs):
        try:
            if (isinstance(data, pd.DataFrame) and 0 < len(data) <= 3000 and data.shape[1] > 0
                    and data.index.is_unique and data.columns.is_unique):
                data = data.style.apply(_zebra_rows, axis=None)
        except Exception:
            pass
        return _orig_st_dataframe(data, *args, **kwargs)

    st.dataframe = _designed_dataframe

    # =========================================================================
    # 🏷️ हेडलाइन डिज़ाइन: st.title / st.header / st.subheader और "#, ##, ###, ####" वाली markdown हेडिंग
    # अपने-आप ग्रेडिएंट बैनर बन जाती हैं (कोड में कहीं कुछ बदलने की ज़रूरत नहीं)
    # =========================================================================
    _orig_st_markdown = st.markdown
    _HEAD_RE = _re.compile(r'^\s*(#{1,4})\s+([^\n]+?)\s*$')

    def _banner_html(text, level):
        t = _html.escape(str(text)).replace("$", "&#36;")
        t = _re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
        return f'<div class="hb hb{int(level)}">{t}</div>'

    def _designed_markdown(body="", *args, **kwargs):
        if isinstance(body, str) and not args and not kwargs.get("unsafe_allow_html"):
            _m = _HEAD_RE.match(body)
            if _m:
                return _orig_st_markdown(_banner_html(_m.group(2), len(_m.group(1))), unsafe_allow_html=True)
        return _orig_st_markdown(body, *args, **kwargs)

    def _make_head_fn(level):
        def _fn(body="", *args, **kwargs):
            return _orig_st_markdown(_banner_html(body, level), unsafe_allow_html=True)
        return _fn

    # =========================================================================
    # ✍️ लिखा हुआ टेक्स्ट (st.write / st.caption / st.info / st.success / st.warning / st.error) का डिज़ाइन
    # =========================================================================
    _orig_st_caption = st.caption
    _orig_st_write = st.write
    _LIST_LIKE_RE = _re.compile(r'(^|\n)\s*([-*+]\s|\d+[.)]\s|\||#|>)')

    def _rich_text(t):
        t = _html.escape(str(t)).replace("$", "&#36;")
        t = _re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
        t = _re.sub(r"`([^`]+?)`", r"<code>\1</code>", t)
        return t.replace("\n", "<br>")

    def _plain_text_ok(body):
        return isinstance(body, str) and body.strip() != "" and not _LIST_LIKE_RE.search(body)

    _ALERT_SYMBOL = {"success": "✓", "info": "i", "warning": "!", "error": "✕"}

    _orig_alerts = {_k: getattr(st, _k) for _k in ("success", "info", "warning", "error")}

    def _make_alert_fn(kind):
        def _fn(body="", *args, icon=None, **kwargs):
            if not _plain_text_ok(body):
                # सूची/टेबल जैसा मार्कडाउन या गैर-टेक्स्ट → Streamlit का अपना अलर्ट (कुछ भी छूटेगा नहीं)
                if icon is not None:
                    kwargs["icon"] = icon
                return _orig_alerts[kind](body, *args, **kwargs)
            _ic = _html.escape(str(icon)) if icon else _ALERT_SYMBOL[kind]
            return _orig_st_markdown(
                f'<div class="al al-{kind}"><div class="al-ic">{_ic}</div><div class="al-tx">{_rich_text(body)}</div></div>',
                unsafe_allow_html=True
            )
        return _fn

    def _designed_caption(body="", *args, **kwargs):
        if _plain_text_ok(body) and not args and not kwargs:
            return _orig_st_markdown(f'<div class="cap">{_rich_text(body)}</div>', unsafe_allow_html=True)
        return _orig_st_caption(body, *args, **kwargs)

    def _designed_write(*args, **kwargs):
        if len(args) == 1 and not kwargs and _plain_text_ok(args[0]):
            return _orig_st_markdown(f'<div class="txt">{_rich_text(args[0])}</div>', unsafe_allow_html=True)
        return _orig_st_write(*args, **kwargs)

    st.success = _make_alert_fn("success")
    st.info = _make_alert_fn("info")
    st.warning = _make_alert_fn("warning")
    st.error = _make_alert_fn("error")
    st.caption = _designed_caption
    st.write = _designed_write

    st.markdown = _designed_markdown
    st.title = _make_head_fn(1)
    st.header = _make_head_fn(2)
    st.subheader = _make_head_fn(3)

    # =========================================================================
    # 🎨 प्रोफेशनल UI स्टाइलिंग (पूरे ऐप में कस्टम CSS)
    # =========================================================================
    st.markdown("""
<style>
    /* मुख्य कंटेनर पैडिंग */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }
    /* हैडिंग्स */
    h1, h2, h3 {
        font-family: 'Segoe UI', 'Trebuchet MS', sans-serif;
        letter-spacing: -0.3px;
    }
    h1 { color: #1a3c6e; }
    /* बटन */
    div.stButton > button {
        border-radius: 8px;
        font-weight: 600;
        border: 1px solid #d0d7e2;
        transition: all 0.15s ease-in-out;
    }
    div.stButton > button:hover {
        border-color: #1a73e8;
        color: #1a73e8;
    }
    div.stButton > button[kind="primary"] {
        background-color: #1a73e8;
    }
    /* डाउनलोड बटन */
    div.stDownloadButton > button {
        border-radius: 8px;
        font-weight: 600;
        background-color: #0f9d58;
        color: white;
        border: none;
    }
    div.stDownloadButton > button:hover {
        background-color: #0c8043;
        color: white;
    }
    /* साइडबार */
    section[data-testid="stSidebar"] {
        background-color: #f6f8fb;
        border-right: 1px solid #e3e8ef;
    }
    /* डेटाफ़्रेम / टेबल कार्ड जैसा दिखे */
    div[data-testid="stDataFrame"] {
        border: 1px solid #e3e8ef;
        border-radius: 10px;
        overflow: hidden;
    }
    /* मेट्रिक कार्ड्स */
    div[data-testid="stMetric"] {
        background-color: #f8fafc;
        border: 1px solid #e3e8ef;
        border-radius: 10px;
        padding: 12px 16px;
    }
    /* एक्सपैंडर */
    div[data-testid="stExpander"] {
        border: 1px solid #e3e8ef;
        border-radius: 10px;
    }
    /* टैब्स */
    button[data-baseweb="tab"] {
        font-weight: 600;
    }
    /* फुटर क्रेडिट */
    .app-footer {
        text-align: center;
        color: #8a94a6;
        font-size: 12.5px;
        padding: 18px 0 4px 0;
        border-top: 1px solid #e3e8ef;
        margin-top: 30px;
    }

    /* ============== 🔐 लॉगिन स्क्रीन स्टाइलिंग ============== */
    @keyframes floatIn {
        0% { opacity: 0; transform: translateY(14px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    .login-hero {
        text-align: center;
        animation: floatIn 0.6s ease-out;
        margin-bottom: 6px;
        margin-top: 38px;
        padding-top: 10px;
    }
    .login-hero .emoji-badge {
        font-size: 46px;
        display: inline-block;
        animation: floatIn 0.5s ease-out;
    }
    .login-hero .login-logo-img {
        border-radius: 14px;
        box-shadow: 0 6px 20px rgba(26, 60, 110, 0.18);
        animation: floatIn 0.5s ease-out;
        object-fit: contain;
        background: #ffffff;
        padding: 6px;
    }
    .login-hero h1 {
        font-size: 34px;
        font-weight: 800;
        margin: 6px 0 2px 0;
        background: linear-gradient(270deg, #1a73e8, #6a4cff, #0f9d58, #1a73e8);
        background-size: 600% 600%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: gradientShift 6s ease infinite;
    }
    .login-hero p {
        color: #6b7688;
        font-size: 15px;
        margin-top: 0;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        animation: floatIn 0.7s ease-out;
    }
    /* लॉगिन कार्ड (st.container(border=True)) को थोड़ा प्रीमियम लुक */
    div[data-testid="stForm"], div[data-testid="stVerticalBlockBorderWrapper"] > div {
        border-radius: 16px !important;
    }
    .login-badge-row {
        display: flex;
        justify-content: center;
        gap: 8px;
        flex-wrap: wrap;
        margin: 10px 0 18px 0;
    }
    .login-badge {
        background: linear-gradient(135deg, #eef3ff, #f3eefc);
        border: 1px solid #dde4f5;
        color: #4a5b8c;
        font-size: 12px;
        font-weight: 600;
        padding: 5px 12px;
        border-radius: 20px;
    }
    .farewell-box {
        text-align: center;
        animation: floatIn 0.5s ease-out;
        background: linear-gradient(135deg, #eafff0, #eef8ff);
        border: 1px solid #cdeedd;
        border-radius: 14px;
        padding: 14px;
        margin-bottom: 18px;
        color: #1a6e3c;
        font-weight: 600;
    }

    /* ============== 🎛️ Admin सेक्शन Hide / Show टॉगल बटन ============== */
    div[class*="st-key-admin_sec_btn_"] button {
        border-radius: 999px !important;
        font-weight: 700 !important;
        letter-spacing: 0.2px;
        padding: 6px 14px !important;
        border: none !important;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.15);
        transition: transform .12s ease, box-shadow .12s ease, filter .12s ease;
    }
    div[class*="st-key-admin_sec_btn_"] button,
    div[class*="st-key-admin_sec_btn_"] button p {
        color: #ffffff !important;
    }
    div[class*="st-key-admin_sec_btn_"] button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.22);
        filter: brightness(1.07);
    }
    div[class*="st-key-admin_sec_btn_"] button:active {
        transform: translateY(0) scale(0.98);
    }
    div[class*="st-key-admin_sec_btn_"][class*="__hidebtn"] button {
        background: linear-gradient(135deg, #ff7a59, #e8433f) !important;
    }
    div[class*="st-key-admin_sec_btn_"][class*="__showbtn"] button {
        background: linear-gradient(135deg, #2bb673, #0f9d58) !important;
    }
    .admin-sec-hidden-note {
        background: #f6f8fb;
        border: 1px dashed #c7d1e0;
        color: #6b7688;
        font-size: 13px;
        border-radius: 10px;
        padding: 8px 14px;
        margin: 2px 0 6px 0;
    }

    /* ============== ✨ प्रीमियम बटन डिज़ाइन (सभी बटन) ============== */
    div.stButton > button,
    div.stDownloadButton > button,
    div[data-testid="stFormSubmitButton"] > button {
        border-radius: 12px;
        font-weight: 700;
        font-size: 14.5px;
        letter-spacing: .2px;
        min-height: 44px;
        padding: .5rem 1.1rem;
        transition: transform .15s ease, box-shadow .15s ease, background .15s ease, border-color .15s ease, filter .15s ease;
    }
    /* सामान्य बटन: सफ़ेद कार्ड जैसा, हल्का शैडो */
    div.stButton > button:not([kind="primary"]) {
        background: linear-gradient(180deg, #ffffff, #f3f6fc);
        color: #1a3c6e;
        border: 1.5px solid #cfd9ea;
        box-shadow: 0 1px 2px rgba(26, 60, 110, .08);
    }
    div.stButton > button:not([kind="primary"]):hover {
        transform: translateY(-2px);
        border-color: #1a73e8;
        color: #1a73e8;
        background: linear-gradient(180deg, #ffffff, #e9f1ff);
        box-shadow: 0 8px 18px rgba(26, 115, 232, .18);
    }
    /* प्राइमरी बटन: नीला-जामुनी ग्रेडिएंट */
    div.stButton > button[kind="primary"],
    div[data-testid="stFormSubmitButton"] > button[kind="primary"],
    div[data-testid="stFormSubmitButton"] > button {
        background: linear-gradient(135deg, #1a73e8, #5b4bdb);
        color: #ffffff;
        border: none;
        box-shadow: 0 5px 16px rgba(91, 75, 219, .35);
    }
    div.stButton > button[kind="primary"] p,
    div[data-testid="stFormSubmitButton"] > button p { color: #ffffff; }
    div.stButton > button[kind="primary"]:hover,
    div[data-testid="stFormSubmitButton"] > button:hover {
        transform: translateY(-2px);
        filter: brightness(1.08);
        color: #ffffff;
        box-shadow: 0 10px 22px rgba(91, 75, 219, .42);
    }
    div.stButton > button:active,
    div.stDownloadButton > button:active,
    div[data-testid="stFormSubmitButton"] > button:active {
        transform: translateY(0) scale(.98);
        box-shadow: 0 1px 4px rgba(0, 0, 0, .18);
    }
    div.stButton > button:focus-visible,
    div.stDownloadButton > button:focus-visible {
        outline: 3px solid rgba(26, 115, 232, .35);
        outline-offset: 2px;
    }
    /* डाउनलोड बटन: हरा ग्रेडिएंट */
    div.stDownloadButton > button {
        background: linear-gradient(135deg, #22b573, #0b8f52);
        color: #ffffff;
        border: none;
        box-shadow: 0 5px 16px rgba(15, 157, 88, .32);
    }
    div.stDownloadButton > button p { color: #ffffff; }
    div.stDownloadButton > button:hover {
        transform: translateY(-2px);
        filter: brightness(1.07);
        color: #ffffff;
        background: linear-gradient(135deg, #22b573, #0b8f52);
        box-shadow: 0 10px 22px rgba(15, 157, 88, .42);
    }
    /* समरी का CSV बटन: आउटलाइन स्टाइल (XLSX हरे भरे बटन से अलग पहचान) */
    div[class*="st-key-db_dl_"]:not([class*="st-key-db_dl_xlsx_"]) button {
        background: #ffffff !important;
        border: 1.8px solid #0f9d58 !important;
        box-shadow: none !important;
    }
    div[class*="st-key-db_dl_"]:not([class*="st-key-db_dl_xlsx_"]) button,
    div[class*="st-key-db_dl_"]:not([class*="st-key-db_dl_xlsx_"]) button p {
        color: #0b7a4b !important;
    }
    div[class*="st-key-db_dl_"]:not([class*="st-key-db_dl_xlsx_"]) button:hover {
        background: #eafaf2 !important;
        box-shadow: 0 8px 18px rgba(15, 157, 88, .22) !important;
    }

    /* ============== 🧩 फ़िल्टर / इनपुट / टैब / मेट्रिक पॉलिश ============== */
    div[data-baseweb="select"] > div {
        border-radius: 10px;
        border-color: #cfd9ea;
        transition: border-color .15s ease, box-shadow .15s ease;
    }
    div[data-baseweb="select"] > div:hover { border-color: #1a73e8; }
    div[data-baseweb="select"] > div:focus-within {
        border-color: #1a73e8;
        box-shadow: 0 0 0 3px rgba(26, 115, 232, .18);
    }
    div[data-testid="stTextInput"] input {
        border-radius: 10px;
    }
    div[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within {
        box-shadow: 0 0 0 3px rgba(26, 115, 232, .18);
        border-radius: 10px;
    }
    button[data-baseweb="tab"] {
        border-radius: 10px 10px 0 0;
        padding: 10px 16px;
        transition: background .15s ease, color .15s ease;
    }
    button[data-baseweb="tab"]:hover { background: #eef4ff; }
    button[data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(180deg, #eaf2ff, #ffffff);
        color: #1a73e8;
    }
    div[data-testid="stMetric"] {
        border-left: 5px solid #1a73e8;
        box-shadow: 0 2px 8px rgba(26, 60, 110, .07);
        transition: transform .15s ease, box-shadow .15s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 18px rgba(26, 60, 110, .13);
    }

    /* ============== 🎓 डिग्री+ब्रांच समरी: बैनर + डाउनलोड पैनल ============== */
    .sum-banner {
        background: linear-gradient(135deg, #1a3c6e, #2f5fb3 60%, #5b4bdb);
        color: #ffffff;
        border-radius: 14px;
        padding: 14px 20px;
        margin: 4px 0 10px 0;
        box-shadow: 0 8px 22px rgba(26, 60, 110, .25);
        animation: floatIn .5s ease-out;
    }
    .sum-banner .t { font-size: 20px; font-weight: 800; letter-spacing: -.2px; }
    .dl-panel-head {
        display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
        margin: 18px 0 6px 0;
    }
    .dl-panel-head .h { font-size: 17px; font-weight: 800; color: #1a3c6e; }
    .dl-chip {
        font-size: 12.5px; font-weight: 700; padding: 4px 12px; border-radius: 999px;
        border: 1px solid #dde4f5; background: #f3f6fc; color: #3b4c73;
    }
    .dl-chip.red { background: #fdecee; border-color: #f5c2c7; color: #a61e2b; }
    /* ============== 🏷️ हेडलाइन बैनर (st.title / subheader / ### सब जगह) ============== */
    .hb {
        color: #ffffff;
        border-radius: 14px;
        margin: 8px 0 14px 0;
        font-family: 'Segoe UI', 'Trebuchet MS', sans-serif;
        font-weight: 800;
        letter-spacing: -.2px;
        line-height: 1.35;
        box-shadow: 0 8px 22px rgba(26, 60, 110, .25);
        animation: floatIn .5s ease-out;
    }
    .hb1 { font-size: 25px; padding: 16px 22px; background: linear-gradient(135deg, #1a3c6e, #2f5fb3 60%, #5b4bdb); }
    .hb2 { font-size: 22px; padding: 13px 20px; background: linear-gradient(135deg, #1f4d8f, #3468c4 60%, #6a5be0); }
    .hb3 { font-size: 19px; padding: 11px 18px; background: linear-gradient(135deg, #2b5aa8, #4a6fd6 60%, #6a5be0); box-shadow: 0 6px 16px rgba(43, 90, 168, .22); }
    .hb4 {
        font-size: 16px; padding: 8px 14px; color: #1a3c6e;
        background: linear-gradient(90deg, #eef3ff, #ffffff);
        border-left: 6px solid #5b4bdb; border-radius: 10px; box-shadow: none;
    }
    .mini-head {
        border-left: 5px solid #1a73e8; background: linear-gradient(90deg, #eef4ff, #ffffff);
        border-radius: 10px; padding: 7px 14px; margin: 4px 0 8px 0;
        color: #1a3c6e; font-weight: 800; font-size: 15px; line-height: 1.4;
    }
    .mini-head span { color: #6b7688; font-weight: 500; font-size: 12.5px; }

    /* ============== ✍️ लिखा हुआ टेक्स्ट: पैराग्राफ, कैप्शन, अलर्ट कार्ड ============== */
    .txt {
        font-size: 15px; line-height: 1.75; color: #2f3b57;
        background: linear-gradient(90deg, #f3f6fd, #ffffff 70%);
        border: 1px solid #e3e8ef; border-left: 5px solid #5b4bdb; border-radius: 12px;
        padding: 10px 16px; margin: 4px 0 10px 0;
        box-shadow: 0 2px 8px rgba(26, 60, 110, .05);
    }
    .txt b, .cap b, .al-tx b { color: #1a3c6e; font-weight: 800; }
    .al .al-tx b { color: inherit; }
    .cap {
        font-size: 13.5px; line-height: 1.7; color: #55607a;
        background: #f8fafc; border-left: 4px solid #b9c9ec; border-radius: 8px;
        padding: 7px 12px; margin: 2px 0 8px 0;
    }
    .txt code, .cap code, .al code {
        background: rgba(26, 60, 110, .09); border-radius: 6px; padding: 1px 6px; font-size: 90%;
    }
    .al {
        display: flex; align-items: center; gap: 12px;
        border: 1px solid transparent; border-left-width: 6px; border-radius: 12px;
        padding: 11px 16px; margin: 8px 0;
        box-shadow: 0 3px 10px rgba(0, 0, 0, .06);
        animation: floatIn .4s ease-out;
    }
    .al .al-ic {
        flex: 0 0 auto; width: 28px; height: 28px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-weight: 800; font-size: 15px; color: #ffffff;
    }
    .al .al-tx { font-size: 14.5px; line-height: 1.6; font-weight: 600; }
    .al-success { background: linear-gradient(90deg, #e8f9ef, #ffffff 85%); border-color: #bfe8d0; border-left-color: #0f9d58; color: #0b6b3a; }
    .al-success .al-ic { background: linear-gradient(135deg, #2bc07a, #0b8f52); }
    .al-info { background: linear-gradient(90deg, #e8f1ff, #ffffff 85%); border-color: #c3d8fa; border-left-color: #1a73e8; color: #1a4fa0; }
    .al-info .al-ic { background: linear-gradient(135deg, #3b8cf0, #1a5fd0); }
    .al-warning { background: linear-gradient(90deg, #fff4de, #ffffff 85%); border-color: #f6dca4; border-left-color: #f59e0b; color: #8a5a00; }
    .al-warning .al-ic { background: linear-gradient(135deg, #fbbf24, #e08a00); }
    .al-error { background: linear-gradient(90deg, #fdeaec, #ffffff 85%); border-color: #f5c2c7; border-left-color: #d92d3a; color: #a61e2b; }
    .al-error .al-ic { background: linear-gradient(135deg, #ff6a5c, #d92d3a); }

    /* ============== 🧭 विजेट लेबल / कैप्शन / डिवाइडर / टैब बार ============== */
    div[data-testid="stWidgetLabel"] p, div[data-testid="stWidgetLabel"] label {
        color: #1a3c6e;
        font-weight: 700;
    }
    div[data-testid="stCaptionContainer"] {
        border-left: 3px solid #c7d6f5;
        padding-left: 10px;
        color: #55607a;
    }
    .block-container hr {
        border: none !important;
        height: 3px !important;
        border-radius: 3px;
        background: linear-gradient(90deg, #1a73e8, #5b4bdb 45%, rgba(91, 75, 219, 0)) !important;
        opacity: .55;
        margin: 1.4rem 0 !important;
    }
    div[data-baseweb="tab-list"] {
        gap: 6px;
        background: #f3f6fc;
        padding: 6px 8px 0 8px;
        border-radius: 14px 14px 0 0;
        border-bottom: 1px solid #dde4f5;
    }
    div[data-baseweb="tab-highlight"] {
        height: 4px !important;
        border-radius: 4px;
        background: linear-gradient(90deg, #1a73e8, #5b4bdb) !important;
    }
    button[data-baseweb="tab"] { font-size: 15px; }

    /* ============== 🏷️ (पुराना तरीका, बचा हुआ) हेडलाइन CSS ============== */
    .block-container div[data-testid="stHeading"] h1,
    .block-container div[data-testid="stMarkdownContainer"] > h1,
    .block-container div[data-testid="stHeading"] h2,
    .block-container div[data-testid="stMarkdownContainer"] > h2,
    .block-container div[data-testid="stHeading"] h3,
    .block-container div[data-testid="stMarkdownContainer"] > h3 {
        background: linear-gradient(135deg, #1a3c6e, #2f5fb3 60%, #5b4bdb);
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff;
        border-radius: 14px;
        padding: 13px 20px !important;
        margin: 6px 0 12px 0 !important;
        box-shadow: 0 8px 22px rgba(26, 60, 110, .25);
        font-family: 'Segoe UI', 'Trebuchet MS', sans-serif;
        font-weight: 800 !important;
        letter-spacing: -.2px;
        line-height: 1.35 !important;
        animation: floatIn .5s ease-out;
    }
    /* बैनर के अंदर की हर चीज़ (लिंक-आइकन समेत) सफ़ेद */
    .block-container div[data-testid="stHeading"] h1 *,
    .block-container div[data-testid="stMarkdownContainer"] > h1 *,
    .block-container div[data-testid="stHeading"] h2 *,
    .block-container div[data-testid="stMarkdownContainer"] > h2 *,
    .block-container div[data-testid="stHeading"] h3 *,
    .block-container div[data-testid="stMarkdownContainer"] > h3 * {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff;
        fill: #ffffff;
    }
    /* बड़ा पैनल-टाइटल (st.title) */
    .block-container div[data-testid="stHeading"] h1,
    .block-container div[data-testid="stMarkdownContainer"] > h1 {
        font-size: 25px !important;
        padding: 16px 22px !important;
    }
    /* डैशबोर्ड बोर्ड आदि (##) : थोड़ा अलग नीला शेड */
    .block-container div[data-testid="stHeading"] h2,
    .block-container div[data-testid="stMarkdownContainer"] > h2 {
        font-size: 22px !important;
        background: linear-gradient(135deg, #1f4d8f, #3468c4 60%, #6a5be0);
    }
    /* सेक्शन हेडिंग (st.subheader / ###) */
    .block-container div[data-testid="stHeading"] h3,
    .block-container div[data-testid="stMarkdownContainer"] > h3 {
        font-size: 19px !important;
        padding: 11px 18px !important;
        background: linear-gradient(135deg, #2b5aa8, #4a6fd6 60%, #6a5be0);
        box-shadow: 0 6px 16px rgba(43, 90, 168, .22);
    }
    /* छोटी हेडिंग (####) : हल्का कार्ड + बाईं पट्टी */
    .block-container div[data-testid="stMarkdownContainer"] > h4 {
        background: linear-gradient(90deg, #eef3ff, #ffffff);
        border-left: 6px solid #5b4bdb;
        border-radius: 10px;
        padding: 8px 14px !important;
        margin: 8px 0 8px 0 !important;
        color: #1a3c6e;
        font-weight: 800;
    }

    /* ============== 📋 लिस्ट / टेबल कार्ड डिज़ाइन ============== */
    div[data-testid="stDataFrame"] {
        border: 1px solid #d7e0f0;
        border-radius: 14px;
        box-shadow: 0 4px 14px rgba(26, 60, 110, .08);
        transition: box-shadow .2s ease, border-color .2s ease;
    }
    div[data-testid="stDataFrame"]:hover {
        border-color: #9db7e8;
        box-shadow: 0 10px 26px rgba(26, 60, 110, .15);
    }
    .list-head {
        display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
        margin: 10px 0 6px 0;
    }
    .list-head .lh-title { font-size: 16px; font-weight: 800; color: #1a3c6e; }
    .list-head .lh-count {
        font-size: 12.5px; font-weight: 700; color: #ffffff; padding: 3px 12px; border-radius: 999px;
        background: linear-gradient(135deg, #1a73e8, #5b4bdb);
    }
    /* 📝 कारण की लिस्ट: हर ब्रांच का अलग कार्ड */
    .reason-card {
        border: 1px solid #e3e8ef; border-left: 6px solid #6b7688; border-radius: 12px;
        background: #ffffff; padding: 10px 14px; margin: 8px 0;
        box-shadow: 0 2px 8px rgba(26, 60, 110, .06);
    }
    .reason-card.red { border-left-color: #d92d3a; background: linear-gradient(90deg, #fff5f6, #ffffff 40%); }
    .reason-card.blue { border-left-color: #17a2b8; background: linear-gradient(90deg, #f0fbfd, #ffffff 40%); }
    .reason-card .rc-title { font-weight: 800; color: #1a3c6e; font-size: 14.5px; margin-bottom: 6px; }
    .reason-card .rs-line {
        font-size: 13px; line-height: 1.6; padding: 4px 10px; border-radius: 8px; margin: 3px 0;
    }
    .reason-card .rs-line.red { background: #fdecee; color: #a61e2b; }
    .reason-card .rs-line.blue { background: #e3f6fa; color: #0c5460; }
    .dl-hint {
        background: #f8fafc; border: 1px solid #e3e8ef; border-left: 4px solid #0f9d58;
        border-radius: 10px; padding: 8px 14px; margin-bottom: 10px;
        color: #55607a; font-size: 13px; line-height: 1.6;
    }

    /* ============== 🎯 अर्थ के हिसाब से बटन रंग (पूरे कोड में) ============== */
    /* 🔴 डिलीट / रीसेट / Revoke = लाल */
    div[class*="st-key-danger_"] button,
    div[class*="st-key-revoke_btn_"] button {
        background: linear-gradient(135deg, #ff6a5c, #d92d3a) !important;
        color: #ffffff !important;
        border: none !important;
        box-shadow: 0 5px 16px rgba(217, 45, 58, .32) !important;
    }
    div[class*="st-key-danger_"] button p,
    div[class*="st-key-revoke_btn_"] button p { color: #ffffff !important; }
    div[class*="st-key-danger_"] button:hover,
    div[class*="st-key-revoke_btn_"] button:hover {
        box-shadow: 0 10px 22px rgba(217, 45, 58, .42) !important;
        filter: brightness(1.07);
    }
    /* ✅ Approve = हरा */
    div[class*="st-key-approve_"] button {
        background: linear-gradient(135deg, #2bc07a, #0b8f52) !important;
        color: #ffffff !important;
        border: none !important;
        box-shadow: 0 5px 16px rgba(15, 157, 88, .32) !important;
    }
    div[class*="st-key-approve_"] button p { color: #ffffff !important; }
    div[class*="st-key-approve_"] button:hover {
        box-shadow: 0 10px 22px rgba(15, 157, 88, .42) !important;
        filter: brightness(1.07);
    }
    /* 💾 Save = आसमानी-नीला */
    div[class*="st-key-save_"] button,
    div[class*="st-key-blank_exempt_save_"] button {
        background: linear-gradient(135deg, #0ea5e9, #2563eb) !important;
        color: #ffffff !important;
        border: none !important;
        box-shadow: 0 5px 16px rgba(37, 99, 235, .32) !important;
    }
    div[class*="st-key-save_"] button p,
    div[class*="st-key-blank_exempt_save_"] button p { color: #ffffff !important; }
    div[class*="st-key-save_"] button:hover,
    div[class*="st-key-blank_exempt_save_"] button:hover {
        box-shadow: 0 10px 22px rgba(37, 99, 235, .42) !important;
        filter: brightness(1.07);
    }
    /* 🔒 Lock = सुनहरा */
    div[class*="st-key-lock_"] button {
        background: linear-gradient(135deg, #f7b731, #e08a00) !important;
        color: #ffffff !important;
        border: none !important;
        box-shadow: 0 5px 16px rgba(224, 138, 0, .32) !important;
    }
    div[class*="st-key-lock_"] button p { color: #ffffff !important; }
    div[class*="st-key-lock_"] button:hover {
        box-shadow: 0 10px 22px rgba(224, 138, 0, .42) !important;
        filter: brightness(1.07);
    }
    /* 🔓 Logout = लाल आउटलाइन */
    div[class*="st-key-logout_btn"] button {
        background: #ffffff !important;
        border: 1.8px solid #e57373 !important;
        box-shadow: none !important;
    }
    div[class*="st-key-logout_btn"] button,
    div[class*="st-key-logout_btn"] button p { color: #c62828 !important; }
    div[class*="st-key-logout_btn"] button:hover {
        background: #fdecee !important;
        box-shadow: 0 8px 18px rgba(198, 40, 40, .2) !important;
    }
    /* बंद (disabled) बटन */
    div.stButton > button:disabled,
    div.stDownloadButton > button:disabled {
        opacity: .5 !important;
        cursor: not-allowed !important;
        transform: none !important;
        box-shadow: none !important;
        filter: grayscale(.4);
    }

    /* ============== 🔘 रेडियो = पिल (गोली) स्विच ============== */
    div[data-testid="stRadio"] div[role="radiogroup"] { gap: 8px; flex-wrap: wrap; }
    div[data-testid="stRadio"] label[data-baseweb="radio"] {
        background: #f3f6fc;
        border: 1.5px solid #cfd9ea;
        border-radius: 999px;
        padding: 8px 18px;
        margin: 0 !important;
        cursor: pointer;
        display: flex !important;
        align-items: center;
        transition: all .15s ease;
    }
    div[data-testid="stRadio"] label[data-baseweb="radio"] > div:first-of-type:not(:has([data-testid="stMarkdownContainer"])) {
        display: none !important;
    }
    div[data-testid="stRadio"] label[data-baseweb="radio"]:hover {
        border-color: #1a73e8;
        background: #e9f1ff;
        transform: translateY(-1px);
    }
    div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) {
        background: linear-gradient(135deg, #1a73e8, #5b4bdb);
        border-color: transparent;
        box-shadow: 0 5px 14px rgba(91, 75, 219, .32);
    }
    div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked),
    div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) * {
        color: #ffffff !important;
        font-weight: 700;
    }

    /* ============== ☑️ चेकबॉक्स / एक्सपैंडर / टैग / अपलोडर ============== */
    div[data-testid="stCheckbox"] label {
        padding: 6px 12px;
        border-radius: 10px;
        transition: background .15s ease;
    }
    div[data-testid="stCheckbox"] label:hover { background: #eef4ff; }
    div[data-testid="stExpander"] summary {
        font-weight: 700;
        border-radius: 10px;
        transition: background .15s ease;
    }
    div[data-testid="stExpander"] summary:hover { background: #f3f6fc; }
    span[data-baseweb="tag"] {
        background: linear-gradient(135deg, #1a73e8, #5b4bdb) !important;
        border-radius: 999px !important;
        color: #ffffff !important;
        font-weight: 600;
    }
    span[data-baseweb="tag"] span, span[data-baseweb="tag"] svg { color: #ffffff !important; fill: #ffffff !important; }
    section[data-testid="stFileUploaderDropzone"] {
        border: 2px dashed #9db7e8;
        border-radius: 14px;
        background: linear-gradient(180deg, #f8fbff, #eef4ff);
        transition: all .15s ease;
    }
    section[data-testid="stFileUploaderDropzone"]:hover {
        border-color: #1a73e8;
        background: #e9f1ff;
        box-shadow: 0 6px 18px rgba(26, 115, 232, .15);
    }
    section[data-testid="stFileUploaderDropzone"] button {
        border-radius: 10px;
        font-weight: 700;
        background: linear-gradient(135deg, #1a73e8, #5b4bdb);
        color: #ffffff;
        border: none;
        box-shadow: 0 4px 12px rgba(91, 75, 219, .3);
        transition: transform .15s ease, filter .15s ease;
    }
    section[data-testid="stFileUploaderDropzone"] button:hover {
        transform: translateY(-1px);
        filter: brightness(1.08);
        color: #ffffff;
    }
</style>
""", unsafe_allow_html=True)

    def render_footer():
        st.markdown(
            "<div class='app-footer'>🛠️ Professionally Developed &amp; Maintained &nbsp;|&nbsp; "
        "NEP Master Data System © 2026</div>",
            unsafe_allow_html=True
        )

    def inline_section_toggle(key, header_html, default_open=True):
        """किसी भी टेबल/सेक्शन के हेडर के साथ डिज़ाइनर Hide / Show बटन लगाता है।
    True = खुला (टेबल दिखाओ), False = छिपा।"""
        state_key = f"inline_sec_open_{key}"
        if state_key not in st.session_state:
            st.session_state[state_key] = default_open
        is_open = st.session_state[state_key]

        head_col, btn_col = st.columns([5, 1.6])
        with head_col:
            st.markdown(header_html, unsafe_allow_html=True)
        with btn_col:
            if is_open:
                btn_label, btn_key = "🙈 Hide करें", f"admin_sec_btn_{key}__hidebtn"
            else:
                btn_label, btn_key = "👁️ Show करें", f"admin_sec_btn_{key}__showbtn"
            if st.button(btn_label, key=btn_key, use_container_width=True):
                st.session_state[state_key] = not is_open
                st.rerun()

        if not is_open:
            st.markdown(
                "<div class='admin-sec-hidden-note'>🙈 यह समरी अभी छिपी हुई है — दिखाने के लिए दाईं ओर 'Show करें' दबाएँ।</div>",
                unsafe_allow_html=True
            )
        return is_open

    def admin_section_toggle(key, title, caption=None, default_open=True):
        """Admin पैनल के हर सेक्शन के हेडर के साथ डिज़ाइनर Hide / Show बटन लगाता है।
    True लौटाए तो सेक्शन खुला है (कंटेंट दिखाओ), False हो तो छिपा है।"""
        state_key = f"admin_sec_open_{key}"
        if state_key not in st.session_state:
            st.session_state[state_key] = default_open
        is_open = st.session_state[state_key]

        head_col, btn_col = st.columns([5, 1.6])
        with head_col:
            st.subheader(title)
            if caption:
                st.caption(caption)
        with btn_col:
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            if is_open:
                btn_label, btn_key = "🙈 Hide करें", f"admin_sec_btn_{key}__hidebtn"
            else:
                btn_label, btn_key = "👁️ Show करें", f"admin_sec_btn_{key}__showbtn"
            if st.button(btn_label, key=btn_key, use_container_width=True):
                st.session_state[state_key] = not is_open
                st.rerun()

        if not is_open:
            st.markdown(
                "<div class='admin-sec-hidden-note'>🙈 यह सेक्शन अभी छिपा हुआ है — दिखाने के लिए दाईं ओर 'Show करें' दबाएँ।</div>",
                unsafe_allow_html=True
            )
        return is_open

    # =========================================================================
    # डेटाबेस सेटअप - टेबल्स संरचना (Raw, Permanent और Rules Lock)
    # =========================================================================
    conn = sqlite3.connect("nep_master_perma_db.db", check_same_thread=False)
    cursor = conn.cursor()

    # 1. अस्थायी स्टेजिंग स्टोरेज (Panel 1 से Upload होकर यहाँ आएगा)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS raw_store (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_json TEXT
    )
""")

    # 2. परमानेंट स्टोरेज (Panel 2 से Approve होकर UG/PG यहाँ आएगा)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS perma_store (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_json TEXT,
        course_type TEXT
    )
""")

    # 3. परमानेंट नियम लॉकिंग स्टोरेज (पुरानी खराब टेबल को डिलीट करके नया बनाने का ऑटो-सिस्टम)
    try:
        # चेक करना कि क्या टेबल सही है
        cursor.execute("SELECT panel_prefix FROM locked_rules LIMIT 1")
    except sqlite3.OperationalError:
        # अगर कोई भी गड़बड़ (जैसे कॉलम गायब होना) मिले, तो पुरानी टेबल हटा दें
        cursor.execute("DROP TABLE IF EXISTS locked_rules")
        conn.commit()

    # अब बिल्कुल सही और नए स्ट्रक्चर के साथ टेबल बनाएं
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS locked_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        panel_prefix TEXT UNIQUE,
        rules_json TEXT
    )
""")
    conn.commit()

    # सुनिश्चित करें कि टेबल बनने के बाद डेटाबेस में बदलाव सुरक्षित (Commit) हो जाएं
    conn.commit()

    # 4. पैनल-वाइज पासवर्ड + हाइड/अनहाइड स्टोरेज (6 पैनल्स के लिए)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS panel_auth (
        panel_key TEXT PRIMARY KEY,
        password TEXT,
        hidden INTEGER DEFAULT 0
    )
""")
    conn.commit()

    # डिफ़ॉल्ट पासवर्ड (सिर्फ पहली बार, जब टेबल में डेटा न हो, तभी डाले जाएंगे)
    _default_panel_passwords = {
        "p2": "p2pass",
        "p3": "ug",       # पहले Teacher_UG का पासवर्ड
        "p4": "pg",       # पहले Teacher_PG का पासवर्ड
        "p5": "p5pass",
        "p6": "psv123",   # पहले Admin का पासवर्ड
    }
    for _pk, _pw in _default_panel_passwords.items():
        cursor.execute("INSERT OR IGNORE INTO panel_auth (panel_key, password, hidden) VALUES (?, ?, 0)", (_pk, _pw))
    conn.commit()

    # पैनल-की और उसके डिस्प्ले नाम की मैपिंग
    PANEL_KEY_TO_NAME = {
        "p2": "💻 2. Work / Approve Panel",
        "p3": "🎓 3. UG Panel",
        "p4": "📜 4. PG Panel",
        "p5": "📊 5. Dashboard / Counter Panel",
        "p6": "⚙️ 6. Admin Panel",
    }
    PANEL_NAME_TO_KEY = {v: k for k, v in PANEL_KEY_TO_NAME.items()}

    def get_panel_password(panel_key):
        cursor.execute("SELECT password FROM panel_auth WHERE panel_key = ?", (panel_key,))
        row = cursor.fetchone()
        return row[0] if row else None

    def is_panel_hidden(panel_key):
        cursor.execute("SELECT hidden FROM panel_auth WHERE panel_key = ?", (panel_key,))
        row = cursor.fetchone()
        return bool(row[0]) if row else False

    def set_panel_password(panel_key, new_password):
        cursor.execute("UPDATE panel_auth SET password = ? WHERE panel_key = ?", (new_password, panel_key))
        conn.commit()

    def set_panel_hidden(panel_key, hidden_flag):
        cursor.execute("UPDATE panel_auth SET hidden = ? WHERE panel_key = ?", (1 if hidden_flag else 0, panel_key))
        conn.commit()

    # 5b. ✅ सब्जेक्ट अप्रूवल स्टोरेज (Panel 3/4 में "गलत विषय" को मैन्युअली Approve करने के लिए)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS subject_approvals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_key TEXT,
        panel_prefix TEXT,
        approved_by TEXT,
        approved_at TEXT,
        UNIQUE(student_key, panel_prefix)
    )
""")
    conn.commit()

    # 5. ऐप सेटिंग्स स्टोरेज (Login टाइटल + लोगो — सिर्फ Admin बदल सकता है)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS app_settings (
        setting_key TEXT PRIMARY KEY,
        setting_value TEXT
    )
""")
    conn.commit()

    def get_app_setting(key, default=None):
        cursor.execute("SELECT setting_value FROM app_settings WHERE setting_key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row and row[0] is not None else default

    def set_app_setting(key, value):
        cursor.execute("""
        INSERT INTO app_settings (setting_key, setting_value) VALUES (?, ?)
        ON CONFLICT(setting_key) DO UPDATE SET setting_value = excluded.setting_value
    """, (key, value))
        conn.commit()

    def delete_app_setting(key):
        cursor.execute("DELETE FROM app_settings WHERE setting_key = ?", (key,))
        conn.commit()

    # =========================================================================
    # परमानेंट डेटा लोड करने का फंक्शन (perma_store से UG/PG डेटा पढ़ने के लिए)
    # =========================================================================
    def load_permanent_data(course_type):
        cursor.execute("SELECT data_json FROM perma_store WHERE course_type = ?", (course_type,))
        rows = cursor.fetchall()
        if not rows:
            return pd.DataFrame()
        all_records = []
        for (data_json,) in rows:
            try:
                records = json.loads(data_json)
                if isinstance(records, list):
                    all_records.extend(records)
                else:
                    all_records.append(records)
            except (json.JSONDecodeError, TypeError):
                continue
        if not all_records:
            return pd.DataFrame()
        return pd.DataFrame(all_records)

    def load_master_data():
        """मास्टर फ़ाइल (shared_student_database.csv) का लाइव डेटा लौटाता है — अलग Entry/Upload पैनल की जगह।"""
        try:
            _m = load_live_data()
        except Exception:
            return pd.DataFrame()
        if _m is None or _m.empty:
            return pd.DataFrame()
        # पूरी तरह खाली रोज़ हटाना
        _m = _m.loc[~(_m.astype(str).apply(lambda c: c.str.strip()).eq("").all(axis=1))].reset_index(drop=True)
        return _m

    import datetime

    # =========================================================================
    # ✅ "गलत विषय" Approve सिस्टम — हेल्पर फंक्शन्स
    # =========================================================================
    def find_student_key_col(df):
        """छात्र की पहचान के लिए सबसे उपयुक्त कॉलम ढूंढना (Roll/Enrollment/Name)"""
        priority_keywords = ['roll', 'enrollment', 'enroll', 'admission', 'regn', 'registration', 'uid', 'scholar']
        for kw in priority_keywords:
            col = next((c for c in df.columns if kw in c.lower()), None)
            if col:
                return col
        return next((c for c in df.columns if 'name' in c.lower()), None)

    def get_student_key(row, position, key_col):
        """हर छात्र के लिए एक यूनीक 'key' बनाना (approvals स्टोर करने के लिए)"""
        if key_col and key_col in row.index and not pd.isna(row[key_col]) and str(row[key_col]).strip():
            return str(row[key_col]).strip()
        return f"row-{position}"

    def get_approval(student_key, prefix):
        cursor.execute(
            "SELECT approved_by, approved_at FROM subject_approvals WHERE student_key = ? AND panel_prefix = ?",
            (student_key, prefix)
        )
        return cursor.fetchone()

    def add_approval(student_key, prefix, approved_by):
        cursor.execute("""
        INSERT INTO subject_approvals (student_key, panel_prefix, approved_by, approved_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(student_key, panel_prefix) DO UPDATE SET
            approved_by = excluded.approved_by, approved_at = excluded.approved_at
    """, (student_key, prefix, approved_by, datetime.datetime.now().strftime("%d-%m-%Y %H:%M")))
        conn.commit()

    def remove_approval(student_key, prefix):
        cursor.execute("DELETE FROM subject_approvals WHERE student_key = ? AND panel_prefix = ?", (student_key, prefix))
        conn.commit()

    def get_all_approvals(prefix):
        cursor.execute(
            "SELECT student_key, approved_by, approved_at FROM subject_approvals WHERE panel_prefix = ? ORDER BY approved_at DESC",
            (prefix,)
        )
        return cursor.fetchall()

    def render_print_button(df, title, button_label="🖨️ इस लिस्ट को A4 पर प्रिंट करें", key_suffix="", orientation="portrait"):
        """दिए गए DataFrame को A4-साइज़ प्रिंट-फ्रेंडली फॉर्मेट में एक नई विंडो में खोलकर सीधे प्रिंट डायलॉग खोलता है।
    orientation: 'portrait' या 'landscape' — यह तय करता है कि प्रिंट पेज सीधा (खड़ा) रहेगा या आड़ा।"""
        orientation = "landscape" if str(orientation).lower().startswith("land") else "portrait"
        _pdf = df.copy()
        if "क्र.सं." not in _pdf.columns and "क्र." not in _pdf.columns:
            _pdf.insert(0, "क्र.", range(1, len(_pdf) + 1))
        table_html = _pdf.to_html(index=False, escape=True, border=0)
        _orient_txt = "लैंडस्केप" if orientation == "landscape" else "पोर्ट्रेट"
        full_html = f"""
    <html>
    <head>
    <meta charset="utf-8">
    <title>{title}</title>
    <style>
        @page {{ size: A4 {orientation}; margin: 14mm; }}
        * {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
        body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #1a1a1a; }}
        .hdr {{ text-align: center; border-bottom: 3px solid #1a3c6e; padding-bottom: 8px; margin-bottom: 12px; }}
        h2 {{ color: #1a3c6e; margin: 0 0 4px 0; font-size: 20px; letter-spacing: -.2px; }}
        p.meta {{ color: #55607a; font-size: 12px; margin: 0; }}
        p.meta b {{ color: #1a3c6e; }}
        table {{ width: 100%; border-collapse: collapse; border: 1px solid #9db0d3; }}
        thead {{ display: table-header-group; }}
        tr {{ page-break-inside: avoid; }}
        th, td {{ border: 1px solid #c3cee6; padding: 6px 8px; font-size: 12px; text-align: left; word-break: break-word; }}
        th {{ background-color: #1a3c6e; color: #ffffff; font-weight: 700; border-color: #1a3c6e; }}
        tbody tr:nth-child(even) {{ background-color: #f1f5fc; }}
        td:first-child, th:first-child {{ text-align: center; width: 4%; }}
        .foot {{ margin-top: 10px; font-size: 11.5px; color: #55607a; text-align: right; }}
    </style>
    </head>
    <body>
        <div class="hdr">
            <h2>{title}</h2>
            <p class="meta">तारीख़: {datetime.datetime.now().strftime('%d-%m-%Y %H:%M')} &nbsp;|&nbsp; पेज: A4 ({_orient_txt}) &nbsp;|&nbsp; <b>कुल रिकॉर्ड: {len(_pdf)}</b></p>
        </div>
        {table_html}
        <div class="foot">— लिस्ट समाप्त • कुल {len(_pdf)} रिकॉर्ड —</div>
    </body>
    </html>
    """
        escaped_json = json.dumps(full_html)
        btn_html = f"""
    <style>
        body {{ margin: 0; padding: 4px 2px; background: transparent; }}
        .pbtn {{
            display: inline-flex; align-items: center; justify-content: center; gap: 8px;
            background: linear-gradient(135deg, #1a73e8, #5b4bdb);
            color: #ffffff; border: none; border-radius: 12px;
            padding: 11px 22px; min-height: 44px; box-sizing: border-box;
            font-family: 'Segoe UI', 'Trebuchet MS', sans-serif;
            font-weight: 700; font-size: 14.5px; letter-spacing: .2px;
            cursor: pointer;
            box-shadow: 0 5px 16px rgba(91, 75, 219, .35);
            transition: transform .15s ease, box-shadow .15s ease, filter .15s ease;
        }}
        .pbtn:hover {{ transform: translateY(-2px); filter: brightness(1.08); box-shadow: 0 10px 22px rgba(91, 75, 219, .42); }}
        .pbtn:active {{ transform: translateY(0) scale(.98); box-shadow: 0 1px 4px rgba(0,0,0,.2); }}
        .pbtn:focus-visible {{ outline: 3px solid rgba(26, 115, 232, .35); outline-offset: 2px; }}
    </style>
    <button id="printBtn_{key_suffix}" class="pbtn">
        {button_label}
    </button>
    <script>
        document.getElementById("printBtn_{key_suffix}").onclick = function() {{
            var content = {escaped_json};
            var w = window.open('', '_blank');
            w.document.write(content);
            w.document.close();
            w.focus();
            setTimeout(function() {{ w.print(); }}, 300);
        }};
    </script>
    """
        components.html(btn_html, height=64)

    # Session States Management
    if "deleted_cols" not in st.session_state: st.session_state["deleted_cols"] = []

    # 🔓 P3 के अंदर अलग लॉगिन पैनल की ज़रूरत नहीं — मुख्य ऐप में लॉगिन पहले ही हो चुका है।
    # सीधे साइडबार से पैनल चुनकर काम किया जाता है।
    panel_key = "p6"
    is_admin_session = True  # सभी पैनल (Hide किए हुए भी) खुले रहेंगे

    st.sidebar.markdown(
        """
    <div style="background: linear-gradient(135deg, #eef6ff, #f3fff5); border: 1px solid #d7e6f9;
                border-radius: 12px; padding: 12px 14px; margin-bottom: 10px;">
        <div style="font-size:11px; color:#7a869f; font-weight:600; letter-spacing:0.5px;">पैनल चुनें</div>
    </div>
    """,
        unsafe_allow_html=True
    )
    active_panel = st.sidebar.selectbox(
        "🗂️ पैनल:",
        [PANEL_KEY_TO_NAME[k] for k in ["p2", "p3", "p4", "p5", "p6"]],
        key="p3_panel_selector"
    )

    import io
    from openpyxl.styles import PatternFill, Border, Side

    # =========================================================================
    # 🔀 UG / PG रूटिंग: कौन सी डिग्री किस डेटाबेस (UG या PG) में जाएगी
    # =========================================================================
    # P2 का ऑटो-विभाजन और P4 (PG Panel) का फ़िल्टर — दोनों यही एक सूची इस्तेमाल करते हैं, ताकि कोई डिग्री
    # P2 में PG में तो जाए पर P4 में दिखे ही नहीं (या उल्टा) — ऐसा न हो। (LL.M. और M.Tech पहले इस सूची में नहीं थे।)
    PG_ROUTE_KEYWORDS = ["ma", "msc", "mcom", "mba", "mca", "post grad", "pg", "grad", "llm", "mtech"]
    # P3 (UG Panel) में जो डिग्री दिखाई जाती हैं
    UG_ALLOWED_KEYWORDS = ["ba", "bsc", "bcom", "bhsc", "bba", "bca", "computer"]

    def is_pg_route_value(v):
        val = str(v).lower().replace(".", "").replace(" ", "").strip()
        return any(k in val for k in PG_ROUTE_KEYWORDS)

    # =========================================================================
    # ⚪ खाली-छूट (Blank Exemption): जिन डिग्री+ब्रांच में Minor/MDC/Voc/PW हमेशा खाली रहते हैं
    # =========================================================================
    def _norm_blank_label(v):
        s_ = "" if pd.isna(v) else str(v).strip()
        return s_ if (s_ and s_.lower() != "nan") else "(खाली/Blank)"

    def detect_deg_branch_cols(df):
        """डिग्री और ब्रांच कॉलम पहचानना (Minor/MDC/Voc/PW वाले कॉलम को ब्रांच न मानना)।"""
        skip_kw = ['minor', 'mdc', 'voc', 'skill', 'pw', 'project']
        cols = list(df.columns)
        deg = next((c for c in cols if any(k in str(c).lower() for k in ['deg', 'course', 'class'])), None)
        br = None
        for kws in (['branch', 'stream'], ['subject']):
            br = next((c for c in cols if c != deg and any(k in str(c).lower() for k in kws)
                       and not any(k in str(c).lower() for k in skip_kw)), None)
            if br is not None:
                break
        return deg, br

    def get_blank_exempt_pairs(prefix=None):
        """सेव की हुई (डिग्री, ब्रांच) जोड़ियाँ। prefix=None हो तो UG + PG दोनों की मिलाकर।"""
        pairs = set()
        for pf in ([prefix] if prefix else ["ug", "pg"]):
            raw = get_app_setting(f"blank_exempt_{pf}", "[]")
            try:
                for item in json.loads(raw):
                    if isinstance(item, (list, tuple)) and len(item) == 2:
                        pairs.add((str(item[0]), str(item[1])))
            except Exception:
                pass
        return pairs

    def set_blank_exempt_pairs(prefix, pairs):
        set_app_setting(f"blank_exempt_{prefix}", json.dumps(sorted([list(p) for p in pairs]), ensure_ascii=False))

    def blank_exempt_mask(df, prefix=None):
        """हर रो के लिए True/False: क्या इस रो की डिग्री+ब्रांच 'खाली-छूट' में है (तो Minor..PW का खाली नीला नहीं होगा)।"""
        n = len(df)
        pairs = get_blank_exempt_pairs(prefix)
        if n == 0 or not pairs:
            return pd.Series([False] * n, index=df.index)
        dc, bc = detect_deg_branch_cols(df)
        deg_lbl = df[dc].map(_norm_blank_label) if dc else pd.Series(["—"] * n, index=df.index)
        br_lbl = df[bc].map(_norm_blank_label) if bc else pd.Series(["—"] * n, index=df.index)
        return pd.Series([(d, b) in pairs for d, b in zip(deg_lbl, br_lbl)], index=df.index)

    def generate_colored_excel_bytes(df_filtered, deg_col, br_col, minor_col_found, mdc_col_found, voc_col_found, pw_col_found, master_rules=None, sheet_name="Verified_Data", approved_keys=None, key_col=None, prefix=None):
        """
    🔧 रीयूज़ेबल फ़ंक्शन: किसी भी DataFrame को रंगीन (🔴 गलत / 🔵 खाली / 🟢 Approved) Excel bytes में बदलता है।
    Panel 3/4 और Admin Panel — दोनों जगह इसी फ़ंक्शन का इस्तेमाल होता है, ताकि रंग-कोडिंग हमेशा एक जैसी रहे।
    approved_keys: उन छात्रों की student_key की list/set, जिन्हें गलत विषय होने के बावजूद Approve किया जा चुका है (उन्हें लाल नहीं, हरा दिखाया जाएगा)।
    """
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_filtered.to_excel(writer, index=False, sheet_name=sheet_name)
            workbook = writer.book
            worksheet = writer.sheets[sheet_name]

            blue_fill = PatternFill(start_color="D1ECF1", end_color="D1ECF1", fill_type="solid")   # ब्लैंक = नीला
            red_fill = PatternFill(start_color="F8D7DA", end_color="F8D7DA", fill_type="solid")     # गलत = लाल
            green_fill = PatternFill(start_color="D4EDDA", end_color="D4EDDA", fill_type="solid")   # Approved = हरा
            thin_border = Border(left=Side(style='thin', color='CCCCCC'), right=Side(style='thin', color='CCCCCC'),
                                 top=Side(style='thin', color='CCCCCC'), bottom=Side(style='thin', color='CCCCCC'))

            targets_xl = {minor_col_found: 'minor', mdc_col_found: 'mdc', voc_col_found: 'voc', pw_col_found: 'pw'}
            approved_keys = approved_keys or set()
            _exempt_list = blank_exempt_mask(df_filtered, prefix).tolist()   # ⚪ खाली-छूट वाली डिग्री+ब्रांच

            for idx, (_, row) in enumerate(df_filtered.iterrows()):
                row_num = idx + 2  # एक्सेल डेटा रो

                deg_part = str(row[deg_col]) if deg_col and deg_col in df_filtered.columns else ""
                br_part = str(row[br_col]) if br_col and br_col in df_filtered.columns else ""
                student_deg = (deg_part + " " + br_part).lower().replace(".", "").replace(" ", "").strip()

                is_row_approved = get_student_key(row, idx, key_col) in approved_keys

                matched_key = "Default"
                if master_rules:
                    sorted_keys = sorted(master_rules.keys(), key=len, reverse=True)
                    for rule_key in sorted_keys:
                        rule_words = [w.lower().replace(".", "").strip() for w in rule_key.split() if w.strip()]
                        if rule_words and all(w in student_deg for w in rule_words):
                            matched_key = rule_key
                            break
                c_rule = master_rules.get(matched_key, {"minor": [], "mdc": [], "voc": [], "pw": []}) if master_rules else {"minor": [], "mdc": [], "voc": [], "pw": []}

                for col_idx, col_name in enumerate(df_filtered.columns, start=1):
                    cell = worksheet.cell(row=row_num, column=col_idx)
                    val = row[col_name]

                    if col_name == br_col:
                        if pd.isna(val) or str(val).strip() == "":
                            cell.fill = blue_fill
                            cell.border = thin_border
                        continue

                    if col_name in targets_xl:
                        rule_key = targets_xl[col_name]

                        if pd.isna(val) or str(val).strip() == "":
                            if not _exempt_list[idx]:
                                cell.fill = blue_fill
                                cell.border = thin_border
                        else:
                            val_clean = str(val).strip().lower().replace(".", "").replace(" ", "")
                            valid_list = c_rule.get(rule_key, [])
                            valid_set = {str(x).strip().lower().replace(".", "").replace(" ", "") for x in valid_list}

                            if valid_set and (val_clean not in valid_set):
                                cell.fill = green_fill if is_row_approved else red_fill
                                cell.border = thin_border

        return output.getvalue()

    def generate_master_excel_bytes(sheets_data):
        """
    🆕 P5 Dashboard के 'मास्टर एक्सेल डाउनलोड' बटन के लिए रीयूज़ेबल फ़ंक्शन।
    एक ही Excel फ़ाइल में कई (UG/PG) कलर-कोडेड शीट्स एक साथ बनाता है, ताकि P5 पर बनी
    हर लिस्ट (चाहे कोई भी डिग्री/टैब हो) एक ही मास्टर फ़ाइल में मिल जाए।
    sheets_data: dict की list, हर dict में ये keys हो सकती हैं:
      df, sheet_name, deg_col, br_col, minor_col, mdc_col, voc_col, pw_col,
      master_rules, approved_keys, key_col, prefix
    """
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            for sheet in sheets_data:
                df_filtered = sheet.get("df")
                sheet_name = sheet.get("sheet_name", "Sheet1")
                if df_filtered is None or df_filtered.empty:
                    continue

                deg_col = sheet.get("deg_col")
                br_col = sheet.get("br_col")
                minor_col_found = sheet.get("minor_col")
                mdc_col_found = sheet.get("mdc_col")
                voc_col_found = sheet.get("voc_col")
                pw_col_found = sheet.get("pw_col")
                master_rules = sheet.get("master_rules")
                approved_keys = sheet.get("approved_keys") or set()
                key_col = sheet.get("key_col")
                prefix = sheet.get("prefix")

                df_filtered.to_excel(writer, index=False, sheet_name=sheet_name)
                worksheet = writer.sheets[sheet_name]

                blue_fill = PatternFill(start_color="D1ECF1", end_color="D1ECF1", fill_type="solid")
                red_fill = PatternFill(start_color="F8D7DA", end_color="F8D7DA", fill_type="solid")
                green_fill = PatternFill(start_color="D4EDDA", end_color="D4EDDA", fill_type="solid")
                thin_border = Border(left=Side(style='thin', color='CCCCCC'), right=Side(style='thin', color='CCCCCC'),
                                     top=Side(style='thin', color='CCCCCC'), bottom=Side(style='thin', color='CCCCCC'))

                targets_xl = {minor_col_found: 'minor', mdc_col_found: 'mdc', voc_col_found: 'voc', pw_col_found: 'pw'}
                _exempt_list = blank_exempt_mask(df_filtered, prefix).tolist()

                for idx, (_, row) in enumerate(df_filtered.iterrows()):
                    row_num = idx + 2

                    deg_part = str(row[deg_col]) if deg_col and deg_col in df_filtered.columns else ""
                    br_part = str(row[br_col]) if br_col and br_col in df_filtered.columns else ""
                    student_deg = (deg_part + " " + br_part).lower().replace(".", "").replace(" ", "").strip()

                    is_row_approved = get_student_key(row, idx, key_col) in approved_keys

                    matched_key = "Default"
                    if master_rules:
                        sorted_keys = sorted(master_rules.keys(), key=len, reverse=True)
                        for rule_key in sorted_keys:
                            rule_words = [w.lower().replace(".", "").strip() for w in rule_key.split() if w.strip()]
                            if rule_words and all(w in student_deg for w in rule_words):
                                matched_key = rule_key
                                break
                    c_rule = master_rules.get(matched_key, {"minor": [], "mdc": [], "voc": [], "pw": []}) if master_rules else {"minor": [], "mdc": [], "voc": [], "pw": []}

                    for col_idx, col_name in enumerate(df_filtered.columns, start=1):
                        cell = worksheet.cell(row=row_num, column=col_idx)
                        val = row[col_name]

                        if col_name == br_col:
                            if pd.isna(val) or str(val).strip() == "":
                                cell.fill = blue_fill
                                cell.border = thin_border
                            continue

                        if col_name in targets_xl:
                            rule_key = targets_xl[col_name]

                            if pd.isna(val) or str(val).strip() == "":
                                if not _exempt_list[idx]:
                                    cell.fill = blue_fill
                                    cell.border = thin_border
                            else:
                                val_clean = str(val).strip().lower().replace(".", "").replace(" ", "")
                                valid_list = c_rule.get(rule_key, [])
                                valid_set = {str(x).strip().lower().replace(".", "").replace(" ", "") for x in valid_list}

                                if valid_set and (val_clean not in valid_set):
                                    cell.fill = green_fill if is_row_approved else red_fill
                                    cell.border = thin_border

        return output.getvalue()

    def generate_p5_master_full_excel(raw_sheets, cat_labels, ug_blocks, pg_blocks,
                                       ug_summary, pg_summary,
                                       ug_students, ug_flags, ug_approved,
                                       pg_students, pg_flags, pg_approved,
                                       sheet1_df=None, sheet1_name="Uploaded_File"):
        """
    🆕 P5 Dashboard के 'मास्टर एक्सेल डाउनलोड' बटन के लिए पूरी 7-शीट Excel फ़ाइल बनाता है:
      Sheet 1: (sheet1_name)         — यूज़र द्वारा अपलोड की गई फ़ाइल, बिना किसी बदलाव के जस की तस
      Sheet 2: UG_Master_List        — पूरा UG रॉ डेटा (रंगीन)
      Sheet 3: PG_Master_List        — पूरा PG रॉ डेटा (रंगीन)
      Sheet 4: Branch_Subject_Sheet  — ब्रांच-वाइज विषय शीट (Total Admission + Minor/MDC/Voc/PW नाम व संख्या, merged cells)
      Sheet 5: Degree_Branch_Summary — डिग्री+ब्रांच-वाइज समरी (Minor+MDC+Voc+PW सभी एक साथ, UG फिर PG)
      Sheet 6: Reason_Students       — जिन छात्रों का कोई विषय गलत/खाली है, उनकी पूरी लिस्ट + कारण
      Sheet 7: Approved_Students     — शीट 6 में से जो पहले ही Approve किए जा चुके हैं, उनकी लिस्ट
    raw_sheets: sheet 2/3 के लिए dict की list (generate_master_excel_bytes जैसा फ़ॉर्मेट)।
    sheet1_df: यूज़र द्वारा P5 में अलग से अपलोड की गई फ़ाइल का DataFrame (None/खाली होने पर Sheet 1 छोड़ दी जाती है)।
    """
        from openpyxl.styles import Font, Alignment
        from openpyxl.utils import get_column_letter

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:

            # ================== Sheet 1: यूज़र की अपलोड की हुई फ़ाइल — जस की तस ==================
            if sheet1_df is not None and not sheet1_df.empty:
                _safe_sheet1 = "".join(ch for ch in str(sheet1_name) if ch not in '[]:*?/\\')[:31] or "Uploaded_File"
                sheet1_df.to_excel(writer, index=False, sheet_name=_safe_sheet1)
                _ws1 = writer.sheets[_safe_sheet1]
                for _c_i, _col_name in enumerate(sheet1_df.columns, start=1):
                    _cell = _ws1.cell(row=1, column=_c_i)
                    _cell.font = Font(bold=True, color="FFFFFF")
                    _cell.fill = PatternFill("solid", start_color="1A3C6E", end_color="1A3C6E")
                    _cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                    _longest = max([len(str(_col_name))] + [len(str(v)) for v in sheet1_df.iloc[:, _c_i - 1].astype(str).tolist()[:500]])
                    _ws1.column_dimensions[get_column_letter(_c_i)].width = min(max(_longest + 3, 10), 40)
                _ws1.freeze_panes = "A2"

            # ================== Sheet 2 & 3: रॉ डेटा (रंगीन) ==================
            for sheet in raw_sheets:
                df_filtered = sheet.get("df")
                sheet_name = sheet.get("sheet_name", "Sheet1")
                if df_filtered is None or df_filtered.empty:
                    continue

                s_deg_col = sheet.get("deg_col")
                s_br_col = sheet.get("br_col")
                minor_col_found = sheet.get("minor_col")
                mdc_col_found = sheet.get("mdc_col")
                voc_col_found = sheet.get("voc_col")
                pw_col_found = sheet.get("pw_col")
                master_rules = sheet.get("master_rules")
                approved_keys = sheet.get("approved_keys") or set()
                key_col = sheet.get("key_col")
                prefix = sheet.get("prefix")

                df_filtered.to_excel(writer, index=False, sheet_name=sheet_name)
                worksheet = writer.sheets[sheet_name]

                blue_fill = PatternFill(start_color="D1ECF1", end_color="D1ECF1", fill_type="solid")
                red_fill = PatternFill(start_color="F8D7DA", end_color="F8D7DA", fill_type="solid")
                green_fill = PatternFill(start_color="D4EDDA", end_color="D4EDDA", fill_type="solid")
                thin_border = Border(left=Side(style='thin', color='CCCCCC'), right=Side(style='thin', color='CCCCCC'),
                                     top=Side(style='thin', color='CCCCCC'), bottom=Side(style='thin', color='CCCCCC'))

                targets_xl = {minor_col_found: 'minor', mdc_col_found: 'mdc', voc_col_found: 'voc', pw_col_found: 'pw'}
                _exempt_list = blank_exempt_mask(df_filtered, prefix).tolist()

                for idx, (_, row) in enumerate(df_filtered.iterrows()):
                    row_num = idx + 2

                    deg_part = str(row[s_deg_col]) if s_deg_col and s_deg_col in df_filtered.columns else ""
                    br_part = str(row[s_br_col]) if s_br_col and s_br_col in df_filtered.columns else ""
                    student_deg = (deg_part + " " + br_part).lower().replace(".", "").replace(" ", "").strip()

                    is_row_approved = get_student_key(row, idx, key_col) in approved_keys

                    matched_key = "Default"
                    if master_rules:
                        sorted_keys = sorted(master_rules.keys(), key=len, reverse=True)
                        for rule_key in sorted_keys:
                            rule_words = [w.lower().replace(".", "").strip() for w in rule_key.split() if w.strip()]
                            if rule_words and all(w in student_deg for w in rule_words):
                                matched_key = rule_key
                                break
                    c_rule = master_rules.get(matched_key, {"minor": [], "mdc": [], "voc": [], "pw": []}) if master_rules else {"minor": [], "mdc": [], "voc": [], "pw": []}

                    for col_idx, col_name in enumerate(df_filtered.columns, start=1):
                        cell = worksheet.cell(row=row_num, column=col_idx)
                        val = row[col_name]

                        if col_name == s_br_col:
                            if pd.isna(val) or str(val).strip() == "":
                                cell.fill = blue_fill
                                cell.border = thin_border
                            continue

                        if col_name in targets_xl:
                            rule_key = targets_xl[col_name]

                            if pd.isna(val) or str(val).strip() == "":
                                if not _exempt_list[idx]:
                                    cell.fill = blue_fill
                                    cell.border = thin_border
                            else:
                                val_clean = str(val).strip().lower().replace(".", "").replace(" ", "")
                                valid_list = c_rule.get(rule_key, [])
                                valid_set = {str(x).strip().lower().replace(".", "").replace(" ", "") for x in valid_list}

                                if valid_set and (val_clean not in valid_set):
                                    cell.fill = green_fill if is_row_approved else red_fill
                                    cell.border = thin_border

            # ================== कॉमन स्टाइल ==================
            thin = Side(style="thin", color="BFBFBF")
            border3 = Border(left=thin, right=thin, top=thin, bottom=thin)
            head_fill3 = PatternFill("solid", start_color="1A3C6E", end_color="1A3C6E")
            band_a3 = PatternFill("solid", start_color="EAF1FB", end_color="EAF1FB")
            band_b3 = PatternFill("solid", start_color="FFFFFF", end_color="FFFFFF")
            red_fill3 = PatternFill("solid", start_color="F8D7DA", end_color="F8D7DA")
            blue_fill3 = PatternFill("solid", start_color="D1ECF1", end_color="D1ECF1")
            zebra_fill3 = PatternFill("solid", start_color="F4F7FD", end_color="F4F7FD")
            green_head_fill3 = PatternFill("solid", start_color="0F9D58", end_color="0F9D58")
            green_fill3 = PatternFill("solid", start_color="D4EDDA", end_color="D4EDDA")

            # ================== Sheet 3: ब्रांच-वाइज विषय शीट (UG + PG मर्ज) ==================
            ws3 = writer.book.create_sheet("Branch_Subject_Sheet")
            headers3 = ["Type", "Degree (डिग्री)", "Branch (ब्रांच)", "Total Admission"]
            for l_ in cat_labels:
                headers3 += [f"{l_} (विषय)", f"{l_} Count"]
            for c_i, t_ in enumerate(headers3, start=1):
                cell = ws3.cell(row=1, column=c_i, value=t_)
                cell.fill = head_fill3
                cell.font = Font(bold=True, color="FFFFFF")
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                cell.border = border3

            r3 = 2
            all_blocks3 = [("UG", b_) for b_ in ug_blocks] + [("PG", b_) for b_ in pg_blocks]
            for bi, (typ_, b_) in enumerate(all_blocks3):
                start, end = r3, r3 + b_["n"] - 1
                fill = band_a3 if bi % 2 == 0 else band_b3
                for rr in range(start, end + 1):
                    for cc in range(1, len(headers3) + 1):
                        cell = ws3.cell(row=rr, column=cc)
                        cell.fill = fill
                        cell.border = border3
                for cc, val in ((1, typ_), (2, b_["degree"]), (3, b_["branch"]), (4, b_["total"])):
                    cell = ws3.cell(row=start, column=cc, value=val)
                    cell.font = Font(bold=True)
                    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                    if end > start:
                        ws3.merge_cells(start_row=start, start_column=cc, end_row=end, end_column=cc)
                for k, items in enumerate(b_["cats"]):
                    for i, (name_, cnt_) in enumerate(items):
                        ws3.cell(row=start + i, column=5 + 2 * k, value=name_).alignment = Alignment(vertical="center", wrap_text=True)
                        ws3.cell(row=start + i, column=6 + 2 * k, value=cnt_).alignment = Alignment(horizontal="center", vertical="center")
                r3 = end + 1

            widths3 = [10, 22, 28, 16] + [34, 12] * len(cat_labels)
            for c_i, w_ in enumerate(widths3, start=1):
                ws3.column_dimensions[get_column_letter(c_i)].width = w_
            ws3.freeze_panes = "A2"
            if r3 == 2:
                ws3.cell(row=2, column=1, value="कोई डेटा उपलब्ध नहीं है।")

            # ================== Sheet 4: डिग्री + ब्रांच-वाइज समरी (UG फिर PG) ==================
            def _write_summary_section(ws, start_row, type_label, summary_df):
                if summary_df is None or summary_df.empty:
                    return start_row
                cols4 = list(summary_df.columns)
                red_idx4 = [i for i, c in enumerate(cols4) if "🔴" in str(c)]
                blue_idx4 = [i for i, c in enumerate(cols4) if "🔵" in str(c)]
                reason_idx4 = next((i for i, c in enumerate(cols4) if "Reason" in str(c)), None)

                headers4 = ["Type"] + cols4
                for c_i, t_ in enumerate(headers4, start=1):
                    cell = ws.cell(row=start_row, column=c_i, value=t_)
                    cell.fill = head_fill3
                    cell.font = Font(bold=True, color="FFFFFF")
                    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                    cell.border = border3

                r_ = start_row + 1
                for _, row in summary_df.iterrows():
                    is_total = str(row.iloc[0]).startswith("कुल योग")
                    cell0 = ws.cell(row=r_, column=1, value=type_label)
                    cell0.border = border3
                    if is_total:
                        cell0.fill = head_fill3
                        cell0.font = Font(bold=True, color="FFFFFF")
                    any_w = (not is_total) and any((row.iloc[i] or 0) > 0 for i in red_idx4)
                    any_b = (not is_total) and any((row.iloc[i] or 0) > 0 for i in blue_idx4)
                    for c_i0, cname in enumerate(cols4):
                        val = row.iloc[c_i0]
                        if c_i0 == reason_idx4 and isinstance(val, str):
                            val = val.replace("  ||  ", "\n")
                        cell = ws.cell(row=r_, column=c_i0 + 2, value=val)
                        cell.border = border3
                        cell.alignment = Alignment(vertical="top", wrap_text=(c_i0 == reason_idx4))
                        if is_total:
                            cell.fill = head_fill3
                            cell.font = Font(bold=True, color="FFFFFF")
                        elif c_i0 in red_idx4 and isinstance(val, (int, float)) and val > 0:
                            cell.fill = red_fill3
                            cell.font = Font(bold=True, color="721C24")
                        elif c_i0 in blue_idx4 and isinstance(val, (int, float)) and val > 0:
                            cell.fill = blue_fill3
                            cell.font = Font(bold=True, color="0C5460")
                        elif c_i0 == reason_idx4 and str(val).strip():
                            if any_w:
                                cell.fill = red_fill3
                                cell.font = Font(bold=True, color="721C24")
                            elif any_b:
                                cell.fill = blue_fill3
                                cell.font = Font(bold=True, color="0C5460")
                    r_ += 1
                return r_ + 1   # अगली टेबल से पहले एक खाली रो

            ws4 = writer.book.create_sheet("Degree_Branch_Summary")
            _r4 = _write_summary_section(ws4, 1, "UG", ug_summary)
            _r4 = _write_summary_section(ws4, _r4, "PG", pg_summary)
            if _r4 == 1:
                ws4.cell(row=1, column=1, value="कोई डेटा उपलब्ध नहीं है।")
            ws4.column_dimensions['A'].width = 8
            ws4.column_dimensions['B'].width = 22
            ws4.column_dimensions['C'].width = 26
            for _cl in ['D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N']:
                ws4.column_dimensions[_cl].width = 16
            ws4.freeze_panes = "C2"

            # ================== Sheet 5: Reason वाले छात्रों की पूरी लिस्ट ==================
            def _write_students_section(ws, start_row, type_label, students_df, flags):
                if students_df is None or students_df.empty:
                    return start_row
                cols5 = list(students_df.columns)
                reason_idx5 = next((i for i, c in enumerate(cols5) if "Reason" in str(c)), None)
                headers5 = ["Type"] + cols5
                for c_i, t_ in enumerate(headers5, start=1):
                    cell = ws.cell(row=start_row, column=c_i, value=t_)
                    cell.fill = head_fill3
                    cell.font = Font(bold=True, color="FFFFFF")
                    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                    cell.border = border3

                r_ = start_row + 1
                flags = flags or {}
                for r_i in range(len(students_df)):
                    row = students_df.iloc[r_i]
                    c0 = ws.cell(row=r_, column=1, value=type_label)
                    c0.border = border3
                    row_has_w = row_has_b = False
                    for c_i0, cname in enumerate(cols5):
                        val = row.iloc[c_i0]
                        if c_i0 == reason_idx5 and isinstance(val, str):
                            val = val.replace("\n", "\n")
                        cell = ws.cell(row=r_, column=c_i0 + 2, value=val)
                        cell.border = border3
                        cell.alignment = Alignment(vertical="top", wrap_text=(c_i0 == reason_idx5))
                        f_list = flags.get(cname)
                        f = f_list[r_i] if f_list is not None else ""
                        if f == "w":
                            cell.fill = red_fill3
                            cell.font = Font(bold=True, color="721C24")
                            row_has_w = True
                        elif f == "b":
                            cell.fill = blue_fill3
                            cell.font = Font(bold=True, color="0C5460")
                            row_has_b = True
                        elif r_i % 2 == 1:
                            cell.fill = zebra_fill3
                    if reason_idx5 is not None:
                        rc = ws.cell(row=r_, column=reason_idx5 + 2)
                        if row_has_w:
                            rc.fill = red_fill3
                            rc.font = Font(bold=True, color="721C24")
                        elif row_has_b:
                            rc.fill = blue_fill3
                            rc.font = Font(bold=True, color="0C5460")
                    r_ += 1
                return r_ + 1

            ws5 = writer.book.create_sheet("Reason_Students")
            _r5 = _write_students_section(ws5, 1, "UG", ug_students, ug_flags)
            _r5 = _write_students_section(ws5, _r5, "PG", pg_students, pg_flags)
            if _r5 == 1:
                ws5.cell(row=1, column=1, value="कोई भी गलत (🔴) या खाली (🔵) एंट्री वाला छात्र नहीं मिला।")
                ws5.column_dimensions['A'].width = 70
            else:
                ws5.column_dimensions['A'].width = 8
                ws5.freeze_panes = "B2"

            # ================== Sheet 6: Approve किए गए छात्रों की लिस्ट (Sheet 5 में से) ==================
            def _write_approved_section(ws, start_row, type_label, approved_df):
                if approved_df is None or approved_df.empty:
                    return start_row
                cols6 = list(approved_df.columns)
                headers6 = ["Type"] + cols6
                for c_i, t_ in enumerate(headers6, start=1):
                    cell = ws.cell(row=start_row, column=c_i, value=t_)
                    cell.fill = green_head_fill3
                    cell.font = Font(bold=True, color="FFFFFF")
                    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                    cell.border = border3

                r_ = start_row + 1
                reason_idx6 = next((i for i, c in enumerate(cols6) if "Reason" in str(c) or "कारण" in str(c)), None)
                for _, row in approved_df.iterrows():
                    c0 = ws.cell(row=r_, column=1, value=type_label)
                    c0.border = border3
                    c0.fill = green_fill3
                    for c_i0, cname in enumerate(cols6):
                        cell = ws.cell(row=r_, column=c_i0 + 2, value=row.iloc[c_i0])
                        cell.border = border3
                        cell.fill = green_fill3
                        cell.font = Font(color="155724")
                        cell.alignment = Alignment(vertical="top", wrap_text=(c_i0 == reason_idx6))
                    r_ += 1
                return r_ + 1

            ws6 = writer.book.create_sheet("Approved_Students")
            _r6 = _write_approved_section(ws6, 1, "UG", ug_approved)
            _r6 = _write_approved_section(ws6, _r6, "PG", pg_approved)
            if _r6 == 1:
                ws6.cell(row=1, column=1, value="अभी तक इनमें से किसी भी 'गलत/खाली' छात्र को Approve नहीं किया गया है।")
                ws6.column_dimensions['A'].width = 70
            else:
                ws6.column_dimensions['A'].width = 8
                ws6.freeze_panes = "B2"

        return output.getvalue()

    def process_panel_validation(df_panel, prefix, allowed_degrees, master_rules=None):
        deg_col = next((c for c in df_panel.columns if any(k in c.lower() for k in ['deg', 'course', 'class'])), df_panel.columns[0])
        br_col = next((c for c in df_panel.columns if any(k in c.lower() for k in ['branch', 'stream', 'subject'])), df_panel.columns[0])
    
        def check_degree(val):
            v = str(val).lower().replace(".", "").replace(" ", "").strip()
            return any(d in v for d in allowed_degrees)
        
        df_filtered = df_panel[df_panel[deg_col].apply(check_degree)].reset_index(drop=True)
    
        if df_filtered.empty:
            st.warning(f"⚠️ {prefix.upper()} पैनल के लिए कोई उपयुक्त डेटा (मैचिंग डिग्री) नहीं मिला।")
            return

        minor_col_found = next((c for c in df_filtered.columns if 'minor' in c.lower()), None)
        mdc_col_found = next((c for c in df_filtered.columns if 'mdc' in c.lower()), None)
        voc_col_found = next((c for c in df_filtered.columns if 'voc' in c.lower() or 'skill' in c.lower()), None)
        pw_col_found = next((c for c in df_filtered.columns if any(k in c.lower() for k in ['pw', 'project', 'ce'])), None)

        # छात्र की पहचान के लिए कॉलम (Roll/Enrollment/Name) — Approve सिस्टम के लिए ज़रूरी
        key_col = find_student_key_col(df_filtered)
        targets = {minor_col_found: 'minor', mdc_col_found: 'mdc', voc_col_found: 'voc', pw_col_found: 'pw'}

        # --- 🔎 हर रो के लिए मिसमैच वाले कॉलम निकालने का साझा फ़ंक्शन ---
        # (लाइव टेबल कलरिंग और नीचे की "Approve" लिस्ट — दोनों जगह इसी लॉजिक का इस्तेमाल होता है)
        def compute_row_mismatches(row):
            # 🔧 फिक्स: Degree column + Branch column दोनों को मिलाकर चेक करना
            # (Biotechnology / Commerce Computer जैसी ब्रांच अक्सर अलग Branch column में होती है, Degree column में नहीं)
            deg_part = str(row[deg_col]) if deg_col else ""
            br_part = str(row[br_col]) if br_col else ""
            student_deg = (deg_part + " " + br_part).lower().replace(".", "").replace(" ", "").strip()

            matched_key = "Default"
            if master_rules:
                sorted_keys = sorted(master_rules.keys(), key=len, reverse=True)
                for rule_key in sorted_keys:
                    # 🔧 फिक्स: पूरा नाम एक साथ ढूंढने के बजाय हर word अलग-अलग ढूंढना
                    # (जैसे "B.Com. Computer" -> "bcom" और "computer" दोनों कहीं भी मिलने चाहिए)
                    rule_words = [w.lower().replace(".", "").strip() for w in rule_key.split() if w.strip()]
                    if rule_words and all(w in student_deg for w in rule_words):
                        matched_key = rule_key
                        break

            c_rule = master_rules.get(matched_key, {"minor": [], "mdc": [], "voc": [], "pw": []}) if master_rules else {"minor": [], "mdc": [], "voc": [], "pw": []}

            mismatched_cols = []
            for col_name, rule_key in targets.items():
                if col_name and col_name in df_filtered.columns:
                    val = row[col_name]
                    if not (pd.isna(val) or str(val).strip() == ""):
                        val_clean = str(val).strip().lower().replace(".", "").replace(" ", "")
                        valid_list = c_rule.get(rule_key, [])
                        valid_set = {str(x).strip().lower().replace(".", "").replace(" ", "") for x in valid_list}
                        if valid_set and (val_clean not in valid_set):
                            mismatched_cols.append(col_name)
            return mismatched_cols

        # ⚪ खाली-छूट वाली डिग्री+ब्रांच की रो (इनमें Minor/MDC/Voc/PW खाली होने पर नीला नहीं होगा)
        _exempt_arr = blank_exempt_mask(df_filtered, prefix).tolist()

        # --- 🖥️ लाइव वैरिफिकेशन स्टाइलर फ़ंक्शन (स्क्रीन ग्रिड के लिए फिक्स) ---
        def cell_styler(dataframe):
            s_df = pd.DataFrame('', index=dataframe.index, columns=dataframe.columns)

            for position, (index, row) in enumerate(dataframe.iterrows()):
                # ब्रांच की खाली चेकिंग
                if br_col and br_col in dataframe.columns:
                    b_val = row[br_col]
                    if pd.isna(b_val) or str(b_val).strip() == "":
                        s_df.at[index, br_col] = 'background-color: #d1ecf1; color: #0c5460; font-weight: bold; border: 1px solid #17a2b8;'

                student_key = get_student_key(row, position, key_col)
                approval = get_approval(student_key, prefix)
                mismatched_cols = compute_row_mismatches(row)

                # स्क्रीन पर नियमों के अनुसार सटीक लाइव कलर कोडिंग
                for col_name in targets:
                    if col_name and col_name in dataframe.columns:
                        val = row[col_name]
                        # 🔵 स्थिति 1: अगर पूरी तरह से ब्लैंक है तो नीला करें (खाली-छूट वाली डिग्री+ब्रांच को छोड़कर)
                        if (pd.isna(val) or str(val).strip() == "") and not _exempt_arr[position]:
                            s_df.at[index, col_name] = 'background-color: #d1ecf1; color: #0c5460; font-weight: bold; border: 1px solid #17a2b8;'

                # 🔴 गलत विषय → लाल | ✅ अगर पहले से Approve हो चुका है → हरा (अब गलत नहीं माना जाएगा)
                for col_name in mismatched_cols:
                    if approval:
                        s_df.at[index, col_name] = 'background-color: #d4edda; color: #155724; font-weight: bold; border: 2px solid #28a745;'
                    else:
                        s_df.at[index, col_name] = 'background-color: #f8d7da; color: #721c24; font-weight: bold; border: 2px solid red;'
            return s_df

        # =====================================================================
        # ⚪ खाली-छूट सेटिंग: यहाँ बताएँ कि किस डिग्री + ब्रांच में Minor / MDC / Voc / PW खाली ही रहते हैं
        # =====================================================================
        _ex_dc, _ex_bc = detect_deg_branch_cols(df_filtered)
        _ex_deg = df_filtered[_ex_dc].map(_norm_blank_label) if _ex_dc else pd.Series(["—"] * len(df_filtered), index=df_filtered.index)
        _ex_br = df_filtered[_ex_bc].map(_norm_blank_label) if _ex_bc else pd.Series(["—"] * len(df_filtered), index=df_filtered.index)
        _saved_pairs = get_blank_exempt_pairs(prefix)
        _all_pairs = sorted(set(zip(_ex_deg, _ex_br)) | _saved_pairs)
        _pair_label = lambda pr: f"{pr[0]} → {pr[1]}"
        _label_to_pair = {_pair_label(pr): pr for pr in _all_pairs}
        _ex_opts = list(_label_to_pair.keys())
        _ex_sig = hashlib.md5("|".join(_ex_opts).encode("utf-8")).hexdigest()[:8]

        with st.expander(f"⚪ खाली-छूट सेटिंग — जिन डिग्री + ब्रांच में Minor/MDC/Voc/PW खाली ही रहते हैं ({len(_saved_pairs)} चुनी हुई)"):
            st.caption("यहाँ चुनी गई डिग्री + ब्रांच में Minor, MDC, Voc और PW खाली होने पर 🔵 नीला रंग नहीं लगेगा, और खाली-गिनती में भी नहीं जुड़ेगा (टेबल, Excel डाउनलोड, खाली-सूची और डैशबोर्ड — सब जगह)। अगर उनमें कोई विषय भरा हो तो वह पहले की तरह जाँचा जाएगा।")
            _ex_sel = st.multiselect(
                "इन डिग्री + ब्रांच में खाली सेल नीला न हो:",
                options=_ex_opts,
                default=[_pair_label(pr) for pr in sorted(_saved_pairs)],
                key=f"blank_exempt_sel_{prefix}_{_ex_sig}"
            )
            if st.button("💾 खाली-छूट सेव करें", key=f"blank_exempt_save_{prefix}"):
                set_blank_exempt_pairs(prefix, {_label_to_pair[l_] for l_ in _ex_sel})
                st.success("🎉 खाली-छूट सेव हो गई! अब चुनी हुई डिग्री+ब्रांच में खाली सेल नीले नहीं दिखेंगे।")
                st.rerun()

        st.subheader(f"📊 लाइव वैरिफाइड {prefix.upper()} डेटा टेबल")
        st.caption("🔵 नीला सेल = डेटा गायब है | 🔴 लाल सेल = गलत विषय (मास्टर गाइडलाइन से मिसमैच) | 🟢 हरा सेल = Approved (मान्य किया गया, अब गलत नहीं गिना जाएगा)")
    
        # स्क्रीन पर सीरियल नंबर 1 से शुरू करना
        df_filtered.index = range(1, len(df_filtered) + 1)
        st.dataframe(df_filtered.style.apply(cell_styler, axis=None), height=500, use_container_width=True)

        # approved_keys सेट पहले से निकाल लेना ताकि एक्सेल डाउनलोड और नीचे की लिस्ट दोनों इस्तेमाल कर सकें
        all_approvals_now = get_all_approvals(prefix)
        approved_keys_set = {a[0] for a in all_approvals_now}

        # --- 🚨 📥 रंगीन एक्सेल डाउनलोड (अब शेयर्ड फ़ंक्शन का इस्तेमाल कर रहा है) 🚨 ---
        processed_data = generate_colored_excel_bytes(
            df_filtered, deg_col, br_col, minor_col_found, mdc_col_found, voc_col_found, pw_col_found,
            master_rules=master_rules, sheet_name="Verified_Data", approved_keys=approved_keys_set, key_col=key_col,
            prefix=prefix
        )
        st.download_button(
            label=f"📥 रंगीन (🔴/🔵/🟢) {prefix.upper()} डेटा एक्सेल डाउनलोड करें",
            data=processed_data,
            file_name=f"Verified_{prefix.upper()}_Colored_Data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"download_validated_excel_{prefix}"
        )

        # =====================================================================
        # 🔵 खाली (Blank) डेटा — किस डिग्री + ब्रांच में क्या खाली है
        # =====================================================================
        st.divider()
        st.subheader("🔵 खाली (Blank) डेटा — किस डिग्री + ब्रांच में")
        st.caption("यहाँ दिखता है कि किस डिग्री + ब्रांच में कौन सा कॉलम खाली (🔵) है और कितने छात्रों का। जाँचने वाले कॉलम नीचे के बॉक्स से बदल भी सकते हैं (PG में जहाँ Minor/MDC जैसे कॉलम नहीं होते, वहाँ अपनी पसंद के कॉलम चुनें)।")

        _skip_kw = ['minor', 'mdc', 'voc', 'skill', 'pw', 'project']
        _bl_deg = deg_col if (deg_col and deg_col in df_filtered.columns) else None
        _bl_br = None
        for _kws in (['branch', 'stream'], ['subject']):
            _bl_br = next((c for c in df_filtered.columns if c != _bl_deg
                           and any(k in str(c).lower() for k in _kws)
                           and not any(k in str(c).lower() for k in _skip_kw)), None)
            if _bl_br is not None:
                break

        _bl_default = [c for c in (minor_col_found, mdc_col_found, voc_col_found, pw_col_found) if c]
        if _bl_br is not None and _bl_br not in _bl_default:
            _bl_default.append(_bl_br)

        # कॉलम-सूची बदलने पर (नई फ़ाइल) चुनाव अपने-आप नए सिरे से शुरू हो, इसलिए key में कॉलमों की पहचान जोड़ी है
        _bl_sig = hashlib.md5("|".join(map(str, df_filtered.columns)).encode("utf-8")).hexdigest()[:8]
        _bl_key = f"blank_cols_{prefix}_{_bl_sig}"
        if _bl_key not in st.session_state:
            st.session_state[_bl_key] = _bl_default

        st.multiselect(
            "🔎 किन कॉलम में खाली जाँचना है:",
            options=list(df_filtered.columns),
            key=_bl_key
        )
        _bl_cols = [c for c in st.session_state[_bl_key] if c in df_filtered.columns]

        if not _bl_cols:
            st.info("ℹ️ ऊपर के बॉक्स से कम से कम एक कॉलम चुनें, फिर खाली डेटा की सूची यहाँ दिखेगी।")
        else:
            def _bl_clean(series):
                s_ = series.astype(str).str.strip()
                return s_.mask(series.isna() | (s_ == "") | (s_.str.lower() == "nan"), "(खाली/Blank)")

            _work = df_filtered.copy()
            _work["Degree (डिग्री)"] = _bl_clean(_work[_bl_deg]) if _bl_deg else "—"
            _work["Branch (ब्रांच)"] = _bl_clean(_work[_bl_br]) if _bl_br else "—"
            _ex_s = pd.Series(_exempt_arr, index=_work.index)
            _cat_set = {c_ for c_ in (minor_col_found, mdc_col_found, voc_col_found, pw_col_found) if c_}
            for _c in _bl_cols:
                _fl = _work[_c].isna() | (_work[_c].astype(str).str.strip() == "")
                if _c in _cat_set:
                    _fl = _fl & ~_ex_s          # ⚪ खाली-छूट वाली डिग्री+ब्रांच में Minor..PW का खाली नहीं गिनना
                _work[f"__b__{_c}"] = _fl
            _flag_cols = [f"__b__{_c}" for _c in _bl_cols]
            _work["__any__"] = _work[_flag_cols].any(axis=1)
            if int(_ex_s.sum()) > 0:
                st.caption(f"⚪ खाली-छूट वाली डिग्री+ब्रांच के {int(_ex_s.sum())} छात्रों के Minor/MDC/Voc/PW यहाँ गिने नहीं गए (सेटिंग ऊपर 'खाली-छूट सेटिंग' में है)।")

            _agg = {"कुल छात्र (Total)": ("__any__", "size"), "🔵 खाली वाले छात्र": ("__any__", "sum")}
            for _c in _bl_cols:
                _agg[f"🔵 {_c}"] = (f"__b__{_c}", "sum")
            _bl_summary = _work.groupby(["Degree (डिग्री)", "Branch (ब्रांच)"]).agg(**_agg).reset_index()
            for _c in ["🔵 खाली वाले छात्र"] + [f"🔵 {_c}" for _c in _bl_cols]:
                _bl_summary[_c] = _bl_summary[_c].astype(int)

            def _bl_reason(r):
                _parts = [f"{_c}: {int(r[f'🔵 {_c}'])} छात्र" for _c in _bl_cols if r[f"🔵 {_c}"] > 0]
                return ("🔵 खाली → " + " ; ".join(_parts)) if _parts else ""
            _bl_summary["📝 कारण (Reason)"] = _bl_summary.apply(_bl_reason, axis=1)

            _total_combos = len(_bl_summary)
            _blank_combos = int((_bl_summary["🔵 खाली वाले छात्र"] > 0).sum())
            _blank_students = int(_work["__any__"].sum())
            _blank_cells = int(sum(_work[f].sum() for f in _flag_cols))

            bm1, bm2, bm3, bm4 = st.columns(4)
            with bm1:
                st.metric("🎓 कुल डिग्री+ब्रांच", _total_combos)
            with bm2:
                st.metric("🔵 खाली वाली डिग्री+ब्रांच", _blank_combos)
            with bm3:
                st.metric("👥 खाली वाले छात्र", _blank_students)
            with bm4:
                st.metric("🔵 कुल खाली सेल", _blank_cells)

            if _blank_cells == 0:
                st.success("✅ चुने गए कॉलम में कोई भी खाली डेटा नहीं मिला।")
            else:
                _show_all_bl = st.checkbox("बिना खाली वाली डिग्री+ब्रांच भी दिखाएँ", value=False, key=f"blank_show_all_{prefix}")
                _bl_show = _bl_summary if _show_all_bl else _bl_summary[_bl_summary["🔵 खाली वाले छात्र"] > 0]
                _bl_show = _bl_show.sort_values(["🔵 खाली वाले छात्र", "Degree (डिग्री)"], ascending=[False, True]).reset_index(drop=True)

                _bl_blue = 'background-color: #d1ecf1; color: #0c5460; font-weight: bold; border: 2px solid #17a2b8;'
                _bl_blue_cols = [c for c in _bl_show.columns if "🔵" in c]

                def _bl_styler(row):
                    _any_b = any(row[c] > 0 for c in _bl_blue_cols)
                    out = []
                    for c in row.index:
                        if c in _bl_blue_cols and row[c] > 0:
                            out.append(_bl_blue)
                        elif c == "📝 कारण (Reason)" and row[c] and _any_b:
                            out.append(_bl_blue)
                        else:
                            out.append("")
                    return out

                st.dataframe(
                    _bl_show.style.apply(_bl_styler, axis=1),
                    hide_index=True,
                    use_container_width=True,
                    height=min(38 * (len(_bl_show) + 1) + 3, 650),
                    column_config={"📝 कारण (Reason)": st.column_config.TextColumn(width=500)}
                )

                _bd1, _bd2 = st.columns(2)
                with _bd1:
                    st.download_button(
                        label="📥 खाली-डेटा सूची CSV में डाउनलोड करें",
                        data=_bl_show.to_csv(index=False).encode("utf-8-sig"),
                        file_name=f"{prefix.upper()}_Blank_Degree_Branch_Report.csv",
                        mime="text/csv",
                        key=f"blank_dl_csv_{prefix}",
                        use_container_width=True
                    )
                with _bd2:
                    st.download_button(
                        label="📊 खाली-डेटा सूची Excel (XLSX) में डाउनलोड करें",
                        data=generate_summary_excel_bytes(_bl_show, sheet_name=f"{prefix.upper()}_Blank"),
                        file_name=f"{prefix.upper()}_Blank_Degree_Branch_Report.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"blank_dl_xlsx_{prefix}",
                        use_container_width=True
                    )

                # 👨‍🎓 छात्र-वार सूची (ताकि सीधे पता चले कि किस छात्र का कौन सा कॉलम भरना है)
                _bl_rows = _work[_work["__any__"]]
                with st.expander(f"👨‍🎓 छात्र-वार खाली सूची ({len(_bl_rows)} छात्र)"):
                    _stu = pd.DataFrame({"टेबल में रो नं.": _bl_rows.index})
                    if key_col and key_col in _bl_rows.columns:
                        _stu["छात्र (Key)"] = _bl_rows[key_col].astype(str).values
                    _stu["Degree (डिग्री)"] = _bl_rows["Degree (डिग्री)"].values
                    _stu["Branch (ब्रांच)"] = _bl_rows["Branch (ब्रांच)"].values
                    _stu["🔵 खाली कॉलम"] = _bl_rows.apply(
                        lambda r: ", ".join(_c for _c in _bl_cols if r[f"__b__{_c}"]), axis=1
                    ).values
                    st.dataframe(_stu, hide_index=True, use_container_width=True, height=min(38 * (len(_stu) + 1) + 3, 500))


        # =====================================================================
        # ✅ "गलत विषय" Approve करने का सिस्टम
        # =====================================================================
        st.divider()
        st.subheader("🛠️ गलत विषय Approve करें")
        st.caption("अगर किसी छात्र का विषय मास्टर गाइडलाइन से मैच नहीं हो रहा लेकिन वह सही है, तो यहाँ से उसे Approve करें — फिर वह टेबल में लाल नहीं, हरा (✅ Approved) दिखेगा।")

        pending_students = []
        for position, (index, row) in enumerate(df_filtered.iterrows()):
            mismatched_cols = compute_row_mismatches(row)
            if mismatched_cols:
                student_key = get_student_key(row, position, key_col)
                if not get_approval(student_key, prefix):
                    pending_students.append((index, row, student_key, mismatched_cols))

        if not pending_students:
            st.info("✅ फिलहाल कोई भी 'गलत विषय' वाला छात्र Approve होने के लिए बाकी नहीं है।")
        else:
            for index, row, student_key, mismatched_cols in pending_students:
                name_display = str(row[key_col]) if key_col and key_col in df_filtered.columns else f"रो #{index}"
                with st.expander(f"⚠️ {name_display} — गलत कॉलम: {', '.join(mismatched_cols)}"):
                    st.write({c: row[c] for c in mismatched_cols})
                    appr_col1, appr_col2 = st.columns([2, 1])
                    with appr_col1:
                        approver_role = st.selectbox(
                            "किसने Approve किया?",
                            ["Nodal", "Student", "Principal"],
                            key=f"approver_role_{prefix}_{student_key}_{index}"
                        )
                    with appr_col2:
                        st.write("")
                        if st.button("✅ Approve करें", key=f"approve_btn_{prefix}_{student_key}_{index}", use_container_width=True):
                            add_approval(student_key, prefix, approver_role)
                            st.success(f"🎉 {name_display} को {approver_role} द्वारा Approve कर दिया गया!")
                            st.rerun()

        # =====================================================================
        # 📋 Approved List (जिन छात्रों का गलत विषय Approve किया जा चुका है)
        # =====================================================================
        st.divider()
        st.subheader("📋 Approved List")
        st.caption("यहाँ वो सभी छात्र दिखेंगे जिनका 'गलत विषय' मान्य (Approve) किया जा चुका है — साथ में किसने Approve किया, यह भी दिखेगा।")

        if not all_approvals_now:
            st.info("अभी तक कोई भी छात्र Approve नहीं हुआ है।")
        else:
            approved_rows = [
                {"छात्र (Key)": sk, "Approve किया": ab, "समय": at}
                for sk, ab, at in all_approvals_now
            ]
            approved_display_df = pd.DataFrame(approved_rows)
            st.dataframe(approved_display_df, use_container_width=True, hide_index=True)
            panel_orientation = st.radio(
                "🖨️ प्रिंट ओरिएंटेशन चुनें:",
                options=["📄 Portrait (सीधा)", "📃 Landscape (आड़ा)"],
                horizontal=True,
                key=f"orientation_panel_{prefix}"
            )
            render_print_button(
                approved_display_df,
                title=f"Approved List - {prefix.upper()}",
                key_suffix=f"panel_{prefix}",
                orientation="landscape" if "Landscape" in panel_orientation else "portrait"
            )

            revoke_choice = st.selectbox(
                "❌ किसी Approval को हटाना है? (Revoke करें):",
                ["-- चुनें --"] + [a[0] for a in all_approvals_now],
                key=f"revoke_select_{prefix}"
            )
            if revoke_choice != "-- चुनें --":
                if st.button("🗑️ चुनी गई Approval हटाएं (Revoke)", key=f"revoke_btn_{prefix}"):
                    remove_approval(revoke_choice, prefix)
                    st.success("🎉 Approval हटा दी गई — यह छात्र अब फिर से 'गलत विषय' में गिना जाएगा।")
                    st.rerun()

    # =========================================================================
    # 🔄 Excel (.xls / .xlsx) → CSV कन्वर्टर (Panel 1 के लिए)
    # =========================================================================
    _OLE_MAGIC = b"\xd0\xcf\x11\xe0"   # असली .xls (पुराना Excel)
    _ZIP_MAGIC = b"PK"                # असली .xlsx / .ods

    class _HTMLTableParser(HTMLParser):
        """बिना किसी एक्स्ट्रा लाइब्रेरी (lxml/bs4) के HTML <table> पढ़ने वाला पार्सर।"""
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.tables = []
            self._stack = []
            self._row = None
            self._cell = None

        def _close_cell(self):
            if self._cell is not None and self._row is not None:
                self._row.append("".join(self._cell).strip())
            self._cell = None

        def _close_row(self):
            self._close_cell()
            if self._row is not None and self._stack and self._row:
                self._stack[-1].append(self._row)
            self._row = None

        def handle_starttag(self, tag, attrs):
            if tag == "table":
                self._stack.append([])
            elif tag == "tr" and self._stack:
                self._close_row()
                self._row = []
            elif tag in ("td", "th") and self._row is not None:
                self._close_cell()
                self._cell = []
            elif tag == "br" and self._cell is not None:
                self._cell.append(" ")

        def handle_data(self, data):
            if self._cell is not None:
                self._cell.append(data)

        def handle_endtag(self, tag):
            if tag in ("td", "th"):
                self._close_cell()
            elif tag == "tr":
                self._close_row()
            elif tag == "table" and self._stack:
                self._close_row()
                self.tables.append(self._stack.pop())

        def finish(self):
            self._close_row()
            while self._stack:
                self.tables.append(self._stack.pop())

    def _html_tables_to_df(text):
        parser = _HTMLTableParser()
        parser.feed(text)
        parser.close()
        parser.finish()
        tables = [t for t in parser.tables if t]
        if not tables:
            raise ValueError("HTML में कोई टेबल नहीं मिली")
        rows = max(tables, key=len)                      # सबसे बड़ी टेबल = असली डेटा
        width = max(len(r) for r in rows)
        rows = [r + [""] * (width - len(r)) for r in rows]
        header = [h if h else f"Unnamed: {i}" for i, h in enumerate(rows[0])]
        return pd.DataFrame(rows[1:], columns=header)

    def _spreadsheetml_to_df(raw):
        """Excel 2003 'XML Spreadsheet' फ़ाइल (पहली शीट)।"""
        ns = "{urn:schemas-microsoft-com:office:spreadsheet}"
        root = ET.fromstring(raw)
        ws = root.find(f"{ns}Worksheet")
        if ws is None:
            raise ValueError("XML में कोई वर्कशीट नहीं मिली")
        rows = []
        for row in ws.iter(f"{ns}Row"):
            vals = []
            for cell in row.findall(f"{ns}Cell"):
                idx = cell.get(f"{ns}Index")
                if idx:
                    while len(vals) < int(idx) - 1:
                        vals.append("")
                data = cell.find(f"{ns}Data")
                vals.append("".join(data.itertext()).strip() if data is not None else "")
            rows.append(vals)
        if not rows:
            raise ValueError("XML शीट खाली है")
        width = max(len(r) for r in rows)
        rows = [r + [""] * (width - len(r)) for r in rows]
        header = [h if h else f"Unnamed: {i}" for i, h in enumerate(rows[0])]
        return pd.DataFrame(rows[1:], columns=header)

    def _decode_text_bytes(raw):
        if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
            return raw.decode("utf-16", errors="replace")
        for enc in ("utf-8-sig", "cp1252"):
            try:
                return raw.decode(enc)
            except UnicodeDecodeError:
                continue
        return raw.decode("latin-1", errors="replace")

    def _delimited_text_to_df(text):
        if "\x00" in text[:20000]:
            raise ValueError("यह टेक्स्ट नहीं, बाइनरी फ़ाइल लगती है")
        first_line = text.lstrip("\ufeff").split("\n", 1)[0]
        counts = {d: first_line.count(d) for d in ("\t", ",", ";", "|")}
        sep = max(counts, key=counts.get)
        if counts[sep] == 0:
            raise ValueError("कोई कॉलम-सेपरेटर (Tab/Comma) नहीं मिला")
        return pd.read_csv(io.StringIO(text), sep=sep)

    @st.cache_data(show_spinner=False)
    def get_excel_sheet_names(raw):
        """असली Excel फ़ाइल की शीट्स के नाम (नकली .xls के लिए खाली लिस्ट)।"""
        if raw[:4] == _OLE_MAGIC or raw[:2] == _ZIP_MAGIC:
            try:
                return pd.ExcelFile(io.BytesIO(raw)).sheet_names
            except Exception:
                return []
        return []

    def excel_bytes_to_dataframe(raw, sheet_name=0):
        """.xls / .xlsx को DataFrame में पढ़ता है। कई पोर्टल .xls नाम से असल में
    HTML / XML / टेक्स्ट फ़ाइल देते हैं — उन सबको भी संभालता है।"""
        if not raw:
            raise ValueError("फ़ाइल खाली है")
        # 1) असली Excel (xls / xlsx / ods)
        if raw[:4] == _OLE_MAGIC or raw[:2] == _ZIP_MAGIC:
            return pd.read_excel(io.BytesIO(raw), sheet_name=sheet_name)
        # 2) नकली .xls: अंदर से देखकर टाइप पहचानना
        text = _decode_text_bytes(raw)
        sample = text[:500000].lower()
        try:
            if "urn:schemas-microsoft-com:office:spreadsheet" in sample:
                return _spreadsheetml_to_df(raw)
            if "<table" in sample:
                return _html_tables_to_df(text)
            return _delimited_text_to_df(text)
        except Exception as e:
            raise ValueError(
                f"यह फ़ाइल असली Excel नहीं है और पढ़ी भी नहीं जा सकी ({e}). "
            f"फ़ाइल की शुरुआत: {raw[:150]!r}"
            ) from e

    @st.cache_data(show_spinner="🔄 Excel फ़ाइल को CSV में बदला जा रहा है...")
    def excel_bytes_to_csv_bytes(raw, sheet_name=0):
        """Excel bytes → (CSV bytes, रोज़ की संख्या)। utf-8-sig ताकि हिंदी Excel में भी सही खुले।"""
        df_in = excel_bytes_to_dataframe(raw, sheet_name)
        return df_in.to_csv(index=False).encode("utf-8-sig"), len(df_in)

    # =========================================================================
    # 📑 ब्रांच-वाइज विषय शीट: Degree/Branch/Total Admission मर्ज + Minor/MDC/Voc/PW नाम+काउंट
    # =========================================================================
    def build_branch_subject_blocks(df, deg_c, br_c, cats):
        """cats = [(label, column_name), ...] -> हर Degree+Branch के लिए एक ब्लॉक"""
        blocks = []
        for (d_, b_), g_ in df.groupby([deg_c, br_c], sort=False):
            cat_lists = []
            for _lbl, _cn in cats:
                s_ = g_[_cn].dropna().astype(str).str.strip()
                s_ = s_[(s_ != "") & (s_.str.lower() != "nan")]
                items_ = sorted(s_.value_counts().items(), key=lambda kv: (-kv[1], kv[0]))
                cat_lists.append([(str(n_), int(c_)) for n_, c_ in items_])
            n_rows = max([1] + [len(x_) for x_ in cat_lists])
            blocks.append({"degree": d_, "branch": b_, "total": int(len(g_)), "cats": cat_lists, "n": n_rows})
        blocks.sort(key=lambda x_: (str(x_["degree"]), -x_["total"], str(x_["branch"])))
        return blocks


    def branch_subject_sheet_html(blocks, cat_labels):
        """स्क्रीन पर दिखाने के लिए rowspan (मर्ज) वाली HTML तालिका"""
        def _e(x):
            return _html.escape(str(x)).replace("$", "&#36;")
        th = "position:sticky;top:0;background:#1a3c6e;color:#fff;padding:8px 10px;border:1px solid #BFBFBF;text-align:center;font-size:13px;white-space:nowrap;z-index:2;"
        h = ['<div style="max-height:650px;overflow:auto;border:1px solid #BFBFBF;border-radius:6px;">',
             '<table style="border-collapse:collapse;width:100%;font-size:13.5px;color:#111;">', '<thead><tr>']
        heads = ["Degree (डिग्री)", "Branch (ब्रांच)", "Total Admission"]
        for l_ in cat_labels:
            heads += [f"{l_} (विषय)", f"{l_} Count"]
        for t_ in heads:
            h.append(f'<th style="{th}">{_e(t_)}</th>')
        h.append("</tr></thead><tbody>")
        for bi, b_ in enumerate(blocks):
            bg = "#EAF1FB" if bi % 2 == 0 else "#FFFFFF"
            td = f"padding:6px 10px;border:1px solid #BFBFBF;background:{bg};"
            for i in range(b_["n"]):
                h.append("<tr>")
                if i == 0:
                    rs = b_["n"]
                    h.append(f'<td rowspan="{rs}" style="{td}vertical-align:middle;text-align:center;font-weight:700;">{_e(b_["degree"])}</td>')
                    h.append(f'<td rowspan="{rs}" style="{td}vertical-align:middle;text-align:center;font-weight:700;">{_e(b_["branch"])}</td>')
                    h.append(f'<td rowspan="{rs}" style="{td}vertical-align:middle;text-align:center;font-weight:800;color:#1a3c6e;">{b_["total"]}</td>')
                for items in b_["cats"]:
                    if i < len(items):
                        h.append(f'<td style="{td}">{_e(items[i][0])}</td><td style="{td}text-align:center;">{items[i][1]}</td>')
                    else:
                        h.append(f'<td style="{td}"></td><td style="{td}"></td>')
                h.append("</tr>")
        h.append("</tbody></table></div>")
        return "".join(h)


    def generate_branch_subject_sheet_excel_bytes(blocks, cat_labels, sheet_name="Branch_Subject_Sheet"):
        """असली merged cells वाली Excel शीट"""
        from openpyxl import Workbook
        from openpyxl.styles import PatternFill, Border, Side, Font, Alignment
        from openpyxl.utils import get_column_letter

        wb = Workbook()
        ws = wb.active
        ws.title = "".join(ch for ch in str(sheet_name) if ch not in '[]:*?/\\')[:31] or "Sheet1"

        thin = Side(style="thin", color="BFBFBF")
        border = Border(left=thin, right=thin, top=thin, bottom=thin)
        head_fill = PatternFill("solid", start_color="1A3C6E", end_color="1A3C6E")
        band_a = PatternFill("solid", start_color="EAF1FB", end_color="EAF1FB")
        band_b = PatternFill("solid", start_color="FFFFFF", end_color="FFFFFF")

        headers = ["Degree (डिग्री)", "Branch (ब्रांच)", "Total Admission"]
        for l_ in cat_labels:
            headers += [f"{l_} (विषय)", f"{l_} Count"]
        ncols = len(headers)

        for c_i, t_ in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=c_i, value=t_)
            cell.fill = head_fill
            cell.font = Font(bold=True, color="FFFFFF")
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = border

        r = 2
        for bi, b_ in enumerate(blocks):
            start, end = r, r + b_["n"] - 1
            fill = band_a if bi % 2 == 0 else band_b
            for rr in range(start, end + 1):
                for cc in range(1, ncols + 1):
                    cell = ws.cell(row=rr, column=cc)
                    cell.fill = fill
                    cell.border = border
            for cc, val in ((1, b_["degree"]), (2, b_["branch"]), (3, b_["total"])):
                cell = ws.cell(row=start, column=cc, value=val)
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                if end > start:
                    ws.merge_cells(start_row=start, start_column=cc, end_row=end, end_column=cc)
            for k, items in enumerate(b_["cats"]):
                for i, (name_, cnt_) in enumerate(items):
                    ws.cell(row=start + i, column=4 + 2 * k, value=name_).alignment = Alignment(vertical="center", wrap_text=True)
                    ws.cell(row=start + i, column=5 + 2 * k, value=cnt_).alignment = Alignment(horizontal="center", vertical="center")
            r = end + 1

        widths = [22, 28, 16] + [34, 12] * len(cat_labels)
        for c_i, w_ in enumerate(widths, start=1):
            ws.column_dimensions[get_column_letter(c_i)].width = w_
        ws.freeze_panes = "A2"

        out = io.BytesIO()
        wb.save(out)
        return out.getvalue()


    # =========================================================================
    # 📊 डिग्री+ब्रांच समरी → रंगीन Excel (लाल/नीली रो + कारण कॉलम)
    # =========================================================================
    def generate_summary_excel_bytes(summary_df, sheet_name="Summary", students_df=None, student_flags=None, students_sheet_name="Reason_Students"):
        from openpyxl.styles import PatternFill, Border, Side, Font, Alignment
        from openpyxl.utils import get_column_letter

        safe_sheet = "".join(ch for ch in str(sheet_name) if ch not in '[]:*?/\\')[:31] or "Summary"
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            summary_df.to_excel(writer, index=False, sheet_name=safe_sheet)
            ws = writer.sheets[safe_sheet]

            thin = Side(style="thin", color="BFBFBF")
            border = Border(left=thin, right=thin, top=thin, bottom=thin)
            red_fill = PatternFill("solid", start_color="F8D7DA", end_color="F8D7DA")
            blue_fill = PatternFill("solid", start_color="D1ECF1", end_color="D1ECF1")
            head_fill = PatternFill("solid", start_color="1A3C6E", end_color="1A3C6E")

            cols = list(summary_df.columns)
            red_idx = [i for i, c in enumerate(cols) if "🔴" in str(c)]      # "गलत" वाले कॉलम
            blue_idx = [i for i, c in enumerate(cols) if "🔵" in str(c)]     # "खाली" वाले कॉलम
            reason_idx = next((i for i, c in enumerate(cols) if "Reason" in str(c)), None)

            # हेडर
            for c_i in range(1, len(cols) + 1):
                cell = ws.cell(row=1, column=c_i)
                cell.fill = head_fill
                cell.font = Font(bold=True, color="FFFFFF")
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                cell.border = border

            # डेटा रो: गलत > 0 = लाल सेल, खाली > 0 = नीला सेल, कारण सेल = लाल (गलत हो तो) वरना नीला
            for r_i, (_, row) in enumerate(summary_df.iterrows(), start=2):
                if str(row.iloc[0]).startswith("कुल योग"):
                    for c_i0 in range(len(cols)):
                        cell = ws.cell(row=r_i, column=c_i0 + 1)
                        cell.border = border
                        cell.fill = head_fill
                        cell.font = Font(bold=True, color="FFFFFF")
                    continue
                any_w = any(row.iloc[i] > 0 for i in red_idx)
                any_b = any(row.iloc[i] > 0 for i in blue_idx)
                for c_i0 in range(len(cols)):
                    cell = ws.cell(row=r_i, column=c_i0 + 1)
                    cell.border = border
                    is_reason = (c_i0 == reason_idx)
                    cell.alignment = Alignment(vertical="top", wrap_text=is_reason)
                    fill, fcolor = None, "000000"
                    if c_i0 in red_idx and row.iloc[c_i0] > 0:
                        fill, fcolor = red_fill, "721C24"
                    elif c_i0 in blue_idx and row.iloc[c_i0] > 0:
                        fill, fcolor = blue_fill, "0C5460"
                    elif is_reason and str(row.iloc[c_i0]).strip():
                        fill, fcolor = (red_fill, "721C24") if any_w else ((blue_fill, "0C5460") if any_b else (None, "000000"))
                    if is_reason:
                        cell.value = str(row.iloc[c_i0]).replace("  ||  ", "\n")   # हर श्रेणी नई लाइन में
                    if fill is not None:
                        cell.fill = fill
                        cell.font = Font(bold=True, color=fcolor)

            # कॉलम चौड़ाई (कारण कॉलम चौड़ा + टेक्स्ट रैप)
            for c_i, name in enumerate(cols):
                if c_i == reason_idx:
                    width = 100
                else:
                    longest = max([len(str(name))] + [len(str(v)) for v in summary_df.iloc[:, c_i].tolist()])
                    width = min(max(longest + 3, 12), 40)
                ws.column_dimensions[get_column_letter(c_i + 1)].width = width

            ws.freeze_panes = "C2"
            _last_r = ws.max_row - 1 if str(summary_df.iloc[-1, 0]).startswith("कुल योग") and ws.max_row > 2 else ws.max_row
            ws.auto_filter.ref = f"A1:{get_column_letter(len(cols))}{_last_r}"   # फ़िल्टर/सॉर्ट में Total रो शामिल नहीं

            # 📄 शीट 2: Reason वाले छात्रों की लिस्ट (जिनका Minor/MDC/Voc/PW गलत या खाली है)
            if students_df is not None:
                safe_sheet2 = "".join(ch for ch in str(students_sheet_name) if ch not in '[]:*?/\\')[:31] or "Reason_Students"
                if safe_sheet2 == safe_sheet:
                    safe_sheet2 = (safe_sheet2[:28] + "_2")
                if students_df.empty:
                    pd.DataFrame({"सूचना": ["कोई भी गलत (🔴) या खाली (🔵) एंट्री वाला छात्र नहीं मिला।"]}).to_excel(
                        writer, index=False, sheet_name=safe_sheet2)
                    ws2 = writer.sheets[safe_sheet2]
                    ws2.column_dimensions["A"].width = 70
                else:
                    students_df.to_excel(writer, index=False, sheet_name=safe_sheet2)
                    ws2 = writer.sheets[safe_sheet2]
                    cols2 = list(students_df.columns)
                    reason_i2 = next((i for i, c in enumerate(cols2) if "Reason" in str(c)), None)
                    for c_i in range(1, len(cols2) + 1):
                        cell = ws2.cell(row=1, column=c_i)
                        cell.fill = head_fill
                        cell.font = Font(bold=True, color="FFFFFF")
                        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                        cell.border = border
                    flags = student_flags or {}
                    for r_i in range(len(students_df)):
                        row_has_w = False
                        row_has_b = False
                        for c_i0, cname in enumerate(cols2):
                            cell = ws2.cell(row=r_i + 2, column=c_i0 + 1)
                            cell.border = border
                            cell.alignment = Alignment(vertical="top", wrap_text=(c_i0 == reason_i2))
                            f_list = flags.get(cname)
                            f = f_list[r_i] if f_list is not None else ""
                            if r_i % 2 == 1 and not f:
                                cell.fill = PatternFill("solid", start_color="F4F7FD", end_color="F4F7FD")
                            if f == "w":
                                cell.fill = red_fill
                                cell.font = Font(bold=True, color="721C24")
                                row_has_w = True
                            elif f == "b":
                                cell.fill = blue_fill
                                cell.font = Font(bold=True, color="0C5460")
                                row_has_b = True
                        if reason_i2 is not None:
                            rc = ws2.cell(row=r_i + 2, column=reason_i2 + 1)
                            if row_has_w:
                                rc.fill = red_fill
                                rc.font = Font(bold=True, color="721C24")
                            elif row_has_b:
                                rc.fill = blue_fill
                                rc.font = Font(bold=True, color="0C5460")
                    for c_i, name in enumerate(cols2):
                        if c_i == reason_i2:
                            width = 70
                        else:
                            longest = max([len(str(name))] + [len(str(v)) for v in students_df.iloc[:, c_i].tolist()[:500]])
                            width = min(max(longest + 3, 10), 32)
                        ws2.column_dimensions[get_column_letter(c_i + 1)].width = width
                    ws2.freeze_panes = "B2"
                    ws2.auto_filter.ref = ws2.dimensions
        return output.getvalue()

    # =========================================================================
    # 💻 PANEL 2: WORK / APPROVE PANEL (कॉलम मूव + लाइव स्प्लिट + डेटाबेस रूटिंग)
    # =========================================================================
    if active_panel == "💻 2. Work / Approve Panel":
        st.title("💻 Work / Approve Panel - डेटा प्रोसेसिंग एवं अप्रूवल")
        if is_panel_hidden("p2") and not is_admin_session:
            st.warning("🔒 यह पैनल फिलहाल Admin द्वारा Hide किया गया है। डेटा उपलब्ध नहीं है।")
            st.dataframe(pd.DataFrame(), use_container_width=True)
            st.stop()
    
        # 🗂️ डेटा सीधे मास्टर फ़ाइल (shared_student_database.csv) से आता है — अलग अपलोड की ज़रूरत नहीं
        raw_df = load_master_data()

        # 📅 सबसे पहले: Admission Session चुनें (मास्टर फ़ाइल के सेशन में से)
        _sess_col = next((c for c in raw_df.columns if c.strip().lower() == "admission session"), None) if not raw_df.empty else None
        if _sess_col:
            _sess_vals = sorted({str(v).strip() for v in raw_df[_sess_col].dropna() if str(v).strip() and str(v).strip().lower() != "nan"})
            st.subheader("📅 Step 1: Admission Session चुनें")
            _sess_pick = st.selectbox(
                "Admission Session:", ["-- चुनें --"] + _sess_vals + ["सभी सेशन (All)"],
                key="p2_admission_session_select"
            )
            if _sess_pick == "-- चुनें --":
                st.info("👆 आगे का डेटा देखने/अप्रूव करने के लिए पहले Admission Session चुनें।")
                st.stop()
            if _sess_pick != "सभी सेशन (All)":
                raw_df = raw_df[raw_df[_sess_col].astype(str).str.strip() == _sess_pick].reset_index(drop=True)
            st.divider()
        st.caption(f"🗂️ डेटा-स्रोत: **मास्टर फ़ाइल** ({len(raw_df)} रोज़)" if not raw_df.empty else "")
    
        if raw_df is None or raw_df.empty:
            st.info("🗂️ मास्टर फ़ाइल में अभी कोई डेटा नहीं है। कृपया पहले मास्टर डेटाबेस में छात्रों का डेटा जोड़ें।")
        else:
            # --- कार्य 1: बेकार कॉलम हटाना ---
            st.subheader("🗑️ बेकार कॉलम हटाएं (Remove Unwanted Columns)")
            active_cols = [c for c in raw_df.columns if c not in st.session_state["deleted_cols"]]
        
            cols_to_delete = st.multiselect("हटाने के लिए अनुपयोगी कॉलम चुनें:", options=active_cols)
            if cols_to_delete:
                if st.button("🔴 चुने गए कॉलम हटाएं", key="danger_delete_cols_btn"):
                    st.session_state["deleted_cols"].extend(cols_to_delete)
                    st.success("चयनित कॉलम स्क्रीन से हटा दिए गए!")
                    st.rerun()
        
            final_raw_df = raw_df[active_cols]

            # --- कार्य 2: 🔄 कॉलमों का क्रम बदलना (Left/Right Move Feature) ---
            st.divider()
            st.subheader("🔄 कॉलमों का क्रम बदलें (Move Columns Left/Right)")
            st.write("नीचे दिए गए बॉक्स में क्रम बदलकर कॉलम को आगे-पीछे सेट करें। अप्रूवल के बाद इसी क्रम में लिस्ट लॉक होगी:")
        
            reordered_cols = st.multiselect(
                "कॉलमों का नया क्रम तय करें (सभी आवश्यक कॉलम इसी क्रम में चुनें):",
                options=active_cols,
                default=active_cols,
                key="col_reorder_select"
            )
        
            missing_cols = [c for c in active_cols if c not in reordered_cols]
            if missing_cols:
                reordered_cols.extend(missing_cols)
            
            final_raw_df = final_raw_df[reordered_cols]
        
            deg_col = next((c for c in final_raw_df.columns if any(k in c.lower() for k in ['deg', 'course', 'class'])), final_raw_df.columns[0])
            br_col = next((c for c in final_raw_df.columns if any(k in c.lower() for k in ['branch', 'stream', 'subject'])), final_raw_df.columns[1] if len(final_raw_df.columns) > 1 else final_raw_df.columns[0])

            # पहले हटाई गई (excluded) डिग्री/ब्रांच की रोज़ फ़िल्टर करना
            _ex_d = st.session_state.get("p2_excl_degs", [])
            _ex_b = st.session_state.get("p2_excl_brs", [])
            if _ex_d or _ex_b:
                _keep = ~(final_raw_df[deg_col].astype(str).isin(_ex_d) | final_raw_df[br_col].astype(str).isin(_ex_b))
                _n_ex = int((~_keep).sum())
                final_raw_df = final_raw_df[_keep]
                raw_df = raw_df[_keep.values]
                c_ex1, c_ex2 = st.columns([4, 1])
                c_ex1.caption(f"🚫 {_n_ex} रोज़ हटाई गई हैं (डिग्री: {', '.join(_ex_d) or '-'} | ब्रांच: {', '.join(_ex_b) or '-'})")
                if c_ex2.button("↩️ वापस लाएँ", key="p2_restore_excl_btn"):
                    st.session_state["p2_excl_degs"] = []
                    st.session_state["p2_excl_brs"] = []
                    st.rerun()
        
            # --- कार्य 3: विशिष्ट डिग्री / ब्रांच की पूरी रो डिलीट करना ---
            st.divider()
            st.subheader("❌ विशिष्ट डिग्री / ब्रांच की पूरी रो डिलीट करें")
            st.write("यदि आप किसी खास कोर्स या स्ट्रीम का पूरा डेटा हटाना चाहते हैं, तो यहाँ से चुनें:")
        
            c_row1, c_row2 = st.columns(2)
            with c_row1:
                unique_degrees = final_raw_df[deg_col].dropna().unique().tolist()
                selected_degs = st.multiselect("डिलीट करने के लिए डिग्री (Course) चुनें:", options=unique_degrees)
            with c_row2:
                unique_branches = final_raw_df[br_col].dropna().unique().tolist()
                selected_branches = st.multiselect("डिलीट करने के लिए ब्रांच (Stream) चुनें:", options=unique_branches)
            
            if selected_degs or selected_branches:
                if st.button("🗑️ चुनी हुई रोज़ हमेशा के लिए डिलीट करें", key="danger_delete_rows_btn"):
                    st.session_state["p2_excl_degs"] = list(set(st.session_state.get("p2_excl_degs", [])) | {str(x) for x in selected_degs})
                    st.session_state["p2_excl_brs"] = list(set(st.session_state.get("p2_excl_brs", [])) | {str(x) for x in selected_branches})
                    st.success("🎉  चयनित डिग्री/ब्रांच की रोज़ इस प्रोसेसिंग से हटा दी गईं (मास्टर फ़ाइल में कोई बदलाव नहीं होता)!")
                    st.rerun()

            # फ़िल्टर्ड और रीऑर्डर किए गए डेटा का लाइव प्रीव्यू दिखाना
            st.divider()
            st.subheader("📋 मास्टर फ़ाइल डेटा का लाइव प्रीव्यू (संशोधित क्रम)")
            st.dataframe(final_raw_df, height=350, use_container_width=True)
        
            el_col = next((c for c in final_raw_df.columns if any(k in c.lower() for k in ['elig', 'qual', 'class', 'course', 'deg'])), final_raw_df.columns)
            st.info(f"🔍 सिस्टम ऑटो-वर्गीकरण के लिए **'{el_col}'** कॉलम का उपयोग कर रहा है।")
        
            st.subheader("👀 लाइव प्री-विभाजन समीक्षा (Live Split Preview)")
            ug_preview_rows = []
            pg_preview_rows = []
        
            for _, row in final_raw_df.iterrows():
                if is_pg_route_value(row[el_col]):
                    pg_preview_rows.append(row.to_dict())
                else:
                    ug_preview_rows.append(row.to_dict())
                
            df_ug_preview = pd.DataFrame(ug_preview_rows)
            df_pg_preview = pd.DataFrame(pg_preview_rows)
        
            prev_tab1, prev_tab2 = st.tabs([f"🎓 UG में जाने वाला डेटा ({len(df_ug_preview)} रोज़)", f"📜 PG में जाने वाला डेटा ({len(df_pg_preview)} रोज़)"])
        
            with prev_tab1:
                if not df_ug_preview.empty: st.dataframe(df_ug_preview, height=250, use_container_width=True)
                else: st.caption("कोई डेटा UG श्रेणी में नहीं मिला।")
            with prev_tab2:
                if not df_pg_preview.empty: st.dataframe(df_pg_preview, height=250, use_container_width=True)
                else: st.caption("कोई डेटा PG श्रेणी में नहीं मिला।")

            # --- कार्य 4: फाइनल अप्रूवल और रूटिंग एक्शन (नया क्रम डेटाबेस में लॉक होगा) ---
            st.divider()
            st.subheader("🚀 FINAL ACTION")
            st.write("📈 **डेटा ट्रांसफर:** क्लीन और रीऑर्डर किए गए छात्रों के डेटा को आगे UG (P3) और PG (P4) पैनल में भेजने के लिए यह बटन दबाएँ।")
        
            if st.button("✅ डेटा अप्रूव करें और पैनल्स में ट्रांसफर करें", key="approve_transfer_all_btn"):
                # मास्टर फ़ाइल हर बार पूरा ताज़ा डेटा देती है, इसलिए पुराना UG/PG डेटा बदला जाता है (डुप्लीकेट नहीं बनते)
                # अगर कोई एक सेशन चुना है तो सिर्फ़ उसी सेशन का पुराना डेटा बदला जाएगा, बाकी सेशन सुरक्षित रहेंगे
                _keep_old = {}
                if _sess_col and st.session_state.get("p2_admission_session_select") not in (None, "-- चुनें --", "सभी सेशन (All)"):
                    _chosen = st.session_state["p2_admission_session_select"]
                    for _ct in ("UG", "PG"):
                        _old = load_permanent_data(_ct)
                        if not _old.empty and _sess_col in _old.columns:
                            _old = _old[_old[_sess_col].astype(str).str.strip() != _chosen]
                            _keep_old[_ct] = _old
                cursor.execute("DELETE FROM perma_store WHERE course_type IN ('UG', 'PG')")
                for _ct, _old in _keep_old.items():
                    if not _old.empty:
                        cursor.execute("INSERT INTO perma_store (data_json, course_type) VALUES (?, ?)", (json.dumps(_old.to_dict(orient='records')), _ct))
                if not df_ug_preview.empty:
                    ug_json_str = json.dumps(df_ug_preview[reordered_cols].to_dict(orient='records'))
                    cursor.execute("INSERT INTO perma_store (data_json, course_type) VALUES (?, ?)", (ug_json_str, "UG"))
                if not df_pg_preview.empty:
                    pg_json_str = json.dumps(df_pg_preview[reordered_cols].to_dict(orient='records'))
                    cursor.execute("INSERT INTO perma_store (data_json, course_type) VALUES (?, ?)", (pg_json_str, "PG"))
            
                conn.commit()
                st.success("🎉 बधाई हो! डेटा सफलतापूर्वक कस्टमाइज्ड क्रम में ट्रांसफर और लॉक कर दिया गया है।")
                st.balloons()
                st.rerun()

    elif active_panel == "🎓 3. UG Panel":
        st.title("🎓 Undergraduate (UG) चेकिंग एवं त्रुटि सुधार पैनल")
        if is_panel_hidden("p3") and not is_admin_session:
            st.warning("🔒 यह पैनल फिलहाल Admin द्वारा Hide किया गया है। डेटा उपलब्ध नहीं है।")
            st.dataframe(pd.DataFrame(), use_container_width=True)
            st.stop()
        df_ug = load_permanent_data("UG")
    
        if df_ug is None or df_ug.empty: 
            st.info("ℹ️ UG डेटाबेस खाली है। कृपया पहले Work / Approve Panel (P2) में मास्टर फ़ाइल का डेटा अप्रूव करें।")
        else:
            # ℹ️ UG डेटाबेस की वो डिग्री जो इस पैनल की डिग्री-सूची में नहीं आतीं (इसलिए यहाँ नहीं दिखेंगी)
            _ug_dc, _ = detect_deg_branch_cols(df_ug)
            if _ug_dc:
                _hidden_ug = sorted({
                    d for d in df_ug[_ug_dc].map(_norm_blank_label).unique()
                    if not any(k in d.lower().replace(".", "").replace(" ", "") for k in UG_ALLOWED_KEYWORDS)
                })
                if _hidden_ug:
                    _pg_like = [d for d in _hidden_ug if is_pg_route_value(d)]
                    _msg = ("ℹ️ UG डेटाबेस में ये डिग्री हैं पर इस पैनल की डिग्री-सूची (BA, B.Sc., B.Com., B.H.Sc., BBA, BCA...) में नहीं आतीं, "
                        "इसलिए इस पैनल की टेबल में नहीं दिखेंगी (Dashboard में दिखेंगी): " + ", ".join(_hidden_ug))
                    if _pg_like:
                        _msg += (f"\n\nइनमें {', '.join(_pg_like)} PG की डिग्री लगती है — यह पुराना डेटा है जो पहले UG में चला गया था। "
                             "अब P2 में नई फ़ाइल आने पर ऐसी डिग्री अपने-आप PG में जाएगी।")
                    st.info(_msg)

            # ऑटो-कॉलम डिटेक्शन
            minor_col = next((c for c in df_ug.columns if 'minor' in c.lower()), None)
            mdc_col = next((c for c in df_ug.columns if 'mdc' in c.lower()), None)
            voc_col = next((c for c in df_ug.columns if 'voc' in c.lower() or 'skill' in c.lower()), None)
            pw_col = next((c for c in df_ug.columns if any(k in c.lower() for k in ['pw', 'project', 'ce'])), None)
        
            # ड्रॉपडाउन में दिखाने के लिए यूनिक लिस्ट
            opt_minor = df_ug[minor_col].dropna().unique().tolist() if minor_col else []
            opt_mdc = df_ug[mdc_col].dropna().unique().tolist() if mdc_col else []
            opt_voc = df_ug[voc_col].dropna().unique().tolist() if voc_col else []
            opt_pw = df_ug[pw_col].dropna().unique().tolist() if pw_col else []
        
            st.markdown("### 🛠️ स्टेप 1: डिग्री-वाइज मास्टर गाइडलाइन सेट करें")
            st.caption("नीचे दी गई प्रत्येक डिग्री के बॉक्स को खोलकर उसके मान्य विषय चुनें और फिर 'लॉक करें' बटन दबाएं।")
        
            # --- डेटाबेस से पहले से सेव नियमों को सुरक्षित लोड करना ---
            ug_master_rules = {}
            try:
                cursor.execute("SELECT rules_json FROM locked_rules WHERE panel_prefix = 'ug_master'")
                locked_row = cursor.fetchone()
                if locked_row and locked_row[0]:
                    ug_master_rules = json.loads(locked_row[0])
            except Exception as e:
                pass

            # आपकी मांगी गई 6 विशिष्ट डिग्रियां
            target_degrees = ["BA", "B.Sc.", "B.Sc. Biotechnology", "B.H.Sc.", "B.Com.", "B.Com. Computer"]
            current_configured_rules = {}
        
            for deg in target_degrees:
                with st.expander(f"📘 {deg} के लिए वैध विषय नियम (Valid Subjects)"):
                    c1, c2, c3, c4 = st.columns(4)
                
                    # पहले से सेव नियमों को ड्रॉपडाउन में डिफ़ॉल्ट दिखाना
                    saved_deg_rule = ug_master_rules.get(deg, {})
                    default_min = [x for x in saved_deg_rule.get("minor", []) if x in opt_minor]
                    default_mdc = [x for x in saved_deg_rule.get("mdc", []) if x in opt_mdc]
                    default_voc = [x for x in saved_deg_rule.get("voc", []) if x in opt_voc]
                    default_pw = [x for x in saved_deg_rule.get("pw", []) if x in opt_pw]
                
                    with c1:
                        r_minor = st.multiselect(f"Valid Minor", opt_minor, default=default_min, key=f"ug_min_{deg}")
                    with c2:
                        r_mdc = st.multiselect(f"Valid MDC", opt_mdc, default=default_mdc, key=f"ug_mdc_{deg}")
                    with c3:
                        r_voc = st.multiselect(f"Valid Vocational", opt_voc, default=default_voc, key=f"ug_voc_{deg}")
                    with c4:
                        r_pw = st.multiselect(f"Valid PW/Ap/CE", opt_pw, default=default_pw, key=f"ug_pw_{deg}")
                    
                    current_configured_rules[deg] = {
                        "minor": r_minor,
                        "mdc": r_mdc,
                        "voc": r_voc,
                        "pw": r_pw
                    }
        
            # नियमों को डेटाबेस में लॉक करने का बटन
            if st.button("🔒 UG मास्टर विषय नियमावली लॉक करें", key="lock_master_ug_btn"):
                try:
                    cursor.execute("""
                    INSERT INTO locked_rules (panel_prefix, rules_json) 
                    VALUES (?, ?)
                    ON CONFLICT(panel_prefix) DO UPDATE SET rules_json = excluded.rules_json
                """, ("ug_master", json.dumps(current_configured_rules)))
                    conn.commit()
                    st.success("🎉 सभी डिग्रियों के नियम डेटाबेस में सुरक्षित हो गए हैं और नीचे की लिस्ट रंगीन हो गई है!")
                    st.rerun()
                except Exception as e:
                    st.error(f"त्रुटि: {e}")
            
            st.divider()
        
            # लाइव वैलिडेशन टेबल रन करना (डेटाबेस से लोड किए गए नियमों को प्राथमिकता दें)
            rules_to_apply = ug_master_rules if ug_master_rules else current_configured_rules
            allowed_ug = list(UG_ALLOWED_KEYWORDS)
        
            process_panel_validation(df_ug, "ug", allowed_ug, master_rules=rules_to_apply)

    # =========================================================================
    # 📜 PANEL 4: PG PANEL
    # =========================================================================
    elif active_panel == "📜 4. PG Panel":
        st.title("📜 Postgraduate (PG) चेकिंग एवं त्रुटि सुधार पैनल")
        if is_panel_hidden("p4") and not is_admin_session:
            st.warning("🔒 यह पैनल फिलहाल Admin द्वारा Hide किया गया है। डेटा उपलब्ध नहीं है।")
            st.dataframe(pd.DataFrame(), use_container_width=True)
            st.stop()
        df_pg = load_permanent_data("PG")
        if df_pg is None or df_pg.empty: 
            st.info("ℹ️ PG डेटाबेस खाली है।")
        else: 
            process_panel_validation(df_pg, "pg", list(PG_ROUTE_KEYWORDS))

    # =========================================================================
    # 📊 PANEL 5: DASHBOARD / COUNTER PANEL (फुल स्क्रीन व्यूअर - भाग 1 और भाग 2 आपस में हाइड/शो)
    # =========================================================================
    elif active_panel == "📊 5. Dashboard / Counter Panel":
        # शीर्षक का फ़ॉन्ट छोटा किया गया है
        st.markdown("### 📊 Dashboard - डिग्री-वाइज लाइव काउंटर एवं विस्तृत डेटा समीक्षा")
        if is_panel_hidden("p5") and not is_admin_session:
            st.warning("🔒 यह पैनल फिलहाल Admin द्वारा Hide किया गया है। डेटा उपलब्ध नहीं है।")
            st.dataframe(pd.DataFrame(), use_container_width=True)
            st.stop()
        st.write("नीचे दिए गए टैब पर क्लिक करें, फिर बटन चुनकर 'विषय समरी' या 'छात्रों की फुल लिस्ट' को पूरी स्क्रीन पर देखें।")
    
        # 🛠️ फिक्स: UG और PG दोनों का डेटा लोड करना और लिस्ट बनाना
        df_ug_all = load_permanent_data("UG")
        df_pg_all = load_permanent_data("PG")
    
        # वेरिएबल को सही ढंग से इनिशियलाइज़ करना (यह डिलीट होने से एरर आ रहा था)
        all_dfs = []
        if df_ug_all is not None and not df_ug_all.empty: 
            all_dfs.append(df_ug_all)
        if df_pg_all is not None and not df_pg_all.empty: 
            all_dfs.append(df_pg_all)
    
        # अब यह कंडीशन बिना किसी एरर के बिल्कुल सही रन होगी
        if not all_dfs:
            st.info("ℹ️ काउंट प्रदर्शित करने के लिए डेटाबेस में कोई डेटा उपलब्ध नहीं है। कृपया पहले Work / Approve Panel (P2) में मास्टर फ़ाइल का डेटा अप्रूव करें।")
        else:
            master_df = pd.concat(all_dfs, ignore_index=True)
        
            # ऑटो-कॉलम डिटेक्शन इंजन
            deg_col = next((c for c in master_df.columns if any(k in c.lower() for k in ['deg', 'course', 'class'])), None)
            br_col = next((c for c in master_df.columns if any(k in c.lower() for k in ['branch', 'stream', 'subject'])), None)
            minor_col = next((c for c in master_df.columns if 'minor' in c.lower()), None)
            mdc_col = next((c for c in master_df.columns if 'mdc' in c.lower()), None)
            voc_col = next((c for c in master_df.columns if 'voc' in c.lower() or 'skill' in c.lower()), None)
            pw_col = next((c for c in master_df.columns if any(k in c.lower() for k in ['pw', 'project', 'ce'])), None)
        
            # 🔒 डेटाबेस से UG मास्टर नियमों को सुरक्षित लोड करना
            ug_master_rules = {}
            try:
                cursor.execute("SELECT rules_json FROM locked_rules WHERE panel_prefix = 'ug_master'")
                locked_row = cursor.fetchone()
                if locked_row and locked_row[0]:
                    ug_master_rules = json.loads(locked_row[0])
            except:
                pass

            # डिग्रियों की सूची की सटीक मैपिंग (P3 - UG Rules Panel जैसी ही 6 डिग्री/ब्रांच संरचना)
            target_degrees = [
                {"display": "UG", "scope": "UG"},
                {"display": "PG", "scope": "PG"},
                {"display": "BA", "keywords": ["ba"]},
                {"display": "B.Sc.", "keywords": ["bsc"], "exclude": ["biotech"]},
                {"display": "B.Sc. Biotechnology", "keywords": ["bsc", "biotech"]},
                {"display": "B.H.Sc.", "keywords": ["bhsc"]},
                {"display": "B.Com.", "keywords": ["bcom"], "exclude": ["computer"]},
                {"display": "B.Com. Computer", "keywords": ["bcom", "computer"]}
            ]

            # ---- UG / PG टैब के लिए helper: हर रो की डिग्री पहचानकर उसी के मास्टर नियम लगाना ----
            _degree_defs = [d for d in target_degrees if "keywords" in d]

            def _norm_txt(x):
                return str(x).strip().lower().replace(".", "").replace(" ", "")

            def _row_degree_name(row):
                _d = str(row[deg_col]) if deg_col and deg_col in row.index else ""
                _b = str(row[br_col]) if br_col and br_col in row.index else ""
                _v = (_d + " " + _b).lower().replace(".", "").replace(" ", "")
                _cands = []
                for _dd in _degree_defs:
                    if all(k in _v for k in _dd["keywords"]) and not any(ex in _v for ex in _dd.get("exclude", [])):
                        _cands.append((-len(_dd["keywords"]), _v.find(_dd["keywords"][0]), _dd["display"]))
                if not _cands:
                    return None
                _cands.sort()
                return _cands[0][2]

            # सभी डिग्रियों के लिए इंटरएक्टिव टैब्स
            tab_titles = [deg["display"] for deg in target_degrees]
            tabs = st.tabs(tab_titles)

            for index, deg_info in enumerate(target_degrees):
                with tabs[index]:
                    st.markdown(f"## 🎓 {deg_info['display']} डैशबोर्ड बोर्ड")
                
                    # छात्र सूची में से इस विशिष्ट डिग्री के छात्रों को फ़िल्टर करना
                    _scope = deg_info.get("scope")
                    _empty_rules = {"minor": [], "mdc": [], "voc": [], "pw": []}

                    def _rules_for_row(row):
                        if _scope == "UG":
                            return ug_master_rules.get(_row_degree_name(row), _empty_rules) or _empty_rules
                        if _scope == "PG":
                            return _empty_rules  # PG के लिए अभी कोई मास्टर नियम सेट नहीं है
                        return ug_master_rules.get(deg_info['display'], _empty_rules) or _empty_rules

                    if _scope == "UG":
                        df_deg_filtered = df_ug_all.reset_index(drop=True) if (df_ug_all is not None and not df_ug_all.empty) else pd.DataFrame()
                    elif _scope == "PG":
                        df_deg_filtered = df_pg_all.reset_index(drop=True) if (df_pg_all is not None and not df_pg_all.empty) else pd.DataFrame()
                    elif deg_col and deg_col in master_df.columns:
                        def match_degree(row):
                            # 🔧 फिक्स: Degree column + Branch column दोनों को मिलाकर चेक करना
                            # (Biotechnology / Commerce Computer जैसी ब्रांच अक्सर अलग Branch column में होती है)
                            deg_part = str(row[deg_col]) if deg_col else ""
                            br_part = str(row[br_col]) if br_col and br_col in master_df.columns else ""
                            v = (deg_part + " " + br_part).lower().replace(".", "").replace(" ", "").strip()
                            match = all(k in v for k in deg_info["keywords"])
                            if "exclude" in deg_info:
                                if any(ex in v for ex in deg_info["exclude"]):
                                    match = False
                            return match
                    
                        df_deg_filtered = master_df[master_df.apply(match_degree, axis=1)].reset_index(drop=True)
                    else:
                        df_deg_filtered = pd.DataFrame()

                    if df_deg_filtered.empty:
                        st.warning(f"⚠️ डेटाबेस में `{deg_info['display']}` का कोई छात्र रिकॉर्ड नहीं मिला।")
                        continue
                
                    # मास्टर नियम लोड करना
                    deg_rule = ug_master_rules.get(deg_info['display'], {"minor":[], "mdc":[], "voc":[], "pw":[]})

                    # ✨ जादुई टॉगल बटन: यह तय करेगा कि भाग 1 देखना है या भाग 2
                    view_option = st.radio(
                        "देखने के लिए व्यू चुनें:",
                        options=["📈 भाग 1: विषय काउंटर समरी (Subject Summary Counters)", "📋 भाग 2: छात्रों की विस्तृत लिस्ट (Detailed Student List)"],
                        horizontal=True,
                        key=f"view_toggle_{deg_info['display']}"
                    )
                
                    st.divider()

                    # -------------------------------------------------------------------------
                    # 📈 केवल भाग 1 (विषय काउंटर समरी) - लाइव कलर कोडिंग और अमान्य विषय रेड फिक्स
                    # -------------------------------------------------------------------------
                    if view_option == "📈 भाग 1: विषय काउंटर समरी (Subject Summary Counters)":
                        st.markdown("### 📈 विषयों की लाइव स्थिति (Summary Counters)")
                    
                        # समरी के अंदर माइनर, एमडीसी स्विच करने के लिए हॉरिजॉन्टल बार
                        selected_category = st.radio(
                            "समीक्षा के लिए विषय प्रकार चुनें:",
                            options=["Minor (माइनर)", "MDC (एम.डी.सी.)", "Vocational (व्यवसायिक)", "Project/PW (परियोजना)"],
                            horizontal=True,
                            key=f"cat_selector_{deg_info['display']}"
                        )
                
                        # 🔒 डेटाबेस से P3 (UG Panel) के नियमों को बिल्कुल सही तरीके से लोड करना
                        current_deg_rules = {}
                        try:
                            cursor.execute("SELECT rules_json FROM locked_rules WHERE panel_prefix = 'ug_master'")
                            locked_row = cursor.fetchone()
                            if locked_row and locked_row[0]:
                                all_rules = json.loads(locked_row[0])
                                current_deg_rules = all_rules.get(deg_info['display'], {"minor":[], "mdc":[], "voc":[], "pw":[]})
                        except Exception as e:
                            pass
                
                        cat_mapping = {
                            "Minor (माइनर)": {"col_name": minor_col, "rule_key": "minor", "label": "विषय का नाम (Minor Subject)"},
                            "MDC (एम.डी.सी.)": {"col_name": mdc_col, "rule_key": "mdc", "label": "विषय का नाम (MDC Subject)"},
                            "Vocational (व्यवसायिक)": {"col_name": voc_col, "rule_key": "voc", "label": "विषय का नाम (Vocational Subject)"},
                            "Project/PW (परियोजना)": {"col_name": pw_col, "rule_key": "pw", "label": "प्रोजेक्ट प्रकार (Project Type)"}
                        }
                
                        current_cat = cat_mapping[selected_category]
                
                        if current_cat["col_name"] and current_cat["col_name"] in df_deg_filtered.columns:
                            # काउंट्स (फ्रीक्वेंसी) की लाइव गणना
                            counts = df_deg_filtered[current_cat["col_name"]].dropna().value_counts().reset_index()
                            counts.columns = ["Subject", "Count"]

                            if _scope:
                                # UG/PG टैब: हर छात्र की अपनी डिग्री के नियम से सही/गलत गिनना
                                _c_col = current_cat["col_name"]
                                _c_rk = current_cat["rule_key"]
                                _sub = df_deg_filtered[df_deg_filtered[_c_col].notna()].copy()

                                def _wrong_flag(r):
                                    _vs = {_norm_txt(x) for x in _rules_for_row(r).get(_c_rk, [])}
                                    return bool(_vs) and (_norm_txt(r[_c_col]) not in _vs)

                                _sub["_wrong"] = _sub.apply(_wrong_flag, axis=1)
                                counts = (
                                    _sub.groupby(_c_col)["_wrong"].agg(["size", "sum"]).reset_index()
                                    .sort_values("size", ascending=False).reset_index(drop=True)
                                )
                                counts.columns = ["Subject", "Count", "Wrong"]
                                counts["Wrong"] = counts["Wrong"].astype(int)
                        
                            if not counts.empty:
                                # P3 के लॉक नियमों से वैध विषयों का क्लीन सेट बनाना
                                valid_list = current_deg_rules.get(current_cat["rule_key"], [])
                                valid_set = {str(x).strip().lower().replace(".", "").replace(" ", "") for x in valid_list}
                            
                                # ✨ भाग 1 के लिए नया सख्त रो स्टाइलर इंजन (गलत विषय = चमकदार गाढ़ा लाल)
                                def row_styler(row):
                                    if "Wrong" in row.index:
                                        if row["Wrong"] > 0:
                                            return ['background-color: #f8d7da; color: #721c24; font-weight: bold; border: 2px solid #dc3545;'] * len(row)
                                        return [''] * len(row)
                                    sub_val = str(row["Subject"]).strip().lower().replace(".", "").replace(" ", "")
                                    # यदि P3 में विषय चुने गए हैं और छात्र का विषय उसमें नहीं है, तो पूरी रो लाल होगी
                                    if valid_set and (sub_val not in valid_set):
                                        return ['background-color: #f8d7da; color: #721c24; font-weight: bold; border: 2px solid #dc3545;'] * len(row)
                                    return [''] * len(row)
                            
                                if current_cat["rule_key"] == "pw":
                                    _sum_hdr_html = "<div class='mini-head'>Project Type Summary<br><span>(प्रोजेक्ट प्रकार की समरी सूची)</span></div>"
                                else:
                                    _sum_hdr_html = "<div class='mini-head'>Subject Distribution Summary<br><span>(विषय आवंटन की समरी सूची)</span></div>"
                                _sum_key = "subsum_" + "".join(ch if ch.isalnum() else "_" for ch in deg_info["display"])
                                _show_summary = inline_section_toggle(_sum_key, _sum_hdr_html)
                            
                                # फुल स्क्रीन चौड़ाई (Width) के साथ काउंटर तालिका रेंडर करना
                                # 🔧 फिक्स: टेबल की ऊंचाई अब रोज़ की संख्या के हिसाब से खुद-ब-खुद सेट होगी,
                                # ताकि पूरी लिस्ट एक बार में दिखे और स्क्रॉल न करना पड़े
                                if _show_summary:
                                    dynamic_height = min(38 * (len(counts) + 1) + 3, 2000)
                                    st.dataframe(
                                        counts.style.apply(row_styler, axis=1), 
                                        hide_index=True, 
                                        use_container_width=True,
                                        height=dynamic_height,
                                        column_config={
                                            "Subject": st.column_config.TextColumn(label=current_cat["label"], width=600), 
                                            "Count": st.column_config.NumberColumn(label="छात्रों की संख्या (Count)", width=150),
                                            **({"Wrong": st.column_config.NumberColumn(label="🔴 गलत (Wrong)", width=150)} if _scope else {})
                                        }
                                    )
                            else:
                                st.caption("इस श्रेणी में कोई डेटा उपलब्ध नहीं है।")
                        else:
                            st.caption("डेटाबेस में संबंधित कॉलम नहीं मिला।")

                        # ---------------------------------------------------------------------
                        # 🎓 केवल UG / PG टैब: डिग्री + ब्रांच-वाइज समरी (Minor + MDC + Voc + PW सभी एक साथ)
                        # ---------------------------------------------------------------------
                        if _scope:
                            st.divider()
                            st.markdown(
                                '<div class="sum-banner"><div class="t">🎓 डिग्री + ब्रांच-वाइज समरी — Minor + MDC + Voc + PW (सभी एक साथ)</div></div>',
                                unsafe_allow_html=True
                            )
                            st.caption("हर डिग्री और ब्रांच के सामने कुल छात्र, और Minor / MDC / Vocational / Project-PW हर श्रेणी में कितने सही (✅), गलत (🔴) और खाली (🔵) हैं। 🔴 लाल सेल = उस डिग्री के मास्टर नियम से मेल न खाने वाला विषय | 🔵 नीला सेल = डेटा खाली है (PG में अभी कोई मास्टर नियम नहीं है, इसलिए वहाँ लाल नहीं दिखेगा)। 📝 कारण कॉलम में हर श्रेणी का पूरा कारण लिखा आता है।")

                            _db = df_deg_filtered.copy()

                            # डिग्री / ब्रांच कॉलम इसी टैब के अपने डेटा से पहचानना (PG के कॉलम नाम अलग हो सकते हैं)
                            _dc = deg_col if (deg_col and deg_col in _db.columns) else next(
                                (c for c in _db.columns if any(k in str(c).lower() for k in ['deg', 'course', 'class'])), None)
                            _skip_kw = ['minor', 'mdc', 'voc', 'skill', 'pw', 'project']
                            _bc = br_col if (br_col and br_col in _db.columns and br_col != _dc) else None
                            if _bc is None:
                                _bc = next((c for c in _db.columns if c != _dc and any(k in str(c).lower() for k in ['branch', 'stream'])), None)
                            if _bc is None:
                                _bc = next((c for c in _db.columns if c != _dc and 'subject' in str(c).lower()
                                            and not any(k in str(c).lower() for k in _skip_kw)), None)

                            def _clean_key(series):
                                s_ = series.astype(str).str.strip()
                                return s_.mask(series.isna() | (s_ == "") | (s_.str.lower() == "nan"), "(खाली/Blank)")

                            _db["Degree (डिग्री)"] = _clean_key(_db[_dc]) if _dc else "—"
                            _db["Branch (ब्रांच)"] = _clean_key(_db[_bc]) if _bc else "—"

                            _deg_options = ["सभी डिग्री"] + sorted(_db["Degree (डिग्री)"].unique().tolist())
                            _deg_pick = st.selectbox(
                                "डिग्री फ़िल्टर:",
                                _deg_options,
                                key=f"db_deg_filter_{deg_info['display']}_all"
                            )
                            if _deg_pick != "सभी डिग्री":
                                _db = _db[_db["Degree (डिग्री)"] == _deg_pick]

                            _red = 'background-color: #f8d7da; color: #721c24; font-weight: bold; border: 2px solid #dc3545;'
                            _blue = 'background-color: #d1ecf1; color: #0c5460; font-weight: bold; border: 2px solid #17a2b8;'

                            # चारों श्रेणियाँ एक साथ: Minor / MDC / Voc / PW
                            _all_cats = [("Minor", "minor", minor_col), ("MDC", "mdc", mdc_col), ("Voc", "voc", voc_col), ("PW", "pw", pw_col)]
                            _present_cats = [(l_, k_, c_) for (l_, k_, c_) in _all_cats if c_ and c_ in _db.columns]
                            _missing_cats = [l_ for (l_, k_, c_) in _all_cats if not (c_ and c_ in _db.columns)]

                            if _present_cats:
                                if _missing_cats:
                                    st.caption("ℹ️ इस डेटा में इन श्रेणियों का कॉलम नहीं मिला, इसलिए ये समरी में शामिल नहीं हैं: " + ", ".join(_missing_cats))

                                # हर छात्र की डिग्री के हिसाब से मास्टर-नियम वाली डिग्री (एक बार निकालना)
                                if _scope == "UG" and len(_db):
                                    _db["_rd"] = _db.apply(_row_degree_name, axis=1)
                                else:
                                    _db["_rd"] = None

                                # ⚪ खाली-छूट वाली डिग्री+ब्रांच (UG/PG की सेटिंग)
                                _ex_pairs = get_blank_exempt_pairs("ug" if _scope == "UG" else "pg")
                                _ex_s = pd.Series([(d_, b_) in _ex_pairs for d_, b_ in zip(_db["Degree (डिग्री)"], _db["Branch (ब्रांच)"])], index=_db.index)

                                # हर श्रेणी के लिए गलत / खाली फ्लैग
                                for _lbl, _rk, _cn in _present_cats:
                                    _empty_s = _db[_cn].isna() | (_db[_cn].astype(str).str.strip() == "")
                                    _blank_s = _empty_s & ~_ex_s     # ⚪ खाली-छूट वाली डिग्री+ब्रांच में खाली नहीं गिनना
                                    _norm_s = _db[_cn].astype(str).map(_norm_txt)
                                    _wrong_s = pd.Series(False, index=_db.index)
                                    if _scope == "UG":
                                        for _rd_name in _db["_rd"].dropna().unique():
                                            _allowed = {_norm_txt(x) for x in ((ug_master_rules.get(_rd_name) or {}).get(_rk, []))}
                                            if _allowed:
                                                _wrong_s = _wrong_s | ((_db["_rd"] == _rd_name) & ~_empty_s & ~_norm_s.isin(_allowed))
                                    _db[f"_w_{_rk}"] = _wrong_s
                                    _db[f"_b_{_rk}"] = _blank_s

                                _first_rk = _present_cats[0][1]
                                _agg = {"_total": (f"_w_{_first_rk}", "size")}
                                for _lbl, _rk, _cn in _present_cats:
                                    _agg[f"_w_{_rk}"] = (f"_w_{_rk}", "sum")
                                    _agg[f"_b_{_rk}"] = (f"_b_{_rk}", "sum")
                                _grp = _db.groupby(["Degree (डिग्री)", "Branch (ब्रांच)"]).agg(**_agg).reset_index()

                                # 📝 कारण (Reason): हर श्रेणी का पूरा कारण (कौन सा विषय गलत, कितने खाली)
                                def _reason_for_group(g):
                                    lines = []
                                    for _lbl, _rk, _cn in _present_cats:
                                        parts = []
                                        w = g[g[f"_w_{_rk}"]]
                                        if len(w):
                                            for _rd_name, _wg in w.groupby("_rd"):
                                                _vc = _wg[_cn].astype(str).str.strip().value_counts()
                                                _subj = ", ".join(f"{k} ({v})" for k, v in _vc.items())
                                                parts.append(f"🔴 {len(_wg)} छात्रों का विषय {_rd_name} के मास्टर नियम में मान्य नहीं है → {_subj}")
                                        _bn = int(g[f"_b_{_rk}"].sum())
                                        if _bn:
                                            parts.append(f"🔵 {_bn} छात्रों का खाली है (डेटा नहीं भरा गया)")
                                        if parts:
                                            lines.append(f"{_lbl}: " + " ; ".join(parts))
                                    return "  ||  ".join(lines)

                                _reasons = {}
                                for (_d_k, _b_k), _g in _db.groupby(["Degree (डिग्री)", "Branch (ब्रांच)"]):
                                    _reasons[(_d_k, _b_k)] = _reason_for_group(_g)

                                db_summary = _grp[["Degree (डिग्री)", "Branch (ब्रांच)"]].copy()
                                db_summary["कुल छात्र (Total)"] = _grp["_total"].astype(int)
                                for _lbl, _rk, _cn in _present_cats:
                                    _w_col = _grp[f"_w_{_rk}"].astype(int)
                                    _b_col = _grp[f"_b_{_rk}"].astype(int)
                                    db_summary[f"{_lbl} ✅ सही"] = db_summary["कुल छात्र (Total)"] - _w_col - _b_col
                                    db_summary[f"{_lbl} 🔴 गलत"] = _w_col
                                    db_summary[f"{_lbl} 🔵 खाली"] = _b_col
                                db_summary["📝 कारण (Reason)"] = [
                                    _reasons.get((_d_k, _b_k), "")
                                    for _d_k, _b_k in zip(_grp["Degree (डिग्री)"], _grp["Branch (ब्रांच)"])
                                ]
                                db_summary = db_summary.sort_values(
                                    ["Degree (डिग्री)", "कुल छात्र (Total)"], ascending=[True, False]
                                ).reset_index(drop=True)
                                _db_core = db_summary.copy()   # मेट्रिक्स के लिए बिना Total रो वाली कॉपी
                                _tot = {c_: "" for c_ in db_summary.columns}
                                _tot["Degree (डिग्री)"] = "कुल योग (GRAND TOTAL)"
                                _tot["Branch (ब्रांच)"] = ""
                                for c_ in db_summary.columns:
                                    if c_ not in ("Degree (डिग्री)", "Branch (ब्रांच)", "📝 कारण (Reason)"):
                                        _tot[c_] = int(db_summary[c_].sum())
                                db_summary = pd.concat([db_summary, pd.DataFrame([_tot])], ignore_index=True)

                                _wrong_cols = [c for c in db_summary.columns if "🔴" in c]
                                _blank_cols = [c for c in db_summary.columns if "🔵" in c]

                                def _db_cell_styler(row):
                                    if str(row["Degree (डिग्री)"]).startswith("कुल योग"):
                                        return ['background-color: #1a3c6e; color: #ffffff; font-weight: bold;'] * len(row)
                                    _any_w = any(row[c] > 0 for c in _wrong_cols)
                                    _any_b = any(row[c] > 0 for c in _blank_cols)
                                    out = []
                                    for c in row.index:
                                        if c in _wrong_cols and row[c] > 0:
                                            out.append(_red)
                                        elif c in _blank_cols and row[c] > 0:
                                            out.append(_blue)
                                        elif c == "📝 कारण (Reason)" and row[c]:
                                            out.append(_red if _any_w else (_blue if _any_b else ""))
                                        else:
                                            out.append("")
                                    return out

                                # 📄 शीट 2 के लिए: Reason वाले (गलत/खाली) छात्रों की व्यक्तिगत लिस्ट
                                _any_flag = pd.Series(False, index=_db.index)
                                for _lbl, _rk, _cn in _present_cats:
                                    _any_flag = _any_flag | _db[f"_w_{_rk}"] | _db[f"_b_{_rk}"]
                                _stu = _db[_any_flag].sort_values(["Degree (डिग्री)", "Branch (ब्रांच)"], kind="stable")
                                _orig_cols = [c for c in df_deg_filtered.columns if c in _stu.columns]

                                def _stu_reason(r):
                                    out_ = []
                                    for _lbl, _rk, _cn in _present_cats:
                                        if r[f"_w_{_rk}"]:
                                            _rd_ = r["_rd"] if r["_rd"] else "इस डिग्री"
                                            out_.append(f"🔴 {_lbl}: '{str(r[_cn]).strip()}' — {_rd_} के मास्टर नियम में मान्य नहीं")
                                        elif r[f"_b_{_rk}"]:
                                            out_.append(f"🔵 {_lbl}: खाली (डेटा नहीं भरा गया)")
                                    return "\n".join(out_)

                                students_df = _stu[_orig_cols].copy().reset_index(drop=True)
                                students_df.insert(0, "क्र.सं.", range(1, len(students_df) + 1))
                                students_df["📝 कारण (Reason)"] = [_stu_reason(r_) for _, r_ in _stu.iterrows()]
                                student_flags = {}
                                for _lbl, _rk, _cn in _present_cats:
                                    student_flags[_cn] = [
                                        "w" if w_ else ("b" if b_ else "")
                                        for w_, b_ in zip(_stu[f"_w_{_rk}"].tolist(), _stu[f"_b_{_rk}"].tolist())
                                    ]

                                dm1, dm2, dm3 = st.columns(3)
                                with dm1:
                                    st.metric("🎓 कुल डिग्री+ब्रांच कॉम्बिनेशन", len(_db_core))
                                with dm2:
                                    st.metric("🔴 कुल गलत एंट्री (सभी श्रेणी)", int(_db_core[_wrong_cols].to_numpy().sum()))
                                with dm3:
                                    st.metric("🔵 कुल खाली सेल (सभी श्रेणी)", int(_db_core[_blank_cols].to_numpy().sum()))

                                st.dataframe(
                                    db_summary.style.apply(_db_cell_styler, axis=1),
                                    hide_index=True,
                                    use_container_width=True,
                                    height=min(38 * (len(db_summary) + 1) + 3, 650),
                                    column_config={"📝 कारण (Reason)": st.column_config.TextColumn(width=900)}
                                )

                                # 📝 लंबा कारण टेबल के सेल में कट सकता है, इसलिए पूरा कारण यहाँ भी दिखाना
                                _reason_rows = db_summary[db_summary["📝 कारण (Reason)"] != ""]
                                if not _reason_rows.empty:
                                    with st.expander(f"📝 पूरा कारण देखें (लाल/नीली {len(_reason_rows)} ब्रांच)"):
                                        for _, _rr in _reason_rows.iterrows():
                                            _rtxt = str(_rr["📝 कारण (Reason)"])
                                            _lines_html = ""
                                            for _ln in _rtxt.split("  ||  "):
                                                _lc = "red" if "🔴" in _ln else "blue"
                                                _lines_html += f'<div class="rs-line {_lc}">{_html.escape(_ln).replace("$", "&#36;")}</div>'
                                            _cc = "red" if "🔴" in _rtxt else "blue"
                                            _ttl = _html.escape(f"{_rr['Degree (डिग्री)']} → {_rr['Branch (ब्रांच)']}").replace("$", "&#36;")
                                            st.markdown(
                                                f'<div class="reason-card {_cc}"><div class="rc-title">{_ttl}</div>{_lines_html}</div>',
                                                unsafe_allow_html=True
                                            )
                            else:
                                # इस डेटा में Minor/MDC/Voc/PW में से कोई कॉलम नहीं है — तब भी डिग्री+ब्रांच की गिनती दिखाना
                                students_df, student_flags = None, None
                                st.info("ℹ️ इस डेटा में Minor / MDC / Vocational / Project-PW में से किसी का कॉलम नहीं मिला, इसलिए नीचे सिर्फ डिग्री + ब्रांच के हिसाब से छात्रों की कुल संख्या दिखाई जा रही है।")
                                st.caption("इस डेटा में उपलब्ध कॉलम: " + ", ".join(str(c) for c in df_deg_filtered.columns))
                                db_summary = (
                                    _db.groupby(["Degree (डिग्री)", "Branch (ब्रांच)"]).size().reset_index(name="कुल छात्र (Total)")
                                    .sort_values(["Degree (डिग्री)", "कुल छात्र (Total)"], ascending=[True, False]).reset_index(drop=True)
                                )
                                dm1, dm2 = st.columns(2)
                                with dm1:
                                    st.metric("🎓 कुल डिग्री+ब्रांच कॉम्बिनेशन", len(db_summary))
                                with dm2:
                                    st.metric("👥 कुल छात्र", int(db_summary["कुल छात्र (Total)"].sum()))
                                db_summary = pd.concat([db_summary, pd.DataFrame([{
                                    "Degree (डिग्री)": "कुल योग (GRAND TOTAL)", "Branch (ब्रांच)": "",
                                    "कुल छात्र (Total)": int(db_summary["कुल छात्र (Total)"].sum())}])], ignore_index=True)
                                st.dataframe(
                                    db_summary,
                                    hide_index=True,
                                    use_container_width=True,
                                    height=min(38 * (len(db_summary) + 1) + 3, 650)
                                )

                            # 📥 डाउनलोड पैनल (CSV + 2-शीट Excel)
                            _n_reason_stu = 0 if students_df is None else len(students_df)
                            _chips = f'<span class="dl-chip">📑 {len(db_summary) - 1 if len(db_summary) > 1 else len(db_summary)} डिग्री+ब्रांच रो</span>'
                            if students_df is not None:
                                _chips += f'<span class="dl-chip red">👥 Reason वाले छात्र: {_n_reason_stu}</span>'
                            st.markdown(
                                f'<div class="dl-panel-head"><span class="h">📥 समरी डाउनलोड करें</span>{_chips}</div>',
                                unsafe_allow_html=True
                            )
                            st.markdown(
                                '<div class="dl-hint">📄 <b>CSV</b> — सिर्फ़ यह समरी टेबल (Total रो सहित)<br>'
                            '📊 <b>Excel</b> — रंगीन, <b>2 शीट</b>: शीट 1 = समरी, शीट 2 = Reason वाले छात्रों की पूरी लिस्ट</div>',
                                unsafe_allow_html=True
                            )
                            _dl1, _dl2 = st.columns(2)
                            with _dl1:
                                st.download_button(
                                    label="📄  CSV डाउनलोड  (सिर्फ़ समरी)",
                                    data=db_summary.to_csv(index=False).encode("utf-8-sig"),
                                    file_name=f"{deg_info['display']}_Degree_Branch_All_Categories_Summary.csv",
                                    mime="text/csv",
                                    key=f"db_dl_{deg_info['display']}_all",
                                    use_container_width=True
                                )
                            with _dl2:
                                st.download_button(
                                    label="📊  Excel डाउनलोड  (2 शीट: समरी + Reason वाले छात्र)",
                                    data=generate_summary_excel_bytes(
                                        db_summary,
                                        sheet_name=f"{deg_info['display']}_Summary",
                                        students_df=students_df,
                                        student_flags=student_flags,
                                        students_sheet_name="Reason_Students"
                                    ),
                                    file_name=f"{deg_info['display']}_Degree_Branch_All_Categories_Summary.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    key=f"db_dl_xlsx_{deg_info['display']}_all",
                                    use_container_width=True
                                )

                            # ---------------------------------------------------------------------
                            # 📑 ब्रांच-वाइज विषय शीट: Degree/Branch/Total Admission मर्ज,
                            # नीचे हर रो में Minor / MDC / Voc / PW के अलग-अलग नाम + count
                            # ---------------------------------------------------------------------
                            if _present_cats:
                                st.divider()
                                st.markdown(
                                    '<div class="sum-banner"><div class="t">📑 ब्रांच-वाइज विषय शीट — Total Admission + Minor / MDC / Voc / PW के नाम व संख्या</div></div>',
                                    unsafe_allow_html=True
                                )
                                st.caption("हर Degree/Branch के लिए Degree, Branch और Total Admission एक बार (मर्ज) दिखते हैं, और उसके नीचे की रो में हर श्रेणी के अलग-अलग विषय अपनी संख्या के साथ आते हैं। जिस श्रेणी में विषय कम हैं वहाँ बाकी सेल खाली रहते हैं। (ऊपर चुना गया डिग्री फ़िल्टर यहाँ भी लागू है)")
                                _bs_cats = [(l_, c_) for (l_, k_, c_) in _present_cats]
                                _bs_labels = [l_ for l_, _c in _bs_cats]
                                _bs_blocks = build_branch_subject_blocks(_db, "Degree (डिग्री)", "Branch (ब्रांच)", _bs_cats)
                                st.markdown(branch_subject_sheet_html(_bs_blocks, _bs_labels), unsafe_allow_html=True)
                                st.download_button(
                                    label="📊  Excel डाउनलोड  (ब्रांच-वाइज विषय शीट, merged)",
                                    data=generate_branch_subject_sheet_excel_bytes(_bs_blocks, _bs_labels, sheet_name=f"{deg_info['display']}_Branch_Subjects"),
                                    file_name=f"{deg_info['display']}_Branch_Subject_Sheet.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    key=f"db_dl_bs_{deg_info['display']}_all",
                                    use_container_width=True
                                )

                    # -------------------------------------------------------------------------
                    # 📋 केवल भाग 2 (छात्रों की विस्तृत लिस्ट) - 1 से शुरू होने वाला सीरियल नंबर फिक्स
                    # -------------------------------------------------------------------------
                    elif view_option == "📋 भाग 2: छात्रों की विस्तृत लिस्ट (Detailed Student List)":
                        st.markdown(f"### 📋 {deg_info['display']} के सभी छात्रों का विस्तृत डेटा")
                    
                        df_to_show = df_deg_filtered.copy()
                    
                        # 🔍 लाइव सर्च बार फीचर
                        search_query = st.text_input(
                            f"🔍 {deg_info['display']} डेटा में सर्च करें (नाम, रोल नंबर या विषय डालें):", 
                            key=f"search_{deg_info['display']}"
                        )
                    
                        if search_query:
                            mask = df_to_show.astype(str).apply(lambda row: row.str.contains(search_query, case=False).any(), axis=1)
                            df_to_show = df_to_show[mask]
                
                        # --- 🛠️ सटीक लाइव कॉलम डिटेक्शन ---
                        actual_minor = next((c for c in df_to_show.columns if 'minor' in c.lower()), None)
                        actual_mdc = next((c for c in df_to_show.columns if 'mdc' in c.lower()), None)
                        actual_voc = next((c for c in df_to_show.columns if 'voc' in c.lower() or 'skill' in c.lower()), None)
                        actual_pw = next((c for c in df_to_show.columns if any(k in c.lower() for k in ['pw', 'project', 'ce'])), None)
                        actual_br = next((c for c in df_to_show.columns if any(k in c.lower() for k in ['branch', 'stream', 'subject'])), None)
                
                        # 🔒 डेटाबेस से P3 के नियमों को लोड करना
                        current_deg_rules = {}
                        try:
                            cursor.execute("SELECT rules_json FROM locked_rules WHERE panel_prefix = 'ug_master'")
                            locked_row = cursor.fetchone()
                            if locked_row and locked_row[0]:
                                all_rules = json.loads(locked_row[0])
                                current_deg_rules = all_rules.get(deg_info['display'], {"minor":[], "mdc":[], "voc":[], "pw":[]})
                        except Exception as e:
                            pass
                
                        # --- 📊 लाइव काउंटर मीटर ---
                        blank_count = 0
                        wrong_count = 0
                    
                        targets_for_counting = {
                            actual_minor: 'minor', 
                            actual_mdc: 'mdc', 
                            actual_voc: 'voc', 
                            actual_pw: 'pw'
                        }
                    
                        _ex_prefix = "ug" if _scope == "UG" else ("pg" if _scope == "PG" else None)
                        _ex_list = blank_exempt_mask(df_to_show, _ex_prefix).tolist()   # ⚪ खाली-छूट वाली रो
                        for _pos, (index, row) in enumerate(df_to_show.iterrows()):
                            _row_rules = _rules_for_row(row)
                            for col_name, rule_key in targets_for_counting.items():
                                if col_name and col_name in df_to_show.columns:
                                    val = row[col_name]
                                    if pd.isna(val) or str(val).strip() == "":
                                        if not _ex_list[_pos]:
                                            blank_count += 1
                                    else:
                                        val_clean = str(val).strip().lower().replace(".", "").replace(" ", "")
                                        valid_list = _row_rules.get(rule_key, [])
                                        valid_set = {str(x).strip().lower().replace(".", "").replace(" ", "") for x in valid_list}
                                        if valid_set and (val_clean not in valid_set):
                                            wrong_count += 1
                
                        # स्क्रीन पर लाइव स्टेट्स कार्ड्स दिखाना
                        metric_c1, metric_c2, metric_c3 = st.columns(3)
                        with metric_c1:
                            st.metric(label="👥 कुल छात्र रिकॉर्ड (Total Rows)", value=len(df_to_show))
                        with metric_c2:
                            st.metric(label="🔵 कुल खाली सेल (Missing Data)", value=blank_count)
                        with metric_c3:
                            st.metric(label="🔴 कुल गलत विषय (Rule Mismatch)", value=wrong_count)
                
                        st.caption("🔵 नीला सेल = डेटा गायब है | 🔴 लाल सेल = गलत विषय (Panel 3 में आपके द्वारा चुने गए विषयों के अलावा बाकी सब)")
                
                        # ✨ जादू यहाँ है: टेबल दिखाने से पहले इंडेक्स को 1 से शुरू करने के लिए शिफ्ट करना
                        df_to_show.index = range(1, len(df_to_show) + 1)
                
                        # --- 🎨 लाइव कलर कोडिंग स्टाइलर इंजन ---
                        def full_table_styler(dataframe):
                            s_df = pd.DataFrame('', index=dataframe.index, columns=dataframe.columns)
                            targets = {
                                actual_minor: 'minor', 
                                actual_mdc: 'mdc', 
                                actual_voc: 'voc', 
                                actual_pw: 'pw'
                            }
                            for _pos, (index, row) in enumerate(dataframe.iterrows()):
                                row_has_wrong = False
                                _row_rules = _rules_for_row(row)
                                for col_name, rule_key in targets.items():
                                    if col_name and col_name in dataframe.columns:
                                        val = row[col_name]
                                        if pd.isna(val) or str(val).strip() == "":
                                            if not _ex_list[_pos]:
                                                s_df.at[index, col_name] = 'background-color: #d1ecf1; color: #0c5460; font-weight: bold; border: 2px solid #17a2b8;'
                                        else:
                                            val_clean = str(val).strip().lower().replace(".", "").replace(" ", "")
                                            valid_list = _row_rules.get(rule_key, [])
                                            valid_set = {str(x).strip().lower().replace(".", "").replace(" ", "") for x in valid_list}
                                            if valid_set and (val_clean not in valid_set):
                                                s_df.at[index, col_name] = 'background-color: #f8d7da; color: #721c24; font-weight: bold; border: 2px solid #dc3545;'
                                                row_has_wrong = True
                                # 🟡 फिक्स: अगर इस रो में कोई भी सेल (Minor/MDC/Voc/PW) लाल (गलत) है,
                                # तो उसी रो के Branch सेल को पीला (Yellow) कर देना
                                if row_has_wrong and actual_br and actual_br in dataframe.columns:
                                    s_df.at[index, actual_br] = 'background-color: #fff3cd; color: #856404; font-weight: bold; border: 2px solid #ffc107;'
                            return s_df
                
                        # full screen view table render
                        st.dataframe(
                            df_to_show.style.apply(full_table_styler, axis=None),
                            height=550,
                            use_container_width=True
                        )

                        # -------------------------------------------------------------------------
                        # 🟡 ब्रांच-वाइज सही/गलत समरी (जिस ब्रांच में कोई गलत छात्र है वो पीली दिखेगी)
                        # -------------------------------------------------------------------------
                        if actual_br and actual_br in df_to_show.columns:
                            st.divider()
                            st.markdown("### 🟡 ब्रांच-वाइज सही / गलत समरी")
                            st.caption("हर ब्रांच के सामने कुल कितने छात्र हैं, उनमें से कितने सही (✅) हैं और कितने गलत (🔴) हैं — जिस ब्रांच में कम-से-कम एक गलत छात्र है, वो रो पीली (Yellow) दिखेगी।")

                            targets_for_branch_summary = {
                                actual_minor: 'minor',
                                actual_mdc: 'mdc',
                                actual_voc: 'voc',
                                actual_pw: 'pw'
                            }

                            def _row_has_wrong_subject(row):
                                _row_rules = _rules_for_row(row)
                                for col_name, rule_key in targets_for_branch_summary.items():
                                    if col_name and col_name in df_to_show.columns:
                                        val = row[col_name]
                                        if not (pd.isna(val) or str(val).strip() == ""):
                                            val_clean = str(val).strip().lower().replace(".", "").replace(" ", "")
                                            valid_list = _row_rules.get(rule_key, [])
                                            valid_set = {str(x).strip().lower().replace(".", "").replace(" ", "") for x in valid_list}
                                            if valid_set and (val_clean not in valid_set):
                                                return True
                                return False

                            branch_summary_rows = []
                            for branch_val, group in df_to_show.groupby(df_to_show[actual_br].fillna("(खाली/Blank)").replace("", "(खाली/Blank)")):
                                total_n = len(group)
                                wrong_n = int(group.apply(_row_has_wrong_subject, axis=1).sum())
                                correct_n = total_n - wrong_n
                                branch_summary_rows.append({
                                    "Branch (ब्रांच)": branch_val,
                                    "कुल छात्र (Total)": total_n,
                                    "✅ सही (Correct)": correct_n,
                                    "🔴 गलत (Wrong)": wrong_n
                                })

                            branch_summary_df = pd.DataFrame(branch_summary_rows).sort_values(
                                "कुल छात्र (Total)", ascending=False
                            ).reset_index(drop=True)

                            def branch_summary_row_styler(row):
                                if row["🔴 गलत (Wrong)"] > 0:
                                    return ['background-color: #fff3cd; color: #856404; font-weight: bold; border: 1px solid #ffc107;'] * len(row)
                                return ['background-color: #d4edda; color: #155724; font-weight: bold; border: 1px solid #28a745;'] * len(row)

                            branch_dyn_height = min(38 * (len(branch_summary_df) + 1) + 3, 1500)
                            st.dataframe(
                                branch_summary_df.style.apply(branch_summary_row_styler, axis=1),
                                hide_index=True,
                                use_container_width=True,
                                height=branch_dyn_height
                            )

                            # -------------------------------------------------------------------------
                            # ✅ Approve किए गए छात्रों का डेटा (Panel 3/4 से जिन्हें Approve किया गया है)
                            # -------------------------------------------------------------------------
                            st.divider()
                            st.markdown("### ✅ Approve किए गए छात्रों का डेटा")
                            st.caption("जिन छात्रों का 'गलत विषय' Nodal / Student / Principal द्वारा Approve किया जा चुका है, वो नीचे दिखेंगे — इन्हें अब गलत नहीं गिना जाएगा।")

                            _dash_key_col = find_student_key_col(df_to_show)
                            _approved_hits = []
                            for _pos, (_idx, _row) in enumerate(df_to_show.iterrows()):
                                _skey = get_student_key(_row, _pos, _dash_key_col)
                                _appr = get_approval(_skey, "pg" if _scope == "PG" else "ug")
                                if _appr:
                                    _approved_hits.append((_idx, _appr[0], _appr[1]))

                            if not _approved_hits:
                                st.info("इस डिग्री/ब्रांच में अभी तक कोई भी छात्र Approve नहीं हुआ है।")
                            else:
                                _approved_students_df = df_to_show.loc[[i for i, _, _ in _approved_hits]].copy()
                                _approved_students_df.insert(0, "✅ Approve किया (By)", [a[1] for a in _approved_hits])
                                _approved_students_df.insert(1, "🕒 Approve समय", [a[2] for a in _approved_hits])
                                st.dataframe(_approved_students_df, use_container_width=True, hide_index=True)
                                _dash_orientation = st.radio(
                                    "🖨️ प्रिंट ओरिएंटेशन चुनें:",
                                    options=["📄 Portrait (सीधा)", "📃 Landscape (आड़ा)"],
                                    horizontal=True,
                                    key=f"orientation_dash_{deg_info['display']}"
                                )
                                render_print_button(
                                    _approved_students_df,
                                    title=f"Approved Students List - {deg_info['display']}",
                                    key_suffix=f"dash_{deg_info['display']}".replace(" ", "_").replace(".", ""),
                                    orientation="landscape" if "Landscape" in _dash_orientation else "portrait"
                                )

            # =====================================================================
            # 📥 मास्टर एक्सेल डाउनलोड (P5 के सबसे नीचे) — ऊपर जितनी भी लिस्ट/डिग्री
            # बनी हैं (UG + PG दोनों), वो सब एक ही Excel फ़ाइल में 7 शीट के रूप में आ जाएँगी।
            # =====================================================================
            st.divider()
            st.markdown("### 📥 मास्टर एक्सेल डाउनलोड करें (7 शीट)")
            st.caption(
                "Sheet 1: मास्टर फ़ाइल का पूरा डेटा जस का तस  |  "
            "Sheet 2-3: UG/PG का पूरा रॉ डेटा (🔵 खाली | 🔴 गलत | 🟢 Approved)  |  "
            "Sheet 4: ब्रांच-वाइज विषय शीट (Total Admission + Minor/MDC/Voc/PW के नाम व संख्या)  |  "
            "Sheet 5: डिग्री+ब्रांच-वाइज समरी (Minor+MDC+Voc+PW सभी एक साथ)  |  "
            "Sheet 6: जिन छात्रों का कोई विषय गलत/खाली है, उनकी पूरी लिस्ट + कारण  |  "
            "Sheet 7: Sheet 6 में से जो पहले ही Approve हो चुके हैं, उनकी लिस्ट।"
            )

            _p5_sheet1_df, _p5_sheet1_name = load_master_data(), "Master_File"
            if _p5_sheet1_df is not None and not _p5_sheet1_df.empty:
                st.caption(f"📎 Sheet 1 में जाएगी: '{_p5_sheet1_name}' ({len(_p5_sheet1_df)} रोज़, मास्टर फ़ाइल)")
            else:
                st.caption("📎 Sheet 1 खाली रहेगी — मास्टर फ़ाइल में अभी कोई डेटा नहीं है।")

            _p5_ug_key_col = find_student_key_col(df_ug_all) if (df_ug_all is not None and not df_ug_all.empty) else None
            _p5_pg_key_col = find_student_key_col(df_pg_all) if (df_pg_all is not None and not df_pg_all.empty) else None
            _p5_ug_approved_keys = {a[0] for a in get_all_approvals("ug")}
            _p5_pg_approved_keys = {a[0] for a in get_all_approvals("pg")}

            _p5_master_sheets = []
            if df_ug_all is not None and not df_ug_all.empty:
                _p5_master_sheets.append({
                    "df": df_ug_all, "sheet_name": "UG_Master_List",
                    "deg_col": deg_col, "br_col": br_col, "minor_col": minor_col, "mdc_col": mdc_col,
                    "voc_col": voc_col, "pw_col": pw_col, "master_rules": ug_master_rules,
                    "approved_keys": _p5_ug_approved_keys, "key_col": _p5_ug_key_col, "prefix": "ug"
                })
            if df_pg_all is not None and not df_pg_all.empty:
                _p5_master_sheets.append({
                    "df": df_pg_all, "sheet_name": "PG_Master_List",
                    "deg_col": deg_col, "br_col": br_col, "minor_col": minor_col, "mdc_col": mdc_col,
                    "voc_col": voc_col, "pw_col": pw_col, "master_rules": None,
                    "approved_keys": _p5_pg_approved_keys, "key_col": _p5_pg_key_col, "prefix": "pg"
                })

            # ---------------------------------------------------------------------
            # 🧮 UG और PG — दोनों के लिए ब्रांच-वाइज विषय ब्लॉक्स, डिग्री+ब्रांच समरी,
            # Reason वाले छात्रों की लिस्ट और उनमें से Approve हो चुके छात्रों की लिस्ट निकालना
            # (यह वही logic है जो ऊपर 'भाग 1' में UG/PG टैब पर दिखता है, बस यहाँ पूरे स्कोप के लिए)
            # ---------------------------------------------------------------------
            def _p5_build_scope_summary(df_scope, scope_rules, prefix):
                if df_scope is None or df_scope.empty:
                    return [], pd.DataFrame(), pd.DataFrame(), {}, pd.DataFrame()

                _sdb = df_scope.copy()
                _skip_kw2 = ['minor', 'mdc', 'voc', 'skill', 'pw', 'project']
                _sdc = deg_col if (deg_col and deg_col in _sdb.columns) else next(
                    (c for c in _sdb.columns if any(k in str(c).lower() for k in ['deg', 'course', 'class'])), None)
                _sbc = br_col if (br_col and br_col in _sdb.columns and br_col != _sdc) else None
                if _sbc is None:
                    _sbc = next((c for c in _sdb.columns if c != _sdc and any(k in str(c).lower() for k in ['branch', 'stream'])), None)
                if _sbc is None:
                    _sbc = next((c for c in _sdb.columns if c != _sdc and 'subject' in str(c).lower()
                                and not any(k in str(c).lower() for k in _skip_kw2)), None)

                def _sclean_key(series):
                    s_ = series.astype(str).str.strip()
                    return s_.mask(series.isna() | (s_ == "") | (s_.str.lower() == "nan"), "(खाली/Blank)")

                _sdb["Degree (डिग्री)"] = _sclean_key(_sdb[_sdc]) if _sdc else "—"
                _sdb["Branch (ब्रांच)"] = _sclean_key(_sdb[_sbc]) if _sbc else "—"

                _all_cats2 = [("Minor", "minor", minor_col), ("MDC", "mdc", mdc_col), ("Voc", "voc", voc_col), ("PW", "pw", pw_col)]
                _present_cats2 = [(l_, k_, c_) for (l_, k_, c_) in _all_cats2 if c_ and c_ in _sdb.columns]

                _blocks2 = build_branch_subject_blocks(_sdb, "Degree (डिग्री)", "Branch (ब्रांच)", [(l_, c_) for l_, k_, c_ in _present_cats2])

                if not _present_cats2:
                    _summary2 = _sdb.groupby(["Degree (डिग्री)", "Branch (ब्रांच)"]).size().reset_index(name="कुल छात्र (Total)")
                    _summary2 = _summary2.sort_values(["Degree (डिग्री)", "कुल छात्र (Total)"], ascending=[True, False]).reset_index(drop=True)
                    _summary2 = pd.concat([_summary2, pd.DataFrame([{
                        "Degree (डिग्री)": "कुल योग (GRAND TOTAL)", "Branch (ब्रांच)": "",
                        "कुल छात्र (Total)": int(_summary2["कुल छात्र (Total)"].sum())}])], ignore_index=True)
                    return _blocks2, _summary2, pd.DataFrame(), {}, pd.DataFrame()

                if scope_rules is not None and len(_sdb):
                    _sdb["_rd"] = _sdb.apply(_row_degree_name, axis=1)
                else:
                    _sdb["_rd"] = None

                _ex_pairs2 = get_blank_exempt_pairs(prefix)
                _ex_s2 = pd.Series([(d_, b_) in _ex_pairs2 for d_, b_ in zip(_sdb["Degree (डिग्री)"], _sdb["Branch (ब्रांच)"])], index=_sdb.index)

                for _lbl, _rk, _cn in _present_cats2:
                    _empty_s2 = _sdb[_cn].isna() | (_sdb[_cn].astype(str).str.strip() == "")
                    _blank_s2 = _empty_s2 & ~_ex_s2
                    _norm_s2 = _sdb[_cn].astype(str).map(_norm_txt)
                    _wrong_s2 = pd.Series(False, index=_sdb.index)
                    if scope_rules is not None:
                        for _rd_name in _sdb["_rd"].dropna().unique():
                            _allowed2 = {_norm_txt(x) for x in ((scope_rules.get(_rd_name) or {}).get(_rk, []))}
                            if _allowed2:
                                _wrong_s2 = _wrong_s2 | ((_sdb["_rd"] == _rd_name) & ~_empty_s2 & ~_norm_s2.isin(_allowed2))
                    _sdb[f"_w_{_rk}"] = _wrong_s2
                    _sdb[f"_b_{_rk}"] = _blank_s2

                _first_rk2 = _present_cats2[0][1]
                _agg2 = {"_total": (f"_w_{_first_rk2}", "size")}
                for _lbl, _rk, _cn in _present_cats2:
                    _agg2[f"_w_{_rk}"] = (f"_w_{_rk}", "sum")
                    _agg2[f"_b_{_rk}"] = (f"_b_{_rk}", "sum")
                _grp2 = _sdb.groupby(["Degree (डिग्री)", "Branch (ब्रांच)"]).agg(**_agg2).reset_index()

                def _reason_for_group2(g):
                    lines = []
                    for _lbl, _rk, _cn in _present_cats2:
                        parts = []
                        w = g[g[f"_w_{_rk}"]]
                        if len(w):
                            for _rd_name, _wg in w.groupby("_rd"):
                                _vc = _wg[_cn].astype(str).str.strip().value_counts()
                                _subj = ", ".join(f"{k} ({v})" for k, v in _vc.items())
                                parts.append(f"🔴 {len(_wg)} छात्रों का विषय {_rd_name or 'इस डिग्री'} के मास्टर नियम में मान्य नहीं है → {_subj}")
                        _bn = int(g[f"_b_{_rk}"].sum())
                        if _bn:
                            parts.append(f"🔵 {_bn} छात्रों का खाली है (डेटा नहीं भरा गया)")
                        if parts:
                            lines.append(f"{_lbl}: " + " ; ".join(parts))
                    return "  ||  ".join(lines)

                _reasons2 = {}
                for (_d_k, _b_k), _g in _sdb.groupby(["Degree (डिग्री)", "Branch (ब्रांच)"]):
                    _reasons2[(_d_k, _b_k)] = _reason_for_group2(_g)

                _summary2 = _grp2[["Degree (डिग्री)", "Branch (ब्रांच)"]].copy()
                _summary2["कुल छात्र (Total)"] = _grp2["_total"].astype(int)
                for _lbl, _rk, _cn in _present_cats2:
                    _w_col2 = _grp2[f"_w_{_rk}"].astype(int)
                    _b_col2 = _grp2[f"_b_{_rk}"].astype(int)
                    _summary2[f"{_lbl} ✅ सही"] = _summary2["कुल छात्र (Total)"] - _w_col2 - _b_col2
                    _summary2[f"{_lbl} 🔴 गलत"] = _w_col2
                    _summary2[f"{_lbl} 🔵 खाली"] = _b_col2
                _summary2["📝 कारण (Reason)"] = [
                    _reasons2.get((_d_k, _b_k), "")
                    for _d_k, _b_k in zip(_grp2["Degree (डिग्री)"], _grp2["Branch (ब्रांच)"])
                ]
                _summary2 = _summary2.sort_values(["Degree (डिग्री)", "कुल छात्र (Total)"], ascending=[True, False]).reset_index(drop=True)
                _tot2 = {c_: "" for c_ in _summary2.columns}
                _tot2["Degree (डिग्री)"] = "कुल योग (GRAND TOTAL)"
                _tot2["Branch (ब्रांच)"] = ""
                for c_ in _summary2.columns:
                    if c_ not in ("Degree (डिग्री)", "Branch (ब्रांच)", "📝 कारण (Reason)"):
                        _tot2[c_] = int(_summary2[c_].sum())
                _summary2 = pd.concat([_summary2, pd.DataFrame([_tot2])], ignore_index=True)

                _any_flag2 = pd.Series(False, index=_sdb.index)
                for _lbl, _rk, _cn in _present_cats2:
                    _any_flag2 = _any_flag2 | _sdb[f"_w_{_rk}"] | _sdb[f"_b_{_rk}"]
                _stu2 = _sdb[_any_flag2].sort_values(["Degree (डिग्री)", "Branch (ब्रांच)"], kind="stable")
                _orig_cols2 = [c for c in df_scope.columns if c in _stu2.columns]

                def _stu_reason2(r):
                    out_ = []
                    for _lbl, _rk, _cn in _present_cats2:
                        if r[f"_w_{_rk}"]:
                            _rd_ = r["_rd"] if r["_rd"] else "इस डिग्री"
                            out_.append(f"🔴 {_lbl}: '{str(r[_cn]).strip()}' — {_rd_} के मास्टर नियम में मान्य नहीं")
                        elif r[f"_b_{_rk}"]:
                            out_.append(f"🔵 {_lbl}: खाली (डेटा नहीं भरा गया)")
                    return "\n".join(out_)

                _students_df2 = _stu2[_orig_cols2].copy().reset_index(drop=True)
                _students_df2.insert(0, "क्र.सं.", range(1, len(_students_df2) + 1))
                _reason_texts2 = [_stu_reason2(r_) for _, r_ in _stu2.iterrows()]
                _students_df2["📝 कारण (Reason)"] = _reason_texts2
                _student_flags2 = {}
                for _lbl, _rk, _cn in _present_cats2:
                    _student_flags2[_cn] = [
                        "w" if w_ else ("b" if b_ else "")
                        for w_, b_ in zip(_stu2[f"_w_{_rk}"].tolist(), _stu2[f"_b_{_rk}"].tolist())
                    ]

                # 🟢 Sheet 6 के लिए: इनमें से जो पहले ही Approve किए जा चुके हैं
                _dash_key_col2 = find_student_key_col(_sdb)
                _approved_hits2 = []
                for _pos, (_idx, _row) in enumerate(_stu2.iterrows()):
                    _skey2 = get_student_key(_row, _pos, _dash_key_col2)
                    _appr2 = get_approval(_skey2, prefix)
                    if _appr2:
                        _approved_hits2.append((_idx, _appr2[0], _appr2[1]))

                if _approved_hits2:
                    _hit_idx2 = [i for i, _, _ in _approved_hits2]
                    _approved_df2 = _stu2.loc[_hit_idx2][_orig_cols2].copy().reset_index(drop=True)
                    _approved_df2.insert(0, "✅ Approve किया (By)", [a[1] for a in _approved_hits2])
                    _approved_df2.insert(1, "🕒 Approve समय", [a[2] for a in _approved_hits2])
                    _approved_df2["📝 कारण (जो गलत/खाली था)"] = [_stu_reason2(r_) for _, r_ in _stu2.loc[_hit_idx2].iterrows()]
                else:
                    _approved_df2 = pd.DataFrame()

                return _blocks2, _summary2, _students_df2, _student_flags2, _approved_df2

            _p5_ug_blocks, _p5_ug_summary, _p5_ug_students, _p5_ug_flags, _p5_ug_approved = _p5_build_scope_summary(df_ug_all, ug_master_rules, "ug")
            _p5_pg_blocks, _p5_pg_summary, _p5_pg_students, _p5_pg_flags, _p5_pg_approved = _p5_build_scope_summary(df_pg_all, None, "pg")
            _p5_cat_labels = [l_ for l_, k_, c_ in [("Minor", "minor", minor_col), ("MDC", "mdc", mdc_col), ("Voc", "voc", voc_col), ("PW", "pw", pw_col)] if c_]

            if _p5_master_sheets or _p5_ug_blocks or _p5_pg_blocks:
                _p5_master_excel_bytes = generate_p5_master_full_excel(
                    _p5_master_sheets, _p5_cat_labels,
                    _p5_ug_blocks, _p5_pg_blocks,
                    _p5_ug_summary, _p5_pg_summary,
                    _p5_ug_students, _p5_ug_flags, _p5_ug_approved,
                    _p5_pg_students, _p5_pg_flags, _p5_pg_approved,
                    sheet1_df=_p5_sheet1_df, sheet1_name=_p5_sheet1_name
                )
                st.download_button(
                    label="📥 मास्टर एक्सेल डाउनलोड करें (7 शीट: अपलोड फ़ाइल, UG+PG लिस्ट, ब्रांच-वाइज विषय, समरी, Reason, Approved)",
                    data=_p5_master_excel_bytes,
                    file_name="P5_Master_Dashboard_Data.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="p5_master_excel_download_btn",
                    use_container_width=True
                )
            else:
                st.info("मास्टर एक्सेल के लिए फिलहाल कोई डेटा उपलब्ध नहीं है।")

    # =========================================================================
    # ⚙️ PANEL 6: ADMIN PANEL
    # =========================================================================
    elif active_panel == "⚙️ 6. Admin Panel":
        st.title("⚙️ Admin Panel - मास्टर डेटाबेस कंट्रोल")

        # =====================================================================
        # 🎨 लॉगिन स्क्रीन कस्टमाइज़ेशन (टाइटल + लोगो अपलोड)
        # =====================================================================
        if admin_section_toggle("login", "🎨 लॉगिन स्क्रीन कस्टमाइज़ करें", "यहाँ से आप लॉगिन पेज पर दिखने वाला टाइटल बदल सकते हैं, और इमोजी की जगह अपना खुद का लोगो अपलोड कर सकते हैं।"):

            logo_col, title_col = st.columns([1, 1.4])

            with logo_col:
                st.markdown("**🖼️ लोगो अपलोड करें**")
                _current_logo = get_app_setting("login_logo_b64")
                _current_mime = get_app_setting("login_logo_mime", "image/png")
                _current_w = int(get_app_setting("login_logo_width", "140"))
                _current_h = int(get_app_setting("login_logo_height", "140"))
                _current_fit = get_app_setting("login_logo_fit", "contain")
                if _current_logo:
                    st.image(f"data:{_current_mime};base64,{_current_logo}", caption="अभी का ओरिजिनल लोगो", width=160)
                else:
                    st.info("अभी कोई लोगो नहीं है — डिफ़ॉल्ट इमोजी (🎓🔒) दिख रहा है।")

                uploaded_logo = st.file_uploader("नया लोगो चुनें (PNG/JPG)", type=["png", "jpg", "jpeg", "webp"], key="logo_uploader")

                st.markdown("**📏 लोगो का साइज़ और फिट (पूरी पावर आपके हाथ में)**")
                wc1, wc2 = st.columns(2)
                with wc1:
                    new_logo_width = st.slider("चौड़ाई / Width (px)", min_value=30, max_value=400, value=_current_w, step=5, key="logo_width_slider")
                with wc2:
                    new_logo_height = st.slider("ऊंचाई / Height (px)", min_value=30, max_value=400, value=_current_h, step=5, key="logo_height_slider")

                new_logo_fit = st.radio(
                    "लोगो फिट मोड:",
                    options=["contain", "cover"],
                    index=(0 if _current_fit == "contain" else 1),
                    horizontal=True,
                    key="logo_fit_radio",
                    help="'contain' = पूरी image दिखेगी, कटेगी नहीं (चारों तरफ थोड़ी खाली जगह आ सकती है) | 'cover' = बॉक्स पूरा भरेगा, लेकिन extra हिस्सा क्रॉप हो सकता है"
                )
                st.caption("👉 अगर लोगो कट रहा है तो हमेशा **'contain'** मोड चुनें, और Width/Height को अपने लोगो के असली अनुपात (aspect ratio) के हिसाब से सेट करें।")

                if _current_logo:
                    _preview_html = (
                        f'<div style="text-align:center; background:#f6f8fb; border:1px dashed #c7d1e0; '
                    f'border-radius:10px; padding:14px;">'
                    f'<img src="data:{_current_mime};base64,{_current_logo}" '
                    f'style="width:{new_logo_width}px; height:{new_logo_height}px; object-fit:{new_logo_fit}; '
                    f'border-radius:10px; background:#fff;" /></div>'
                    )
                    st.markdown("**👁️ लाइव प्रिव्यू (Login स्क्रीन पर ऐसा दिखेगा):**")
                    st.markdown(_preview_html, unsafe_allow_html=True)

                if st.button("📏 साइज़ & फिट सेव करें", use_container_width=True, key="save_logo_size_btn"):
                    set_app_setting("login_logo_width", str(new_logo_width))
                    set_app_setting("login_logo_height", str(new_logo_height))
                    set_app_setting("login_logo_fit", new_logo_fit)
                    st.success(f"🎉 लोगो साइज़ ({new_logo_width}x{new_logo_height}px, {new_logo_fit}) सेव हो गया!")
                    st.rerun()

                lc1, lc2 = st.columns(2)
                with lc1:
                    if st.button("💾 लोगो सेव करें", use_container_width=True, disabled=(uploaded_logo is None), key="save_logo_btn"):
                        import base64 as _b64
                        logo_bytes = uploaded_logo.getvalue()
                        encoded = _b64.b64encode(logo_bytes).decode("utf-8")
                        set_app_setting("login_logo_b64", encoded)
                        set_app_setting("login_logo_mime", uploaded_logo.type or "image/png")
                        st.success("🎉 लोगो सफलतापूर्वक सेव हो गया!")
                        st.rerun()
                with lc2:
                    if st.button("🗑️ लोगो हटाएं (इमोजी दिखाएं)", use_container_width=True, disabled=(not _current_logo), key="danger_delete_logo_btn"):
                        delete_app_setting("login_logo_b64")
                        delete_app_setting("login_logo_mime")
                        st.success("लोगो हटा दिया गया, अब डिफ़ॉल्ट इमोजी दिखेगा।")
                        st.rerun()

            with title_col:
                st.markdown("**✏️ टाइटल और सबटाइटल एडिट करें**")
                _cur_title = get_app_setting("login_title", "NEP Master Data System")
                _cur_subtitle = get_app_setting("login_subtitle", "अपना पैनल चुनें और आगे बढ़ने के लिए पासवर्ड डालें")
                new_title_input = st.text_input("लॉगिन पेज का टाइटल", value=_cur_title, key="login_title_input")
                new_subtitle_input = st.text_input("लॉगिन पेज का सबटाइटल", value=_cur_subtitle, key="login_subtitle_input")
                if st.button("💾 टाइटल सेव करें", key="save_login_title_btn"):
                    set_app_setting("login_title", new_title_input.strip() or "NEP Master Data System")
                    set_app_setting("login_subtitle", new_subtitle_input.strip() or "अपना पैनल चुनें और आगे बढ़ने के लिए पासवर्ड डालें")
                    st.success("🎉 टाइटल सफलतापूर्वक अपडेट हो गया!")
                    st.rerun()

        st.divider()

        # =====================================================================
        # 🔑 पैनल पासवर्ड अपडेट सिस्टम (6 पैनल्स)
        # =====================================================================
        if admin_section_toggle("passwords", "🔑 पैनल पासवर्ड अपडेट करें", "यहाँ से आप किसी भी पैनल (P2-P6) का पासवर्ड बदल सकते हैं। बदलने के बाद उस पैनल में लॉगिन के लिए नया पासवर्ड इस्तेमाल होगा।"):

            pw_cols = st.columns(3)
            new_pw_inputs = {}
            for i, (pk, pname) in enumerate(PANEL_KEY_TO_NAME.items()):
                with pw_cols[i % 3]:
                    new_pw_inputs[pk] = st.text_input(f"{pname} का नया पासवर्ड", value="", type="password", key=f"pw_input_{pk}", placeholder="खाली छोड़ें तो नहीं बदलेगा")

            if st.button("🔐 पासवर्ड सेव करें", key="save_panel_passwords_btn"):
                updated_any = False
                for pk, new_pw in new_pw_inputs.items():
                    if new_pw.strip():
                        set_panel_password(pk, new_pw.strip())
                        updated_any = True
                if updated_any:
                    st.success("🎉 चुने गए पैनल्स के पासवर्ड सफलतापूर्वक अपडेट हो गए हैं!")
                else:
                    st.info("कोई नया पासवर्ड नहीं डाला गया, कुछ भी नहीं बदला।")

        st.divider()

        # =====================================================================
        # 👁️ पैनल हाइड / अनहाइड सिस्टम (P1 से P5 तक)
        # =====================================================================
        if admin_section_toggle("panelvis", "👁️ पैनल Hide / Unhide करें (P2 से P5)", "जिस पैनल को Hide करेंगे, उसमें सही पासवर्ड डालने पर भी डेटा नहीं दिखेगा (सिर्फ पैनल का ढांचा दिखेगा)। Unhide करने पर डेटा फिर से दिखने लगेगा।"):

            hide_cols = st.columns(4)
            hide_keys = ["p2", "p3", "p4", "p5"]
            new_hidden_state = {}
            for i, pk in enumerate(hide_keys):
                with hide_cols[i]:
                    current_hidden = is_panel_hidden(pk)
                    new_hidden_state[pk] = st.checkbox(f"🙈 {PANEL_KEY_TO_NAME[pk]} Hide करें", value=current_hidden, key=f"hide_chk_{pk}")

            if st.button("💾 Hide/Unhide सेटिंग सेव करें", key="save_hide_settings_btn"):
                for pk, hide_flag in new_hidden_state.items():
                    set_panel_hidden(pk, hide_flag)
                st.success("🎉 Hide/Unhide सेटिंग सफलतापूर्वक सेव हो गई है!")
                st.rerun()

        st.divider()

        if admin_section_toggle("backup", "📥 डेटाबेस बैकअप डाउनलोड करें", "🔵 नीला सेल = डेटा गायब है | 🔴 लाल सेल = गलत विषय (मास्टर गाइडलाइन से मिसमैच) | 🟢 हरा सेल = Approved (मान्य किया गया)"):
            df_ug_download = load_permanent_data("UG")
            df_pg_download = load_permanent_data("PG")

            # 🔒 UG मास्टर रूल्स लोड करना ताकि Admin की रंगीन डाउनलोड भी बाकी पैनल्स जैसी सही हो
            _admin_ug_rules = {}
            try:
                cursor.execute("SELECT rules_json FROM locked_rules WHERE panel_prefix = 'ug_master'")
                _locked_row = cursor.fetchone()
                if _locked_row and _locked_row[0]:
                    _admin_ug_rules = json.loads(_locked_row[0])
            except Exception:
                pass

            def _detect_cols(df):
                deg_c = next((c for c in df.columns if any(k in c.lower() for k in ['deg', 'course', 'class'])), df.columns[0] if len(df.columns) else None)
                br_c = next((c for c in df.columns if any(k in c.lower() for k in ['branch', 'stream', 'subject'])), None)
                min_c = next((c for c in df.columns if 'minor' in c.lower()), None)
                mdc_c = next((c for c in df.columns if 'mdc' in c.lower()), None)
                voc_c = next((c for c in df.columns if 'voc' in c.lower() or 'skill' in c.lower()), None)
                pw_c = next((c for c in df.columns if any(k in c.lower() for k in ['pw', 'project', 'ce'])), None)
                return deg_c, br_c, min_c, mdc_c, voc_c, pw_c

            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### 🎓 UG डेटा बैकअप")
                if df_ug_download is not None and not df_ug_download.empty:
                    st.download_button(
                        label="📥 UG डेटा CSV डाउनलोड करें (सादा)", 
                        data=df_ug_download.to_csv(index=False).encode('utf-8'), 
                        file_name="Approved_UG_Data_Backup.csv", 
                        mime="text/csv",
                        key="admin_ug_csv_dl"
                    )
                    deg_c, br_c, min_c, mdc_c, voc_c, pw_c = _detect_cols(df_ug_download)
                    _ug_key_col = find_student_key_col(df_ug_download)
                    _ug_approved_keys = {a[0] for a in get_all_approvals("ug")}
                    ug_colored = generate_colored_excel_bytes(
                        df_ug_download, deg_c, br_c, min_c, mdc_c, voc_c, pw_c,
                        master_rules=_admin_ug_rules, sheet_name="UG_Backup",
                        approved_keys=_ug_approved_keys, key_col=_ug_key_col, prefix="ug"
                    )
                    st.download_button(
                        label="📥 रंगीन (🔴/🔵) UG डेटा एक्सेल डाउनलोड करें",
                        data=ug_colored,
                        file_name="Approved_UG_Colored_Backup.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="admin_ug_colored_dl"
                    )
                else: 
                    st.info("UG डेटाबेस खाली है।")
            
            with c2:
                st.markdown("#### 📜 PG डेटा बैकअप")
                if df_pg_download is not None and not df_pg_download.empty:
                    st.download_button(
                        label="📥 PG डेटा CSV डाउनलोड करें (सादा)", 
                        data=df_pg_download.to_csv(index=False).encode('utf-8'), 
                        file_name="Approved_PG_Data_Backup.csv", 
                        mime="text/csv",
                        key="admin_pg_csv_dl"
                    )
                    deg_c, br_c, min_c, mdc_c, voc_c, pw_c = _detect_cols(df_pg_download)
                    _pg_key_col = find_student_key_col(df_pg_download)
                    _pg_approved_keys = {a[0] for a in get_all_approvals("pg")}
                    pg_colored = generate_colored_excel_bytes(
                        df_pg_download, deg_c, br_c, min_c, mdc_c, voc_c, pw_c,
                        master_rules=None, sheet_name="PG_Backup",
                        approved_keys=_pg_approved_keys, key_col=_pg_key_col, prefix="pg"
                    )
                    st.download_button(
                        label="📥 रंगीन (🔵) PG डेटा एक्सेल डाउनलोड करें",
                        data=pg_colored,
                        file_name="Approved_PG_Colored_Backup.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="admin_pg_colored_dl",
                        help="PG के लिए फिलहाल कोई मास्टर सब्जेक्ट नियम सेट नहीं है, इसलिए सिर्फ खाली सेल नीले दिखेंगे।"
                    )
                else: 
                    st.info("PG डेटाबेस खाली है।")

        st.divider()
        if admin_section_toggle("danger", "🚨 डेंजर ज़ोन", None):
            confirm_reset = st.checkbox("मैं पूरे सिस्टम (रॉ + अप्रूव्ड दोनों डेटाबेस) को रीसेट करने की पुष्टि करता हूँ।")
            also_delete_rules = st.checkbox("⚠️ लॉक किए गए सब्जेक्ट नियम (Minor/MDC/Voc/PW रूल्स) भी डिलीट करें (सामान्यतः इसे टिक न करें)")
            if st.button("💥 ऑल डेटाबेस रीसेट करें", key="danger_reset_all_btn"):
                if confirm_reset:
                    cursor.execute("DELETE FROM raw_store")
                    cursor.execute("DELETE FROM perma_store")
                    # 🔧 फिक्स: locked_rules अब डिफ़ॉल्ट रूप से डिलीट नहीं होगा, ताकि लॉक किए गए सब्जेक्ट नियम
                    # नई फ़ाइल अपलोड करने के बाद भी सुरक्षित बने रहें
                    if also_delete_rules:
                        cursor.execute("DELETE FROM locked_rules")
                    conn.commit()
                    st.session_state["deleted_cols"] = []
                    if also_delete_rules:
                        st.success("सिस्टम पूरी तरह से रीसेट हो गया है (डेटा + लॉक किए गए नियम दोनों हट गए)!")
                    else:
                        st.success("डेटा रीसेट हो गया है! लॉक किए गए सब्जेक्ट नियम सुरक्षित रखे गए हैं।")
                    st.rerun()
                else: 
                    st.error("कृपया पहले पुष्टि चेकबॉक्स पर टिक करें।")

    # =========================================================================
    # 🏁 फुटर (हर पेज के नीचे प्रोफेशनल क्रेडिट लाइन)
    # =========================================================================
    render_footer()


# ==========================================================
# 📁 स्टेप 2: डेटा सहेजने और लोड करने वाले कोर फंक्शन्स
# ==========================================================

# 🟢 नया यूटिलिटी फंक्शन: Student Name / Father Name / Mother Name जैसे नाम वाले
# कॉलम्स को हमेशा "Riya Sharma" जैसे Proper Case (हर शब्द का पहला अक्षर Capital) में
# दिखाने के लिए। यह load_live_data और load_stage_data दोनों में लगाया गया है, इसलिए
# चाहे कोई भी बड़े/छोटे अक्षरों में डेटा अपलोड/एंटर करे, हर पैनल में (स्क्रीन पर देखने से
# लेकर प्रिंट तक) यह हमेशा Proper Case में ही दिखेगा — क्योंकि सभी पैनल इसी live_db से डेटा लेते हैं।
NAME_CASE_COLUMNS = ["Student Name", "Father Name", "Mother Name"]

def to_proper_name_case(name_val):
    s = str(name_val).strip()
    if not s or s.lower() == "nan":
        return s
    return " ".join(word.capitalize() for word in s.split(" "))

def apply_name_proper_case(df):
    for name_col in NAME_CASE_COLUMNS:
        if name_col in df.columns:
            df[name_col] = df[name_col].apply(to_proper_name_case)
    return df

# 🆕 P2 Matrix Filter (Box 2): "Eligibility Name" column ke text se pehchanta hai
# ki record Under Graduate hai ya Post Graduate.
# - "After 12th / HSC / 10+2 / XII" jaisa likha ho (B.A., B.Com., B.Sc. jaisi degree
#   ke liye eligibility) → Under Graduate
# - "After Graduation" jaisa likha ho (M.A., M.Com., M.Sc. jaisi degree ke liye
#   eligibility) → Post Graduate
def classify_ug_pg(eligibility_val):
    s = str(eligibility_val).strip().upper()
    if not s or s == "NAN":
        return ""
    if "UNDER GRADUATE" in s or "UNDERGRADUATE" in s:
        return "Under Graduate"
    if "POST GRADUATE" in s or "POSTGRADUATE" in s:
        return "Post Graduate"
    if "12TH" in s or "HSC" in s or "10+2" in s or "XII" in s or "INTERMEDIATE" in s:
        return "Under Graduate"
    if "GRADUATION" in s or "GRADUATE" in s:
        return "Post Graduate"
    return "Other"

def load_pre_login_config():
    return _load_pre_login_config_cached()

@st.cache_data(show_spinner=False)
def _load_pre_login_config_cached():
    if os.path.exists(PRE_LOGIN_CONFIG_FILE):
        try:
            with open(PRE_LOGIN_CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict): return data
        except: return DEFAULT_PRE_LOGIN_CONFIG.copy()
    return DEFAULT_PRE_LOGIN_CONFIG.copy()

def save_pre_login_config(config_dict):
    with open(PRE_LOGIN_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config_dict, f, ensure_ascii=False, indent=4)
    _load_pre_login_config_cached.clear()

# 🟢 P12 SYLLABUS MANAGER: har Subject + Year ke combination ke liye File-upload YA
# Link — dono me se koi bhi ek tarika chuna ja sakta hai. Data yahan nested format me
# save hota hai: { Subject: { Year: {"type","value","file_name"} } }
def load_syllabus_data():
    return _load_syllabus_data_cached()

@st.cache_data(show_spinner=False)
def _load_syllabus_data_cached():
    if os.path.exists(SYLLABUS_FILE):
        try:
            with open(SYLLABUS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict): return data
        except: return {}
    return {}

def save_syllabus_data(data_dict):
    with open(SYLLABUS_FILE, "w", encoding="utf-8") as f:
        json.dump(data_dict, f, ensure_ascii=False, indent=4)
    _load_syllabus_data_cached.clear()

# 🟢 FIX: Ab har Subject ke liye utne hi Years dikhenge jitni uski asli "Duration"
# (jaise 3 saal ka course ho to sirf 1st/2nd/3rd Year hi dikhega, 4th/5th/6th nahi) —
# Duration wahi column hai jo already "Current Year" auto-calculate karne me use hoti hai.
def get_subject_syllabus_year_count(subject_name, df):
    try:
        if "Duration" not in df.columns or "Subject" not in df.columns:
            return len(SYLLABUS_YEAR_OPTIONS)
        sub_rows = df[df["Subject"].astype(str).str.strip() == str(subject_name).strip()]
        durations = pd.to_numeric(sub_rows["Duration"], errors="coerce").dropna()
        if durations.empty:
            return len(SYLLABUS_YEAR_OPTIONS)
        # Us Subject ke jitne bhi students hain, unme sabse zyada baar aaya Duration
        # lete hain — taaki kisi ek galat/typo entry se poori list na bigde
        mode_vals = durations.mode()
        chosen = int(mode_vals.iloc[0]) if not mode_vals.empty else int(durations.iloc[0])
        chosen = max(1, chosen)
        return min(chosen, len(SYLLABUS_YEAR_OPTIONS))
    except Exception:
        return len(SYLLABUS_YEAR_OPTIONS)

def load_dynamic_lists():
    return _load_dynamic_lists_cached()

@st.cache_data(show_spinner=False)
def _load_dynamic_lists_cached():
    if os.path.exists(DYNAMIC_LISTS_FILE):
        try:
            with open(DYNAMIC_LISTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and "file_types" in data and "academic_years" in data and "academic_sessions" in data:
                    return data
        except: return DEFAULT_DYNAMIC_LISTS.copy()
    return DEFAULT_DYNAMIC_LISTS.copy()

def save_dynamic_lists(lists_dict):
    with open(DYNAMIC_LISTS_FILE, "w", encoding="utf-8") as f:
        json.dump(lists_dict, f, ensure_ascii=False, indent=4)
    _load_dynamic_lists_cached.clear()

@st.cache_data(show_spinner=False)
def load_credentials():
    if os.path.exists(CRED_FILE):
        try:
            with open(CRED_FILE, "r") as f: return json.load(f)
        except: return DEFAULT_CREDENTIALS.copy()
    else:
        with open(CRED_FILE, "w") as f: json.dump(DEFAULT_CREDENTIALS, f)
        return DEFAULT_CREDENTIALS.copy()

def load_panel_names():
    return _load_panel_names_cached()

@st.cache_data(show_spinner=False)
def _load_panel_names_cached():
    if os.path.exists(PANEL_NAME_FILE):
        try:
            with open(PANEL_NAME_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: return DEFAULT_PANELS.copy()
    return DEFAULT_PANELS.copy()

def save_panel_names(panel_dict):
    with open(PANEL_NAME_FILE, "w", encoding="utf-8") as f:
        json.dump(panel_dict, f, ensure_ascii=False, indent=4)
    _load_panel_names_cached.clear()

@st.cache_data(show_spinner=False)
def load_column_mappings():
    if os.path.exists(MAP_FILE):
        try:
            with open(MAP_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: return {}
    return {}

def load_notice_board():
    return _load_notice_board_cached()

@st.cache_data(show_spinner=False)
def _load_notice_board_cached():
    if os.path.exists(NOTICE_FILE):
        try:
            with open(NOTICE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("notice_text", DEFAULT_NOTICE)
        except: return DEFAULT_NOTICE
    return DEFAULT_NOTICE

def save_notice_board(text):
    with open(NOTICE_FILE, "w", encoding="utf-8") as f:
        json.dump({"notice_text": text}, f, ensure_ascii=False, indent=4)
    _load_notice_board_cached.clear()

# 🟢 NOTICE BOARD LINK FEATURE:
# Agar Notice me admin koi link (http://..., https://..., ya www....) type karta hai,
# to use is function se pehle HTML-escape karke, phir us link ko clickable <a> tag me
# badal dete hain — jisse user Notice Board par us link par touch/click karke seedhe
# us page par pahunch jaaye (naya tab me khulega, taaki Notice Board wala tab band na ho).
_NOTICE_URL_PATTERN = _re_notice_link.compile(
    r'((?:https?://|www\.)[^\s<>\"\']+)', _re_notice_link.IGNORECASE
)

def linkify_notice_line(line_text):
    """Ek line ke andar jitne bhi URL (http/https/www) mile, unhe safe clickable <a> tag me convert karta hai.
    Baaki normal text HTML-escape karke as-is rakha jaata hai (taaki koi bhi galti se HTML/script
    likh de to bhi wo tootn na paaye)."""
    escaped = _html_escape_lib.escape(line_text)

    def _make_link(match):
        raw_url = match.group(1)
        # Trailing punctuation (., ,, ), आदि) ko link ke bahar rakho taaki link kharab na ho
        trailing = ""
        while raw_url and raw_url[-1] in ".,);:!?\u0964":
            trailing = raw_url[-1] + trailing
            raw_url = raw_url[:-1]
        href = raw_url if raw_url.lower().startswith("http") else "https://" + raw_url
        return (
            f'<a href="{href}" target="_blank" rel="noopener noreferrer" '
            f'style="color:#0F2A4A; text-decoration:underline; font-weight:600;">{raw_url}</a>{trailing}'
        )

    return _NOTICE_URL_PATTERN.sub(_make_link, escaped)

# 🆕 P11 डायनेमिक कॉलम मैपिंग लोडर फंक्शन
def load_twin_mappings():
    return _load_twin_mappings_cached()

@st.cache_data(show_spinner=False)
def _load_twin_mappings_cached():
    # 🔒 पहले सेव्ड JSON फ़ाइल से मैपिंग्स उठाओ (अगर मौजूद हो)
    if os.path.exists(TWIN_MAP_FILE):
        try:
            with open(TWIN_MAP_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
        except:
            loaded = {}
    else:
        loaded = {}

    # 🔒 PERMANENT FIX: चाहे JSON फ़ाइल खाली हो, डिलीट हो जाए या corrupt हो जाए,
    # ये 2 डिफ़ॉल्ट मैपिंग हमेशा जबरदस्ती (force) लागू रहेंगी — इन्हें कभी भी
    # ओवरराइट/डिलीट नहीं किया जा सकता, ताकि सिस्टम रीस्टार्ट/रीडिप्लॉय के बाद भी
    # यह कनेक्शन हमेशा जुड़ा हुआ मिले।
    merged = dict(loaded)
    merged.update(PERMANENT_TWIN_MAPPINGS)
    return merged

# 🆕 P11 डायनेमिक कॉलम मैपिंग सेवर फंक्शन
def save_twin_mappings(mapping_dict):
    with open(TWIN_MAP_FILE, "w", encoding="utf-8") as f:
        json.dump(mapping_dict, f, ensure_ascii=False, indent=4)
    _load_twin_mappings_cached.clear()

def load_live_data():
    return _load_live_data_cached().copy()

@st.cache_data(show_spinner=False)
def _load_live_data_cached():
    if not os.path.exists(DB_FILE) or os.path.getsize(DB_FILE) == 0:
        df_empty = pd.DataFrame(columns=DEFAULT_COLUMNS)
        df_empty.to_csv(DB_FILE, index=False)
        return df_empty
    try:
        df = pd.read_csv(DB_FILE, dtype=str)
        # 🧹 Purane test-version ke bache hue columns ("Sent To P15" / "P21 Saved") database se hamesha ke liye hatao
        _stale_cols = [c for c in ("Sent To P15", "P21 Saved") if c in df.columns]
        if _stale_cols:
            df = df.drop(columns=_stale_cols)
            df.to_csv(DB_FILE, index=False)
        for col in DEFAULT_COLUMNS:
            if col not in df.columns: df[col] = ""
        df = df.fillna("").reset_index(drop=True)
        df = apply_name_proper_case(df)
        
        # 🔄 P11 डायनेमिक लोड-टाइम सिंक इंजन (Twin Sync)
        twin_maps = load_twin_mappings()
        for source_col, target_col in twin_maps.items():
            if source_col in df.columns and target_col in df.columns:
                # दोनों तरफ से डेटा अलाइन करें ताकि किसी भी पैनल को खाली डेटा न दिखे
                mask1 = (df[source_col].astype(str).str.strip() != "") & (df[target_col].astype(str).str.strip() == "")
                df.loc[mask1, target_col] = df.loc[mask1, source_col]
                
                mask2 = (df[target_col].astype(str).str.strip() != "") & (df[source_col].astype(str).str.strip() == "")
                df.loc[mask2, source_col] = df.loc[mask2, target_col]
        return df
    except:
        return pd.DataFrame(columns=DEFAULT_COLUMNS)

def save_live_data(df_to_save):
    if df_to_save.empty:
        df_to_save.fillna("").astype(str).to_csv(DB_FILE, index=False)
        _load_live_data_cached.clear()
        return

    df_temp = df_to_save.copy()
    
    # 🔄 P11 डायनेमिक सेव-टाइम सिंक इंजन (Twin Sync)
    twin_maps = load_twin_mappings()
    for source_col, target_col in twin_maps.items():
        if source_col in df_temp.columns and target_col in df_temp.columns:
            # ⚡ पहले हर row पर iterrows() loop चलता था (धीमा); अब वही नियम पूरे कॉलम पर एक साथ
            _s = df_temp[source_col].astype(str).str.strip()
            _t = df_temp[target_col].astype(str).str.strip()
            _m_tgt = (_s != "") & (_s != _t)      # source भरा है और target खाली/अलग -> target = source
            _m_src = (_t != "") & (_s == "")      # source खाली, target भरा -> source = target
            df_temp.loc[_m_tgt, target_col] = _s[_m_tgt]
            df_temp.loc[_m_src, source_col] = _t[_m_src]

    # 🛑 नो न्यू कॉलम पॉलिसी: केवल ओरिजिनल DEFAULT_COLUMNS ही सीएसवी फ़ाइल में सेव होंगे
    final_cols_to_save = [col for col in DEFAULT_COLUMNS if col in df_temp.columns]
    df_temp[final_cols_to_save].fillna("").astype(str).to_csv(DB_FILE, index=False)
    _load_live_data_cached.clear()

def load_stage_data():
    return _load_stage_data_cached().copy()

@st.cache_data(show_spinner=False)
def _load_stage_data_cached():
    if not os.path.exists(STAGE_FILE) or os.path.getsize(STAGE_FILE) == 0:
        return pd.DataFrame(columns=DEFAULT_COLUMNS + ["Uploaded File Name"])
    try:
        df = pd.read_csv(STAGE_FILE, dtype=str)
        df = df.fillna("").reset_index(drop=True)
        df = apply_name_proper_case(df)

        # 🟢 सेफ्टी-नेट फिक्स: पुराने मैनुअल एंट्री बग की वजह से कुछ पेंडिंग रिकॉर्ड्स में
        # "Date Of Birth" / "Email" / "Enrollment No" जैसे गलत-नाम वाले कॉलम बन गए होंगे।
        # यहाँ उनका डेटा सही स्कीमा कॉलम ("Date of Birth" / "Email ID" / "Enrollment No.") में
        # कॉपी करके गलत कॉलम हटा दिया जाता है, ताकि कोई डेटा गुम न हो।
        legacy_fix_map = {"Date Of Birth": "Date of Birth", "Email": "Email ID", "Enrollment No": "Enrollment No."}
        for bad_col, good_col in legacy_fix_map.items():
            if bad_col in df.columns:
                if good_col not in df.columns:
                    df[good_col] = ""
                mask = (df[good_col].astype(str).str.strip() == "") & (df[bad_col].astype(str).str.strip() != "")
                df.loc[mask, good_col] = df.loc[mask, bad_col]
                df = df.drop(columns=[bad_col])

        return df.reset_index(drop=True)
    except:
        return pd.DataFrame(columns=DEFAULT_COLUMNS + ["Uploaded File Name"])

def save_stage_data(df_to_save):
    df_to_save.fillna("").astype(str).to_csv(STAGE_FILE, index=False)
    _load_stage_data_cached.clear()

@st.cache_data(show_spinner=False)
def get_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as image_file:
            return f"data:image/png;base64,{base64.b64encode(image_file.read()).decode()}"
    return ""

# ==========================================================
# 🧠 स्टेप 3: सेशन स्टेट वेरिएबल्स इनिशियलाइज़ेशन
# ==========================================================
if "pre_login_config" not in st.session_state or not isinstance(st.session_state.pre_login_config, dict):
    st.session_state.pre_login_config = load_pre_login_config()

if "dynamic_lists" not in st.session_state:
    st.session_state.dynamic_lists = load_dynamic_lists()

if "p1_dropdown_schemas" not in st.session_state:
    st.session_state.p1_dropdown_schemas = {
        "file_types": [
            "admission file", "admission fee file", "unique id file", 
            "roll no file", "enrollment file", "promotion file", "result file"
        ],
        "academic_years": [str(year) for year in range(2014, 2027)],
        "academic_sessions": [f"{year}-{str(year+1)[2:]}" for year in range(2014, 2027)]
    }

if "credentials" not in st.session_state or len(st.session_state.credentials) < 14:
    st.session_state.credentials = load_credentials()

if "column_mappings" not in st.session_state: 
    st.session_state.column_mappings = load_column_mappings()

if "panel_names" not in st.session_state or len(st.session_state.panel_names) < 15:
    st.session_state.panel_names = load_panel_names()

if "notice_text" not in st.session_state:
    st.session_state.notice_text = load_notice_board()

if "user_role" not in st.session_state: st.session_state.user_role = None  
if "logged_username" not in st.session_state: st.session_state.logged_username = None
if "show_login_form" not in st.session_state: st.session_state.show_login_form = False
if "admin_columns_order" not in st.session_state: st.session_state.admin_columns_order = DEFAULT_COLUMNS.copy()
if "admin_lock_state" not in st.session_state: st.session_state.admin_lock_state = True
if "admin_unhide_edit" not in st.session_state: st.session_state.admin_unhide_edit = False
if "admin_unhide_move" not in st.session_state: st.session_state.admin_unhide_move = False
if "admin_hide_master_data" not in st.session_state: st.session_state.admin_hide_master_data = False
if "cce_foil_generated" not in st.session_state: st.session_state.cce_foil_generated = False
if "p10_reg_list_generated" not in st.session_state: st.session_state.p10_reg_list_generated = False

# 🆕 फ़ाइल अपलोडर को खाली करने के लिए काउंटर (P1 ऑटो-क्लियर मैकेनिज्म हेतु)
if "uploader_key_counter" not in st.session_state:
    st.session_state.uploader_key_counter = 0

for k in DEFAULT_PANELS.keys():
    if f"hide_panel_{k}" not in st.session_state: st.session_state[f"hide_panel_{k}"] = False

# ==========================================================
# 🧠 स्टेप 3.5: मास्टर रिपॉजिटरी लोड और ऑटो-ईयर कैलकुलेशन इंजन (Duration Based)
# ==========================================================
import numpy as _np_fast

def _vectorized_current_year(df, highest_admission_year):
    """calculate_current_academic_year जैसा ही नियम, पर पूरे DataFrame पर एक साथ (row-by-row apply से कई गुना तेज़)।"""
    n = len(df)
    empty = pd.Series([""] * n, index=df.index)
    dur_s = df["Duration"].astype(str).str.strip() if "Duration" in df.columns else empty
    adm_s = df["Admission Year"].astype(str).str.strip() if "Admission Year" in df.columns else empty
    dur = pd.to_numeric(dur_s, errors="coerce")
    adm = pd.to_numeric(adm_s, errors="coerce")
    bad = (dur_s.eq("") | dur_s.str.lower().eq("nan") | dur_s.eq("0")
           | ~_np_fast.isfinite(dur) | ~_np_fast.isfinite(adm))
    dur_i = _np_fast.trunc(dur.where(~bad, 0))
    adm_i = _np_fast.trunc(adm.where(~bad, 0))
    diff = highest_admission_year - adm_i
    ordinals = {0: "1st Year", 1: "2nd Year", 2: "3rd Year", 3: "4th Year", 4: "5th Year", 5: "6th Year"}
    lbl = diff.map(ordinals)
    lbl = lbl.where(lbl.notna(), (diff + 1).astype("int64").astype(str) + "th Year")
    status = df["Status"].astype(str).str.strip().str.upper() if "Status" in df.columns else empty
    after = _np_fast.where(status.eq("EX-STUDENT"), "EX-STUDENT", "Passout").astype(object)
    inside = (diff >= 0) & (diff < dur_i)
    res = _np_fast.select(
        [bad.to_numpy(), inside.to_numpy(), (diff >= dur_i).to_numpy()],
        [_np_fast.full(n, "plz Fill the Duretion", dtype=object), lbl.to_numpy(dtype=object), after],
        default="1st Year")
    return pd.Series(res, index=df.index)

# 1. डेटाबेस से मूल डेटा लोड करें
live_db = load_live_data()

# 2. कोर्स Duration के आधार पर लाइव ऑटोमैटिक ईयर कैलकुलेशन इंजन
if not live_db.empty and "Admission Year" in live_db.columns:
    try:
        # एडमिशन ईयर कॉलम से सबसे हाईएस्ट (लेटेस्ट) साल ढूंढें
        valid_years = pd.to_numeric(live_db["Admission Year"], errors='coerce').dropna()
        if not valid_years.empty:
            highest_admission_year = int(valid_years.max())
            
            # प्रत्येक रो के लिए लाइव एडमिशन ईयर और कोर्स Duration के आधार पर कैलकुलेट करें
            def calculate_current_academic_year(row):
                try:
                    row_admission_year = row.get("Admission Year", "")
                    student_status = str(row.get("Status", "")).strip().upper()
                    
                    # Duration कॉलम का मान निकालें और स्पेस साफ़ करें
                    duration_val = str(row.get("Duration", "")).strip()
                    
                    # 🚨 नियम: यदि Duration कॉलम खाली है, nan है, तो सीधे अलर्ट दिखाएँ
                    if not duration_val or duration_val == "" or duration_val.lower() == "nan" or duration_val == "0":
                        return "plz Fill the Duretion"
                    
                    max_duration = int(float(duration_val))
                    adm_yr = int(float(row_admission_year))
                    year_diff = highest_admission_year - adm_yr
                    
                    # यदि अंतर कोर्स की अवधि के अंदर है (जैसे 1st Year से 6th Year तक)
                    if 0 <= year_diff < max_duration:
                        if year_diff == 0: return "1st Year"
                        elif year_diff == 1: return "2nd Year"
                        elif year_diff == 2: return "3rd Year"
                        elif year_diff == 3: return "4th Year"
                        elif year_diff == 4: return "5th Year"
                        elif year_diff == 5: return "6th Year"
                        else: return f"{year_diff + 1}th Year"
                    
                    # यदि अंतर कोर्स की अवधि के बराबर या उससे ज़्यादा हो चुका है
                    elif year_diff >= max_duration:
                        if student_status == "EX-STUDENT":
                            return "EX-STUDENT"
                        else:
                            return "Passout"
                    else:
                        return "1st Year"
                except:
                    return "plz Fill the Duretion"
            
            # पूरे डेटाबेस ग्रिड को लाइव अपडेट करें
            # ⚡ पहले हर row पर Python function चलता था (धीमा) — अब वही नियम vectorized (पूरे कॉलम पर एक साथ) चलते हैं
            live_db["Current Year"] = _vectorized_current_year(live_db, highest_admission_year)
            if "Year" in live_db.columns:
                live_db["Year"] = live_db["Current Year"]
                
    except Exception as auto_yr_err:
        st.error(f"करंट ईयर ऑटो-कैलकुलेशन इंजन में तकनीकी समस्या: {auto_yr_err}")

# पी12 और कॉलम मैपिंग के लिए यूटिलिटी फ़ंक्शंस
def get_display_name(internal_col_name):
    return st.session_state.column_mappings.get(internal_col_name, internal_col_name)

def get_panel_title(panel_id):
    return st.session_state.panel_names.get(panel_id, DEFAULT_PANELS[panel_id])

# ==========================================================
# 🔎 P15 इनलाइन-फ़िल्टर टेबल: हेडर-रो और पहली डेटा-रो के ठीक बीच में हर कॉलम का सर्च बॉक्स
#    (Streamlit की st.dataframe में यह सुविधा नहीं है, इसलिए यह एक हल्की HTML/JS टेबल है।
#     फ़िल्टर ब्राउज़र में ही चलता है — टाइप करते ही लाइव, पेज रीलोड/रीरन नहीं होता।)
#    - कई कॉलम में एक साथ टेक्स्ट भरें तो सभी शर्तें साथ (AND) लागू होती हैं (Contains, केस-इनसेंसिटिव)
#    - हेडर पर क्लिक करने से Sort (▲/▼); हेडर और सर्च-रो स्क्रॉल करने पर ऊपर चिपकी रहती हैं
# ==========================================================
_INLINE_FILTER_TABLE_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
*{box-sizing:border-box}
html,body{margin:0;padding:0;background:transparent}
body{font-family:"Source Sans Pro","Segoe UI","Noto Sans Devanagari","Nirmala UI",Arial,sans-serif;font-size:14px;color:#31333f}
#bar{display:flex;justify-content:space-between;align-items:center;min-height:28px;padding:0 2px 4px;font-size:13px;color:#555}
#clr{display:none;border:1px solid #d0d4dc;background:#fff;border-radius:6px;padding:3px 10px;font-size:12px;cursor:pointer;color:#31333f}
#clr:hover{background:#f0f2f6}
#wrap{border:1px solid #e6e9ef;border-radius:8px;overflow:auto;height:__HEIGHT__px;background:#fff;box-shadow:0 1px 4px rgba(0,0,0,.08)}
table{border-collapse:separate;border-spacing:0;table-layout:fixed;min-width:100%}
th,td{padding:0 10px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;border-bottom:1px solid #eceef3;border-right:1px solid #f1f2f6;text-align:left}
td{height:35px;line-height:20px}
td.n{text-align:right;color:#31333f}
thead th{position:sticky;background:#f7f8fb;z-index:2}
thead tr.h th{top:0;height:36px;font-weight:400;color:#6b7080;cursor:pointer;user-select:none}
thead tr.h th:hover{background:#eef0f6}
thead tr.f th{top:36px;height:40px;padding:4px 5px;background:#fff;cursor:default}
thead tr.f input{width:100%;height:30px;border:1px solid transparent;background:#f0f2f6;border-radius:6px;padding:0 8px;font-size:13px;font-family:inherit;color:#31333f;outline:none}
thead tr.f input:focus{border-color:#ff4b4b;background:#fff}
.ar{font-style:normal;font-size:10px;color:#ff4b4b}
tbody tr:hover td{background:#f7f9fc}
</style></head>
<body>
<div id="bar"><span id="cnt"></span><button id="clr" type="button">🧹 सर्च साफ़ करें</button></div>
<div id="wrap"><table id="tbl"><colgroup id="cg"></colgroup><thead id="thead"></thead><tbody id="tbody"></tbody></table></div>
<script>
(function(){
var D = __DATA__;
var H = D.headers, R = D.rows, W = D.widths;
var N = R.length, C = H.length;
var RH = 35, BUF = 10, HEAD_H = 36, FILT_H = 40;
var wrap = document.getElementById('wrap');
var thead = document.getElementById('thead');
var tbody = document.getElementById('tbody');
var cnt = document.getElementById('cnt');
var clr = document.getElementById('clr');
var filters = []; for (var z = 0; z < C; z++) filters.push('');
var sortCol = -1, sortDir = 1, view = [], timer = null, ticking = false;

function esc(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }

var cg = '<col style="width:64px">', total_w = 64;
for (var w = 0; w < C; w++) { cg += '<col style="width:' + W[w] + 'px">'; total_w += W[w]; }
document.getElementById('cg').innerHTML = cg;
document.getElementById('tbl').style.width = total_w + 'px';

var h1 = '<tr class="h"><th>S.No.</th>', h2 = '<tr class="f"><th></th>';
for (var i = 0; i < C; i++) {
  h1 += '<th data-c="' + i + '" title="' + esc(H[i]) + '"><span>' + esc(H[i]) + '</span><i class="ar"></i></th>';
  h2 += '<th><input type="text" data-c="' + i + '" placeholder="🔎 खोजें..." autocomplete="off"></th>';
}
thead.innerHTML = h1 + '</tr>' + h2 + '</tr>';

function cmp(x, y){
  var nx = Number(x), ny = Number(y);
  if (x.trim() !== '' && y.trim() !== '' && isFinite(nx) && isFinite(ny)) return nx - ny;
  return x.localeCompare(y, undefined, {numeric: true, sensitivity: 'base'});
}

function updateArrows(){
  var ths = thead.querySelectorAll('tr.h th[data-c]');
  for (var k = 0; k < ths.length; k++) {
    var c = +ths[k].getAttribute('data-c');
    ths[k].querySelector('.ar').textContent = (c === sortCol) ? (sortDir === 1 ? ' ▲' : ' ▼') : '';
  }
}

function render(){
  var total = view.length, top = wrap.scrollTop, ch = wrap.clientHeight, hh = HEAD_H + FILT_H;
  var s = Math.max(0, Math.floor((top - hh) / RH) - BUF);
  var e = Math.min(total, Math.ceil((top + ch - hh) / RH) + BUF);
  if (e < s) e = s;
  var html = '';
  if (total === 0) {
    html = '<tr><td colspan="' + (C + 1) + '" style="height:70px;text-align:center;color:#888">कोई रिकॉर्ड मैच नहीं हुआ</td></tr>';
  } else {
    if (s > 0) html += '<tr><td colspan="' + (C + 1) + '" style="height:' + (s * RH) + 'px;padding:0;border:0"></td></tr>';
    for (var p = s; p < e; p++) {
      var row = R[view[p]];
      html += '<tr><td class="n">' + (p + 1) + '</td>';
      for (var c = 0; c < C; c++) {
        var v = row[c];
        html += (v.length > 18) ? '<td title="' + esc(v) + '">' + esc(v) + '</td>' : '<td>' + esc(v) + '</td>';
      }
      html += '</tr>';
    }
    if (e < total) html += '<tr><td colspan="' + (C + 1) + '" style="height:' + ((total - e) * RH) + 'px;padding:0;border:0"></td></tr>';
  }
  tbody.innerHTML = html;
}

function recompute(){
  var act = [];
  for (var c = 0; c < C; c++) if (filters[c] !== '') act.push(c);
  var out = [];
  for (var i = 0; i < N; i++) {
    var row = R[i], ok = true;
    for (var k = 0; k < act.length; k++) {
      if (row[act[k]].toLowerCase().indexOf(filters[act[k]]) === -1) { ok = false; break; }
    }
    if (ok) out.push(i);
  }
  if (sortCol >= 0) {
    var sc = sortCol, sd = sortDir;
    out.sort(function(a, b){
      var x = R[a][sc], y = R[b][sc];
      if (x === '' && y === '') return 0;
      if (x === '') return 1;
      if (y === '') return -1;
      return sd * cmp(x, y);
    });
  }
  view = out;
  if (act.length) {
    cnt.innerHTML = '🔎 सर्च फ़िल्टर सक्रिय है — कुल <b>' + out.length + '</b> रिकॉर्ड मैच हुए (पूरे <b>' + N + '</b> रिकॉर्ड्स में से)।';
    clr.style.display = 'inline-block';
  } else {
    cnt.innerHTML = '';
    clr.style.display = 'none';
  }
  render();
}

thead.addEventListener('input', function(ev){
  var t = ev.target;
  if (t.tagName !== 'INPUT') return;
  filters[+t.getAttribute('data-c')] = t.value.trim().toLowerCase();
  clearTimeout(timer);
  timer = setTimeout(function(){ wrap.scrollTop = 0; recompute(); }, 120);
});

thead.addEventListener('click', function(ev){
  var th = ev.target.closest ? ev.target.closest('tr.h th') : null;
  if (!th) return;
  var c = th.getAttribute('data-c');
  if (c === null) return;
  c = +c;
  if (sortCol === c) { if (sortDir === 1) sortDir = -1; else { sortCol = -1; sortDir = 1; } }
  else { sortCol = c; sortDir = 1; }
  updateArrows();
  recompute();
});

clr.addEventListener('click', function(){
  var ins = thead.querySelectorAll('tr.f input');
  for (var k = 0; k < ins.length; k++) ins[k].value = '';
  for (var z2 = 0; z2 < C; z2++) filters[z2] = '';
  wrap.scrollTop = 0;
  recompute();
});

wrap.addEventListener('scroll', function(){
  if (ticking) return;
  ticking = true;
  requestAnimationFrame(function(){ ticking = false; render(); });
});
window.addEventListener('resize', render);

recompute();
})();
</script></body></html>"""


def render_inline_filter_table(df, height=520):
    """DataFrame को ऐसी टेबल में दिखाता है जिसमें हेडर-रो और पहली डेटा-रो के बीच हर कॉलम का सर्च बॉक्स होता है।
    S.No. कॉलम टेबल खुद जोड़ती है (फ़िल्टर/सॉर्ट के बाद 1, 2, 3... दोबारा गिनती है)।"""
    safe_df = df.fillna("").astype(str)
    headers = [str(c) for c in safe_df.columns]
    rows = safe_df.values.tolist()

    widths = []
    sample = safe_df.head(300)
    for i, h in enumerate(headers):
        longest_cell = max([len(v) for v in sample.iloc[:, i].tolist()] or [0])
        w = max(len(h) * 8 + 40, longest_cell * 8 + 26)
        widths.append(int(min(max(w, 100), 340)))

    payload = json.dumps({"headers": headers, "rows": rows, "widths": widths}, ensure_ascii=False)
    # <script> के अंदर सुरक्षित रखने के लिए
    payload = payload.replace("</", "<\\/").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")

    html_doc = _INLINE_FILTER_TABLE_HTML.replace("__HEIGHT__", str(int(height))).replace("__DATA__", payload)
    components.html(html_doc, height=int(height) + 44, scrolling=False)



def save_p1_dropdown_schemas():
    P1_SCHEMA_FILE = "p1_dropdown_config_schema.json"
    with open(P1_SCHEMA_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.p1_dropdown_schemas, f, ensure_ascii=False, indent=4)

# ==========================================================
# 🎨 स्टेप 4: डायनेमिक सीएसएस (CSS) रेंडरिंग इंजन (परफेक्ट स्क्रीन हाइड फिक्स)
# ==========================================================
b_color = st.session_state.pre_login_config.get("notice_board_border_color", "#FF5733")
bg_color = st.session_state.pre_login_config.get("notice_board_bg_color", "#f9f9f9")

st.markdown(f"""
    <style>
    /* 📋 स्क्रीन पर इस कंटेनर को पूरी तरह गायब रखें (ताकि नीचे कोई लिस्ट न दिखे) */
    .print-only-container {{
        display: none !important;
    }}
    
    @media print {{
        /* 1. स्क्रीन की बाकी सारी चीजें (हेडर, फॉर्म, बटन्स और ऐप की ओरिजिनल ग्रिड) छुपाएं */
        header, [data-testid="stHeader"], [data-testid="stSidebar"], 
        [data-testid="stDecoration"], [data-testid="stNotification"], 
        [data-testid="stForm"], .header-container, .notice-board,
        .print-hide, iframe, div.element-container, div[data-testid="stDataFrame"] {{
            display: none !important;
        }}
        
        /* 2. प्रिंट लेते समय इस कंटेनर और इसके अंदर की टेबल को एक्टिव करें */
        .print-only-container {{
            display: block !important;
        }}
        .print-only-container table {{
            display: table !important;
            width: 100% !important;
            border-collapse: collapse !important;
            font-family: Arial, sans-serif !important;
            font-size: 11px !important;
            color: #000 !important;
        }}
        .print-only-container th {{
            background-color: #f2f2f2 !important;
            border: 1px solid #111 !important;
            padding: 6px !important;
            font-weight: bold !important;
            text-align: center !important;
        }}
        .print-only-container td {{
            border: 1px solid #111 !important;
            padding: 5px !important;
            text-align: left !important;
        }}
        
        @page {{ 
            margin: 8mm; 
            size: A4 landscape; 
        }}
    }}
    
    /* स्क्रीन डिस्प्ले के लिए सामान्य CSS */
    .header-container {{ display: flex; align-items: center; gap: 20px; margin-bottom: 20px; }}
    .header-text {{ display: flex; flex-direction: column; }}
    .header-text h3 {{ margin: 0 !important; padding: 0 !important; color: #0F2A4A; }}
    .header-text h1 {{ margin: 0 !important; }}
    
    .notice-board {{
        background-color: {bg_color};
        border-left: 6px solid {b_color};
        padding: 15px;
        margin-bottom: 25px;
        border-radius: 4px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }}
    .notice-title {{ font-weight: bold; color: #333; margin-bottom: 8px; font-size: 18px; }}

    /* ============================================================
       🎨 UNIFIED INSTITUTIONAL THEME — Navy + Gold
       Yeh poore app (P1 se P15 tak, login screen samet) par apne aap
       lagu hota hai kyunki yeh sabhi Streamlit ke standard widgets
       (headers, buttons, tables, alerts, inputs) ko target karta hai.
       ============================================================ */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@500;600;700&family=Inter:wght@400;500;600;700&display=swap');

    :root {{
        --pg-navy: #0F2A4A;
        --pg-navy-light: #1D4A7A;
        --pg-gold: #C9973F;
        --pg-gold-dark: #A97A25;
        --pg-bg: #F5F7FA;
        --pg-surface: #FFFFFF;
        --pg-border: #DCE3EC;
        --pg-text: #1B2430;
    }}

    [data-testid="stAppViewContainer"], .main, body {{
        background: var(--pg-bg) !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
        color: var(--pg-text) !important;
    }}
    [data-testid="stHeader"] {{ background: transparent !important; }}
    .block-container {{ padding-top: 2rem !important; }}

    /* --- हेडलाइन्स (h1-h4) — Poppins + Navy, हर सेक्शन-हेड के नीचे गोल्ड अंडरलाइन --- */
    h1, h2, h3, h4 {{
        font-family: 'Poppins', 'Inter', sans-serif !important;
        color: var(--pg-navy) !important;
        font-weight: 600 !important;
    }}
    .stMarkdown h1, .stMarkdown h2, div[data-testid="stHeadingWithActionElements"] h1,
    div[data-testid="stHeadingWithActionElements"] h2 {{
        display: inline-block;
        padding-bottom: 6px;
        border-bottom: 3px solid var(--pg-gold);
        margin-bottom: 16px !important;
    }}

    /* --- बटन्स (सभी पैनल्स के Save/Verify/Delete/Update आदि बटन) --- */
    .stButton > button, .stDownloadButton > button {{
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.55rem 1.2rem !important;
        transition: transform 0.12s ease, box-shadow 0.12s ease !important;
    }}
    .stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, var(--pg-navy) 0%, var(--pg-navy-light) 100%) !important;
        border: none !important; color: #fff !important;
    }}
    .stButton > button[kind="primary"]:hover {{
        box-shadow: 0 4px 14px rgba(15,42,74,0.30) !important; transform: translateY(-1px);
    }}
    .stButton > button[kind="secondary"] {{
        background: var(--pg-surface) !important; color: var(--pg-navy) !important;
        border: 1.5px solid var(--pg-navy) !important;
    }}
    .stButton > button[kind="secondary"]:hover {{ background: #EEF2F8 !important; }}
    /* Download/Share बटन्स — Gold accent ताकि 'share' actions बाकी बटन्स से अलग दिखें */
    .stDownloadButton > button {{
        background: linear-gradient(135deg, var(--pg-gold-dark) 0%, var(--pg-gold) 100%) !important;
        color: #fff !important; border: none !important;
    }}
    .stDownloadButton > button:hover {{
        box-shadow: 0 4px 14px rgba(201,151,63,0.38) !important; transform: translateY(-1px);
    }}

    /* --- लिस्ट/शीट (st.dataframe और st.data_editor) --- */
    div[data-testid="stDataFrame"], div[data-testid="stDataEditor"] {{
        border: 1px solid var(--pg-border) !important;
        border-radius: 10px !important;
        overflow: hidden !important;
        box-shadow: 0 1px 4px rgba(15,42,74,0.07) !important;
    }}
    div[data-testid="stDataFrame"] [role="columnheader"],
    div[data-testid="stDataEditor"] [role="columnheader"] {{
        background: var(--pg-navy) !important; color: #fff !important; font-weight: 600 !important;
    }}

    /* --- अलर्ट बॉक्स (success/info/warning/error) --- */
    div[data-testid="stAlert"] {{ border-radius: 8px !important; border-left-width: 5px !important; }}

    /* --- इनपुट फ़ील्ड्स --- */
    .stTextInput input, .stNumberInput input, .stTextArea textarea,
    .stSelectbox div[data-baseweb="select"] > div {{
        border-radius: 6px !important; border-color: var(--pg-border) !important;
    }}
    .stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {{
        border-color: var(--pg-gold) !important; box-shadow: 0 0 0 1px var(--pg-gold) !important;
    }}

    /* --- टैब्स और एक्सपैंडर्स --- */
    button[data-baseweb="tab"] {{ font-weight: 600 !important; }}
    button[data-baseweb="tab"][aria-selected="true"] {{
        color: var(--pg-navy) !important; border-bottom-color: var(--pg-gold) !important;
    }}
    details {{ border-radius: 8px !important; border-color: var(--pg-border) !important; }}

    .notice-board {{ border-radius: 10px !important; }}
    hr {{ border-top: 1px solid var(--pg-border) !important; }}

    /* ============================================================
       🧭 SIDEBAR NAVIGATION — "Navigate Active Modules" ko
       Dark-Navy panel ke andar Gold-highlight wale pill buttons
       jaisa banaya gaya hai, taaki active module turant dikhe.
       ============================================================ */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #0F2A4A 0%, #0A1E33 100%) !important;
        border-right: 1px solid #0A1E33 !important;
    }}
    [data-testid="stSidebar"] * {{ color: #F2F5FA !important; }}
    [data-testid="stSidebar"] hr {{ border-top: 1px solid rgba(255,255,255,0.15) !important; }}
    [data-testid="stSidebar"] label[data-testid="stWidgetLabel"] p {{
        font-family: 'Poppins','Inter',sans-serif !important;
        font-size: 16px !important; font-weight: 700 !important;
        color: #E9C989 !important; letter-spacing: 0.2px;
        padding-bottom: 10px !important; margin-bottom: 4px !important;
        border-bottom: 2px solid rgba(233,201,137,0.35);
    }}

    /* हर मॉड्यूल एक साफ़, अलग-अलग "pill" कार्ड जैसा दिखे */
    [data-testid="stSidebar"] div[role="radiogroup"] {{
        display: flex !important; flex-direction: column !important; gap: 7px !important;
        margin-top: 6px !important;
    }}
    [data-testid="stSidebar"] div[role="radiogroup"] label {{
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(255,255,255,0.14) !important;
        border-radius: 9px !important;
        padding: 11px 14px !important;
        margin: 0 !important;
        width: 100% !important;
        transition: background 0.15s ease, border-color 0.15s ease, transform 0.1s ease !important;
        cursor: pointer !important;
    }}
    [data-testid="stSidebar"] div[role="radiogroup"] label:hover {{
        background: rgba(201,151,63,0.18) !important;
        border-color: #C9973F !important;
        transform: translateX(2px);
    }}
    /* चुना हुआ (Active) मॉड्यूल — गोल्ड हाईलाइट */
    [data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {{
        background: linear-gradient(135deg, #C9973F 0%, #A97A25 100%) !important;
        border-color: #E9C989 !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.25) !important;
    }}
    [data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p {{
        color: #0F2A4A !important; font-weight: 700 !important;
    }}
    /* डिफ़ॉल्ट गोल बुलेट हटाकर साफ़ pill जैसा लुक */
    [data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child {{
        display: none !important;
    }}
    </style>
""", unsafe_allow_html=True)

# ==========================================================
# 🛑स्टेप 5: सुरक्षित लॉगिन ऑथेंटिकेशन गेटवे (Bold Mantra & Shadow Border Added)
# ==========================================================
if st.session_state.user_role is None:
    show_header = st.session_state.pre_login_config.get("show_header_text", True)
    mantra = st.session_state.pre_login_config.get("header_mantra", "ॐ श्री गुरवे नमः")
    sys_title = st.session_state.pre_login_config.get("system_title", "Permanent Shared Live Database System")
    logo_file_path = st.session_state.pre_login_config.get("logo_path", "logo pratap.png")
    logo_w = st.session_state.pre_login_config.get("logo_width", 110)
    logo_h = st.session_state.pre_login_config.get("logo_height", 110)
    logo_fit = st.session_state.pre_login_config.get("logo_fit_mode", "contain")
    mantra_font_px = int(st.session_state.pre_login_config.get("header_mantra_font_size", 24))  # 🟢 FONT SIZE OPTION
    title_font_px = int(st.session_state.pre_login_config.get("header_title_font_size", 32))    # 🟢 FONT SIZE OPTION
    
    if show_header:
        img_base64 = get_image_base64(logo_file_path)
        
        # 🎨 यहाँ लोगो पर 'box-shadow' बॉर्डर और मंत्र को 'font-weight: bold' किया गया है
        header_html = f"""
        <div style="display: flex; align-items: center; gap: 20px; margin-bottom: 20px; font-family: 'Poppins','Inter',sans-serif; background: linear-gradient(135deg, #FFFFFF 0%, #F5F7FA 100%); border: 1px solid #DCE3EC; border-radius: 12px; padding: 16px 20px;">
            <div style="flex-shrink: 0; width: {logo_w}px; height: {logo_h}px; display: flex; align-items: center; justify-content: center; overflow: hidden; border-radius: 10px; box-shadow: 0 4px 12px rgba(15,42,74,0.18); border: 2px solid #C9973F;">
                {"<img src='" + img_base64 + "' style='width: 100%; height: 100%; object-fit: " + logo_fit + "; display: block;'>" if img_base64 else "<h1 style='margin: 0;'>🏛️</h1>"}
            </div>
            <div style="display: flex; flex-direction: column; justify-content: center;">
                <h3 style="margin: 0 !important; padding: 0 !important; color: #A97A25; font-weight: 700 !important; font-size: {mantra_font_px}px; letter-spacing: 0.5px;">{mantra}</h3>
                <h1 style="margin: 5px 0 0 0 !important; padding: 0 !important; color: #0F2A4A; font-size: {title_font_px}px; font-weight: 700; border: none !important;">{sys_title}</h1>
            </div>
        </div>
        <hr style="margin-top: 10px; margin-bottom: 25px; border: 0; border-top: 1px solid #DCE3EC;">
        """
        st.markdown(header_html, unsafe_allow_html=True)

    # 📢 कॉलेज सूचना पटल (Official Notice Board)
    # 🟢 FIX: ab har line ke andar agar koi link (http/https/www) hai to use HTML-escape karne
    # ke baad clickable <a> tag me convert kar dete hain — Notice Board par click/touch karte hi
    # user seedhe us link ke page par (naye tab me) pahunch jaayega.
    formatted_notice = "".join([f"<p>{linkify_notice_line(line.strip())}</p>" for line in st.session_state.notice_text.split('\n') if line.strip()])
    st.markdown(f"""
        <div class="notice-board">
            <div class="notice-title">📢 कॉलेज सूचना पटल (Official Notice Board)</div>
            {formatted_notice}
        </div>
    """, unsafe_allow_html=True)

    # ==========================================================
    # 📚 STUDENT SYLLABUS LOOKUP (बिना लॉगिन के, Desk Board पर ही)
    # P12 (Admin) me jo Subject + Year ke hisab se Syllabus File/Link
    # save ki jaati hai, wahi yahan student khud Subject aur Year
    # chunkar dekh/download kar sakta hai — koi login nahi chahiye.
    # ==========================================================
    _p_syllabus_data = load_syllabus_data()
    # 🟢 Fix: "__mode__" sirf Year/Semester mode yaad rakhne wali internal key hai (koi
    # asli Syllabus entry nahi) — isliye is akeli key ke aadhar par Subject ko "Syllabus
    # available" mat maano, warna khaali Subject bhi list me dikhne lagega.
    _p_syllabus_subjects = sorted([
        s for s, yrs in _p_syllabus_data.items()
        if any(k != "__mode__" for k in yrs)
    ])
    if _p_syllabus_subjects:
        st.markdown("---")
        st.markdown("### 📚 अपना Syllabus देखें (Check Your Syllabus)")
        st.caption("नीचे अपना Subject और Year/Semester चुनें — Syllabus File या Link तुरंत यहीं मिल जाएगी।")

        _p_col_subj, _p_col_year = st.columns(2)
        with _p_col_subj:
            _p_sel_subject = st.selectbox(
                "📘 अपना Subject चुनें:",
                options=_p_syllabus_subjects,
                key="p_public_syllabus_subject_select"
            )
        with _p_col_year:
            # 🟢 नया: Subject ya to Year-wise (SYLLABUS_YEAR_OPTIONS) ya Semester-wise
            # (SYLLABUS_SEM_OPTIONS — जैसे PG के 2 Year = 4 Semester) मोड में सेव हुआ हो सकता
            # है, इसलिए दोनों लिस्ट में से जो भी इस Subject में असल में मौजूद हैं वही दिखाएँ।
            _p_subj_years_available = [
                y for y in (SYLLABUS_YEAR_OPTIONS + SYLLABUS_SEM_OPTIONS)
                if y in _p_syllabus_data.get(_p_sel_subject, {})
            ]
            if _p_subj_years_available:
                _p_sel_year = st.selectbox(
                    "🗓️ अपना Year/Semester चुनें:",
                    options=_p_subj_years_available,
                    key="p_public_syllabus_year_select"
                )
            else:
                _p_sel_year = None
                st.info("इस Subject के लिए अभी किसी भी Year/Semester की Syllabus उपलब्ध नहीं है।")

        if _p_sel_year:
            _p_result = _p_syllabus_data.get(_p_sel_subject, {}).get(_p_sel_year, {})
            if _p_result.get("type") == "file" and _p_result.get("value") and os.path.exists(_p_result["value"]):
                st.success(f"✅ **{_p_sel_subject} — {_p_sel_year}** की Syllabus मिल गई!")
                try:
                    with open(_p_result["value"], "rb") as _p_fh:
                        st.download_button(
                            "⬇️ Syllabus Download करें",
                            data=_p_fh.read(),
                            file_name=_p_result.get("file_name", os.path.basename(_p_result["value"])),
                            key="p_public_syllabus_download_btn",
                            use_container_width=True,
                            type="primary"
                        )
                except Exception:
                    st.error("⚠️ फ़ाइल पढ़ने में समस्या आई — कृपया एडमिन से संपर्क करें।")
            elif _p_result.get("type") == "link" and _p_result.get("value"):
                st.success(f"✅ **{_p_sel_subject} — {_p_sel_year}** की Syllabus मिल गई!")
                st.markdown(
                    f'<a href="{_p_result["value"]}" target="_blank" rel="noopener noreferrer" '
                    f'style="display:inline-block; padding:10px 18px; background:linear-gradient(135deg,#A97A25,#C9973F); color:white; '
                    f'border-radius:8px; text-decoration:none; font-weight:600; box-shadow:0 3px 10px rgba(201,151,63,0.35);">🔗 Syllabus खोलें (नए टैब में)</a>',
                    unsafe_allow_html=True
                )
            else:
                st.info("इस Subject/Year के लिए अभी Syllabus उपलब्ध नहीं है।")

    if not st.session_state.show_login_form:
        if st.button("🔐 Click Here to Open Secure Login System", type="primary", use_container_width=True):
            st.session_state.show_login_form = True
            st.rerun()
            
    if st.session_state.show_login_form:
        st.markdown("---")
        st.subheader("🔒 Enter Secure Gateway Credentials")
        col_l1, col_l2 = st.columns(2)
        
        with col_l1:
            user_list_options = list(st.session_state.credentials.keys())
            def get_lbl(uid): return st.session_state.credentials[uid].get("label", uid)
            user_input = st.selectbox("👤 Select Your User ID / Panel Account:", options=user_list_options, format_func=get_lbl)
            
        with col_l2:
            password_input = st.text_input("🔑 Enter Secure Password:", type="password")
            
        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
            if st.button("🔓 Verify & Access System", type="primary", use_container_width=True):
                if user_input in st.session_state.credentials and st.session_state.credentials[user_input]["password"] == password_input:
                    st.session_state.user_role = st.session_state.credentials[user_input]["role"]
                    st.session_state.logged_username = user_input
                    st.session_state.show_login_form = False
                    st.success("✅ क्रेडेंशियल स्वीकृत! पैनल में प्रवेश किया जा रहा है...")
                    st.rerun()
                else:
                    st.error("❌ गलत पासवर्ड दर्ज किया गया है!")
                    
        with c_btn2:
            if st.button("❌ Close Login Windows", type="secondary", use_container_width=True):
                st.session_state.show_login_form = False
                st.rerun()

# ==========================================================
# 🧭 स्टेप 6: पोस्ट-लॉगिन वर्कस्पेस और पैनल राउटिंग इंजन
# ==========================================================
else:
    role = st.session_state.user_role
    username = st.session_state.logged_username
    
    # 🏛️ हर पैनल के ऊपर भी इमेज जैसा हॉरिजॉन्टल हेडर दिखाएं
    show_header = st.session_state.pre_login_config.get("show_header_text", True)
    mantra = st.session_state.pre_login_config.get("header_mantra", "ॐ श्री गुरवे नमः")
    sys_title = st.session_state.pre_login_config.get("system_title", "Permanent Shared Live Database System")
    logo_file_path = st.session_state.pre_login_config.get("logo_path", "logo pratap.png")
    logo_w = st.session_state.pre_login_config.get("logo_width", 110)
    logo_h = st.session_state.pre_login_config.get("logo_height", 110)
    logo_fit = st.session_state.pre_login_config.get("logo_fit_mode", "contain")
    # 🟢 FONT SIZE OPTION: panel ke andar header thoda chhota rehta hai, isliye yahan
    # Part-2 me set kiye gaye size ka ~75% le rahe hain (login page jaisa bada nahi, lekin
    # ratio bana rehta hai — jitna bada Mantra/Title font Part-2 me set karoge, utna hi
    # yahan bhi proportionally bada/chhota dikhega).
    mantra_font_px = max(10, int(round(int(st.session_state.pre_login_config.get("header_mantra_font_size", 24)) * 0.75)))
    title_font_px = max(10, int(round(int(st.session_state.pre_login_config.get("header_title_font_size", 32)) * 0.75)))
    
    if show_header:
        img_base64 = get_image_base64(logo_file_path)
        
        # 🎨 पैनल के अंदर प्रीमियम शैडो बॉर्डर और बोल्ड लुक
        panel_header_html = f"""
        <div class="print-hide" style="display: flex; align-items: center; gap: 15px; margin-bottom: 15px; font-family: 'Poppins','Inter',sans-serif; background: linear-gradient(135deg, #FFFFFF 0%, #F5F7FA 100%); border: 1px solid #DCE3EC; border-radius: 10px; padding: 12px 16px;">
            <div style="flex-shrink: 0; width: {logo_w}px; height: {logo_h}px; display: flex; align-items: center; justify-content: center; overflow: hidden; border-radius: 8px; box-shadow: 0 3px 8px rgba(15,42,74,0.15); border: 2px solid #C9973F;">
                {"<img src='" + img_base64 + "' style='width: 100%; height: 100%; object-fit: " + logo_fit + "; display: block;'>" if img_base64 else "<h2 style='margin: 0;'>🏛️</h2>"}
            </div>
            <div style="display: flex; flex-direction: column; justify-content: center;">
                <h4 style="margin: 0 !important; padding: 0 !important; color: #A97A25; font-weight: 700 !important; font-size: {mantra_font_px}px;">{mantra}</h4>
                <h2 style="margin: 3px 0 0 0 !important; padding: 0 !important; color: #0F2A4A; font-size: {title_font_px}px; font-weight: 700; border: none !important;">{sys_title}</h2>
            </div>
        </div>
        <div class="print-hide"><hr style="margin-top: 5px; margin-bottom: 15px; border: 0; border-top: 1px solid #DCE3EC;"></div>
        """
        st.markdown(panel_header_html, unsafe_allow_html=True)

    # 🚪 सक्रिय सत्र और लॉगआउट ब्लॉक
    st.markdown('<div class="print-hide">', unsafe_allow_html=True)
    col_top1, col_top2 = st.columns(2)
    with col_top1:
        st.success(f"🔑 सक्रिय सत्र: {username.upper()} | भूमिका अधिकार: {role.upper()}")
    with col_top2:
        if st.button("🔒 Secure Logout / Exit System", type="primary", use_container_width=True):
            st.session_state.user_role = None
            st.session_state.logged_username = None
            st.session_state.cce_foil_generated = False
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("---")

    allowed_panels = []
    if role == "full_admin":
        allowed_panels = list(DEFAULT_PANELS.keys()) 
    elif role == "p1_role": allowed_panels = ["P1"]
    elif role == "p2_role": allowed_panels = ["P2"]
    elif role == "p3_role": allowed_panels = ["P3"]
    elif role == "p4_role": allowed_panels = ["P4"]
    elif role == "p5_role": allowed_panels = ["P5"]
    elif role == "p6_role": allowed_panels = ["P6"]
    elif role == "p7_role": allowed_panels = ["P7"]
    elif role == "p8_role": allowed_panels = ["P8"]
    elif role == "p9_role": allowed_panels = ["P9"]
    elif role == "p10_role": allowed_panels = ["P10"]
    elif role == "p11_role": allowed_panels = ["P11"]
    elif role == "p12_role": allowed_panels = ["P12"]
    elif role == "p13_role": allowed_panels = ["P13"]
    elif role == "p14_role": allowed_panels = ["P14"]

    active_tabs_names = [f"{p} : {get_panel_title(p)}" for p in allowed_panels if not st.session_state.get(f"hide_panel_{p}", False) or role == "full_admin"]
    
    if not active_tabs_names:
        st.warning("⚠️ वर्तमान में आपकी भूमिका के लिए कोई भी पैनल एक्टिव नहीं किया गया है।")
    else:
        st.sidebar.markdown(
            f"""
            <div style="display:flex; align-items:center; gap:10px; padding:2px 2px 14px 2px; margin-bottom:10px; border-bottom:1px solid rgba(255,255,255,0.15);">
                <div style="width:38px; height:38px; border-radius:9px; background:linear-gradient(135deg,#C9973F,#A97A25); display:flex; align-items:center; justify-content:center; font-size:19px; box-shadow:0 2px 6px rgba(0,0,0,0.3); flex-shrink:0;">🏛️</div>
                <div style="line-height:1.25;">
                    <div style="font-size:13px; color:#E9C989; font-weight:700;">{username.upper()}</div>
                    <div style="font-size:11px; color:rgba(242,245,250,0.65);">{role.upper()} · {len(active_tabs_names)} Module{'s' if len(active_tabs_names) != 1 else ''} Active</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        selected_tab_ui = st.sidebar.radio("🧭 Navigate Active Modules:", options=active_tabs_names)
        
        # 🎯 यहाँ फिक्स किया गया है (अंतिम भाग [0] को जोड़कर इसे दोबारा स्ट्रिंग बनाया गया है)
        current_panel_id = selected_tab_ui.split(" : ")[0]

        # ----------------------------------------------------------------------
        # P1: PANEL ENTRY MODULE (3 Scroll Lists & Multi-Format Upload System)
        # ----------------------------------------------------------------------
        if current_panel_id == "P1":
            st.header(f"📝 {get_panel_title('P1')} (Student Data Onboarding)")
            entry_method = st.selectbox(
                "⚙️ डेटा एंट्री का माध्यम चुनें:", 
                options=["📁 फ़ाइल बल्क अपलोड (Bulk File Upload)", "➕ नया छात्र मैनुअल फॉर्म (Manual Form Entry)"]
            )
            
            # 📁 बल्क फ़ाइल अपलोड सब-सिस्टम
            if entry_method == "📁 फ़ाइल बल्क अपलोड (Bulk File Upload)":
                st.subheader("📊 Select Target Configurations Before Upload")
                col_sc1, col_sc2, col_sc3 = st.columns(3)
                
                with col_sc1:
                    p1_file_type = st.selectbox(
                        "1. फ़ाइल प्रकार चुनें (Select File Type):",
                        options=["-- चुनें --"] + st.session_state.p1_dropdown_schemas["file_types"],
                        key="p1_scroll_file_type"
                    )
                with col_sc2:
                    p1_admission_year = st.selectbox(
                        "2. Admission Year चुनें:",
                        options=["-- चुनें --"] + st.session_state.p1_dropdown_schemas["academic_years"],
                        key="p1_scroll_admission_year"
                    )
                with col_sc3:
                    p1_admission_session = st.selectbox(
                        "3. Admission Session चुनें:",
                        options=["-- चुनें --"] + st.session_state.p1_dropdown_schemas["academic_sessions"],
                        key="p1_session_scroll_secure_bulk_main"
                    )

                if (p1_file_type == "-- चुनें --" or p1_admission_year == "-- चुनें --" or p1_admission_session == "-- चुनें --"):
                    st.info("💡 कृपया फ़ाइल अपलोड विंडो खोलने के लिए ऊपर दिए गए तीनों विकल्पों (File Segment, Year और Session) का चयन करें।")
                else:
                    st.success(f"✅ कॉन्फ़िगरेशन锁: **{p1_file_type.upper()}** | वर्ष: **{p1_admission_year}** | सत्र: **{p1_admission_session}**")
                    
                    uploader_unique_key = f"p1_bulk_uploader_widget_run_{st.session_state.get('uploader_key_counter', 0)}"
                    
                    uploaded_files = st.file_uploader(
                        f"अपलोड करने के लिए '{p1_file_type}' की फ़ाइलें चुनें (अधिकतम 5):", 
                        type=["csv", "xlsx", "xls"],
                        accept_multiple_files=True,
                        key=uploader_unique_key
                    )
                    
                    if uploaded_files:
                        if len(uploaded_files) > 5:
                            st.warning("⚠️ कृपया एक बार में केवल 1 से 5 फ़ाइलें ही अपलोड करें।")
                        
                        if st.button("Upload & Send to System Database Now", type="primary", use_container_width=True):
                            try:
                                success_count = 0
                                current_stage_db = load_stage_data()
                                all_new_dfs = [current_stage_db]
                                
                                for uploaded_file in uploaded_files:
                                    uploaded_df = read_uploaded_file_as_csv_df(uploaded_file)
                                    
                                    if uploaded_df.empty:
                                        st.error(f"❌ फ़ाइल '{uploaded_file.name}' के अंदर कोई मान्य डेटा नहीं मिला।")
                                        if _UPLOAD_DIAG["info"]:
                                            st.caption(f"🔎 Diagnostic: {_UPLOAD_DIAG['info']}")
                                        continue

                                    uploaded_df = uploaded_df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

                                    # 🧠 स्मार्ट कॉलम मैचिंग: अपलोड फ़ाइल के हेडर अलग-अलग तरीके से लिखे हो सकते हैं
                                    # (जैसे "Enrollment No", "DOB", "Email", "Scholarship" आदि) — इन्हें सही इंटरनल
                                    # कॉलम नाम ("Enrollment No.", "Date of Birth", "Email ID", "Scholarship Name")
                                    # से ऑटोमैटिक मैच करके डेटा गायब होने से बचाएँ।
                                    def _normalize_col_name(name):
                                        return re.sub(r"[^a-z0-9]", "", str(name).strip().lower())

                                    normalized_lookup = {}
                                    for internal_col in DEFAULT_COLUMNS:
                                        normalized_lookup[_normalize_col_name(internal_col)] = internal_col
                                        normalized_lookup[_normalize_col_name(get_display_name(internal_col))] = internal_col

                                    # आम तौर पर एक्सेल/CSV में इस्तेमाल होने वाले जाने-पहचाने वैरिएशन
                                    manual_aliases = {
                                        # 🆔 "Admission Id" = "Admission Application Number" (P3 wali file me yahi naam aata hai)
                                        "admissionid": "Admission Application Number",
                                        "admissionno": "Admission Application Number",
                                        "admissionnumber": "Admission Application Number",
                                        "admissionappno": "Admission Application Number",
                                        "admissionapplicationid": "Admission Application Number",
                                        "admissionapplicationno": "Admission Application Number",
                                        "enrollmentno": "Enrollment No.",
                                        "enrollmentnumber": "Enrollment No.",
                                        "enrollmentnum": "Enrollment No.",
                                        "universityenrollmentno": "Enrollment No.",
                                        "dob": "Date of Birth",
                                        "dateofbirth": "Date of Birth",
                                        "birthdate": "Date of Birth",
                                        "email": "Email ID",
                                        "emailid": "Email ID",
                                        "emailaddress": "Email ID",
                                        "mailid": "Email ID",
                                        "scholarship": "Scholarship Name",
                                        "scholarshipname": "Scholarship Name",
                                        "scholarshiptitle": "Scholarship Name",
                                    }
                                    for _alias_key, _alias_target in manual_aliases.items():
                                        normalized_lookup.setdefault(_alias_key, _alias_target)

                                    rename_map_for_upload = {}
                                    for col in uploaded_df.columns:
                                        if col in DEFAULT_COLUMNS:
                                            continue  # पहले से ही एकदम सही (exact) इंटरनल नाम है
                                        norm_key = _normalize_col_name(col)
                                        if norm_key in normalized_lookup:
                                            target_internal_col = normalized_lookup[norm_key]
                                            # अगर सही इंटरनल कॉलम पहले से ही फ़ाइल में अलग से मौजूद है, तो टकराव से बचें
                                            if target_internal_col in uploaded_df.columns:
                                                continue
                                            rename_map_for_upload[col] = target_internal_col

                                    if rename_map_for_upload:
                                        uploaded_df = uploaded_df.rename(columns=rename_map_for_upload)
                                    
                                    for col in DEFAULT_COLUMNS:
                                        if col not in uploaded_df.columns: 
                                            uploaded_df[col] = ""
                                    
                                    uploaded_df["Admission Year"] = p1_admission_year
                                    uploaded_df["Admission Session"] = p1_admission_session
                                    uploaded_df["Target Panel Visibility"] = "Pending Approval"
                                    
                                    if "Uploaded File Type" not in uploaded_df.columns:
                                        uploaded_df["Uploaded File Type"] = p1_file_type
                                    
                                    cleaned_uploaded_df = uploaded_df[DEFAULT_COLUMNS].copy()
                                    cleaned_uploaded_df["Uploaded File Name"] = uploaded_file.name
                                    
                                    all_new_dfs.append(cleaned_uploaded_df)
                                    success_count += 1
                                
                                if success_count > 0:
                                    updated_stage_df = pd.concat(all_new_dfs, ignore_index=True)
                                    save_stage_data(updated_stage_df)
                                    st.session_state.uploader_key_counter += 1
                                    st.success(f"🎉 कुल {success_count} फ़ाइलें (CSV/XLSX) सफलतापूर्वक 'merge & approve panel' में भेज दी गई हैं!")
                                    st.balloons()
                                    st.rerun()
                            except Exception as e: 
                                st.error(f"फ़ाइल प्रोसेसिंग चक्र में तकनीकी त्रुटि आई: {e}")
                                
            # ➕ नया छात्र मैनुअल फॉर्म सब-सिस्टम
            elif entry_method == "➕ नया छात्र मैनुअल फॉर्म (Manual Form Entry)":
                with st.form(key="student_add_form", clear_on_submit=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        admission_year = st.selectbox("Admission Year *", options=st.session_state.p1_dropdown_schemas["academic_years"])
                        app_number = st.text_input("Application Number *")
                        abc_id = st.text_input("Student Abc Id")
                        s_name = st.text_input("Student Name *")
                        f_name = st.text_input("Father Name")
                        m_name = st.text_input("Mother Name")
                        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
                        dob = st.text_input("Date Of Birth (DD-MM-YYYY)")
                        category = st.selectbox("Category", ["General", "OBC", "SC", "ST"])
                        adm_category = st.selectbox("Admission Category", ["General", "OBC", "SC", "ST"])
                        degree = st.text_input("Degree")
                        branch = st.text_input("Branch")
                    with col2:
                        admission_session = st.selectbox("Admission Session *", options=st.session_state.p1_dropdown_schemas["academic_sessions"])
                        minor_sub = st.text_input("Minor Subjects")
                        vocational_sub = st.text_input("Vocational Subjects")
                        mdc_sub = st.text_input("MDC Subjects")
                        pw_ap_ce_sub = st.text_input("PW/Ap/CE Subjects")
                        mobile = st.text_input("Mobile Number")
                        email = st.text_input("Email")
                        address = st.text_area("Address", height=68)
                        enroll_no = st.text_input("Enrollment No")
                        fees_paid = st.text_input("Admssion & Enrollment Fees")
                        scholarship_name = st.text_input("Scholarship Name")
                        payment_date = st.text_input("Payment Date (DD-MM-YYYY)")
                    
                    st.markdown("<p style='color:gray;'>* चिन्ह वाले फ़ील्ड्स डेटाबेस ट्रैकिंग के लिए महत्वपूर्ण हैं।</p>", unsafe_allow_html=True)
                    submit_student = st.form_submit_button("Save Student Data Systematically", type="primary", use_container_width=True)
                    
                if submit_student:
                    if s_name.strip() == "" or app_number.strip() == "": 
                        st.warning("⚠️ Student Name और Application Number भरना अनिवार्य है।")
                    else:
                        new_row = {c: "" for c in DEFAULT_COLUMNS}
                        # 🟢 फिक्स: पहले यहाँ "Date Of Birth", "Email", "Enrollment No" जैसे गलत-केस/नाम
                        # वाली keys इस्तेमाल होती थीं, जो DEFAULT_COLUMNS की असली keys
                        # ("Date of Birth", "Email ID", "Enrollment No.") से मेल नहीं खाती थीं — इसलिए
                        # डेटा एक अलग (गलत) कॉलम में चला जाता था और असली कॉलम हमेशा खाली दिखता था।
                        # अब सही स्कीमा नामों का उपयोग किया गया है ताकि DOB, Email और Enrollment No
                        # हर जगह सही तरीके से दिखें।
                        new_row.update({
                            "Application Number": app_number, "Student Abc Id": abc_id, 
                            "Student Name": s_name, "Father Name": f_name, "Mother Name": m_name,                             "Gender": gender, "Date of Birth": dob, "Category": category, 
                            "Admission Category": adm_category, "Degree": degree, "Branch": branch, 
                            "Minor Subjects": minor_sub, "Vocational Subjects": vocational_sub, 
                            "MDC Subjects": mdc_sub, "PW/Ap/CE Subjects": pw_ap_ce_sub, 
                            "Mobile Number": mobile, "Email ID": email, "Address": address, 
                            "Enrollment No.": enroll_no, "Admssion & Enrollment Fees": fees_paid, 
                            "Scholarship Name": scholarship_name, "Payment Date": payment_date,
                            "Admission Year": admission_year, "Admission Session": admission_session,  
                            "Status": "Regular Student", "Current Year": "1", "Target Panel Visibility": "Pending Approval"
                        })
                        new_df = pd.DataFrame([new_row])
                        new_df["Uploaded File Name"] = "Manual Form Entry"
                        
                        # Route manual entries directly to merge stage room 
                        updated_stage_df = pd.concat([load_stage_data(), new_df], ignore_index=True)
                        save_stage_data(updated_stage_df)
                        st.success("🎉 Record successfully sent in merge & approve panel!")
                        st.rerun()

        # ----------------------------------------------------------------------
        # P2: PANEL ADMISSION MODULE (Displays Only Content Explicitly Approved for P2)
        # ----------------------------------------------------------------------
        elif current_panel_id == "P2":
            st.header(f"🎓 {get_panel_title('P2')} (Admission Control & Payment Tracker)")
            
            # 🔍 Isolated Firewall Query Filter Rule
            p2_authorized_db = live_db[live_db["Target Panel Visibility"] == "P2"].copy()

            # 🆕 2.1 "Save" ke baad (rerun ke baad) result message dikhao
            _p21_move_msg = st.session_state.pop("p21_move_msg", None)
            if _p21_move_msg:
                st.success(_p21_move_msg)
            
            if p2_authorized_db.empty: 
                st.warning("⚠️ डेटाबेस वर्तमान में खाली है या इस पैनल के लिए कोई अधिकृत स्वीकृत (Approved) डेटा उपलब्ध नहीं है।")
            else:
                # ==============================================================
                # 🗂️ P2 ke andar 2 sub-panel: 2.1 (Document Submit Status) aur 2.2 (purana poora P2)
                # ==============================================================
                # ⚡ st.tabs me dono tab ka code har baar chalta hai (2.2 ka bhi, jo bhaari hai) — isliye radio: sirf chuna hua sub-panel chalta hai
                _P2_SUBS = ["📄 2.1 Document Submit Status", "🎓 2.2 Admission Control & Payment Tracker"]
                _p2_sub = st.radio("P2 sub-panel:", _P2_SUBS, horizontal=True, key="p2_sub_panel_choice", label_visibility="collapsed")

                # ==============================================================
                # 📄 2.1 — P2 ki list + "Document Submit Status" column + har row ke left me Submit / Not Submit Document button
                # ==============================================================
                if _p2_sub == _P2_SUBS[0]:
                    st.subheader("📄 2.1 Document Submit Status")
                    st.caption("हर छात्र के बाईं ओर ✅ Submit / ❌ Not Submit Document बटन दबाएँ — स्थिति सीधे मुख्य डेटाबेस में सेव हो जाएगी।")

                    _P21_COL = "Document Submit Status"
                    # 🔄 Save ke baad row-buttons ke keys badal jate hain, taaki purane click/focus ki halat kisi dusre student ke button par na chipke
                    _p21_kv = int(st.session_state.get("p21_key_ver", 0))

                    def _p21_set_status(row_idx, new_status):
                        """Ek student ki Document Submit Status ko database me turant save karta hai."""
                        _fresh_db = load_live_data()
                        if _P21_COL not in _fresh_db.columns:
                            _fresh_db[_P21_COL] = ""
                        if row_idx in _fresh_db.index:
                            _fresh_db.at[row_idx, _P21_COL] = new_status
                            save_live_data(_fresh_db)

                    p21_db = p2_authorized_db.copy()      # index = live_db ka asli index (isi se save hoga)
                    if _P21_COL not in p21_db.columns:
                        p21_db[_P21_COL] = ""
                    for _c in ["Admission Year", "Subject", "Student Name", "Father Name", "Admission Application Number", _P21_COL]:
                        if _c not in p21_db.columns:
                            p21_db[_c] = ""
                        p21_db[_c] = p21_db[_c].fillna("").astype(str).str.strip()

                    # 🆕 Jo students 2.1 me Save ho chuke wo sirf 2.1 ki list se hatenge (database, 2.2 aur P15 me jaise the waise rahenge).
                    #    Koi naya column nahi — Save ki gayi list ek chhoti JSON file me rehti hai.
                    _P21_SAVED_FILE = "p21_saved_students.json"

                    def _p21_key(_name, _father, _app):
                        return f"{str(_app).strip()}|{str(_name).strip()}|{str(_father).strip()}".lower()

                    def _p21_load_saved():
                        """{student-key: saved status} — purani list wali file ho to sabko 'Submit' maana jayega."""
                        try:
                            with open(_P21_SAVED_FILE, "r", encoding="utf-8") as _f:
                                _d = json.load(_f)
                            if isinstance(_d, list):
                                return {str(_k): "Submit" for _k in _d}
                            return {str(_k): str(_v) for _k, _v in dict(_d).items()}
                        except Exception:
                            return {}

                    def _p21_write_saved(_d):
                        with open(_P21_SAVED_FILE, "w", encoding="utf-8") as _f:
                            json.dump(_d, _f, ensure_ascii=False, indent=2)

                    # Status ko pehle saaf karo (sirf "Submit" / "Not Submit Document", warna khaali)
                    p21_db[_P21_COL] = p21_db[_P21_COL].apply(lambda v: v if v in ("Submit", "Not Submit Document") else "")

                    _p21_saved = _p21_load_saved()
                    if _p21_saved and not p21_db.empty:
                        _keys_now = p21_db.apply(lambda _r: _p21_key(_r["Student Name"], _r["Father Name"],
                                                                    _r["Admission Application Number"]), axis=1)
                        _saved_status = _keys_now.map(_p21_saved)                      # NaN = Save nahi hua
                        # 🙈 Sirf "Submit" wali rows hide hongi — "Not Submit Document" wali row Save ke baad bhi list me rahegi
                        _hide_mask = _saved_status.notna() & (_saved_status == p21_db[_P21_COL]) & (p21_db[_P21_COL] == "Submit")
                        # 🔁 Save ke baad jis student ka status badal gaya / hat gaya (P15 me), uski purani Save-entry hata do —
                        #    wo 2.1 me wapas dikhega aur dobara Save dabane par hi hatega
                        _stale = set(_keys_now[_saved_status.notna() & ~_hide_mask])
                        if _stale:
                            _p21_saved = {_k: _v for _k, _v in _p21_saved.items() if _k not in _stale}
                            try:
                                _p21_write_saved(_p21_saved)
                            except Exception:
                                pass
                        p21_db = p21_db[~_hide_mask]

                    p21_view = p21_db.copy()

                    # ---- 🔎 P15 jaisa inline column-search: header ke theek neeche har column ka search box
                    #      (widget values session_state me pehle se hoti hain, isliye filter list/count/pagination se PEHLE lag jata hai)
                    _cf_defs = [("p21_cf_name", "Student Name"), ("p21_cf_father", "Father Name"),
                                ("p21_cf_app", "Admission Application Number"), ("p21_cf_subj", "Subject"),
                                ("p21_cf_status", _P21_COL)]

                    def _p21_clear_cf():
                        for _k, _ in _cf_defs:
                            st.session_state[_k] = ""

                    _cf_active = False
                    for _k, _col in _cf_defs:
                        _q = str(st.session_state.get(_k, "") or "").strip().lower()
                        if _q:
                            _cf_active = True
                            p21_view = p21_view[p21_view[_col].str.lower().str.contains(_q, regex=False)]

                    _n_sub = int((p21_view[_P21_COL] == "Submit").sum())
                    _n_not = int((p21_view[_P21_COL] == "Not Submit Document").sum())
                    _n_unm = int((p21_view[_P21_COL] == "").sum())
                    st.write(f"कुल छात्र: **{len(p21_view)}**  |  ✅ Submit: **{_n_sub}**  |  ❎ Not Submit Document: **{_n_not}**  |  ⏳ Not Marked: **{_n_unm}**")
                    if _cf_active:
                        st.button("🧹 सर्च साफ़ करें", key="p21_cf_clear", on_click=_p21_clear_cf)

                    # ---- 💾 Save: jin students ka "Document Submit Status" 'Submit' hai unki poori row 2.1 ki list se hat jayegi.
                    #      "Not Submit Document" aur khaali (Not Marked) wale students list me rahenge.
                    _n_ready_p21 = int((p21_db[_P21_COL] == "Submit").sum())
                    # 🙈 Button tabhi dikhega jab kam se kam ek student ka status aaya ho; Save ke baad wo rows hat jati hain, isliye button bhi hide ho jata hai
                    if _n_ready_p21 > 0 and st.button(f"💾 Save ({_n_ready_p21} rows 2.1 se hategi)",
                                 key="p21_save_hide_submit_btn", type="primary",
                                 help="Jinka Document Submit Status 'Submit' hai, unki poori row 2.1 se hata deta hai. 'Not Submit Document' wali rows list me rahengi (2.2 aur P15 me sab pehle jaisa rahega)."):
                        _marked_rows = p21_db[p21_db[_P21_COL] == "Submit"]
                        _p21_new = {_p21_key(_r["Student Name"], _r["Father Name"], _r["Admission Application Number"]): _r[_P21_COL]
                                    for _, _r in _marked_rows.iterrows()}
                        _p21_write_saved({**_p21_load_saved(), **_p21_new})
                        st.session_state["p21_key_ver"] = _p21_kv + 1
                        st.session_state["p21_move_msg"] = f"✅ {len(_p21_new)} Submit students save ho gaye aur unki row 2.1 ki list se hata di gayi। ❎ Not Submit Document wali rows list me hi rahengi।"
                        st.rerun()

                    # 🔀 List Order Selector — 2.2 jaisa hi Sort Order system ab 2.1 me bhi
                    #    (sirf list ka dikhne wala order badalta hai; har row ka asli index wahi rehta hai,
                    #     isliye ✅ / ❎ aur Save usi student par lagte hain jo screen par dikh raha hai)
                    p21_sort_order_choice = st.selectbox(
                        "🔀 लिस्ट किस क्रम में करें (Sort Order):",
                        options=[
                            "डिफ़ॉल्ट क्रम (जैसा डेटा है)",
                            "Student Name (अल्फाबेटिक A-Z क्रम में)",
                            "Subject → Student Name (पहले Subject, फिर नाम अनुसार A-Z)"
                        ],
                        key="p21_sort_order_choice"
                    )
                    if not p21_view.empty:
                        if p21_sort_order_choice.startswith("Subject"):
                            # 🔤 पहले Subject के अल्फाबेटिक क्रम में, फिर उसी Subject के अंदर Student Name A-Z
                            p21_view = p21_view.assign(
                                _sk1=p21_view["Subject"].astype(str).str.strip().str.upper(),
                                _sk2=p21_view["Student Name"].astype(str).str.strip().str.upper()
                            ).sort_values(by=["_sk1", "_sk2"], ascending=[True, True], kind="mergesort"
                            ).drop(columns=["_sk1", "_sk2"])
                        elif p21_sort_order_choice.startswith("Student Name"):
                            # 🔤 Alphabetical (A-Z) क्रम — Student Name के आधार पर
                            p21_view = p21_view.assign(
                                _sk=p21_view["Student Name"].astype(str).str.strip().str.upper()
                            ).sort_values(by=["_sk"], ascending=[True], kind="mergesort"
                            ).drop(columns=["_sk"])
                        # "डिफ़ॉल्ट क्रम" चुनने पर कोई sort नहीं — डेटा जैसा है वैसा ही क्रम रहेगा

                    # ---- pagination (buttons zyada hone se page heavy na ho)
                    _start = 0
                    p21_page_df = p21_view.iloc[0:0]
                    if not p21_view.empty:
                        pg1, pg2 = st.columns(2)
                        with pg1:
                            p21_page_size = st.selectbox("एक पेज पर कितनी rows:", [5, 10, 25, 50, 100], key="p21_page_size")
                        _total_pages = max(1, (len(p21_view) + p21_page_size - 1) // p21_page_size)
                        # filter lagne par pages kam ho jaayein to page number automatically 1 par
                        if int(st.session_state.get("p21_page_no", 1)) > _total_pages:
                            st.session_state["p21_page_no"] = 1
                        with pg2:
                            p21_page_no = st.number_input(f"पेज नंबर (1 – {_total_pages}):", min_value=1, max_value=_total_pages,
                                                          value=1, step=1, key="p21_page_no")
                        _start = (int(p21_page_no) - 1) * p21_page_size
                        p21_page_df = p21_view.iloc[_start:_start + p21_page_size]

                    # ---- header row
                    _W = [0.7, 0.7, 0.6, 2.3, 2.1, 1.9, 2.3, 1.8]
                    st.markdown(
                        "<style>"
                        "[class*='st-key-p21_btn_'] button{min-height:1.9rem !important;height:1.9rem !important;"
                        "padding:0 .55rem !important;font-size:.95rem !important;line-height:1 !important;"
                        "border-radius:6px !important;width:auto !important;}"
                        "[class*='st-key-p21_btn_'] button p{font-size:.95rem !important;margin:0 !important;}"
                        "[class*='st-key-p21_btn_'] button[kind='secondary']:focus:not(:hover):not(:active){"
                        "border-color:rgba(49,51,63,.2) !important;color:inherit !important;box-shadow:none !important;outline:none !important;}"
                        "</style>",
                        unsafe_allow_html=True)
                    st.caption("✅ = Submit   |   ❎ = Not Submit Document")
                    _h = st.columns(_W)
                    for _hc, _lbl in zip(_h, ["✅", "❎", "S. No.", "Student Name", "Father Name",
                                              "Application No.", "Subject", _P21_COL]):
                        _hc.markdown(f"**{_lbl}**")

                    # ---- search-box row (header aur pehli data-row ke beech) — hamesha dikhti hai, taaki khaali result me bhi saaf kar sakein
                    _fr = st.columns(_W)
                    for _ci, (_k, _col) in zip([3, 4, 5, 6, 7], _cf_defs):
                        _fr[_ci].text_input(_col, key=_k, placeholder="🔎 खोजें...", label_visibility="collapsed")
                    st.markdown("---")

                    if p21_view.empty:
                        st.info("इन फ़िल्टर्स के अनुसार कोई छात्र नहीं मिला।")
                    else:
                        _pretty = {"Submit": "✅ Submit", "Not Submit Document": "❎ Not Submit Document", "": "—"}
                        for _n, (_ridx, _r) in enumerate(p21_page_df.iterrows(), start=_start + 1):
                            _ridx = int(_ridx)
                            _cur = _r[_P21_COL]
                            _c = st.columns(_W)
                            _c[0].button("✅", key=f"p21_btn_sub_{_ridx}_v{_p21_kv}", help="Submit",
                                         type="secondary",   # 🔕 laal (selected) look hata diya — abhi ka status sabse right wale column me likha dikhta hai,
                                         on_click=_p21_set_status, args=(_ridx, "Submit"))
                            _c[1].button("❎", key=f"p21_btn_not_{_ridx}_v{_p21_kv}", help="Not Submit Document",
                                         type="secondary",
                                         on_click=_p21_set_status, args=(_ridx, "Not Submit Document"))
                            _c[2].write(_n)
                            _c[3].write(_r["Student Name"])
                            _c[4].write(_r["Father Name"])
                            _c[5].write(_r["Admission Application Number"])
                            _c[6].write(_r["Subject"])
                            _c[7].write(_pretty[_cur])

                # ==============================================================
                # 🎓 2.2 — P2 me jo kuch pehle se tha, wo sab bilkul waisa hi (sirf ek level andar)
                # ==============================================================
                if _p2_sub == _P2_SUBS[1]:
                    # 🟢 Fix: "Student Abc Id" ko galti se "Student Abc ld" (typo) mein rename kar diya jaata tha,
                    # jisse yeh column aage 'Student Abc Id' naam se dhoondhne par nahi milta tha aur khaali dikhta tha.
                    column_mapping_fixes = {
                        "Unique Id": "Unique ID",
                        "Date Of Birth": "Date of Birth", "Duretion": "Duration", 
                        "Email Id": "Email ID", "Year": "Current Year",
                        "Application Number": "Admission Application Number"
                    }
                    p2_authorized_db = p2_authorized_db.rename(columns=column_mapping_fixes)
                    p2_authorized_db = p2_authorized_db.loc[:, ~p2_authorized_db.columns.duplicated()].copy()

                    # सभी कॉलम के डेटा को साफ़ और स्ट्रिंग (String) में बदलें
                    for c in p2_authorized_db.columns:
                        p2_authorized_db[c] = p2_authorized_db[c].astype(str).str.strip()

                    # ==================================================================
                    # 🎛️ Advanced Matrix Filters System
                    # ==================================================================
                    st.markdown('<div class="print-hide">', unsafe_allow_html=True)
                    st.subheader("🔍 Advanced Matrix Filters System")
                
                    col_p2_1, col_p2_2, col_p2_3, col_p2_4, col_p2_5 = st.columns(5)
                
                    with col_p2_1:
                        year_list = ["All Years"] + sorted([y for y in p2_authorized_db["Admission Year"].unique() if y and y.lower() != "nan"])
                        p2_filter_year = st.selectbox("1. Select Admission Year:", options=year_list, key="p2_scroll_filter_year_v18")
                
                    temp_db_after_year = p2_authorized_db.copy()
                    if p2_filter_year != "All Years":
                        temp_db_after_year = temp_db_after_year[temp_db_after_year["Admission Year"] == p2_filter_year]

                    # 🆕 बॉक्स 2: Under Graduate / Post Graduate फ़िल्टर — "Eligibility Name" कॉलम के टेक्स्ट से पहचानता है
                    with col_p2_2:
                        if "Eligibility Name" in temp_db_after_year.columns:
                            ugpg_seen = sorted({classify_ug_pg(d) for d in temp_db_after_year["Eligibility Name"].unique()} - {""})
                        else:
                            ugpg_seen = []
                        ugpg_list = ["All"] + ugpg_seen
                        p2_filter_ugpg = st.selectbox("2. Select Under Graduate/Post Graduate:", options=ugpg_list, key="p2_scroll_filter_ugpg_v18")

                    temp_db_for_sub = temp_db_after_year.copy()
                    if p2_filter_ugpg != "All" and "Eligibility Name" in temp_db_for_sub.columns:
                        temp_db_for_sub = temp_db_for_sub[temp_db_for_sub["Eligibility Name"].apply(classify_ug_pg) == p2_filter_ugpg]

                    with col_p2_3:
                        subject_list = ["All Subjects"] + sorted([s for s in temp_db_for_sub["Subject"].unique() if s and s.lower() != "nan"])
                        p2_filter_subject = st.selectbox("3. Select Subject:", options=subject_list, key="p2_scroll_filter_subject_v18")
                
                    with col_p2_4:
                        # 🟢 Fix: "Subject" ko yahan se hata diya gaya hai kyunki uska apna dedicated
                        # dropdown (3. Select Subject) upar hi maujood hai — dono jagah Subject rakhne se
                        # confusing double-filtering hoti thi. Ab "Subject" ki jagah is dropdown mein
                        # nahi dikhega (jab bhi "All Subjects" ho ya na ho, "Column Filter Target" hamesha
                        # baaki dusre columns hi dikhayega).
                        ignore_cols = ["Target Panel Visibility", "Uploaded File Name", "Uploaded File Type", "Subject"]
                        available_cols = [c for c in p2_authorized_db.columns if c not in ignore_cols]
                        p2_selected_col = st.selectbox("4. Select Column Filter Target:", options=available_cols, key="p2_scroll_filter_column_name_v18")
                
                    dependent_db = p2_authorized_db.copy()
                    if p2_filter_year != "All Years":
                        dependent_db = dependent_db[dependent_db["Admission Year"] == p2_filter_year]
                    if p2_filter_ugpg != "All" and "Eligibility Name" in dependent_db.columns:
                        dependent_db = dependent_db[dependent_db["Eligibility Name"].apply(classify_ug_pg) == p2_filter_ugpg]
                    if p2_filter_subject != "All Subjects":
                        dependent_db = dependent_db[dependent_db["Subject"] == p2_filter_subject]

                    with col_p2_5:
                        raw_vals = dependent_db[p2_selected_col].unique()
                        val_list = ["All Values"] + sorted([v for v in raw_vals if v and v.lower() != "nan"])
                        p2_selected_val = st.selectbox(f"5. Filter Value for '{p2_selected_col}':", options=val_list, key="p2_scroll_filter_value_data_v18")
                
                    # Payment Date Range Filter
                    st.markdown("---")
                    if "p2_show_date_filter_section" not in st.session_state:
                        st.session_state.p2_show_date_filter_section = True
                    hdr_dt_1, hdr_dt_2 = st.columns([6, 1])
                    with hdr_dt_1:
                        st.subheader("📆 Filter Records By Payment Date Range")
                    with hdr_dt_2:
                        st.write("")
                        if st.button("🙈 Hide" if st.session_state.p2_show_date_filter_section else "👁️ Unhide",
                                     key="p2_toggle_date_filter_section", use_container_width=True):
                            st.session_state.p2_show_date_filter_section = not st.session_state.p2_show_date_filter_section

                    start_date = pd.to_datetime("2024-01-01")
                    end_date = pd.to_datetime("2026-12-31")

                    if st.session_state.p2_show_date_filter_section:
                        use_date_filter = st.checkbox("Enable Payment Date Range Filter (तारीख सीमा फ़िल्टर सक्रिय करें)", value=False, key="p2_enable_date_filter_secure_v18")

                        if use_date_filter:
                            col_dt1, col_dt2 = st.columns(2)
                            with col_dt1:
                                start_date = st.date_input("कब से (From Date):", value=pd.to_datetime("2024-01-01"), key="p2_start_date_secure_v18")
                            with col_dt2:
                                end_date = st.date_input("कब तक (To Date):", value=pd.to_datetime("2026-12-31"), key="p2_end_date_secure_v18")
                    else:
                        st.caption("🙈 यह सेक्शन फ़िलहाल छुपा हुआ है। (Unhide करने पर पिछली सेटिंग बनी रहेगी)")

                    use_date_filter = st.session_state.get("p2_enable_date_filter_secure_v18", False)
                    start_date = st.session_state.get("p2_start_date_secure_v18", pd.to_datetime("2024-01-01"))
                    end_date = st.session_state.get("p2_end_date_secure_v18", pd.to_datetime("2026-12-31"))
                
                    st.markdown('</div>', unsafe_allow_html=True)

                    # ==================================================================
                    # ⚡ Filters Execution Engine
                    # ==================================================================
                    admission_display_db = p2_authorized_db.copy()
                
                    if p2_filter_year != "All Years":
                        admission_display_db = admission_display_db[admission_display_db["Admission Year"] == p2_filter_year]
                
                    if p2_filter_ugpg != "All" and "Eligibility Name" in admission_display_db.columns:
                        admission_display_db = admission_display_db[admission_display_db["Eligibility Name"].apply(classify_ug_pg) == p2_filter_ugpg]
                
                    if p2_filter_subject != "All Subjects":
                        admission_display_db = admission_display_db[admission_display_db["Subject"] == p2_filter_subject]
                
                    if p2_selected_val != "All Values":
                        admission_display_db = admission_display_db[admission_display_db[p2_selected_col] == p2_selected_val]

                    if use_date_filter:
                        try:
                            admission_display_db["_parsed_date"] = pd.to_datetime(admission_display_db["Payment Date"], dayfirst=True, errors="coerce")
                            admission_display_db = admission_display_db[
                                (admission_display_db["_parsed_date"] >= pd.to_datetime(start_date)) & 
                                (admission_display_db["_parsed_date"] <= pd.to_datetime(end_date))
                            ]
                            admission_display_db = admission_display_db.drop(columns=["_parsed_date"], errors="ignore")
                        except Exception as date_err:
                            st.error(f"तिथि फ़ॉर्मेट मिलान में तकनीकी त्रुटि: {date_err}")

                    # ==================================================================
                    # ✍️ Print Header Text Boxes Customizer
                    # ==================================================================
                    st.markdown("---")
                    if "p2_show_header_customizer_section" not in st.session_state:
                        st.session_state.p2_show_header_customizer_section = True
                    hdr_pc_1, hdr_pc_2 = st.columns([6, 1])
                    with hdr_pc_1:
                        st.subheader("✍️ प्रिंट हेडर कस्टमाइज़र (Print Header Text Customizer)")
                    with hdr_pc_2:
                        st.write("")
                        if st.button("🙈 Hide" if st.session_state.p2_show_header_customizer_section else "👁️ Unhide",
                                     key="p2_toggle_header_customizer_section", use_container_width=True):
                            st.session_state.p2_show_header_customizer_section = not st.session_state.p2_show_header_customizer_section

                    # 🔄 Header 3 & Header 4 ऑटो-सिंक इंजन — जब भी ऊपर "Advanced Matrix Filters System" में
                    # Year/Subject (बॉक्स 3 के लिए) या Column Filter Target/Filter Value (बॉक्स 4 के लिए) बदलें,
                    # ये टेक्स्ट बॉक्स अपने आप नई चुनी हुई वैल्यू के हिसाब से रीफ़्रेश हो जाएंगे।
                    # (पहले सिर्फ पहली बार वाली default value सेट होती थी, बाद में year/subject बदलने पर भी
                    # बॉक्स पुरानी वैल्यू पर ही अटका रहता था — यही bug अब ठीक कर दिया गया है)
                    default_header_3 = f"Session: {p2_filter_year} | Subject: {p2_filter_subject}"
                    default_header_4 = f"{p2_selected_col}: {p2_selected_val}" if p2_selected_val != "All Values" else ""
                    default_header_ugpg = p2_filter_ugpg if p2_filter_ugpg != "All" else ""

                    _h3_track_key = "_p2_h3_last_filters"
                    if st.session_state.get(_h3_track_key) != (p2_filter_year, p2_filter_subject):
                        st.session_state["p2_custom_head_line_3_final_fixed"] = default_header_3
                        st.session_state[_h3_track_key] = (p2_filter_year, p2_filter_subject)

                    _h4_track_key = "_p2_h4_last_filters"
                    if st.session_state.get(_h4_track_key) != (p2_selected_col, p2_selected_val):
                        st.session_state["p2_custom_head_line_4_final_fixed"] = default_header_4
                        st.session_state[_h4_track_key] = (p2_selected_col, p2_selected_val)

                    # 🆕 हेडर लाइन 2 (Under Graduate/Post Graduate) — मैट्रिक्स फ़िल्टर बॉक्स 2 से अपने आप सिंक होगी।
                    # जब "All" चुना हो तो यह खाली रहेगी और प्रिंट में पूरी तरह गायब हो जाएगी (नीचे वाली लाइन ऊपर खिसक आएगी)।
                    _h_ugpg_track_key = "_p2_h_ugpg_last_filter"
                    if st.session_state.get(_h_ugpg_track_key) != p2_filter_ugpg:
                        st.session_state["p2_custom_head_line_ugpg_final_fixed"] = default_header_ugpg
                        st.session_state[_h_ugpg_track_key] = p2_filter_ugpg

                    if st.session_state.p2_show_header_customizer_section:
                        st.caption("नीचे दिए गए बॉक्स में आप जो भी लिखेंगे, वह प्रिंट रिपोर्ट के पहले पेज पर सबसे ऊपर दिखाई देगा। "
                                    "बॉक्स 2, 4 और 5 अपने आप ऊपर चुने गए Under Graduate/Post Graduate, Year/Subject और Column Filter Target/Filter Value के हिसाब से अपडेट होते हैं "
                                    "(बॉक्स 2 सिर्फ तभी दिखेगा जब 'Select Under Graduate/Post Graduate' में 'All' के अलावा कोई खास वैल्यू चुनी गई हो, और बॉक्स 5 सिर्फ तभी जब 'Filter Value for...' में 'All Values' के अलावा कोई खास वैल्यू चुनी गई हो — जरूरत न हो तो ये खाली/print में गायब रहेंगे, और उनकी जगह खाली रो नहीं बनेगी, बाकी लाइनें अपने आप ऊपर खिसक आएँगी)।")

                        col_tb1, col_tb2, col_tb3, col_tb4, col_tb5 = st.columns(5)
                        with col_tb1:
                            custom_header_1 = st.text_input("1. हेडर लाइन 1 (उदा. कॉलेज का नाम):", value="GOVT. KAMLARAJA GIRLS POST-GRADUATE AUTONOMOUS COLLEGE, GWALIOR (M.P.)", key="p2_custom_head_line_1_final_fixed")
                        with col_tb2:
                            custom_header_ugpg = st.text_input("2. Select Under Graduate/Post Graduate:", value=default_header_ugpg, key="p2_custom_head_line_ugpg_final_fixed")
                        with col_tb3:
                            custom_header_2 = st.text_input("3. हेडर लाइन 2 (उदा. रिपोर्ट का प्रकार):", value="ADMISSION LIST", key="p2_custom_head_line_2_final_fixed")
                        with col_tb4:
                            custom_header_3 = st.text_input("4. हेडर लाइन 3 (उदा. आदेश संख्या या कोई विशेष नोट):", value=default_header_3, key="p2_custom_head_line_3_final_fixed")
                        with col_tb5:
                            custom_header_4 = st.text_input(f"5. Select Column Filter Target: (Filter Value for '{p2_selected_col}'):", value=default_header_4, key="p2_custom_head_line_4_final_fixed")

                        render_print_header_style_controls()
                    else:
                        st.caption("🙈 यह सेक्शन फ़िलहाल छुपा हुआ है। (Unhide करने पर पिछली सेटिंग बनी रहेगी)")

                    custom_header_1 = st.session_state.get("p2_custom_head_line_1_final_fixed", "GOVT. K.R.G. POST-GRADUATE AUTONOMOUS COLLEGE, GWALIOR (M.P.)")
                    custom_header_ugpg = st.session_state.get("p2_custom_head_line_ugpg_final_fixed", default_header_ugpg)
                    custom_header_2 = st.session_state.get("p2_custom_head_line_2_final_fixed", "ADMISSION CONTROL & FEES PAYMENT REPORT SHEET")
                    custom_header_3 = st.session_state.get("p2_custom_head_line_3_final_fixed", default_header_3)
                    custom_header_4 = st.session_state.get("p2_custom_head_line_4_final_fixed", default_header_4)
                    header_style_css = build_print_header_css()  # 🎨 Font size + colour (print header)
                
                    # ==================================================================
                    # 👁️ NEW: Multi-Select Column Filter (कॉलम यहाँ से सेलेक्ट करें)
                    # ==================================================================
                    st.markdown("---")
                    if "p2_show_columns_section" not in st.session_state:
                        st.session_state.p2_show_columns_section = True
                    hdr_cs_1, hdr_cs_2 = st.columns([6, 1])
                    with hdr_cs_1:
                        st.subheader("👁️ Select Columns to Display & Print")
                    with hdr_cs_2:
                        st.write("")
                        if st.button("🙈 Hide" if st.session_state.p2_show_columns_section else "👁️ Unhide",
                                     key="p2_toggle_columns_section", use_container_width=True):
                            st.session_state.p2_show_columns_section = not st.session_state.p2_show_columns_section

                    # 🟢 फिक्स: यहाँ पहले कॉलम नाम असली डेटा कॉलम्स से मेल नहीं खाते थे
                    # (जैसे "Date Of Birth" vs असली कॉलम "Date of Birth", "Email" vs "Email ID",
                    # "Enrollment No" vs "Enrollment No.") — इसी वजह से DOB, Email और Enrollment No
                    # हमेशा खाली दिखते थे। अब नाम बिल्कुल सही स्कीमा फॉर्मेट में फिक्स किए गए हैं।
                    all_possible_p2_cols = [
                        "Application Number", "Student Abc Id", "Unique ID", "Roll No.", "Student Name", "Father Name", "Mother Name",
                        "Date of Birth", "Category", "Admission Category", "Subject", "Degree", "Branch",
                        "Minor Subjects", "Vocational Subjects", "MDC Subjects", "PW/Ap/CE Subjects",
                        "Mobile Number", "Email ID", "Address", "Enrollment No.", "Admssion & Enrollment Fees",
                        "Scholarship Name", "Payment Date", "Document Submit Status", "Remark"
                    ]
                    # 🆕 2.1 me mark hua "Document Submit Status" ab 2.2 me bhi ek column ke roop me dikhta hai.
                    # Purane session me multiselect ki saved list me ye column nahi hota, isliye ek baar automatically jod dete hain.
                    _ms_key = "p2_columns_multiselect_dropdown_v20"
                    if not st.session_state.get("_p2_docstatus_col_added"):
                        if _ms_key in st.session_state and "Document Submit Status" not in st.session_state[_ms_key]:
                            st.session_state[_ms_key] = list(st.session_state[_ms_key]) + ["Document Submit Status"]
                        st.session_state["_p2_docstatus_col_added"] = True
                    # 🆕 Unique ID aur Roll No. bhi ab fee ki tarah P2 me merge hokar aate hain —
                    # purane session ki saved column-list me ye dono nahi hote, isliye ek baar automatically jod dete hain.
                    if not st.session_state.get("_p2_uid_roll_cols_added"):
                        if _ms_key in st.session_state:
                            _cur_sel = list(st.session_state[_ms_key])
                            for _nc in ["Unique ID", "Roll No."]:
                                if _nc not in _cur_sel:
                                    _cur_sel.append(_nc)
                            st.session_state[_ms_key] = _cur_sel
                        st.session_state["_p2_uid_roll_cols_added"] = True

                    if st.session_state.p2_show_columns_section:
                        # ड्रॉपडाउन लिस्ट जो स्क्रीन और प्रिंट दोनों को कंट्रोल करेगी
                        chosen_render_cols = st.multiselect(
                            "रिपोर्ट में देखने के लिए आवश्यक कॉलम्स चुनें:",
                            options=all_possible_p2_cols,
                            default=all_possible_p2_cols, # डिफ़ॉल्ट रूप से सभी सेलेक्ट रहेंगे
                            key="p2_columns_multiselect_dropdown_v20"
                        )

                        # 🖨️ नया फ़ीचर: प्रिंट ओरिएंटेशन चुनने का विकल्प (Portrait / Landscape)
                        print_orientation = st.selectbox(
                            "🖨️ प्रिंट पेज का लेआउट चुनें (Choose Print Orientation):",
                            options=["Portrait (खड़ा पेज - कम कॉलम्स के लिए उत्तम)", "Landscape (आड़ा पेज - अधिक कॉलम्स के लिए उत्तम)"],
                            index=1, # डिफ़ॉल्ट रूप से Landscape सेट रहेगा
                            key="p2_print_orientation_selector"
                        )
                    else:
                        st.caption("🙈 यह सेक्शन फ़िलहाल छुपा हुआ है। (Unhide करने पर पिछली सेटिंग बनी रहेगी)")

                    chosen_render_cols = st.session_state.get("p2_columns_multiselect_dropdown_v20", all_possible_p2_cols)
                    print_orientation = st.session_state.get(
                        "p2_print_orientation_selector",
                        "Landscape (आड़ा पेज - अधिक कॉलम्स के लिए उत्तम)"
                    )

                    # सीएसएस के लिए वैल्यू सेट करना
                    orientation_css = "portrait" if "Portrait" in print_orientation else "landscape"

                    # सुरक्षा नियम: यदि सब डिलीट कर दें तो कम से कम नाम और नंबर जरूर दिखे
                    if not chosen_render_cols:
                        chosen_render_cols = ["Admission Application Number", "Student Name"]

                    # 🔀 List Order Selector — P10 जैसा ही Sort Order सिस्टम अब P2 में भी
                    p2_sort_order_choice = st.selectbox(
                        "🔀 लिस्ट किस क्रम में प्रिंट करें (Sort Order):",
                        options=[
                            "डिफ़ॉल्ट क्रम (जैसा डेटा है)",
                            "Student Name (अल्फाबेटिक A-Z क्रम में)",
                            "Subject → Student Name (पहले Subject, फिर नाम अनुसार A-Z)"
                        ],
                        key="p2_sort_order_choice"
                    )
                    if p2_sort_order_choice.startswith("Subject"):
                        # 🔤 पहले Subject के अल्फाबेटिक क्रम में, फिर उसी Subject के अंदर Student Name A-Z
                        admission_display_db["_sort_key_1"] = admission_display_db.get("Subject", "").astype(str).str.strip().str.upper()
                        admission_display_db["_sort_key_2"] = admission_display_db.get("Student Name", "").astype(str).str.strip().str.upper()
                        admission_display_db = admission_display_db.sort_values(
                            by=["_sort_key_1", "_sort_key_2"], ascending=[True, True]
                        ).drop(columns=["_sort_key_1", "_sort_key_2"]).reset_index(drop=True)
                    elif p2_sort_order_choice.startswith("Student Name"):
                        # 🔤 Alphabetical (A-Z) क्रम — Student Name के आधार पर
                        admission_display_db["_sort_key"] = admission_display_db.get("Student Name", "").astype(str).str.strip().str.upper()
                        admission_display_db = admission_display_db.sort_values(
                            by=["_sort_key"], ascending=[True]
                        ).drop(columns=["_sort_key"]).reset_index(drop=True)
                    # "डिफ़ॉल्ट क्रम" चुनने पर कोई sort नहीं होगा — डेटा जैसा है वैसा ही क्रम रहेगा

                    st.markdown("---")
                
                    # ==================================================================
                    # 📊 Data Grid Overview (स्क्रीन पर दिखने वाली एकमात्र मुख्य तालिका)
                    # ==================================================================
                    # 🟢 सुधार: दोनों नाम विविधताओं को सुरक्षित रूप से सिंक करें
                    if "Admission Application Number" in admission_display_db.columns:
                        admission_display_db["Application Number"] = admission_display_db["Admission Application Number"]
                    elif "Application Number" in admission_display_db.columns:
                        admission_display_db["Admission Application Number"] = admission_display_db["Application Number"]

                    for col in chosen_render_cols:
                        if col not in admission_display_db.columns:
                            if col == "Admission & Enrollment Fees" and "Admssion & Enrollment Fees" in admission_display_db.columns:
                                admission_display_db["Admission & Enrollment Fees"] = admission_display_db["Admssion & Enrollment Fees"]
                            else:
                                admission_display_db[col] = ""
                        
                    # 🧹 Unique ID / Roll No. jinki value merge se nahi aayi, wahan "nan" ki jagah khaali dikhe
                    for _uc in ["Unique ID", "Roll No."]:
                        if _uc in admission_display_db.columns:
                            admission_display_db[_uc] = admission_display_db[_uc].astype(str).str.strip().replace({"nan": "", "None": "", "NaN": ""})
                    final_p2_render = admission_display_db[chosen_render_cols].copy()
                
                    # 🟢 पुराना रीनेम कोड हटाकर इसे पूरी तरह साफ़ और सुरक्षित किया गया
                    final_p2_render = final_p2_render.loc[:, ~final_p2_render.columns.duplicated()].copy()
                
                    if not final_p2_render.empty:
                        final_p2_render.insert(0, "S. No.", range(1, len(final_p2_render) + 1))
                
                    st.write(f"ग्रिड में प्रदर्शित कुल छात्र रिकॉर्ड संख्या: **{len(final_p2_render)}**")
                
                    # ==================================================================
                    # ✏️ कॉलम नाम एडिटर — जिस भी कॉलम का नाम (हेडर) बदलना हो, यहाँ से बदलें
                    # (सिर्फ़ स्क्रीन/प्रिंट/डाउनलोड में दिखने वाला नाम बदलता है, असली डेटा कॉलम सुरक्षित रहता है)
                    # ==================================================================
                    def render_column_name_editor(df_in, section_key):
                        """
                        Har column ke liye ek chhota text box deta hai jisse uska display
                        naam (header) badla ja sake. Return: renamed dataframe.
                        Original data / underlying column names change nahi hote — sirf
                        is table (screen + print + download) me dikhne wala label badalta hai.
                        """
                        rename_map_key = f"{section_key}_rename_map"
                        if rename_map_key not in st.session_state:
                            st.session_state[rename_map_key] = {}

                        with st.expander("✏️ कॉलम नाम एडिटर (Edit Column Header Names)", expanded=False):
                            st.caption("नीचे जिस कॉलम का नाम बदलना है, उसके सामने नया नाम लिखें। खाली छोड़ने पर पुराना नाम ही रहेगा।")
                            editable_cols = [c for c in df_in.columns if c != "S. No."]
                            new_names = {}
                            n_per_row = 3
                            for i in range(0, len(editable_cols), n_per_row):
                                row_cols = st.columns(n_per_row)
                                for j, orig_col in enumerate(editable_cols[i:i + n_per_row]):
                                    with row_cols[j]:
                                        current_label = st.session_state[rename_map_key].get(orig_col, orig_col)
                                        new_val = st.text_input(
                                            f"'{orig_col}' का नया नाम:",
                                            value=current_label,
                                            key=f"{section_key}_rename_{orig_col}"
                                        )
                                        new_names[orig_col] = new_val.strip() if new_val.strip() else orig_col
                            if st.button("✅ नाम लागू करें (Apply Names)", key=f"{section_key}_apply_rename_btn"):
                                st.session_state[rename_map_key] = new_names
                                st.rerun()
                            if st.session_state[rename_map_key]:
                                if st.button("↩️ मूल नाम पर वापस जाएँ (Reset Names)", key=f"{section_key}_reset_rename_btn"):
                                    st.session_state[rename_map_key] = {}
                                    st.rerun()

                        active_map = {k: v for k, v in st.session_state[rename_map_key].items() if k in df_in.columns}
                        return df_in.rename(columns=active_map) if active_map else df_in.copy()

                    final_p2_render = render_column_name_editor(final_p2_render, "p2_grid")

                    # ==================================================================
                    # 📐 Remark कॉलम का साइज़ (Width / Height) खुद तय करें
                    # ==================================================================
                    remark_display_label = st.session_state.get("p2_grid_rename_map", {}).get("Remark", "Remark")
                    if remark_display_label in final_p2_render.columns:
                        with st.expander("📐 Remark कॉलम का साइज़ सेट करें (Set Remark Column Width/Height)", expanded=False):
                            size_c1, size_c2 = st.columns(2)
                            with size_c1:
                                remark_width_px = st.slider(
                                    "↔️ Remark कॉलम की चौड़ाई (Width in px):",
                                    min_value=60, max_value=500, value=st.session_state.get("p2_remark_width_px", 180),
                                    step=10, key="p2_remark_width_px"
                                )
                            with size_c2:
                                remark_height_px = st.slider(
                                    "↕️ Remark के लिए अतिरिक्त ऊँचाई (Extra Height in px — 0 = कोई खाली जगह नहीं, सिर्फ़ प्रिंट में लागू होगी):",
                                    min_value=0, max_value=100, value=st.session_state.get("p2_remark_height_px", 0),
                                    step=4, key="p2_remark_height_px"
                                )
                    else:
                        remark_width_px = st.session_state.get("p2_remark_width_px", 180)
                        remark_height_px = st.session_state.get("p2_remark_height_px", 0)

                    # 🌟 स्क्रीन की एकमात्र मुख्य ग्रिड तालिका — "Remark" कॉलम यहीं से लिखा/एडिट किया जा सकता है
                    lockable_cols = [c for c in final_p2_render.columns if c != remark_display_label]
                    if remark_display_label in final_p2_render.columns:
                        # स्क्रीन ग्रिड में Remark कॉलम की चौड़ाई लागू करना (small/medium/large के रूप में मैप करके)
                        remark_width_bucket = "small" if remark_width_px < 130 else ("large" if remark_width_px > 280 else "medium")
                        try:
                            remark_col_config = {
                                remark_display_label: st.column_config.TextColumn(remark_display_label, width=remark_width_bucket)
                            }
                        except Exception:
                            remark_col_config = None

                        edited_p2_render = st.data_editor(
                            final_p2_render,
                            use_container_width=True,
                            hide_index=True,
                            disabled=lockable_cols,
                            column_config=remark_col_config,
                            key="p2_remark_live_editor_grid"
                        )
                        if st.button("💾 Remark सुरक्षित करें (Save Remarks)", key="p2_save_remark_btn", use_container_width=True):
                            try:
                                app_no_col = "Admission Application Number" if "Admission Application Number" in edited_p2_render.columns \
                                    else ("Application Number" if "Application Number" in edited_p2_render.columns else None)
                                if app_no_col is None:
                                    st.error("Remark सेव करने के लिए 'Application Number' कॉलम चुना होना ज़रूरी है (ऊपर 'Select Columns to Display & Print' में जोड़ें).")
                                else:
                                    remark_sync_counter = 0
                                    for _, r_row in edited_p2_render.iterrows():
                                        target_app_no = str(r_row[app_no_col]).strip()
                                        remark_val = str(r_row[remark_display_label]).strip()
                                        idx_matches = live_db[live_db["Admission Application Number"].astype(str).str.strip() == target_app_no].index
                                        if not idx_matches.empty:
                                            if "Remark" not in live_db.columns:
                                                live_db["Remark"] = ""
                                            for match_idx in idx_matches:
                                                live_db.at[match_idx, "Remark"] = remark_val
                                                remark_sync_counter += 1
                                    save_live_data(live_db)
                                    st.success(f"🎉 {remark_sync_counter} छात्र रिकॉर्ड्स की Remark मुख्य डेटाबेस में सुरक्षित हो गई है।")
                                    st.rerun()
                            except Exception as remark_err:
                                st.error(f"Remark सेव करने में समस्या आई: {remark_err}")
                        final_p2_render = edited_p2_render
                    else:
                        st.dataframe(final_p2_render, use_container_width=True, hide_index=True)

                    # ==================================================================
                    # 📥 Excel Download — ऊपर चुने गए कॉलम्स + Sort Order + Filters के अनुसार ही (जैसा ग्रिड में दिख रहा है)
                    # ==================================================================
                    if not final_p2_render.empty:
                        try:
                            p2_excel_bytes = dataframe_to_excel_bytes(final_p2_render, "Admission List")
                            st.download_button(
                                label="📥 Download Excel File (.xlsx) — चुने हुए कॉलम्स के साथ",
                                data=p2_excel_bytes,
                                file_name=f"admission_list_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True,
                                key="p2_download_excel_btn"
                            )
                        except Exception as p2_xl_err:
                            st.error(f"Excel फ़ाइल बनाने में समस्या आई: {p2_xl_err} (requirements.txt में `openpyxl` जोड़ें)")

                    # ==================================================================
                    # 🖨️ Clean Variable-Based Iframe Print Engine (Dynamic Layout Fix)
                    # ==================================================================
                    if not final_p2_render.empty:
                        columns_list = list(final_p2_render.columns)
                        records_list = final_p2_render.to_dict(orient="records")
                    
                        # 📐 Remark कॉलम के लिए तय की गई चौड़ाई यहाँ प्रिंट टेबल पर लागू होती है
                        _remark_col_style = f"width:{remark_width_px}px; max-width:{remark_width_px}px;"
                        _remark_cell_style = "word-wrap:break-word; white-space:normal;"

                        # 🟢 फिक्स: सभी रो का साइज़ एक-समान (compact) रखने के लिए कम padding + line-height,
                        # और हर <tr> को "page-break-inside: avoid" ताकि कोई रो बीच में कटे नहीं
                        _uniform_row_style = "padding:3px 5px; line-height:1.25; page-break-inside:avoid;"

                        # 🟢 फिक्स: सिर्फ़ Remark सेल पर "min-height" लगाने पर कई प्रिंट/iframe इंजन में
                        # रो की ऊँचाई नहीं बढ़ती थी। अब जब स्लाइडर 0 से ज़्यादा हो, तो पूरी <tr> और उसके
                        # हर सेल पर सीधे "height" लगाया जाता है — यह हर ब्राउज़र में भरोसेमंद तरीक़े से काम करता है।
                        _row_height_style = f"height:{remark_height_px}px;" if remark_height_px > 0 else ""

                        def _th_style(col_name):
                            base = f"border:1px solid #111; {_uniform_row_style} background:#f2f2f2; font-weight:bold; text-align:center; vertical-align:top;"
                            return base + (" " + _remark_col_style if col_name == remark_display_label else "")

                        # 🟢 नया: जिस भी सेल की वैल्यू सिर्फ़ एक नंबर (जैसे "13", "8319564700") हो,
                        # वह अपने आप बीच में (center) दिखेगी — बाकी टेक्स्ट वाली सेल्स पहले जैसे left में ही रहेंगी
                        def _is_pure_number(v):
                            v = v.strip()
                            return v != "" and v.replace(".", "", 1).replace("-", "", 1).isdigit()

                        def _td_style(col_name, cell_val=""):
                            align = "center" if (col_name == "S. No." or _is_pure_number(cell_val)) else "left"
                            base = f"border:1px solid #111; {_uniform_row_style} {_row_height_style} text-align:{align}; vertical-align:top;"
                            return base + (" " + _remark_col_style + " " + _remark_cell_style if col_name == remark_display_label else "")

                        headers_html = "".join([f"<th style='{_th_style(col)}'>{col}</th>" for col in columns_list])
                    
                        rows_html = ""
                        for row in records_list:
                            rows_html += f"<tr style='page-break-inside: avoid; {_row_height_style}'>"
                            for col in columns_list:
                                val = str(row.get(col, "")).replace("`", "'").replace("\n", " ")
                                rows_html += f"<td style='{_td_style(col, val)}'>{val}</td>"
                            rows_html += "</tr>"
                    
                        clean_table_html = f"""
                        <html>
                        <head>
                            <style>
                                @page {{
                                    size: A4 {orientation_css};
                                    margin: 8mm 8mm 14mm 8mm;
                                }}
                                /* 🔢 पेज नंबर — पेज के नीचे बीच में (सपोर्टेड ब्राउज़र्स में अपने-आप हर पेज पर दिखेगा) */
                                @page {{
                                    @bottom-center {{
                                        content: "Page No. " counter(page) " / " counter(pages);
                                        font-size: 10px;
                                        font-family: Arial, sans-serif;
                                        color: #333;
                                    }}
                                }}
                                body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; color: #000; }}
                                .custom-print-header {{
                                    width: 100%; border: 2px solid #0F2A4A; background-color: #EEF2F8;
                                    padding: 15px; margin-bottom: 20px; border-radius: 6px;
                                    box-sizing: border-box; text-align: center;
                                }}
                                {header_style_css}
                                table {{ width: 100%; border-collapse: collapse; font-size: 11px; margin-top: 10px; page-break-inside: auto; }}
                                thead {{ display: table-header-group; }}
                                tr {{ page-break-inside: avoid; page-break-after: auto; }}
                            </style>
                        </head>
                        <body>
                            <div class="custom-print-header">
                                <div class="h-line-1">{custom_header_1}</div>
                                {f'<div class="h-line-ugpg">{custom_header_ugpg}</div>' if custom_header_ugpg and custom_header_ugpg.strip() else ''}
                                <div class="h-line-2">{custom_header_2}</div>
                                <div class="h-line-3">{custom_header_3}</div>
                                {f'<div class="h-line-4">{custom_header_4}</div>' if custom_header_4 and custom_header_4.strip() else ''}
                            </div>
                            <table>
                                <thead><tr>{headers_html}</tr></thead>
                                <tbody>{rows_html}</tbody>
                            </table>
                        </body>
                        </html>
                        """
                    
                        safe_html_string = clean_table_html.replace("\\", "\\\\").replace("`", "'").replace("\n", " ").replace("\r", "")
                    
                        # 🟢 यहाँ इंडेंटेशन फिक्स किया गया है (16 Spaces / 4 Tabs)
                        st.markdown('<div class="print-hide" style="margin-top: 20px;"></div>', unsafe_allow_html=True)
                    
                        # प्रिंट बटन जो सीधे बैकएंड से कनेक्टेड है
                        components.html(
                            f"""
                            <html>
                            <body>
                                <script>
                                function printAdmissionList() {{
                                    var iframe = window.parent.document.createElement('iframe');
                                    iframe.style.position = 'fixed'; iframe.style.right = '0'; iframe.style.bottom = '0';
                                    iframe.style.width = '0'; iframe.style.height = '0'; iframe.style.border = '0';
                                    window.parent.document.body.appendChild(iframe);
                                
                                    var doc = iframe.contentWindow.document;
                                    doc.open(); doc.write(`{safe_html_string}`); doc.close();
                                    iframe.contentWindow.focus(); iframe.contentWindow.print();
                                
                                    setTimeout(function() {{ window.parent.document.body.removeChild(iframe); }}, 1000);
                                }}
                                </script>
                                <button onclick="printAdmissionList()" style="
                                    width: 100%; background-color: #0F2A4A; color: white; padding: 14px; 
                                    border: none; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 16px;
                                    font-family: sans-serif; box-shadow: 0 4px 6px rgba(20, 101, 222, 0.2);">
                                    🖨️ Click Here to Print Admission & Payment Report Sheet
                                </button>
                            </body>
                            </html>
                            """,
                            height=70
                        )

        # ----------------------------------------------------------------------
        # P3: UG / PG CHECKING APP (app__75_.py का पूरा कोड — ऊपर _run_p3_ug_pg_app() फ़ंक्शन में मौजूद है)
        # ----------------------------------------------------------------------
        elif current_panel_id == "P3":
            try:
                _run_p3_ug_pg_app(_P3StProxy(st, {
                    "stop": _p3_stop,
                    "set_page_config": (lambda *a, **k: None),
                    "sidebar": _P3LazySidebar(),
                }))
            except _P3SubAppStop:
                pass

        # ----------------------------------------------------------------------
        # P4: PANEL ROLL NO MODULE (University Roll Number Allocation Engine)
        # ----------------------------------------------------------------------
        elif current_panel_id == "P4":
            st.header(f"🔢 {get_panel_title('P4')} (University Roll Number Allocation Engine)")
            
            # 🔍 Isolated Firewall Query Filter Rule: Only show records explicitly routed to P4
            p4_authorized_db = live_db[live_db["Target Panel Visibility"] == "P4"].copy()
            
            if p4_authorized_db.empty: 
                st.warning("⚠️ इस पैनल के लिए कोई अधिकृत स्वीकृत (Approved) डेटा उपलब्ध नहीं है। कृपया P13 पैनल से डेटा अप्रूव करें।")
            else:
                # 🟢 सही किया गया कोड (यह सुरक्षित सिंगल-लाइन स्ट्रिंग फॉर्मेट में है)
                st.markdown(
                    '<div style="background-color: #f7f9fa; border-left: 5px solid #28a745; padding: 10px; border-radius: 4px; margin-bottom: 15px;">'
                    '📌 <b>ऑपरेटर निर्देश:</b> इस ग्रिड में विश्वविद्यालय रोल नंबर (Roll No.) से संबंधित डेटा प्रदर्शित है। सुरक्षा नियमों के अनुसार केवल सुपर एडमिन ही इसमें बदलाव कर सकता है।'
                    '</div>', 
                    unsafe_allow_html=True
                )
                
                # 🔍 Real-time Search Filter Sub-system
                col_r1, col_r2 = st.columns(2)
                with col_r1:
                    roll_search_field = st.selectbox("खोजने का माध्यम चुनें (Filter By):", ["Student Name", "Unique ID", "Admission Application Number"], key="p4_search_field_secure")
                with col_r2:
                    roll_search_query = st.text_input(f"यहाँ {roll_search_field} प्रविष्टि खोजें:", key="p4_search_query_secure").strip()
                
                # Filter records based on active user query input
                roll_filter_df = p4_authorized_db.copy()
                if roll_search_query != "":
                    roll_filter_df = roll_filter_df[
                        roll_filter_df[roll_search_field].astype(str).str.contains(roll_search_query, case=False, na=False)
                    ]
                
                # Standardized 22 columns layout mapping configuration for P4 Workspace
                roll_fixed_cols = [
                    "Admission Application Number", "Roll No.", "Unique ID", "Enrollment No.", "Student Name", "Father Name", 
                    "Admission Year", "Admission Session", "Eligibility Name", "Admission Date", "Application Enrollment No.", 
                    "Mother Name", "Date of Birth", "Category", "Subject", "Duration", "Mobile Number", "Email ID", 
                    "Address", "Status", "Current Year", "Payment Date"
                ]
                
                # Fallback translation maps to catch old column variations automatically
                column_mapping_fixes = {
                    "Unique Id": "Unique ID", "Student Abc Id": "Unique ID", 
                    "Date Of Birth": "Date of Birth", "Duretion": "Duration", 
                    "Email Id": "Email ID", "Year": "Current Year",
                    "Application Number": "Admission Application Number"
                }
                roll_filter_df = roll_filter_df.rename(columns=column_mapping_fixes)
                
                # Ensure all target columns exist cleanly to bypass blank key runtime errors
                for col in roll_fixed_cols:
                    if col not in roll_filter_df.columns:
                        roll_filter_df[col] = ""
                
                render_df = roll_filter_df[roll_fixed_cols].copy()
                render_df.insert(0, "S. No.", range(1, len(render_df) + 1))
                
                st.write(f"ग्रिड में प्रदर्शित कुल मैचिंग छात्र रिकॉर्ड संख्या (Active Matrix Records): **{len(render_df)}**")
                
                # Access guard constraints setup depending on session user role attributes
                if role == "full_admin":
                    disabled_cols = [c for c in render_df.columns if c != "Roll No."]
                    st.info("🔓 **एडमिन कंट्रोल मोड:** आपके पास विश्वविद्यालय रोल नंबर एडिट और सिंक करने का पूर्ण अधिकार है।")
                else:
                    disabled_cols = [c for c in render_df.columns]
                    st.warning("🔒 **रीड-ओनली मोड:** सुरक्षा कारणों से आपके पास इस लिस्ट में Roll No. बदलने का अधिकार नहीं है।")
                
                # Live dynamic spreadsheet data editor canvas interface
                edited_roll_df = st.data_editor(
                    render_df, 
                    use_container_width=True, 
                    disabled=disabled_cols, 
                    key="roll_live_editor_grid_p4_secure_engine", 
                    hide_index=True
                )
                
                # Synchronization engine to sync and save custom adjustments securely to main live database
                if role == "full_admin":
                    if st.button("Save & Sync Roll Numbers", type="primary", use_container_width=True, key="p4_save_btn_secure"):
                        try:
                            clean_edited = edited_roll_df.drop(columns=["S. No."], errors="ignore")
                            roll_sync_counter = 0
                            
                            for _, row_edit in clean_edited.iterrows():
                                target_app_num = str(row_edit["Admission Application Number"]).strip()
                                roll_number_val = str(row_edit["Roll No."]).strip()
                                
                                idx_matches = live_db[live_db["Application Number"].astype(str).str.strip() == target_app_num].index
                                
                                if not idx_matches.empty:
                                    for match_idx in idx_matches:
                                        live_db.at[match_idx, "Roll No."] = roll_number_val
                                        roll_sync_counter += 1
                            
                            save_live_data(live_db)
                            st.success(f"🎉 सफलता! कुल {roll_sync_counter} छात्र रिकॉर्ड्स की Roll No. मुख्य डेटाबेस (Live CSV) में सफलतापूर्वक सिंक हो गई है।")
                            st.rerun()
                        except Exception as e:
                            st.error(f"डेटाबेस सिंक्रोनाइज़ेशन चक्र में तकनीकी समस्या आई: {e}")

        # ----------------------------------------------------------------------
        # P5: PANEL ENROLLMENT MODULE (University Enrollment Manager)
        # ----------------------------------------------------------------------
        elif current_panel_id == "P5":
            st.header(f"📑 {get_panel_title('P5')} (University Enrollment Manager)")
            
            # 🔍 Isolated Firewall Query Filter Rule: Only show records explicitly approved for P5
            p5_authorized_db = live_db[live_db["Target Panel Visibility"] == "P5"].copy()
            
            if p5_authorized_db.empty: 
                st.warning("⚠️ इस पैनल के लिए कोई अधिकृत स्वीकृत (Approved) डेटा उपलब्ध नहीं है। कृपया पहले P13 (Merge Panel) से डेटा को इस पैनल पर असाइन कर अप्रूव करें।")
            else:
                # 🟢 सही किया गया कोड
                st.markdown(
                    '<div style="background-color: #fff9e6; border-left: 5px solid #ffc107; padding: 10px; border-radius: 4px; margin-bottom: 15px;">'
                    '📌 <b>ऑपरेटर निर्देश:</b> इस ग्रिड में विश्वविद्यालय नामांकन (Enrollment No) से संबंधित डेटा प्रदर्शित है। सुरक्षा नियमों के अनुसार केवल सुपर एडमिन ही इसमें बदलाव कर सकता है।'
                    '</div>', 
                    unsafe_allow_html=True
                )
                
                # Fallback dictionary to translate legacy/alternate columns to core fields
                column_mapping_fixes = {
                    "Unique Id": "Unique ID", "Student Abc Id": "Unique ID", 
                    "Date Of Birth": "Date of Birth", "Duretion": "Duration", 
                    "Email Id": "Email ID", "Year": "Current Year",
                    "Application Number": "Admission Application Number"
                }
                p5_authorized_db = p5_authorized_db.rename(columns=column_mapping_fixes)

                # Branch field tracking check to build fallback subject isolation filters safely
                branch_key = "Branch" if "Branch" in p5_authorized_db.columns else "Subject"
                available_subjects = ["All"] + sorted(list(set(p5_authorized_db[branch_key].dropna().astype(str).str.strip())))
                selected_subject = st.selectbox("Branch (शाखा) / Subject फ़िल्टर चुनें:", options=available_subjects, key="p5_subject_filter_secure_select")
                
                # Filter rows based on branch/subject criteria
                filtered_enrollment = p5_authorized_db.copy()
                if selected_subject != "All": 
                    filtered_enrollment = filtered_enrollment[filtered_enrollment[branch_key].str.strip() == selected_subject]
                
                # Standardized 22 columns layout matrix for P5 workspace configuration
                enrollment_fixed_cols = [
                    "Admission Application Number", "Enrollment No.", "Roll No.", "Unique ID", "Student Name", "Father Name",
                    "Admission Year", "Admission Session", "Eligibility Name", "Admission Date", "Application Enrollment No.", 
                    "Mother Name", "Date of Birth", "Category", "Subject", "Duration", 
                    "Mobile Number", "Email ID", "Address", "Status", "Current Year", "Payment Date"
                ]
                
                # Bypassing missing structural field errors with string allocations
                for col in enrollment_fixed_cols:
                    if col not in filtered_enrollment.columns:
                        filtered_enrollment[col] = ""
                        
                render_df = filtered_enrollment[enrollment_fixed_cols].copy()
                render_df.insert(0, "S. No.", range(1, len(render_df) + 1))
                
                st.write(f"ग्रिड में प्रदर्शित कुल छात्र रिकॉर्ड संख्या (Active Enrollment Records): **{len(render_df)}**")
                
                # 🔐 Access Restriction Interface (Security Gateway)
                if role == "full_admin":
                    # Admins have interactive editing permissions isolated to the Enrollment No field
                    disabled_cols = [c for c in render_df.columns if c != "Enrollment No."]
                    st.info("🔓 **एडमिन कंट्रोल मोड:** आपके पास विश्वविद्यालय नामांकन संख्या (Enrollment No) एडिट और सिंक करने का पूर्ण अधिकार है।")
                else:
                    # Regular operators receive a comprehensive read-only view of the dataset layout
                    disabled_cols = [c for c in render_df.columns]
                    st.warning("🔒 **रीड-ओनली मोड:** सुरक्षा कारणों से आपके पास इस लिस्ट में नामांकन संख्या बदलने का अधिकार नहीं है।")
                
                # Render interactive workspace spreadsheet data editor
                edited_enrollment_df = st.data_editor(
                    render_df, 
                    use_container_width=True, 
                    disabled=disabled_cols, 
                    column_config={
                        "Enrollment No.": st.column_config.TextColumn(
                            "University Enrollment No", 
                            help="विश्वविद्यालय द्वारा आवंटित स्थायी नामांकन संख्या दर्ज करें"
                        )
                    },
                    key="enrollment_live_editor_grid_p5_secure_engine", 
                    hide_index=True
                )
                
                # Commit updates engine to synchronize state with core spreadsheet CSV files
                if role == "full_admin":
                    if st.button("Save & Sync Enrollment Numbers", type="primary", use_container_width=True, key="p5_save_btn_secure_tracker"):
                        try:
                            clean_edited = edited_enrollment_df.drop(columns=["S. No."], errors="ignore")
                            enroll_sync_counter = 0
                            
                            for _, row_edit in clean_edited.iterrows():
                                app_num = str(row_edit["Admission Application Number"]).strip()
                                
                                # Locating exact records via Application Number references
                                idx_matches = live_db[live_db["Application Number"].astype(str).str.strip() == app_num].index
                                
                                if not idx_matches.empty:
                                    for match_idx in idx_matches:
                                        live_db.at[match_idx, "Enrollment No."] = str(row_edit["Enrollment No."]).strip()
                                        enroll_sync_counter += 1
                            
                            # Commit modifications to storage file permanently
                            save_live_data(live_db)
                            st.success(f"🎉 सफलता! कुल {enroll_sync_counter} छात्र रिकॉर्ड्स का विश्वविद्यालय नामांकन नंबर मुख्य डेटाबेस (Live CSV) में सिंक और अपडेट हो गया है!")
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"डेटा सिंक्रोनाइज़ेशन चक्र में तकनीकी समस्या आई: {e}")

        # ----------------------------------------------------------------------
        # P6: PANEL SCHOLARSHIP MODULE (Portal & Scholarship Tracker)
        # ----------------------------------------------------------------------
        elif current_panel_id == "P6":
            st.header(f"💰 {get_panel_title('P6')} (Portal & Scholarship Tracker)")
            
            # Ensure the tracking fallback status column exists inside the master dataframe array
            if "Scholarship Status" not in live_db.columns: 
                live_db["Scholarship Status"] = "Not Applied"
                
            # 🔍 Isolated Firewall Query Filter Rule: Only fetch records explicitly approved for P6
            p6_authorized_db = live_db[live_db["Target Panel Visibility"] == "P6"].copy()
            
            if p6_authorized_db.empty:
                st.warning("⚠️ इस पैनल के लिए कोई अधिकृत स्वीकृत (Approved) डेटा उपलब्ध नहीं है। कृपया पहले P13 (Merge Panel) से डेटा को इस पैनल पर असाइन कर अप्रूव करें।")
            else:
                # 🟢 सही किया गया कोड
                st.markdown(
                    '<div style="background-color: #f4fbf7; border-left: 5px solid #2e7d32; padding: 10px; border-radius: 4px; margin-bottom: 15px;">'
                    '📌 <b>ऑपरेटर निर्देश:</b> इस ग्रिड में छात्रवृत्ति प्रोग्रेस (Scholarship Status) से संबंधित डेटा प्रदर्शित है। सुरक्षा नियमों के अनुसार केवल सुपर एडमिन ही इसमें बदलाव कर सकता है।'
                    '</div>', 
                    unsafe_allow_html=True
                )
                
                # Normalise alternate column structural headers to match baseline fields smoothly
                column_mapping_fixes = {
                    "Unique Id": "Unique ID", "Student Abc Id": "Unique ID", 
                    "Date Of Birth": "Date of Birth", "Duretion": "Duration", 
                    "Email Id": "Email ID", "Year": "Current Year",
                    "Application Number": "Admission Application Number"
                }
                p6_authorized_db = p6_authorized_db.rename(columns=column_mapping_fixes)

                # Isolate unique list categories to build search shorting options cleanly
                available_categories = ["All"] + sorted(list(set(p6_authorized_db["Category"].dropna().astype(str).str.strip())))
                selected_category = st.selectbox("Category (वर्ग) फ़िल्टर चुनें:", options=available_categories, key="p6_category_filter_secure_select_box")
                
                # Apply row shorting filters based on category criteria selection
                filtered_scholarship = p6_authorized_db.copy()
                if selected_category != "All": 
                    filtered_scholarship = filtered_scholarship[filtered_scholarship["Category"].str.strip() == selected_category]
                
                # Standardized 22 columns layout matrix + 1 interactive cell for operations comfort
                scholarship_fixed_cols = [
                    "Admission Application Number", "Scholarship Status", "Scholarship Name", "Unique ID", "Roll No.", "Enrollment No.",
                    "Student Name", "Father Name", "Admission Year", "Admission Session", "Eligibility Name", "Admission Date", 
                    "Application Enrollment No.", "Mother Name", "Date of Birth", "Category", "Subject", "Duration", 
                    "Mobile Number", "Email ID", "Address", "Status", "Current Year", "Payment Date"
                ]
                
                # Pre-populate missing structural columns with placeholders to bypass layout crashes
                for col in scholarship_fixed_cols:
                    if col not in filtered_scholarship.columns:
                        filtered_scholarship[col] = ""
                
                render_df = filtered_scholarship[scholarship_fixed_cols].copy()
                render_df.insert(0, "S. No.", range(1, len(render_df) + 1))
                
                st.write(f"ग्रिड में प्रदर्शित कुल सक्रिय रिकॉर्ड संख्या (Active Matrix Profiles): **{len(render_df)}**")
                
                # 🔐 Access Restriction Interface (Security Gateway)
                if role == "full_admin" or role == "p6_role":
                    # Admins and designated operators can interactively modify the Scholarship Status field
                    disabled_cols = [c for c in render_df.columns if c != "Scholarship Status"]
                    st.info("🔓 **एडमिन कंट्रोल मोड:** आपके पास छात्रवृत्ति ट्रैकिंग मैट्रिक्स (Scholarship Status) एडिट और सिंक करने का पूर्ण अधिकार है।")
                else:
                    # Regular viewers get a protected comprehensive spreadsheet canvas layout
                    disabled_cols = [c for c in render_df.columns]
                    st.warning("🔒 **रीड-ओनली मोड:** सुरक्षा कारणों से आपके पास इस लिस्ट में छात्रवृत्ति स्थिति बदलने का अधिकार नहीं है।")
                
                # Render interactive workspace spreadsheet data editor with custom selection menus
                edited_scholarship_df = st.data_editor(
                    render_df, 
                    use_container_width=True, 
                    disabled=disabled_cols, 
                    column_config={
                        "Scholarship Status": st.column_config.SelectboxColumn(
                            "Scholarship Status", 
                            options=["Not Applied", "Applied", "Sanctioned", "Disbursed", "Rejected"],
                            required=True,
                            help="छात्रवृत्ति आवेदन की वर्तमान स्थिति चुनें"
                        )
                    }, 
                    key="scholarship_live_editor_grid_p6_secure_engine", 
                    hide_index=True
                )
                
                # Commit updates engine to synchronize state modifications with core live datasets
                if role == "full_admin" or role == "p6_role":
                    if st.button("Save & Sync Scholarship Matrix", type="primary", use_container_width=True, key="p6_save_btn_secure_tracker_engine"):
                        try:
                            clean_edited = edited_scholarship_df.drop(columns=["S. No."], errors="ignore")
                            scholarship_sync_counter = 0
                            
                            for _, row_edit in clean_edited.iterrows():
                                app_num = str(row_edit["Admission Application Number"]).strip()
                                
                                # Locating matching data indexes using internal primary Application Key references
                                idx_matches = live_db[live_db["Application Number"].astype(str).str.strip() == app_num].index
                                
                                if not idx_matches.empty:
                                    for match_idx in idx_matches:
                                        live_db.at[match_idx, "Scholarship Status"] = str(row_edit["Scholarship Status"]).strip()
                                        scholarship_sync_counter += 1
                            
                            # Save modifications permanently to the CSV file repository
                            save_live_data(live_db)
                            st.success(f"🎉 सफलता! कुल {scholarship_sync_counter} छात्र रिकॉर्ड्स का छात्रवृत्ति स्टेटस डेटा मुख्य डेटाबेस (Live CSV) में सुरक्षित सिंक हो गया है!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"डेटा सिंक्रोनाइज़ेशन चक्र में तकनीकी समस्या आई: {e}")

        # ----------------------------------------------------------------------
        # P7: PANEL CCE DESK (Strict 22-Cols Selection, Map & Custom Foil System)
        # ----------------------------------------------------------------------
        elif current_panel_id == "P7":
            st.header(f"📋 {get_panel_title('P7')} (Complete CCE Management & Foil Desk)")
            
            # सुनिश्चित करें कि मार्क्स वाले कॉलम डेटाबेस स्कीमा में मौजूद हों
            for f in ["CCE Marks Obtained", "CCE Attendance Status"]:
                if f not in live_db.columns: 
                    live_db[f] = ""
            
            p7_authorized_db = live_db.copy()

            if p7_authorized_db.empty: 
                st.warning("⚠️ इस पैनल के लिए कोई अधिकृत स्वीकृत (Approved) डेटा उपलब्ध नहीं है।")
            else:
                # ------------------------------------------------------------------
                # भाग 1: 22-कॉलम छात्र सूची और लाइव असेसमेंट एंट्री ग्रिड
                # ------------------------------------------------------------------
                st.markdown('<div class="print-hide">', unsafe_allow_html=True)
                st.subheader("📝 1. CCE Data Entry Desk & 22-Columns Student List")
                
                st.markdown(
                    '<div style="background-color: #f1f8e9; border-left: 5px solid #558b2f; padding: 10px; border-radius: 4px; margin-bottom: 15px;">'
                    '📌 <b>डेटा एंट्री निर्देश:</b> नीचे दी गयी तालिका में छात्र के नाम के आगे सीधे <b>CCE Marks Obtained</b> और <b>CCE Attendance Status</b> भरें। बदलाव करने के बाद <b>Save Grid Changes</b> बटन को ज़रूर दबाएं।'
                    '</div>', 
                    unsafe_allow_html=True
                )
                st.markdown('</div>', unsafe_allow_html=True)
                
                # आपके द्वारा मांगे गए सटीक 22 कॉलम का फ़्रेमवर्क
                cce_requested_cols = [
                    "Admission Year", "Admission Session", "Eligibility Name", "Admission Application Number", 
                    "Admission Date", "Unique ID", "Roll No.", "Application Enrollment No.", "Enrollment No.", 
                    "Student Name", "Father Name", "Mother Name", "Date of Birth", "Category", "Subject",
                    "Branch", "Minor Subjects", "Vocational Subjects", "MDC Subjects", "PW/Ap/CE Subjects",
                    "Duration", "Mobile Number", "Email ID", "Address", "Current Year", "Status",
                    "CCE Marks Obtained", "CCE Attendance Status"
                ]

                # स्पेलिंग्स और विसंगतियों को ठीक करने के लिए ट्रांसलेशन मैप
                column_mapping_fixes = {
                    "Unique Id": "Unique ID", "Student Abc Id": "Unique ID", "Unique ID": "Unique ID",
                    "Date Of Birth": "Date of Birth", "Date of Birth": "Date of Birth",
                    "Duretion": "Duration", "Duration": "Duration",
                    "Email Id": "Email ID", "Email ID": "Email ID", 
                    "Year": "Current Year", "Current Year": "Current Year",
                    "Application Number": "Admission Application Number", "Admission Application Number": "Admission Application Number",
                    "Enrollment No": "Enrollment No.", "Enrollment No.": "Enrollment No."
                }
                
                filtered_cce = p7_authorized_db.copy()
                filtered_cce = filtered_cce.rename(columns=column_mapping_fixes)

                if "Application Number" in filtered_cce.columns and "Admission Application Number" not in filtered_cce.columns:
                    filtered_cce["Admission Application Number"] = filtered_cce["Application Number"]
                if "Year" in filtered_cce.columns and "Current Year" not in filtered_cce.columns:
                    filtered_cce["Current Year"] = filtered_cce["Year"]

                for col in cce_requested_cols:
                    if col not in filtered_cce.columns: 
                        filtered_cce[col] = ""
                
                # केवल वही 22 कॉलम छाँटें
                render_df = filtered_cce[cce_requested_cols].copy()
                render_df = render_df.loc[:, ~render_df.columns.duplicated()].copy()

                # 🎓 render_df me "Degree" column nahi hota, isliye Format 4 ke Degree filter ke liye alag se bacha ke rakho
                _fc_unique = filtered_cce.loc[:, ~filtered_cce.columns.duplicated()]
                if "Degree" in _fc_unique.columns:
                    p7_degree_series = _fc_unique["Degree"].reindex(render_df.index)
                else:
                    p7_degree_series = pd.Series("", index=render_df.index)
                
                # डिस्प्ले रीनेम मैप
                display_rename_map = {
                    "Unique ID": "Unique Id",
                    "Email ID": "Email Id",
                    "Duration": "Duretion",
                    "Current Year": "Year"
                }
                render_df = render_df.rename(columns=display_rename_map)
                
                if "S. No." in render_df.columns: 
                    render_df = render_df.drop(columns=["S. No."])
                render_df.insert(0, "S. No.", range(1, len(render_df) + 1))
                
                # CCE लाइव डेटा एडिटर ग्रिड
                st.markdown('<div class="print-hide">', unsafe_allow_html=True)
                if role in ["full_admin", "p7_role"]:
                    disabled_cols = [c for c in render_df.columns if c not in ["CCE Marks Obtained", "CCE Attendance Status"]]
                    st.info("🔓 **डेटा एंट्री मोड एक्टिव:** आप CCE Marks और Attendance Status बदल सकते हैं।")
                else:
                    disabled_cols = [c for c in render_df.columns]
                    st.warning("🔒 **रीड-ओनली मोड:** आपके पास बदलाव का अधिकार नहीं है।")
                    
                edited_cce = st.data_editor(
                    render_df, 
                    use_container_width=True, 
                    disabled=disabled_cols, 
                    column_config={
                        "CCE Marks Obtained": st.column_config.TextColumn("CCE Marks (Max 20)"),
                        "CCE Attendance Status": st.column_config.SelectboxColumn("Attendance Status", options=["Present", "Absent", "Detained"], required=True)
                    }, 
                    key="cce_live_entry_grid_p7_desk_final", 
                    hide_index=True
                )
                
                if role in ["full_admin", "p7_role"]:
                    if st.button("💾 Save Grid Changes to Master Database", type="primary", use_container_width=True, key="p7_save_grid_btn"):
                        try:
                            clean_edited = edited_cce.drop(columns=["S. No."], errors="ignore")
                            cce_sync_counter = 0
                            for _, r_edit in clean_edited.iterrows():
                                app_num = str(r_edit["Admission Application Number"]).strip()
                                idx_matches = pd.Index([])
                                if "Application Number" in live_db.columns:
                                    idx_matches = live_db[live_db["Application Number"].astype(str).str.strip() == app_num].index
                                if idx_matches.empty and "Admission Application Number" in live_db.columns:
                                    idx_matches = live_db[live_db["Admission Application Number"].astype(str).str.strip() == app_num].index
                                
                                if not idx_matches.empty:
                                    for match_idx in idx_matches:
                                        live_db.at[match_idx, "CCE Marks Obtained"] = str(r_edit["CCE Marks Obtained"]).strip()
                                        live_db.at[match_idx, "CCE Attendance Status"] = str(r_edit["CCE Attendance Status"]).strip()
                                        cce_sync_counter += 1
                            save_live_data(live_db)
                            st.success(f"🎉 सफलता! कुल {cce_sync_counter} छात्रों के CCE मार्क्स सुरक्षित सेव हो गए हैं!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"डेटाबेस सिंक चक्र में तकनीकी समस्या: {e}")
                st.markdown('</div>', unsafe_allow_html=True)

                # ----------------------------------------------------------------------
                # भाग 2: ब्लैंक फ़ॉयल जनरेटर (P7 लिस्ट से सिंक और डायनेमिक फ़िल्टर)
                # ----------------------------------------------------------------------
                st.markdown("---")
                st.markdown('<div class="print-hide">', unsafe_allow_html=True)
                st.subheader("📄 2. Generate University Official Blank Foil Sheets")
                
                foil_format_type = st.selectbox(
                    "📄 Select Foil Format Type:",
                    options=[
                        "University Official Blank Foil Sheets (Side-by-Side)",
                        "CCE Mark Entry (Detailed Marks View)",
                        "CCE List (Internal Evaluation - Multi Paper)",
                        "CCE List - Signature Format (CCE-1 to CCE-4 + Total)"
                    ],
                    key="p7_foil_format_type_selector"
                )
                p7_is_sig_format = (foil_format_type == "CCE List - Signature Format (CCE-1 to CCE-4 + Total)")

                # 🆕 Format 4: sab se pehle Degree puchho (Class Line me aayega)
                p7_sig_class_line = ""
                p7_sig_paper_line = ""
                if p7_is_sig_format:
                    p7_sig_degree_choice = st.selectbox(
                        "🎓 Degree चुनें (Class Line में आएगा):",
                        options=["B. SC.", "B. A.", "B. COM.", "M. SC.", "M. A.", "M. COM.", "BBA", "BCA", "Other (खुद लिखें)"],
                        key="p7_sig_degree_choice"
                    )
                    if p7_sig_degree_choice.startswith("Other"):
                        p7_sig_class_line = st.text_input("✍️ Degree खुद लिखें:", key="p7_sig_degree_custom").strip()
                    else:
                        p7_sig_class_line = p7_sig_degree_choice

                # 🎓 Degree ke hisab se list chhantne ke helper (Format 4)
                import re as _re_deg
                def _p7_degree_key(raw):
                    n = _re_deg.sub(r"[^a-z]", "", str(raw).lower())
                    if not n or n == "nan":
                        return ""
                    long_names = [
                        ("bachelorofscience", "bsc"), ("bachelorofarts", "ba"), ("bachelorofcommerce", "bcom"),
                        ("bachelorofbusiness", "bba"), ("bachelorofcomputer", "bca"),
                        ("masterofscience", "msc"), ("masterofarts", "ma"), ("masterofcommerce", "mcom"),
                    ]
                    for _full, _k in long_names:
                        if n.startswith(_full):
                            return _k
                    for _k in ("bsc", "bcom", "bba", "bca", "msc", "mcom", "ba", "ma"):
                        if n.startswith(_k):
                            return _k
                    return ""

                def _p7_deg_keys(df_in):
                    # Degree column se key nikalo; khali/na-pehchani ho to Subject column ("M.Sc. (Chemistry)") se
                    src = p7_degree_series.reindex(df_in.index).fillna("").astype(str)
                    keys = src.map(_p7_degree_key)
                    if "Subject" in df_in.columns:
                        _sk = df_in["Subject"].fillna("").astype(str).map(_p7_degree_key)
                        keys = keys.where(keys != "", _sk)
                    return keys

                def _p7_apply_degree(df_in, key):
                    if not key:
                        return df_in
                    _keys = _p7_deg_keys(df_in)
                    if not (_keys != "").any():
                        return df_in   # data me Degree pehchana nahi gaya => filter nahi lagega
                    return df_in[_keys == key]

                p7_deg_key = _p7_degree_key(p7_sig_class_line) if p7_is_sig_format else ""
                p7_deg_df = _p7_apply_degree(render_df, p7_deg_key) if p7_is_sig_format else render_df
                if p7_is_sig_format and p7_deg_key:
                    if (_p7_deg_keys(render_df) != "").any():
                        st.caption(f"🎓 {p7_sig_class_line} के कुल {len(p7_deg_df)} students मिले (बाकी degrees की list नहीं आएगी)")
                    else:
                        st.warning("⚠️ Data में Degree पहचानी नहीं गई, इसलिए Degree filter नहीं लग पाया — सभी degrees के students दिखेंगे।")

                # 🟢 P7: Subject Filter se pehle "Column Scroll List" — user pehle yeh chunega
                # ki kis column (Subject / Branch / Minor Subjects / MDC Subjects /
                # Vocational Subjects / PW/Ap/CE Subjects) ke aadhar par filter karna hai,
                # us column ke unique values ki list neeche dropdown me aa jaayegi.
                p7_filter_column_options = [
                    "Subject", "Branch", "Minor Subjects", "Vocational Subjects",
                    "MDC Subjects", "PW/Ap/CE Subjects"
                ]
                # UG degree (B.A./B.Sc./B.Com./BBA/BCA) => Branch/Minor/MDC/Vocational/PW-Ap-CE ; PG degree (M.A./M.Sc./M.Com.) => sirf Subject
                if p7_is_sig_format and p7_deg_key in ("ba", "bsc", "bcom", "bba", "bca"):
                    p7_filter_column_options = [c for c in p7_filter_column_options if c != "Subject"]
                elif p7_is_sig_format and p7_deg_key in ("ma", "msc", "mcom"):
                    p7_filter_column_options = ["Subject"]
                p7_available_filter_columns = [c for c in p7_filter_column_options if c in render_df.columns]
                if not p7_available_filter_columns:
                    p7_available_filter_columns = ["Subject"]

                selected_filter_column = st.selectbox(
                    "🗂️ Select Column to Filter By (Subject / Branch / Minor / MDC / Vocational / PW-Ap-CE):",
                    options=p7_available_filter_columns,
                    format_func=lambda c: "Branch (Major)" if c == "Branch" else c,
                    key="p7_foil_filter_column_select"
                )

                col_p7_1, col_p7_2 = st.columns(2)
                with col_p7_1:
                    if selected_filter_column in p7_deg_df.columns:
                        unique_subjects = sorted(list(set(p7_deg_df[selected_filter_column].dropna().astype(str).str.strip())))
                    else:
                        unique_subjects = []
                    selected_subject = st.selectbox(f"📚 Select {'Branch (Major)' if selected_filter_column == 'Branch' else selected_filter_column} Filter:", options=["All Subjects"] + [s for s in unique_subjects if s != ""], key="p7_foil_subject_filter")
                with col_p7_2:
                    custom_year_options = [
                        "All Years", "1st Sem.", "2nd Sem.", "3rd Sem.", "4th Sem.", "5th Sem.", "6th Sem.", 
                        "7th Sem.", "8th Sem.", "9th Sem.", "10th Sem.", "11th Sem.", "12th Sem.",
                        "1st Year", "2nd Year", "3rd Year", "4th Year", "5th Year", "6th Year"
                    ]
                    chosen_option = st.selectbox("📅 Select Semester / Year Scope:", options=custom_year_options, key="p7_foil_year_filter")
                    
                # 🆕 Format 4: Paper Line — chune hue Column ke hisab se scroll list (Major - I, II, III / Minor - I, II ...)
                if p7_is_sig_format:
                    # ✏️ yahan list badal sakte hain: {column: (prefix, [paper numbers])}
                    p7_paper_kind_map = {
                        "Branch": ("MAJOR", ["I", "II", "III"]),
                        "Minor Subjects": ("MINOR", ["I", "II"]),
                        "MDC Subjects": ("MDC", []),
                        "Vocational Subjects": ("VOCATIONAL", []),
                        "PW/Ap/CE Subjects": ("PW/Ap/CE Subjects", []),
                    }
                    _kind, _nums = p7_paper_kind_map.get(selected_filter_column, ("", []))
                    _auto_opt = "Auto (बिना Paper No.)"
                    _custom_opt = "Custom (खुद लिखें)"
                    if _nums:
                        _paper_opts = [_auto_opt] + [f"{_kind} - {n}" for n in _nums] + [_custom_opt]
                    elif _kind:
                        _paper_opts = [_kind, _custom_opt]  # bina number wali list (MDC / VOCATIONAL / PW/Ap/CE Subjects)
                    else:
                        _paper_opts = [_auto_opt, _custom_opt]
                    _paper_pick = st.selectbox(
                        "📘 Paper Line चुनें:",
                        options=_paper_opts,
                        key=f"p7_sig_paper_sel_{selected_filter_column}"
                    )
                    if _paper_pick == _custom_opt:
                        p7_sig_paper_line = st.text_input(
                            "✍️ Paper Line खुद लिखें (जैसे: MAJOR - III ( CHEMISTRY )):",
                            key="p7_sig_paper_line"
                        ).strip()
                    elif _paper_pick == _auto_opt:
                        p7_sig_paper_line = ""
                    else:
                        _sub_part = "" if selected_subject == "All Subjects" else f" ( {selected_subject.upper()} )"
                        p7_sig_paper_line = f"{_paper_pick}{_sub_part}"

                max_marks = "20"

                if st.button("🔄 Generate Foil Sheet Now", type="primary", use_container_width=True, key="p7_foil_generate_btn"):
                    st.session_state.cce_foil_generated = True
                st.markdown('</div>', unsafe_allow_html=True)
                        
                if st.session_state.get("cce_foil_generated", False):
                    foil_data_df = render_df.copy()
                    if p7_is_sig_format:
                        foil_data_df = _p7_apply_degree(foil_data_df, p7_deg_key).copy()
                    
                    # 📚 सेमेस्टर-टू-ईयर लाइव मैपिंग इंजन
                    sem_to_year_map = {
                        "1st Sem.": "1st Year", "2nd Sem.": "1st Year",
                        "3rd Sem.": "2nd Year", "4th Sem.": "2nd Year",
                        "5th Sem.": "3rd Year", "6th Sem.": "3rd Year",
                        "7th Sem.": "4th Year", "8th Sem.": "4th Year",
                        "9th Sem.": "5th Year", "10th Sem.": "5th Year",
                        "11th Sem.": "6th Year", "12th Sem.": "6th Year"
                    }
                    target_db_year = sem_to_year_map.get(chosen_option, chosen_option)
                    
                    # 1. पहले चुने गए Column (Subject / Branch / Minor / MDC / Vocational / PW-Ap-CE) के आधार पर फ़िल्टर करें
                    if selected_subject != "All Subjects" and selected_filter_column in foil_data_df.columns:
                        foil_data_df = foil_data_df[foil_data_df[selected_filter_column].astype(str).str.strip() == selected_subject]
                    
                    # 🟢 2. Semester / Year Scope के आधार पर फ़िल्टर करें
                    # 🟢 Fix: पहले यहाँ "Year == साल" के साथ "Status == 'Regular Student'" (exact match)
                    # की भी जरूरत पड़ती थी, और EX-STUDENT वाली condition कभी सही मैच ही नहीं करती थी
                    # (EX-STUDENT का Year हमेशा सीधा "EX-STUDENT" सेट होता है, "2nd Year" जैसा नहीं) —
                    # यही वजह थी कि P10 जैसा ही यह Semester/Year Scope सिस्टम भी काम नहीं कर रहा था।
                    # अब सीधा सिर्फ "Year" कॉलम से मैच किया जाता है।
                    if chosen_option != "All Years":
                        foil_data_df = foil_data_df[
                            foil_data_df["Year"].astype(str).str.strip().str.upper() ==
                            str(target_db_year).strip().upper()
                        ]
                    
                    # 🆕 Asli Roll No. pehle hi bacha lo (Signature Format me khali roll khali hi dikhega)
                    if "Roll No." in foil_data_df.columns:
                        foil_data_df["_orig_roll"] = foil_data_df["Roll No."].fillna("").astype(str).str.strip().replace({"nan": "", "None": ""})
                    else:
                        foil_data_df["_orig_roll"] = ""

                    # 🟢 3. रोल नंबर खाली होने पर स्टूडेंट नेम रिप्लेसमेंट नियम (ONLY FOR 1st YEAR FILTER)
                    if not foil_data_df.empty and "Roll No." in foil_data_df.columns:
                        def apply_roll_name_rule(row):
                            roll_val = str(row.get("Roll No.", "")).strip()
                            is_in_first_year_scope = (target_db_year == "1st Year")
                            
                            if is_in_first_year_scope and (roll_val == "" or roll_val.lower() == "nan"):
                                return str(row.get("Student Name", "")).strip().upper()
                            return roll_val

                        foil_data_df["Roll No."] = foil_data_df.apply(apply_roll_name_rule, axis=1)

                    # 🔢 4. शॉर्टिंग इंजन: नाम और रोल नंबर दोनों को वर्णानुक्रम/बढ़ते क्रम में व्यवस्थित रखना
                    if not foil_data_df.empty and "Roll No." in foil_data_df.columns:
                        foil_data_df["_sort_key"] = pd.to_numeric(foil_data_df["Roll No."], errors='coerce')
                        foil_data_df = foil_data_df.sort_values(
                            by=["_sort_key", "Roll No."], 
                            ascending=[True, True]
                        ).drop(columns=["_sort_key"]).reset_index(drop=True)
                        
                    records_list = foil_data_df.to_dict(orient="records")

                    if len(records_list) == 0:
                        st.warning(f"🔍 चयनित {selected_filter_column} और '{chosen_option}' ({target_db_year}) के आधार पर कोई डेटा नहीं मिला।")
                    else:
                        def num_to_words(m_str):
                            m_str = str(m_str).strip()
                            if not m_str or m_str.lower() == "nan": return ""
                            words_dict = {
                                "0": "ZERO", "1": "ONE", "2": "TWO", "3": "THREE", "4": "FOUR", "5": "FIVE",
                                "6": "SIX", "7": "SEVEN", "8": "EIGHT", "9": "NINE", "10": "TEN",
                                "11": "ELEVEN", "12": "TWELVE", "13": "THIRTEEN", "14": "FOURTEEN", "15": "FIFTEEN",
                                "16": "SIXTEEN", "17": "SEVENTEEN", "18": "EIGHTEEN", "19": "NINETEEN", "20": "TWENTY"
                            }
                            return words_dict.get(m_str, m_str) + " ONLY"

                        # --- फ़ॉर्मेट 1: Standard Side-By-Side Blank Foil (Vertical Half-Split Pagination) ---
                        if foil_format_type == "University Official Blank Foil Sheets (Side-by-Side)":
                            
                            chunk_size = 35 # प्रति फॉयल ब्लॉक की सटीक रोल नंबर सीमा
                            total_students = len(records_list)
                            
                            # 🟢 चेक करें कि क्या लिस्ट में वास्तव में किसी छात्र का नाम रोल नंबर वाले कॉलम में आया है
                            # यदि कोई रोल नंबर खाली था और उसकी जगह टेक्स्ट (नाम) आया है, तो यह True हो जाएगा
                            has_names_in_roll_col = any(not str(row.get("Roll No.", "")).strip().isdigit() for row in records_list if str(row.get("Roll No.", "")).strip() != "")
                            
                            # 🟢 यदि नाम आया है तभी हेडर "Roll No./ Student Name" होगा, अन्यथा केवल "Roll No." रहेगा
                            column_header_text = "Roll No./ Student Name" if has_names_in_roll_col else "Roll No."
                            
                            # 🎯 ड्रॉपडाउन विकल्प के टेक्स्ट को कस्टमाइज़ करने का आंतरिक इंजन
                            def format_scope_label(raw_opt):
                                raw_str = str(raw_opt).strip().lower()
                                if "sem" in raw_str:
                                    num_part = raw_str.split("sem")[0].strip()
                                    return f"{num_part} Sem."
                                elif "year" in raw_str:
                                    num_part = raw_str.split("year")[0].strip()
                                    return f"{num_part} Year"
                                return raw_opt

                            formatted_scope = format_scope_label(chosen_option)
                            
                            # 🔄 कुल छात्रों की संख्या के आधार पर आवश्यक कुल पेजों की गणना (Vertical Split Logic)
                            import math
                            total_pages_needed = math.ceil(total_students / (chunk_size * 2))
                            if total_pages_needed == 0:
                                total_pages_needed = 1
                                
                            half_total_capacity = total_pages_needed * chunk_size
                            left_side_students = records_list[0:half_total_capacity]
                            right_side_students = records_list[half_total_capacity:]
                            
                            pages_html = ""
                            
                            # प्रत्येक लूप एक पूरा A4 पेज (बायां + दायां ब्लॉक) जनरेट करेगा
                            for p_num in range(total_pages_needed):
                                
                                # ⬅️ वर्तमान पेज का बायां हिस्सा (Left Side Vertical Slice)
                                l_start = p_num * chunk_size
                                l_end = l_start + chunk_size
                                current_left_chunk = left_side_students[l_start:l_end]
                                
                                # ➡️ वर्तमान पेज का दायां हिस्सा (Right Side Vertical Slice)
                                r_start = p_num * chunk_size
                                r_end = r_start + chunk_size
                                current_right_chunk = right_side_students[r_start:r_end]
                                
                                # 🛠️ फंक्शन: सिंगल ब्लॉक (लेफ्ट या राइट) की टेबल रो रेंडर करना
                                def generate_vertical_rows(absolute_start_idx, data_subset):
                                    html_rows = ""
                                    for i in range(chunk_size):
                                        if i < len(data_subset):
                                            row = data_subset[i]
                                            roll_no = str(row.get("Roll No.", "")).strip()
                                            s_no = absolute_start_idx + i + 1
                                        else:
                                            # खाली रो ताकि टेबल का ढांचा (Height) छोटा-बड़ा न हो
                                            roll_no = "&nbsp;"
                                            s_no = absolute_start_idx + i + 1
                                            
                                        # 🟢 डायनेमिक स्टाइलिंग इंजन: 
                                        # यदि शुद्ध नंबर (Roll No) है, तो Center align रहेगा।
                                        # यदि रोल नंबर गायब है और नाम आया है, तो Left align हो जाएगा।
                                        is_numeric_roll = roll_no.isdigit() or roll_no == "&nbsp;"
                                        
                                        if is_numeric_roll:
                                            td_style = "font-family: monospace; font-size: 11px; text-align: center; letter-spacing: 0.5px; padding: 4px 2px;"
                                        else:
                                            td_style = "font-family: Arial, sans-serif; font-size: 10px; text-align: left !important; padding: 4px 2px 4px 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 140px; letter-spacing: 0px;"
                                            
                                        html_rows += f"""
                                        <tr>
                                            <td style='border: 1px solid #000; padding: 4px; font-weight: bold; text-align: center;'>{s_no}</td>
                                            <td style='border: 1px solid #000; {td_style}'>{roll_no}</td>
                                            <td style='border: 1px solid #000; padding: 4px;'>&nbsp;</td>
                                            <td style='border: 1px solid #000; padding: 4px;'>&nbsp;</td>
                                        </tr>
                                        """
                                    return html_rows

                                # 📄 सिंगल A4 पेज टेम्पलेट विथ कस्टमाइज्ड वर्टिकल अलाइनमेंट रूल्स
                                pages_html += f"""
                                <div class='a4-page-wrapper' style='page-break-after: always; box-sizing: border-box; width: 100%; display: flex; justify-content: space-between; gap: 2%; margin-bottom: 30px; background: #fff;'>
                                    
                                    <!-- ⬅️ लेफ्ट फॉयल ब्लॉक -->
                                    <div class='foil-block' style='width: 49%; border: 1px solid #000; padding: 12px; box-sizing: border-box; display: flex; flex-direction: column;'>
                                        <div class='top-meta' style='display: flex; flex-direction: column; align-items: flex-end; font-size: 11px; font-weight: bold; margin-bottom: 5px; width: 100%; text-align: right;'>
                                            <div style='margin-bottom: 2px;'>Paper Code...................</div>
                                            <div>Bundle No.....................</div>
                                        </div>
                                        <div class='header-block' style='text-align: center; border-top: 1.5px solid #000; border-bottom: 1.5px solid #000; padding-top: 6px; padding-bottom: 6px; margin-top: 5px; margin-bottom: 8px;'>
                                            <h2 style='margin: 0; font-size: 16px; font-weight: bold;'>GOVT. K.R.G. POST-GRADUATE AUTONOMOUS COLLEGE, GWALIOR (M.P.)</h2>
                                        </div>
                                        <div class='info-row' style='display: flex; justify-content: space-between; font-size: 11px; font-weight: bold; border-bottom: 1px solid #000; padding-bottom: 4px; margin-bottom: 4px;'>
                                            <span>Examination :- CCE</span>
                                            <span>{selected_subject.upper()} {formatted_scope}</span>
                                        </div>
                                        <div class='info-row' style='font-size: 11px; font-weight: bold; border-bottom: 1px solid #000; padding-bottom: 4px; margin-bottom: 4px; display: flex; justify-content: space-between;'>
                                            <span>Subject: ..........................</span>
                                            <span>Paper: ............................</span>                                            
                                        </div>
                                        <div class='info-row' style='display: flex; justify-content: space-between; font-size: 11px; font-weight: bold; border-bottom: 1px solid #000; padding-bottom: 4px; margin-bottom: 4px;'>
                                            <span>Maximum Marks: ........................</span>
                                            <span>Min Pass Marks: ............</span>
                                        </div>
                                        <div class='foil-label' style='text-align: center; font-weight: bold; font-size: 12px; margin-bottom: 5px; letter-spacing: 2px;'>FOIL</div>
                                        <table style='width: 100%; border-collapse: collapse; font-size: 10px; margin-bottom: 8px;'>
                                            <thead>
                                                <tr>
                                                    <th colspan='2' style='border: 1px solid #000; text-align: center; font-weight: bold; padding: 2px;'>1</th>
                                                    <th colspan='2' style='border: 1px solid #000; text-align: center; font-weight: bold; padding: 2px;'>2</th>
                                                </tr>
                                                <tr>
                                                    <th rowspan='2' style='border: 1px solid #000; text-align: center; width: 15%; padding: 2px;'>Code No.</th>
                                                    <th rowspan='2' style='border: 1px solid #000; text-align: center; width: 35%; padding: 2px;'>{column_header_text}</th>
                                                    <th colspan='2' style='border: 1px solid #000; text-align: center; padding: 2px;'>Marks Obtained</th>
                                                </tr>
                                                <tr>
                                                    <th style='border: 1px solid #000; text-align: center; width: 20%; padding: 2px;'>In Fig</th>
                                                    <th style='border: 1px solid #000; text-align: center; width: 30%; padding: 2px;'>In Words</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {generate_vertical_rows(l_start, current_left_chunk)}
                                            </tbody>
                                        </table>
                                        <div class='note-box' style='border: 1px solid #000; padding: 5px; font-size: 9px; line-height: 1.2; margin-bottom: 10px; text-align: justify;'>
                                            <b>Note:</b> Roll Number and Marks awarded to the candidate may be entered under respective columns very carefully. Marks and Roll Number should be legible.
                                        </div>
                                        <div class='footer-sign' style='font-size: 10px; line-height: 1.6; font-weight: bold;'>
                                            <div>Signature of Examiner........................................................</div>
                                            <div>Name of Examiner...........................................................</div>
                                            <div style='display: flex; justify-content: space-between; margin-top: 3px;'>
                                                <span>Place............................................</span>
                                                <span style='padding: 2px; font-size: 9px;'>Date: ____/____/________</span>
                                            </div>
                                        </div>
                                    </div>

                                    <!-- ➡️ राइट फॉयल ब्लॉक (वर्टिकल क्रम में लेफ्ट साइड की पूरी सिरीज़ खत्म होने के बाद के रोल नंबर) -->
                                    <div class='foil-block' style='width: 49%; border: 1px solid #000; padding: 12px; box-sizing: border-box; display: flex; flex-direction: column;'>
                                        <div class='top-meta' style='display: flex; flex-direction: column; align-items: flex-end; font-size: 11px; font-weight: bold; margin-bottom: 5px; width: 100%; text-align: right;'>
                                            <div style='margin-bottom: 2px;'>Paper Code...................</div>
                                            <div>Bundle No.....................</div>
                                        </div>
                                        <div class='header-block' style='text-align: center; border-top: 1.5px solid #000; border-bottom: 1.5px solid #000; padding-top: 6px; padding-bottom: 6px; margin-top: 5px; margin-bottom: 8px;'>
                                            <h2 style='margin: 0; font-size: 16px; font-weight: bold;'>GOVT. K.R.G. POST-GRADUATE AUTONOMOUS COLLEGE, GWALIOR (M.P.)</h2>
                                        </div>
                                        <div class='info-row' style='display: flex; justify-content: space-between; font-size: 11px; font-weight: bold; border-bottom: 1px solid #000; padding-bottom: 4px; margin-bottom: 4px;'>
                                            <span>Examination :- CCE</span>
                                            <span>{selected_subject.upper()} {formatted_scope}</span>
                                        </div>
                                        <div class='info-row' style='font-size: 11px; font-weight: bold; border-bottom: 1px solid #000; padding-bottom: 4px; margin-bottom: 4px; display: flex; justify-content: space-between;'>
                                            <span>Subject: ..........................</span>
                                            <span>Paper: ............................</span>
                                        </div>
                                        <div class='info-row' style='display: flex; justify-content: space-between; font-size: 11px; font-weight: bold; border-bottom: 1px solid #000; padding-bottom: 4px; margin-bottom: 4px;'>
                                            <span>Maximum Marks: ........................</span>
                                            <span>Min Pass Marks: ............</span>
                                        </div>
                                        <div class='foil-label' style='text-align: center; font-weight: bold; font-size: 12px; margin-bottom: 5px; letter-spacing: 2px;'>FOIL</div>
                                        <table style='width: 100%; border-collapse: collapse; font-size: 10px; margin-bottom: 8px;'>
                                            <thead>
                                                <tr>
                                                    <th colspan='2' style='border: 1px solid #000; text-align: center; font-weight: bold; padding: 2px;'>1</th>
                                                    <th colspan='2' style='border: 1px solid #000; text-align: center; font-weight: bold; padding: 2px;'>2</th>
                                                </tr>
                                                <tr>
                                                    <th rowspan='2' style='border: 1px solid #000; text-align: center; width: 15%; padding: 2px;'>Code No.</th>
                                                    <th rowspan='2' style='border: 1px solid #000; text-align: center; width: 35%; padding: 2px;'>{column_header_text}</th>
                                                    <th colspan='2' style='border: 1px solid #000; text-align: center; padding: 2px;'>Marks Obtained</th>
                                                </tr>
                                                <tr>
                                                    <th style='border: 1px solid #000; text-align: center; width: 20%; padding: 2px;'>In Fig</th>
                                                    <th style='border: 1px solid #000; text-align: center; width: 30%; padding: 2px;'>In Words</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {generate_vertical_rows(half_total_capacity + r_start, current_right_chunk)}
                                            </tbody>
                                        </table>
                                        <div class='note-box' style='border: 1px solid #000; padding: 5px; font-size: 9px; line-height: 1.2; margin-bottom: 10px; text-align: justify;'>
                                            <b>Note:</b> Roll Number and Marks awarded to the candidate may be entered under respective columns very carefully. Marks and Roll Number should be legible.
                                        </div>
                                        <div class='footer-sign' style='font-size: 10px; line-height: 1.6; font-weight: bold;'>
                                            <div>Signature of Examiner........................................................</div>
                                            <div>Name of Examiner...........................................................</div>
                                            <div style='display: flex; justify-content: space-between; margin-top: 3px;'>
                                                <span>Place............................................</span>
                                                <span style='padding: 2px; font-size: 9px;'>Date: ____/____/________</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                """

                            # 🏛️ 3. पूर्ण एकीकृत एचटीएमएल संरचना (A4 Portrait Frame)
                            clean_foil_template = f"""
                            <html>
                            <head>
                                <style>
                                    @page {{ 
                                        size: A4 portrait; 
                                        margin: 8mm; 
                                    }}
                                    body {{ 
                                        font-family: Arial, sans-serif; 
                                        margin: 0; 
                                        padding: 20px; 
                                        background-color: #f0f2f5; 
                                        display: flex;
                                        flex-direction: column;
                                        align-items: center;
                                    }}
                                    .a4-page-wrapper {{ 
                                        box-sizing: border-box; 
                                        width: 210mm; 
                                        min-height: 297mm; 
                                        padding: 15mm; 
                                        margin-bottom: 30px; 
                                        background: #ffffff !important; 
                                        box-shadow: 0 4px 12px rgba(0,0,0,0.15); 
                                        display: flex; 
                                        justify-content: space-between; 
                                        gap: 3%;
                                        page-break-after: always; 
                                    }}
                                    .foil-block {{ 
                                        width: 48.5%; 
                                        border: 1px solid #000; 
                                        padding: 12px; 
                                        box-sizing: border-box; 
                                        display: flex; 
                                        flex-direction: column; 
                                        background: #ffffff !important;
                                    }}
                                    
                                    /* 🟢 कॉलेज के नाम के ऊपर और नीचे एक जैसी समान मजबूत बॉर्डर रेखा का नियम */
                                    .header-block {{
                                        text-align: center; 
                                        border-top: 1.5px solid #000 !important; 
                                        border-bottom: 1.5px solid #000 !important; 
                                        padding-top: 6px !important;
                                        padding-bottom: 6px !important; 
                                        margin-top: 5px !important;
                                        margin-bottom: 8px !important;
                                    }}
                                    
                                    @media print {{
                                        body {{ 
                                            background-color: #fff; 
                                            padding: 0; 
                                        }}
                                        .a4-page-wrapper {{ 
                                            width: 100%; 
                                            min-height: auto; 
                                            padding: 0; 
                                            margin-bottom: 0; 
                                            box-shadow: none; 
                                            page-break-after: always !important; 
                                        }}
                                    }}
                                </style>
                            </head>
                            <body>
                                {pages_html}
                            </body>
                            </html>
                            """
                            
                            safe_html_string = clean_foil_template.replace("\\", "\\\\").replace("`", "'").replace("\n", " ").replace("\r", "")
                            
                            # स्क्रीन प्रीव्यू के लिए स्वतंत्र आईफ्रेम (स्वच्छ सैंडबॉक्स व्यू)
                            st.components.v1.html(clean_foil_template, height=800, scrolling=True)
                            
                            st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
                            
                            # 🖨️ मुख्य सुरक्षित प्रिंटर गेटवे बटन
                            components.html(
                                f"""
                                <html>
                                <body>
                                    <script>
                                    function printFoilSheet() {{
                                        var iframe = window.parent.document.createElement('iframe');
                                        iframe.style.position = 'fixed'; iframe.style.right = '0'; iframe.style.bottom = '0';
                                        iframe.style.width = '0'; iframe.style.height = '0'; iframe.style.border = '0';
                                        window.parent.document.body.appendChild(iframe);
                                        
                                        var doc = iframe.contentWindow.document;
                                        doc.open(); doc.write(`{safe_html_string}`); doc.close();
                                        iframe.contentWindow.focus(); iframe.contentWindow.print();
                                        
                                        setTimeout(function() {{ window.parent.document.body.removeChild(iframe); }}, 1000);
                                    }}
                                    </script>
                                    <button onclick="printFoilSheet()" style="
                                        width: 100%; background-color: #28a745; color: white; padding: 14px; 
                                        border: none; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 16px;
                                        font-family: sans-serif; box-shadow: 0 4px 6px rgba(40, 167, 69, 0.2);">
                                        🖨️ Click Here to Print Official Blank Foil Sheet (A4 Size)
                                    </button>
                                </body>
                                </html>
                                """,
                                height=60
                            )

                        # --- फ़ॉर्मेट 2: DETAILED MARKS VIEW (Display Fixed विथ Iframe) ---
                        elif foil_format_type == "CCE Mark Entry (Detailed Marks View)":
                            f2_rows_per_page = 35
                            f2_total_pages = max(1, -(-len(records_list) // f2_rows_per_page))
                            f2_pages_html = ""
                            for _pi, _ps in enumerate(range(0, len(records_list), f2_rows_per_page), start=1):
                                _chunk = records_list[_ps:_ps + f2_rows_per_page]
                                f2_pages_html += f"""
                                <div class="wrapper">
                                    <div class="title">GOVT. K.R.G. POST-GRADUATE (AUTO.) COLLEGE, GWALIOR (M.P.)</div>
                                    <div class="meta-row">
                                        <span>Examination: CCE</span>
                                        <span>SCOPE: {chosen_option.upper()} ({target_db_year.upper()})</span>
                                    </div>
                                    <div class="sub-row">Subject: {selected_subject.upper()}</div>
                                    <table>
                                        <thead>
                                            <tr>
                                                <th style="width: 10%;">Code No.</th>
                                                <th style="width: 20%;">Roll Number</th>
                                                <th style="width: 15%;">CCE Marks</th>
                                                <th style="width: 15%;">Attendance</th>
                                                <th style="width: 40%;">In Words</th>
                                            </tr>
                                        </thead>
                                        <tbody>"""
                                for _j, row in enumerate(_chunk):
                                    idx = _ps + _j
                                    tot = str(row.get("CCE Marks Obtained", "")).strip()
                                    att = str(row.get("CCE Attendance Status", "")).strip()
                                    f2_pages_html += f"""
                                            <tr>
                                                <td style="font-weight: bold;">{idx + 1}</td>
                                                <td style="font-family: monospace; font-size: 13px;">{row.get("Roll No.", "")}</td>
                                                <td style="font-weight: bold; color: blue;">{tot if tot else "&nbsp;"}</td>
                                                <td>{att if att else "&nbsp;"}</td>
                                                <td style="text-align: left; padding-left: 10px;">{num_to_words(tot) if tot else ""}</td>
                                            </tr>"""
                                f2_pages_html += f"""
                                        </tbody>
                                    </table>
                                    <div class="pgno">Page {_pi} of {f2_total_pages}</div>
                                </div>"""
                            mark_entry_html = f"""
                            <html>
                            <head>
                                <meta charset="utf-8">
                                <style>
                                    body {{ font-family: Arial, sans-serif; margin: 10px; background-color: #fff; color: #000; }}
                                    .bar {{ text-align: right; margin-bottom: 8px; }}
                                    .bar button {{ padding: 6px 14px; font-weight: bold; cursor: pointer; }}
                                    .wrapper {{ width: 100%; max-width: 850px; margin: 0 auto 20px auto; border: 1px solid #000; padding: 15px; box-sizing: border-box; page-break-after: always; }}
                                    .wrapper:last-child {{ page-break-after: auto; }}
                                    .title {{ text-align: center; border-bottom: 1px solid #000; padding-bottom: 5px; margin-bottom: 5px; font-weight: bold; font-size: 14px; }}
                                    .meta-row {{ display: flex; justify-content: space-between; font-size: 12px; font-weight: bold; padding: 3px 0; }}
                                    .sub-row {{ font-size: 12px; font-weight: bold; padding: 3px 0; border-bottom: 1px solid #000; margin-bottom: 8px; }}
                                    table {{ width: 100%; border-collapse: collapse; font-size: 12px; text-align: center; }}
                                    th, td {{ border: 1px solid #000; padding: 5px; }}
                                    th {{ background-color: #f2f2f2; font-weight: bold; }}
                                    .pgno {{ text-align: center; font-size: 11px; font-weight: bold; margin-top: 8px; }}
                                    @page {{ size: A4; margin: 10mm; }}
                                    @media print {{ .bar {{ display: none; }} body {{ margin: 0; }} .wrapper {{ margin: 0 auto; }} }}
                                </style>
                            </head>
                            <body>
                                <div class="bar"><button onclick="window.print()">🖨️ Print</button></div>
                                {f2_pages_html}
                            </body>
                            </html>
                            """
                            st.components.v1.html(mark_entry_html, height=650, scrolling=True)

                        # --- फ़ॉर्मेट 3: MULTI-PAPER ASSESSMENT LIST (Display Fixed विथ Iframe) ---
                        elif foil_format_type == "CCE List (Internal Evaluation - Multi Paper)":
                            f3_rows_per_page = 30
                            f3_total_pages = max(1, -(-len(records_list) // f3_rows_per_page))
                            f3_pages_html = ""
                            for _pi, _ps in enumerate(range(0, len(records_list), f3_rows_per_page), start=1):
                                _chunk = records_list[_ps:_ps + f3_rows_per_page]
                                f3_pages_html += f"""
                                <div class="wrapper">
                                    <div class="center-txt">GOVT. K.R.G. POST-GRADUATE AUTONOMOUS COLLEGE, GWALIOR (M.P.)</div>
                                    <div class="center-txt" style="font-size: 13px;">Scope: {chosen_option.upper()} | Mapped Year: {target_db_year}</div>
                                    <div class="border-bottom">CCE List (Internal Evaluation Master Log)</div>
                                    <table>
                                        <thead>
                                            <tr style="font-weight: bold;">
                                                <th style="width: 8%;">S. No.</th>
                                                <th style="width: 16%;">Roll No.</th>
                                                <th style="width: 24%; text-align: left;">Name</th>
                                                <th style="width: 24%; text-align: left;">Father Name</th>
                                                <th style="width: 14%;">CCE Obtained</th>
                                                <th style="width: 14%;">Status</th>
                                                <th style="width: 14%;">Sign</th>
                                            </tr>
                                        </thead>
                                        <tbody>"""
                                for _j, row in enumerate(_chunk):
                                    idx = _ps + _j
                                    s_name = str(row.get("Student Name", "")).upper()
                                    f_name = str(row.get("Father Name", "")).upper()
                                    cce_live = str(row.get("CCE Marks Obtained", "")).strip()
                                    att_live = str(row.get("CCE Attendance Status", "")).strip()
                                    f3_pages_html += f"""
                                            <tr>
                                                <td style="font-weight: bold;">{idx + 1}</td>
                                                <td style="font-family: monospace;">{row.get("_orig_roll", "")}</td>
                                                <td style="text-align: left;">{s_name}</td>
                                                <td style="text-align: left;">{f_name}</td>
                                                <td style="font-weight: bold; color: blue;">{cce_live if cce_live else "&nbsp;"}</td>
                                                <td>{att_live if att_live else "&nbsp;"}</td>
                                                <td>&nbsp;</td>
                                            </tr>"""
                                f3_pages_html += f"""
                                        </tbody>
                                    </table>
                                    <div class="pgno">Page {_pi} of {f3_total_pages}</div>
                                </div>"""
                            multi_paper_html = f"""
                            <html>
                            <head>
                                <meta charset="utf-8">
                                <style>
                                    body {{ font-family: Arial, sans-serif; margin: 10px; background-color: #fff; color: #000; }}
                                    .bar {{ text-align: right; margin-bottom: 8px; }}
                                    .bar button {{ padding: 6px 14px; font-weight: bold; cursor: pointer; }}
                                    .wrapper {{ width: 100%; max-width: 950px; margin: 0 auto 20px auto; border: 1px solid #000; padding: 15px; box-sizing: border-box; page-break-after: always; }}
                                    .wrapper:last-child {{ page-break-after: auto; }}
                                    .center-txt {{ text-align: center; font-weight: bold; font-size: 14px; margin-bottom: 4px; }}
                                    .border-bottom {{ text-align: center; font-weight: bold; font-size: 13px; margin-bottom: 4px; border-bottom: 1px solid #000; padding-bottom: 5px; }}
                                    table {{ width: 100%; border-collapse: collapse; font-size: 12px; text-align: center; table-layout: fixed; }}
                                    th, td {{ border: 1px solid #000; padding: 5px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
                                    th {{ background-color: #f2f2f2; font-weight: bold; }}
                                    .pgno {{ text-align: center; font-size: 11px; font-weight: bold; margin-top: 8px; }}
                                    @page {{ size: A4; margin: 10mm; }}
                                    @media print {{ .bar {{ display: none; }} body {{ margin: 0; }} .wrapper {{ margin: 0 auto; }} }}
                                </style>
                            </head>
                            <body>
                                <div class="bar"><button onclick="window.print()">🖨️ Print</button></div>
                                {f3_pages_html}
                            </body>
                            </html>
                            """
                            st.components.v1.html(multi_paper_html, height=650, scrolling=True)

                        # --- फ़ॉर्मेट 4: CCE LIST - SIGNATURE FORMAT (CCE-1..CCE-4 + TOTAL) ---
                        elif foil_format_type == "CCE List - Signature Format (CCE-1 to CCE-4 + Total)":
                            import html as _html_mod
                            _roman = {"1st Year": "I", "2nd Year": "II", "3rd Year": "III",
                                      "4th Year": "IV", "5th Year": "V", "6th Year": "VI"}
                            _yr_txt = _roman.get(str(target_db_year), str(target_db_year).upper())
                            _deg = ""
                            for _c in ("Degree", "Eligibility Name"):
                                if _c in foil_data_df.columns and not foil_data_df[_c].dropna().empty:
                                    _deg = str(foil_data_df[_c].dropna().astype(str).iloc[0]).strip()
                                    if _deg: break
                            _deg_in = p7_sig_class_line.strip().upper()
                            if not _deg_in:
                                _deg_in = _deg.upper()
                            if chosen_option != "All Years":
                                sig_class_line = f"{_deg_in} {_yr_txt} YEAR".strip()
                            else:
                                sig_class_line = _deg_in
                            if p7_sig_paper_line.strip():
                                sig_paper_line = p7_sig_paper_line.strip()
                            else:
                                _subj_txt = "" if selected_subject == "All Subjects" else selected_subject.upper()
                                _paper_kind = {
                                    "Branch": "MAJOR", "Minor Subjects": "MINOR", "MDC Subjects": "MDC",
                                    "Vocational Subjects": "VOCATIONAL", "PW/Ap/CE Subjects": "PW/Ap/CE Subjects"
                                }.get(selected_filter_column, "")
                                if _subj_txt:
                                    sig_paper_line = f"{_paper_kind} ( {_subj_txt} )".strip()
                                else:
                                    sig_paper_line = _paper_kind
                            sig_title_line = f"CCE LIST - {sig_paper_line}".strip(" -") if sig_paper_line else "CCE LIST"

                            sig_rows_per_page = 30
                            sig_max_each = "10"
                            sig_max_total = "30"
                            _esc = lambda v: _html_mod.escape(str(v if v is not None else "").strip())
                            _nan = lambda v: "" if str(v).strip().lower() == "nan" else _esc(v)

                            # Agar Roll No. column me data hai to Admission No. column nahi aayega
                            sig_has_roll = any(str(_r.get("_orig_roll", "")).strip() not in ("", "nan", "None") for _r in records_list)
                            sig_show_adm = not sig_has_roll
                            _adm_th = '<th rowspan="2" class="c-adm" style="width:11%;">Admission No.</th>' if sig_show_adm else ""
                            _name_w = "19%" if sig_show_adm else "25%"
                            _tbl_cls = "sg" if sig_show_adm else "sg noadm"

                            def _sig_table(chunk, start_idx, page_no, total_pages, sign=False):
                                # sign=True => Sign. List: TOTAL nahi, CCE columns chaude, rows double unchi
                                # Dono lists ki columns ki chaudai ek jaisi (marks list me TOTAL ke liye 6% nikalkar barabar ghataai gayi)
                                _b_sno, _b_adm, _b_roll, _b_nm = 4.0, 9.0, 9.0, 14.0
                                _b_cce = 12.5 if sig_show_adm else 14.75
                                _tot_w = 6.0
                                _k = 100.0 / (100.0 + _tot_w)
                                _pc = lambda v: f"{round(v, 2)}%"
                                if sign:
                                    _w_sno, _w_adm, _w_roll, _w_nm = _pc(_b_sno), _pc(_b_adm), _pc(_b_roll), _pc(_b_nm)
                                    _w_cce = _pc(_b_cce)
                                    _grp_txt = "SIGNATURE"
                                    _tot_th = ""
                                    _cls = "page pg-sign"
                                else:
                                    _w_sno, _w_adm, _w_roll, _w_nm = _pc(_b_sno * _k), _pc(_b_adm * _k), _pc(_b_roll * _k), _pc(_b_nm * _k)
                                    _w_cce = _pc(_b_cce * _k)
                                    _grp_txt = "MARKS"
                                    _tot_th = f'<th rowspan="2" class="c-tot" style="width:{_pc(_tot_w * _k)};">TOTAL<br>({sig_max_total})</th>'
                                    _cls = "page pg-marks"
                                _adm_head = f'<th rowspan="2" style="width:{_w_adm};">Admission No.</th>' if sig_show_adm else ""
                                _cce_head = "".join(
                                    f'<th style="width:{_w_cce};">CCE-{k}<br>({sig_max_each})</th>' for k in (1, 2, 3, 4)
                                )
                                t = f"""
                                <div class="{_cls}">
                                <div class="c1">GOVT. KAMLARAJA GIRLS POST-GRADUATE AUTONOMOUS COLLEGE, GWALIOR (M.P.)</div>
                                <div class="c2">{_esc(sig_class_line)}</div>
                                <div class="c2">{_esc(sig_title_line)}</div>
                                <table class="sg">
                                  <thead>
                                    <tr>
                                      <th rowspan="2" style="width:{_w_sno};">S. No.</th>
                                      {_adm_head}
                                      <th rowspan="2" style="width:{_w_roll};">Roll No.</th>
                                      <th rowspan="2" style="width:{_w_nm};">Student Name</th>
                                      <th rowspan="2" style="width:{_w_nm};">Father Name</th>
                                      <th colspan="4">{_grp_txt}</th>
                                      {_tot_th}
                                    </tr>
                                    <tr>
                                      {_cce_head}
                                    </tr>
                                  </thead>
                                  <tbody>"""
                                for j, r in enumerate(chunk):
                                    adm_td = f"<td>{_nan(r.get('Admission Application Number', ''))}</td>" if sig_show_adm else ""
                                    if sign:
                                        _blank_cells = '<td></td><td></td><td></td><td></td>'
                                    else:
                                        _blank_cells = '<td class="ed"></td><td class="ed"></td><td class="ed"></td><td class="ed"></td><td class="tot"></td>'
                                    t += f"""
                                    <tr>
                                      <td>{start_idx + j + 1}</td>
                                      {adm_td}
                                      <td>{_nan(r.get("_orig_roll", ""))}</td>
                                      <td class="l">{_nan(r.get("Student Name", ""))}</td>
                                      <td class="l">{_nan(r.get("Father Name", ""))}</td>
                                      {_blank_cells}
                                    </tr>"""
                                t += f"""
                                  </tbody>
                                </table>
                                <div class="pgno">Page {page_no} of {total_pages}</div>
                                </div>"""
                                return t

                            sig_pages_html = ""
                            _sig_total_pages = max(1, -(-len(records_list) // sig_rows_per_page))
                            for _pi, _ps in enumerate(range(0, len(records_list), sig_rows_per_page), start=1):
                                sig_pages_html += _sig_table(records_list[_ps:_ps + sig_rows_per_page], _ps, _pi, _sig_total_pages)

                            # 📝 Sign. List pages: rows double unchi hone se ek page par kam rows (14)
                            sign_rows_per_page = 14
                            sign_pages_html = ""
                            _sign_total_pages = max(1, -(-len(records_list) // sign_rows_per_page))
                            for _pi, _ps in enumerate(range(0, len(records_list), sign_rows_per_page), start=1):
                                sign_pages_html += _sig_table(records_list[_ps:_ps + sign_rows_per_page], _ps, _pi, _sign_total_pages, sign=True)

                            sig_full_html = f"""
                            <html>
                            <head>
                              <meta charset="utf-8">
                              <style>
                                body {{ font-family: Arial, sans-serif; margin: 8px; background:#fff; color:#000; }}
                                .bar {{ text-align:right; margin-bottom:8px; }}
                                .bar button {{ padding:6px 14px; font-weight:bold; cursor:pointer; margin-left:6px; }}
                                .bar #modeLbl {{ font-size:12px; font-weight:bold; margin-right:8px; }}
                                body.entry td.ed {{ background:#fffbe0; outline:1px dashed #c9a400; outline-offset:-2px; }}
                                body.entry td.ed:focus {{ background:#fff3b0; outline:2px solid #0b57d0; }}
                                td.tot {{ font-weight:bold; }}
                                /* 📝 Sign. List: alag pages — marks wale aur sign wale sets me se ek hi dikhta hai */
                                #signSet {{ display:none; }}
                                body.signmode #signSet {{ display:block; }}
                                body.signmode #marksSet {{ display:none; }}
                                .pg-sign td {{ height:50px; }}
                                .page {{ max-width: 900px; margin: 0 auto 20px auto; }}
                                .page + .page {{ page-break-before: always; }}
                                .c1 {{ text-align:center; font-weight:bold; font-size:15px; }}
                                .c2 {{ text-align:center; font-weight:bold; font-size:13px; margin-top:3px; }}
                                table {{ width:100%; border-collapse:collapse; margin-top:8px; font-size:11px; text-align:center; table-layout:fixed; }}
                                th, td {{ border:1px solid #000; padding:4px 3px; height:20px; overflow:hidden; word-wrap:break-word; }}
                                th {{ font-weight:bold; }}
                                td.l {{ text-align:left; }}
                                .pgno {{ text-align:center; font-size:11px; font-weight:bold; margin-top:8px; }}
                                @page {{ size: A4; margin: 10mm; }}
                                @media print {{ .bar {{ display:none; }} body {{ margin:0; }} .page {{ margin:0; }} }}
                              </style>
                            </head>
                            <body>
                              <div class="bar">
                                <span id="modeLbl">Mode: 🖨️ Print Ready</span>
                                <button id="modeBtn" type="button">✏️ Data Entry Mode</button>
                                <button id="signBtn" type="button">📝 Sign. List</button>
                                <button type="button" onclick="window.print()">🖨️ Print</button>
                              </div>
                              <div id="marksSet">{sig_pages_html}</div>
                              <div id="signSet">{sign_pages_html}</div>
                              <script>
                                var cells = Array.prototype.slice.call(document.querySelectorAll('td.ed'));
                                var btn = document.getElementById('modeBtn');
                                var lbl = document.getElementById('modeLbl');
                                var editing = false;
                                var signing = false;
                                var signBtn = document.getElementById('signBtn');
                                function setSign(on) {{
                                  if (on && editing) {{ setMode(false); }}
                                  signing = on;
                                  document.body.classList.toggle('signmode', on);
                                  signBtn.textContent = on ? '↩️ Marks List (वापस)' : '📝 Sign. List';
                                  btn.disabled = on;
                                  lbl.textContent = on ? 'Mode: 📝 Sign. List' : 'Mode: 🖨️ Print Ready';
                                }}
                                signBtn.addEventListener('click', function() {{ setSign(!signing); }});
                                function setMode(on) {{
                                  editing = on;
                                  cells.forEach(function(td) {{ td.contentEditable = on ? 'true' : 'false'; }});
                                  document.body.classList.toggle('entry', on);
                                  btn.textContent = on ? '✅ Done (Print ke liye)' : '✏️ Data Entry Mode';
                                  lbl.textContent = on ? 'Mode: ✏️ Data Entry' : 'Mode: 🖨️ Print Ready';
                                  if (on && cells.length) {{ cells[0].focus(); }}
                                }}
                                btn.addEventListener('click', function() {{ setMode(!editing); }});
                                cells.forEach(function(td, i) {{
                                  td.addEventListener('keydown', function(e) {{
                                    if (e.key === 'Enter') {{
                                      e.preventDefault();
                                      var nxt = cells[i + 4];   // ek row neeche, usi column me
                                      if (nxt) {{ nxt.focus(); }}
                                    }}
                                  }});
                                  td.addEventListener('input', function() {{ calcTotal(td.parentElement); }});
                                }});
                                // TOTAL = CCE-1..CCE-4 me se sabse zyada 3 marks ka jod (khud nikalta hai)
                                function calcTotal(tr) {{
                                  var eds = tr.querySelectorAll('td.ed');
                                  var tot = tr.querySelector('td.tot');
                                  var nums = [];
                                  eds.forEach(function(c) {{
                                    var v = parseFloat((c.textContent || '').trim());
                                    if (!isNaN(v)) {{ nums.push(v); }}
                                  }});
                                  if (!nums.length) {{ tot.textContent = ''; return; }}
                                  nums.sort(function(a, b) {{ return b - a; }});
                                  var sum = nums.slice(0, 3).reduce(function(a, b) {{ return a + b; }}, 0);
                                  tot.textContent = String(Math.round(sum * 100) / 100);
                                }}
                                window.addEventListener('beforeprint', function() {{ if (editing) {{ setMode(false); }} }});
                              </script>
                            </body>
                            </html>
                            """
                            st.components.v1.html(sig_full_html, height=650, scrolling=True)                
                            
        # ----------------------------------------------------------------------
        # P8: PANEL PROMOTION MODULE (Academic Year Batch Progression Control)
        # ----------------------------------------------------------------------
        elif current_panel_id == "P8":
            st.header(f"📈 {get_panel_title('P8')} (Academic Year Batch Progression Control)")
            
            # Ensure proper promotion status column fallback exists inside runtime
            if "Promotion Status" not in live_db.columns: 
                live_db["Promotion Status"] = "Eligible"
                
            p8_authorized_db = live_db.copy()
            
            if p8_authorized_db.empty: 
                st.warning("⚠️ डेटाबेस वर्तमान में खाली है या कोई स्वीकृत डेटा उपलब्ध नहीं है।")
            else:
                # 🟢 Corrected inline-concatenated string mapping fix to bypass compilation parser limits
                st.markdown(
                    '<div style="background-color: #f7f9fa; border-left: 5px solid #0288d1; padding: 10px; border-radius: 4px; margin-bottom: 15px;">'
                    '📌 <b>ऑपरेटर निर्देश:</b> इस ग्रिड में बैच प्रमोशन (Batch Progression) से संबंधित डेटा प्रदर्शित है। सुरक्षा नियमों के अनुसार केवल सुपर एडमिन ही इसमें बदलाव कर सकता है।'
                    '</div>',
                    unsafe_allow_html=True
                )
                
                available_years = ["All"] + sorted(list(set(p8_authorized_db["Current Year"].dropna().astype(str).str.strip())))
                selected_year = st.selectbox("Current Year (वर्तमान वर्ष) फ़िल्टर चुनें:", options=available_years, key="p8_promo_year_filter_new")
                
                filtered_promo = p8_authorized_db.copy()
                if selected_year != "All": 
                    filtered_promo = filtered_promo[filtered_promo["Current Year"].str.strip() == selected_year]
                
                # Standardized 22 columns tracking for P8 Workspace
                promotion_fixed_cols = [
                    "Admission Application Number", "Roll No.", "Enrollment No.", "Student Name", "Father Name",
                    "Status", "Promotion Status", "Admission Year", "Admission Session", 
                    "Eligibility Name", "Admission Date", "Unique ID", "Application Enrollment No.", 
                    "Mother Name", "Date of Birth", "Category", "Subject", "Duration", 
                    "Mobile Number", "Email ID", "Address", "Current Year"
                ]

        # ----------------------------------------------------------------------
        # P9: PANEL RESULT MODULE (Examination Register Ledger Desk)
        # ----------------------------------------------------------------------
        elif current_panel_id == "P9":
            st.header(f"📊 {get_panel_title('P9')} (Tabulation Register Exam Controller)")
            
            for f in ["Marks Obtained", "Result Status", "Exam Remarks"]:
                if f not in live_db.columns: 
                    live_db[f] = ""
            
            p9_authorized_db = live_db.copy()
            
            if p9_authorized_db.empty: 
                st.warning("⚠️ इस पैनल के लिए कोई अधिकृत स्वीकृत (Approved) डेटा उपलब्ध नहीं है।")
            else:
                # 🟢 Corrected Safe Inline Str Framework Configuration
                st.markdown(
                    '<div style="background-color: #f3e5f5; border-left: 5px solid #8e24aa; padding: 10px; border-radius: 4px; margin-bottom: 15px;">'
                    '📌 <b>ऑपरेटर निर्देश:</b> इस ग्रिड में परीक्षा परिणाम (Exam Result) से संबंधित डेटा प्रदर्शित है। सुरक्षा नियमों के अनुसार केवल सुपर एडमिन ही इसमें बदलाव कर सकता है।'
                    '</div>', 
                    unsafe_allow_html=True
                )
                
                available_subjects = ["All"] + sorted(list(set(p9_authorized_db["Branch"].dropna().astype(str).str.strip()))) if "Branch" in p9_authorized_db.columns else ["All"]
                selected_sub = st.selectbox("Branch (शाखा) फ़िल्टर चुनें:", options=available_subjects, key="p9_subject_filter_secure_engine_new")
                
                filtered_res = p9_authorized_db.copy()
                if selected_sub != "All" and "Branch" in filtered_res.columns: 
                    filtered_res = filtered_res[filtered_res["Branch"].str.strip() == selected_sub]
                
                # Standardized 22 columns tracking for P9 Workspace
                result_fixed_cols = [
                    "Admission Application Number", "Roll No.", "Enrollment No.", "Student Name", "Father Name",
                    "Marks Obtained", "Result Status", "Exam Remarks", "Admission Year", "Admission Session", 
                    "Eligibility Name", "Admission Date", "Unique ID", "Application Enrollment No.", 
                    "Mother Name", "Date of Birth", "Category", "Subject", "Duration", 
                    "Mobile Number", "Email ID", "Address", "Current Year", "Status"
                ]
                
                column_mapping_fixes = {
                    "Unique Id": "Unique ID", "Student Abc Id": "Unique ID", 
                    "Date Of Birth": "Date of Birth", "Duretion": "Duration", 
                    "Email Id": "Email ID", "Year": "Current Year",
                    "Application Number": "Admission Application Number"
                }
                filtered_res = filtered_res.rename(columns=column_mapping_fixes)

                # 🔧 Duplicate column fix (P10 jaisa hi): rename ke baad agar same naam ke
                # multiple columns ban jaayein, to unhe ek hi column mein merge kar do
                # taaki data_editor / st.dataframe crash na ho.
                if filtered_res.columns.duplicated().any():
                    combined_cols_res = {}
                    for col_name in filtered_res.columns.unique():
                        matching_res = filtered_res.loc[:, filtered_res.columns == col_name]
                        if matching_res.shape[1] > 1:
                            merged_res = matching_res.iloc[:, 0]
                            for i in range(1, matching_res.shape[1]):
                                merged_res = merged_res.mask(
                                    merged_res.astype(str).str.strip().eq(""), matching_res.iloc[:, i]
                                )
                                merged_res = merged_res.fillna(matching_res.iloc[:, i])
                            combined_cols_res[col_name] = merged_res
                        else:
                            combined_cols_res[col_name] = matching_res.iloc[:, 0]
                    filtered_res = pd.DataFrame(combined_cols_res)

                for col in result_fixed_cols:
                    if col not in filtered_res.columns: 
                        filtered_res[col] = ""
                        
                render_df = filtered_res[result_fixed_cols].copy()
                render_df.insert(0, "S. No.", range(1, len(render_df) + 1))
                
                st.write(f"📊 ग्रिड में प्रदर्शित कुल छात्र रिकॉर्ड संख्या (Active Result Profiles): **{len(render_df)}**")
                
                if role == "full_admin":
                    disabled_cols = [c for c in render_df.columns if c not in ["Marks Obtained", "Result Status", "Exam Remarks"]]
                    st.info("🔓 **एडमिन कंट्रोल मोड:** आपके पास परीक्षा परिणाम (Marks, Status & Remarks) एडिट और सिंक करने का पूर्ण अधिकार है।")
                else:
                    disabled_cols = [c for c in render_df.columns]
                    st.warning("🔒 **रीड-ओनली मोड:** सुरक्षा कारणों से आपके पास इस लिस्ट में परीक्षा परिणाम बदलने का अधिकार नहीं है।")
                
                edited_res = st.data_editor(
                    render_df, 
                    use_container_width=True, 
                    disabled=disabled_cols, 
                    column_config={
                        "Marks Obtained": st.column_config.TextColumn("Marks Obtained"),
                        "Result Status": st.column_config.SelectboxColumn("Result Status", options=["Pass", "Fail", "ATKT", "Withheld", "Absent"], required=True),
                        "Exam Remarks": st.column_config.TextColumn("Exam Remarks")
                    }, 
                    key="result_live_editor_grid_p9_secure_engine_new", 
                    hide_index=True
                )
                
                if role == "full_admin":
                    if st.button("Save & Sync Tabulation Register", type="primary", use_container_width=True, key="p9_save_btn_secure_new"):
                        try:
                            clean_edited = edited_res.drop(columns=["S. No."], errors="ignore")
                            result_sync_counter = 0
                            
                            for _, r_edit in clean_edited.iterrows():
                                app_num = str(r_edit["Admission Application Number"]).strip()
                                idx_matches = live_db[live_db["Application Number"].astype(str).str.strip() == app_num].index
                                
                                if not idx_matches.empty:
                                    for match_idx in idx_matches:
                                        live_db.at[match_idx, "Marks Obtained"] = str(r_edit["Marks Obtained"]).strip()
                                        live_db.at[match_idx, "Result Status"] = str(r_edit["Result Status"]).strip()
                                        live_db.at[match_idx, "Exam Remarks"] = str(r_edit["Exam Remarks"]).strip()
                                        result_sync_counter += 1
                                        
                            save_live_data(live_db)
                            st.success(f"🎉 सफलता! कुल {result_sync_counter} छात्र रिकॉर्ड्स का परीक्षा परिणाम मुख्य डेटाबेस में सुरक्षित सिंक हो गया है!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"डेटाबेस सिंक्रोनाइज़ेशन चक्र में तकनीकी समस्या आई: {e}")

        # ----------------------------------------------------------------------
        # P10: PANEL REGISTER MODULE (University TR / Ledger Archiver Desk)
        # ----------------------------------------------------------------------
        elif current_panel_id == "P10":
            st.header(f"📋 {get_panel_title('P10')} (Tabulation Ledger & Permanent Registry)")
            
            p10_authorized_db = live_db.copy()
            
            if p10_authorized_db.empty:
                st.warning("⚠️ मास्टर डेटाबेस रिक्त है।")
            else:
                # 🟢 Corrected safe inline string format to prevent syntax errors
                st.markdown(
                    '<div style="background-color: #fff9e6; border-left: 5px solid #ffc107; padding: 10px; border-radius: 4px; margin-bottom: 15px;">'
                    '📌 <b>स्थायी पंजी डेस्क:</b> यह विश्वविद्यालय का मुख्य रिकॉर्ड लेजर है। यहाँ सभी छात्र प्रोफाइल का सम्पूर्ण विवरण सुरक्षित संग्रहित रहता है। लॉन्ग-टर्म सिक्योरिटी नियमों के कारण यह डेटा केवल रीड-ओनली व्यू में उपलब्ध है।'
                    '</div>', 
                    unsafe_allow_html=True
                )
                
                # Perfect 22 core fields layout mapping for P10
                # 🟢 Fix: "Student Abc Id" ab apne alag column mein dikhega — pehle ise "Unique ID"
                # mein hi merge/rename kar diya jaata tha, jisse Unique ID column mein Student Abc Id
                # ka data aa jaata tha. Ab dono alag-alag columns hain.
                # 🟢 नया Fix: पहले यहाँ सिर्फ ऊपर दिए गए fixed 21 columns ही available hote the।
                # अब "Master Database List View & Advanced Operational Controls" (P15) में जितने भी
                # columns मौजूद हैं (st.session_state.admin_columns_order — जिसमें एडमिन द्वारा नए
                # जोड़े गए columns भी शामिल हो जाते हैं), वही सभी columns यहाँ P10 में भी उपलब्ध रहेंगे,
                # ताकि जिस column की ज़रूरत हो उसे नीचे "Print Columns चुनें" वाले multiselect से चुनकर
                # इस्तेमाल किया जा सके।
                archive_view_cols = [
                    col for col in st.session_state.get("admin_columns_order", DEFAULT_COLUMNS)
                    if col not in ("S.No.", "S. No.")
                ]
                # Safety fallback: agar kisi wajah se master column list khaali mil jaaye,
                # to purane fixed 21 columns hi backup ke roop mein use ho jaayenge.
                if not archive_view_cols:
                    archive_view_cols = [
                        "Admission Year", "Admission Session", "Eligibility Name", "Admission Application Number", 
                        "Admission Date", "Unique ID", "Student Abc Id", "Roll No.", "Application Enrollment No.", "Enrollment No.", 
                        "Student Name", "Father Name", "Mother Name", "Date of Birth", "Category", "Subject", 
                        "Duration", "Mobile Number", "Email ID", "Address", "Current Year", "Status"
                    ]
                
                column_mapping_fixes = {
                    "Unique Id": "Unique ID", 
                    "Date Of Birth": "Date of Birth", "Duretion": "Duration", 
                    "Email Id": "Email ID", "Year": "Current Year",
                    "Application Number": "Admission Application Number"
                }
                p10_authorized_db = p10_authorized_db.rename(columns=column_mapping_fixes)

                # 🔧 Duplicate column fix: rename se pehle agar same naam ke 2 columns
                # already maujood the (jaise "Unique ID" aur "Unique Id" dono), to rename
                # ke baad wahi naam duplicate ho jaata hai jisse pyarrow/streamlit error deta hai.
                # Yahan duplicate naam wale columns ko ek hi column mein merge kar rahe hain
                # (jahan bhi value khaali ho, wahan dusre duplicate column ki value le lo).
                if p10_authorized_db.columns.duplicated().any():
                    combined_cols = {}
                    for col_name in p10_authorized_db.columns.unique():
                        matching = p10_authorized_db.loc[:, p10_authorized_db.columns == col_name]
                        if matching.shape[1] > 1:
                            merged = matching.iloc[:, 0]
                            for i in range(1, matching.shape[1]):
                                merged = merged.mask(
                                    merged.astype(str).str.strip().eq(""), matching.iloc[:, i]
                                )
                                merged = merged.fillna(matching.iloc[:, i])
                            combined_cols[col_name] = merged
                        else:
                            combined_cols[col_name] = matching.iloc[:, 0]
                    p10_authorized_db = pd.DataFrame(combined_cols)

                # Ensure all target columns exist cleanly to bypass blank key runtime errors
                for col in archive_view_cols:
                    if col not in p10_authorized_db.columns: 
                        p10_authorized_db[col] = ""
                
                # 🟢 CCE (P7) panel jaisa hi Semester / Year scope filter — यहाँ भी वैसा ही जोड़ा गया है
                custom_year_options_p10 = [
                    "All Years", "1st Sem.", "2nd Sem.", "3rd Sem.", "4th Sem.", "5th Sem.", "6th Sem.",
                    "7th Sem.", "8th Sem.", "9th Sem.", "10th Sem.", "11th Sem.", "12th Sem.",
                    "1st Year", "2nd Year", "3rd Year", "4th Year", "5th Year", "6th Year"
                ]
                col_p10_f1, col_p10_f2, col_p10_f3 = st.columns(3)
                with col_p10_f1:
                    chosen_option_p10 = st.selectbox(
                        "📅 Select Semester / Year Scope:", options=custom_year_options_p10, key="p10_archive_year_filter"
                    )

                # 📚 सेमेस्टर-टू-ईयर लाइव मैपिंग इंजन (CCE panel jaisa hi)
                # 🟢 ध्यान दें: 1st Sem. और 2nd Sem. दोनों 1st Year में ही मैप होते हैं,
                # इसलिए "1 Sem" चुनने पर भी वही डेटा आएगा जो "2 Sem" या "1st Year" चुनने पर आता है।
                sem_to_year_map_p10 = {
                    "1st Sem.": "1st Year", "2nd Sem.": "1st Year",
                    "3rd Sem.": "2nd Year", "4th Sem.": "2nd Year",
                    "5th Sem.": "3rd Year", "6th Sem.": "3rd Year",
                    "7th Sem.": "4th Year", "8th Sem.": "4th Year",
                    "9th Sem.": "5th Year", "10th Sem.": "5th Year",
                    "11th Sem.": "6th Year", "12th Sem.": "6th Year"
                }
                target_db_year_p10 = sem_to_year_map_p10.get(chosen_option_p10, chosen_option_p10)

                # 🟢 Pehle Year/Sem scope tay hota hai, ab usi scope ke andar maujood Subjects ki list banayenge
                # taaki "Select Subject Filter" dropdown me sirf usi saal/semester ke Subjects hi dikhein
                if chosen_option_p10 != "All Years":
                    subject_scope_df_p10 = p10_authorized_db[
                        p10_authorized_db["Current Year"].astype(str).str.strip().str.upper() ==
                        str(target_db_year_p10).strip().upper()
                    ]
                else:
                    subject_scope_df_p10 = p10_authorized_db

                # 🟢 2nd dropdown: user pehle ye tay karega ki kis COLUMN ke data par filter lagana hai
                # (jaise "Subject", "Category", "Status" etc.) — fir 3rd dropdown me usi column ka
                # unique data list ho kar aayega, use chun kar list filter ho jayegi.
                p10_filter_column_options = [c for c in archive_view_cols if c in p10_authorized_db.columns]
                if "Subject" in p10_filter_column_options:
                    default_col_idx_p10 = p10_filter_column_options.index("Subject")
                else:
                    default_col_idx_p10 = 0

                with col_p10_f2:
                    selected_column_p10 = st.selectbox(
                        "🗂️ Select Column:",
                        options=p10_filter_column_options,
                        index=default_col_idx_p10 if p10_filter_column_options else 0,
                        key="p10_archive_column_filter"
                    )

                unique_subjects_p10 = sorted(list(set(
                    subject_scope_df_p10[selected_column_p10].dropna().astype(str).str.strip()
                ))) if selected_column_p10 else []

                # 🟢 Fix: agar pehle se selected value naye column/scope me maujood nahi hai (ya column hi
                # badal gaya hai), to wo apne aap "All Subjects" par reset ho jayega (taaki galat/khaali list na dikhe)
                prev_selected_column_p10 = st.session_state.get("p10_archive_column_prev", None)
                prev_selected_subject_p10 = st.session_state.get("p10_archive_subject_filter", "All Subjects")
                subject_options_p10 = ["All Subjects"] + [s for s in unique_subjects_p10 if s != ""]
                if prev_selected_column_p10 != selected_column_p10 or prev_selected_subject_p10 not in subject_options_p10:
                    st.session_state["p10_archive_subject_filter"] = "All Subjects"
                st.session_state["p10_archive_column_prev"] = selected_column_p10

                with col_p10_f3:
                    selected_subject_p10 = st.selectbox(
                        "📚 Select Subject Filter:",
                        options=subject_options_p10,
                        key="p10_archive_subject_filter"
                    )

                render_archive = p10_authorized_db[archive_view_cols].copy()

                # 1️⃣ पहले selected COLUMN के आधार पर फ़िल्टर करें (agar value select ki ho)
                # 🟢 Ab ye filter hardcoded "Subject" column par nahi, balki upar chune gaye
                # "Select Column" (selected_column_p10) par kaam karta hai.
                if selected_subject_p10 != "All Subjects" and selected_column_p10 in render_archive.columns:
                    render_archive = render_archive[
                        render_archive[selected_column_p10].astype(str).str.strip() == selected_subject_p10
                    ]

                # 2️⃣ फिर Semester / Year scope के आधार पर फ़िल्टर करें
                # 🟢 Fix: पहले यहाँ "Current Year == साल" के साथ-साथ "Status == 'Regular Student'"
                # (हूबहू यही टेक्स्ट) की भी जरूरत पड़ती थी, और EX-STUDENT वाली condition कभी सही मैच
                # ही नहीं करती थी (क्योंकि EX-STUDENT का Current Year हमेशा सीधा "EX-STUDENT" ही सेट
                # होता है, "2nd Year" जैसा कुछ नहीं) — इसी वजह से पूरा Select Semester / Year Scope
                # सिस्टम काम नहीं कर रहा था। अब सीधा सिर्फ "Current Year" कॉलम से मैच किया जाता है,
                # जो असल डेटा के साथ सही तरीके से काम करता है।
                if chosen_option_p10 != "All Years":
                    render_archive = render_archive[
                        render_archive["Current Year"].astype(str).str.strip().str.upper() ==
                        str(target_db_year_p10).strip().upper()
                    ]

                render_archive = render_archive.reset_index(drop=True)
                render_archive.insert(0, "S. No.", range(1, len(render_archive) + 1))
                
                st.write(f"💾 पंजी लेजर में कुल सक्रिय छात्र प्रविष्टियाँ ('{chosen_option_p10}' | {selected_column_p10}: '{selected_subject_p10}'): **{len(render_archive)}**")
                
                # Strict read-only dataframe display to protect long-term archived columns
                st.dataframe(render_archive, use_container_width=True, hide_index=True)
                
                # Fast CSV archival download snapshot trigger (filtered scope ke sath)
                st.download_button(
                    label="📥 Download Complete Permanent Registry Snapshot (CSV)",
                    data=render_archive.drop(columns=["S. No."], errors="ignore").to_csv(index=False).encode('utf-8'),
                    file_name=f"permanent_registry_snapshot_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="p10_download_archive_btn_new"
                )

                # ==========================================================================
                # 🖨️ नया सब-मॉड्यूल: Roll-No Wise Printable Register List
                #    (CCE Foil जैसा Roll No. सॉर्ट इंजन, कस्टम रो-हाइट और पेज साइज़ के साथ)
                # ==========================================================================
                st.markdown("---")
                st.subheader("🖨️ Roll No. वाइज़ प्रिंट-योग्य रजिस्टर लिस्ट (S.No. / Roll No. / Student Name / Father Name)")
                st.markdown(
                    '<div style="background-color: #eef6ff; border-left: 5px solid #2563EB; padding: 10px; '
                    'border-radius: 4px; margin-bottom: 15px;">📌 यह लिस्ट Roll No. के अनुसार क्रम में (CCE Foil जैसे) '
                    'सॉर्ट होकर बनती है। आप यहाँ से तय कर सकते हैं कि एक पेज पर कितनी रो (Row) आएँगी और हर रो की ऊँचाई '
                    'कितनी mm, cm या inch होगी — फिर सीधा A4 पेज पर प्रिंट कर सकते हैं।</div>',
                    unsafe_allow_html=True
                )

                col_reg_c1, col_reg_c2, col_reg_c3 = st.columns(3)
                with col_reg_c1:
                    reg_rows_per_page = st.number_input(
                        "📄 एक पेज में कुल कितनी Row चाहिए:",
                        min_value=5, max_value=100, value=40, step=1,
                        key="p10_reg_rows_per_page"
                    )
                with col_reg_c2:
                    reg_row_height_val = st.number_input(
                        "📏 हर Row की ऊँचाई (वैल्यू दर्ज करें):",
                        min_value=1.0, value=8.0, step=0.5,
                        key="p10_reg_row_height_val"
                    )
                with col_reg_c3:
                    reg_row_height_unit = st.selectbox(
                        "📐 ऊँचाई की यूनिट चुनें:",
                        options=["mm", "cm", "Inch"],
                        key="p10_reg_row_height_unit"
                    )

                reg_unit_css_map = {"mm": "mm", "cm": "cm", "Inch": "in"}
                reg_unit_css = reg_unit_css_map.get(reg_row_height_unit, "mm")

                # 🟢 Column Select Engine — user jo columns select karega sirf wahi paper par print honge
                # 🟢 Fix: पहले सिर्फ 8 columns ही list में थे, अब सभी उपलब्ध columns (जो ऊपर register
                # ग्रिड में दिखते हैं) यहाँ भी दिख रहे हैं ताकि जो भी column चाहिए वो select किया जा सके।
                REG_ALL_PRINT_COLS = ["S. No."] + archive_view_cols
                if "p10_reg_selected_cols" not in st.session_state:
                    st.session_state.p10_reg_selected_cols = ["S. No.", "Roll No.", "Student Name", "Father Name"]
                else:
                    # पुराने session में सिर्फ पुरानी (सीमित) columns की selection saved थी — safety ke liye
                    # सिर्फ वही values रखें जो अब भी REG_ALL_PRINT_COLS में valid हैं
                    st.session_state.p10_reg_selected_cols = [
                        c for c in st.session_state.p10_reg_selected_cols if c in REG_ALL_PRINT_COLS
                    ]

                if "p10_show_print_cols_section" not in st.session_state:
                    st.session_state.p10_show_print_cols_section = True
                hdr_pcols_1, hdr_pcols_2 = st.columns([6, 1])
                with hdr_pcols_1:
                    st.markdown("**🧾 Print Columns चुनें (सिर्फ चुने हुए Column ही Paper पर आएंगे):**")
                with hdr_pcols_2:
                    if st.button("🙈 Hide" if st.session_state.p10_show_print_cols_section else "👁️ Unhide",
                                 key="p10_toggle_print_cols_section", use_container_width=True):
                        st.session_state.p10_show_print_cols_section = not st.session_state.p10_show_print_cols_section

                if st.session_state.p10_show_print_cols_section:
                    reg_chosen_cols_raw = st.multiselect(
                        "Columns:",
                        options=REG_ALL_PRINT_COLS,
                        default=st.session_state.p10_reg_selected_cols,
                        key="p10_reg_col_multiselect"
                    )
                    # Order hamesha REG_ALL_PRINT_COLS ke fixed sequence mein rahega, चाहे selection kisi bhi order mein ki ho
                    reg_selected_print_cols = [c for c in REG_ALL_PRINT_COLS if c in reg_chosen_cols_raw]
                    st.session_state.p10_reg_selected_cols = reg_selected_print_cols
                else:
                    st.caption("🙈 यह सेक्शन फ़िलहाल छुपा हुआ है। (Unhide करने पर पिछली सेटिंग बनी रहेगी)")
                    reg_selected_print_cols = st.session_state.p10_reg_selected_cols

                if not reg_selected_print_cols:
                    st.warning("⚠️ कृपया कम से कम एक Column select करें।")

                # 🟢 Column Width Resize Engine (Row Height jaisa hi — column select karke uski width set karo)
                # 🟢 Fix: अब हर column (नई जोड़ी गई सभी columns सहित) के लिए default width मौजूद है,
                # ताकि कोई भी नया column select करने पर error न आए।
                REG_DEFAULT_WIDTHS = {c: 12 for c in REG_ALL_PRINT_COLS}
                REG_DEFAULT_WIDTHS.update({
                    "S. No.": 8, "Roll No.": 10, "Duration": 8, "Category": 10, "Current Year": 10,
                    "Student Name": 20, "Father Name": 20, "Mother Name": 18, "Status": 10,
                    "Subject": 16, "Address": 16, "Eligibility Name": 14, "Admission Date": 10,
                    "Admission Year": 10, "Admission Session": 10
                })
                if "p10_reg_col_widths" not in st.session_state:
                    st.session_state.p10_reg_col_widths = dict(REG_DEFAULT_WIDTHS)
                # Agar purane session mein koi naya column missing ho to default jod do
                for _c, _w in REG_DEFAULT_WIDTHS.items():
                    if _c not in st.session_state.p10_reg_col_widths:
                        st.session_state.p10_reg_col_widths[_c] = _w

                if "p10_show_col_width_section" not in st.session_state:
                    st.session_state.p10_show_col_width_section = True

                if reg_selected_print_cols:
                    hdr_cw_1, hdr_cw_2 = st.columns([6, 1])
                    with hdr_cw_1:
                        st.markdown("**📏 Column Width Resize करें (जैसे Row Height करते हैं):**")
                    with hdr_cw_2:
                        if st.button("🙈 Hide" if st.session_state.p10_show_col_width_section else "👁️ Unhide",
                                     key="p10_toggle_col_width_section", use_container_width=True):
                            st.session_state.p10_show_col_width_section = not st.session_state.p10_show_col_width_section

                    if st.session_state.p10_show_col_width_section:
                        col_w1, col_w2, col_w3 = st.columns([2, 2, 1])
                        with col_w1:
                            reg_selected_col = st.selectbox(
                                "🧱 Column चुनें जिसकी Width बदलनी है:",
                                options=reg_selected_print_cols,
                                key="p10_reg_col_select"
                            )
                        with col_w2:
                            reg_new_width_val = st.number_input(
                                "📐 नई Width (%) दर्ज करें:",
                                min_value=5, max_value=70,
                                value=int(st.session_state.p10_reg_col_widths[reg_selected_col]),
                                step=1,
                                key=f"p10_reg_col_width_input_{reg_selected_col}"
                            )
                        with col_w3:
                            st.write("")
                            st.write("")
                            if st.button("✅ Apply Width", key="p10_reg_col_width_apply_btn", use_container_width=True):
                                st.session_state.p10_reg_col_widths[reg_selected_col] = reg_new_width_val
                                st.success(f"'{reg_selected_col}' की width अब {reg_new_width_val}% सेट हो गई है।")
                    else:
                        st.caption("🙈 यह सेक्शन फ़िलहाल छुपा हुआ है। (Unhide करने पर पिछली सेटिंग बनी रहेगी)")

                reg_col_widths = st.session_state.p10_reg_col_widths
                total_width_pct = sum(reg_col_widths[c] for c in reg_selected_print_cols) if reg_selected_print_cols else 0
                if reg_selected_print_cols and total_width_pct != 100:
                    st.caption(f"ℹ️ चुने हुए Columns की कुल Width अभी **{total_width_pct}%** है (आदर्श रूप से 100% होनी चाहिए, लेकिन टेबल फिर भी सही दिखेगी)।")

                # ======================================================================
                # 🌐 नया सब-मॉड्यूल: प्रिंट कॉलम ट्रांसलेशन इंजन (सिर्फ प्रिंट के लिए,
                # असली डेटाबेस में कोई बदलाव नहीं होगा — सिर्फ यह वाली रजिस्टर लिस्ट
                # चुनी हुई भाषा में दिखेगी/प्रिंट होगी)
                # ======================================================================
                st.markdown("---")
                tr_hdr_col1, tr_hdr_col2 = st.columns([5, 2])
                with tr_hdr_col1:
                    st.subheader("🌐 प्रिंट ट्रांसलेशन (वैकल्पिक)")
                with tr_hdr_col2:
                    st.write("")
                    if st.button("🧹 Clear Translation Cache", key="p10_clear_translation_cache_btn", use_container_width=True):
                        st.session_state.p10_reg_translation_cache = {}
                        st.success("✅ Translation cache साफ़ हो गई। अगली बार सभी values फिर से नई सिरे से ट्रांसलेट होंगी।")

                if not TRANSLATOR_AVAILABLE:
                    st.warning(
                        "⚠️ ट्रांसलेशन लाइब्रेरी इंस्टॉल नहीं है। इसे चालू करने के लिए टर्मिनल में "
                        "यह कमांड चलाएँ: `pip install deep-translator` — फिर ऐप को दोबारा शुरू करें।"
                    )
                    reg_translate_lang_code = "none"
                    reg_translate_cols_selected = []
                else:
                    # 🗣️ भाषाओं की स्क्रॉल लिस्ट — नाम + Google Translate कोड
                    REG_LANGUAGE_OPTIONS = {
                        "⬜ Normal (No Translation — जैसा है वैसा रखें)": "none",
                        "🇮🇳 Hindi (हिन्दी)": "hi",
                        "🇬🇧 English (अंग्रेज़ी)": "en",
                        "मराठी (Marathi)": "mr",
                        "ગુજરાતી (Gujarati)": "gu",
                        "ਪੰਜਾਬੀ (Punjabi)": "pa",
                        "বাংলা (Bengali)": "bn",
                        "தமிழ் (Tamil)": "ta",
                        "తెలుగు (Telugu)": "te",
                        "ಕನ್ನಡ (Kannada)": "kn",
                        "മലയാളം (Malayalam)": "ml",
                        "ଓଡ଼ିଆ (Odia)": "or",
                        "اردو (Urdu)": "ur",
                        "असमिया (Assamese)": "as",
                        "संस्कृत (Sanskrit)": "sa",
                        "नेपाली (Nepali)": "ne",
                        "अरबी (Arabic - العربية)": "ar",
                        "फ्रेंच (French)": "fr",
                        "स्पेनिश (Spanish)": "es",
                        "जर्मन (German)": "de",
                        "चीनी (Chinese - Simplified)": "zh-CN",
                        "जापानी (Japanese)": "ja",
                        "रूसी (Russian)": "ru",
                        "पुर्तगाली (Portuguese)": "pt",
                    }

                    col_tr1, col_tr2 = st.columns(2)
                    with col_tr1:
                        reg_translate_lang_label = st.selectbox(
                            "🈯 किस भाषा में प्रिंट करना है (भाषा चुनें):",
                            options=list(REG_LANGUAGE_OPTIONS.keys()),
                            key="p10_reg_translate_lang_select"
                        )
                        reg_translate_lang_code = REG_LANGUAGE_OPTIONS[reg_translate_lang_label]

                    with col_tr2:
                        reg_translatable_cols = [c for c in reg_selected_print_cols if c != "S. No."]
                        reg_translate_cols_selected = st.multiselect(
                            "🧾 कौन-कौन से Column ट्रांसलेट करने हैं:",
                            options=reg_translatable_cols,
                            default=[c for c in ["Category", "Subject", "Address", "Status"] if c in reg_translatable_cols],
                            key="p10_reg_translate_cols_select",
                            disabled=(reg_translate_lang_code == "none")
                        )

                    if reg_translate_lang_code != "none" and reg_translate_cols_selected:
                        st.caption(
                            f"ℹ️ **{reg_translate_lang_label}** भाषा में सिर्फ ये Columns ट्रांसलेट होकर प्रिंट होंगे: "
                            f"**{', '.join(reg_translate_cols_selected)}** — असली डेटाबेस पहले जैसा ही रहेगा, "
                            f"यह सिर्फ इस प्रिंट लिस्ट पर लागू होगा।"
                        )
                    elif reg_translate_lang_code == "none":
                        st.caption("ℹ️ **Normal** चुना हुआ है — सभी Columns अंग्रेज़ी/जैसी भी DB में हैं वैसी ही, बिना किसी बदलाव के प्रिंट होंगी।")

                # 🧠 ट्रांसलेशन कैश — एक बार ट्रांसलेट हो चुकी वैल्यू दोबारा API कॉल किए बिना यहीं से मिल जाएगी
                if "p10_reg_translation_cache" not in st.session_state:
                    st.session_state.p10_reg_translation_cache = {}

                # 🚨 Google कभी-कभी बहुत सारी requests एक साथ आने पर rate-limit/error-page
                # (जैसे "Error 500 (Server Error)!!1500...") वापस भेज देता है, और वो error-page
                # text galti se translation jaisa dikh sakta hai. Isliye har result ko validate
                # karte hain — agar usme ye error patterns dikhein to use turant reject kar dete hain.
                REG_TRANSLATE_ERROR_MARKERS = [
                    "error 500", "server error", "that's an error", "that's all we know",
                    "please try again later", "1500."
                ]

                def reg_is_bad_translation(result_text, original_text):
                    if not result_text:
                        return True
                    low = result_text.lower()
                    if any(marker in low for marker in REG_TRANSLATE_ERROR_MARKERS):
                        return True
                    # Google ka error-page result asli text se kaafi lamba hota hai (HTML/message)
                    if len(result_text) > (len(original_text) * 6 + 40):
                        return True
                    return False

                # 🟢 P10 FIX: naam wale columns (Student Name / Father Name / Mother Name) ko
                # kabhi "translate" nahi karna chahiye — translation ek meaning-based process hai
                # aur naam ka koi "meaning" translate nahi hota, isse ulti-seedhi cheez (jaise
                # "Manoj" ka "Your assessment" ban jaana) print ho jaati hai. Naamon ke liye humesha
                # TRANSLITERATION (sirf spelling ko Devanagari/target script me badalna) chahiye.
                REG_TRANSLIT_COLUMNS = NAME_CASE_COLUMNS  # ["Student Name", "Father Name", "Mother Name"]

                # Google Input Tools ka wahi transliteration engine jo online Hindi typing tools
                # use karte hain — ye naam ko translate nahi karta, sirf sahi spelling deta hai.
                REG_TRANSLIT_LANG_MAP = {
                    "hi": "hi-t-i0-und", "mr": "mr-t-i0-und", "gu": "gu-t-i0-und",
                    "pa": "pa-t-i0-und", "bn": "bn-t-i0-und", "ta": "ta-t-i0-und",
                    "te": "te-t-i0-und", "kn": "kn-t-i0-und", "ml": "ml-t-i0-und",
                    "or": "or-t-i0-und", "ur": "ur-t-i0-und", "ne": "ne-t-i0-und",
                    "as": "as-t-i0-und", "sa": "sa-t-i0-und",
                }

                def reg_translate_value(text_val, lang_code, max_retries=5):
                    """Ek single cell value ko chuni hui bhasha me translate karta hai, retry + cache ke sath.
                    max_retries badhaya gaya hai (3 -> 5) aur backoff lamba kiya gaya hai taaki
                    Google ke temporary rate-limit/error se translation beech me na ruke."""
                    text_str = "" if text_val is None else str(text_val).strip()
                    if lang_code == "none" or text_str == "" or text_str.lower() == "nan":
                        return text_val, True
                    cache_key = f"{lang_code}::{text_str}"
                    cache = st.session_state.p10_reg_translation_cache
                    if cache_key in cache:
                        return cache[cache_key], True

                    translated = text_str  # fallback: kuch bhi kaam na kare to original text hi rahega
                    success = False
                    for attempt in range(max_retries):
                        try:
                            result = GoogleTranslator(source="auto", target=lang_code).translate(text_str)
                            if result and not reg_is_bad_translation(result, text_str):
                                translated = result
                                success = True
                                break
                            # Bad/error-page result mila — thoda ruk kar dobara koshish karo
                            time.sleep(1.0 * (attempt + 1))
                        except Exception:
                            time.sleep(1.0 * (attempt + 1))

                    # 🚨 Safety net: agar phir bhi galti se error-page text aa gaya ho to use kabhi cache/print na karein
                    if reg_is_bad_translation(translated, text_str):
                        translated = text_str
                        success = False

                    cache[cache_key] = translated
                    time.sleep(0.2)  # har request ke beech chhota sa gap — Google ko rate-limit se bachane ke liye
                    return translated, success

                def reg_transliterate_name(text_val, lang_code, max_retries=4):
                    """Naam ko TRANSLATE nahi karta — sirf uski sahi spelling (transliteration)
                    target script me deta hai, jaise 'Manoj' -> 'मनोज'. Google Input Tools ke
                    transliteration engine se, har shabd (word) alag se bhejkar (taaki spacing na
                    bigde). Agar transliteration na ho paye (unsupported language ya network issue)
                    to seedhe translation API par fallback ho jaata hai."""
                    text_str = "" if text_val is None else str(text_val).strip()
                    if lang_code == "none" or text_str == "" or text_str.lower() == "nan":
                        return text_val, True

                    cache_key = f"translit::{lang_code}::{text_str}"
                    cache = st.session_state.p10_reg_translation_cache
                    if cache_key in cache:
                        return cache[cache_key], True

                    itc_code = REG_TRANSLIT_LANG_MAP.get(lang_code)
                    if not itc_code:
                        # Is language ke liye transliteration support nahi hai — seedha translate use karo
                        result_text, ok = reg_translate_value(text_str, lang_code)
                        cache[cache_key] = result_text
                        return result_text, ok

                    words = [w for w in text_str.split(" ") if w.strip() != ""]
                    translit_words = []
                    all_words_ok = True
                    for w_clean in words:
                        word_result = w_clean
                        word_ok = False
                        for attempt in range(max_retries):
                            try:
                                resp = requests.get(
                                    "https://inputtools.google.com/request",
                                    params={
                                        "text": w_clean, "itc": itc_code, "num": 1,
                                        "cp": 0, "cs": 1, "ie": "utf-8", "oe": "utf-8"
                                    },
                                    timeout=6
                                )
                                data = resp.json()
                                if (
                                    isinstance(data, list) and len(data) > 1 and data[0] == "SUCCESS"
                                    and data[1] and data[1][0][1]
                                ):
                                    word_result = data[1][0][1][0]
                                    word_ok = True
                                    break
                                time.sleep(0.5 * (attempt + 1))
                            except Exception:
                                time.sleep(0.5 * (attempt + 1))
                        translit_words.append(word_result)
                        if not word_ok:
                            all_words_ok = False
                        time.sleep(0.1)

                    result_text = " ".join(translit_words) if translit_words else text_str

                    if not all_words_ok:
                        # Kuch/sabhi shabd transliterate nahi ho paaye — translation API se poora naam
                        # dobara try karo taaki result khaali/adhoora na rahe
                        fallback_text, fallback_ok = reg_translate_value(text_str, lang_code)
                        if fallback_ok:
                            result_text = fallback_text
                            all_words_ok = True

                    cache[cache_key] = result_text
                    return result_text, all_words_ok

                # 🔤 List Order Selector — Roll No. के क्रम में, Student Name के अल्फाबेटिकल (A-Z) क्रम में,
                # या पहले Subject फिर उसके अंदर Student Name के अल्फाबेटिकल क्रम में
                reg_sort_order_choice = st.selectbox(
                    "🔀 लिस्ट किस क्रम में प्रिंट करें (Sort Order):",
                    options=[
                        "Roll No. (संख्या क्रम में)",
                        "Student Name (अल्फाबेटिक A-Z क्रम में)",
                        "Subject → Student Name (पहले Subject, फिर नाम अनुसार A-Z)"
                    ],
                    key="p10_reg_sort_order_choice"
                )

                if st.button("🔄 Generate Roll-Wise Printable Register List", type="primary", use_container_width=True, key="p10_reg_generate_btn"):
                    st.session_state.p10_reg_list_generated = True

                # 🟢 Side-by-Side Layout selector: कम columns select होने पर एक ही पेज पर
                # 2 या 3 लिस्ट (एक साथ पास-पास) प्रिंट होंगी ताकि पेज की खाली जगह बर्बाद न हो।
                # अब यह सिर्फ ON/OFF checkbox नहीं, बल्कि user khud decide kar sakta hai ki
                # 1 (Normal), 2 (Side-by-Side) ya 3 (Triple) list ek page par chahiye.
                reg_default_layout_count = 2 if len(reg_selected_print_cols) <= 4 else 1
                reg_layout_options = [
                    "1 (Normal — एक ही लिस्ट)",
                    "2 (Side-by-Side — दो लिस्ट)",
                    "3 (Triple — तीन लिस्ट)"
                ]
                reg_layout_choice = st.selectbox(
                    "📰 एक Page पर कितनी लिस्ट दिखाएं (Side-by-Side Layout):",
                    options=reg_layout_options,
                    index=(reg_default_layout_count - 1),
                    key="p10_reg_side_by_side_layout_count"
                )
                reg_layout_count = int(reg_layout_choice.split(" ")[0])
                reg_side_by_side = reg_layout_count > 1
                if reg_side_by_side:
                    st.caption(f"ℹ️ ऊपर दी गई 'एक Page में कुल कितनी Row' वैल्यू अब **हर लिस्ट (हर हिस्से) की row count** मानी जाएगी (कुल {reg_layout_count} लिस्ट एक Page पर)।")

                if st.session_state.get("p10_reg_list_generated", False) and reg_selected_print_cols:
                    # 🟢 Fix: ab yahan upar wale Subject + Semester/Year filter se hi
                    # filtered data (render_archive) use hoga, poore DB (p10_authorized_db) se nahi
                    reg_src_df = render_archive.drop(columns=["S. No."], errors="ignore").copy()

                    if "Roll No." not in reg_src_df.columns:
                        st.warning("⚠️ डेटाबेस में 'Roll No.' कॉलम नहीं मिला।")
                    else:
                        if reg_sort_order_choice.startswith("Subject"):
                            # 🔤 पहले Subject के अल्फाबेटिक क्रम में, फिर उसी Subject के अंदर Student Name A-Z
                            reg_src_df["_sort_key_1"] = reg_src_df.get("Subject", "").astype(str).str.strip().str.upper()
                            reg_src_df["_sort_key_2"] = reg_src_df.get("Student Name", "").astype(str).str.strip().str.upper()
                            reg_src_df = reg_src_df.sort_values(
                                by=["_sort_key_1", "_sort_key_2"], ascending=[True, True]
                            ).drop(columns=["_sort_key_1", "_sort_key_2"]).reset_index(drop=True)
                        elif reg_sort_order_choice.startswith("Student Name"):
                            # 🔤 Alphabetical (A-Z) क्रम — Student Name के आधार पर
                            reg_src_df["_sort_key"] = reg_src_df.get("Student Name", "").astype(str).str.strip().str.upper()
                            reg_src_df = reg_src_df.sort_values(
                                by=["_sort_key"], ascending=[True]
                            ).drop(columns=["_sort_key"]).reset_index(drop=True)
                        else:
                            # 🔢 CCE Foil जैसा ही Roll No. सॉर्ट इंजन (न्यूमेरिक क्रम में)
                            reg_src_df["_sort_key"] = pd.to_numeric(reg_src_df["Roll No."], errors="coerce")
                            reg_src_df = reg_src_df.sort_values(
                                by=["_sort_key", "Roll No."], ascending=[True, True]
                            ).drop(columns=["_sort_key"]).reset_index(drop=True)

                        # "S. No." data column nahi hai (wo page ke hisaab se calculate hota hai),
                        # baaki sab actual database columns hain
                        reg_data_cols_needed = [c for c in reg_selected_print_cols if c != "S. No."]
                        for c in reg_data_cols_needed:
                            if c not in reg_src_df.columns:
                                reg_src_df[c] = ""
                        reg_records = reg_src_df[reg_data_cols_needed].to_dict(orient="records") if reg_data_cols_needed else [{} for _ in range(len(reg_src_df))]

                        # 🌐 चुने गए Column(s) की वैल्यू को चुनी हुई भाषा में ट्रांसलेट करें
                        # (सिर्फ इसी प्रिंट लिस्ट के लिए — असली live_db बिल्कुल अनछुआ रहता है)
                        if TRANSLATOR_AVAILABLE and reg_translate_lang_code != "none" and reg_translate_cols_selected:
                            translate_progress_bar = st.progress(0.0, text="🌐 चुने गए Columns ट्रांसलेट किए जा रहे हैं...")
                            total_translate_steps = max(len(reg_translate_cols_selected), 1)
                            reg_translate_fail_report = {}  # column -> list of values jo translate/transliterate nahi ho paaye
                            for step_i, t_col in enumerate(reg_translate_cols_selected):
                                if t_col in reg_data_cols_needed:
                                    # पहले उस column की सिर्फ unique values निकालें ताकि बार-बार एक ही
                                    # value को translate करने पर API कॉल्स waste न हों
                                    unique_vals = sorted(set(str(r.get(t_col, "")) for r in reg_records))
                                    value_translation_map = {}
                                    failed_vals = []
                                    for uv in unique_vals:
                                        # 🟢 FIX: naam wale columns (Student Name/Father Name/Mother Name)
                                        # ko TRANSLATE nahi, TRANSLITERATE karte hain — isse "Manoj" jaisa
                                        # naam "मनोज" bane, na ki koi ulta-seedha translated phrase.
                                        if t_col in REG_TRANSLIT_COLUMNS:
                                            result_val, was_ok = reg_transliterate_name(uv, reg_translate_lang_code)
                                        else:
                                            result_val, was_ok = reg_translate_value(uv, reg_translate_lang_code)
                                        value_translation_map[uv] = result_val
                                        if not was_ok and uv.strip() != "":
                                            failed_vals.append(uv)
                                    if failed_vals:
                                        reg_translate_fail_report[t_col] = failed_vals
                                    for rec in reg_records:
                                        original_val = str(rec.get(t_col, ""))
                                        rec[t_col] = value_translation_map.get(original_val, original_val)
                                translate_progress_bar.progress((step_i + 1) / total_translate_steps)
                            translate_progress_bar.empty()

                            # 🟢 FIX: pehle translation fail hone par chup-chaap original English reh jaata
                            # tha aur user ko pata hi nahi chalta tha ki kaunsi values reh gayin. Ab saaf-saaf
                            # dikha denge ki kaunsi values translate/transliterate nahi ho paayin (agar koi hui to).
                            if reg_translate_fail_report:
                                fail_lines = [
                                    f"**{col}**: {', '.join(vals[:15])}" + (f" ... (+{len(vals)-15} और)" if len(vals) > 15 else "")
                                    for col, vals in reg_translate_fail_report.items()
                                ]
                                st.warning(
                                    "⚠️ इंटरनेट/Google सर्विस की अस्थायी समस्या की वजह से नीचे दी गई values पूरी तरह "
                                    "ट्रांसलेट/ट्रांसलिटरेट नहीं हो पाईं और अंग्रेज़ी में ही रह गई हैं। दोबारा 'Generate' बटन दबाएँ, "
                                    "आमतौर पर दूसरी कोशिश में ये ठीक हो जाती हैं:\n\n" + "\n\n".join(fail_lines)
                                )

                        if len(reg_records) == 0:
                            st.warning(f"🔍 चयनित Subject ('{selected_subject_p10}') और '{chosen_option_p10}' scope के आधार पर रजिस्टर लिस्ट बनाने के लिए कोई रिकॉर्ड नहीं मिला।")
                        else:
                            rows_per_page_int = int(reg_rows_per_page)

                            # हर column के लिए alignment तय करें (नंबर वाले columns center में, बाकी left में)
                            reg_center_cols = {"S. No.", "Unique ID", "Student Abc Id", "Roll No.", "Mobile Number", "Current Year", "Duration", "Admission Year"}

                            # 🛠️ एक block (single list table) की HTML बनाने वाला helper — Side-by-Side और Normal दोनों में इस्तेमाल होगा
                            def build_reg_block_table(records_chunk, start_sno):
                                block_rows_html = ""
                                for i, rec in enumerate(records_chunk):
                                    overall_sno = start_sno + i + 1
                                    row_cells_html = ""
                                    for col_name in reg_selected_print_cols:
                                        cell_val = overall_sno if col_name == "S. No." else rec.get(col_name, "")
                                        align = "center" if col_name in reg_center_cols else "left"
                                        row_cells_html += f'<td style="border:1px solid #000; text-align:{align}; padding:2px 6px;">{cell_val}</td>'
                                    block_rows_html += f"""
                                        <tr style="height:{reg_row_height_val}{reg_unit_css};">
                                            {row_cells_html}
                                        </tr>
                                    """
                                block_header_html = "".join(
                                    f'<th style="border:1px solid #000; width:{reg_col_widths[c]}%;">{c}</th>'
                                    for c in reg_selected_print_cols
                                )
                                return f"""
                                    <table style="width:100%; border-collapse:collapse; table-layout:fixed; font-family:Arial, sans-serif; font-size:11px;">
                                        <thead>
                                            <tr style="height:{reg_row_height_val}{reg_unit_css}; background:#f2f2f2;">
                                                {block_header_html}
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {block_rows_html}
                                        </tbody>
                                    </table>
                                """

                            pages_html_parts = []

                            if reg_side_by_side:
                                # 🟢 हर पेज पर reg_layout_count (2 या 3) blocks पास-पास दिखेंगे
                                # (row count = rows_per_page_int प्रति block/लिस्ट)
                                import math
                                blocks_per_page = reg_layout_count
                                per_page_capacity = rows_per_page_int * blocks_per_page
                                total_pages_needed = math.ceil(len(reg_records) / per_page_capacity) if len(reg_records) > 0 else 1
                                reg_total_pages_for_summary = total_pages_needed

                                # हर block की width % (छोटे gaps छोड़कर) — 2 blocks ke liye ~48.5%, 3 ke liye ~32%
                                block_gap_pct = 3
                                block_width_pct = (100 - (block_gap_pct * (blocks_per_page - 1))) / blocks_per_page

                                for page_no in range(1, total_pages_needed + 1):
                                    page_start = (page_no - 1) * per_page_capacity
                                    block_divs_html = ""
                                    for b_idx in range(blocks_per_page):
                                        b_start = page_start + (b_idx * rows_per_page_int)
                                        b_chunk = reg_records[b_start: b_start + rows_per_page_int]
                                        b_table_html = build_reg_block_table(b_chunk, b_start)
                                        block_divs_html += f'<div style="width:{block_width_pct}%;">{b_table_html}</div>'

                                    pages_html_parts.append(f"""
                                        <div class="a4-reg-page">
                                            <div style="text-align:center; font-weight:bold; font-size:15px; margin-bottom:8px; letter-spacing:1px;">
                                                PERMANENT REGISTER — ROLL NO. WISE STUDENT LIST ({chosen_option_p10} | {selected_subject_p10}) (Page {page_no} of {total_pages_needed})
                                            </div>
                                            <div style="display:flex; justify-content:space-between; gap:{block_gap_pct}%;">
                                                {block_divs_html}
                                            </div>
                                        </div>
                                    """)
                            else:
                                # सामान्य (सिंगल कॉलम) लेआउट — पहले जैसा
                                reg_pages = [
                                    reg_records[i:i + rows_per_page_int]
                                    for i in range(0, len(reg_records), rows_per_page_int)
                                ]
                                reg_total_pages_for_summary = len(reg_pages)
                                for page_no, page_rows in enumerate(reg_pages, start=1):
                                    table_html = build_reg_block_table(page_rows, (page_no - 1) * rows_per_page_int)
                                    pages_html_parts.append(f"""
                                        <div class="a4-reg-page">
                                            <div style="text-align:center; font-weight:bold; font-size:15px; margin-bottom:8px; letter-spacing:1px;">
                                                PERMANENT REGISTER — ROLL NO. WISE STUDENT LIST ({chosen_option_p10} | {selected_subject_p10}) (Page {page_no} of {len(reg_pages)})
                                            </div>
                                            {table_html}
                                        </div>
                                    """)

                            reg_pages_html = "".join(pages_html_parts)

                            reg_print_template = f"""
                            <html>
                            <head>
                                <style>
                                    @page {{ size: A4 portrait; margin: 10mm; }}
                                    body {{
                                        font-family: Arial, sans-serif; margin: 0; padding: 20px;
                                        background-color: #f0f2f5; display: flex; flex-direction: column; align-items: center;
                                    }}
                                    .a4-reg-page {{
                                        box-sizing: border-box; width: 210mm; min-height: 297mm; padding: 15mm;
                                        margin-bottom: 30px; background: #ffffff !important;
                                        box-shadow: 0 4px 12px rgba(0,0,0,0.15); page-break-after: always;
                                    }}
                                    @media print {{
                                        body {{ background-color: #fff; padding: 0; }}
                                        .a4-reg-page {{
                                            width: 100%; min-height: auto; padding: 0; margin-bottom: 0;
                                            box-shadow: none; page-break-after: always !important;
                                        }}
                                    }}
                                </style>
                            </head>
                            <body>
                                {reg_pages_html}
                            </body>
                            </html>
                            """

                            reg_width_summary = " / ".join(f"{c}: {reg_col_widths[c]}%" for c in reg_selected_print_cols)
                            st.write(f"🧾 फ़िल्टर: **{chosen_option_p10} | Subject: {selected_subject_p10}** | कुल स्टूडेंट: **{len(reg_records)}** | कुल पेज बनेंगे: **{reg_total_pages_for_summary}** | प्रति पेज/साइड रो: **{rows_per_page_int}** | रो हाइट: **{reg_row_height_val} {reg_row_height_unit}** | कॉलम विड्थ: **{reg_width_summary}**")

                            st.components.v1.html(reg_print_template, height=800, scrolling=True)

                            reg_safe_html_string = reg_print_template.replace("\\", "\\\\").replace("`", "'").replace("\n", " ").replace("\r", "")

                            st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
                            components.html(
                                f"""
                                <html>
                                <body>
                                    <script>
                                    function printRegisterList() {{
                                        var iframe = window.parent.document.createElement('iframe');
                                        iframe.style.position = 'fixed'; iframe.style.right = '0'; iframe.style.bottom = '0';
                                        iframe.style.width = '0'; iframe.style.height = '0'; iframe.style.border = '0';
                                        window.parent.document.body.appendChild(iframe);

                                        var doc = iframe.contentWindow.document;
                                        doc.open(); doc.write(`{reg_safe_html_string}`); doc.close();
                                        iframe.contentWindow.focus(); iframe.contentWindow.print();

                                        setTimeout(function() {{ window.parent.document.body.removeChild(iframe); }}, 1000);
                                    }}
                                    </script>
                                    <button onclick="printRegisterList()" style="
                                        width: 100%; background-color: #28a745; color: white; padding: 14px;
                                        border: none; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 16px;
                                        font-family: sans-serif; box-shadow: 0 4px 6px rgba(40, 167, 69, 0.2);">
                                        🖨️ Click Here to Print Roll-Wise Register List (A4 Size)
                                    </button>
                                </body>
                                </html>
                                """,
                                height=60
                            )

        # ----------------------------------------------------------------------
        # P11: ADVANCED PANEL-WISE COLUMN TWIN MAPPING SYSTEM (Fixed Core Sync)
        # ----------------------------------------------------------------------
        elif current_panel_id == "P11":
            st.header(f"📢 {get_panel_title('P11')} (Advanced Panel Column Linker)")
            
            # 🟢 Corrected Safe Single-Quote Concatenation Format
            st.markdown(
                '<div style="background-color: #f4fbf7; border-left: 5px solid #2e7d32; padding: 12px; border-radius: 4px; margin-bottom: 20px;">'
                '🎯 <b>कंट्रोल निर्देश:</b> यहाँ से आप किसी भी एक वर्किंग पैनल (P1 से P15) के कॉलम को किसी दूसरे पैनल के कॉलम के साथ आपस में जोड़ सकते हैं।'
                '<br>1. बाईं तरफ (Source) वह पैनल और कॉलम चुनें जहां से डेटा सिंक करना शुरू करना है।'
                '<br>2. दाईं तरफ (Target) वह पैनल और कॉलम चुनें जिसके साथ डेटा लिंक और एक्सचेंज करना है।'
                '<br><br>⚠️ <b>नो न्यू कॉलम पॉलिसी:</b> सिस्टम डेटाबेस में कोई भी नया कॉलम नहीं बनाएगा। दोनों पैनल्स के चुने गए कॉलम्स के बीच बैकएंड डेटा लाइव एक्सचेंज और सिंक हो जाएगा।'
                '</div>', 
                unsafe_allow_html=True
            )
            
            # मुख्य डेटाबेस के सभी 22+ प्रमाणित कॉलम्स
            all_22_columns = [
                "Admission Application Number", "Roll No.", "Enrollment No.", "Student Name", "Father Name", 
                "Admission Year", "Admission Session", "Eligibility Name", "Admission Date", "Unique ID", 
                "Application Enrollment No.", "Mother Name", "Date of Birth", "Category", "Subject", 
                "Duration", "Mobile Number", "Email ID", "Address", "Status", "Current Year", "Payment Date"
            ]
            
            # 🟢 P1 और P15 सहित सभी पैनल्स और उनके कॉलम की कम्प्लीट लिस्ट
            panel_columns_repository = {
                "Panel 1: Data entry Onboarding": all_22_columns,
                "Panel 2: Admission panel": ["Application Number", "Payment Date", "Admission Year", "Admission Session", "Student Name", "Father Name", "Mobile Number", "Status"],
                "Panel 3: Unique ID panel": ["Admission Application Number", "Student Name", "Father Name", "Unique ID"],
                "Panel 4: Roll No. panel": ["Admission Application Number", "Unique ID", "Student Name", "Roll No."],
                "Panel 5: Enrollment panel": ["Admission Application Number", "Student Name", "Subject", "Enrollment No."],
                "Panel 6: Scholarship panel": ["Admission Application Number", "Unique ID", "Student Name", "Category", "Scholarship Name", "Scholarship Status"],
                "Panel 7: CCE panel": all_22_columns,
                "Panel 8: Promotion panel": all_22_columns,
                "Panel 9: Result panel": ["Admission Application Number", "Roll No.", "Enrollment No.", "Student Name", "Father Name", "Marks Obtained", "Result Status", "Exam Remarks"],
                "Panel 10: Register panel": all_22_columns,
                "Panel 15: Super-Admin Master Control": all_22_columns
            }
            
            current_twins = load_twin_mappings()
            
            st.subheader("🔗 लिंक करें पैनल्स के जुड़वाँ कॉलम्स (Link Panel Columns)")
            
            # लेआउट को 4 कॉलम ग्रिड में विभाजित किया गया है
            col_p11_left_p, col_p11_left_c, col_p11_right_p, col_p11_right_c = st.columns(4)
            
            with col_p11_left_p:
                # 1. LEFT SIDE - PANEL SELECT
                left_panel = st.selectbox(
                    "🏢 1. सोर्स पैनल चुनें (From Panel):",
                    options=list(panel_columns_repository.keys()),
                    key="p11_left_panel_select"
                )
                
            with col_p11_left_c:
                # 2. LEFT SIDE - COLUMN SELECT
                left_available_cols = panel_columns_repository[left_panel]
                src_selection = st.selectbox(
                    "⬅️ 2. सोर्स कॉलम (Source Column):",
                    options=left_available_cols,
                    key="p11_left_col_select"
                )
                
            with col_p11_right_p:
                # 3. RIGHT SIDE - PANEL SELECT
                right_panel = st.selectbox(
                    "🏢 3. टारगेट पैनल चुनें (To Panel):",
                    options=list(panel_columns_repository.keys()),
                    key="p11_right_panel_select"
                )
                
            with col_p11_right_c:
                # 4. RIGHT SIDE - COLUMN SELECT
                right_available_cols = panel_columns_repository[right_panel]
                tgt_selection = st.selectbox(
                    "➡️ 4. टारगेट कॉलम (Target Column):",
                    options=right_available_cols,
                    key="p11_right_col_select"
                )
            
            # फाइनल सबमिशन बटन
            btn_label = f"🔗 सिंक सक्रिय करें: {left_panel.split(':')[0]} ({src_selection}) ↔ {right_panel.split(':')[0]} ({tgt_selection})"
            if st.button(btn_label, type="primary", use_container_width=True):
                if left_panel == right_panel and src_selection == tgt_selection:
                    st.error("❌ आप एक ही पैनल के एक ही कॉलम को खुद से लिंक नहीं कर सकते! कृपया अलग कॉलम नाम या पैनल चुनें।")
                else:
                    # बैकएंड मैपिंग स्कीमा में मैप को सेव करें
                    current_twins[src_selection] = tgt_selection
                    save_twin_mappings(current_twins)
                    st.success(f"🎉 सफलता! `{left_panel.split(':')[0]}` के `{src_selection}` और `{right_panel.split(':')[0]}` के `{tgt_selection}` के बीच लाइव डेटा सिंक कनेक्शन स्थापित हो गया है।")
                    st.balloons()
                    st.rerun()
            
            # भाग 2: वर्तमान में सक्रिय मैपिंग की लिस्ट और डिलीट करने का विकल्प
            st.markdown("---")
            st.subheader("📋 वर्तमान सक्रिय जुड़वाँ कॉलम्स की सूची (Active Mappings)")
            
            if not current_twins:
                st.info("💡 वर्तमान में कोई डायनेमिक मैपिंग सेट नहीं है। डेटाबेस अपने डिफ़ॉल्ट रूप में काम कर रहा है।")
            else:
                active_maps_list = [
                    {
                        "S.No.": i + 1,
                        "Source Column Connection": k,
                        "Target Column Linked": v,
                        "Type": "🔒 Permanent (Fixed)" if k in PERMANENT_TWIN_MAPPINGS else "✏️ Custom"
                    }
                    for i, (k, v) in enumerate(current_twins.items())
                ]
                st.dataframe(pd.DataFrame(active_maps_list), use_container_width=True, hide_index=True)
                st.caption("🔒 **Permanent (Fixed)** मैपिंग्स कोड में हमेशा के लिए सेट हैं — ये कभी डिलीट नहीं होंगी, चाहे JSON फ़ाइल रीसेट/डिलीट हो जाए।")
                
                # 🔒 PERMANENT FIX: सिर्फ वही मैपिंग्स डिलीट की जा सकती हैं जो Permanent list में नहीं हैं
                deletable_twins = {k: v for k, v in current_twins.items() if k not in PERMANENT_TWIN_MAPPINGS}
                
                st.markdown("##### 🗑️ मैपिंग हटाएं (Remove Link)")
                if not deletable_twins:
                    st.info("🔒 इस समय सिर्फ Permanent (Fixed) मैपिंग्स सक्रिय हैं, जिन्हें हटाया नहीं जा सकता।")
                else:
                    mapping_to_delete = st.selectbox("हटाने के लिए मैपिंग चुनें:", options=list(deletable_twins.keys()), format_func=lambda x: f"{x} ↔ {deletable_twins[x]}")
                    
                    if st.button("🗑️ सिंक कनेक्शन तोड़ें (Delete Mapping)", type="secondary", use_container_width=True):
                        if mapping_to_delete in current_twins and mapping_to_delete not in PERMANENT_TWIN_MAPPINGS:
                            del current_twins[mapping_to_delete]
                            save_twin_mappings(current_twins)
                            st.error("💥 मैपिंग सफलतापूर्वक हटा दी गई है!")
                            st.rerun()

        # ----------------------------------------------------------------------
        # P12: DASH BOARD EDITER MODULE (Pre-Login & Notice Customizer Combined)
        # ----------------------------------------------------------------------
        elif current_panel_id == "P12":
            st.header(f"📚 {get_panel_title('P12')} (Subject + Year wise Syllabus Upload / Link Manager)")

            st.markdown(
                '<div style="background-color: #fcf8e3; border-left: 5px solid #f0ad4e; padding: 12px; border-radius: 4px; margin-bottom: 20px;">'
                '📌 <b>निर्देश:</b> डेटाबेस में मौजूद हर <b>Subject</b> के लिए, हर <b>Year</b> (1st Year, 2nd Year...) के हिसाब से अलग-अलग '
                '<b>Syllabus File अपलोड</b> कर सकते हैं या उसका <b>Link (URL)</b> दे सकते हैं। यही Syllabus होम पेज (Desk Board) पर '
                'बिना लॉगिन किए भी छात्रों को दिखेगा — वो अपना Subject और Year चुनकर सीधे Syllabus पा सकेंगे। '
                '(नोट: Notice Board और Header/Branding Settings अब <b>Panel Admin (P15)</b> से मैनेज होती हैं।)'
                '</div>',
                unsafe_allow_html=True
            )

            p12_can_edit = role in ("full_admin", "p12_role")
            if not p12_can_edit:
                st.warning("🔒 **रीड-ओनली मोड:** आपके पास यहाँ Syllabus अपलोड/एडिट करने का अधिकार नहीं है — आप सिर्फ मौजूदा Syllabus देख/डाउनलोड कर सकते हैं।")

            p12_live_db = load_live_data()
            p12_subject_list = []
            if "Subject" in p12_live_db.columns:
                p12_subject_list = sorted([
                    s for s in p12_live_db["Subject"].dropna().astype(str).str.strip().unique()
                    if s and s.lower() != "nan"
                ])

            if not p12_subject_list:
                st.info("ℹ️ अभी तक डेटाबेस में कोई Subject उपलब्ध नहीं है। पहले P1 (Data Onboarding) से Students जोड़ें — उनके Subjects यहाँ अपने-आप दिखने लगेंगे।")
            else:
                # 🟢 Data structure ab nested hai: { Subject: { Year: {"type","value","file_name"} } }
                p12_syllabus_data = load_syllabus_data()
                st.caption(f"📚 कुल **{len(p12_subject_list)}** Subjects मिले — हर Subject के अंदर अब **Year-wise** Syllabus सेट कर सकते हैं।")

                for p12_subj in p12_subject_list:
                    p12_safe_subj_key = _re_notice_link.sub(r'[^A-Za-z0-9_-]+', '_', p12_subj)
                    p12_subj_years = p12_syllabus_data.get(p12_subj, {})
                    # 🟢 FIX: fixed 6 Years ki jagah ab is Subject ki asli Duration ke
                    # hisaab se hi Years ki list banti hai (jaise 3 saal ka course ho to
                    # sirf 3 Years hi dikhenge)
                    p12_yr_count = get_subject_syllabus_year_count(p12_subj, p12_live_db)

                    # 🟢 नया: PG कोर्सेज़ (जैसे 2 Year का कोर्स) के लिए अब Year-wise की जगह
                    # Semester-wise भी Syllabus सेट किया जा सकता है — 2 Year = 4 Semester,
                    # 3 Year = 6 Semester वगैरह। हर Subject अपनी चुनी हुई Mode याद रखता है
                    # (डेटा फ़ाइल में "__mode__" key में सेव होती है), ताकि दोबारा खोलने पर
                    # सही Mode (Year / Semester) अपने आप दिखे।
                    p12_saved_mode = p12_subj_years.get("__mode__", "year")
                    p12_mode_options = ["📅 Year-wise", "📆 Semester-wise (PG)"]
                    p12_mode_default_idx = 1 if p12_saved_mode == "semester" else 0
                    p12_chosen_mode_raw = st.radio(
                        f"**{p12_subj}** — Syllabus किस हिसाब से सेट करें?",
                        options=p12_mode_options,
                        index=p12_mode_default_idx,
                        key=f"p12_period_mode_{p12_safe_subj_key}",
                        horizontal=True,
                        disabled=not p12_can_edit
                    )
                    p12_chosen_mode = "semester" if p12_chosen_mode_raw == p12_mode_options[1] else "year"
                    if p12_can_edit and p12_chosen_mode != p12_saved_mode:
                        p12_subj_years["__mode__"] = p12_chosen_mode
                        p12_syllabus_data[p12_subj] = p12_subj_years
                        save_syllabus_data(p12_syllabus_data)

                    if p12_chosen_mode == "semester":
                        # PG जैसे कोर्स: N Year = N × 2 Semester (ज़्यादा से ज़्यादा 12 Semester)
                        p12_sem_count = min(p12_yr_count * 2, len(SYLLABUS_SEM_OPTIONS))
                        p12_years_for_subject = SYLLABUS_SEM_OPTIONS[:p12_sem_count]
                        p12_period_word = "Semester"
                    else:
                        p12_years_for_subject = SYLLABUS_YEAR_OPTIONS[:p12_yr_count]
                        p12_period_word = "Year"

                    p12_years_done = sum(1 for _y in p12_years_for_subject if _y in p12_subj_years)
                    with st.expander(f"📘 {p12_subj}  —  ({p12_years_done}/{len(p12_years_for_subject)} {p12_period_word} की Syllabus सेट है)", expanded=False):

                        # --- मौजूदा सभी Year/Semester का status एक साथ दिखाएँ ---
                        for p12_yr in p12_years_for_subject:
                            p12_yr_existing = p12_subj_years.get(p12_yr, {})
                            p12_yr_safe_key = f"{p12_safe_subj_key}__{_re_notice_link.sub(r'[^A-Za-z0-9_-]+', '_', p12_yr)}"
                            st.markdown(f"**🗓️ {p12_yr}**")
                            p12_status_col, p12_action_col = st.columns([3, 2])

                            with p12_status_col:
                                if p12_yr_existing.get("type") == "file" and p12_yr_existing.get("value") and os.path.exists(p12_yr_existing["value"]):
                                    st.success(f"✅ फ़ाइल मौजूद: **{p12_yr_existing.get('file_name', os.path.basename(p12_yr_existing['value']))}**")
                                elif p12_yr_existing.get("type") == "link" and p12_yr_existing.get("value"):
                                    st.success("✅ Link मौजूद है:")
                                    st.markdown(f"🔗 [Syllabus खोलें (नए टैब में)]({p12_yr_existing['value']})")
                                else:
                                    st.info("अभी तक कोई Syllabus नहीं जोड़ा गया।")

                            with p12_action_col:
                                if p12_yr_existing.get("type") == "file" and p12_yr_existing.get("value") and os.path.exists(p12_yr_existing["value"]):
                                    try:
                                        with open(p12_yr_existing["value"], "rb") as p12_fh:
                                            st.download_button(
                                                "⬇️ Download",
                                                data=p12_fh.read(),
                                                file_name=p12_yr_existing.get("file_name", os.path.basename(p12_yr_existing["value"])),
                                                key=f"p12_dl_{p12_yr_safe_key}",
                                                use_container_width=True
                                            )
                                    except Exception:
                                        st.error("⚠️ फ़ाइल पढ़ने में समस्या।")
                                if p12_can_edit and p12_yr_existing:
                                    if st.button("🗑️ हटाएँ", key=f"p12_remove_{p12_yr_safe_key}", use_container_width=True):
                                        if p12_yr_existing.get("type") == "file" and p12_yr_existing.get("value") and os.path.exists(p12_yr_existing["value"]):
                                            try:
                                                os.remove(p12_yr_existing["value"])
                                            except Exception:
                                                pass
                                        del p12_subj_years[p12_yr]
                                        p12_syllabus_data[p12_subj] = p12_subj_years
                                        save_syllabus_data(p12_syllabus_data)
                                        st.success(f"🗑️ {p12_subj} — {p12_yr} का Syllabus हटा दिया गया।")
                                        st.rerun()

                            if p12_can_edit:
                                p12_mode = st.radio(
                                    f"{p12_yr} के लिए Syllabus कैसे जोड़ें/बदलें?",
                                    ["📎 File Upload", "🔗 Link (URL)"],
                                    key=f"p12_mode_{p12_yr_safe_key}",
                                    horizontal=True,
                                    label_visibility="collapsed"
                                )
                                if p12_mode == "📎 File Upload":
                                    p12_up_file = st.file_uploader(
                                        f"{p12_yr} — Syllabus File चुनें (PDF/DOC/DOCX/Image):",
                                        type=["pdf", "doc", "docx", "png", "jpg", "jpeg"],
                                        key=f"p12_upl_{p12_yr_safe_key}",
                                        label_visibility="collapsed"
                                    )
                                    if st.button(f"💾 {p12_yr} — File Save करें", key=f"p12_savefile_{p12_yr_safe_key}", use_container_width=True):
                                        if p12_up_file is not None:
                                            os.makedirs(SYLLABUS_UPLOAD_DIR, exist_ok=True)
                                            p12_ext = os.path.splitext(p12_up_file.name)[1] or ".pdf"
                                            p12_save_path = os.path.join(SYLLABUS_UPLOAD_DIR, f"{p12_yr_safe_key}{p12_ext}")
                                            with open(p12_save_path, "wb") as p12_fo:
                                                p12_fo.write(p12_up_file.getvalue())
                                            p12_subj_years[p12_yr] = {
                                                "type": "file", "value": p12_save_path, "file_name": p12_up_file.name
                                            }
                                            p12_syllabus_data[p12_subj] = p12_subj_years
                                            save_syllabus_data(p12_syllabus_data)
                                            st.success(f"🎉 {p12_subj} — {p12_yr} के लिए Syllabus फ़ाइल सेव हो गई!")
                                            st.rerun()
                                        else:
                                            st.warning("⚠️ पहले कोई फ़ाइल चुनें, फिर Save करें।")
                                else:
                                    p12_default_link = p12_yr_existing.get("value", "") if p12_yr_existing.get("type") == "link" else ""
                                    p12_link_val = st.text_input(
                                        f"{p12_yr} — Syllabus Link (URL) डालें:",
                                        value=p12_default_link,
                                        key=f"p12_link_{p12_yr_safe_key}",
                                        placeholder="https://...",
                                        label_visibility="collapsed"
                                    )
                                    if st.button(f"💾 {p12_yr} — Link Save करें", key=f"p12_savelink_{p12_yr_safe_key}", use_container_width=True):
                                        if p12_link_val.strip():
                                            p12_subj_years[p12_yr] = {"type": "link", "value": p12_link_val.strip(), "file_name": ""}
                                            p12_syllabus_data[p12_subj] = p12_subj_years
                                            save_syllabus_data(p12_syllabus_data)
                                            st.success(f"🎉 {p12_subj} — {p12_yr} के लिए Syllabus Link सेव हो गया!")
                                            st.rerun()
                                        else:
                                            st.warning("⚠️ Link खाली नहीं छोड़ सकते।")
                            st.markdown("---")

        # ======================================================================
        # P13: 🔀 MERGE & APPROVE PANEL (Complete Integrated Routing System)
        # ======================================================================
        elif current_panel_id == "P13":
            st.header(f"🔀 {get_panel_title('P13')} (Live Multi-Column Merge Verification & Routing Room)")
            
            # Load the staging verification queue and main central repository
            stage_db = load_stage_data()
            master_db_lookup = load_live_data()
            
            if stage_db.empty:
                st.success("🟢 शानदार! स्टेजिंग कतार पूर्णतः खाली है। पैनल 1 से भेजी गयी सभी फाइलें प्रोसेस की जा चुकी हैं।")
            else:
                # 🟢 Corrected Safe Inline String Setup
                st.markdown(
                    '<div style="background-color: #EEF2F8; border-left: 5px solid #0F2A4A; padding: 12px; border-radius: 4px; margin-bottom: 20px;">'
                    '🎯 <b>कन्फर्मेशन मर्ज गाइड:</b> पहले वह पैनल (Main File) चुनें जिसका डेटा बदलना है, फिर स्टेजिंग से नई फ़ाइल (Anya File) चुनकर लाइव मैचिंग चेक करें। यदि मर्ज नहीं करना है तो सीधे अप्रूव करें।'
                    '</div>', 
                    unsafe_allow_html=True
                )
                
                # ----------------------------------------------------------------------
                # 👑 स्टेप 1: MAIN FILE (पैनल से डेटा का चयन और लाइव प्रीव्यू)
                # ----------------------------------------------------------------------
                st.subheader("👑 Step 1: Select Main File Panel")
                panel_options_map = {
                    "Panel 2: Admission View": "P2", "Panel 3: Unique ID View": "P3",
                    "Panel 4: Roll No View": "P4", "Panel 5: Enrollment View": "P5",
                    "Panel 6: Scholarship View": "P6", "Panel 7: CCE panel View": "P7",
                    "Panel 8: Promotion panel View": "P8", "Panel 9: Result panel View": "P9",
                    "Panel 10: Register panel View": "P10"
                }
                
                selected_main_panel_lbl = st.selectbox(
                    "निरीक्षण और अपडेट करने के लिए मुख्य पैनल (Main File Source) चुनें:",
                    options=list(panel_options_map.keys()),
                    key="p13_main_panel_dropdown_v15"
                )
                target_main_panel_id = panel_options_map[selected_main_panel_lbl]
                
                # Fetch approved records tied to the selected workspace platform visibility token
                main_file_db = master_db_lookup[master_db_lookup["Target Panel Visibility"] == target_main_panel_id].copy()
                
                st.write(f"📊 **Main File (Approved DB):** `{selected_main_panel_lbl}` | वर्तमान रिकॉर्ड्स संख्या: `{len(main_file_db)}`")
                if not main_file_db.empty:
                    with st.expander("👁️ मुख्य फ़ाइल (Main File) का पूरा लाइव डेटा देखें", expanded=False):
                        st.dataframe(main_file_db[[c for c in ["Admission Year", "Application Number", "Student Name", "Father Name", "Subject"] if c in main_file_db.columns]], use_container_width=True)
                else:
                    st.warning("⚠️ इस चयनित पैनल में वर्तमान में कोई स्वीकृत डेटा उपलब्ध नहीं है।")

                # ----------------------------------------------------------------------
                # 📄 स्टेप 2: ANYA FILE (स्टेजिंग कतार से नई फ़ाइल का चयन)
                # ----------------------------------------------------------------------
                st.markdown("---")
                st.subheader("📄 Step 2: Select Anya File (New Uploaded Staging File)")
                distinct_files = list(stage_db["Uploaded File Name"].unique())
                
                selected_anya_file = st.selectbox(
                    "स्टेजिंग कतार से वह नई फ़ाइल चुनें जिससे डेटा खींचना है (या सीधे अप्रूव करने के लिए छोड़ें):", 
                    options=["-- कोई अन्य फ़ाइल नहीं चुनें --"] + distinct_files,
                    key="p13_anya_file_select_v15"
                )

                # ----------------------------------------------------------------------
                # 🚀 केस ए: बिना मर्ज किए सीधे अप्रूव करने का मैकेनिज्म (Direct Approve Window)
                # ----------------------------------------------------------------------
                if selected_anya_file == "-- कोई अन्य फ़ाइल नहीं चुनें --":
                    st.markdown("---")
                    st.subheader("🚀 बिना मर्ज किए सीधे अप्रूव करें (Direct Approval Window)")
                    
                    direct_target_file_name = distinct_files[0] if distinct_files else ""
                    
                    if not direct_target_file_name:
                        st.warning("कतार में कोई फ़ाइल उपलब्ध नहीं है।")
                    else:
                        file_subset_direct = stage_db[stage_db["Uploaded File Name"] == direct_target_file_name].copy()
                        st.info(f"💡 वर्तमान में स्टेजिंग कतार की फ़ाइल '**{direct_target_file_name}**' को इसके मूल रूप में सीधे किसी भी वर्किंग पैनल पर भेजने के लिए नीचे सेटिंग्स चुनें।")
                        
                        col_dir1, col_dir2 = st.columns(2)
                        with col_dir1:
                            direct_routing_panel = st.selectbox(
                                "📌 इस फ़ाइल को किस विशिष्ट वर्किंग पैनल पर विज़िबल करना है?",
                                options=[
                                    "P2 : Admission panel",
                                    "P3 : Unique ID panel",
                                    "P4 : Roll No. panel",
                                    "P5 : Enrollment panel",
                                    "P6 : Scholarship panel",
                                    "P7 : CCE panel",
                                    "P8 : Promotion panel",
                                    "P9 : Result panel",
                                    "P10 : Register panel"
                                ],
                                key="p13_direct_panel_routing_dropdown_v15"
                            )
                            parsed_direct_panel_id = direct_routing_panel.split(" : ")[0].strip()
                            
                        with col_dir2:
                            st.write("")
                            st.write("")
                            direct_approve_btn = st.button("🚀 सीधे अप्रूव करें (Direct Approve & Sync)", type="primary", use_container_width=True, key="p13_direct_approve_btn_v15")
                        
                        with st.expander("⚠️ डेंजर ज़ोन: इस फ़ाइल को स्टेजिंग से हटाएं (बिना अप्रूव किए)", expanded=False):
                            confirm_delete_dir = st.checkbox("हाँ, मैं इस फ़ाइल को पूरी तरह कतार से हटाना चाहता हूँ।", key="confirm_delete_dir_key_v15")
                            if st.button("🗑️ इस फ़ाइल को डिलीट करें", type="primary", use_container_width=True, disabled=not confirm_delete_dir):
                                updated_stage_db = stage_db[stage_db["Uploaded File Name"] != direct_target_file_name]
                                save_stage_data(updated_stage_db)
                                st.error(f"💥 फ़ाइल '{direct_target_file_name}' हटा दी गई!")
                                st.rerun()

                        if direct_approve_btn:
                            try:
                                file_subset_direct["Target Panel Visibility"] = parsed_direct_panel_id
                                
                                # 1. नाम बदलने से पहले ही डुप्लिकेट कॉलम हटाएँ
                                file_subset_direct = file_subset_direct.loc[:, ~file_subset_direct.columns.duplicated()].copy()
                                
                                # Remap layout variables to protect 22 column structural norms
                                column_mapping_fixes = {
                                    "Unique Id": "Unique ID", 
                                    "Date Of Birth": "Date of Birth", "Duretion": "Duration", 
                                    "Email Id": "Email ID", "Year": "Current Year"
                                }
                                file_subset_direct = file_subset_direct.rename(columns=column_mapping_fixes)
                                
                                # 2. नाम बदलने के बाद भी यदि कोई डुप्लिकेट बनता है तो साफ़ करें
                                file_subset_direct = file_subset_direct.loc[:, ~file_subset_direct.columns.duplicated()].copy()
                                
                                # सुरक्षित असाइनमेंट
                                if "Application Number" not in file_subset_direct.columns:
                                    if "Admission Application Number" in file_subset_direct.columns:
                                        file_subset_direct["Application Number"] = file_subset_direct["Admission Application Number"].astype(str)
                                    else:
                                        file_subset_direct["Application Number"] = ""
                                
                                # 3. सुनिश्चित करें कि टारगेट कॉलम्स का ढांचा साफ़ हो
                                for col in DEFAULT_COLUMNS:
                                    if col not in file_subset_direct.columns:
                                        file_subset_direct[col] = ""
                                        
                                # 4. मास्टर डेटाबेस के डुप्लिकेट कॉलम्स भी हटाएँ ताकि जोड़ने में एरर न आए
                                master_db_clean = master_db_lookup.loc[:, ~master_db_lookup.columns.duplicated()].copy()
                                remaining_master_db_dir = master_db_clean[master_db_clean["Target Panel Visibility"] != parsed_direct_panel_id].copy()
                                
                                # 5. अंतिम सुरक्षित कॉनकेट (Concat)
                                final_direct_master = pd.concat([remaining_master_db_dir, file_subset_direct[DEFAULT_COLUMNS]], ignore_index=True)
                                save_live_data(final_direct_master)
                                
                                remaining_stage_db_dir = stage_db[stage_db["Uploaded File Name"] != direct_target_file_name]
                                save_stage_data(remaining_stage_db_dir)
                                
                                st.success(f"🎉 शत-प्रतिशत सफलता! आपकी फ़ाइल बिना किसी बदलाव के सीधे स्वीकृत होकर {parsed_direct_panel_id} पैनल पर लाइव हो चुकी है!")
                                st.balloons()
                                st.rerun()
                            except Exception as dir_err:
                                st.error(f"सीधे अप्रूवल चक्र के दौरान तकनीकी समस्या आई: {dir_err}")

                # ----------------------------------------------------------------------
                # 🔍 केस बी: जब यूजर मर्ज करने के लिए स्टेजिंग से कोई ANYA FILE सेलेक्ट करता है
                # ----------------------------------------------------------------------
                else:
                    anya_file_subset = stage_db[stage_db["Uploaded File Name"] == selected_anya_file].copy()
                    # 🆕 Unique ID / Roll No. file ke headers ki alag spelling (Unique Id, Roll No, Roll Number...) ko standard naam par lao,
                    # taaki merge ke baad ye main file ke "Unique ID" / "Roll No." column me hi bharein (alag duplicate column na bane)
                    _anya_alias = {"Unique Id": "Unique ID", "UniqueID": "Unique ID", "Unique id": "Unique ID",
                                   "Roll No": "Roll No.", "Roll Number": "Roll No.", "Roll no.": "Roll No.", "Roll No.": "Roll No."}
                    anya_file_subset = anya_file_subset.rename(columns={k: v for k, v in _anya_alias.items() if k in anya_file_subset.columns and v not in anya_file_subset.columns})
                    st.write(f"📦 **Anya File (Staging Column Source):** `{selected_anya_file}` | छात्र रिकॉर्ड्स: `{len(anya_file_subset)}`")

                    with st.expander("⚠️ डेंजर ज़ोन: गलत फ़ाइल को स्टेजिंग से हटाएं", expanded=False):
                        st.warning(f"क्या आप निश्चित रूप से फ़ाइल '**{selected_anya_file}**' को स्टेजिंग कतार से हटाना चाहते हैं?")
                        confirm_delete = st.checkbox("हाँ, मैं इस फ़ाइल को डिलीट करना चाहता हूँ।", key="confirm_delete_v15")
                        if st.button("🗑️ परमानेंटली डिलीट करें", type="primary", use_container_width=True, disabled=not confirm_delete):
                            updated_stage_db = stage_db[stage_db["Uploaded File Name"] != selected_anya_file]
                            save_stage_data(updated_stage_db)
                            st.error(f"💥 फ़ाइल '{selected_anya_file}' हटा दी गई!")
                            st.rerun()

                    st.markdown("---")
                    st.subheader("🔍 Step 3: Configure Matching & Columns Data Retrieval")
                    
                    if main_file_db.empty:
                        st.info("💡 अन्य फ़ाइल से मर्ज करने के लिए मुख्य पैनल में कम से कम एक डेटा रिकॉर्ड होना आवश्यक है।")
                    else:
                        col_m1, col_m2 = st.columns(2)
                        with col_m1:
                            main_match_key = st.selectbox(
                                "Main File का मैचिंग कॉलम चुनें (जैसे Application Number):",
                                options=list(main_file_db.columns),
                                key="xl_main_match_key_v15"
                            )
                        with col_m2:
                            anya_match_key = st.selectbox(
                                "Anya File का मैचिंग कॉलम चुनें (जैसे Application Number):",
                                options=list(anya_file_subset.columns),
                                key="xl_anya_match_key_v15"
                            )
                            
                        anya_return_cols = st.multiselect(
                            "Anya File के वे कॉलम्स चुनें जिनका डेटा Main File में भरना है (जैसे B, C, D कॉलम्स):",
                            options=[c for c in anya_file_subset.columns if c not in ["Uploaded File Name", "Target Panel Visibility"]],
                            default=[c for c in ["Student Name", "Father Name", "Mother Name", "Unique ID", "Roll No.", "Enrollment No."] if c in anya_file_subset.columns],
                            key="xl_anya_return_cols_v15"
                        )

                        # ----------------------------------------------------------------------
                        # 👁️ Live Merge Preview Engine
                        # ----------------------------------------------------------------------
                        if anya_return_cols:
                            try:
                                main_file_db[main_match_key] = main_file_db[main_match_key].astype(str).str.strip()
                                anya_file_subset[anya_match_key] = anya_file_subset[anya_match_key].astype(str).str.strip()
                                
                                anya_clean = anya_file_subset[[anya_match_key] + [c for c in anya_return_cols if c != anya_match_key]].copy().drop_duplicates(subset=[anya_match_key])
                                
                                preview_merged = pd.merge(
                                    main_file_db,
                                    anya_clean,
                                    left_on=main_match_key,
                                    right_on=anya_match_key,
                                    how='left',
                                    suffixes=('', '_new_data')
                                )
                                
                                for col in anya_return_cols:
                                    new_col_name = f"{col}_new_data" if f"{col}_new_data" in preview_merged.columns else col
                                    if new_col_name in preview_merged.columns:
                                        preview_merged[col] = preview_merged[new_col_name].fillna(preview_merged[col]).astype(str)
                                
                                if main_match_key in preview_merged.columns:
                                    if f"{main_match_key}_new_data" in preview_merged.columns:
                                        preview_merged[main_match_key] = preview_merged[main_match_key].fillna(preview_merged[f"{main_match_key}_new_data"])
                                
                                keep_preview_cols = [c for c in preview_merged.columns if not c.endswith('_new_data') and c != f"{anya_match_key}_y"]
                                final_preview_df = preview_merged[keep_preview_cols].copy()
                                
                                if main_match_key not in final_preview_df.columns and f"{main_match_key}_x" in final_preview_df.columns:
                                    final_preview_df = final_preview_df.rename(columns={f"{main_match_key}_x": main_match_key})
                                
                                st.markdown("#### 📈 Live Merge Preview (जांचें कि सही मर्ज है या नहीं)")
                                st.caption("नीचे दी गई तालिका दिखा रही है कि अप्रूव करने पर मेन फ़ाइल में डेटा किस प्रकार अपडेट होकर सेव होगा:")
                                
                                preview_display_cols = list(set(["Admission Year", main_match_key, "Student Name", "Father Name", "Target Panel Visibility"] + anya_return_cols))
                                st.dataframe(final_preview_df[[c for c in preview_display_cols if c in final_preview_df.columns]], use_container_width=True)
                                
                                # ----------------------------------------------------------------------
                                # 🚀 Step 4: Finalize & Precision Approve
                                # ----------------------------------------------------------------------
                                st.markdown("---")
                                st.subheader("🚀 Step 4: Finalize & Precision Approve")
                                
                                col_app1, col_app2 = st.columns(2)
                                with col_app1:
                                    target_routing_panel = st.selectbox(
                                        "📌 इस स्वीकृत डेटा को किस वर्किंग पैनल पर विज़िबल रखना है?",
                                        options=[
                                            "P2 : Admission panel",
                                            "P3 : Unique ID panel",
                                            "P4 : Roll No. panel",
                                            "P5 : Enrollment panel",
                                            "P6 : Scholarship panel",
                                            "P7 : CCE panel",
                                            "P8 : Promotion panel",
                                            "P9 : Result panel",
                                            "P10 : Register panel"
                                        ],
                                        key="p13_target_panel_routing_dropdown_v15"
                                    )
                                    parsed_panel_id = target_routing_panel.split(" : ")[0].strip()
                                    
                                with col_app2:
                                    st.write("")
                                    st.write("")
                                    approve_action_btn = st.button("🚀 Approve & Update Selected Data Rows", type="primary", use_container_width=True, key="p13_final_approve_btn_v15")
                                
                                if approve_action_btn:
                                    try:
                                        # 1. किसी भी तरह के डुप्लिकेट कॉलम को पहले ही साफ़ करें
                                        final_preview_df = final_preview_df.loc[:, ~final_preview_df.columns.duplicated()].copy()
                                        
                                        final_preview_df["Target Panel Visibility"] = parsed_panel_id
                                        
                                        # 2. पुराने कॉलम नामों को प्रमाणित स्कीमों में बदलें
                                        column_mapping_fixes = {
                                            "Unique Id": "Unique ID", 
                                            "Date Of Birth": "Date of Birth", "Duretion": "Duration", 
                                            "Email Id": "Email ID", "Year": "Current Year"
                                        }
                                        final_preview_df = final_preview_df.rename(columns=column_mapping_fixes)
                                        
                                        # 3. नाम बदलने के बाद यदि फिर से कोई डुप्लिकेट बनता है, तो उसे दोबारा साफ़ करें
                                        final_preview_df = final_preview_df.loc[:, ~final_preview_df.columns.duplicated()].copy()
                                        
                                        # 4. 🔴 एरर फिक्स सुरक्षित असाइनमेंट इंजन:
                                        # चेक करें कि 'Application Number' कॉलम मौजूद है या नहीं
                                        if "Application Number" in final_preview_df.columns:
                                            # सुनिश्चित करें कि हम डेटाफ्रेम नहीं, बल्कि उसकी वैल्यू या सीरीज़ ही ले रहे हैं
                                            app_num_data = final_preview_df["Application Number"]
                                            if isinstance(app_num_data, pd.DataFrame):
                                                final_preview_df["Application Number"] = app_num_data.iloc[:, 0].astype(str)
                                            else:
                                                final_preview_df["Application Number"] = app_num_data.astype(str)
                                        elif "Admission Application Number" in final_preview_df.columns:
                                            adm_app_data = final_preview_df["Admission Application Number"]
                                            if isinstance(adm_app_data, pd.DataFrame):
                                                final_preview_df["Application Number"] = adm_app_data.iloc[:, 0].astype(str)
                                            else:
                                                final_preview_df["Application Number"] = adm_app_data.astype(str)
                                        else:
                                            final_preview_df["Application Number"] = ""

                                        # 5. मास्टर डेटाबेस से पुराना विज़िबिलिटी डेटा साफ़ करें
                                        remaining_master_db = master_db_lookup[master_db_lookup["Target Panel Visibility"] != parsed_panel_id].copy()
                                        remaining_master_db = remaining_master_db.loc[:, ~remaining_master_db.columns.duplicated()].copy()
                                        
                                        # 6. सभी आवश्यक DEFAULT_COLUMNS को सुरक्षित सेट करें
                                        for col in DEFAULT_COLUMNS:
                                            if col not in final_preview_df.columns:
                                                final_preview_df[col] = ""
                                                
                                        # 7. केवल एकल और ओरिजिनल कॉलम्स का सुरक्षित संकलन (Concat)
                                        final_updated_master_db = pd.concat([remaining_master_db, final_preview_df[DEFAULT_COLUMNS]], ignore_index=True)
                                        save_live_data(final_updated_master_db)
                                        
                                        # 8. स्टेजिंग कतार से प्रविष्टि हटाएं
                                        remaining_stage_db = stage_db[stage_db["Uploaded File Name"] != selected_anya_file]
                                        save_stage_data(remaining_stage_db)
                                        
                                        st.success(f"🎉 शत-प्रतिशत सफलता! Anya फ़ाइल का डेटा मुख्य फ़ाइल में सही जगह अपडेट होकर और मैचिंग कॉलम के साथ {parsed_panel_id} पर लाइव हो चुका है!")
                                        st.balloons()
                                        st.rerun()
                                        
                                    except Exception as inner_merge_err:
                                        st.error(f"मर्ज डेटाबेस सेव चक्र के दौरान तकनीकी समस्या आई: {inner_merge_err}")
                                    
                                    # Normalize alternate key names to standardized core database headers before final commit
                                    column_mapping_fixes = {
                                        "Unique Id": "Unique ID", 
                                        "Date Of Birth": "Date of Birth", "Duretion": "Duration", 
                                        "Email Id": "Email ID", "Year": "Current Year",
                                        "Application Number": "Admission Application Number"
                                    }
                                    final_preview_df = final_preview_df.rename(columns=column_mapping_fixes)
                                    if "Application Number" not in final_preview_df.columns and "Admission Application Number" in final_preview_df.columns:
                                        final_preview_df["Application Number"] = final_preview_df["Admission Application Number"]

                                    remaining_master_db = master_db_lookup[master_db_lookup["Target Panel Visibility"] != parsed_panel_id].copy()
                                    
                                    for col in DEFAULT_COLUMNS:
                                        if col not in final_preview_df.columns:
                                            final_preview_df[col] = ""
                                            
                                    final_updated_master_db = pd.concat([remaining_master_db, final_preview_df[DEFAULT_COLUMNS]], ignore_index=True)
                                    save_live_data(final_updated_master_db)
                                    
                                    remaining_stage_db = stage_db[stage_db["Uploaded File Name"] != selected_anya_file]
                                    save_stage_data(remaining_stage_db)
                                    
                                    st.success(f"🎉 शत-प्रतिशत सफलता! Anya फ़ाइल का डेटा मुख्य फ़ाइल में सही जगह अपडेट होकर और मैचिंग कॉलम के साथ {parsed_panel_id} पर लाइव हो चुका है!")
                                    st.balloons()
                                    st.rerun()
                                    
                            except Exception as merge_err:
                                st.error(f"लाइव मर्ज वेरिफिकेशन के दौरान तकनीकी समस्या आई: {merge_err}")
                        else:
                            st.info("💡 कृपया प्रीव्यू और अपडेट इंजन को सक्रिय करने के लिए Step 3 से कम से कम एक रिटर्न कॉलम ज़रूर चुनें।")

        # ----------------------------------------------------------------------
        # P14: PANEL VIEWER (INTEGRATED INDEX SYSTEM - Isolated Inspector Window)
        # ----------------------------------------------------------------------
        elif current_panel_id == "P14":
            st.header(f"👁️ {get_panel_title('P14')} (Multi-Panel Inspection Window)")

            # Standardized 22 core fields mapping per target layout configuration
            all_22_columns = [
                "Admission Application Number", "Roll No.", "Enrollment No.", "Student Name", "Father Name", 
                "Admission Year", "Admission Session", "Eligibility Name", "Admission Date", "Unique ID", 
                "Application Enrollment No.", "Mother Name", "Date of Birth", "Category", "Subject", 
                "Duration", "Mobile Number", "Email ID", "Address", "Status", "Current Year", "Payment Date"
            ]

            # Structural column profiles customized per workspace panel selection
            panel_options_list = {
                "Panel 2: Admission View": all_22_columns,
                "Panel 3: Unique ID View": ["Admission Application Number", "Student Name", "Father Name", "Unique ID"],
                "Panel 4: Roll No View": ["Admission Application Number", "Unique ID", "Student Name", "Roll No."],
                "Panel 5: Enrollment View": ["Admission Application Number", "Student Name", "Subject", "Enrollment No."],
                "Panel 6: Scholarship View": ["Admission Application Number", "Unique ID", "Student Name", "Category", "Scholarship Name", "Scholarship Status"],
                "Panel 7: CCE panel View": all_22_columns,
                "Panel 8: Promotion panel View": all_22_columns,
                "Panel 9: Result panel View": all_22_columns,
                "Panel 10: Register panel View": all_22_columns
            }

            st.subheader("📂 Select Panel Dashboard View")
            selected_panel_view = st.selectbox(
                "निरीक्षण करने के लिए पैनल सूची चुनें (Select Dashboard to Inspect):",
                options=list(panel_options_list.keys()),
                key="p14_panel_selector_dropdown_secure_v15"
            )

            # Map selection labels to their exact database target visibility tracking tags
            panel_id_map = {
                "Panel 2: Admission View": "P2", "Panel 3: Unique ID View": "P3",
                "Panel 4: Roll No View": "P4", "Panel 5: Enrollment View": "P5",
                "Panel 6: Scholarship View": "P6", "Panel 7: CCE panel View": "P7",
                "Panel 8: Promotion panel View": "P8", "Panel 9: Result panel View": "P9",
                "Panel 10: Register panel View": "P10"
            }
            target_panel_id = panel_id_map[selected_panel_view]
            target_columns = panel_options_list[selected_panel_view]

            # 🔍 Isolated Firewall Query Rule: Filter centralized records matching visibility tokens
            view_filtered_db = live_db[live_db["Target Panel Visibility"] == target_panel_id].copy()

            # Normalization translator dictionary to prevent cell mismatches or blank structures
            column_mapping_fixes = {
                "Unique Id": "Unique ID", "Student Abc Id": "Unique ID", 
                "Date Of Birth": "Date of Birth", "Duretion": "Duration", 
                "Email Id": "Email ID", "Year": "Current Year",
                "Application Number": "Admission Application Number",
                "Enrollment No": "Enrollment No."
            }
            view_filtered_db = view_filtered_db.rename(columns=column_mapping_fixes)
            if "Application Number" in view_filtered_db.columns and "Admission Application Number" not in view_filtered_db.columns:
                view_filtered_db["Admission Application Number"] = view_filtered_db["Application Number"]

            # Populate any structural column keys missing from memory
            for c_col in target_columns:
                if c_col not in view_filtered_db.columns:
                    view_filtered_db[c_col] = ""

            st.markdown(f"### 📋 {selected_panel_view} - Isolated Inspection Records")
            
            col_search1, col_search2 = st.columns(2)
            with col_search1:
                search_target_col = st.selectbox("खोजने के लिए फ़ील्ड चुनें:", options=target_columns, key="p14_search_col_target_secure_v15")
            with col_search2:
                search_query_text = st.text_input(f"'{search_target_col}' में प्रविष्टि खोजें:", key="p14_query_val_text_secure_v15").strip()

            if search_query_text != "":
                # 🟢 डुप्लिकेट कॉलम एरर फिक्स इंजन
                col_data = view_filtered_db[search_target_col]
                search_series = col_data.iloc[:, 0] if isinstance(col_data, pd.DataFrame) else col_data
                
                view_filtered_db = view_filtered_db[
                    search_series.astype(str).str.contains(search_query_text, case=False, na=False)
                ]

            st.write(f"वर्तमान ग्रिड में कुल उपलब्ध स्वीकृत छात्र रिकॉर्ड संख्या: **{len(view_filtered_db)}**")

            final_render_cols = [col for col in target_columns if col in view_filtered_db.columns]
            
            if not view_filtered_db.empty:
                display_ready_df = view_filtered_db[final_render_cols].copy()
                display_ready_df.insert(0, "S. No.", range(1, len(display_ready_df) + 1))
            
                # 🟢 एरर फिक्स: डुप्लिकेट कॉलम को डिलीट करने के लिए यह लाइन यहाँ जोड़ें
                display_ready_df = display_ready_df.loc[:, ~display_ready_df.columns.duplicated()].copy()
            
                st.dataframe(display_ready_df, use_container_width=True, hide_index=True)
                
                st.download_button(
                    label=f"📥 Download Selected Dashboard Report Snapshot (CSV)",
                    data=view_filtered_db[final_render_cols].to_csv(index=False).encode('utf-8'),
                    file_name=f"{selected_panel_view.replace(':', '').replace(' ', '_').lower()}_snapshot.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="p14_download_compiled_report_btn_secure_v15"
                )
            else:
                st.warning("🔍 निर्दिष्ट खोज प्रविष्टि या स्वीकृत पैनल विज़िबिलिटी के आधार पर कोई रिकॉर्ड नहीं मिला।")

        # ----------------------------------------------------------------------
        # P15: PANEL ADMIN (15 PANELS SUPREME ENGINE & NOTICE BOARD MANAGER)
        # ----------------------------------------------------------------------
        elif current_panel_id == "P15":
            st.header(f"🛠️ {get_panel_title('P15')} (Full Super-Admin Control Command)")
            
            # 📢 Live Notice Board Manager Panel Area
            hdr_c1_p15_show_notice_board, hdr_c2_p15_show_notice_board = st.columns([6, 1])
            with hdr_c1_p15_show_notice_board:
                st.subheader("📢 Live Notice Board Manager")
            with hdr_c2_p15_show_notice_board:
                if st.button("🙈 Hide" if st.session_state.get("p15_show_notice_board", True) else "👁️ Unhide", key="p15_show_notice_board_toggle_btn", use_container_width=True):
                    st.session_state["p15_show_notice_board"] = not st.session_state.get("p15_show_notice_board", True)
                    st.rerun()

            if st.session_state.get("p15_show_notice_board", True):
                with st.expander("कॉलेज सूचना पटल (Official Notice Board) की गाइडलाइंस एडिट करें", expanded=True):
                    with st.form(key="p15_global_notice_form_final_secure"):
                        updated_notice_input = st.text_area(
                            "सूचना पटल की पंक्तियाँ लिखें (प्रत्येक नई लाइन मुख्य पेज पर एक नया पॉइंट बनेगी):",
                            value=st.session_state.notice_text,
                            height=150,
                            key="p15_notice_text_area_input_final_secure"
                        )
                        if st.form_submit_button("Publish & Save Notice Board Permanently", type="primary", use_container_width=True):
                            st.session_state.notice_text = updated_notice_input
                            save_notice_board(updated_notice_input)
                            st.success("🎉 कॉलेज सूचना पटल सफलतापूर्वक अपडेट हो गया है! यह बिना लॉगिन वाले होम पेज पर लाइव दिखाई देगा।")
                            st.rerun()

            st.markdown("---")

            # --- (P12 se yahan shift kiya gaya) Header Elements & Branding Themes ---
            hdr_c1_p15_show_header_branding, hdr_c2_p15_show_header_branding = st.columns([6, 1])
            with hdr_c1_p15_show_header_branding:
                st.subheader("🖼️ Header Elements & Branding Themes")
            with hdr_c2_p15_show_header_branding:
                if st.button("🙈 Hide" if st.session_state.get("p15_show_header_branding", True) else "👁️ Unhide", key="p15_show_header_branding_toggle_btn", use_container_width=True):
                    st.session_state["p15_show_header_branding"] = not st.session_state.get("p15_show_header_branding", True)
                    st.rerun()

            if st.session_state.get("p15_show_header_branding", True):
                with st.form(key="p15_landing_view_editor_form_secure"):
                    col_view1, col_view2 = st.columns(2)
                    with col_view1:
                        header_toggle = st.checkbox(
                            "Display Institutional Header Text Block", 
                            value=bool(st.session_state.pre_login_config.get("show_header_text", True))
                        )
                        mantra_text = st.text_input(
                            "Spiritual Invocation / Mantra Text:", 
                            value=str(st.session_state.pre_login_config.get("header_mantra", "ॐ श्री गुरवे नमः"))
                        )
                    with col_view2:
                        system_title_text = st.text_input(
                            "Main Gateway Application Title:", 
                            value=str(st.session_state.pre_login_config.get("system_title", "Permanent Shared Live Database System"))
                        )

                    st.markdown("##### 🔤 Header Text Font Size")
                    col_font1, col_font2 = st.columns(2)
                    with col_font1:
                        mantra_font_size = st.slider(
                            "Spiritual Invocation / Mantra — Font Size (px):",
                            min_value=10, max_value=60,
                            value=int(st.session_state.pre_login_config.get("header_mantra_font_size", 24)),
                            key="p15_mantra_font_size_slider"
                        )
                    with col_font2:
                        title_font_size = st.slider(
                            "Main Gateway Application Title — Font Size (px):",
                            min_value=10, max_value=80,
                            value=int(st.session_state.pre_login_config.get("header_title_font_size", 32)),
                            key="p15_title_font_size_slider"
                        )

                    st.markdown("##### Notice Board Branding Colors")
                    col_theme1, col_theme2 = st.columns(2)
                    with col_theme1:
                        border_color = st.color_picker(
                            "Left Accent Border Color:",
                            value=str(st.session_state.pre_login_config.get("notice_board_border_color", "#FF5733"))
                        )
                    with col_theme2:
                        bg_color = st.color_picker(
                            "Container Background Surface Color:", 
                            value=str(st.session_state.pre_login_config.get("notice_board_bg_color", "#f9f9f9"))
                        )
                    
                    submit_settings = st.form_submit_button("💾 Apply & Save Landing View Settings Permanently", type="primary", use_container_width=True)
                    
                    if submit_settings:
                        updated_config = {
                            "show_header_text": header_toggle,
                            "header_mantra": mantra_text,
                            "system_title": system_title_text,
                            "header_mantra_font_size": mantra_font_size,
                            "header_title_font_size": title_font_size,
                            "notice_board_border_color": border_color,
                            "notice_board_bg_color": bg_color
                        }
                        st.session_state.pre_login_config = updated_config
                        save_pre_login_config(updated_config)
                        st.success("🎉 डैशबोर्ड विजुअल सेटिंग्स सफलतापूर्वक सेव हो गई हैं!")
                        st.rerun()

            st.markdown("---")

            # --- (P12 se yahan shift kiya gaya) Logo Upload, Size & Fit Mode Customizer ---
            hdr_c1_p15_show_logo_upload, hdr_c2_p15_show_logo_upload = st.columns([6, 1])
            with hdr_c1_p15_show_logo_upload:
                st.subheader("🖼️ लोगो अपलोड, साइज़ और फिट मोड कंट्रोल")
            with hdr_c2_p15_show_logo_upload:
                if st.button("🙈 Hide" if st.session_state.get("p15_show_logo_upload", True) else "👁️ Unhide", key="p15_show_logo_upload_toggle_btn", use_container_width=True):
                    st.session_state["p15_show_logo_upload"] = not st.session_state.get("p15_show_logo_upload", True)
                    st.rerun()

            if st.session_state.get("p15_show_logo_upload", True):
                st.caption("यहाँ से नया लोगो अपलोड करें, उसकी Width/Height अलग-अलग सेट करें और Fit Mode चुनें — Live Preview में सेव करने से पहले ही देख सकते हैं कि लोगो कैसा दिखेगा।")

                current_logo_path = st.session_state.pre_login_config.get("logo_path", "logo pratap.png")
                current_logo_w = int(st.session_state.pre_login_config.get("logo_width", 110))
                current_logo_h = int(st.session_state.pre_login_config.get("logo_height", 110))
                current_logo_fit = st.session_state.pre_login_config.get("logo_fit_mode", "contain")

                new_logo_file = st.file_uploader(
                    "नया लोगो अपलोड करें (PNG/JPG) — खाली छोड़ने पर मौजूदा लोगो बना रहेगा:",
                    type=["png", "jpg", "jpeg"],
                    key="p15_logo_uploader_v1"
                )

                col_logo1, col_logo2, col_logo3 = st.columns(3)
                with col_logo1:
                    logo_width_input = st.slider("↔️ Logo Width (px)", min_value=30, max_value=400, value=current_logo_w, key="p15_logo_width_slider_v1")
                with col_logo2:
                    logo_height_input = st.slider("↕️ Logo Height (px)", min_value=30, max_value=400, value=current_logo_h, key="p15_logo_height_slider_v1")
                with col_logo3:
                    fit_options = ["contain", "cover"]
                    fit_index = fit_options.index(current_logo_fit) if current_logo_fit in fit_options else 0
                    logo_fit_input = st.selectbox(
                        "🖼️ Fit Mode",
                        options=fit_options,
                        index=fit_index,
                        format_func=lambda x: "contain (पूरी image दिखेगी, कटेगी नहीं)" if x == "contain" else "cover (box भरेगा, extra हिस्सा crop हो सकता है)",
                        key="p15_logo_fit_selector_v1"
                    )

                preview_img_base64 = ""
                if new_logo_file is not None:
                    preview_bytes = new_logo_file.getvalue()
                    preview_img_base64 = f"data:image/png;base64,{base64.b64encode(preview_bytes).decode()}"
                else:
                    preview_img_base64 = get_image_base64(current_logo_path)

                st.markdown("##### 👁️ Live Preview")
                if preview_img_base64:
                    st.markdown(
                        f"""
                        <div style="width:{logo_width_input}px; height:{logo_height_input}px; display:flex; align-items:center; justify-content:center;
                                    overflow:hidden; border-radius:8px; box-shadow:0 4px 10px rgba(0,0,0,0.15); border:1px solid #e2e8f0; background:#fff;">
                            <img src="{preview_img_base64}" style="width:100%; height:100%; object-fit:{logo_fit_input}; display:block;">
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    st.info("ℹ️ अभी कोई लोगो उपलब्ध नहीं है — प्रीव्यू देखने के लिए एक लोगो अपलोड करें।")

                if st.button("📏 साइज़ & फिट सेव करें", type="primary", use_container_width=True, key="p15_logo_save_btn_v1"):
                    saved_path = current_logo_path
                    if new_logo_file is not None:
                        ext = os.path.splitext(new_logo_file.name)[1] or ".png"
                        saved_path = f"custom_logo{ext}"
                        with open(saved_path, "wb") as f_logo:
                            f_logo.write(new_logo_file.getvalue())

                    updated_logo_config = dict(st.session_state.pre_login_config)
                    updated_logo_config["logo_path"] = saved_path
                    updated_logo_config["logo_width"] = logo_width_input
                    updated_logo_config["logo_height"] = logo_height_input
                    updated_logo_config["logo_fit_mode"] = logo_fit_input

                    st.session_state.pre_login_config = updated_logo_config
                    save_pre_login_config(updated_logo_config)
                    st.success("🎉 लोगो साइज़, फिट मोड और (यदि अपलोड की गई हो तो) नई इमेज सफलतापूर्वक सेव हो गई!")
                    st.rerun()

            st.markdown("---")
            hdr_c1_p15_show_panel_names, hdr_c2_p15_show_panel_names = st.columns([6, 1])
            with hdr_c1_p15_show_panel_names:
                st.subheader("✏️ Dynamic 15 Panels Name & Label Customizer")
            with hdr_c2_p15_show_panel_names:
                if st.button("🙈 Hide" if st.session_state.get("p15_show_panel_names", True) else "👁️ Unhide", key="p15_show_panel_names_toggle_btn", use_container_width=True):
                    st.session_state["p15_show_panel_names"] = not st.session_state.get("p15_show_panel_names", True)
                    st.rerun()

            if st.session_state.get("p15_show_panel_names", True):
                with st.expander("15 पैनल्स के नाम (App Titles) एडिट करने के लिए यहाँ क्लिक करें", expanded=False):
                    with st.form(key="p15_panel_rename_matrix_form_final_secure"):
                        p_setup1, p_setup2 = st.columns(2)
                        temp_panel_mappings = {}
                        for idx, p_key in enumerate(DEFAULT_PANELS.keys()):
                            current_panel_name = st.session_state.panel_names.get(p_key, DEFAULT_PANELS[p_key])
                            if idx % 2 == 0:
                                with p_setup1: 
                                    temp_panel_mappings[p_key] = st.text_input(f"Name for {p_key}:", value=current_panel_name, key=f"p15_ren_final_{p_key}")
                            else:
                                with p_setup2: 
                                    temp_panel_mappings[p_key] = st.text_input(f"Name for {p_key}:", value=current_panel_name, key=f"p15_ren_final_{p_key}")
                        
                        if st.form_submit_button("Save All 15 Panel Titles Permanently", type="primary", use_container_width=True):
                            st.session_state.panel_names = temp_panel_mappings
                            save_panel_names(temp_panel_mappings)
                            st.success("✅ सभी 15 पैनल्स के नाम अपडेट हो गए हैं!")
                            st.rerun()

            st.markdown("---")
            hdr_c1_p15_show_panel_visibility, hdr_c2_p15_show_panel_visibility = st.columns([6, 1])
            with hdr_c1_p15_show_panel_visibility:
                st.subheader("🛡️ Global 15 Panels Visibility Toggle Switch Board")
            with hdr_c2_p15_show_panel_visibility:
                if st.button("🙈 Hide" if st.session_state.get("p15_show_panel_visibility", True) else "👁️ Unhide", key="p15_show_panel_visibility_toggle_btn", use_container_width=True):
                    st.session_state["p15_show_panel_visibility"] = not st.session_state.get("p15_show_panel_visibility", True)
                    st.rerun()

            if st.session_state.get("p15_show_panel_visibility", True):
                vis_tabs = st.tabs(["🔒 Panels P1 - P7 Control", "🔒 Panels P8 - P15 Control"])
                
                # Visibility Panel Controllers Layer for P1 - P7
                with vis_tabs[0]:
                    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
                    panels_p1_p7 = ["P1", "P2", "P3", "P4", "P5", "P6", "P7"]
                    cols_p1_p7 = [c1, c2, c3, c4, c5, c6, c7]
                    for i, p_key in enumerate(panels_p1_p7):
                        with cols_p1_p7[i]:
                            status_lbl = "🙈 Hidden" if st.session_state.get(f"hide_panel_{p_key}", False) else "👀 Active"
                            if st.button(f"{p_key}\n({status_lbl})", use_container_width=True, key=f"p15_btn_v_final_{p_key}"):
                                st.session_state[f"hide_panel_{p_key}"] = not st.session_state.get(f"hide_panel_{p_key}", False)
                                st.rerun()

                # Visibility Panel Controllers Layer for P8 - P15
                with vis_tabs[1]:
                    c8, c9, c10, c11, c12, c13, c14, c15 = st.columns(8)
                    panels_p8_p15 = ["P8", "P9", "P10", "P11", "P12", "P13", "P14", "P15"]
                    cols_p8_p15 = [c8, c9, c10, c11, c12, c13, c14, c15]
                    for i, p_key in enumerate(panels_p8_p15):
                        with cols_p8_p15[i]:
                            status_lbl = "🙈 Hidden" if st.session_state.get(f"hide_panel_{p_key}", False) else "👀 Active"
                            if st.button(f"{p_key}\n({status_lbl})", use_container_width=True, key=f"p15_btn_v_final_{p_key}"):
                                st.session_state[f"hide_panel_{p_key}"] = not st.session_state.get(f"hide_panel_{p_key}", False)
                                st.rerun()

            # ⚙️ सुपर-एडमिन मास्टर ड्रॉपडाउन लिस्ट कस्टमाइज़र
            st.markdown("---")
            hdr_c1_p15_show_dropdown_customizer, hdr_c2_p15_show_dropdown_customizer = st.columns([6, 1])
            with hdr_c1_p15_show_dropdown_customizer:
                st.subheader("⚙️ Super-Admin Master Dropdown List Customizer")
            with hdr_c2_p15_show_dropdown_customizer:
                if st.button("🙈 Hide" if st.session_state.get("p15_show_dropdown_customizer", True) else "👁️ Unhide", key="p15_show_dropdown_customizer_toggle_btn", use_container_width=True):
                    st.session_state["p15_show_dropdown_customizer"] = not st.session_state.get("p15_show_dropdown_customizer", True)
                    st.rerun()

            if st.session_state.get("p15_show_dropdown_customizer", True):
                st.markdown("पैनल 1 (Data Onboarding) में दिखने वाली तीनों स्क्रॉल सूचियों के विकल्पों को यहाँ से लाइव कस्टमाइज़ करें:")
                
                col_drop1, col_drop2, col_drop3 = st.columns(3)
                with col_drop1:
                    st.markdown("##### 📁 1. File Segments / Types")
                    edited_file_types = st.text_area("File Types (एक प्रति लाइन):", value="\n".join(st.session_state.p1_dropdown_schemas["file_types"]), height=140, key="p15_custom_file_types_text")
                with col_drop2:
                    st.markdown("##### 📆 2. Academic Years")
                    edited_years = st.text_area("Admission Years (एक प्रति लाइन):", value="\n".join(st.session_state.p1_dropdown_schemas["academic_years"]), height=140, key="p15_custom_years_text")
                with col_drop3:
                    st.markdown("##### ⏳ 3. Academic Sessions")
                    edited_sessions = st.text_area("Admission Sessions (एक प्रति line):", value="\n".join(st.session_state.p1_dropdown_schemas["academic_sessions"]), height=140, key="p15_custom_sessions_text")
                
                if st.button("💾 Apply & Update Master Dropdown Framework", type="primary", use_container_width=True, key="p15_save_dropdowns_btn"):
                    st.session_state.p1_dropdown_schemas["file_types"] = [line.strip() for line in edited_file_types.split("\n") if line.strip()]
                    st.session_state.p1_dropdown_schemas["academic_years"] = [line.strip() for line in edited_years.split("\n") if line.strip()]
                    st.session_state.p1_dropdown_schemas["academic_sessions"] = [line.strip() for line in edited_sessions.split("\n") if line.strip()]
                    st.success("🎉 ड्रॉपडाउन सूचियाँ सफलतापूर्वक अपडेट हो गईं!")
                    st.rerun()

            # ======================================================================
            # 🔐 न्यू मॉड्यूल: सुरक्षित मास्टर CSV/XLSX फ़ाइल ओवरराइट अपलोडर (Fixed Auto Lock)
            # ======================================================================
            st.markdown("---")
            hdr_c1_p15_show_master_overwrite, hdr_c2_p15_show_master_overwrite = st.columns([6, 1])
            with hdr_c1_p15_show_master_overwrite:
                st.subheader("⚠️ Advanced Action: Dangerous Master File Overwrite Uploader (CSV / XLSX)")
            with hdr_c2_p15_show_master_overwrite:
                if st.button("🙈 Hide" if st.session_state.get("p15_show_master_overwrite", True) else "👁️ Unhide", key="p15_show_master_overwrite_toggle_btn", use_container_width=True):
                    st.session_state["p15_show_master_overwrite"] = not st.session_state.get("p15_show_master_overwrite", True)
                    st.rerun()

            if st.session_state.get("p15_show_master_overwrite", True):
                st.warning("यह एक अत्यंत संवेदनशील विकल्प है। यहाँ नई फ़ाइल अपलोड करने पर वर्तमान का पूरा लाइव डेटाबेस (`shared_student_database.csv`) स्थायी रूप से मिट जाएगा और नई फ़ाइल का डेटा नया मास्टर बन जाएगा।")
                
                # ऑटो-रीसेट ट्रिगर काउंटर स्टेट जो विजेट को रीबूट करेगा
                if "p15_uploader_reset_counter" not in st.session_state:
                    st.session_state.p15_uploader_reset_counter = 0

                with st.expander("🔑 सुरक्षित मास्टर फ़ाइल अपलोड गेटवे खोलें", expanded=False):
                    col_up_pass, col_up_file = st.columns(2)
                    
                    with col_up_pass:
                        # काउंटर को की (Key) के साथ जोड़कर डायनेमिक बनाया गया है ताकि एरर न आए
                        uploader_secure_password = st.text_input(
                            "🛡️ फ़ाइल अपलोडर स्पेशल पासवर्ड दर्ज करें:", 
                            type="password", 
                            key=f"p15_master_pass_widget_run_{st.session_state.p15_uploader_reset_counter}"
                        )
                    
                    with col_up_file:
                        is_password_correct = (uploader_secure_password == "admin@upload15")
                        
                        uploaded_master_file = st.file_uploader(
                            "सिस्टम में ओवरराइट करने के लिए मास्टर फ़ाइल चुनें (CSV / XLSX / XLS):", 
                            type=["csv", "xlsx", "xls"],
                            key=f"p15_master_file_widget_run_{st.session_state.p15_uploader_reset_counter}",
                            disabled=not is_password_correct
                        )
                    
                    if uploader_secure_password and not is_password_correct:
                        st.error("❌ गलत फ़ाइल अपलोडर पासवर्ड! अपलोड ब्लॉक लॉक है।")
                    elif is_password_correct:
                        st.success("🔓 पासवर्ड सत्यापित! आप फ़ाइल अपलोड कर सकते हैं।")
                        
                        if uploaded_master_file is not None:
                            st.info(f"📁ं चयनित फ़ाइल: `{uploaded_master_file.name}` प्रोसेस होने के लिए तैयार है।")
                            
                            confirm_overwrite_checkbox = st.checkbox(
                                "मैं प्रमाणित करता हूँ कि मैं पुराना मास्टर डेटा डिलीट करके इस नई फ़ाइल को लाइव डेटाबेस बनाना चाहता हूँ।",
                                key=f"p15_master_chk_run_{st.session_state.p15_uploader_reset_counter}"
                            )
                            
                            if st.button("💥 FORCE OVERWRITE COMPLETE MASTER DATABASE NOW", type="primary", use_container_width=True, disabled=not confirm_overwrite_checkbox):
                                try:
                                    raw_uploaded_df = read_uploaded_file_as_csv_df(uploaded_master_file)
                                    
                                    if raw_uploaded_df.empty:
                                        st.error("❌ अपलोडेड फ़ाइल के अंदर कोई मान्य डेटा नहीं मिला।")
                                        if _UPLOAD_DIAG["info"]:
                                            st.caption(f"🔎 Diagnostic: {_UPLOAD_DIAG['info']}")
                                    else:
                                        raw_uploaded_df = raw_uploaded_df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
                                        
                                        for col in DEFAULT_COLUMNS:
                                            if col not in raw_uploaded_df.columns:
                                                raw_uploaded_df[col] = ""
                                        
                                        if "Target Panel Visibility" not in raw_uploaded_df.columns or raw_uploaded_df["Target Panel Visibility"].eq("").all():
                                            raw_uploaded_df["Target Panel Visibility"] = "P2"
                                        
                                        finalized_uploaded_master = raw_uploaded_df[DEFAULT_COLUMNS].copy()
                                        save_live_data(finalized_uploaded_master)
                                        
                                        # 🔒 सुरक्षित रीसेट मैकेनिज्म: काउंटर बदलते ही विजेट फ्रेश रीबूट हो जाएगा और पुराना डेटा मिट जाएगा
                                        st.session_state.p15_uploader_reset_counter += 1
                                        
                                        st.success(f"🎉 शत-प्रतिशत सफलता! `{uploaded_master_file.name}` को नया लाइव मास्टर डेटाबेस बना दिया गया है। गेटवे को सुरक्षित लॉक कर दिया गया है।")
                                        st.balloons()
                                        st.rerun()
                                        
                                except Exception as upload_err:
                                    st.error(f"मास्टर फ़ाइल डेटा प्रोसेसिंग चक्र में तकनीकी खराबी आई: {upload_err}")

            # ----------------------------------------------------------------------
            # यहाँ से आपका पुराना कोड वापस शुरू हो जाएगा:
            # ----------------------------------------------------------------------
            st.markdown("---")
            hdr_c1_p15_show_master_db_view, hdr_c2_p15_show_master_db_view = st.columns([6, 1])
            with hdr_c1_p15_show_master_db_view:
                st.subheader("📊 Master Database List View & Advanced Operational Controls")
            with hdr_c2_p15_show_master_db_view:
                if st.button("🙈 Hide" if st.session_state.get("p15_show_master_db_view", True) else "👁️ Unhide", key="p15_show_master_db_view_toggle_btn", use_container_width=True):
                    st.session_state["p15_show_master_db_view"] = not st.session_state.get("p15_show_master_db_view", True)
                    st.rerun()

            if st.session_state.get("p15_show_master_db_view", True):
                
                # Action Toggles Column Layout
                col_ctrl1, col_ctrl2, col_ctrl3 = st.columns(3)
                with col_ctrl3:
                    lock_label = "🔒 लिस्ट लॉक करें (Locked)" if st.session_state.admin_lock_state else "🔓 लिस्ट अनलॉक करें (Editable)"
                    if st.button(lock_label, use_container_width=True, type="primary" if not st.session_state.admin_lock_state else "secondary", key="p15_lock_toggle_master_btn_final"):
                        st.session_state.admin_lock_state = not st.session_state.admin_lock_state
                        st.rerun()

                with col_ctrl1:
                    lbl_edit = "👀 एडमिट टेक्स्ट FUNCTION: active" if st.session_state.admin_unhide_edit else "🙈 एडमिट टेक्स्ट FUNCTION: hidden"
                    if st.button(lbl_edit, use_container_width=True, disabled=st.session_state.admin_lock_state, key="p15_edit_toggle_master_btn_final"):
                        st.session_state.admin_unhide_edit = not st.session_state.admin_unhide_edit
                        st.rerun()

                with col_ctrl2:
                    lbl_move = "👀 कॉलम मूव बटन्स: active" if st.session_state.admin_unhide_move else "🙈 कॉलम मूव बटन्स: hidden"
                    if st.button(lbl_move, use_container_width=True, key="p15_move_toggle_master_btn_final"):
                        st.session_state.admin_unhide_move = not st.session_state.admin_unhide_move
                        st.rerun()

                # ======================================================================
                # 🔀 कॉलम शिफ्टर ब्लॉक (लिस्ट लॉक होने पर यह आटोमेटिक फ्रीज हो जाएगा)
                # ======================================================================
                if st.session_state.admin_unhide_move:
                    st.info("🔀 कॉलम का क्रम बदलने के लिए सेलेक्ट करें (Select Column to Shift):")
                    
                    # 🚨 यदि लिस्ट लॉक है, तो ड्रॉपडाउन को भी डिसेबल (फ्रीज) कर दें
                    target_col = st.selectbox(
                        "मूव करने के लिए कॉलम चुनें:", 
                        options=[c for c in st.session_state.admin_columns_order if c not in P15_HIDDEN_GRID_COLUMNS], 
                        disabled=st.session_state.admin_lock_state,
                        key="p15_column_shifter_select_box_final"
                    )
                    c_left, c_right = st.columns(2)
                    
                    # 🔒 सुरक्षा गेटवे: यदि लिस्ट लॉक है (admin_lock_state = True), तो बटन लॉक रहेंगे
                    if c_left.button("⬅️ Shift Left", use_container_width=True, disabled=st.session_state.admin_lock_state, key="p15_shift_left_master_btn_final"):
                        idx = st.session_state.admin_columns_order.index(target_col)
                        if idx > 0:
                            st.session_state.admin_columns_order[idx], st.session_state.admin_columns_order[idx-1] = st.session_state.admin_columns_order[idx-1], st.session_state.admin_columns_order[idx]
                            st.rerun()
                            
                    if c_right.button("➡️ Shift Right", use_container_width=True, disabled=st.session_state.admin_lock_state, key="p15_shift_right_master_btn_final"):
                        idx = st.session_state.admin_columns_order.index(target_col)
                        if idx < len(st.session_state.admin_columns_order) - 1:
                            st.session_state.admin_columns_order[idx], st.session_state.admin_columns_order[idx+1] = st.session_state.admin_columns_order[idx+1], st.session_state.admin_columns_order[idx]
                            st.rerun()

                # फ़ील्ड्स और ऑर्डर्स मैपिंग
                # 🙈 Permanent Fix: "Application Number" aur "Payment Date" ab P15 ki master grid me nahi dikhenge
                # (In dono ka data aur P11 wala Twin-Sync engine bilkul pehle jaisa hi normal kaam karta rahega)
                render_columns = [col for col in st.session_state.admin_columns_order if col in live_db.columns and col not in P15_HIDDEN_GRID_COLUMNS]

                # 🕓 "पेंडिंग डिलीट" स्टेज: जब तक "Save Grid Changes" बटन नहीं दबाया जाता, तब तक Delete
                #    सिर्फ़ रो को व्यू से छुपाता है — असली CSV फ़ाइल में कुछ भी परमानेंट डिलीट नहीं होता।
                if "p15_pending_delete_ids" not in st.session_state:
                    st.session_state.p15_pending_delete_ids = set()

                live_db_for_display = live_db.drop(
                    index=[i for i in st.session_state.p15_pending_delete_ids if i in live_db.index],
                    errors="ignore"
                )

                ordered_db = live_db_for_display[render_columns].copy()
                ordered_db_display = ordered_db.rename(columns={c: get_display_name(c) for c in ordered_db.columns})
                # 🛡️ पूरा (बिना सर्च-फ़िल्टर वाला) view — "Save Grid Changes" इसी से सेव होगा, ताकि सर्च चालू होने पर बाकी रिकॉर्ड CSV से गलती से न हट जाएँ
                ordered_db_display_all = ordered_db_display.copy()

                # ======================================================================
                # 🔍 हर कॉलम के नाम के ठीक नीचे, टेबल शुरू होने से ठीक पहले सर्च बॉक्स
                #    टाइप करते ही टेबल लाइव फ़िल्टर होगी (केस-इनसेंसिटिव, "Contains" मैच)।
                #    कई कॉलम में एक साथ टेक्स्ट भरें तो सभी शर्तें एक साथ (AND) लागू होंगी।
                # ======================================================================
                if not live_db.empty and not st.session_state.admin_lock_state:
                    search_display_columns = list(ordered_db_display.columns)
                    cols_per_row = 4
                    col_search_values = {}
                    for row_start in range(0, len(search_display_columns), cols_per_row):
                        row_cols_chunk = search_display_columns[row_start:row_start + cols_per_row]
                        search_row_widgets = st.columns(len(row_cols_chunk))
                        for widget_slot, disp_col_name in zip(search_row_widgets, row_cols_chunk):
                            with widget_slot:
                                col_search_values[disp_col_name] = st.text_input(
                                    disp_col_name,
                                    key=f"p15_colsearch_{disp_col_name}",
                                    placeholder="🔎 खोजें..."
                                )

                    # फ़िल्टर लागू करें: सिर्फ़ वही रो दिखेंगी जो हर भरे हुए सर्च बॉक्स की शर्त पूरी करें
                    active_filter_mask = pd.Series(True, index=ordered_db_display.index)
                    for disp_col_name, search_text in col_search_values.items():
                        search_text = (search_text or "").strip()
                        if search_text:
                            active_filter_mask &= ordered_db_display[disp_col_name].astype(str).str.contains(
                                search_text, case=False, na=False, regex=False
                            )

                    if not active_filter_mask.all():
                        cap_col, clear_col = st.columns([4, 1])
                        with cap_col:
                            st.caption(f"🔎 सर्च फ़िल्टर सक्रिय है — कुल `{active_filter_mask.sum()}` रिकॉर्ड मैच हुए (पूरे `{len(active_filter_mask)}` रिकॉर्ड्स में से)।")
                        with clear_col:
                            if st.button("🧹 सर्च साफ़ करें", key="p15_clear_col_search_btn", use_container_width=True):
                                for disp_col_name in search_display_columns:
                                    st.session_state[f"p15_colsearch_{disp_col_name}"] = ""
                                st.rerun()

                    ordered_db_display = ordered_db_display[active_filter_mask]
                    live_db_for_display = live_db_for_display.loc[ordered_db_display.index]

                ordered_db_display.insert(0, "S.No.", range(1, len(ordered_db_display) + 1))

                st.markdown(f"**📈 मुख्य लाइव डेटाबेस रिकॉर्ड्स की कुल संख्या:** `{len(ordered_db_display)}`")

                # ==================================================================
                # 📥 P15 Master Database — Excel (.xlsx) Download System
                # जो भी रिकॉर्ड्स अभी ग्रिड में दिख रहे हैं (सर्च फ़िल्टर लगा हो तो सिर्फ़ वही),
                # उन्हीं को उसी कॉलम-ऑर्डर में फॉर्मेटेड .xlsx फ़ाइल में डाउनलोड कर देता है।
                # ==================================================================
                if not ordered_db_display.empty:
                    try:
                        p15_excel_bytes = dataframe_to_excel_bytes(ordered_db_display, "Master Database")
                        p15_inner_filename = f"master_database_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx"
                        # 🔒 Password-protected .zip (asli, tested AES encryption) — andar wahi .xlsx file hai
                        p15_zip_bytes = make_password_protected_zip(p15_excel_bytes, p15_inner_filename, "15081999")
                        st.download_button(
                            label=f"📥 Download Excel File (.zip, password-protected) — कुल {len(ordered_db_display)} रिकॉर्ड्स 🔒",
                            data=p15_zip_bytes,
                            file_name=f"master_database_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.zip",
                            mime="application/zip",
                            use_container_width=True,
                            key="p15_master_db_download_excel_btn"
                        )
                        st.caption("🔒 यह ZIP पासवर्ड-प्रोटेक्टेड है — extract करते समय सही पासवर्ड डालना ज़रूरी होगा, तभी अंदर की Excel फ़ाइल खुलेगी।")
                    except Exception as p15_xl_err:
                        st.error(f"Excel फ़ाइल बनाने में समस्या आई: {p15_xl_err} (requirements.txt में `openpyxl` और `pyzipper` जोड़ें)")

                if live_db.empty:
                    st.warning("💡 वर्तमान में मास्टर डेटाबेस पूरी तरह खाली है। कृपया पहले Panel 1 से नया डेटा लोड करें।")
                else:
                    if st.session_state.admin_lock_state:
                        # लॉक मोड: केवल डेटा व्यू करने के लिए (Read-Only) — हेडर और पहली रो के बीच सर्च बॉक्स के साथ
                        st.caption("🔒 लिस्ट अभी **Locked** है — रो Delete/Edit करने के लिए ऊपर **🔓 लिस्ट अनलॉक करें (Editable)** बटन दबाएं।")
                        render_inline_filter_table(ordered_db_display.drop(columns=["S.No."], errors="ignore"), height=520)
                    else:
                        # अनलॉक मोड: ग्रिड एडिटिंग और रो डिलीट करने के लिए एक्टिवेट
                        if st.session_state.admin_unhide_edit:
                            st.warning("✏️ **अभी EDIT टेबल दिख रही है (👀 एडमिट टेक्स्ट FUNCTION: active)** — इसमें सिर्फ़ सेल बदले जा सकते हैं, **Row Delete का option यहाँ नहीं आता।** रो डिलीट करने के लिए ऊपर का **'👀 एडमिट टेक्स्ट FUNCTION'** बटन दबाकर उसे **🙈 hidden** कर दें — तब Delete टेबल (चेकबॉक्स + 🗑️ Delete Selected Rows बटन) दिखेगी।")
                        else:
                            st.info("🔓 **डिलीट मोड सक्रिय:** नीचे टेबल में रो सेलेक्ट करें (बाईं ओर चेकबॉक्स), फिर 🗑️ **Delete Selected Rows** बटन दबाएं। सेल एडिट करना हो तो ऊपर '👀 एडमिट टेक्स्ट FUNCTION' को active करें।")
                        
                        disabled_fields = ["S.No."]
                        # यदि 'एडमिट टेक्स्ट FUNCTION' चालू नहीं (hidden) है, तो संवेदनशील कॉलम्स लॉक रहेंगे
                        if not st.session_state.admin_unhide_edit:
                            disabled_fields.extend([get_display_name("Application Number"), get_display_name("Student Name"), get_display_name("Father Name")])

                        disabled_fields = ["S.No."]
                        # यदि 'एडमिट टेक्स्ट FUNCTION' चालू नहीं (hidden) है, तो संवेदनशील कॉलम्स लॉक रहेंगे
                        if not st.session_state.admin_unhide_edit:
                            disabled_fields.extend([get_display_name("Application Number"), get_display_name("Student Name"), get_display_name("Father Name")])
                        
                        # 🛡️ 🆕 यहाँ यह नया स्कीमा एडिटर (कॉलम और रो जोड़ने/हटाने का फ़ंक्शन) पेस्ट हो रहा है:
                        if role == "full_admin" and not st.session_state.admin_lock_state:
                            st.markdown("---")
                            st.markdown("#### 🛠️ Super-Admin Schema Editor (Add/Delete Columns & Rows)")
                            tab_col_ctrl, tab_row_ctrl = st.tabs(["📊 Dynamic Column Panel Engine", "➕ Manual Row Injector"])
                            
                            with tab_col_ctrl:
                                col_add_side, col_del_side = st.columns(2)
                                with col_add_side:
                                    st.markdown("##### ➕ नया कॉलम जोड़ें (Add Column)")
                                    new_col_input = st.text_input("नया कॉलम का सटीक नाम दर्ज करें:", key="p15_new_col_input_name").strip()
                                    if st.button("🚀 Create Column Globally", type="primary", use_container_width=True):
                                        if new_col_input and new_col_input not in live_db.columns:
                                            live_db[new_col_input] = ""
                                            if new_col_input not in DEFAULT_COLUMNS: DEFAULT_COLUMNS.append(new_col_input)
                                            if new_col_input not in st.session_state.admin_columns_order: st.session_state.admin_columns_order.append(new_col_input)
                                            save_live_data(live_db)
                                            st.success(f"🎉 कॉलम `{new_col_input}` संरचना में जुड़ गया है।")
                                            st.rerun()
                                            
                                with col_del_side:
                                    st.markdown("##### 🗑️ कॉलम हटाएं (Delete Column)")
                                    col_to_delete = st.selectbox("हटाने के लिए कॉलम चुनें:", options=[c for c in live_db.columns if c != "Target Panel Visibility"], key="p15_col_to_delete_select")
                                    confirm_col_del = st.checkbox("हाँ, मैं इस कॉलम का पूरा डेटा नष्ट करना चाहता हूँ।", key="p15_confirm_col_del_chk")
                                    if st.button("🗑️ ERASE COLUMN PERMANENT PERMANENTLY", type="primary", use_container_width=True, disabled=not confirm_col_del):
                                        if col_to_delete in live_db.columns: live_db = live_db.drop(columns=[col_to_delete])
                                        if col_to_delete in DEFAULT_COLUMNS: DEFAULT_COLUMNS.remove(col_to_delete)
                                        if col_to_delete in st.session_state.admin_columns_order: st.session_state.admin_columns_order.remove(col_to_delete)
                                        save_live_data(live_db)
                                        st.error(f"💥 कॉलम `{col_to_delete}` हटा दिया गया है!")
                                        st.rerun()

                            with tab_row_ctrl:
                                st.markdown("##### ➕ डेटाबेस में सिंगल रो इंजेक्ट करें (Add Row)")
                                if st.button("➕ Inject Blank Data Row at the End", use_container_width=True):
                                    blank_row = {c: "" for c in live_db.columns}
                                    blank_row["Target Panel Visibility"] = "P2"
                                    live_db = pd.concat([live_db, pd.DataFrame([blank_row])], ignore_index=True)
                                    save_live_data(live_db)
                                    st.success("🎉 एक खाली रो डेटाबेस के अंत में जोड़ दी गई है!")
                                    st.rerun()

                        st.markdown("---")
                        
                        # 🎯 आपकी शर्त: लॉक होने पर माउस कर्सर से कॉलम हिलना बंद होगा, अनलॉक पर चालू रहेगा
                        if st.session_state.admin_lock_state:
                            # 🔒 लॉक मोड: यह माउस कर्सर से कॉलम को खींचना (Move करना) पूरी तरह बंद कर देगा
                            st.dataframe(
                                ordered_db_display, 
                                use_container_width=True, 
                                hide_index=True
                            )
                            edited_master_db = ordered_db_display_all
                        else:
                            # 🔓 अनलॉक मोड: यहाँ आप माउस कर्सर से कॉलम को अपनी मर्जी से आगे-पीछे हिला सकते हैं
                            #
                            # 🔴 रो डिलीट करने के लिए Streamlit की असली "native" row-selection
                            #    (लाल हाइलाइट वाली, खाली चेकबॉक्स) इस्तेमाल की गई है — जिस रो पर
                            #    क्लिक करेंगे वह लाल हो जाएगी/चेकबॉक्स टिक हो जाएगा, और यह चयन Python कोड को भी
                            #    मिलता है (st.dataframe के on_select फीचर से)। इसी में हेडर पर एक
                            #    बिल्ट-इन "सभी चुनें" चेकबॉक्स भी अपने-आप आता है — अलग से कुछ नहीं जोड़ा गया।
                            #
                            # 🆔 हर रो की असली पहचान (live_db का असली index) एक छिपे हुए कॉलम "_row_id" में
                            #    रखते हैं, ताकि सही रो ही डिलीट हो — गलत रो डिलीट होने वाली दिक्कत दोबारा न आए।
                            select_source_df = ordered_db_display.copy()
                            select_source_df.insert(0, "_row_id", live_db_for_display.index)
                            edit_disabled_fields = list(dict.fromkeys(disabled_fields + ["_row_id"]))
                            visible_columns_order = [c for c in select_source_df.columns if c != "_row_id"]

                            if st.session_state.p15_pending_delete_ids:
                                pend_col1, pend_col2 = st.columns([3, 1])
                                with pend_col1:
                                    st.info(f"🕓 {len(st.session_state.p15_pending_delete_ids)} रो अभी सिर्फ़ छुपाई गई हैं (Hidden), CSV फ़ाइल में अभी तक permanent delete नहीं हुईं हैं। पक्का करने के लिए नीचे **💾 Save Grid Changes** बटन दबाएं।")
                                with pend_col2:
                                    if st.button("↩️ Undo Pending Deletes", use_container_width=True, key="p15_undo_pending_delete_btn"):
                                        st.session_state.p15_pending_delete_ids = set()
                                        st.rerun()

                            # 🔁 एक ही टॉगल (👀 एडमिट टेक्स्ट FUNCTION) से तय होता है कि अभी एडिट टेबल दिखे या डिलीट टेबल —
                            #    दोनों एक साथ कभी नहीं दिखतीं। "👀 एडमिट टेक्स्ट FUNCTION: active" हो तो एडिट टेबल, वरना डिलीट टेबल।
                            if st.session_state.admin_unhide_edit:
                                st.caption("✏️ किसी भी सेल पर क्लिक करके सीधे वैल्यू बदलें।")

                                edited_select_df = st.data_editor(
                                    select_source_df,
                                    use_container_width=True,
                                    hide_index=True,
                                    column_order=visible_columns_order,
                                    disabled=edit_disabled_fields,
                                    key=f"p15_master_editor_{st.session_state.get('p15_delete_selector_version', 0)}"
                                )
                                edited_master_db = edited_select_df.drop(columns=["_row_id"], errors="ignore")
                            else:
                                # 🔴 रो डिलीट करने के लिए Streamlit की असली "native" row-selection
                                #    (लाल हाइलाइट वाली, खाली चेकबॉक्स) इस्तेमाल की गई है — जिस रो पर
                                #    क्लिक करेंगे वह लाल हो जाएगी/चेकबॉक्स टिक हो जाएगा, और यह चयन Python कोड को भी
                                #    मिलता है (st.dataframe के on_select फीचर से)।
                                st.caption("🔴 जिस रो को डिलीट करना है, उसे नीचे टेबल में क्लिक करके सिलेक्ट करें (रो लाल हो जाएगी), फिर Delete बटन दबाएं।")

                                if "p15_delete_selector_version" not in st.session_state:
                                    st.session_state.p15_delete_selector_version = 0
                                selector_key = f"p15_master_delete_selector_{st.session_state.p15_delete_selector_version}"

                                select_event = st.dataframe(
                                    select_source_df,
                                    use_container_width=True,
                                    hide_index=True,
                                    column_order=visible_columns_order,
                                    on_select="rerun",
                                    selection_mode="multi-row",
                                    key=selector_key
                                )

                                selected_positions = list(select_event.selection.rows) if select_event and select_event.selection else []
                                rows_marked_for_delete = select_source_df.iloc[selected_positions] if selected_positions else select_source_df.iloc[0:0]

                                del_col1, del_col2 = st.columns([3, 1])
                                with del_col1:
                                    if not rows_marked_for_delete.empty:
                                        st.warning(f"⚠️ कुल {len(rows_marked_for_delete)} रो सिलेक्ट हैं — Delete बटन दबाने पर ये टेबल से छुप जाएंगी (अभी CSV में permanent नहीं होंगी, उसके लिए Save Grid Changes दबाना होगा)।")
                                with del_col2:
                                    if st.button(
                                        "🗑️ Delete Selected Rows",
                                        type="primary",
                                        use_container_width=True,
                                        disabled=rows_marked_for_delete.empty,
                                        key="p15_delete_selected_rows_btn"
                                    ):
                                        row_ids_to_delete = [
                                            rid for rid in rows_marked_for_delete["_row_id"].tolist()
                                            if pd.notna(rid) and rid in live_db.index
                                        ]
                                        st.session_state.p15_pending_delete_ids.update(row_ids_to_delete)
                                        st.session_state.p15_delete_selector_version += 1
                                        st.warning(f"🕓 कुल {len(row_ids_to_delete)} रो अस्थायी रूप से छुपाई गई हैं — Save Grid Changes दबाने पर ही permanent डिलीट होंगी।")
                                        st.rerun()

                                edited_master_db = select_source_df.drop(columns=["_row_id"], errors="ignore")

                        if st.button("💾 Save Grid Changes to Master CSV File", type="primary", use_container_width=True, key="p15_save_master_csv_btn"):
                            try:
                                clean_edited_master = edited_master_db.drop(columns=["S.No."], errors="ignore")
                                display_to_orig_map = {get_display_name(c): c for c in live_db.columns}
                                clean_edited_master = clean_edited_master.rename(columns=display_to_orig_map)
                                save_live_data(clean_edited_master)
                                # ✅ यही वह पल है जब पेंडिंग डिलीट रो असल में CSV से permanent हटती हैं
                                #    (ऊपर की टेबल पहले से ही इन्हें छुपाकर दिखा रही थी, अब सेव भी हो गया)
                                st.session_state.p15_pending_delete_ids = set()
                                st.success("🎉 संपूर्ण मास्टर चेंजेस लाइव डेटाबेस फ़ाइल में सुरक्षित अपडेट हो गए हैं! (Pending delete रो भी अब permanent हट गई हैं)")
                                st.rerun()
                            except Exception as e:
                                st.error(f"डेटाबेस अपडेट चक्र में तकनीकी समस्या आई: {e}")

                        # ======================================================================
                        # 🔁 नया सब-सिस्टम: Database Find & Replace (पूरे डेटाबेस में ढूंढें और बदलें)
                        #    किसी भी एक कॉलम में मौजूद किसी वैल्यू को नई वैल्यू से बदलने के लिए
                        # ======================================================================
                        if role == "full_admin" and not st.session_state.admin_lock_state:
                            st.markdown("---")
                            st.markdown("#### 🔁 Database Find & Replace (डेटाबेस में ढूंढें और बदलें)")
                            st.caption("किसी एक कॉलम को चुनें, जो वैल्यू ढूंढनी है वो लिखें, और जिससे बदलनी है वो लिखें — यह पूरे मास्टर डेटाबेस में लागू होगा।")

                            fr_col1, fr_col2, fr_col3 = st.columns(3)
                            with fr_col1:
                                fr_target_col = st.selectbox(
                                    "🎯 किस कॉलम में बदलना है:",
                                    options=list(live_db.columns),
                                    key="p15_find_replace_col"
                                )
                            with fr_col2:
                                fr_find_val = st.text_input("🔍 ढूंढें (Find):", key="p15_find_replace_find_val")
                            with fr_col3:
                                fr_replace_val = st.text_input("✏️ इससे बदलें (Replace With):", key="p15_find_replace_new_val")

                            fr_opt1, fr_opt2 = st.columns(2)
                            with fr_opt1:
                                fr_match_mode = st.radio(
                                    "मिलान का तरीक़ा (Match Type):",
                                    options=["🎯 पूरी वैल्यू बिल्कुल मैच हो (Exact Match)", "🔎 वैल्यू के अंदर कहीं भी मौजूद हो (Contains / Partial)"],
                                    key="p15_find_replace_match_mode"
                                )
                            with fr_opt2:
                                fr_case_sensitive = st.checkbox("🔠 Case Sensitive (बड़े/छोटे अक्षर का फ़र्क़ माना जाए)", value=False, key="p15_find_replace_case_sensitive")

                            fr_exact_mode = fr_match_mode.startswith("🎯")

                            def _fr_series_for_compare(series):
                                s = series.astype(str)
                                return s if fr_case_sensitive else s.str.lower()

                            fr_find_compare = fr_find_val if fr_case_sensitive else fr_find_val.lower()

                            if fr_find_val.strip() != "" and fr_target_col in live_db.columns:
                                compare_series = _fr_series_for_compare(live_db[fr_target_col])
                                if fr_exact_mode:
                                    fr_match_mask = compare_series == fr_find_compare
                                else:
                                    fr_match_mask = compare_series.str.contains(re.escape(fr_find_compare), na=False)
                                fr_match_count = int(fr_match_mask.sum())
                            else:
                                fr_match_mask = None
                                fr_match_count = 0

                            if fr_find_val.strip() != "":
                                st.info(f"🔍 **{fr_match_count}** रिकॉर्ड्स में `{fr_target_col}` कॉलम का मिलान मिला।")

                            fr_confirm = st.checkbox(
                                f"हाँ, मैं `{fr_target_col}` कॉलम में `{fr_find_val}` को `{fr_replace_val}` से बदलना चाहता हूँ।",
                                key="p15_find_replace_confirm_chk",
                                disabled=(fr_match_count == 0)
                            )

                            if st.button(
                                "🔁 Apply Find & Replace to Database",
                                type="primary",
                                use_container_width=True,
                                disabled=(fr_match_count == 0 or not fr_confirm),
                                key="p15_find_replace_apply_btn"
                            ):
                                try:
                                    if fr_exact_mode:
                                        live_db.loc[fr_match_mask, fr_target_col] = fr_replace_val
                                    else:
                                        col_as_str = live_db[fr_target_col].astype(str)
                                        if fr_case_sensitive:
                                            live_db.loc[fr_match_mask, fr_target_col] = col_as_str[fr_match_mask].str.replace(fr_find_val, fr_replace_val, regex=False)
                                        else:
                                            live_db.loc[fr_match_mask, fr_target_col] = col_as_str[fr_match_mask].str.replace(fr_find_val, fr_replace_val, case=False, regex=False)
                                    save_live_data(live_db)
                                    st.success(f"🎉 सफलता! `{fr_target_col}` कॉलम में कुल {fr_match_count} रिकॉर्ड्स अपडेट होकर मास्टर डेटाबेस में सुरक्षित हो गए हैं।")
                                    st.session_state["p15_find_replace_confirm_chk"] = False
                                    st.rerun()
                                except Exception as fr_err:
                                    st.error(f"Find & Replace लागू करने में तकनीकी समस्या आई: {fr_err}")

                        # ======================================================================
                        # 🎓 न्यू सब-सिस्टम: Degree + Branch → Subject ऑटो-जेनरेटर
                        #    (Degree के ब्रैकेट में लिखा नंबर अपने-आप Duration कॉलम में चला जाएगा,
                        #     ब्रैकेट/उसका डेटा Degree से हट जाएगा, फिर Degree + Branch जोड़कर
                        #     "Degree (Branch)" फॉर्मेट में Subject कॉलम में लिख दिया जाएगा)
                        # ======================================================================
                        if role == "full_admin" and not st.session_state.admin_lock_state and "Degree" in live_db.columns:
                            st.markdown("---")
                            st.subheader("🎓 Degree + Branch → Subject Auto-Generator (Bracket → Duration)")
                            st.info(
                                "🔓 इस बटन को दबाने पर: Degree कॉलम में मौजूद `(...)` ब्रैकेट में अगर कोई नंबर लिखा है "
                                "तो वह नंबर उसी रो के Duration कॉलम में सेट हो जाएगा, और Degree से ब्रैकेट + उसके अंदर "
                                "का डेटा हटा दिया जाएगा। फिर Degree और Branch को जोड़कर Subject कॉलम में "
                                "`Degree (Branch)` फॉर्मेट में लिख दिया जाएगा। उदाहरण: Degree = `M.Sc.`, "
                                "Branch = `Home Science` → Subject = `M.Sc. (Home Science)`"
                            )

                            bracket_pattern = re.compile(r"\(([^)]*)\)")

                            if st.button(
                                "🚀 Process Degree/Branch → Subject & Duration (All Rows)",
                                type="primary",
                                use_container_width=True,
                                key="p15_degree_branch_subject_auto_btn"
                            ):
                                try:
                                    processed_counter = 0
                                    duration_updated_counter = 0

                                    for idx in live_db.index:
                                        degree_raw = str(live_db.at[idx, "Degree"]) if pd.notna(live_db.at[idx, "Degree"]) else ""
                                        if degree_raw.strip().lower() == "nan":
                                            degree_raw = ""

                                        branch_raw = ""
                                        if "Branch" in live_db.columns and pd.notna(live_db.at[idx, "Branch"]):
                                            branch_raw = str(live_db.at[idx, "Branch"])
                                            if branch_raw.strip().lower() == "nan":
                                                branch_raw = ""

                                        if degree_raw.strip() == "" and branch_raw.strip() == "":
                                            continue

                                        # 1️⃣ Degree में मौजूद हर ब्रैकेट ढूंढें
                                        bracket_matches = bracket_pattern.findall(degree_raw)

                                        # 2️⃣ अगर किसी ब्रैकेट के अंदर सिर्फ नंबर है तो वह Duration कॉलम में डालें
                                        for bracket_content in bracket_matches:
                                            num_match = re.search(r"\d+(\.\d+)?", bracket_content)
                                            if num_match:
                                                if "Duration" in live_db.columns:
                                                    live_db.at[idx, "Duration"] = num_match.group(0)
                                                    duration_updated_counter += 1
                                                break  # पहला नंबर वाला ब्रैकेट मिलते ही रुक जाएँ

                                        # 3️⃣ Degree से हर ब्रैकेट + उसके अंदर का डेटा हटा दें (चाहे नंबर हो या टेक्स्ट)
                                        clean_degree = bracket_pattern.sub("", degree_raw)
                                        clean_degree = re.sub(r"\s{2,}", " ", clean_degree).strip()

                                        # 4️⃣ Degree + Branch जोड़कर Subject कॉलम बनाएँ
                                        branch_clean = branch_raw.strip()
                                        if clean_degree and branch_clean:
                                            new_subject = f"{clean_degree} ({branch_clean})"
                                        elif clean_degree:
                                            new_subject = clean_degree
                                        else:
                                            new_subject = branch_clean

                                        live_db.at[idx, "Degree"] = clean_degree
                                        if "Subject" in live_db.columns:
                                            live_db.at[idx, "Subject"] = new_subject
                                        processed_counter += 1

                                    save_live_data(live_db)
                                    st.success(
                                        f"🎉 सफलता! कुल {processed_counter} रिकॉर्ड्स प्रोसेस किए गए, जिनमें से "
                                        f"{duration_updated_counter} रिकॉर्ड्स में ब्रैकेट वाला नंबर Duration कॉलम में अपडेट हुआ।"
                                    )
                                    st.balloons()
                                    st.rerun()
                                except Exception as deg_err:
                                    st.error(f"Degree/Branch → Subject प्रोसेस करने में तकनीकी समस्या आई: {deg_err}")

                        # ======================================================================
                        # 📚 न्यू सब-सिस्टम: बल्क सब्जेक्ट-वाइज ड्यूरेशन कस्टमाइज़र (सिर्फ एडमिन लॉक-सिक्योर)
                        # ======================================================================
                        if not live_db.empty and "Subject" in live_db.columns:
                            st.markdown("---")
                            st.subheader("📚 Bulk Subject-Wise Duration Settings (Admin Control)")
                            
                            # लॉक स्टेट के आधार पर एडमिन को निर्देश दिखाएं
                            if st.session_state.admin_lock_state:
                                st.warning("🔒 **यह ग्रिड अभी लॉक है:** ड्यूरेशन बदलने के लिए ऊपर जाकर पहले '🔓 लिस्ट अनलॉक करें (Editable)' बटन दबाएं।")
                            else:
                                st.info("🔓 **अनलॉक मोड सक्रिय:** अब आप किसी भी विषय के सामने उसकी कोर्स अवधि (Duration) बदल सकते हैं।")
                            
                            # 1. डेटाबेस से सभी उपलब्ध यूनीक विषयों की लिस्ट निकालें
                            unique_db_subjects = sorted([s for s in live_db["Subject"].dropna().unique() if str(s).strip() != ""])
                            
                            if not unique_db_subjects:
                                st.warning("⚠️ डेटाबेस में कोई भी विषय (Subject) नहीं मिला।")
                            else:
                                # 2. कस्टमाइज़ेशन के लिए एक डेटाफ्रेम मैट्रिक्स तैयार करें
                                subject_duration_mapping = []
                                for sub in unique_db_subjects:
                                    existing_sub_rows = live_db[live_db["Subject"] == sub]
                                    existing_duration = "3" # डिफ़ॉल्ट मान
                                    if not existing_sub_rows.empty:
                                        valid_durations = existing_sub_rows["Duration"].dropna().unique()
                                        valid_durations = [str(d).strip() for d in valid_durations if str(d).strip() != ""]
                                        if valid_durations:
                                            first_val = valid_durations[0].split('.')[0]
                                            if first_val in ["1", "2", "3", "4", "5", "6"]:
                                                existing_duration = first_val
                                    
                                    subject_duration_mapping.append({
                                        "Subject Name": sub,
                                        "Course Duration (Years)": existing_duration
                                    })
                                
                                sub_mapping_df = pd.DataFrame(subject_duration_mapping)
                                
                                # 🚨 सुरक्षा गेटवे: यदि मास्टर लिस्ट लॉक है, तो पूरा ग्रिड डिसेबल रहेगा
                                is_grid_disabled = st.session_state.admin_lock_state
                                
                                # 3. एडमिन के लिए एक इंटरैक्टिव कस्टमाइज़ेशन ग्रिड रेंडर करें
                                edited_sub_mapping_df = st.data_editor(
                                    sub_mapping_df,
                                    use_container_width=True,
                                    disabled=True if is_grid_disabled else ["Subject Name"], # लॉक होने पर पूरी टेबल फ्रीज हो जाएगी
                                    column_config={
                                        "Course Duration (Years)": st.column_config.SelectboxColumn(
                                            "Select Duration",
                                            options=["1", "2", "3", "4", "5", "6"],
                                            required=True,
                                            help="इस विषय के लिए कोर्स की कुल अवधि वर्षों में चुनें"
                                        )
                                    },
                                    key="p15_bulk_subject_duration_editor_grid_final_clean",
                                    hide_index=True
                                )
                                
                                # 🚨 सुरक्षा गेटवे 2: सेव बटन केवल तभी दिखाई देगा जब लिस्ट अनलॉक होगी
                                if not st.session_state.admin_lock_state:
                                    if st.button("💾 Apply & Update Bulk Subject Durations", type="primary", use_container_width=True, key="p15_save_bulk_sub_duration_btn"):
                                        try:
                                            bulk_update_counter = 0
                                            bulk_skip_counter = 0
                                            
                                            # ग्रिड की प्रत्येक रो को लूप करें और मास्टर डेटाबेस में बदलें
                                            for _, edit_row in edited_sub_mapping_df.iterrows():
                                                target_sub = edit_row["Subject Name"]
                                                new_duration_to_apply = edit_row["Course Duration (Years)"]
                                                
                                                # मास्टर डेटाबेस में इस सब्जेक्ट के सभी इंडेक्स ढूंढें
                                                sub_match_indices = live_db[live_db["Subject"] == target_sub].index
                                                
                                                if not sub_match_indices.empty:
                                                    for idx in sub_match_indices:
                                                        # 🚨 अगर इस रो में Duration पहले से भरा हुआ है, तो उसे छोड़ दें (ignore) और अगली रो पर जाएँ
                                                        existing_val = live_db.at[idx, "Duration"]
                                                        existing_val_str = "" if pd.isna(existing_val) else str(existing_val).strip()
                                                        if existing_val_str != "" and existing_val_str.lower() != "nan":
                                                            bulk_skip_counter += 1
                                                            continue

                                                        # Duration खाली है, तभी नया मान भरेंगे
                                                        live_db.at[idx, "Duration"] = str(new_duration_to_apply)
                                                        bulk_update_counter += 1
                                                        
                                            # परिवर्तनों को स्थायी रूप से सेव करें
                                            save_live_data(live_db)
                                            st.success(
                                                f"🎉 शत-प्रतिशत सफलता! कुल {bulk_update_counter} छात्रों का ड्यूरेशन डेटा विषय के अनुसार अपडेट कर दिया गया है। "
                                                f"({bulk_skip_counter} रिकॉर्ड्स को छोड़ दिया गया क्योंकि उनमें Duration पहले से भरा हुआ था)"
                                            )
                                            st.balloons()
                                            st.rerun()
                                        except Exception as bulk_err:
                                            st.error(f"सब्जेक्ट-वाइज ड्यूरेशन सिंक करने में तकनीकी समस्या आई: {bulk_err}")
