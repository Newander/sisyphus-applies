import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import Session

from backend.config import Settings, get_settings
from backend.db import get_session
from backend.models import GmailMessage
from backend.schemas import GmailMessageRead, GmailStatus, GmailSyncResult, Page
from backend.services.gmail import get_gmail_status, sync_gmail_messages

router = APIRouter(prefix="/api/gmail", tags=["gmail"])
logger = logging.getLogger(__name__)


@router.get("/status", response_model=GmailStatus)
def gmail_status(
    session: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> GmailStatus:
    logger.info("Getting Gmail status")
    status_data = get_gmail_status(session, settings)
    logger.info(
        "Gmail status connected=%s messages_count=%s token_file_exists=%s",
        status_data.connected,
        status_data.messages_count,
        status_data.token_file_exists,
    )
    return status_data


@router.get("/messages", response_model=list[GmailMessageRead])
def list_gmail_messages(
    session: Annotated[Session, Depends(get_session)],
    limit: int = 50,
) -> list[GmailMessageRead]:
    logger.info("Listing Gmail messages limit=%s", limit)
    messages = session.scalars(
        select(GmailMessage).order_by(desc(GmailMessage.internal_date)).limit(limit)
    ).all()
    result = [GmailMessageRead.model_validate(message) for message in messages]
    logger.info("Gmail messages listed count=%s", len(result))
    return result


@router.get("/messages/page", response_model=Page[GmailMessageRead])
def list_gmail_messages_page(
    session: Annotated[Session, Depends(get_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
    sort: str = "internal_date",
    direction: Annotated[str, Query(pattern="^(asc|desc)$")] = "desc",
) -> Page[GmailMessageRead]:
    logger.info(
        "Listing Gmail messages page page=%s page_size=%s sort=%s direction=%s",
        page,
        page_size,
        sort,
        direction,
    )
    sort_columns = {
        "internal_date": GmailMessage.internal_date,
        "sender": GmailMessage.sender,
        "subject": GmailMessage.subject,
    }
    sort_column = sort_columns.get(sort, GmailMessage.internal_date)
    sort_expression = asc(sort_column) if direction == "asc" else desc(sort_column)
    total = session.scalar(select(func.count(GmailMessage.id))) or 0
    messages = session.scalars(
        select(GmailMessage)
        .order_by(sort_expression, desc(GmailMessage.id))
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return Page[GmailMessageRead](
        items=[GmailMessageRead.model_validate(message) for message in messages],
        total=total,
        page=page,
        page_size=page_size,
        sort=sort,
        direction=direction,
    )


@router.delete("/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_gmail_message(
    message_id: int,
    session: Annotated[Session, Depends(get_session)],
) -> Response:
    logger.info("Deleting Gmail message message_id=%s", message_id)
    message = session.get(GmailMessage, message_id)
    if message is None:
        logger.warning("Gmail message delete target not found message_id=%s", message_id)
        raise HTTPException(status_code=404, detail="Gmail message not found")

    session.delete(message)
    session.commit()
    logger.info("Gmail message deleted message_id=%s", message_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/sync", response_model=GmailSyncResult)
def sync_gmail(max_results: int = 50) -> GmailSyncResult:
    logger.info("Starting Gmail sync max_results=%s", max_results)
    try:
        result = sync_gmail_messages(max_results=max_results)
        logger.info(
            "Gmail sync finished imported_count=%s updated_count=%s "
            "scanned_count=%s email_address=%s",
            result.imported_count,
            result.updated_count,
            result.scanned_count,
            result.email_address,
        )
        return result
    except RuntimeError as error:
        logger.warning("Gmail sync blocked error=%s", error)
        raise HTTPException(status_code=409, detail=str(error)) from error
    except FileNotFoundError as error:
        logger.warning("Gmail sync missing file error=%s", error)
        raise HTTPException(status_code=409, detail=str(error)) from error
