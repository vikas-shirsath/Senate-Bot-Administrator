"""
Ration Card service router — Supabase-backed.
"""

from fastapi import APIRouter, Depends
from app.auth import get_current_user
from app.supabase_client import get_supabase

router = APIRouter()


@router.get("/ration/{ration_id}")
async def get_ration_status(ration_id: str):
    """Look up a ration card by ID from the database."""
    sb = get_supabase()
    result = (
        sb.table("ration_cards")
        .select("*")
        .eq("ration_id", ration_id.upper())
        .execute()
    )
    if result.data:
        rec = result.data[0]
        return {
            "ration_id": rec["ration_id"],
            "holder_name": rec["holder_name"],
            "status": rec["status"],
            "card_type": rec["card_type"],
            "entitlement": rec["entitlement"],
            "scheme": rec["scheme"],
            "family_members": rec["family_members"],
            "district": rec["district"],
            "state": rec["state"],
            "policy_reference": rec["policy_reference"],
        }
    return {
        "ration_id": ration_id,
        "holder_name": "Unknown",
        "status": "Not Found",
        "card_type": "N/A",
        "entitlement": "N/A",
        "scheme": "N/A",
        "family_members": 0,
        "district": "N/A",
        "state": "N/A",
        "policy_reference": "No matching record found. Please verify the ration card number and try again.",
    }
