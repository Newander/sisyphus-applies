import logging
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from backend.config import Settings, get_settings
from backend.db import get_session
from backend.models import Company
from backend.schemas import DocumentCreate, DocumentItem, DocumentPreview, Page
from backend.services.documents import (
    create_text_document,
    get_storage_document,
    list_storage_documents,
    list_storage_documents_page,
    read_document_preview,
    resolve_storage_document_path,
    send_document_to_recycle_bin,
)
from backend.services.ssh_sync import (
    make_sync_config,
    push_file,
    remove_from_manifest,
    sync_documents,
)

router = APIRouter(prefix="/api/documents", tags=["documents"])
logger = logging.getLogger(__name__)


@router.get("", response_model=list[DocumentItem])
def list_documents(settings: Annotated[Settings, Depends(get_settings)]) -> list[DocumentItem]:
    logger.info("Listing documents storage_dir=%s", settings.storage_dir)
    documents = list_storage_documents(settings.storage_dir, limit=None)
    logger.info("Documents listed count=%s", len(documents))
    return documents


@router.get("/page", response_model=Page[DocumentItem])
def list_documents_page(
    settings: Annotated[Settings, Depends(get_settings)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
    sort: str = "modified_at",
    direction: Annotated[str, Query(pattern="^(asc|desc)$")] = "desc",
) -> Page[DocumentItem]:
    logger.info(
        "Listing documents page page=%s page_size=%s sort=%s direction=%s",
        page,
        page_size,
        sort,
        direction,
    )
    documents, total = list_storage_documents_page(
        settings.storage_dir,
        page=page,
        page_size=page_size,
        sort=sort,
        direction=direction,
    )
    return Page[DocumentItem](
        items=documents,
        total=total,
        page=page,
        page_size=page_size,
        sort=sort,
        direction=direction,
    )


@router.post("", response_model=DocumentItem, status_code=status.HTTP_201_CREATED)
def create_document(
    payload: DocumentCreate,
    background_tasks: BackgroundTasks,
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[Session, Depends(get_session)],
) -> DocumentItem:
    logger.info(
        "Creating document file_name=%s document_type=%s company_id=%s storage_dir=%s",
        payload.file_name,
        payload.document_type,
        payload.company_id,
        settings.storage_dir,
    )
    company_name = None
    if payload.company_id is not None:
        company = session.get(Company, payload.company_id)
        if company is None:
            logger.warning(
                "Document create references missing company company_id=%s",
                payload.company_id,
            )
            raise HTTPException(status_code=422, detail="Company does not exist")
        company_name = company.name

    try:
        document = create_text_document(
            settings.storage_dir,
            file_name=payload.file_name,
            text=payload.text,
            document_type=payload.document_type,
            company_id=payload.company_id,
            company_name=company_name,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except FileExistsError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error

    logger.info("Document created path=%s", document.path)
    sync_config = make_sync_config(settings)
    if sync_config is not None:
        relative = Path(document.path).relative_to(settings.storage_dir).as_posix()
        background_tasks.add_task(push_file, settings.storage_dir, sync_config, relative)
    return document


@router.get("/{document_id}", response_model=DocumentItem)
def get_document(
    document_id: str,
    settings: Annotated[Settings, Depends(get_settings)],
) -> DocumentItem:
    logger.info("Getting document document_id=%s storage_dir=%s", document_id, settings.storage_dir)
    document = get_storage_document(settings.storage_dir, document_id)
    if document is None:
        logger.warning("Document not found document_id=%s", document_id)
        raise HTTPException(status_code=404, detail="Document not found")
    logger.info("Document found document_id=%s path=%s", document_id, document.path)
    return document


@router.get("/{document_id}/preview", response_model=DocumentPreview)
def get_document_preview(
    document_id: str,
    settings: Annotated[Settings, Depends(get_settings)],
) -> DocumentPreview:
    logger.info(
        "Getting document preview document_id=%s storage_dir=%s",
        document_id,
        settings.storage_dir,
    )
    document_path = resolve_storage_document_path(settings.storage_dir, document_id)
    if document_path is None:
        logger.warning("Document not found for preview document_id=%s", document_id)
        raise HTTPException(status_code=404, detail="Document not found")
    return read_document_preview(document_path)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: str,
    background_tasks: BackgroundTasks,
    settings: Annotated[Settings, Depends(get_settings)],
) -> Response:
    logger.info(
        "Deleting document document_id=%s storage_dir=%s",
        document_id,
        settings.storage_dir,
    )
    document_path = resolve_storage_document_path(settings.storage_dir, document_id)
    if document_path is None:
        logger.warning("Document not found for delete document_id=%s", document_id)
        raise HTTPException(status_code=404, detail="Document not found")

    relative = document_path.relative_to(settings.storage_dir).as_posix()

    try:
        send_document_to_recycle_bin(document_path)
    except RuntimeError as exc:
        logger.exception(
            "Failed to delete document document_id=%s path=%s",
            document_id,
            document_path,
        )
        raise HTTPException(status_code=501, detail=str(exc)) from exc

    remove_from_manifest(settings.storage_dir, relative)
    sync_config = make_sync_config(settings)
    if sync_config is not None:
        background_tasks.add_task(sync_documents, settings.storage_dir, sync_config)
    logger.info("Document moved to recycle bin document_id=%s path=%s", document_id, document_path)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
