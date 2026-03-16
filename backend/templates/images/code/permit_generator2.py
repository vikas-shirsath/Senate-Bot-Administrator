import pdfkit
import os

# -------- WKHTML PATH --------
config = pdfkit.configuration(
    wkhtmltopdf=r"D:\WORK & PROJECTS\bluebit\wkhtmltopdf\bin\wkhtmltopdf.exe"
)

# -------- INPUTS --------
issue_no = input("Issue Number: ")
owner = input("Owner / Organization Name: ")
business = input("Business Name: ")
address = input("Address: ")
activity = input("Type of Activity: ")
authority = input("Issuing Authority: ")
permit_no = input("Permit Number: ")
start_date = input("Start Date: ")
end_date = input("Expiry Date: ")
city = input("City: ")
date = input("Issued Date: ")

# -------- ASSET PATHS --------
emblem = os.path.abspath("emblem.png")
maha_logo = os.path.abspath("maha.png")
stamp = os.path.abspath("stamp.png")

# -------- HTML --------
html = f"""
<html>
<head>
<style>

body {{
    font-family: "Times New Roman";
    background:white;
}}

.page {{
    width: 850px;
    height: 1150px;
    margin:auto;
    padding:70px;
    border:14px solid black;
    position:relative;
}}

.issue {{
    position:absolute;
    top:40px;
    left:70px;
    font-size:20px;
}}

.maha {{
    position:absolute;
    top:30px;
    right:70px;
}}

.centerlogo {{
    text-align:center;
    margin-top:30px;
}}

.title {{
    text-align:center;
    font-size:40px;
    font-weight:bold;
    margin-top:15px;
}}

.subtitle {{
    text-align:center;
    font-size:26px;
    margin-top:10px;
    letter-spacing:3px;
}}

.text {{
    margin-top:60px;
    font-size:24px;
    line-height:2.0;
    text-align:justify;
}}

.conditions {{
    margin-top:30px;
    font-size:22px;
    line-height:1.8;
}}

.footer {{
    margin-top:40px;
    font-size:22px;
}}

.sign {{
    position:absolute;
    bottom:120px;
    left:90px;
    font-size:22px;
}}

.stamp {{
    position:absolute;
    bottom:80px;
    right:90px;
}}

</style>
</head>

<body>

<div class="page">

<div class="issue">Issue No: {issue_no}</div>

<div class="maha">
<img src="file:///{maha_logo}" width="90">
</div>

<div class="centerlogo">
<img src="file:///{emblem}" width="110">
</div>

<div class="title">OFFICIAL PERMIT CERTIFICATE</div>
<div class="subtitle">GOVERNMENT AUTHORIZATION</div>

<div class="text">
This is to certify that <b>{owner}</b>, operating under the name 
<b>{business}</b>, located at <b>{address}</b>, is hereby granted 
permission by <b>{authority}</b> to conduct <b>{activity}</b> in accordance 
with applicable rules and regulations.

This permit is issued under Permit Number <b>{permit_no}</b> and shall remain 
valid from <b>{start_date}</b> to <b>{end_date}</b>, unless suspended or 
revoked by the issuing authority for non-compliance with prescribed conditions.
</div>

<div class="conditions">
<b>Conditions:</b><br>
    1.Comply with all applicable laws and safety standards.<br>
    2.Display this permit at the place of business at all times.<br>
    3.Allow inspection by authorized officials whenever required.<br>
    4.Ensure activity does not cause public nuisance or environmental harm.<br>
</div>

<div class="footer">
Issued on: <b>{date}</b><br>
Place: <b>{city}</b>
</div>

<div class="sign">
_________________________<br>
Authorized Signatory
</div>

<div class="stamp">
<img src="file:///{stamp}" width="150">
</div>

</div>

</body>
</html>
"""

options = {
    "enable-local-file-access": None,
    "page-size": "A4"
}

pdfkit.from_string(html, "permit_certificate.pdf",
                   configuration=config,
                   options=options)

print("✅ Permit Certificate Generated Successfully")