from pathlib import Path

from backend.config import Settings
from backend.schemas import SeniorityLevel
from backend.services.application_scraper import (
    build_job_extraction_prompt,
    normalize_seniority_level,
    parse_job_extraction_json,
)


def test_build_job_extraction_prompt_loads_configured_prompt_file(tmp_path: Path) -> None:
    prompt_file = tmp_path / "prompt.md"
    prompt_file.write_text("Return JSON only.", encoding="utf-8")
    settings = Settings(_env_file=None, codex_job_extraction_prompt_file=prompt_file)

    prompt = build_job_extraction_prompt("Senior Python Engineer at Acme", settings)

    assert "Return JSON only." in prompt
    assert "Senior Python Engineer at Acme" in prompt


def test_parse_job_extraction_json_accepts_fenced_json() -> None:
    extraction = parse_job_extraction_json(
        """```json
        {
          "company_name": "Acme",
          "position_title": "Senior Python Engineer",
          "position_description": "Build APIs",
          "location": "Remote",
          "remote_policy": "remote",
          "seniority": "senior",
          "employment_type": "full-time",
          "salary": null,
          "tags": [
            {"name": "python", "kind": "technology", "confidence": 0.95, "source": "codex"}
          ]
        }
        ```"""
    )

    assert extraction.company_name == "Acme"
    assert extraction.position_title == "Senior Python Engineer"
    assert extraction.tags[0].name == "python"


def test_normalize_seniority_level_accepts_allowed_values_and_aliases() -> None:
    assert normalize_seniority_level("Senior Developer") == SeniorityLevel.SENIOR_DEVELOPER
    assert normalize_seniority_level("senior software engineer") == SeniorityLevel.SENIOR_DEVELOPER
    assert normalize_seniority_level("Mid Data Engineer") == SeniorityLevel.MIDDLE_DATA_ENGINEER
    assert normalize_seniority_level("lead") is None
