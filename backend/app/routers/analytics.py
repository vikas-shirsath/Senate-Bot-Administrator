"""
Analytics router — admin dashboard endpoints for governance metrics.
Uses Supabase service key to bypass RLS and query across all users.
"""

from fastapi import APIRouter, Depends
from app.auth import get_current_user
from app.supabase_client import get_supabase

router = APIRouter()


@router.get("/overview")
async def analytics_overview(user: dict = Depends(get_current_user)):
    """High-level stats: total users, chats, messages, service requests."""
    sb = get_supabase()

    users = sb.table("users").select("id", count="exact").execute()
    chats_data = sb.table("chats").select("id", count="exact").execute()
    messages = sb.table("messages").select("id", count="exact").execute()
    requests = sb.table("service_requests").select("id", count="exact").execute()

    return {
        "total_users": users.count or 0,
        "total_chats": chats_data.count or 0,
        "total_messages": messages.count or 0,
        "total_service_requests": requests.count or 0,
    }


@router.get("/top-queries")
async def top_queries(user: dict = Depends(get_current_user)):
    """Most common user queries — grouped by content keywords."""
    sb = get_supabase()

    # Get recent user messages
    result = (
        sb.table("messages")
        .select("content, original_language")
        .eq("role", "user")
        .order("created_at", desc=True)
        .limit(500)
        .execute()
    )

    # Categorize by intent keywords
    intent_keywords = {
        "Ration Card Status": ["ration", "राशन", "रेशन", "ration card", "ration status"],
        "Birth Certificate": ["birth", "जन्म", "certificate", "प्रमाणपत्र", "BC"],
        "Grievance Registration": ["grievance", "complaint", "तक्रार", "शिकायत", "grievance"],
        "Location Lookup": ["pincode", "pin code", "location", "पिनकोड", "स्थान"],
        "Housing Scheme": ["housing", "house", "आवास", "गृहनिर्माण", "home"],
        "Apply for Service": ["apply", "application", "अर्ज", "आवेदन"],
        "Eligibility Check": ["eligible", "eligibility", "पात्र", "योग्यता"],
        "Scheme Information": ["scheme", "yojana", "योजना", "plan"],
    }

    counts = {intent: 0 for intent in intent_keywords}
    other_count = 0

    for msg in result.data:
        content = (msg.get("content") or "").lower()
        matched = False
        for intent, keywords in intent_keywords.items():
            if any(kw.lower() in content for kw in keywords):
                counts[intent] += 1
                matched = True
                break
        if not matched:
            other_count += 1

    # Sort by count descending, filter out zeros
    queries = [
        {"intent": intent, "count": count}
        for intent, count in sorted(counts.items(), key=lambda x: x[1], reverse=True)
        if count > 0
    ]
    if other_count > 0:
        queries.append({"intent": "Other Queries", "count": other_count})

    return queries


@router.get("/bottlenecks")
async def bottlenecks(user: dict = Depends(get_current_user)):
    """Identify services with pending requests and average processing time."""
    sb = get_supabase()

    result = (
        sb.table("service_requests")
        .select("service_type, status, created_at, updated_at")
        .execute()
    )

    from collections import defaultdict
    from datetime import datetime

    service_stats = defaultdict(lambda: {
        "total": 0, "pending": 0, "approved": 0, "rejected": 0,
        "processing_times": [],
    })

    for req in result.data:
        stype = req.get("service_type", "unknown")
        status = req.get("status", "pending").lower()
        service_stats[stype]["total"] += 1

        if status == "pending":
            service_stats[stype]["pending"] += 1
        elif status == "approved":
            service_stats[stype]["approved"] += 1
        elif status == "rejected":
            service_stats[stype]["rejected"] += 1

        # Calculate processing time for completed requests
        if status in ("approved", "rejected") and req.get("updated_at") and req.get("created_at"):
            try:
                created = datetime.fromisoformat(req["created_at"].replace("Z", "+00:00"))
                updated = datetime.fromisoformat(req["updated_at"].replace("Z", "+00:00"))
                diff_hours = (updated - created).total_seconds() / 3600
                service_stats[stype]["processing_times"].append(diff_hours)
            except Exception:
                pass

    bottleneck_data = []
    for stype, stats in service_stats.items():
        avg_hours = 0
        if stats["processing_times"]:
            avg_hours = sum(stats["processing_times"]) / len(stats["processing_times"])

        # Format avg time
        if avg_hours < 1:
            avg_time = f"{int(avg_hours * 60)} min"
        elif avg_hours < 24:
            avg_time = f"{avg_hours:.1f} hrs"
        else:
            avg_time = f"{avg_hours / 24:.1f} days"

        bottleneck_data.append({
            "service": stype,
            "total": stats["total"],
            "pending": stats["pending"],
            "approved": stats["approved"],
            "rejected": stats["rejected"],
            "avg_processing_time": avg_time,
        })

    return sorted(bottleneck_data, key=lambda x: x["pending"], reverse=True)


@router.get("/completion-rate")
async def completion_rate(user: dict = Depends(get_current_user)):
    """Completion percentage per service type."""
    sb = get_supabase()

    result = (
        sb.table("service_requests")
        .select("service_type, status")
        .execute()
    )

    from collections import defaultdict
    service_counts = defaultdict(lambda: {"total": 0, "completed": 0})

    for req in result.data:
        stype = req.get("service_type", "unknown")
        status = req.get("status", "pending").lower()
        service_counts[stype]["total"] += 1
        if status == "approved":
            service_counts[stype]["completed"] += 1

    rates = []
    for stype, counts in service_counts.items():
        rate = round((counts["completed"] / counts["total"]) * 100) if counts["total"] > 0 else 0
        rates.append({
            "service": stype,
            "total": counts["total"],
            "completed": counts["completed"],
            "completion_rate": rate,
        })

    return sorted(rates, key=lambda x: x["total"], reverse=True)


@router.get("/language-stats")
async def language_stats(user: dict = Depends(get_current_user)):
    """Usage breakdown by language."""
    sb = get_supabase()

    result = (
        sb.table("messages")
        .select("original_language")
        .eq("role", "user")
        .execute()
    )

    from collections import Counter
    lang_map = {"en": "English", "hi": "Hindi", "mr": "Marathi"}
    langs = Counter()
    for msg in result.data:
        lang = msg.get("original_language") or "en"
        langs[lang_map.get(lang, lang)] += 1

    return [{"language": lang, "count": count} for lang, count in langs.most_common()]


@router.get("/usage-timeline")
async def usage_timeline(user: dict = Depends(get_current_user)):
    """Message count per day for the last 30 days."""
    sb = get_supabase()

    from datetime import datetime, timedelta
    cutoff = (datetime.utcnow() - timedelta(days=30)).isoformat()

    result = (
        sb.table("messages")
        .select("created_at")
        .eq("role", "user")
        .gte("created_at", cutoff)
        .order("created_at", desc=False)
        .execute()
    )

    from collections import Counter
    daily = Counter()
    for msg in result.data:
        day = msg.get("created_at", "")[:10]  # YYYY-MM-DD
        if day:
            daily[day] += 1

    return [{"date": day, "messages": count} for day, count in sorted(daily.items())]
