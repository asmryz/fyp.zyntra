"""
ZYNTRA FastAPI application.

Run from the backend folder:
    uvicorn app.main:app --reload
"""
import logging

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DataError, IntegrityError

from app.config import settings
from app.constants import MAX_REQUEST_BYTES
from app.routers import (
    admin_content, admin_roadmaps, admin_test_prep, admin_users, auth, content, integrations, invitations, public,
    student,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("zyntra.api")

app = FastAPI(
    title="ZYNTRA API",
    description="Backend for ZYNTRA, the AI-powered admission assistance system for SZABIST.",
    version="1.0.0",
)


# ---------- Request size limit ----------

class RequestTooLarge(Exception):
    pass


TOO_LARGE_BODY = (
    b'{"detail":"The submitted data is too large. Please shorten the text and try again."}'
)


class BodySizeLimitMiddleware:
    """
    Refuses request bodies larger than MAX_REQUEST_BYTES (413) before they are
    read into memory: by the Content-Length header, and also while streaming
    for requests that do not send one.
    """

    def __init__(self, app, max_bytes: int):
        self.app = app
        self.max_bytes = max_bytes

    async def _reject(self, send):
        await send({"type": "http.response.start", "status": 413,
                    "headers": [(b"content-type", b"application/json")]})
        await send({"type": "http.response.body", "body": TOO_LARGE_BODY})

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        length = dict(scope.get("headers") or []).get(b"content-length")
        if length is not None and length.isdigit() and int(length) > self.max_bytes:
            await self._reject(send)
            return

        received = 0
        started = False

        async def limited_receive():
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_bytes:
                    raise RequestTooLarge()
            return message

        async def tracking_send(message):
            nonlocal started
            if message["type"] == "http.response.start":
                started = True
            await send(message)

        try:
            await self.app(scope, limited_receive, tracking_send)
        except RequestTooLarge:
            if not started:
                await self._reject(send)


app.add_middleware(BodySizeLimitMiddleware, max_bytes=MAX_REQUEST_BYTES)


# ---------- Database errors: clear messages instead of "Internal Server Error" ----------

@app.exception_handler(DataError)
async def database_value_error(request: Request, error: DataError):
    # e.g. a number beyond the range of its column. The details stay in the server log only.
    logger.warning("Rejected out-of-range value on %s %s: %s", request.method, request.url.path, type(error.orig).__name__)
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                        content={"detail": "One of the values is outside the allowed range. Please check your input."})


@app.exception_handler(IntegrityError)
async def database_integrity_error(request: Request, error: IntegrityError):
    # A database constraint caught something the API checks missed (e.g. a duplicate entry)
    constraint = getattr(getattr(error.orig, "diag", None), "constraint_name", None)
    logger.warning("Constraint %s refused a change on %s %s", constraint, request.method, request.url.path)
    return JSONResponse(status_code=status.HTTP_409_CONFLICT,
                        content={"detail": "This change conflicts with existing data or breaks a data rule. "
                                           "Please check the values and try again."})


# ---------- Security headers on every API response ----------

@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    if request.url.path.startswith("/api/auth/") or request.url.path.startswith("/api/invitations/"):
        # Tokens and personal details must not be stored by browsers or proxies
        response.headers.setdefault("Cache-Control", "no-store")
    return response

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
