import pdfkit
import base64

# -------- WKHTML PATH --------
config = pdfkit.configuration(
    wkhtmltopdf=r"D:\WORK & PROJECTS\bluebit\wkhtmltopdf\bin\wkhtmltopdf.exe"
)

# -------- BASE64 FUNCTION --------
def b64(file):
    with open(file, "rb") as f:
        return base64.b64encode(f.read()).decode()

# -------- EMBED IMAGES --------
logo1 = b64("maha.png")
logo2 = b64("seva.png")
sign = b64("stamp.png")
stamp = b64("tick.png")

# -------- INPUTS --------
cert_no = input("Certificate Number: ")
name = input("Applicant Name: ")
village = input("Village: ")
taluka = input("Taluka: ")
district = input("District: ")
year = input("Financial Year: ")
income = input("Annual Income Amount: ")
income_words = input("Income In Words: ")
place = input("Place: ")
date = input("Date: ")

# -------- HTML TEMPLATE --------
html = f"""
<html>
<head>
<meta charset="UTF-8">

<style>

body {{
font-family: Arial;
}}

.page {{
width:850px;
height:1150px;
margin:auto;
padding:60px;
border:4px solid black;
position:relative;
}}

.top {{
display:flex;
justify-content:space-between;
}}

.barcode {{
position:absolute;
top:70px;
right:140px;
font-size:22px;
letter-spacing:4px;
}}

.title {{
text-align:center;
font-size:34px;
margin-top:20px;
font-weight:bold;
}}

.subtitle {{
text-align:center;
font-size:28px;
margin-top:10px;
}}

.text {{
margin-top:40px;
font-size:22px;
line-height:1.8;
text-align:justify;
}}

.table {{
margin-top:30px;
width:100%;
border-collapse:collapse;
font-size:22px;
}}

.table td,.table th {{
border:2px solid black;
padding:12px;
text-align:center;
}}

.footer {{
position:absolute;
bottom:130px;
left:60px;
font-size:22px;
}}

.sign {{
position:absolute;
bottom:180px;   /* moved UP */
right:120px;
}}

.stamp {{
position:absolute;
bottom:60px;    /* below sign */
right:120px;
}}

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
This is to certify that <b>{name}</b>, resident of <b>{village}</b>, 
Taluka <b>{taluka}</b>, District <b>{district}</b>, has an annual income 
as detailed below.
</div>

<table class="table">
<tr>
<th>Financial Year</th>
<th>Annual Income (₹)</th>
<th>Income In Words</th>
</tr>

<tr>
<td>{year}</td>
<td>{income}</td>
<td>{income_words}</td>
</tr>
</table>

<div class="text">
This certificate is issued based on the documents submitted by the applicant 
and is valid for one year from the date of issue.
</div>

<div class="footer">
Certificate No: {cert_no} <br>
Place: {place} <br>
Date: {date}
</div>

<div class="sign">
<img src="data:image/png;base64,{sign}" width="150">
</div>

<div class="stamp">
<img src="data:image/png;base64,{stamp}" width="220">
</div>

</div>

</body>
</html>
"""

options = {
    "page-size": "A4",
    "encoding": "UTF-8"
}

pdfkit.from_string(html, "income_certificate.pdf",
                   configuration=config,
                   options=options)

print("✅ English Income Certificate Generated Successfully")