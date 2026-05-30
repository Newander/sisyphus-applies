import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from backend.config import Settings, get_settings
from backend.db import get_session
from backend.services.rag import index_missing

router = APIRouter(prefix="/api/rag", tags=["rag"])
logger = logging.getLogger(__name__)


@router.post("/reindex")
async def reindex_missing(
    background_tasks: BackgroundTasks,
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[Session, Depends(get_session)],
) -> dict:
    background_tasks.add_task(index_missing, settings, session)
    return {"status": "started", "message": "Indexing missing records in background — check logs for progress."}
