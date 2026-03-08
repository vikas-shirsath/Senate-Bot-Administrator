"""
Auth dependency — validates Supabase JWT tokens on protected endpoints
by calling Supabase's own auth.getUser() endpoint.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client
import os

security = HTTPBearer()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Validate the access token by asking Supabase to resolve it.
    Returns a dict with {"id": "<uuid>", "email": "..."}.
    """
    token = credentials.credentials

    try:
        # Create a temporary client using the user's own token
        # so Supabase validates it server-side
        sb = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        user_resp = sb.auth.get_user(token)
        user = user_resp.user

        if not user:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")

        return {
            "id": user.id,
            "email": user.email or "",
        }
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "invalid" in error_msg.lower() or "expired" in error_msg.lower():
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Auth error: {error_msg}")
