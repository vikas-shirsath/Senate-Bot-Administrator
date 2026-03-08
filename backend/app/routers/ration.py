"""
Ration Card mock service router.
"""

from fastapi import APIRouter

router = APIRouter()

# ── Mock data store ──────────────────────────────────────
_RATION_DB: dict[str, dict] = {
    "MH123456": {
        "ration_id": "MH123456",
        "holder_name": "Rajesh Kumar",
        "status": "Active",
        "card_type": "BPL",
        "entitlement": "5 kg wheat, 3 kg rice per person per month",
        "scheme": "National Food Security Act",
        "family_members": 4,
        "district": "Mumbai",
        "state": "Maharashtra",
        "policy_reference": "National Food Security Act 2013, Section 3 — Every eligible household is entitled to receive subsidized food grains from the Targeted Public Distribution System.",
    },
    "MH789012": {
        "ration_id": "MH789012",
        "holder_name": "Sunita Devi",
        "status": "Inactive",
        "card_type": "AAY",
        "entitlement": "35 kg food grains per household per month",
        "scheme": "Antyodaya Anna Yojana",
        "family_members": 6,
        "district": "Pune",
        "state": "Maharashtra",
        "policy_reference": "Antyodaya Anna Yojana — Launched in December 2000, this scheme targets the poorest of the poor families.",
    },
}


@router.get("/ration/{ration_id}")
async def get_ration_status(ration_id: str):
    """Return mock ration-card status for a given ID."""
    record = _RATION_DB.get(ration_id.upper())
    if record:
        return record
    # Generic fallback for any unknown ID
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
