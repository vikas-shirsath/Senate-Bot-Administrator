"""
Senate Bot Administrator — FastAPI Backend
"""

from dotenv import load_dotenv
load_dotenv()  # Load .env before anything else

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import chat, location, ration, birth, grievance, chats, auth_router, service_requests, analytics, admin

app = FastAPI(
    title="Senate Bot Administrator",
    description="Autonomous Digital Governance ChatOps Platform",
    version="2.0.0",
)

# CORS — allow the React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────
app.include_router(auth_router.router, prefix="/auth", tags=["Auth"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(chats.router, prefix="/chats", tags=["Chats"])
app.include_router(location.router, prefix="/api", tags=["Location"])
app.include_router(ration.router, prefix="/api", tags=["Ration"])
app.include_router(birth.router, prefix="/api", tags=["Birth Certificate"])
app.include_router(grievance.router, prefix="/api", tags=["Grievance"])
app.include_router(service_requests.router, prefix="/service-requests", tags=["Service Requests"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])


@app.get("/")
async def root():
    return {"message": "Senate Bot Administrator API is running"}
