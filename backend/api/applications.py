import logging
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.orm import Session

from backend.config import Settings, get_settings
from backend.db import get_session
from backend.models import (
    APPLICATION_FLOW,
    APPLICATION_STATUS_TRANSITIONS,
    ApplicationSource,
    ApplicationStatus,
    ApplicationTag,
    ApplicationUpdate,
    ApplicationUpdateType,
    Company,
    JobApplication,
)
from backend.schemas import (
    ApplicationCreate,
    ApplicationRead,
    ApplicationRejectionUpdate,
    ApplicationScrapePreview,
    ApplicationScrapeRequest,
    ApplicationTagPayload,
    ApplicationTagRead,
    ApplicationTextPreviewRequest,
    ApplicationUpdateRequest,
    Page,
)
from backend.services.application_scraper import (
    scrape_application_preview,
    scrape_application_text_preview,
)

router = APIRouter(prefix="/api/applications", tags=["applications"])
logger = logging.getLogger(__name__)


def parse_status(value: str) -> ApplicationStatus:
    try:
        return ApplicationStatus(value)
    except ValueError as error:
        logger.warning("Unknown application status value=%s", value)
        raise HTTPException(
            status_code=422, detail=f"Unknown application status: {value}"
        ) from error


def update_type_for_status(status: ApplicationStatus) -> ApplicationUpdateType:
    return ApplicationUpdateType(status.value)


def update_title(update_type: ApplicationUpdateType) -> str:
    return {
        ApplicationUpdateType.SENT_CV: "CV sent",
        ApplicationUpdateType.RECRUITER_CALL: "Recruiter call",
        ApplicationUpdateType.RECEIVE_RESPONSE: "Response received",
        ApplicationUpdateType.INTERVIEW_SCHEDULED: "Interview scheduled",
        ApplicationUpdateType.INTERVIEW_FINISHED: "Interview finished",
        ApplicationUpdateType.OFFER: "Offer received",
        ApplicationUpdateType.REJECTED: "Rejected",
    }[update_type]


def ensure_status_transition(
    previous_status: ApplicationStatus,
    next_status: ApplicationStatus,
) -> None:
    if previous_status == next_status:
        return
    if next_status in APPLICATION_STATUS_TRANSITIONS[previous_status]:
        return

    logger.warning(
        "Invalid application status transition previous_status=%s next_status=%s",
        previous_status.value,
        next_status.value,
    )
    raise HTTPException(
        status_code=422,
        detail=f"Invalid status transition: {previous_status.value} -> {next_status.value}",
    )


def to_application_read(application: JobApplication) -> ApplicationRead:
    return ApplicationRead(
        id=application.id,
        company_id=application.company_id,
        company_name=application.company.name,
        application_source_id=application.application_source_id,
        application_source_name=(
            application.application_source.name if application.application_source else None
        ),
        primary_document_id=application.primary_document_id,
        position_title=application.position_title,
        status=application.status.value,
        source_url=application.source_url,
        position_url=application.position_url,
        rejection_reason=application.rejection_reason,
        seniority=application.seniority,
        contact_url=application.contact_url,
        contact_description=application.contact_description,
        recruitment_description=application.recruitment_description,
        cover_letter=application.cover_letter,
        notes=application.notes,
        raw_position_text=application.raw_position_text,
        raw_position_source=application.raw_position_source,
        expected_salary_min_pln=application.expected_salary_min_pln,
        expected_salary_max_pln=application.expected_salary_max_pln,
        applied_at=application.applied_at,
        last_update_at=application.last_update_at,
        created_at=application.created_at,
        updated_at=application.updated_at,
        tags=[
            ApplicationTagRead(
                id=tag.id,
                name=tag.name,
                kind=tag.kind,
                confidence=tag.confidence,
                source=tag.source,
            )
            for tag in sorted(application.tags, key=lambda item: (item.kind, item.name.lower()))
        ],
    )


def ensure_company(session: Session, company_id: int) -> None:
    if session.get(Company, company_id) is None:
        logger.warning("Application references missing company company_id=%s", company_id)
        raise HTTPException(status_code=422, detail="Company does not exist")


def ensure_application_source(session: Session, application_source_id: int | None) -> None:
    if application_source_id is None:
        return
    if session.get(ApplicationSource, application_source_id) is None:
        logger.warning(
            "Application references missing source application_source_id=%s",
            application_source_id,
        )
        raise HTTPException(status_code=422, detail="Application source does not exist")


def normalize_tag_name(value: str) -> str:
    return " ".join(value.strip().split())


def sync_application_tags(
    session: Session,
    application: JobApplication,
    payload_tags: list[ApplicationTagPayload],
) -> None:
    next_tags: list[ApplicationTag] = []
    seen_names: set[str] = set()

    for payload_tag in payload_tags:
        name = normalize_tag_name(payload_tag.name)
        if not name:
            continue

        normalized_key = name.lower()
        if normalized_key in seen_names:
            continue
        seen_names.add(normalized_key)

        tag = session.scalar(
            select(ApplicationTag).where(func.lower(ApplicationTag.name) == normalized_key)
        )
        if tag is None:
            tag = ApplicationTag(
                name=name,
                kind=payload_tag.kind.strip() or "keyword",
                confidence=payload_tag.confidence,
                source=payload_tag.source,
            )
            session.add(tag)
        else:
            tag.kind = payload_tag.kind.strip() or tag.kind
            tag.confidence = (
                payload_tag.confidence if payload_tag.confidence is not None else tag.confidence
            )
            tag.source = payload_tag.source or tag.source

        next_tags.append(tag)

    application.tags = next_tags


@router.get("/statuses", response_model=list[str])
def list_application_statuses() -> list[str]:
    logger.debug("Application statuses listed count=%s", len(APPLICATION_FLOW))
    return list(APPLICATION_FLOW)


@router.post("/scrape-preview", response_model=ApplicationScrapePreview)
async def scrape_preview(
    payload: ApplicationScrapeRequest,
    settings: Annotated[Settings, Depends(get_settings)],
) -> ApplicationScrapePreview:
    logger.info("Scraping application preview url=%s", payload.url)
    try:
        preview = await scrape_application_preview(payload.url, settings)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except RuntimeError as error:
        logger.exception("Application scrape failed url=%s", payload.url)
        raise HTTPException(status_code=501, detail=str(error)) from error
    except Exception as error:
        logger.exception("Application scrape failed url=%s", payload.url)
        raise HTTPException(status_code=502, detail="Failed to scrape position page") from error
    logger.info("Application preview scraped url=%s tags_count=%s", payload.url, len(preview.tags))
    return preview


@router.post("/text-preview", response_model=ApplicationScrapePreview)
async def text_preview(
    payload: ApplicationTextPreviewRequest,
    settings: Annotated[Settings, Depends(get_settings)],
) -> ApplicationScrapePreview:
    logger.info("Parsing application preview from text content source_url=%s", payload.source_url)
    try:
        preview = await scrape_application_text_preview(payload.text, payload.source_url, settings)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except Exception as error:
        logger.exception("Application text parse failed source_url=%s", payload.source_url)
        raise HTTPException(status_code=502, detail="Failed to parse text content") from error
    logger.info("Application text preview parsed tags_count=%s", len(preview.tags))
    return preview


APPLICATION_SORT_COLUMNS = {
    "application_source_name": ApplicationSource.name,
    "applied_at": JobApplication.applied_at,
    "company_name": Company.name,
    "expected_salary_min_pln": JobApplication.expected_salary_min_pln,
    "position_title": JobApplication.position_title,
    "rejection_reason": JobApplication.rejection_reason,
    "source_url": JobApplication.source_url,
    "status": JobApplication.status,
}


@router.get("", response_model=list[ApplicationRead])
def list_applications(session: Annotated[Session, Depends(get_session)]) -> list[ApplicationRead]:
    logger.info("Listing applications")
    applications = session.scalars(
        select(JobApplication).join(JobApplication.company).order_by(desc(JobApplication.applied_at))
    ).all()
    result = [to_application_read(application) for application in applications]
    logger.info("Applications listed count=%s", len(result))
    return result


@router.get("/page", response_model=Page[ApplicationRead])
def list_applications_page(
    session: Annotated[Session, Depends(get_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
    sort: str = "applied_at",
    direction: Annotated[str, Query(pattern="^(asc|desc)$")] = "desc",
    include_closed: bool = False,
    q: str | None = None,
) -> Page[ApplicationRead]:
    logger.info(
        "Listing applications page=%s page_size=%s sort=%s direction=%s include_closed=%s q=%s",
        page,
        page_size,
        sort,
        direction,
        include_closed,
        q,
    )
    sort_column = APPLICATION_SORT_COLUMNS.get(sort, JobApplication.applied_at)
    sort_expression = asc(sort_column) if direction == "asc" else desc(sort_column)
    total_query = select(func.count(JobApplication.id)).join(JobApplication.company)
    applications_query = (
        select(JobApplication).join(JobApplication.company).outerjoin(JobApplication.application_source)
    )
    if not include_closed:
        open_applications_filter = JobApplication.status != ApplicationStatus.REJECTED
        total_query = total_query.where(open_applications_filter)
        applications_query = applications_query.where(open_applications_filter)

    if q and q.strip():
        term = f"%{q.strip()}%"
        search_filter = or_(
            JobApplication.position_title.ilike(term),
            Company.name.ilike(term),
            JobApplication.notes.ilike(term),
            JobApplication.raw_position_text.ilike(term),
        )
        total_query = total_query.where(search_filter)
        applications_query = applications_query.where(search_filter)

    total = session.scalar(total_query) or 0
    applications = session.scalars(
        applications_query
        .order_by(sort_expression, desc(JobApplication.id))
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return Page[ApplicationRead](
        items=[to_application_read(application) for application in applications],
        total=total,
        page=page,
        page_size=page_size,
        sort=sort,
        direction=direction,
    )


@router.post("", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
def create_application(
    payload: ApplicationCreate,
    session: Annotated[Session, Depends(get_session)],
) -> ApplicationRead:
    logger.info(
        "Creating application company_id=%s position_title=%s status=%s",
        payload.company_id,
        payload.position_title,
        payload.status,
    )
    ensure_company(session, payload.company_id)
    ensure_application_source(session, payload.application_source_id)
    application = JobApplication(
        company_id=payload.company_id,
        application_source_id=payload.application_source_id,
        primary_document_id=payload.primary_document_id,
        position_title=payload.position_title.strip(),
        status=parse_status(payload.status),
        source_url=payload.source_url,
        position_url=payload.position_url,
        rejection_reason=payload.rejection_reason,
        seniority=payload.seniority.value if payload.seniority else None,
        contact_url=payload.contact_url,
        contact_description=payload.contact_description,
        recruitment_description=payload.recruitment_description,
        cover_letter=payload.cover_letter,
        notes=payload.notes,
        raw_position_text=payload.raw_position_text,
        raw_position_source=payload.raw_position_source,
        expected_salary_min_pln=payload.expected_salary_min_pln,
        expected_salary_max_pln=payload.expected_salary_max_pln,
        applied_at=payload.applied_at,
        last_update_at=payload.last_update_at,
    )
    session.add(application)
    session.flush()
    sync_application_tags(session, application, payload.tags)
    initial_update_type = update_type_for_status(application.status)
    session.add(
        ApplicationUpdate(
            application_id=application.id,
            update_type=initial_update_type.value,
            title=update_title(initial_update_type),
            description=f"Initial update type: {application.status.value}",
            occurred_at=datetime.now(UTC),
        )
    )
    session.commit()
    session.refresh(application)
    logger.info(
        "Application created application_id=%s company_id=%s status=%s",
        application.id,
        application.company_id,
        application.status.value,
    )
    return to_application_read(application)


@router.get("/{application_id}", response_model=ApplicationRead)
def get_application(
    application_id: int,
    session: Annotated[Session, Depends(get_session)],
) -> ApplicationRead:
    logger.info("Getting application application_id=%s", application_id)
    application = session.get(JobApplication, application_id)
    if application is None:
        logger.warning("Application not found application_id=%s", application_id)
        raise HTTPException(status_code=404, detail="Application not found")
    return to_application_read(application)


@router.put("/{application_id}", response_model=ApplicationRead)
def update_application(
    application_id: int,
    payload: ApplicationUpdateRequest,
    session: Annotated[Session, Depends(get_session)],
) -> ApplicationRead:
    logger.info(
        "Updating application application_id=%s company_id=%s status=%s",
        application_id,
        payload.company_id,
        payload.status,
    )
    application = session.get(JobApplication, application_id)
    if application is None:
        logger.warning("Application update target not found application_id=%s", application_id)
        raise HTTPException(status_code=404, detail="Application not found")

    ensure_company(session, payload.company_id)
    ensure_application_source(session, payload.application_source_id)
    previous_status = application.status
    next_status = parse_status(payload.status)
    ensure_status_transition(previous_status, next_status)

    application.company_id = payload.company_id
    application.application_source_id = payload.application_source_id
    application.primary_document_id = payload.primary_document_id
    application.position_title = payload.position_title.strip()
    application.status = next_status
    application.source_url = payload.source_url
    application.position_url = payload.position_url
    application.rejection_reason = payload.rejection_reason
    application.seniority = payload.seniority.value if payload.seniority else None
    application.contact_url = payload.contact_url
    application.contact_description = payload.contact_description
    application.recruitment_description = payload.recruitment_description
    application.cover_letter = payload.cover_letter
    application.notes = payload.notes
    application.raw_position_text = payload.raw_position_text
    application.raw_position_source = payload.raw_position_source
    application.expected_salary_min_pln = payload.expected_salary_min_pln
    application.expected_salary_max_pln = payload.expected_salary_max_pln
    application.applied_at = payload.applied_at
    application.last_update_at = payload.last_update_at
    sync_application_tags(session, application, payload.tags)

    if previous_status != next_status:
        next_update_type = update_type_for_status(next_status)
        logger.info(
            "Application status changed application_id=%s previous_status=%s next_status=%s",
            application.id,
            previous_status.value,
            next_status.value,
        )
        session.add(
            ApplicationUpdate(
                application_id=application.id,
                update_type=next_update_type.value,
                title=update_title(next_update_type),
                description=f"{previous_status.value} -> {next_status.value}",
                occurred_at=datetime.now(UTC),
            )
        )

    session.commit()
    session.refresh(application)
    logger.info("Application updated application_id=%s", application.id)
    return to_application_read(application)


@router.patch("/{application_id}/rejection", response_model=ApplicationRead)
def update_application_rejection(
    application_id: int,
    payload: ApplicationRejectionUpdate,
    session: Annotated[Session, Depends(get_session)],
) -> ApplicationRead:
    logger.info("Updating application rejection reason application_id=%s", application_id)
    application = session.get(JobApplication, application_id)
    if application is None:
        logger.warning(
            "Application rejection update target not found application_id=%s",
            application_id,
        )
        raise HTTPException(status_code=404, detail="Application not found")

    previous_status = application.status
    application.rejection_reason = payload.rejection_reason.strip()
    application.status = ApplicationStatus.REJECTED
    application.last_update_at = datetime.now(UTC)
    if previous_status != ApplicationStatus.REJECTED:
        session.add(
            ApplicationUpdate(
                application_id=application.id,
                update_type=ApplicationUpdateType.REJECTED.value,
                title=update_title(ApplicationUpdateType.REJECTED),
                description=f"{previous_status.value} -> {ApplicationStatus.REJECTED.value}",
                occurred_at=datetime.now(UTC),
            )
        )
    session.commit()
    session.refresh(application)
    return to_application_read(application)


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_application(
    application_id: int,
    session: Annotated[Session, Depends(get_session)],
) -> Response:
    logger.info("Deleting application application_id=%s", application_id)
    application = session.get(JobApplication, application_id)
    if application is None:
        logger.warning("Application delete target not found application_id=%s", application_id)
        raise HTTPException(status_code=404, detail="Application not found")

    session.delete(application)
    session.commit()
    logger.info("Application deleted application_id=%s", application_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
