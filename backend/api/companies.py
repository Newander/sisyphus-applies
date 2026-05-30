import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Response, status
from sqlalchemy import asc, desc, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.config import Settings, get_settings
from backend.db import get_session
from backend.models import Company, JobApplication
from backend.services.rag import delete_document_index, index_company
from backend.schemas import CompanyCreate, CompanyRead, CompanyUpdate, Page

router = APIRouter(prefix="/api/companies", tags=["companies"])
logger = logging.getLogger(__name__)


def to_company_read(company: Company, applications_count: int = 0) -> CompanyRead:
    return CompanyRead(
        id=company.id,
        name=company.name,
        website=company.website,
        notes=company.notes,
        created_at=company.created_at,
        updated_at=company.updated_at,
        applications_count=applications_count,
    )


@router.get("", response_model=list[CompanyRead])
def list_companies(session: Annotated[Session, Depends(get_session)]) -> list[CompanyRead]:
    logger.info("Listing companies")
    rows = session.execute(
        select(Company, func.count(JobApplication.id))
        .outerjoin(JobApplication, JobApplication.company_id == Company.id)
        .group_by(Company.id)
        .order_by(Company.name)
    ).all()
    companies = [
        to_company_read(company, applications_count)
        for company, applications_count in rows
    ]
    logger.info("Companies listed count=%s", len(companies))
    return companies


@router.get("/page", response_model=Page[CompanyRead])
def list_companies_page(
    session: Annotated[Session, Depends(get_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
    sort: str = "name",
    direction: Annotated[str, Query(pattern="^(asc|desc)$")] = "asc",
) -> Page[CompanyRead]:
    logger.info(
        "Listing companies page page=%s page_size=%s sort=%s direction=%s",
        page,
        page_size,
        sort,
        direction,
    )
    applications_count = func.count(JobApplication.id).label("applications_count")
    sort_columns = {
        "applications_count": applications_count,
        "name": Company.name,
        "updated_at": Company.updated_at,
    }
    sort_column = sort_columns.get(sort, Company.name)
    sort_expression = asc(sort_column) if direction == "asc" else desc(sort_column)
    total = session.scalar(select(func.count(Company.id))) or 0
    rows = session.execute(
        select(Company, applications_count)
        .outerjoin(JobApplication, JobApplication.company_id == Company.id)
        .group_by(Company.id)
        .order_by(sort_expression, asc(Company.id))
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return Page[CompanyRead](
        items=[
            to_company_read(company, count)
            for company, count in rows
        ],
        total=total,
        page=page,
        page_size=page_size,
        sort=sort,
        direction=direction,
    )


@router.post("", response_model=CompanyRead, status_code=status.HTTP_201_CREATED)
def create_company(
    payload: CompanyCreate,
    background_tasks: BackgroundTasks,
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[Session, Depends(get_session)],
) -> CompanyRead:
    logger.info("Creating company name=%s website=%s", payload.name, payload.website)
    company = Company(name=payload.name.strip(), website=payload.website, notes=payload.notes)
    session.add(company)
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        logger.warning("Company create conflict name=%s", payload.name)
        raise HTTPException(
            status_code=409, detail="Company with this name already exists"
        ) from error
    session.refresh(company)
    background_tasks.add_task(index_company, company.id, settings, session)
    logger.info("Company created company_id=%s name=%s", company.id, company.name)
    return to_company_read(company)


@router.get("/{company_id}", response_model=CompanyRead)
def get_company(
    company_id: int,
    session: Annotated[Session, Depends(get_session)],
) -> CompanyRead:
    logger.info("Getting company company_id=%s", company_id)
    company = session.get(Company, company_id)
    if company is None:
        logger.warning("Company not found company_id=%s", company_id)
        raise HTTPException(status_code=404, detail="Company not found")

    applications_count = (
        session.scalar(
            select(func.count(JobApplication.id)).where(JobApplication.company_id == company_id)
        )
        or 0
    )
    return to_company_read(company, applications_count)


@router.put("/{company_id}", response_model=CompanyRead)
def update_company(
    company_id: int,
    payload: CompanyUpdate,
    background_tasks: BackgroundTasks,
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[Session, Depends(get_session)],
) -> CompanyRead:
    logger.info("Updating company company_id=%s name=%s", company_id, payload.name)
    company = session.get(Company, company_id)
    if company is None:
        logger.warning("Company update target not found company_id=%s", company_id)
        raise HTTPException(status_code=404, detail="Company not found")

    company.name = payload.name.strip()
    company.website = payload.website
    company.notes = payload.notes
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        logger.warning("Company update conflict company_id=%s name=%s", company_id, payload.name)
        raise HTTPException(
            status_code=409, detail="Company with this name already exists"
        ) from error
    session.refresh(company)
    background_tasks.add_task(index_company, company.id, settings, session)
    logger.info("Company updated company_id=%s name=%s", company.id, company.name)
    return get_company(company.id, session)


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company(
    company_id: int,
    session: Annotated[Session, Depends(get_session)],
) -> Response:
    logger.info("Deleting company company_id=%s", company_id)
    company = session.get(Company, company_id)
    if company is None:
        logger.warning("Company delete target not found company_id=%s", company_id)
        raise HTTPException(status_code=404, detail="Company not found")

    applications_count = (
        session.scalar(
            select(func.count(JobApplication.id)).where(JobApplication.company_id == company_id)
        )
        or 0
    )
    if applications_count:
        logger.warning(
            "Company delete blocked company_id=%s applications_count=%s",
            company_id,
            applications_count,
        )
        raise HTTPException(status_code=409, detail="Company has applications")

    delete_document_index(f"company:{company_id}", session)
    session.delete(company)
    session.commit()
    logger.info("Company deleted company_id=%s", company_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
