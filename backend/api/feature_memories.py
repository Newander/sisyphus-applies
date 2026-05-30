import logging
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import Session

from backend.db import get_session
from backend.models import FeatureMemory
from backend.schemas import FeatureMemoryCreate, FeatureMemoryRead, FeatureMemoryUpdate, Page

router = APIRouter(prefix="/api/feature-memories", tags=["feature-memories"])
logger = logging.getLogger(__name__)


def to_feature_memory_read(memory: FeatureMemory) -> FeatureMemoryRead:
    return FeatureMemoryRead(
        id=memory.id,
        text=memory.text,
        page_url=memory.page_url,
        page_title=memory.page_title,
        screenshot_data_url=memory.screenshot_data_url,
        created_at=memory.created_at,
        closed_at=memory.closed_at,
    )


@router.get("", response_model=list[FeatureMemoryRead])
def list_feature_memories(
    session: Annotated[Session, Depends(get_session)],
) -> list[FeatureMemoryRead]:
    logger.info("Listing open feature memories")
    memories = session.scalars(
        select(FeatureMemory)
        .where(FeatureMemory.closed_at.is_(None))
        .order_by(desc(FeatureMemory.created_at))
    ).all()
    return [to_feature_memory_read(memory) for memory in memories]


@router.get("/page", response_model=Page[FeatureMemoryRead])
def list_feature_memories_page(
    session: Annotated[Session, Depends(get_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
    sort: str = "created_at",
    direction: Annotated[str, Query(pattern="^(asc|desc)$")] = "desc",
) -> Page[FeatureMemoryRead]:
    logger.info(
        "Listing feature memories page page=%s page_size=%s sort=%s direction=%s",
        page,
        page_size,
        sort,
        direction,
    )
    sort_columns = {
        "created_at": FeatureMemory.created_at,
        "page_url": FeatureMemory.page_url,
        "text": FeatureMemory.text,
    }
    sort_column = sort_columns.get(sort, FeatureMemory.created_at)
    sort_expression = asc(sort_column) if direction == "asc" else desc(sort_column)
    base_filter = FeatureMemory.closed_at.is_(None)
    total = session.scalar(select(func.count(FeatureMemory.id)).where(base_filter)) or 0
    memories = session.scalars(
        select(FeatureMemory)
        .where(base_filter)
        .order_by(sort_expression, desc(FeatureMemory.id))
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return Page[FeatureMemoryRead](
        items=[to_feature_memory_read(memory) for memory in memories],
        total=total,
        page=page,
        page_size=page_size,
        sort=sort,
        direction=direction,
    )


@router.post("", response_model=FeatureMemoryRead, status_code=status.HTTP_201_CREATED)
def create_feature_memory(
    payload: FeatureMemoryCreate,
    session: Annotated[Session, Depends(get_session)],
) -> FeatureMemoryRead:
    logger.info("Creating feature memory page_url=%s", payload.page_url)
    memory = FeatureMemory(
        text=payload.text.strip(),
        page_url=str(payload.page_url),
        page_title=payload.page_title.strip() if payload.page_title else None,
        screenshot_data_url=payload.screenshot_data_url,
    )
    session.add(memory)
    session.commit()
    session.refresh(memory)
    return to_feature_memory_read(memory)


@router.get("/{memory_id}", response_model=FeatureMemoryRead)
def get_feature_memory(
    memory_id: int,
    session: Annotated[Session, Depends(get_session)],
) -> FeatureMemoryRead:
    memory = session.get(FeatureMemory, memory_id)
    if memory is None:
        raise HTTPException(status_code=404, detail="Feature memory not found")
    return to_feature_memory_read(memory)


@router.patch("/{memory_id}", response_model=FeatureMemoryRead)
def update_feature_memory(
    memory_id: int,
    payload: FeatureMemoryUpdate,
    session: Annotated[Session, Depends(get_session)],
) -> FeatureMemoryRead:
    logger.info("Updating feature memory memory_id=%s", memory_id)
    memory = session.get(FeatureMemory, memory_id)
    if memory is None:
        raise HTTPException(status_code=404, detail="Feature memory not found")

    memory.text = payload.text.strip()
    memory.page_title = payload.page_title.strip() if payload.page_title else None
    session.commit()
    session.refresh(memory)
    return to_feature_memory_read(memory)


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
def close_feature_memory(
    memory_id: int,
    session: Annotated[Session, Depends(get_session)],
) -> Response:
    logger.info("Closing feature memory memory_id=%s", memory_id)
    memory = session.get(FeatureMemory, memory_id)
    if memory is None:
        raise HTTPException(status_code=404, detail="Feature memory not found")

    memory.closed_at = datetime.now(UTC)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
