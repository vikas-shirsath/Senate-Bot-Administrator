"""
Service Router — maps detected intents/actions from the LLM to concrete
API calls on the backend, then formats the result for the chatbot.
"""

import random
import httpx
from app.supabase_client import get_supabase

# Base URL for internal API calls (self-referencing the FastAPI app)
_BASE = "http://localhost:8000"

# Prefix map for request IDs
_SERVICE_PREFIXES = {
    "ration_card": "RC",
    "birth_certificate": "BC",
    "grievance": "GR",
    "housing": "HS",
}

# Scheme information for active ration card holders
_RATION_SCHEMES = """
**Available Government Schemes for Ration Card Holders:**

1. **National Food Security Act (NFSA)**
   → Entitlement: 5 kg food grains per person per month at ₹1-3/kg
   → Steps: Visit nearest PDS shop → Show ration card → Collect allotted grains → Sign register

2. **Pradhan Mantri Garib Kalyan Anna Yojana (PMGKAY)**
   → Entitlement: Additional 5 kg free food grains per person per month
   → Steps: Already linked to ration card → Visit Fair Price Shop → Collect free grains

3. **One Nation One Ration Card (ONORC)**
   → Benefit: Use ration card in any state across India
   → Steps: Link Aadhaar with ration card → Visit any PDS shop → Authenticate via biometric

4. **Annapurna Scheme** (for senior citizens 65+)
   → Entitlement: 10 kg free food grains per month
   → Steps: Apply at Block Development Office → Submit age proof → Approval → Monthly collection
"""


async def execute_action(action: str, entities: dict) -> dict:
    """
    Given an action name and extracted entities, call the appropriate
    service endpoint and return a structured result.
    """
    handler = _ACTION_MAP.get(action)
    if handler is None:
        return {
            "success": False,
            "message": f"Unknown action '{action}'. I can help with ration card status, birth certificate status, location lookup, grievance registration, service applications, and request status tracking.",
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

    summary = (
        f"**Ration Card:** {data['ration_id']}\n"
        f"**Holder:** {data['holder_name']}\n"
        f"**Status:** {data['status']}\n"
        f"**Card Type:** {data['card_type']}\n"
        f"**Entitlement:** {data['entitlement']}\n"
        f"**Scheme:** {data['scheme']}\n"
        f"**Family Members:** {data['family_members']}\n\n"
        f"📜 **Policy Reference:**\n{data['policy_reference']}"
    )

    # If the card is Active, append scheme information
    if data.get("status", "").lower() == "active":
        summary += f"\n\n{'─' * 40}\n{_RATION_SCHEMES}"

    return {
        "success": True,
        "service": "Ration Card Status",
        "data": data,
        "summary": summary,
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

    summary = (
        f"**Certificate ID:** {data['certificate_id']}\n"
        f"**Name:** {data['name']}\n"
        f"**Status:** {data['status']}\n"
        f"**Issue Date:** {issue}\n\n"
        f"📜 **Policy Reference:**\n{data['policy_reference']}"
    )

    # If issued, suggest services the certificate enables
    if data.get("status", "").lower() == "issued":
        summary += (
            "\n\n**Services enabled with this Birth Certificate:**\n"
            "1. **School Admission** → Present certificate at school → Complete admission form\n"
            "2. **Passport Application** → Visit passportindia.gov.in → Upload certificate → Submit at PSK\n"
            "3. **Aadhaar Enrollment** → Visit enrollment center → Submit certificate → Biometric capture\n"
            "4. **Caste Certificate** → Apply at Tehsildar office → Submit birth certificate + proof"
        )

    return {
        "success": True,
        "service": "Birth Certificate Status",
        "data": data,
        "summary": summary,
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
    """Rule-based eligibility checker for common government schemes."""
    income = entities.get("income", 0)
    age = entities.get("age", 0)
    category = entities.get("category", "General")

    eligible_schemes = []

    if income and int(income) <= 300000:
        eligible_schemes.append(
            "**Pradhan Mantri Awas Yojana (PMAY):** Eligible for housing subsidy up to ₹2.67 lakh.\n"
            "   → Steps: Visit pmay-urban.gov.in → Register → Upload documents → Track application\n"
            "   (Reference: PMAY Guidelines 2015, Section 4)"
        )
    if income and int(income) <= 250000:
        eligible_schemes.append(
            "**National Food Security Act:** Eligible for subsidized food grains.\n"
            "   → Steps: Apply at Tehsildar office → Submit income proof → Receive ration card\n"
            "   (Reference: NFSA 2013, Section 3)"
        )
    if category in ("SC", "ST") and age and int(age) <= 25:
        eligible_schemes.append(
            "**Post-Matric Scholarship for SC/ST Students:** Eligible for educational scholarship.\n"
            "   → Steps: Register at scholarships.gov.in → Upload documents → Apply online\n"
            "   (Reference: Ministry of Social Justice)"
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

    schemes_text = "\n\n".join(f"- {s}" for s in eligible_schemes)
    return {
        "success": True,
        "service": "Eligibility Check",
        "data": entities,
        "summary": f"Based on your details, you may be eligible for:\n\n{schemes_text}",
    }


# ── Service Request Application ─────────────────────────

async def _apply_service(entities: dict) -> dict:
    """
    Submit a service application. Collects applicant details,
    generates a unique request ID, and stores everything in Supabase.
    """
    service_type = entities.get("service_type", "")
    user_id = entities.get("_user_id", "")
    applicant_details = entities.get("applicant_details", {})

    if not service_type:
        return {
            "success": False,
            "message": "Please specify the service type you want to apply for (e.g., ration_card, birth_certificate, grievance, housing).",
        }

    # Validate required fields per service type
    required_fields = {
        "ration_card": ["name", "district", "state", "family_members"],
        "birth_certificate": ["name", "date_of_birth", "father_name", "mother_name", "district", "state"],
        "housing": ["name", "district", "state", "income"],
        "grievance": ["name", "description"],
    }

    needed = required_fields.get(service_type, ["name"])
    missing = [f for f in needed if not applicant_details.get(f)]

    if missing:
        friendly = ", ".join(f.replace("_", " ").title() for f in missing)
        return {
            "success": False,
            "message": f"To complete your **{service_type.replace('_', ' ').title()}** application, I still need: **{friendly}**. Please provide these details.",
        }

    prefix = _SERVICE_PREFIXES.get(service_type, "SR")
    request_id = f"{prefix}-{random.randint(10000, 99999)}"

    if user_id:
        try:
            sb = get_supabase()
            sb.table("service_requests").insert({
                "user_id": user_id,
                "service_type": service_type,
                "request_id": request_id,
                "status": "pending",
                "applicant_details": applicant_details,
                "attached_file_urls": entities.get("attached_files", []),
            }).execute()
        except Exception as e:
            print(f"Error saving service request: {e}")
            pass  # Gracefully continue even if DB save fails

    friendly_name = service_type.replace("_", " ").title()
    details_summary = "\n".join(
        f"  • **{k.replace('_', ' ').title()}:** {v}"
        for k, v in applicant_details.items()
        if v
    )

    return {
        "success": True,
        "service": "Service Application",
        "data": {"request_id": request_id, "service_type": service_type, "status": "pending"},
        "summary": (
            f"✅ Your **{friendly_name}** application has been submitted!\n\n"
            f"**Request ID:** {request_id}\n"
            f"**Status:** Pending\n\n"
            f"**Application Details:**\n{details_summary}\n\n"
            f"You can check the status anytime by saying:\n"
            f"*\"Check status of {request_id}\"*"
        ),
    }


# ── Check Service Request Status ────────────────────────

async def _check_request_status(entities: dict) -> dict:
    """Query the service_requests table by request_id."""
    request_id = entities.get("request_id", "")
    if not request_id:
        return {
            "success": False,
            "message": "Please provide a request ID (e.g., RC-10021).",
        }

    try:
        sb = get_supabase()
        result = (
            sb.table("service_requests")
            .select("*")
            .eq("request_id", request_id.upper())
            .execute()
        )
        if result.data:
            rec = result.data[0]
            friendly = rec["service_type"].replace("_", " ").title()
            status_emoji = "✅" if rec["status"] == "approved" else "⏳" if rec["status"] == "pending" else "📋"
            status_msg = {
                "pending": "Your request is currently under review.",
                "approved": "Your request has been approved!",
                "rejected": "Your request was unfortunately rejected.",
                "processing": "Your request is being processed.",
            }.get(rec["status"], f"Current status: {rec['status']}")

            # Include applicant details if available
            details = rec.get("applicant_details", {})
            detail_lines = ""
            if details:
                detail_lines = "\n\n**Application Details:**\n" + "\n".join(
                    f"  • **{k.replace('_', ' ').title()}:** {v}"
                    for k, v in details.items()
                    if v
                )

            return {
                "success": True,
                "service": "Request Status",
                "data": rec,
                "summary": (
                    f"{status_emoji} **{friendly} — {rec['request_id']}**\n\n"
                    f"**Status:** {rec['status'].title()}\n"
                    f"{status_msg}{detail_lines}\n\n"
                    f"**Submitted:** {rec['created_at']}"
                ),
            }
    except Exception:
        pass

    return {
        "success": False,
        "message": f"No service request found with ID **{request_id}**. Please double-check the request ID.",
    }


# ── Certificate Application Handlers ────────────────────

async def _apply_permit_certificate(entities: dict) -> dict:
    """Generate a Permit Certificate directly."""
    from app.services.certificate_generator import (
        generate_permit_pdf, generate_permit_number,
        generate_issue_number, calculate_expiry_date,
    )
    import uuid

    required = ["owner", "business", "address", "activity", "start_date", "city", "issued_date"]
    missing = [f for f in required if not entities.get(f)]
    if missing:
        friendly = ", ".join(f.replace("_", " ").title() for f in missing)
        return {"success": False, "message": f"I still need: **{friendly}** to generate your Permit Certificate."}

    user_id = entities.get("_user_id", "")
    sb = get_supabase()

    # Get next sequential ID
    count_result = sb.table("permit_certificates").select("id", count="exact").execute()
    seq_id = (count_result.count or 0) + 1

    permit_number = generate_permit_number(seq_id)
    issue_number = generate_issue_number(seq_id)
    expiry_date = calculate_expiry_date(entities["start_date"])
    authority = "Government of Maharashtra"

    cert_data = {
        "issue_number": issue_number,
        "permit_number": permit_number,
        "owner": entities["owner"],
        "business": entities["business"],
        "address": entities["address"],
        "activity": entities["activity"],
        "authority": authority,
        "start_date": entities["start_date"],
        "expiry_date": expiry_date,
        "city": entities["city"],
        "issued_date": entities["issued_date"],
    }

    try:
        pdf_bytes = generate_permit_pdf(cert_data)
        print(f"[Permit Cert] PDF generated: {len(pdf_bytes)} bytes")
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "message": f"PDF generation failed: {str(e)}"}

    if not pdf_bytes or len(pdf_bytes) < 100:
        return {"success": False, "message": "PDF generation produced empty output. Check wkhtmltopdf installation."}

    # Upload PDF
    pdf_filename = f"permit_{permit_number.replace('-', '_')}.pdf"
    try:
        print(f"[Permit Cert] Uploading to certificates/{pdf_filename}")
        sb.storage.from_("certificates").upload(
            pdf_filename, pdf_bytes,
            file_options={"content-type": "application/pdf"}
        )
        print(f"[Permit Cert] Upload successful")
    except Exception as e:
        print(f"[Permit Cert] First upload failed: {e}, trying fallback name")
        try:
            pdf_filename = f"permit_{uuid.uuid4().hex[:8]}.pdf"
            sb.storage.from_("certificates").upload(
                pdf_filename, pdf_bytes,
                file_options={"content-type": "application/pdf"}
            )
            print(f"[Permit Cert] Fallback upload successful: {pdf_filename}")
        except Exception as e2:
            import traceback
            traceback.print_exc()
            return {"success": False, "message": f"Failed to upload certificate to storage: {str(e2)}. Make sure the 'certificates' storage bucket exists in Supabase and is set to public."}

    certificate_url = sb.storage.from_("certificates").get_public_url(pdf_filename)
    print(f"[Permit Cert] Public URL: {certificate_url}")

    # Save to DB
    try:
        sb.table("permit_certificates").insert({
            "user_id": user_id,
            "issue_number": issue_number,
            "permit_number": permit_number,
            "owner": entities["owner"],
            "business": entities["business"],
            "address": entities["address"],
            "activity": entities["activity"],
            "authority": authority,
            "start_date": entities["start_date"],
            "expiry_date": expiry_date,
            "city": entities["city"],
            "issued_date": entities["issued_date"],
            "aadhaar_document_url": entities.get("aadhaar_document_url", ""),
            "pan_document_url": entities.get("pan_document_url", ""),
            "certificate_url": certificate_url,
        }).execute()
        print(f"[Permit Cert] DB record saved")
    except Exception as e:
        print(f"[Permit Cert] DB save error (continuing): {e}")

    return {
        "success": True,
        "service": "Permit Certificate",
        "data": {"permit_number": permit_number, "issue_number": issue_number,
                 "expiry_date": expiry_date, "certificate_url": certificate_url},
        "summary": (
            f"✅ Your **Permit Certificate** has been generated successfully!\n\n"
            f"**Permit Number:** {permit_number}\n"
            f"**Issue Number:** {issue_number}\n"
            f"**Valid Until:** {expiry_date}\n\n"
            f"📥 **Download:** {certificate_url}"
        ),
    }


async def _apply_income_certificate(entities: dict) -> dict:
    """Generate an Income Certificate directly."""
    from app.services.certificate_generator import (
        generate_income_pdf, generate_income_cert_number,
    )
    import uuid

    required = ["name", "village", "taluka", "district", "financial_year",
                 "annual_income", "income_words", "place", "date"]
    missing = [f for f in required if not entities.get(f)]
    if missing:
        friendly = ", ".join(f.replace("_", " ").title() for f in missing)
        return {"success": False, "message": f"I still need: **{friendly}** to generate your Income Certificate."}

    user_id = entities.get("_user_id", "")
    sb = get_supabase()

    try:
        count_result = sb.table("income_certificates").select("id", count="exact").execute()
        seq_id = (count_result.count or 0) + 1
    except Exception as e:
        print(f"[Income Cert] DB count error: {e}")
        seq_id = 1

    certificate_number = generate_income_cert_number(seq_id)
    print(f"[Income Cert] Generating certificate: {certificate_number}")

    cert_data = {
        "certificate_number": certificate_number,
        "name": entities["name"],
        "village": entities["village"],
        "taluka": entities["taluka"],
        "district": entities["district"],
        "financial_year": entities["financial_year"],
        "annual_income": entities["annual_income"],
        "income_words": entities["income_words"],
        "place": entities["place"],
        "date": entities["date"],
    }

    # Generate PDF
    try:
        pdf_bytes = generate_income_pdf(cert_data)
        print(f"[Income Cert] PDF generated: {len(pdf_bytes)} bytes")
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "message": f"PDF generation failed: {str(e)}"}

    if not pdf_bytes or len(pdf_bytes) < 100:
        return {"success": False, "message": "PDF generation produced empty output. Check wkhtmltopdf installation."}

    # Upload PDF to Supabase Storage
    pdf_filename = f"income_{certificate_number.replace('-', '_')}.pdf"
    try:
        print(f"[Income Cert] Uploading to certificates/{pdf_filename}")
        sb.storage.from_("certificates").upload(
            pdf_filename, pdf_bytes,
            file_options={"content-type": "application/pdf"}
        )
        print(f"[Income Cert] Upload successful")
    except Exception as e:
        print(f"[Income Cert] First upload failed: {e}, trying fallback name")
        try:
            pdf_filename = f"income_{uuid.uuid4().hex[:8]}.pdf"
            sb.storage.from_("certificates").upload(
                pdf_filename, pdf_bytes,
                file_options={"content-type": "application/pdf"}
            )
            print(f"[Income Cert] Fallback upload successful: {pdf_filename}")
        except Exception as e2:
            import traceback
            traceback.print_exc()
            return {"success": False, "message": f"Failed to upload certificate to storage: {str(e2)}. Make sure the 'certificates' storage bucket exists in Supabase and is set to public."}

    certificate_url = sb.storage.from_("certificates").get_public_url(pdf_filename)
    print(f"[Income Cert] Public URL: {certificate_url}")

    # Save to DB
    try:
        sb.table("income_certificates").insert({
            "user_id": user_id,
            "certificate_number": certificate_number,
            "name": entities["name"],
            "village": entities["village"],
            "taluka": entities["taluka"],
            "district": entities["district"],
            "financial_year": entities["financial_year"],
            "annual_income": entities["annual_income"],
            "income_words": entities["income_words"],
            "place": entities["place"],
            "date": entities["date"],
            "aadhaar_document_url": entities.get("aadhaar_document_url", ""),
            "pan_document_url": entities.get("pan_document_url", ""),
            "certificate_url": certificate_url,
        }).execute()
        print(f"[Income Cert] DB record saved")
    except Exception as e:
        print(f"[Income Cert] DB save error (continuing): {e}")

    return {
        "success": True,
        "service": "Income Certificate",
        "data": {"certificate_number": certificate_number, "certificate_url": certificate_url},
        "summary": (
            f"✅ Your **Income Certificate** has been generated successfully!\n\n"
            f"**Certificate Number:** {certificate_number}\n\n"
            f"📥 **Download:** {certificate_url}"
        ),
    }


# ── Action map ───────────────────────────────────────────
_ACTION_MAP = {
    "check_ration": _check_ration,
    "check_birth": _check_birth,
    "check_location": _check_location,
    "register_grievance": _register_grievance,
    "check_eligibility": _check_eligibility,
    "apply_service": _apply_service,
    "check_request_status": _check_request_status,
    "apply_permit_certificate": _apply_permit_certificate,
    "apply_income_certificate": _apply_income_certificate,
}
