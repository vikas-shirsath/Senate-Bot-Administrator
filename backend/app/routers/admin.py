"""
Admin router — endpoints for admin users to manage users and service requests.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.auth import get_current_user
from app.supabase_client import get_supabase

router = APIRouter()


# ── Admin guard ──────────────────────────────────────
async def require_admin(user: dict = Depends(get_current_user)):
    """Check that the current user has admin role."""
    sb = get_supabase()
    result = sb.table("users").select("role").eq("id", user["id"]).execute()
    if not result.data or result.data[0].get("role") != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin access required")
    return user


# ── Set user role ────────────────────────────────────
class RoleRequest(BaseModel):
    role: str  # "user" or "admin"


@router.post("/set-role")
async def set_role(req: RoleRequest, user: dict = Depends(get_current_user)):
    """Set the current user's role (user/admin)."""
    if req.role not in ("user", "admin"):
        raise HTTPException(400, "Role must be 'user' or 'admin'")

    sb = get_supabase()
    sb.table("users").update({"role": req.role}).eq("id", user["id"]).execute()
    return {"ok": True, "role": req.role}


@router.get("/me/role")
async def get_role(user: dict = Depends(get_current_user)):
    """Get the current user's role."""
    sb = get_supabase()
    result = sb.table("users").select("role").eq("id", user["id"]).execute()
    role = result.data[0].get("role", "user") if result.data else "user"
    return {"role": role}


# ── List all users (admin only) ──────────────────────
@router.get("/users")
async def list_users(user: dict = Depends(require_admin)):
    sb = get_supabase()
    result = (
        sb.table("users")
        .select("id, email, name, role, created_at")
        .order("created_at", desc=True)
        .execute()
    )
    return result.data


# ── List ALL service requests (admin only) ───────────
@router.get("/service-requests")
async def list_all_service_requests(user: dict = Depends(require_admin)):
    sb = get_supabase()

    # Get all service requests
    requests = (
        sb.table("service_requests")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )

    # Enrich with user email
    user_ids = list(set(r.get("user_id") for r in requests.data if r.get("user_id")))
    users_map = {}
    if user_ids:
        users_result = sb.table("users").select("id, email, name").in_("id", user_ids).execute()
        users_map = {u["id"]: u for u in users_result.data}

    enriched = []
    for req in requests.data:
        u = users_map.get(req.get("user_id"), {})
        enriched.append({
            **req,
            "user_email": u.get("email", ""),
            "user_name": u.get("name", ""),
        })

    return enriched


# ── Update service request status (admin only) ───────
class StatusUpdate(BaseModel):
    status: str  # "approved", "rejected", "pending"


@router.patch("/service-requests/{request_id}")
async def update_service_request(
    request_id: str,
    body: StatusUpdate,
    user: dict = Depends(require_admin),
):
    if body.status not in ("pending", "approved", "rejected"):
        raise HTTPException(400, "Status must be pending, approved, or rejected")

    sb = get_supabase()
    from datetime import datetime
    result = (
        sb.table("service_requests")
        .update({"status": body.status, "updated_at": datetime.utcnow().isoformat()})
        .eq("id", request_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(404, "Service request not found")

    return result.data[0]


# ── View specific user's chats and messages (admin only) ──
@router.get("/users/{user_id}/chats")
async def get_user_chats(user_id: str, user: dict = Depends(require_admin)):
    sb = get_supabase()
    result = (
        sb.table("chats")
        .select("id, title, created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data


@router.get("/users/{user_id}/messages")
async def get_user_messages(user_id: str, user: dict = Depends(require_admin)):
    """Get all messages across all chats for a specific user."""
    sb = get_supabase()

    # First get user's chat IDs
    chats = sb.table("chats").select("id").eq("user_id", user_id).execute()
    chat_ids = [c["id"] for c in chats.data]

    if not chat_ids:
        return []

    messages = (
        sb.table("messages")
        .select("id, chat_id, role, content, created_at, original_language, input_type")
        .in_("chat_id", chat_ids)
        .order("created_at", desc=True)
        .limit(200)
        .execute()
    )
    return messages.data
