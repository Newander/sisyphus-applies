import logging
import time
from typing import Annotated

from fastapi import Depends, FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from starlette.responses import Response

from backend.api.application_sources import router as application_sources_router
from backend.api.applications import router as applications_router
from backend.api.codex import router as codex_router
from backend.api.companies import router as companies_router
from backend.api.documents import router as documents_router
from backend.api.feature_memories import router as feature_memories_router
from backend.api.gmail import router as gmail_router
from backend.api.prompts import router as prompts_router
from backend.config import Settings, get_settings
from backend.db import get_session
from backend.logging_config import configure_logging
from backend.migrations import upgrade_database
from backend.schemas import DashboardResponse, Page, RecentCompany
from backend.services.dashboard import get_dashboard, list_recent_companies_page
from backend.services.prompts import seed_default_prompts

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(title="Local Job Tracker API")
app.include_router(companies_router)
app.include_router(application_sources_router)
app.include_router(applications_router)
app.include_router(documents_router)
app.include_router(feature_memories_router)
app.include_router(gmail_router)
app.include_router(codex_router)
app.include_router(prompts_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://127.0.0.1:3000"],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next) -> Response:
    started_at = time.perf_counter()
    client_host = request.client.host if request.client else "unknown"
    query = str(request.query_params) or "-"
    logger.info(
        "HTTP request started method=%s path=%s query=%s client=%s",
        request.method,
        request.url.path,
        query,
        client_host,
    )
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (time.perf_counter() - started_at) * 1000
        logger.exception(
            "HTTP request failed method=%s path=%s query=%s duration_ms=%.2f",
            request.method,
            request.url.path,
            query,
            duration_ms,
        )
        raise

    duration_ms = (time.perf_counter() - started_at) * 1000
    logger.info(
        "HTTP request finished method=%s path=%s status_code=%s duration_ms=%.2f",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


@app.on_event("startup")
def on_startup() -> None:
    logger.info("Backend startup storage_dir=%s", settings.storage_dir)
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    upgrade_database()
    seed_default_prompts()
    logger.info("Backend startup complete")


@app.get("/health")
def health() -> dict[str, str]:
    logger.debug("Health check called")
    return {"status": "ok"}


@app.get("/api/dashboard", response_model=DashboardResponse)
def dashboard(
    session: Annotated[Session, Depends(get_session)],
    app_settings: Annotated[Settings, Depends(get_settings)],
) -> DashboardResponse:
    logger.info("Dashboard requested storage_dir=%s", app_settings.storage_dir)
    dashboard_data = get_dashboard(session, app_settings)
    logger.info(
        "Dashboard built applications_total=%s updates_total=%s documents_count=%s",
        dashboard_data.stats.applications_total,
        dashboard_data.stats.updates_total,
        len(dashboard_data.documents),
    )
    return dashboard_data


@app.get("/api/dashboard/recent-companies/page", response_model=Page[RecentCompany])
def dashboard_recent_companies_page(
    session: Annotated[Session, Depends(get_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 5,
    sort: str = "latest_added_at",
    direction: Annotated[str, Query(pattern="^(asc|desc)$")] = "desc",
) -> Page[RecentCompany]:
    logger.info(
        "Dashboard recent companies page requested page=%s page_size=%s sort=%s direction=%s",
        page,
        page_size,
        sort,
        direction,
    )
    items, total = list_recent_companies_page(
        session,
        page=page,
        page_size=page_size,
        sort=sort,
        direction=direction,
    )
    return Page[RecentCompany](
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        sort=sort,
        direction=direction,
    )
