"""api/routes/chat.py — AI chat endpoint."""

import uuid
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_db, get_current_user
from database.models.models import User
from schemas.schemas import ChatRequest, ChatResponse
from services.chat_service import ChatService
from core.logging import logger

router = APIRouter()

@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    session_id = request.session_id or str(uuid.uuid4())
    logger.info("Chat request", user_id=current_user.id, session_id=session_id)
    result = await ChatService(db).process_message(
        user_id=current_user.id, session_id=session_id,
        message=request.message, context=request.context or {},
    )
    return ChatResponse(session_id=session_id, message=result["response"],
                        agent_steps=result.get("steps"), tools_used=result.get("tools_used"),
                        timestamp=datetime.utcnow())

@router.get("/sessions")
async def list_sessions(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from database.repositories.chat_repository import ChatRepository
    sessions = await ChatRepository(db).get_user_sessions(current_user.id)
    return {"sessions": list(sessions)}

@router.get("/sessions/{session_id}")
async def get_session_history(session_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from database.repositories.chat_repository import ChatRepository
    messages = await ChatRepository(db).get_session_history(current_user.id, session_id)
    return {"session_id": session_id, "messages": [
        {"role": m.role, "content": m.content, "timestamp": m.created_at.isoformat()} for m in messages
    ]}

@router.delete("/sessions/{session_id}", status_code=204)
async def clear_session(session_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from database.repositories.chat_repository import ChatRepository
    await ChatRepository(db).clear_session(current_user.id, session_id)
