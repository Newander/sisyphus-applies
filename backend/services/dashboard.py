import logging
from datetime import UTC, datetime, time, timedelta

from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import Session

from backend.config import Settings
from backend.models import ApplicationUpdate, Company, JobApplication
from backend.schemas import (
    DashboardResponse,
    DashboardStats,
    RecentCompany,
    SeniorityCount,
    TimelinePoint,
)
from backend.services.documents import list_storage_documents

logger = logging.getLogger(__name__)


def list_seniority_counts(
    session: Session,
    *,
    since: datetime | None = None,
) -> list[SeniorityCount]:
    count_label = func.count(JobApplication.id).label("applications_count")
    query = select(JobApplication.seniority, count_label).group_by(JobApplication.seniority)
    if since is not None:
        query = query.where(JobApplication.applied_at >= since)

    rows = session.execute(
        query.order_by(desc(count_label), asc(JobApplication.seniority))
    ).all()
    return [
        SeniorityCount(
            seniority=seniority,
            count=count,
        )
        for seniority, count in rows
    ]


def get_dashboard(session: Session, settings: Settings) -> DashboardResponse:
    now = datetime.now(UTC)
    today_start = datetime.combine(now.date(), time.min, tzinfo=UTC)
    since = now - timedelta(days=30)
    logger.debug(
        "Building dashboard today_start=%s since=%s storage_dir=%s",
        today_start,
        since,
        settings.storage_dir,
    )

    applications_total = session.scalar(select(func.count(JobApplication.id))) or 0
    updates_total = session.scalar(select(func.count(ApplicationUpdate.id))) or 0
    applications_today = (
        session.scalar(
            select(func.count(JobApplication.id)).where(JobApplication.applied_at >= today_start)
        )
        or 0
    )
    updates_today = (
        session.scalar(
            select(func.count(ApplicationUpdate.id)).where(
                ApplicationUpdate.occurred_at >= today_start
            )
        )
        or 0
    )
    applications_last_30_days = (
        session.scalar(
            select(func.count(JobApplication.id)).where(JobApplication.applied_at >= since)
        )
        or 0
    )
    updates_last_30_days = (
        session.scalar(
            select(func.count(ApplicationUpdate.id)).where(ApplicationUpdate.occurred_at >= since)
        )
        or 0
    )

    recent_rows = session.execute(
        select(JobApplication, Company)
        .join(Company, JobApplication.company_id == Company.id)
        .order_by(desc(JobApplication.created_at), desc(JobApplication.id))
        .limit(5)
    ).all()

    counts = dict(
        session.execute(
            select(JobApplication.company_id, func.count(JobApplication.id)).group_by(
                JobApplication.company_id
            )
        ).all()
    )

    recent_companies = [
        RecentCompany(
            company_id=company.id,
            latest_application_id=application.id,
            company_name=company.name,
            applications_count=counts.get(company.id, 0),
            latest_position=application.position_title,
            latest_status=application.status.value,
            latest_added_at=application.created_at,
            latest_applied_at=application.applied_at,
        )
        for application, company in recent_rows
    ]

    timeline_start = now - timedelta(days=29)
    apps_by_day = dict(
        session.execute(
            select(func.date(JobApplication.applied_at), func.count(JobApplication.id))
            .where(JobApplication.applied_at >= timeline_start)
            .group_by(func.date(JobApplication.applied_at))
        ).all()
    )
    updates_by_day = dict(
        session.execute(
            select(func.date(ApplicationUpdate.occurred_at), func.count(ApplicationUpdate.id))
            .where(ApplicationUpdate.occurred_at >= timeline_start)
            .group_by(func.date(ApplicationUpdate.occurred_at))
        ).all()
    )
    timeline = [
        TimelinePoint(
            date=(now.date() - timedelta(days=29 - i)).isoformat(),
            applications=apps_by_day.get(now.date() - timedelta(days=29 - i), 0),
            updates=updates_by_day.get(now.date() - timedelta(days=29 - i), 0),
        )
        for i in range(30)
    ]

    documents = list_storage_documents(settings.storage_dir)
    logger.debug(
        "Dashboard values applications_total=%s updates_total=%s recent_companies=%s documents=%s",
        applications_total,
        updates_total,
        len(recent_companies),
        len(documents),
    )
    return DashboardResponse(
        stats=DashboardStats(
            applications_total=applications_total,
            updates_total=updates_total,
            applications_today=applications_today,
            updates_today=updates_today,
            applications_last_30_days=applications_last_30_days,
            updates_last_30_days=updates_last_30_days,
        ),
        seniority_all_time=list_seniority_counts(session),
        seniority_today=list_seniority_counts(session, since=today_start),
        recent_companies=recent_companies,
        documents=documents,
        storage_dir=str(settings.storage_dir),
        timeline=timeline,
    )


def list_recent_companies_page(
    session: Session,
    *,
    page: int,
    page_size: int,
    sort: str,
    direction: str,
) -> tuple[list[RecentCompany], int]:
    counts = dict(
        session.execute(
            select(JobApplication.company_id, func.count(JobApplication.id)).group_by(
                JobApplication.company_id
            )
        ).all()
    )
    sort_columns = {
        "company_name": Company.name,
        "latest_added_at": JobApplication.created_at,
        "latest_position": JobApplication.position_title,
        "latest_status": JobApplication.status,
    }
    sort_column = sort_columns.get(sort, JobApplication.created_at)
    sort_expression = asc(sort_column) if direction == "asc" else desc(sort_column)
    total = session.scalar(select(func.count(JobApplication.id))) or 0
    rows = session.execute(
        select(JobApplication, Company)
        .join(Company, JobApplication.company_id == Company.id)
        .order_by(sort_expression, desc(JobApplication.id))
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return [
        RecentCompany(
            company_id=company.id,
            latest_application_id=application.id,
            company_name=company.name,
            applications_count=counts.get(company.id, 0),
            latest_position=application.position_title,
            latest_status=application.status.value,
            latest_added_at=application.created_at,
            latest_applied_at=application.applied_at,
        )
        for application, company in rows
    ], total
