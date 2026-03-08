"""
Location router — proxies the Postal PIN Code API.
"""

import httpx
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/location/{pin}")
async def get_location(pin: str):
    """Fetch post-office / district / state info for a given PIN code."""
    url = f"https://api.postalpincode.in/pincode/{pin}"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url)

    if resp.status_code != 200:
        raise HTTPException(502, "Upstream PIN-code API unavailable")

    data = resp.json()
    if not data or data[0].get("Status") == "Error":
        raise HTTPException(404, f"No data found for PIN {pin}")

    post_offices = data[0].get("PostOffice", [])
    if not post_offices:
        raise HTTPException(404, f"No post offices found for PIN {pin}")

    first = post_offices[0]
    return {
        "pin": pin,
        "district": first.get("District", ""),
        "state": first.get("State", ""),
        "country": first.get("Country", "India"),
        "post_offices": [
            {"name": po.get("Name"), "branch_type": po.get("BranchType")}
            for po in post_offices
        ],
    }
