import json
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from agents.graph import cropilot_agent
from core.config import settings
from models.user import User
from schemas.ai import ChatRequest, ChatResponse, IntelRequest, RAGStreamRequest


class RAGChatService:
    async def chat(
        self, db: AsyncSession, user: User, request: ChatRequest
    ) -> ChatResponse:
        from langchain_core.messages import HumanMessage

        config = {
            "configurable": {
                "user_id": str(user.id),
                "user_role": user.role,
                "state": user.state or "Telangana",
                "conversation_id": request.conversation_id,
            }
        }

        result = await cropilot_agent.ainvoke(
            {"messages": [HumanMessage(content=request.message)]},
            config=config,
        )

        return ChatResponse(
            message=result["messages"][-1].content,
            conversation_id=request.conversation_id or str(user.id),
            sources=result.get("sources", []),
        )

    async def stream_chat(self, db, user, request):
        from langchain_core.messages import HumanMessage

        config = {
            "configurable": {
                "user_id": str(user.id),
                "user_role": user.role,
                "state": user.state or "Telangana",
                "conversation_id": request.conversation_id,
            }
        }

        async for event in cropilot_agent.astream_events(
            {"messages": [HumanMessage(content=request.message)]},
            config=config,
            version="v1",
        ):
            kind = event.get("event")
            if kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    yield f"data: {json.dumps({'type': 'token', 'content': content})}\n\n"
            elif kind == "on_tool_start":
                yield f"data: {json.dumps({'type': 'tool_start', 'tool': event['name']})}\n\n"
            elif kind == "on_tool_end":
                yield f"data: {json.dumps({'type': 'tool_end', 'tool': event['name']})}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    async def stream_rag(self, db, user, request: RAGStreamRequest):
        from rag.pipeline import rag_pipeline

        results = await rag_pipeline.hybrid_search(
            query=request.query,
            h3_index=request.h3_index,
            top_k=request.top_k,
        )

        yield f"data: {json.dumps({'type': 'sources', 'count': len(results)})}\n\n"
        for r in results:
            yield f"data: {json.dumps({'type': 'source', 'payload': r})}\n\n"

        context = "\n\n".join([r.get("content", "") for r in results])

        from langchain_core.messages import HumanMessage, SystemMessage
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=settings.OPENAI_TEMPERATURE,
            api_key=settings.OPENAI_API_KEY,
        )

        system_prompt = SystemMessage(
            content=f"You are CropPilot AI, an agricultural assistant for farmers in {user.state or 'India'}. "
            f"Use the following context to answer the farmer's question. "
            f"Context:\n{context}\n\nProvide concise, actionable advice."
        )

        async for chunk in llm.astream([system_prompt, HumanMessage(content=request.query)]):
            if chunk.content:
                yield f"data: {json.dumps({'type': 'token', 'content': chunk.content})}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    async def stream_intel(self, db, user, request: IntelRequest):
        from agents.graph import intel_agent

        async for event in intel_agent.astream_events(
            {"incident_id": str(request.incident_id)},
            config={"configurable": {"user_id": str(user.id)}},
            version="v1",
        ):
            kind = event.get("event")
            if kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    yield f"data: {json.dumps({'type': 'token', 'content': content})}\n\n"
            elif kind == "on_tool_start":
                yield f"data: {json.dumps({'type': 'tool_start', 'tool': event['name']})}\n\n"
            elif kind == "on_tool_end":
                yield f"data: {json.dumps({'type': 'tool_end', 'tool': event['name']})}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"


rag_chat_service = RAGChatService()
