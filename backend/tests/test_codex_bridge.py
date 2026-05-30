import asyncio
import sys

from backend.config import Settings
from backend.connectors.codex_cli import (
    CodexCliUnavailableError,
    build_codex_command,
    get_codex_cli_connector,
)
from backend.schemas import CodexAskRequest
from backend.services.codex_bridge import ask_codex, build_codex_prompt, resolve_codex_context


def make_settings(args: str) -> Settings:
    return Settings(
        _env_file=None,
        llm_provider="codex",
        codex_cli_command=sys.executable,
        codex_cli_args=args,
        codex_cli_timeout_seconds=5,
    )


def test_build_codex_command_splits_configured_args() -> None:
    settings = make_settings('exec --skip-git-repo-check "-"')

    assert build_codex_command(settings) == [
        sys.executable,
        "exec",
        "--skip-git-repo-check",
        "-",
    ]


def test_codex_cli_connector_send_runs_process_in_worker_thread() -> None:
    settings = make_settings('-c "import sys; print(sys.stdin.read().upper())"')

    result = asyncio.run(get_codex_cli_connector(settings).send("ping"))

    assert result.stdout == "PING"


def test_codex_cli_connector_raises_unavailable_for_missing_command() -> None:
    settings = Settings(
        _env_file=None,
        codex_cli_command="definitely-missing-codex-command",
        codex_cli_args="exec -",
        codex_cli_timeout_seconds=5,
    )

    try:
        asyncio.run(get_codex_cli_connector(settings).send("ping"))
    except CodexCliUnavailableError as exc:
        assert "not found" in str(exc)
    else:
        raise AssertionError("Expected CodexCliUnavailableError")


def test_build_codex_prompt_includes_question_and_context() -> None:
    prompt = build_codex_prompt(
        CodexAskRequest(question="Where is routing?", context="FastAPI backend")
    )

    assert "Do not modify files" in prompt
    assert "FastAPI backend" in prompt
    assert "Where is routing?" in prompt


def test_ask_codex_uses_stdin_and_returns_stdout() -> None:
    settings = make_settings('-c "import sys; print(sys.stdin.read().splitlines()[-1])"')

    response = asyncio.run(ask_codex(settings, CodexAskRequest(question="ping")))

    assert response.answer == "ping"
    assert response.context_source == "manual text"


def test_resolve_codex_context_scrapes_url_mode(monkeypatch) -> None:
    async def fake_scrape_rendered_text(url: str, settings: Settings) -> tuple[str, list[str]]:
        return f"scraped from {url}", ["network idle warning"]

    monkeypatch.setattr(
        "backend.services.codex_bridge.scrape_rendered_text",
        fake_scrape_rendered_text,
    )

    context = asyncio.run(
        resolve_codex_context(
            make_settings('exec "-"'),
            CodexAskRequest(
                mode="url",
                question="summarize",
                context_url="https://example.com/job",
            ),
        )
    )

    assert context.text == "scraped from https://example.com/job"
    assert context.source == "https://example.com/job"
    assert context.warnings == ["network idle warning"]
