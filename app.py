import streamlit as pd_st
import csv
import io

# Website configuration (Standard wide layout)
pd_st.set_page_config(layout="wide") 

# Custom CSS: Print media rules taaki print me sirf foils aayein
pd_st.markdown("""
 <style>
 @media print {
 header, [data-testid="stHeader"], [data-testid="stSidebar"], 
 .stButton, .stFileUploader, [data-testid="stDecoration"], 
 [data-testid="stNotification"], h1, h3, .stAlert, .web-only-btn {
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
 </style>
""", unsafe_allow_html=True) 

pd_st.title("🏫 College CCE Foil Sheet Generator") 
pd_st.subheader("Institute of Law, Govt. Kamlaraja Girls Post-Graduate Autonomous College, Gwalior,(M.P.)") 

# File Upload Option
uploaded_file = pd_st.file_uploader("Apni 'master_sheet.csv' file yahan upload karein", type=["csv"]) 

if uploaded_file is not None: 
    stringio = io.StringIO(uploaded_file.getvalue().decode("utf-8")) 
    csv_reader = csv.DictReader(stringio) 
    all_rows = list(csv_reader) 
 
    pd_st.success("✅ Master sheet successfully upload ho gayi hai!") 
 
    # Dynamic Current Year Calculation based on the highest year in 'Admission Year' column
    years_found = []
    for row in all_rows:
        ay_val = row.get('Admission Year', row.get('admission year', '')).strip()
        # Find 4-digit numbers
        matches = re.findall(r'\b\d{4}\b', ay_val)
        for m in matches:
            years_found.append(int(m))
            
    if years_found:
        current_calendar_year = max(years_found)
    else:
        current_calendar_year = 2026  # Default fallback if no years found
        
    pd_st.info(f"Detected Current Year (Highest Admission Year): **{current_calendar_year}**")

    # Semester Dropdown
    semesters = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"] 
    target_sem = pd_st.selectbox("Kaun sa Semester chahiye?", semesters) 
 
    sem_to_year_num = { 
        "1": "1", "2": "1", 
        "3": "2", "4": "2", 
        "5": "3", "6": "3", 
        "7": "4", "8": "4", 
        "9": "5", "10": "5"
    } 
    target_num = sem_to_year_num[target_sem] 
 
    # Offset Calculation for EX-Students based on dynamic current year
    year_offsets = {"1": 0, "2": 1, "3": 2, "4": 3, "5": 4}
    target_offset = year_offsets[target_num]
    ex_target_year_str = str(current_calendar_year - target_offset)
 
    college_name = "GOVT. K.R.G. POST-GRADUATE AUTONOMOUS COLLEGE, GWALIOR (M.P.)"
    exam_info = f"Examination :- CCE &nbsp;&nbsp;&nbsp;&nbsp; B.A. LL.B. {target_sem}th SEMESTER"
 
    regular_rolls = [] 
    ex_rolls = [] 
 
    for row in all_rows: 
        roll = row.get('Roll No.', row.get('Roll No', '')).strip() 
        student_year = row.get('year', row.get('YEAR', row.get('Year', ''))).strip().lower() 
        status = row.get('Status', row.get('STATUS', '')).strip().upper() 
        row_sem = row.get('Semester', row.get('SEMESTER', row.get('sem', ''))).strip() 
        
        row_admission_year = row.get('Admission Year', row.get('admission year', '')).strip()
 
        if not roll: 
            continue
 
        # Regular Students Logic
        if target_num in student_year and 'REGULAR' in status: 
            regular_rolls.append(roll) 
            
        # EX-Students Logic with Dynamic Year Offset checked against 'Admission Year'
        elif 'EX-STUDENT' in status or 'EX' in status: 
            if ex_target_year_str in row_admission_year: 
                ex_rolls.append(roll) 
 
    # Sort and Remove Duplicates
    regular_rolls = sorted(list(set(regular_rolls))) 
    ex_rolls = sorted(list(set(ex_rolls))) 
 
    # EX-Students first, then Regular Students
    roll_numbers = ex_rolls + regular_rolls 
 
    if roll_numbers: 
        pd_st.info(f"Total {len(roll_numbers)} students mile hain (EX: {len(ex_rolls)}, Regular: {len(regular_rolls)}). Niche aapka format ready hai.") 
        left_side_rolls = roll_numbers[:30] 
        right_side_rolls = roll_numbers[30:60] 

        # Reusable function to create an independent Foil Block content
        def generate_html_block(rolls, start_idx, foil_label, has_data): 
            if not has_data: 
                return '<div class="foil-unit" style="border:none; background:transparent;"></div>'
 
            block = f"""
            <div class="foil-unit">
            <div class="top-fields">
            <div></div><div>Paper Code....................</div>
            </div>
            <div class="top-fields" style="margin-top: 5px;">
            <div></div><div>Bundle No....................</div>
            </div>
            <div class="header-box">{college_name}</div>
            <div class="sub-box exam-right">{exam_info}</div>
            <div class="sub-box">Subject.................................................... Paper.........................</div>
            <div class="marks-info">
            <div>Max. Marks: ...................</div>
            <div>Min. Pass Marks: ...................</div>
            </div>
            <div class="foil-title">{foil_label}</div>
            <table>
            <tr>
            <th class="col-header-num" style="width: 8%;">1</th>
            <th class="col-header-num" style="width: 30%;" colspan="3">2</th>
            </tr>
            <tr>
            <th rowspan="2">Code No.</th>
            <th rowspan="2">Roll No.</th>
            <th colspan="2">Marks Obtained</th>
            </tr>
            <tr>
            <th style="width: 15%;">In Figures</th>
            <th style="width: 45%;">In Words</th>
            </tr>
            """
            for i, r in enumerate(rolls, start=start_idx): 
                block += f"""
                <tr>
                <td><b>{i}</b></td>
                <td>{r}</td>
                <td></td>
                <td></td>
                </tr>"""
 
            # Form height symmetric rakhne ke liye khali rows
            current_len = len(rolls) 
            if current_len < 30: 
                for k in range(current_len + start_idx, 30 + start_idx): 
                    block += """
                    <tr>
                    <td>&nbsp;</td>
                    <td>&nbsp;</td>
                    <td>&nbsp;</td>
                    <td>&nbsp;</td>
                    </tr>"""
            block += f"""
            </table>
            <div class="note">
            <b>Note:</b> Roll Number and Marks awarded to the candidate may be entered under respective columns very carefully. Marks and Roll Number should be legible. These may be checked again to ensure that no mistake remains.
            </div>
            <div class="footer-fields">
            Signature of Examiner...............................................................<br>
            Name of Examiner.....................................................................<br>
            ....................................................................................................<br>
            <div style="display: flex; justify-content: space-between; margin-top: 5px;">
            <div>Place.......................................................</div>
            <div>Date: ___/___/{current_calendar_year}</div>
            </div>
            </div>
            </div>
            """
            return block

        # --- SIDE-BY-SIDE LAYOUT WITH INTEGRATED ACTIONABLE PRINT BUTTON ---
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
        .foil-title {{ text-align: center; font-weight: bold; background-color: #f2f2f2; border: 1px solid black; border-bottom: none; padding: 4px 0; font-size: 13px; margin-top: 5px; }}
        table {{ width: 100%; border-collapse: collapse; text-align: center; font-size: 12px; }}
        th, td {{ border: 1px solid black; padding: 4px; height: 22px; }}
        .col-header-num {{ font-size: 10px; background-color: #f9f9f9; }}
        .note {{ font-size: 10.5px; padding: 8px 4px; border-top: 2px solid black; border-bottom: 2px solid black; text-align: justify; margin-top: 15px; }}
        .footer-fields {{ margin-top: 15px; font-size: 12px; font-weight: bold; line-height: 1.8; }}
 
        @media print {{
        body {{ max-width: 100%; padding: 0; }}
        .flex-container {{ gap: 15px; }}
        .print-action-area {{ display: none !important; }}
        }}
        </style>
        </head>
        <body>
        <div class="print-action-area">
        <button class="action-btn" onclick="window.print()">🖨  Print Only Foils (Portrait)</button>
        </div>
 
        <div class="flex-container">
        """
        full_html += generate_html_block(left_side_rolls, 1, "FOIL", True) 
        has_right_data = len(right_side_rolls) > 0
        full_html += generate_html_block(right_side_rolls, 31, "FOIL", has_right_data) 
        full_html += """
        </div>
        </body>
        </html>
        """
        pd_st.components.v1.html(full_html, height=1550, scrolling=False) 
    else: 
        pd_st.error("⚠  Is Semester ka koi data nahi mila.")
