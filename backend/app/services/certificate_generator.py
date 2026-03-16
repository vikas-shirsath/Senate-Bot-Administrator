"""
Certificate Generator — converts data into PDF certificates using pdfkit.
Uses the user-provided HTML templates for Permit and Income certificates.
"""

import os
import base64
import pdfkit
from datetime import datetime


# ── Paths ──────────────────────────────────────────────
_TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "templates", "images")

# wkhtmltopdf binary
_WKHTML_PATH = os.getenv(
    "WKHTMLTOPDF_PATH",
    r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
)

_config = pdfkit.configuration(wkhtmltopdf=_WKHTML_PATH)


def _b64_image(filename: str) -> str:
    """Read an image file and return its base64 string."""
    path = os.path.join(_TEMPLATE_DIR, filename)
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def _file_uri(filename: str) -> str:
    """Return a file:/// URI for an image (used by wkhtmltopdf)."""
    path = os.path.abspath(os.path.join(_TEMPLATE_DIR, filename))
    return path.replace("\\", "/")


def calculate_expiry_date(start_date_str: str) -> str:
    """
    Expiry = 31 March of the year that is 3 years after start_date.
    Example: start 6 Aug 2026 → expiry 31 March 2029
    """
    try:
        # Try multiple date formats
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d %B %Y", "%B %d, %Y"):
            try:
                dt = datetime.strptime(start_date_str.strip(), fmt)
                break
            except ValueError:
                continue
        else:
            # Default: assume it's a year
            dt = datetime(int(start_date_str.strip()[:4]), 1, 1)

        expiry_year = dt.year + 3
        return f"31 March {expiry_year}"
    except Exception:
        return "31 March 2029"


def generate_permit_number(seq_id: int) -> str:
    """PERMIT-MH-{YEAR}-{SEQ:05d}"""
    year = datetime.now().year
    return f"PERMIT-MH-{year}-{seq_id:05d}"


def generate_income_cert_number(seq_id: int) -> str:
    """INC-MH-{YEAR}-{SEQ:05d}"""
    year = datetime.now().year
    return f"INC-MH-{year}-{seq_id:05d}"


def generate_issue_number(seq_id: int) -> str:
    """ISS-{YEAR}-{SEQ:05d}"""
    year = datetime.now().year
    return f"ISS-{year}-{seq_id:05d}"


# ═══════════════════════════════════════════════════════
# Permit Certificate PDF
# ═══════════════════════════════════════════════════════

def generate_permit_pdf(data: dict) -> bytes:
    """
    Generate a Permit Certificate PDF from data dict.
    Returns raw PDF bytes.
    """
    emblem = _file_uri("emblem.png")
    maha_logo = _file_uri("maha.png")
    stamp = _file_uri("stamp.png")

    html = f"""
<html>
<head>
<style>
body {{ font-family: "Times New Roman"; background: white; }}
.page {{ width: 850px; height: 1150px; margin: auto; padding: 70px;
         border: 14px solid black; position: relative; }}
.issue {{ position: absolute; top: 40px; left: 70px; font-size: 20px; }}
.maha {{ position: absolute; top: 30px; right: 70px; }}
.centerlogo {{ text-align: center; margin-top: 30px; }}
.title {{ text-align: center; font-size: 40px; font-weight: bold; margin-top: 15px; }}
.subtitle {{ text-align: center; font-size: 26px; margin-top: 10px; letter-spacing: 3px; }}
.text {{ margin-top: 60px; font-size: 24px; line-height: 2.0; text-align: justify; }}
.conditions {{ margin-top: 30px; font-size: 22px; line-height: 1.8; }}
.footer {{ margin-top: 40px; font-size: 22px; }}
.sign {{ position: absolute; bottom: 120px; left: 90px; font-size: 22px; }}
.stamp {{ position: absolute; bottom: 80px; right: 90px; }}
</style>
</head>
<body>
<div class="page">
    <div class="issue">Issue No: {data['issue_number']}</div>
    <div class="maha"><img src="file:///{maha_logo}" width="90"></div>
    <div class="centerlogo"><img src="file:///{emblem}" width="110"></div>
    <div class="title">OFFICIAL PERMIT CERTIFICATE</div>
    <div class="subtitle">GOVERNMENT AUTHORIZATION</div>
    <div class="text">
        This is to certify that <b>{data['owner']}</b>, operating under the name
        <b>{data['business']}</b>, located at <b>{data['address']}</b>, is hereby granted
        permission by <b>{data['authority']}</b> to conduct <b>{data['activity']}</b> in accordance
        with applicable rules and regulations.
        <br><br>
        This permit is issued under Permit Number <b>{data['permit_number']}</b> and shall remain
        valid from <b>{data['start_date']}</b> to <b>{data['expiry_date']}</b>, unless suspended or
        revoked by the issuing authority for non-compliance with prescribed conditions.
    </div>
    <div class="conditions">
        <b>Conditions:</b><br>
        1. Comply with all applicable laws and safety standards.<br>
        2. Display this permit at the place of business at all times.<br>
        3. Allow inspection by authorized officials whenever required.<br>
        4. Ensure activity does not cause public nuisance or environmental harm.<br>
    </div>
    <div class="footer">
        Issued on: <b>{data['issued_date']}</b><br>
        Place: <b>{data['city']}</b>
    </div>
    <div class="sign">_________________________<br>Authorized Signatory</div>
    <div class="stamp"><img src="file:///{stamp}" width="150"></div>
</div>
</body>
</html>
"""

    options = {"enable-local-file-access": None, "page-size": "A4"}
    pdf_bytes = pdfkit.from_string(html, False, configuration=_config, options=options)
    return pdf_bytes


# ═══════════════════════════════════════════════════════
# Income Certificate PDF
# ═══════════════════════════════════════════════════════

def generate_income_pdf(data: dict) -> bytes:
    """
    Generate an Income Certificate PDF from data dict.
    Returns raw PDF bytes.
    """
    logo1 = _b64_image("maha.png")
    logo2 = _b64_image("seva.png")
    sign_img = _b64_image("stamp.png")
    stamp_img = _b64_image("tick.png")

    html = f"""
<html>
<head>
<meta charset="UTF-8">
<style>
body {{ font-family: Arial; }}
.page {{ width: 850px; height: 1150px; margin: auto; padding: 60px;
         border: 4px solid black; position: relative; }}
.top {{ display: flex; justify-content: space-between; }}
.barcode {{ position: absolute; top: 70px; right: 140px; font-size: 22px; letter-spacing: 4px; }}
.title {{ text-align: center; font-size: 34px; margin-top: 20px; font-weight: bold; }}
.subtitle {{ text-align: center; font-size: 28px; margin-top: 10px; }}
.text {{ margin-top: 40px; font-size: 22px; line-height: 1.8; text-align: justify; }}
.table {{ margin-top: 30px; width: 100%; border-collapse: collapse; font-size: 22px; }}
.table td, .table th {{ border: 2px solid black; padding: 12px; text-align: center; }}
.footer {{ position: absolute; bottom: 130px; left: 60px; font-size: 22px; }}
.sign {{ position: absolute; bottom: 180px; right: 120px; }}
.stamp {{ position: absolute; bottom: 60px; right: 120px; }}
</style>
</head>
<body>
<div class="page">
    <div class="top">
        <img src="data:image/png;base64,{logo1}" width="90">
        <img src="data:image/png;base64,{logo2}" width="120">
    </div>
    <div class="barcode">||||||||||||||||||||||||||||</div>
    <div class="title">Office of the Tahsildar</div>
    <div class="subtitle">INCOME CERTIFICATE</div>
    <div class="text">
        This is to certify that <b>{data['name']}</b>, resident of <b>{data['village']}</b>,
        Taluka <b>{data['taluka']}</b>, District <b>{data['district']}</b>, has an annual income
        as detailed below.
    </div>
    <table class="table">
        <tr><th>Financial Year</th><th>Annual Income (₹)</th><th>Income In Words</th></tr>
        <tr><td>{data['financial_year']}</td><td>{data['annual_income']}</td><td>{data['income_words']}</td></tr>
    </table>
    <div class="text">
        This certificate is issued based on the documents submitted by the applicant
        and is valid for one year from the date of issue.
    </div>
    <div class="footer">
        Certificate No: {data['certificate_number']}<br>
        Place: {data['place']}<br>
        Date: {data['date']}
    </div>
    <div class="sign"><img src="data:image/png;base64,{sign_img}" width="150"></div>
    <div class="stamp"><img src="data:image/png;base64,{stamp_img}" width="220"></div>
</div>
</body>
</html>
"""

    options = {"page-size": "A4", "encoding": "UTF-8"}
    pdf_bytes = pdfkit.from_string(html, False, configuration=_config, options=options)
    return pdf_bytes
