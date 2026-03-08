"""
Grievance Registration mock service router.
"""

import random
import string
from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class GrievanceRequest(BaseModel):
    name: str
    description: str
    category: str = "General"
    pin: str = ""


@router.post("/grievance")
async def register_grievance(payload: GrievanceRequest):
    """Register a mock grievance and return a ticket."""
    ticket_id = "GRV" + "".join(random.choices(string.digits, k=4))
    return {
        "ticket_id": ticket_id,
        "status": "Submitted",
        "submitted_at": datetime.now().isoformat(),
        "name": payload.name,
        "category": payload.category,
        "description": payload.description,
        "estimated_resolution": "7-10 working days",
        "policy_reference": "Centralized Public Grievance Redress and Monitoring System (CPGRAMS) — Citizens can lodge grievances related to service delivery of any government department.",
    }
