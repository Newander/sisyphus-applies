import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from backend.config import Settings
from backend.connectors.llm import LLMError, get_llm_provider
from backend.schemas import CodexAskRequest, CodexAskResponse
from backend.services.rag import build_rag_context
from backend.services.application_scraper import (
    MAX_RAW_TEXT_CHARS,
    scrape_rendered_text,
    validate_public_url,
)
from backend.services.prompts import get_prompt_content

logger = logging.getLogger(__name__)


CodexBridgeError = LLMError


@dataclass(frozen=True)
class CodexContext:
    text: str | None
    source: str
    warnings: list[str]


def build_codex_prompt(request: CodexAskRequest) -> str:
    return build_codex_prompt_from_template(
        template=get_prompt_content("codex_bridge"),
        question=request.question,
        context=request.context,
        context_source="manual text",
    )


def build_codex_prompt_from_template(
    template: str,
    question: str,
    context: str | None,
    context_source: str,
    rag_context: str | None = None,
) -> str:
    parts = [template]
    if rag_context:
        parts.append(rag_context)
    if context:
        parts.append(f"Context source: {context_source}\n\nAdditional context:\n{context}")
    parts.append(f"Question:\n{question}")
    return "\n\n".join(parts)


async def resolve_codex_context(settings: Settings, request: CodexAskRequest) -> CodexContext:
    if request.mode == "url":
        if not request.context_url:
            raise CodexBridgeError("context_url is required in url mode")
        try:
            source_url = validate_public_url(request.context_url)
        except ValueError as exc:
            raise CodexBridgeError(str(exc)) from exc
        raw_text, warnings = await scrape_rendered_text(source_url, settings)
        if len(raw_text) > MAX_RAW_TEXT_CHARS:
            raw_text = raw_text[:MAX_RAW_TEXT_CHARS]
            warnings.append("Page text was truncated before sending to Codex.")
        return CodexContext(text=raw_text, source=source_url, warnings=warnings)

    return CodexContext(text=request.context, source="manual text", warnings=[])


async def _prepare(
    settings: Settings, request: CodexAskRequest, session: Session | None
) -> tuple[str, CodexContext]:
    context = await resolve_codex_context(settings, request)
    rag_context = None
    if session is not None and settings.llm_provider == "ollama":
        try:
            rag_context = await build_rag_context(request.question, settings, session)
        except Exception as exc:
            logger.warning("RAG context retrieval failed: %s", exc)
    prompt = build_codex_prompt_from_template(
        template=get_prompt_content("codex_bridge"),
        question=request.question,
        context=context.text,
        context_source=context.source,
        rag_context=rag_context,
    )
    return prompt, context


async def ask_codex(
    settings: Settings, request: CodexAskRequest, session: Session | None = None
) -> CodexAskResponse:
    prompt, context = await _prepare(settings, request, session)
    result = await get_llm_provider(settings).ask(prompt)
    return CodexAskResponse(
        answer=result.content,
        context_source=context.source,
        warnings=context.warnings,
    )


async def stream_codex(settings: Settings, request: CodexAskRequest, session: Session | None = None):
    prompt, _ = await _prepare(settings, request, session)
    async for chunk in get_llm_provider(settings).stream(prompt):
        yield chunk
