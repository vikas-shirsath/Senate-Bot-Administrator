"""
Auth router — handles user upsert after Supabase Auth login.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth import get_current_user
from app.supabase_client import get_supabase

router = APIRouter()


class UserProfile(BaseModel):
    name: str = ""


@router.post("/callback")
async def auth_callback(
    profile: UserProfile,
    user: dict = Depends(get_current_user),
):
    """
    Called by the frontend after a successful Supabase Auth login.
    Upserts the user record into the `users` table.
    """
    sb = get_supabase()
    sb.table("users").upsert(
        {
            "id": user["id"],
            "email": user["email"],
            "name": profile.name or user["email"].split("@")[0],
        },
        on_conflict="id",
    ).execute()

    return {"status": "ok", "user_id": user["id"], "email": user["email"]}


@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    """Return the current user's profile from the database."""
    sb = get_supabase()
    result = sb.table("users").select("*").eq("id", user["id"]).single().execute()
    return result.data
