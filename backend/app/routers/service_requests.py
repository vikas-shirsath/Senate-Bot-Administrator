"""
Service Requests router — endpoints for listing user's service requests.
"""

from fastapi import APIRouter, Depends
from app.auth import get_current_user
from app.supabase_client import get_supabase

router = APIRouter()


@router.get("")
async def list_service_requests(user: dict = Depends(get_current_user)):
    """List all service requests for the authenticated user."""
    sb = get_supabase()
    result = (
        sb.table("service_requests")
        .select("*")
        .eq("user_id", user["id"])
        .order("created_at", desc=True)
        .execute()
    )
    return result.data
