"""
Certificates router — endpoints for generating permit & income certificates,
uploading documents, and listing user certificates.
"""

import uuid
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from app.auth import get_current_user
from app.supabase_client import get_supabase
from app.services.certificate_generator import (
    generate_permit_pdf, generate_income_pdf,
    generate_permit_number, generate_income_cert_number,
    generate_issue_number, calculate_expiry_date,
)

router = APIRouter()


# ── Document Upload ──────────────────────────────────
@router.post("/upload-document")
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str = Form("aadhaar"),
    user: dict = Depends(get_current_user),
):
    """Upload Aadhaar/PAN to Supabase Storage bucket 'user_documents'."""
    allowed = (".pdf", ".jpg", ".jpeg", ".png")
    ext = "." + (file.filename or "file.png").rsplit(".", 1)[-1].lower()
    if ext not in allowed:
        raise HTTPException(400, f"File type {ext} not allowed. Use PDF, JPG, or PNG.")

    file_bytes = await file.read()
    file_name = f"{user['id']}/{doc_type}_{uuid.uuid4().hex[:8]}{ext}"

    sb = get_supabase()
    # Upload to storage
    try:
        sb.storage.from_("user_documents").upload(
            file_name, file_bytes,
            file_options={"content-type": file.content_type or "application/octet-stream"}
        )
    except Exception as e:
        # If file exists, try with different name
        file_name = f"{user['id']}/{doc_type}_{uuid.uuid4().hex}{ext}"
        sb.storage.from_("user_documents").upload(
            file_name, file_bytes,
            file_options={"content-type": file.content_type or "application/octet-stream"}
        )

    # Get public URL
    public_url = sb.storage.from_("user_documents").get_public_url(file_name)

    return {"url": public_url, "doc_type": doc_type, "filename": file.filename}


# ── Permit Certificate ──────────────────────────────
class PermitRequest(BaseModel):
    owner: str
    business: str
    address: str
    activity: str
    start_date: str
    city: str
    issued_date: str
    aadhaar_document_url: str = ""
    pan_document_url: str = ""


@router.post("/permit")
async def create_permit_certificate(
    req: PermitRequest,
    user: dict = Depends(get_current_user),
):
    sb = get_supabase()

    # Get next sequential ID
    count_result = sb.table("permit_certificates").select("id", count="exact").execute()
    seq_id = (count_result.count or 0) + 1

    permit_number = generate_permit_number(seq_id)
    issue_number = generate_issue_number(seq_id)
    expiry_date = calculate_expiry_date(req.start_date)
    authority = "Government of Maharashtra"

    cert_data = {
        "issue_number": issue_number,
        "permit_number": permit_number,
        "owner": req.owner,
        "business": req.business,
        "address": req.address,
        "activity": req.activity,
        "authority": authority,
        "start_date": req.start_date,
        "expiry_date": expiry_date,
        "city": req.city,
        "issued_date": req.issued_date,
    }

    # Generate PDF
    try:
        pdf_bytes = generate_permit_pdf(cert_data)
    except Exception as e:
        raise HTTPException(500, f"PDF generation failed: {str(e)}")

    # Upload PDF to Supabase Storage
    pdf_filename = f"permit_{permit_number.replace('-', '_')}.pdf"
    try:
        sb.storage.from_("certificates").upload(
            pdf_filename, pdf_bytes,
            file_options={"content-type": "application/pdf"}
        )
    except Exception:
        pdf_filename = f"permit_{uuid.uuid4().hex[:8]}.pdf"
        sb.storage.from_("certificates").upload(
            pdf_filename, pdf_bytes,
            file_options={"content-type": "application/pdf"}
        )

    certificate_url = sb.storage.from_("certificates").get_public_url(pdf_filename)

    # Save to database
    db_record = {
        "user_id": user["id"],
        "issue_number": issue_number,
        "permit_number": permit_number,
        "owner": req.owner,
        "business": req.business,
        "address": req.address,
        "activity": req.activity,
        "authority": authority,
        "start_date": req.start_date,
        "expiry_date": expiry_date,
        "city": req.city,
        "issued_date": req.issued_date,
        "aadhaar_document_url": req.aadhaar_document_url,
        "pan_document_url": req.pan_document_url,
        "certificate_url": certificate_url,
    }
    sb.table("permit_certificates").insert(db_record).execute()

    return {
        "success": True,
        "permit_number": permit_number,
        "issue_number": issue_number,
        "expiry_date": expiry_date,
        "certificate_url": certificate_url,
    }


# ── Income Certificate ──────────────────────────────
class IncomeRequest(BaseModel):
    name: str
    village: str
    taluka: str
    district: str
    financial_year: str
    annual_income: str
    income_words: str
    place: str
    date: str
    aadhaar_document_url: str = ""
    pan_document_url: str = ""


@router.post("/income")
async def create_income_certificate(
    req: IncomeRequest,
    user: dict = Depends(get_current_user),
):
    sb = get_supabase()

    # Get next sequential ID
    count_result = sb.table("income_certificates").select("id", count="exact").execute()
    seq_id = (count_result.count or 0) + 1

    certificate_number = generate_income_cert_number(seq_id)

    cert_data = {
        "certificate_number": certificate_number,
        "name": req.name,
        "village": req.village,
        "taluka": req.taluka,
        "district": req.district,
        "financial_year": req.financial_year,
        "annual_income": req.annual_income,
        "income_words": req.income_words,
        "place": req.place,
        "date": req.date,
    }

    # Generate PDF
    try:
        pdf_bytes = generate_income_pdf(cert_data)
    except Exception as e:
        raise HTTPException(500, f"PDF generation failed: {str(e)}")

    # Upload PDF to Supabase Storage
    pdf_filename = f"income_{certificate_number.replace('-', '_')}.pdf"
    try:
        sb.storage.from_("certificates").upload(
            pdf_filename, pdf_bytes,
            file_options={"content-type": "application/pdf"}
        )
    except Exception:
        pdf_filename = f"income_{uuid.uuid4().hex[:8]}.pdf"
        sb.storage.from_("certificates").upload(
            pdf_filename, pdf_bytes,
            file_options={"content-type": "application/pdf"}
        )

    certificate_url = sb.storage.from_("certificates").get_public_url(pdf_filename)

    # Save to database
    db_record = {
        "user_id": user["id"],
        "certificate_number": certificate_number,
        "name": req.name,
        "village": req.village,
        "taluka": req.taluka,
        "district": req.district,
        "financial_year": req.financial_year,
        "annual_income": req.annual_income,
        "income_words": req.income_words,
        "place": req.place,
        "date": req.date,
        "aadhaar_document_url": req.aadhaar_document_url,
        "pan_document_url": req.pan_document_url,
        "certificate_url": certificate_url,
    }
    sb.table("income_certificates").insert(db_record).execute()

    return {
        "success": True,
        "certificate_number": certificate_number,
        "certificate_url": certificate_url,
    }


# ── My Certificates ─────────────────────────────────
@router.get("/my-certificates")
async def my_certificates(user: dict = Depends(get_current_user)):
    sb = get_supabase()

    permits = (
        sb.table("permit_certificates")
        .select("*")
        .eq("user_id", user["id"])
        .order("created_at", desc=True)
        .execute()
    )

    incomes = (
        sb.table("income_certificates")
        .select("*")
        .eq("user_id", user["id"])
        .order("created_at", desc=True)
        .execute()
    )

    return {
        "permit_certificates": permits.data,
        "income_certificates": incomes.data,
    }
