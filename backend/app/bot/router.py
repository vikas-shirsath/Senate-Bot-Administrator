"""
Service Router — maps detected intents/actions from the LLM to concrete
API calls on the backend, then formats the result for the chatbot.
"""

import httpx

# Base URL for internal API calls (self-referencing the FastAPI app)
_BASE = "http://localhost:8000"


async def execute_action(action: str, entities: dict) -> dict:
    """
    Given an action name and extracted entities, call the appropriate
    service endpoint and return a structured result.
    """
    handler = _ACTION_MAP.get(action)
    if handler is None:
        return {
            "success": False,
            "message": f"Unknown action '{action}'. I can help with ration card status, birth certificate status, location lookup, and grievance registration.",
        }
    return await handler(entities)


# ── Individual action handlers ───────────────────────────

async def _check_ration(entities: dict) -> dict:
    ration_id = entities.get("ration_id", "")
    if not ration_id:
        return {"success": False, "message": "Please provide a ration card ID (e.g. MH123456)."}
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{_BASE}/api/ration/{ration_id}")
    data = resp.json()
    if data.get("status") == "Not Found":
        return {"success": False, "message": f"No ration card found for ID {ration_id}. Please double-check the number."}
    return {
        "success": True,
        "service": "Ration Card Status",
        "data": data,
        "summary": (
            f"**Ration Card:** {data['ration_id']}\n"
            f"**Holder:** {data['holder_name']}\n"
            f"**Status:** {data['status']}\n"
            f"**Card Type:** {data['card_type']}\n"
            f"**Entitlement:** {data['entitlement']}\n"
            f"**Scheme:** {data['scheme']}\n"
            f"**Family Members:** {data['family_members']}\n\n"
            f"📜 **Policy Reference:**\n{data['policy_reference']}"
        ),
    }


async def _check_birth(entities: dict) -> dict:
    cert_id = entities.get("certificate_id", "")
    if not cert_id:
        return {"success": False, "message": "Please provide a birth certificate ID (e.g. BC1021)."}
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{_BASE}/api/birth/{cert_id}")
    data = resp.json()
    if data.get("status") == "Not Found":
        return {"success": False, "message": f"No birth certificate found for ID {cert_id}."}
    issue = data.get("issue_date") or "Pending"
    return {
        "success": True,
        "service": "Birth Certificate Status",
        "data": data,
        "summary": (
            f"**Certificate ID:** {data['certificate_id']}\n"
            f"**Name:** {data['name']}\n"
            f"**Status:** {data['status']}\n"
            f"**Issue Date:** {issue}\n\n"
            f"📜 **Policy Reference:**\n{data['policy_reference']}"
        ),
    }


async def _check_location(entities: dict) -> dict:
    pin = entities.get("pin", "")
    if not pin:
        return {"success": False, "message": "Please provide a 6-digit PIN code."}
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{_BASE}/api/location/{pin}")
    if resp.status_code != 200:
        return {"success": False, "message": f"Could not find location data for PIN {pin}."}
    data = resp.json()
    offices = ", ".join(po["name"] for po in data.get("post_offices", [])[:5])
    return {
        "success": True,
        "service": "Location Lookup",
        "data": data,
        "summary": (
            f"📍 **PIN Code:** {data['pin']}\n"
            f"**District:** {data['district']}\n"
            f"**State:** {data['state']}\n"
            f"**Post Offices:** {offices}"
        ),
    }


async def _register_grievance(entities: dict) -> dict:
    name = entities.get("name", "")
    description = entities.get("description", "")
    if not name or not description:
        return {
            "success": False,
            "message": "To register a grievance I need your **name** and a **description** of the issue.",
        }
    payload = {
        "name": name,
        "description": description,
        "category": entities.get("category", "General"),
        "pin": entities.get("pin", ""),
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(f"{_BASE}/api/grievance", json=payload)
    data = resp.json()
    return {
        "success": True,
        "service": "Grievance Registration",
        "data": data,
        "summary": (
            f"✅ Your grievance has been registered!\n\n"
            f"**Ticket ID:** {data['ticket_id']}\n"
            f"**Status:** {data['status']}\n"
            f"**Estimated Resolution:** {data['estimated_resolution']}\n\n"
            f"📜 **Policy Reference:**\n{data['policy_reference']}"
        ),
    }


async def _check_eligibility(entities: dict) -> dict:
    """
    Rule-based eligibility checker for common government housing schemes.
    """
    income = entities.get("income", 0)
    age = entities.get("age", 0)
    category = entities.get("category", "General")
    family_size = entities.get("family_size", 1)

    eligible_schemes = []

    # PMAY – Pradhan Mantri Awas Yojana
    if income and int(income) <= 300000:
        eligible_schemes.append(
            "**Pradhan Mantri Awas Yojana (PMAY):** Eligible for housing subsidy up to ₹2.67 lakh. "
            "(Reference: PMAY Guidelines 2015, Section 4)"
        )
    # NFSA
    if income and int(income) <= 250000:
        eligible_schemes.append(
            "**National Food Security Act:** Eligible for subsidized food grains. "
            "(Reference: NFSA 2013, Section 3)"
        )
    # SC/ST scholarship
    if category in ("SC", "ST") and age and int(age) <= 25:
        eligible_schemes.append(
            "**Post-Matric Scholarship for SC/ST Students:** Eligible for educational scholarship. "
            "(Reference: Ministry of Social Justice)"
        )

    if not eligible_schemes:
        return {
            "success": True,
            "service": "Eligibility Check",
            "data": entities,
            "summary": (
                "Based on the information provided, you may not be eligible for the schemes I currently check. "
                "I recommend visiting your nearest Common Service Center (CSC) for a comprehensive eligibility assessment."
            ),
        }

    schemes_text = "\n".join(f"- {s}" for s in eligible_schemes)
    return {
        "success": True,
        "service": "Eligibility Check",
        "data": entities,
        "summary": f"Based on your details, you may be eligible for:\n\n{schemes_text}",
    }


# ── Action map ───────────────────────────────────────────
_ACTION_MAP = {
    "check_ration": _check_ration,
    "check_birth": _check_birth,
    "check_location": _check_location,
    "register_grievance": _register_grievance,
    "check_eligibility": _check_eligibility,
}
