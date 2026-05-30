import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.db import get_session
from backend.models import ApplicationSource, JobApplication
from backend.schemas import ApplicationSourceCreate, ApplicationSourceRead

router = APIRouter(prefix="/api/application-sources", tags=["application-sources"])
logger = logging.getLogger(__name__)


def to_application_source_read(
    source: ApplicationSource,
    applications_count: int = 0,
) -> ApplicationSourceRead:
    return ApplicationSourceRead(
        id=source.id,
        name=source.name,
        created_at=source.created_at,
        updated_at=source.updated_at,
        applications_count=applications_count,
    )


@router.get("", response_model=list[ApplicationSourceRead])
def list_application_sources(
    session: Annotated[Session, Depends(get_session)],
) -> list[ApplicationSourceRead]:
    logger.info("Listing application sources")
    rows = session.execute(
        select(ApplicationSource, func.count(JobApplication.id))
        .outerjoin(JobApplication, JobApplication.application_source_id == ApplicationSource.id)
        .group_by(ApplicationSource.id)
        .order_by(ApplicationSource.name)
    ).all()
    sources = [
        to_application_source_read(source, applications_count)
        for source, applications_count in rows
    ]
    logger.info("Application sources listed count=%s", len(sources))
    return sources


@router.post("", response_model=ApplicationSourceRead, status_code=status.HTTP_201_CREATED)
def create_application_source(
    payload: ApplicationSourceCreate,
    session: Annotated[Session, Depends(get_session)],
) -> ApplicationSourceRead:
    logger.info("Creating application source name=%s", payload.name)
    source = ApplicationSource(name=payload.name.strip())
    session.add(source)
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        logger.warning("Application source create conflict name=%s", payload.name)
        raise HTTPException(
            status_code=409, detail="Application source with this name already exists"
        ) from error
    session.refresh(source)
    logger.info("Application source created source_id=%s name=%s", source.id, source.name)
    return to_application_source_read(source)


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_application_source(
    source_id: int,
    session: Annotated[Session, Depends(get_session)],
) -> Response:
    logger.info("Deleting application source source_id=%s", source_id)
    source = session.get(ApplicationSource, source_id)
    if source is None:
        logger.warning("Application source delete target not found source_id=%s", source_id)
        raise HTTPException(status_code=404, detail="Application source not found")

    applications_count = (
        session.scalar(
            select(func.count(JobApplication.id)).where(
                JobApplication.application_source_id == source_id
            )
        )
        or 0
    )
    if applications_count:
        logger.warning(
            "Application source delete blocked source_id=%s applications_count=%s",
            source_id,
            applications_count,
        )
        raise HTTPException(status_code=409, detail="Application source has applications")

    session.delete(source)
    session.commit()
    logger.info("Application source deleted source_id=%s", source_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
