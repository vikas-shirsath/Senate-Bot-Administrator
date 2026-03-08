"""
Birth Certificate mock service router.
"""

from fastapi import APIRouter

router = APIRouter()

_BIRTH_DB: dict[str, dict] = {
    "BC1021": {
        "certificate_id": "BC1021",
        "name": "Amit Sharma",
        "status": "Issued",
        "issue_date": "2023-05-10",
        "district": "Mumbai",
        "state": "Maharashtra",
        "policy_reference": "Registration of Births and Deaths Act 1969, Section 8 — Birth must be registered within 21 days.",
    },
    "BC2045": {
        "certificate_id": "BC2045",
        "name": "Priya Patil",
        "status": "Processing",
        "issue_date": None,
        "district": "Pune",
        "state": "Maharashtra",
        "policy_reference": "Registration of Births and Deaths Act 1969 — Delayed registration may require an affidavit and magistrate order.",
    },
}


@router.get("/birth/{certificate_id}")
async def get_birth_status(certificate_id: str):
    """Return mock birth-certificate status."""
    record = _BIRTH_DB.get(certificate_id.upper())
    if record:
        return record
    return {
        "certificate_id": certificate_id,
        "name": "Unknown",
        "status": "Not Found",
        "issue_date": None,
        "district": "N/A",
        "state": "N/A",
        "policy_reference": "No matching record found. Please verify the certificate ID.",
    }
