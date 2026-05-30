import json
import logging
import re
from asyncio import to_thread
from urllib.parse import urlparse

from pydantic import BaseModel, Field, ValidationError

from backend.config import Settings
from backend.connectors.codex_cli import (
    CodexCliError,
    CodexCliUnavailableError,
    get_codex_cli_connector,
)
from backend.schemas import ApplicationScrapePreview, ApplicationTagPayload, SeniorityLevel
from backend.services.prompts import get_prompt_content

logger = logging.getLogger(__name__)

MAX_RAW_TEXT_CHARS = 24_000
MAX_DESCRIPTION_CHARS = 12_000

TAG_PATTERNS: dict[str, tuple[str, tuple[str, ...]]] = {
    "python": ("technology", ("python",)),
    "typescript": ("technology", ("typescript", "type script")),
    "javascript": ("technology", ("javascript", "java script")),
    "react": ("framework", ("react", "react.js", "reactjs")),
    "next.js": ("framework", ("next.js", "nextjs", "next js")),
    "fastapi": ("framework", ("fastapi", "fast api")),
    "django": ("framework", ("django",)),
    "flask": ("framework", ("flask",)),
    "sqlalchemy": ("framework", ("sqlalchemy", "sql alchemy")),
    "postgresql": ("database", ("postgresql", "postgres")),
    "mysql": ("database", ("mysql",)),
    "redis": ("database", ("redis",)),
    "mongodb": ("database", ("mongodb", "mongo db")),
    "elasticsearch": ("database", ("elasticsearch", "elastic search")),
    "docker": ("devops", ("docker",)),
    "kubernetes": ("devops", ("kubernetes", "k8s")),
    "aws": ("cloud", ("aws", "amazon web services")),
    "gcp": ("cloud", ("gcp", "google cloud")),
    "azure": ("cloud", ("azure",)),
    "terraform": ("devops", ("terraform",)),
    "ci/cd": ("devops", ("ci/cd", "continuous integration", "continuous delivery")),
    "kafka": ("messaging", ("kafka", "apache kafka")),
    "rabbitmq": ("messaging", ("rabbitmq", "rabbit mq")),
    "microservices": ("architecture", ("microservices", "micro-services")),
    "event-driven": ("architecture", ("event-driven", "event driven")),
    "observability": ("devops", ("observability", "opentelemetry", "open telemetry")),
    "rest api": ("architecture", ("rest api", "restful")),
    "graphql": ("architecture", ("graphql",)),
    "machine learning": ("domain", ("machine learning", "ml engineer")),
    "llm": ("domain", ("llm", "large language model", "genai", "generative ai")),
    "agile": ("methodology", ("agile", "scrum", "kanban")),
    "ownership": ("buzzword", ("ownership", "take ownership")),
    "stakeholder management": ("buzzword", ("stakeholder management", "stakeholders")),
}

SENIORITY_ALIASES: dict[str, SeniorityLevel] = {
    "middle developer": SeniorityLevel.MIDDLE_DEVELOPER,
    "mid developer": SeniorityLevel.MIDDLE_DEVELOPER,
    "mid-level developer": SeniorityLevel.MIDDLE_DEVELOPER,
    "middle software developer": SeniorityLevel.MIDDLE_DEVELOPER,
    "mid software developer": SeniorityLevel.MIDDLE_DEVELOPER,
    "middle software engineer": SeniorityLevel.MIDDLE_DEVELOPER,
    "mid software engineer": SeniorityLevel.MIDDLE_DEVELOPER,
    "senior developer": SeniorityLevel.SENIOR_DEVELOPER,
    "senior software developer": SeniorityLevel.SENIOR_DEVELOPER,
    "senior software engineer": SeniorityLevel.SENIOR_DEVELOPER,
    "principal developer": SeniorityLevel.PRINCIPAL_DEVELOPER,
    "principal software developer": SeniorityLevel.PRINCIPAL_DEVELOPER,
    "principal software engineer": SeniorityLevel.PRINCIPAL_DEVELOPER,
    "middle data engineer": SeniorityLevel.MIDDLE_DATA_ENGINEER,
    "mid data engineer": SeniorityLevel.MIDDLE_DATA_ENGINEER,
    "mid-level data engineer": SeniorityLevel.MIDDLE_DATA_ENGINEER,
    "senior data engineer": SeniorityLevel.SENIOR_DATA_ENGINEER,
    "principal data engineer": SeniorityLevel.PRINCIPAL_DATA_ENGINEER,
    "software architect": SeniorityLevel.SOFTWARE_ARCHITECT,
    "solution architect": SeniorityLevel.SOFTWARE_ARCHITECT,
    "solutions architect": SeniorityLevel.SOFTWARE_ARCHITECT,
    "data architect": SeniorityLevel.DATA_ARCHITECT,
    "middle manager": SeniorityLevel.MIDDLE_MANAGER,
    "mid manager": SeniorityLevel.MIDDLE_MANAGER,
    "mid-level manager": SeniorityLevel.MIDDLE_MANAGER,
    "senior manager": SeniorityLevel.SENIOR_MANAGER,
}


class ExtractedTag(BaseModel):
    name: str
    kind: str = "keyword"
    confidence: float | None = None
    source: str | None = None


class JobPostExtraction(BaseModel):
    company_name: str | None = None
    position_title: str | None = None
    position_description: str | None = None
    location: str | None = None
    remote_policy: str | None = None
    seniority: str | None = None
    employment_type: str | None = None
    salary: str | None = None
    contact_url: str | None = None
    contact_description: str | None = None
    recruitment_description: str | None = None
    tags: list[ExtractedTag] = Field(default_factory=list)


def normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def normalize_seniority_level(value: str | None) -> SeniorityLevel | None:
    if value is None:
        return None

    normalized = normalize_whitespace(value).lower()
    if not normalized:
        return None

    for seniority in SeniorityLevel:
        if normalized == seniority.value.lower():
            return seniority

    return SENIORITY_ALIASES.get(normalized)


def validate_public_url(value: str) -> str:
    url = value.strip()
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("URL must be an absolute http(s) URL")
    return url


def scrape_rendered_text_sync(url: str, settings: Settings) -> tuple[str, list[str]]:
    warnings: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as error:
        raise RuntimeError("Playwright is not installed") from error

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = None
        try:
            page = browser.new_page()
            page.set_default_timeout(settings.scrape_timeout_ms)
            page.goto(url, wait_until="domcontentloaded", timeout=settings.scrape_timeout_ms)
            try:
                page.wait_for_load_state("networkidle", timeout=5_000)
            except Exception:
                warnings.append(
                    "Страница не дождалась полной сетевой тишины, текст взят после DOM-загрузки."
                )

            data = page.evaluate(
                """
                () => {
                  const blockedSelectors = [
                    "script", "style", "noscript", "svg", "canvas", "nav", "footer",
                    "[aria-hidden='true']"
                  ];
                  for (const selector of blockedSelectors) {
                    for (const node of document.querySelectorAll(selector)) {
                      node.remove();
                    }
                  }
                  const metaDescription = document
                    .querySelector("meta[name='description'], meta[property='og:description']")
                    ?.getAttribute("content") || "";
                  const ogTitle = document
                    .querySelector("meta[property='og:title']")
                    ?.getAttribute("content") || "";
                  return {
                    title: document.title || "",
                    ogTitle,
                    metaDescription,
                    bodyText: document.body ? document.body.innerText : "",
                  };
                }
                """
            )
        finally:
            if page is not None:
                try:
                    page.close()
                except Exception:
                    pass
            browser.close()

    text_parts = [
        normalize_whitespace(data.get("title", "")),
        normalize_whitespace(data.get("ogTitle", "")),
        normalize_whitespace(data.get("metaDescription", "")),
        data.get("bodyText", ""),
    ]
    raw_text = "\n\n".join(part for part in text_parts if part).strip()
    raw_text = re.sub(r"\n{3,}", "\n\n", raw_text)

    if len(raw_text) > MAX_RAW_TEXT_CHARS:
        raw_text = raw_text[:MAX_RAW_TEXT_CHARS]
        warnings.append("Текст описания был обрезан перед анализом.")

    return raw_text, warnings


async def scrape_rendered_text(url: str, settings: Settings) -> tuple[str, list[str]]:
    return await to_thread(scrape_rendered_text_sync, url, settings)


def extract_tags_with_dictionary(text: str) -> list[ApplicationTagPayload]:
    lowered = text.lower()
    tags: list[ApplicationTagPayload] = []
    for name, (kind, aliases) in TAG_PATTERNS.items():
        if any(
            re.search(rf"(?<![\w.+#-]){re.escape(alias)}(?![\w.+#-])", lowered) for alias in aliases
        ):
            tags.append(
                ApplicationTagPayload(
                    name=name,
                    kind=kind,
                    confidence=0.7,
                    source="dictionary",
                )
            )
    return tags


def infer_title(raw_text: str) -> str | None:
    for line in raw_text.splitlines():
        cleaned = normalize_whitespace(line)
        if 8 <= len(cleaned) <= 160:
            return cleaned
    return None


def infer_company_from_title(title: str | None) -> str | None:
    if not title:
        return None
    separators = (" - ", " | ", " at ", " @ ")
    for separator in separators:
        if separator in title:
            candidate = title.rsplit(separator, 1)[-1].strip()
            if 2 <= len(candidate) <= 120:
                return candidate
    return None


def merge_tags(
    dictionary_tags: list[ApplicationTagPayload],
    model_tags: list[ExtractedTag],
) -> list[ApplicationTagPayload]:
    by_name: dict[str, ApplicationTagPayload] = {
        tag.name.strip().lower(): tag for tag in dictionary_tags if tag.name.strip()
    }
    for tag in model_tags:
        name = tag.name.strip()
        if not name:
            continue
        key = name.lower()
        existing = by_name.get(key)
        if existing is None or (tag.confidence or 0) > (existing.confidence or 0):
            by_name[key] = ApplicationTagPayload(
                name=name,
                kind=tag.kind.strip() or "keyword",
                confidence=tag.confidence,
                source=tag.source,
            )
    return sorted(by_name.values(), key=lambda tag: (tag.kind, tag.name.lower()))


def build_job_extraction_prompt(raw_text: str, settings: Settings) -> str:
    template = get_prompt_content("job_post_extraction")
    return f"{template}\n\nRendered page text:\n{raw_text}"


def parse_job_extraction_json(output: str) -> JobPostExtraction:
    cleaned = output.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    json_start = cleaned.find("{")
    json_end = cleaned.rfind("}")
    if json_start == -1 or json_end == -1 or json_end < json_start:
        raise ValueError("Codex output did not contain a JSON object")

    payload = json.loads(cleaned[json_start : json_end + 1])
    return JobPostExtraction.model_validate(payload)


async def extract_with_codex(raw_text: str, settings: Settings) -> JobPostExtraction | None:
    prompt = build_job_extraction_prompt(raw_text, settings)
    try:
        result = await get_codex_cli_connector(settings).send(prompt)
        return parse_job_extraction_json(result.stdout)
    except CodexCliUnavailableError as exc:
        logger.warning("Codex extraction skipped: %s", exc)
        return None
    except (CodexCliError, ValueError, json.JSONDecodeError, ValidationError):
        logger.exception("Codex extraction failed; using fallback extraction")
        return None


async def build_preview_from_text(
    raw_text: str,
    source_url: str,
    settings: Settings,
    warnings: list[str],
    raw_source: str = "url",
) -> ApplicationScrapePreview:
    if not raw_text:
        warnings.append("Не удалось извлечь видимый текст со страницы.")

    dictionary_tags = extract_tags_with_dictionary(raw_text)
    extracted = await extract_with_codex(raw_text, settings)
    if extracted is None:
        warnings.append("Codex-извлечение не выполнено: CLI недоступен или вернул невалидный JSON.")
        inferred_title = infer_title(raw_text)
        extracted = JobPostExtraction(
            company_name=infer_company_from_title(inferred_title),
            position_title=inferred_title,
            position_description=raw_text[:MAX_DESCRIPTION_CHARS],
            tags=[],
        )

    return ApplicationScrapePreview(
        source_url=source_url,
        company_name=extracted.company_name,
        position_title=extracted.position_title,
        position_description=(extracted.position_description or raw_text)[:MAX_DESCRIPTION_CHARS],
        location=extracted.location,
        remote_policy=extracted.remote_policy,
        seniority=normalize_seniority_level(extracted.seniority),
        employment_type=extracted.employment_type,
        salary=extracted.salary,
        contact_url=extracted.contact_url,
        contact_description=extracted.contact_description,
        recruitment_description=extracted.recruitment_description,
        tags=merge_tags(dictionary_tags, extracted.tags),
        raw_text=raw_text,
        raw_source=raw_source,
        warnings=warnings,
    )


async def scrape_application_preview(url: str, settings: Settings) -> ApplicationScrapePreview:
    source_url = validate_public_url(url)
    raw_text, warnings = await scrape_rendered_text(source_url, settings)
    return await build_preview_from_text(
        raw_text=raw_text,
        source_url=source_url,
        settings=settings,
        warnings=warnings,
        raw_source="url",
    )


async def scrape_application_text_preview(
    text: str,
    source_url: str | None,
    settings: Settings,
) -> ApplicationScrapePreview:
    warnings: list[str] = []
    normalized_source_url = validate_public_url(source_url) if source_url else ""
    raw_text = text.strip()
    if len(raw_text) > MAX_RAW_TEXT_CHARS:
        raw_text = raw_text[:MAX_RAW_TEXT_CHARS]
        warnings.append("Текст описания был обрезан перед анализом.")

    return await build_preview_from_text(
        raw_text=raw_text,
        source_url=normalized_source_url,
        settings=settings,
        warnings=warnings,
        raw_source="text",
    )
