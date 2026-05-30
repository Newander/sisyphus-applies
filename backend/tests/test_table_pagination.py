from datetime import UTC, datetime

from fastapi import BackgroundTasks
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.api.applications import (
    create_application,
    list_applications_page,
    update_application_rejection,
)
from backend.config import Settings
from backend.api.companies import list_companies_page
from backend.db import Base
from backend.models import ApplicationStatus, Company, JobApplication
from backend.schemas import ApplicationCreate, ApplicationRejectionUpdate, SeniorityLevel


def make_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_companies_page_sorts_and_paginates() -> None:
    session = make_session()
    session.add_all(
        [
            Company(name="Bravo", website=None, notes=None),
            Company(name="Alpha", website=None, notes=None),
            Company(name="Charlie", website=None, notes=None),
        ]
    )
    session.commit()

    page = list_companies_page(
        session=session,
        page=2,
        page_size=1,
        sort="name",
        direction="asc",
    )

    assert page.total == 3
    assert [company.name for company in page.items] == ["Bravo"]


def test_applications_page_sorts_and_paginates() -> None:
    session = make_session()
    company = Company(name="Acme", website=None, notes=None)
    session.add(company)
    session.flush()
    session.add_all(
        [
            JobApplication(
                company_id=company.id,
                position_title="Bravo",
                status=ApplicationStatus.SENT_CV,
                applied_at=datetime(2026, 5, 2, tzinfo=UTC),
            ),
            JobApplication(
                company_id=company.id,
                position_title="Alpha",
                status=ApplicationStatus.SENT_CV,
                applied_at=datetime(2026, 5, 1, tzinfo=UTC),
            ),
            JobApplication(
                company_id=company.id,
                position_title="Charlie",
                status=ApplicationStatus.SENT_CV,
                applied_at=datetime(2026, 5, 3, tzinfo=UTC),
            ),
        ]
    )
    session.commit()

    page = list_applications_page(
        session=session,
        page=2,
        page_size=1,
        sort="position_title",
        direction="asc",
    )

    assert page.total == 3
    assert [application.position_title for application in page.items] == ["Bravo"]


def test_application_create_persists_seniority_as_field() -> None:
    session = make_session()
    company = Company(name="Acme", website=None, notes=None)
    session.add(company)
    session.flush()

    result = create_application(
        payload=ApplicationCreate(
            company_id=company.id,
            position_title="Backend Engineer",
            status=ApplicationStatus.SENT_CV.value,
            seniority=SeniorityLevel.SENIOR_DEVELOPER,
            notes="Notes without seniority",
            applied_at=datetime(2026, 5, 1, tzinfo=UTC),
        ),
        background_tasks=BackgroundTasks(),
        settings=Settings(_env_file=None),
        session=session,
    )

    application = session.get(JobApplication, result.id)
    assert application is not None
    assert result.seniority == SeniorityLevel.SENIOR_DEVELOPER
    assert application.seniority == SeniorityLevel.SENIOR_DEVELOPER.value
    assert application.notes == "Notes without seniority"


def test_applications_page_excludes_rejected_by_default() -> None:
    session = make_session()
    company = Company(name="Acme", website=None, notes=None)
    session.add(company)
    session.flush()
    session.add_all(
        [
            JobApplication(
                company_id=company.id,
                position_title="Open",
                status=ApplicationStatus.SENT_CV,
                applied_at=datetime(2026, 5, 1, tzinfo=UTC),
            ),
            JobApplication(
                company_id=company.id,
                position_title="Closed",
                status=ApplicationStatus.REJECTED,
                applied_at=datetime(2026, 5, 2, tzinfo=UTC),
            ),
        ]
    )
    session.commit()

    page = list_applications_page(session=session)

    assert page.total == 1
    assert [application.position_title for application in page.items] == ["Open"]


def test_applications_page_can_include_rejected() -> None:
    session = make_session()
    company = Company(name="Acme", website=None, notes=None)
    session.add(company)
    session.flush()
    session.add_all(
        [
            JobApplication(
                company_id=company.id,
                position_title="Open",
                status=ApplicationStatus.SENT_CV,
                applied_at=datetime(2026, 5, 1, tzinfo=UTC),
            ),
            JobApplication(
                company_id=company.id,
                position_title="Closed",
                status=ApplicationStatus.REJECTED,
                applied_at=datetime(2026, 5, 2, tzinfo=UTC),
            ),
        ]
    )
    session.commit()

    page = list_applications_page(session=session, include_closed=True)

    assert page.total == 2
    assert [application.position_title for application in page.items] == ["Closed", "Open"]


def test_application_rejection_reason_can_be_updated() -> None:
    session = make_session()
    company = Company(name="Acme", website=None, notes=None)
    session.add(company)
    session.flush()
    application = JobApplication(
        company_id=company.id,
        position_title="Backend Engineer",
        status=ApplicationStatus.SENT_CV,
        applied_at=datetime(2026, 5, 1, tzinfo=UTC),
    )
    session.add(application)
    session.commit()

    result = update_application_rejection(
        application_id=application.id,
        payload=ApplicationRejectionUpdate(rejection_reason="Position closed"),
        session=session,
    )

    assert result.rejection_reason == "Position closed"
    assert result.status == ApplicationStatus.REJECTED.value
    assert result.last_update_at is not None
