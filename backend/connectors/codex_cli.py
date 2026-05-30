import asyncio
import logging
import shlex
import shutil
import subprocess
from dataclasses import dataclass

from backend.config import Settings

logger = logging.getLogger(__name__)


class CodexCliError(RuntimeError):
    pass


class CodexCliUnavailableError(CodexCliError):
    pass


@dataclass(frozen=True)
class CodexCliResult:
    stdout: str
    stderr: str | None


@dataclass(frozen=True)
class CodexCliConnector:
    command: list[str]
    cwd: str
    timeout_seconds: int

    async def send(self, prompt: str) -> CodexCliResult:
        return await asyncio.to_thread(self.send_sync, prompt)

    def send_sync(self, prompt: str) -> CodexCliResult:
        logger.info("Starting Codex CLI command=%s cwd=%s", self.command, self.cwd)
        try:
            completed = subprocess.run(
                self.command,
                cwd=self.cwd,
                input=prompt,
                capture_output=True,
                check=False,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout_seconds,
            )
        except FileNotFoundError as exc:
            raise CodexCliUnavailableError(
                f"Codex CLI command not found: {self.command[0]}"
            ) from exc
        except PermissionError as exc:
            raise CodexCliUnavailableError(
                f"Codex CLI command is not executable: {self.command[0]}"
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise CodexCliError(
                f"Codex CLI timed out after {self.timeout_seconds} seconds"
            ) from exc
        except OSError as exc:
            raise CodexCliUnavailableError(f"Codex CLI failed to start: {exc}") from exc

        stdout_text = completed.stdout.strip()
        stderr_text = completed.stderr.strip()

        if completed.returncode != 0:
            logger.warning(
                "Codex CLI failed returncode=%s stderr=%s",
                completed.returncode,
                stderr_text,
            )
            detail = stderr_text or stdout_text or f"Codex CLI exited with {completed.returncode}"
            raise CodexCliError(detail)

        logger.info("Codex CLI completed output_chars=%s", len(stdout_text))
        return CodexCliResult(stdout=stdout_text, stderr=stderr_text or None)


def build_codex_command(settings: Settings) -> list[str]:
    executable = shutil.which(settings.codex_cli_command) or settings.codex_cli_command
    return [executable, *shlex.split(settings.codex_cli_args)]


def get_codex_cli_connector(settings: Settings) -> CodexCliConnector:
    return CodexCliConnector(
        command=build_codex_command(settings),
        cwd=str(settings.project_root),
        timeout_seconds=settings.codex_cli_timeout_seconds,
    )
