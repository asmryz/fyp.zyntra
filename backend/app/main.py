"""
ZYNTRA FastAPI application.

Run from the backend folder:
    uvicorn app.main:app --reload
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import (
    admin_content, admin_roadmaps, admin_test_prep, admin_users, auth, content, integrations, invitations, public,
    student,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

app = FastAPI(
    title="ZYNTRA API",
    description="Backend for ZYNTRA, the AI-powered admission assistance system for SZABIST.",
    version="1.0.0",
)

# The React dev server proxies /api to this backend, so CORS is only needed
# when the frontend is served from a different address.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

for module in (auth, invitations, public, content, student, integrations,
               admin_users, admin_content, admin_roadmaps, admin_test_prep):
    app.include_router(module.router)


@app.get("/api/health", tags=["Health"])
def health():
    return {"status": "ok"}
