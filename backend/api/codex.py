import json
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.config import Settings, get_settings
from backend.connectors.llm import LLMError, get_llm_provider
from backend.db import get_session
from backend.schemas import (
    CodexAskRequest,
    CodexAskResponse,
    CoverLetterRequest,
    CoverLetterResponse,
    LLMStatusResponse,
)
from backend.services.codex_bridge import (
    CodexBridgeError,
    ask_codex,
    resolve_codex_context,
    stream_codex,
)
from backend.services.prompts import get_prompt_content

router = APIRouter(prefix="/api/codex", tags=["codex"])
logger = logging.getLogger(__name__)


@router.get("/status", response_model=LLMStatusResponse)
def codex_status(settings: Annotated[Settings, Depends(get_settings)]) -> LLMStatusResponse:
    provider = get_llm_provider(settings)
    return LLMStatusResponse(
        provider=provider.name,
        timeout_seconds=provider.timeout_seconds,
        info=provider.info,
    )


@router.post("/ask", response_model=CodexAskResponse)
async def codex_ask(
    request: CodexAskRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[Session, Depends(get_session)],
) -> CodexAskResponse:
    try:
        return await ask_codex(settings, request, session)
    except CodexBridgeError as exc:
        logger.exception("LLM bridge request failed")
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/ask/stream")
async def codex_ask_stream(
    request: CodexAskRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[Session, Depends(get_session)],
) -> StreamingResponse:
    try:
        context = await resolve_codex_context(settings, request)
    except CodexBridgeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    async def generate():
        try:
            async for chunk in stream_codex(settings, request, session):
                yield f"data: {json.dumps({'content': chunk})}\n\n"
            yield f"data: {json.dumps({'done': True, 'context_source': context.source, 'warnings': context.warnings})}\n\n"
        except CodexBridgeError as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"
        except Exception as exc:
            logger.exception("Stream failed")
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


def _build_cover_letter_prompt(template: str, request: CoverLetterRequest) -> str:
    parts = [
        f"Position: {request.position_title}",
        f"Company: {request.company_name}",
    ]
    if request.notes:
        parts.append(f"Notes: {request.notes}")
    if request.raw_position_text:
        parts.append(f"Job posting:\n{request.raw_position_text}")
    context = "\n".join(parts)
    return f"{template}\n\nContext:\n{context}"


@router.post("/cover-letter", response_model=CoverLetterResponse)
async def generate_cover_letter(
    request: CoverLetterRequest,
    settings: Annotated[Settings, Depends(get_settings)],
) -> CoverLetterResponse:
    template = get_prompt_content("cover_letter_generation")
    prompt = _build_cover_letter_prompt(template, request)
    try:
        result = await get_llm_provider(settings).ask(prompt)
    except LLMError as exc:
        logger.exception("Cover letter generation failed")
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return CoverLetterResponse(content=result.content)
