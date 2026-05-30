import logging
from pathlib import Path

from sqlalchemy import select

from backend.db import engine
from backend.models import Prompt

logger = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

_DEFAULT_PROMPTS = [
    {
        "name": "codex_bridge",
        "description": "Base prompt for answering project questions via Codex",
        "file": "codex_bridge.md",
    },
    {
        "name": "job_post_extraction",
        "description": "Extracting job data from page text",
        "file": "job_post_extraction.md",
    },
    {
        "name": "cover_letter_generation",
        "description": "Generating a cover letter from application context",
        "file": None,
        "content": (
            "Generate a professional cover letter based on the job application context"
            " provided.\n\n"
            "The cover letter should:\n"
            "- Be addressed to the hiring team\n"
            "- Highlight relevant experience matching the position\n"
            "- Be concise (3-4 paragraphs)\n"
            "- End with a call to action\n\n"
            "Write in the same language as the job posting context."
        ),
    },
]


def get_prompt_content(name: str) -> str:
    from sqlalchemy.orm import Session

    with Session(engine) as session:
        prompt = session.scalar(select(Prompt).where(Prompt.name == name))
        if prompt is None:
            raise RuntimeError(f"Prompt '{name}' not found in database")
        return prompt.content.strip()


def seed_default_prompts() -> None:
    from sqlalchemy.orm import Session

    with Session(engine) as session:
        for entry in _DEFAULT_PROMPTS:
            if entry.get("file") is None:
                content = entry["content"]
            else:
                prompt_file = _PROMPTS_DIR / entry["file"]
                if not prompt_file.exists():
                    logger.warning("Prompt file not found path=%s", prompt_file)
                    continue
                content = prompt_file.read_text(encoding="utf-8")

            existing = session.scalar(select(Prompt).where(Prompt.name == entry["name"]))
            if existing is None:
                session.add(
                    Prompt(name=entry["name"], description=entry["description"], content=content)
                )
                logger.info("Seeded default prompt name=%s", entry["name"])
            elif existing.content.strip() != content.strip():
                existing.content = content
                logger.info("Updated default prompt name=%s", entry["name"])
        session.commit()
