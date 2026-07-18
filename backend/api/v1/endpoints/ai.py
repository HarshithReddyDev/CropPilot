import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_current_user, get_db
from models.user import User
from schemas.ai import ChatRequest, IntelRequest, RAGStreamRequest
from services.rag_chat import rag_chat_service

router = APIRouter(prefix="/intel", tags=["AI Assistant"])


@router.post("/chat")
async def chat(
    request: ChatRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    if request.stream:
        return StreamingResponse(
            rag_chat_service.stream_chat(db, current_user, request),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    result = await rag_chat_service.chat(db, current_user, request)
    return result


@router.post("/rag-stream")
async def rag_stream(
    request: RAGStreamRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return StreamingResponse(
        rag_chat_service.stream_rag(db, current_user, request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/rag-stream/{incident_id}")
async def intel_engine(
    request: IntelRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return StreamingResponse(
        rag_chat_service.stream_intel(db, current_user, request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
