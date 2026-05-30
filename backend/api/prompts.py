import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.db import get_session
from backend.models import Prompt
from backend.schemas import PromptCreate, PromptRead, PromptUpdate

router = APIRouter(prefix="/api/prompts", tags=["prompts"])
logger = logging.getLogger(__name__)


def to_prompt_read(prompt: Prompt) -> PromptRead:
    return PromptRead(
        id=prompt.id,
        name=prompt.name,
        description=prompt.description,
        content=prompt.content,
        created_at=prompt.created_at,
        updated_at=prompt.updated_at,
    )


@router.get("", response_model=list[PromptRead])
def list_prompts(session: Annotated[Session, Depends(get_session)]) -> list[PromptRead]:
    logger.info("Listing prompts")
    prompts = session.scalars(select(Prompt).order_by(Prompt.name)).all()
    return [to_prompt_read(p) for p in prompts]


@router.get("/{prompt_id}", response_model=PromptRead)
def get_prompt(
    prompt_id: int,
    session: Annotated[Session, Depends(get_session)],
) -> PromptRead:
    prompt = session.get(Prompt, prompt_id)
    if prompt is None:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return to_prompt_read(prompt)


@router.post("", response_model=PromptRead, status_code=status.HTTP_201_CREATED)
def create_prompt(
    payload: PromptCreate,
    session: Annotated[Session, Depends(get_session)],
) -> PromptRead:
    logger.info("Creating prompt name=%s", payload.name)
    existing = session.scalar(select(Prompt).where(Prompt.name == payload.name))
    if existing is not None:
        raise HTTPException(status_code=409, detail="Prompt with this name already exists")
    prompt = Prompt(
        name=payload.name.strip(),
        description=payload.description.strip() if payload.description else None,
        content=payload.content,
    )
    session.add(prompt)
    session.commit()
    session.refresh(prompt)
    return to_prompt_read(prompt)


@router.put("/{prompt_id}", response_model=PromptRead)
def update_prompt(
    prompt_id: int,
    payload: PromptUpdate,
    session: Annotated[Session, Depends(get_session)],
) -> PromptRead:
    logger.info("Updating prompt prompt_id=%s", prompt_id)
    prompt = session.get(Prompt, prompt_id)
    if prompt is None:
        raise HTTPException(status_code=404, detail="Prompt not found")
    prompt.description = payload.description.strip() if payload.description else None
    prompt.content = payload.content
    session.commit()
    session.refresh(prompt)
    return to_prompt_read(prompt)


@router.delete("/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_prompt(
    prompt_id: int,
    session: Annotated[Session, Depends(get_session)],
) -> Response:
    logger.info("Deleting prompt prompt_id=%s", prompt_id)
    prompt = session.get(Prompt, prompt_id)
    if prompt is None:
        raise HTTPException(status_code=404, detail="Prompt not found")
    session.delete(prompt)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
