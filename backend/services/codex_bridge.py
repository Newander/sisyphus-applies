import logging
from dataclasses import dataclass

from backend.config import Settings
from backend.connectors.codex_cli import CodexCliError, get_codex_cli_connector
from backend.schemas import CodexAskRequest, CodexAskResponse
from backend.services.application_scraper import (
    MAX_RAW_TEXT_CHARS,
    scrape_rendered_text,
    validate_public_url,
)
from backend.services.prompts import get_prompt_content

logger = logging.getLogger(__name__)


CodexBridgeError = CodexCliError


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
) -> str:
    if context:
        return (
            f"{template}\n\n"
            f"Context source: {context_source}\n\n"
            f"Additional context:\n{context}\n\n"
            f"Question:\n{question}"
        )
    return f"{template}\n\nQuestion:\n{question}"


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
            warnings.append("Текст страницы был обрезан перед отправкой в Codex.")
        return CodexContext(text=raw_text, source=source_url, warnings=warnings)

    return CodexContext(text=request.context, source="manual text", warnings=[])


async def ask_codex(settings: Settings, request: CodexAskRequest) -> CodexAskResponse:
    context = await resolve_codex_context(settings, request)
    prompt = build_codex_prompt_from_template(
        template=get_prompt_content("codex_bridge"),
        question=request.question,
        context=context.text,
        context_source=context.source,
    )
    result = await get_codex_cli_connector(settings).send(prompt)
    return CodexAskResponse(
        answer=result.stdout,
        stderr=result.stderr,
        context_source=context.source,
        warnings=context.warnings,
    )
