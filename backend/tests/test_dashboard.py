from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

import backend.services.dashboard as dashboard_service
from backend.config import Settings
from backend.db import Base
from backend.models import ApplicationStatus, ApplicationUpdate, Company, JobApplication
from backend.services.dashboard import get_dashboard, list_recent_companies_page


def make_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def add_application(
    session: Session,
    company: Company,
    position_title: str,
    created_at: datetime,
    applied_at: datetime | None = None,
    seniority: str | None = None,
) -> JobApplication:
    application = JobApplication(
        company_id=company.id,
        position_title=position_title,
        status=ApplicationStatus.SENT_CV,
        seniority=seniority,
        applied_at=applied_at or created_at - timedelta(days=7),
        created_at=created_at,
    )
    session.add(application)
    session.flush()
    return application


def test_dashboard_returns_last_five_positions_by_created_at(tmp_path: Path) -> None:
    session = make_session()
    first_company = Company(name="Acme", website=None, notes=None)
    second_company = Company(name="Globex", website=None, notes=None)
    session.add_all([first_company, second_company])
    session.flush()

    base_time = datetime(2026, 5, 25, 12, tzinfo=UTC)
    applications = [
        add_application(
            session=session,
            company=first_company if index % 2 == 0 else second_company,
            position_title=f"Position {index}",
            created_at=base_time + timedelta(minutes=index),
        )
        for index in range(7)
    ]
    session.commit()

    dashboard = get_dashboard(session, Settings(job_tracker_storage_dir=tmp_path))

    assert [item.latest_application_id for item in dashboard.recent_companies] == [
        application.id for application in reversed(applications[2:])
    ]
    assert len(dashboard.recent_companies) == 5
    assert [item.latest_position for item in dashboard.recent_companies] == [
        "Position 6",
        "Position 5",
        "Position 4",
        "Position 3",
        "Position 2",
    ]
    assert [item.company_name for item in dashboard.recent_companies].count("Acme") == 3
    assert dashboard.recent_companies[0].latest_added_at == applications[6].created_at
    assert dashboard.recent_companies[0].applications_count == 4


def test_recent_companies_page_sorts_and_paginates(tmp_path: Path) -> None:
    session = make_session()
    company = Company(name="Acme", website=None, notes=None)
    session.add(company)
    session.flush()
    base_time = datetime(2026, 5, 25, 12, tzinfo=UTC)
    applications = [
        add_application(session, company, f"Position {index}", base_time + timedelta(minutes=index))
        for index in range(3)
    ]
    session.commit()

    items, total = list_recent_companies_page(
        session,
        page=2,
        page_size=1,
        sort="latest_added_at",
        direction="desc",
    )

    assert total == 3
    assert [item.latest_application_id for item in items] == [applications[1].id]


def test_dashboard_counts_today_stats(tmp_path: Path, monkeypatch) -> None:
    fixed_now = datetime(2026, 5, 26, 15, 30, tzinfo=UTC)

    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_now if tz is not None else fixed_now.replace(tzinfo=None)

    monkeypatch.setattr(dashboard_service, "datetime", FixedDatetime)

    session = make_session()
    company = Company(name="Acme", website=None, notes=None)
    session.add(company)
    session.flush()

    today_application = add_application(session, company, "Today", fixed_now, fixed_now)
    add_application(session, company, "Yesterday", fixed_now - timedelta(days=1))
    session.add_all(
        [
            ApplicationUpdate(
                application_id=today_application.id,
                update_type="status",
                title="Today update",
                description=None,
                occurred_at=fixed_now,
            ),
            ApplicationUpdate(
                application_id=today_application.id,
                update_type="status",
                title="Yesterday update",
                description=None,
                occurred_at=fixed_now - timedelta(days=1),
            ),
        ]
    )
    session.commit()

    dashboard = get_dashboard(session, Settings(job_tracker_storage_dir=tmp_path))

    assert dashboard.stats.applications_today == 1
    assert dashboard.stats.updates_today == 1
    assert dashboard.stats.applications_last_30_days == 2
    assert dashboard.stats.updates_last_30_days == 2


def test_dashboard_counts_seniority_for_all_time_and_today(tmp_path: Path, monkeypatch) -> None:
    fixed_now = datetime(2026, 5, 26, 15, 30, tzinfo=UTC)

    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_now if tz is not None else fixed_now.replace(tzinfo=None)

    monkeypatch.setattr(dashboard_service, "datetime", FixedDatetime)

    session = make_session()
    company = Company(name="Acme", website=None, notes=None)
    session.add(company)
    session.flush()

    add_application(session, company, "Senior today", fixed_now, fixed_now, "Senior Developer")
    add_application(
        session,
        company,
        "Senior yesterday",
        fixed_now,
        fixed_now - timedelta(days=1),
        "Senior Developer",
    )
    add_application(session, company, "Middle today", fixed_now, fixed_now, "Middle Developer")
    add_application(session, company, "Unknown today", fixed_now, fixed_now, None)
    session.commit()

    dashboard = get_dashboard(session, Settings(job_tracker_storage_dir=tmp_path))

    assert [(item.seniority, item.count) for item in dashboard.seniority_all_time] == [
        ("Senior Developer", 2),
        (None, 1),
        ("Middle Developer", 1),
    ]
    assert [(item.seniority, item.count) for item in dashboard.seniority_today] == [
        (None, 1),
        ("Middle Developer", 1),
        ("Senior Developer", 1),
    ]
