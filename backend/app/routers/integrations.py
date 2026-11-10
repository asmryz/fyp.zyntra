"""
Integration points for services that run outside this web application.

AI admission assistant
    The LangGraph / RAG / Ollama service is not part of this repository yet.
    When it exists, set AI_SERVICE_URL in .env. This backend will forward
    questions to POST {AI_SERVICE_URL}/ask with JSON
        {"question": "...", "student_profile": {...}}
    and expects JSON back:
        {"answer": "...", "sources": ["...", ...]}

WhatsApp assistance
    The whatsapp-web.js bot runs as its own Node.js service. The website only
    needs the bot's phone number (WHATSAPP_NUMBER) to show a chat link.
"""
import json
import logging
import urllib.error
import urllib.request

from fastapi import APIRouter, Depends, HTTPException, status

from app.config import settings
from app.core.dependencies import get_current_student
from app.models import User
from app.schemas.student import AssistantAnswer, AssistantQuestion
from app.services.student_service import build_profile_out

logger = logging.getLogger("zyntra.integrations")

router = APIRouter(prefix="/api/student", tags=["Integrations"])

NOT_CONNECTED_MESSAGE = (
    "The ZYNTRA AI admission assistant is not connected yet. "
    "Please use the published admission guidance and program information for now."
)


@router.get("/assistant/status")
def assistant_status(user: User = Depends(get_current_student)):
    if not settings.ai_service_url:
        return {"available": False, "message": NOT_CONNECTED_MESSAGE}
    return {"available": True, "message": "The AI admission assistant is connected."}


@router.post("/assistant/ask", response_model=AssistantAnswer)
def ask_assistant(data: AssistantQuestion, user: User = Depends(get_current_student)):
    if not settings.ai_service_url:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=NOT_CONNECTED_MESSAGE)

    profile = build_profile_out(user, user.profile).model_dump(exclude={"email", "missing_fields"})
    body = json.dumps({"question": data.question, "student_profile": profile}).encode("utf-8")
    request = urllib.request.Request(
        f"{settings.ai_service_url.rstrip('/')}/ask",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        logger.error("AI service request failed: %s", type(error).__name__)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY,
                            detail="The AI assistant did not respond. Please try again later.")

    return AssistantAnswer(answer=str(result.get("answer", "")), sources=list(result.get("sources", [])))


@router.get("/whatsapp")
def whatsapp_info(user: User = Depends(get_current_student)):
    number = "".join(ch for ch in settings.whatsapp_number if ch.isdigit())
    if not number:
        return {"configured": False, "number": None, "chat_url": None}
    return {"configured": True, "number": f"+{number}", "chat_url": f"https://wa.me/{number}"}
