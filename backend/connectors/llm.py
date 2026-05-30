import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

import ollama as ollama_client

from backend.connectors.codex_cli import CodexCliError, get_codex_cli_connector

logger = logging.getLogger(__name__)


class LLMError(RuntimeError):
    pass


@dataclass(frozen=True)
class LLMResponse:
    content: str


class LLMProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def timeout_seconds(self) -> int: ...

    @property
    @abstractmethod
    def info(self) -> dict[str, str]: ...

    @abstractmethod
    async def ask(self, prompt: str) -> LLMResponse: ...

    async def stream(self, prompt: str):
        result = await self.ask(prompt)
        yield result.content


class CodexProvider(LLMProvider):
    def __init__(self, settings: "Settings") -> None:  # type: ignore[name-defined]
        self._connector = get_codex_cli_connector(settings)
        self._timeout = settings.codex_cli_timeout_seconds

    @property
    def name(self) -> str:
        return "codex"

    @property
    def timeout_seconds(self) -> int:
        return self._timeout

    @property
    def info(self) -> dict[str, str]:
        return {
            "command": " ".join(self._connector.command),
            "working directory": self._connector.cwd,
        }

    async def ask(self, prompt: str) -> LLMResponse:
        try:
            result = await self._connector.send(prompt)
        except CodexCliError as exc:
            raise LLMError(str(exc)) from exc
        return LLMResponse(content=result.stdout)


_MAX_TOOL_ITERATIONS = 5


class OllamaProvider(LLMProvider):
    def __init__(
        self,
        base_url: str,
        model: str,
        num_ctx: int,
        timeout_sec: int,
        web_search_enabled: bool = False,
        web_search_max_results: int = 5,
    ) -> None:
        self._client = ollama_client.AsyncClient(host=base_url)
        self._model = model
        self._num_ctx = num_ctx
        self._timeout = timeout_sec
        self._base_url = base_url
        self._web_search_enabled = web_search_enabled
        self._web_search_max_results = web_search_max_results

    @property
    def name(self) -> str:
        return "ollama"

    @property
    def timeout_seconds(self) -> int:
        return self._timeout

    @property
    def info(self) -> dict[str, str]:
        return {
            "model": self._model,
            "base url": self._base_url,
            "context window": str(self._num_ctx),
            "web search": "enabled" if self._web_search_enabled else "disabled",
        }

    def _tools(self) -> list[dict]:
        if not self._web_search_enabled:
            return []
        from backend.services.web_search import TOOL_DEFINITION
        return [TOOL_DEFINITION]

    async def _run_tool(self, name: str, arguments: dict) -> str:
        if name == "web_search":
            from backend.services.web_search import search
            return await search(
                arguments.get("query", ""), max_results=self._web_search_max_results
            )
        return f"Unknown tool: {name}"

    async def ask(self, prompt: str) -> LLMResponse:
        logger.info("Ollama request model=%s ctx=%s web_search=%s", self._model, self._num_ctx, self._web_search_enabled)
        tools = self._tools()
        messages: list = [{"role": "user", "content": prompt}]

        try:
            for iteration in range(_MAX_TOOL_ITERATIONS):
                response = await asyncio.wait_for(
                    self._client.chat(
                        model=self._model,
                        messages=messages,
                        tools=tools,
                        options={"num_ctx": self._num_ctx},
                    ),
                    timeout=self._timeout,
                )

                if not response.message.tool_calls:
                    content = response.message.content or ""
                    logger.info("Ollama response iteration=%s chars=%s", iteration, len(content))
                    return LLMResponse(content=content)

                messages.append(response.message)
                for tc in response.message.tool_calls:
                    tool_result = await self._run_tool(tc.function.name, tc.function.arguments)
                    logger.info("Tool call name=%s result_chars=%s", tc.function.name, len(tool_result))
                    messages.append({"role": "tool", "content": tool_result})

        except asyncio.TimeoutError as exc:
            raise LLMError(f"Ollama timed out after {self._timeout}s") from exc
        except LLMError:
            raise
        except Exception as exc:
            raise LLMError(f"Ollama request failed: {exc}") from exc

        raise LLMError("Exceeded maximum tool call iterations")

    async def stream(self, prompt: str):
        tools = self._tools()
        messages: list = [{"role": "user", "content": prompt}]

        try:
            for _ in range(_MAX_TOOL_ITERATIONS):
                accumulated_content = ""
                tool_calls = None

                async for chunk in await self._client.chat(
                    model=self._model,
                    messages=messages,
                    tools=tools,
                    stream=True,
                    options={"num_ctx": self._num_ctx},
                ):
                    if chunk.message.content:
                        accumulated_content += chunk.message.content
                        yield chunk.message.content
                    if chunk.message.tool_calls:
                        tool_calls = chunk.message.tool_calls

                if not tool_calls:
                    return

                messages.append({
                    "role": "assistant",
                    "content": accumulated_content,
                    "tool_calls": [
                        {"function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                        for tc in tool_calls
                    ],
                })
                for tc in tool_calls:
                    logger.info("Tool call (stream) name=%s", tc.function.name)
                    result = await self._run_tool(tc.function.name, tc.function.arguments)
                    messages.append({"role": "tool", "content": result})

        except LLMError:
            raise
        except Exception as exc:
            raise LLMError(f"Ollama stream failed: {exc}") from exc


def get_llm_provider(settings: "Settings") -> LLMProvider:  # type: ignore[name-defined]
    from backend.config import Settings  # avoid circular import at module level

    assert isinstance(settings, Settings)
    if settings.llm_provider == "ollama":
        return OllamaProvider(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            num_ctx=settings.ollama_num_ctx,
            timeout_sec=settings.ollama_timeout_seconds,
            web_search_enabled=settings.web_search_enabled,
            web_search_max_results=settings.web_search_max_results,
        )
    return CodexProvider(settings)
