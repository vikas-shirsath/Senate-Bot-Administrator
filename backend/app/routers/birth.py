"""
Birth Certificate service router — Supabase-backed.
"""

from fastapi import APIRouter
from app.supabase_client import get_supabase

router = APIRouter()


@router.get("/birth/{certificate_id}")
async def get_birth_status(certificate_id: str):
    """Look up a birth certificate by ID from the database."""
    sb = get_supabase()
    result = (
        sb.table("birth_certificates")
        .select("*")
        .eq("certificate_id", certificate_id.upper())
        .execute()
    )
    if result.data:
        rec = result.data[0]
        return {
            "certificate_id": rec["certificate_id"],
            "name": rec["name"],
            "status": rec["status"],
            "issue_date": rec.get("issue_date"),
            "district": rec["district"],
            "state": rec["state"],
            "date_of_birth": rec.get("date_of_birth"),
            "father_name": rec.get("father_name", ""),
            "mother_name": rec.get("mother_name", ""),
            "place_of_birth": rec.get("place_of_birth", ""),
            "policy_reference": rec["policy_reference"],
        }
    return {
        "certificate_id": certificate_id,
        "name": "Unknown",
        "status": "Not Found",
        "issue_date": None,
        "district": "N/A",
        "state": "N/A",
        "policy_reference": "No matching record found. Please verify the certificate ID.",
    }
