from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.config import get_settings
from backend.db import SessionLocal
from backend.migrations import upgrade_database
from backend.models import (
    ApplicationStatus,
    ApplicationUpdate,
    ApplicationUpdateType,
    Company,
    JobApplication,
)

SEED_COMPANIES = [
    {
        "name": "Northstar Labs",
        "website": "https://northstar.example",
        "notes": "Backend platform team, Python-heavy role.",
        "applications": [
            {
                "position_title": "Senior Backend Engineer",
                "status": ApplicationStatus.INTERVIEW_SCHEDULED,
                "source_url": "https://northstar.example/jobs/backend",
                "days_ago": 6,
                "updates": [
                    (ApplicationUpdateType.SENT_CV, "CV sent", 6),
                    (ApplicationUpdateType.RECRUITER_CALL, "Recruiter call", 4),
                    (ApplicationUpdateType.RECEIVE_RESPONSE, "Response received", 3),
                    (ApplicationUpdateType.INTERVIEW_SCHEDULED, "Interview scheduled", 2),
                ],
            }
        ],
    },
    {
        "name": "BrightHire",
        "website": "https://brighthire.example",
        "notes": "SaaS product with strong data workflows.",
        "applications": [
            {
                "position_title": "Python Developer",
                "status": ApplicationStatus.SENT_CV,
                "source_url": "https://brighthire.example/careers/python",
                "days_ago": 2,
                "updates": [(ApplicationUpdateType.SENT_CV, "CV sent", 2)],
            }
        ],
    },
    {
        "name": "Helio Systems",
        "website": "https://helio.example",
        "notes": "Interesting calendar/email automation domain.",
        "applications": [
            {
                "position_title": "Full Stack Engineer",
                "status": ApplicationStatus.RECEIVE_RESPONSE,
                "source_url": "https://helio.example/jobs/full-stack",
                "days_ago": 21,
                "updates": [
                    (ApplicationUpdateType.SENT_CV, "CV sent", 21),
                    (ApplicationUpdateType.RECEIVE_RESPONSE, "Response received", 9),
                ],
            }
        ],
    },
]


def ensure_sample_documents() -> None:
    storage_dir = get_settings().storage_dir
    storage_dir.mkdir(parents=True, exist_ok=True)
    samples = {
        "cv_backend_2026.md": "# Backend CV\n\nSeed document for dashboard testing.\n",
        "cover_letter_northstar.md": "# Cover Letter\n\nSeed document for dashboard testing.\n",
    }

    for file_name, content in samples.items():
        path = storage_dir / file_name
        if not path.exists():
            path.write_text(content, encoding="utf-8")


def get_or_create_company(session: Session, payload: dict) -> Company:
    company = session.scalar(select(Company).where(Company.name == payload["name"]))
    if company is not None:
        return company

    company = Company(name=payload["name"], website=payload["website"], notes=payload["notes"])
    session.add(company)
    session.flush()
    return company


def application_exists(session: Session, company: Company, position_title: str) -> bool:
    return (
        session.scalar(
            select(JobApplication.id).where(
                JobApplication.company_id == company.id,
                JobApplication.position_title == position_title,
            )
        )
        is not None
    )


def seed_database() -> None:
    upgrade_database()
    ensure_sample_documents()
    now = datetime.now(UTC)

    with SessionLocal() as session:
        for company_payload in SEED_COMPANIES:
            company = get_or_create_company(session, company_payload)
            for application_payload in company_payload["applications"]:
                if application_exists(session, company, application_payload["position_title"]):
                    continue

                applied_at = now - timedelta(days=application_payload["days_ago"])
                application = JobApplication(
                    company_id=company.id,
                    position_title=application_payload["position_title"],
                    status=application_payload["status"],
                    source_url=application_payload["source_url"],
                    notes="Seed application. Replace with real data when ready.",
                    applied_at=applied_at,
                    last_update_at=applied_at,
                )
                session.add(application)
                session.flush()

                for update_type, title, days_ago in application_payload["updates"]:
                    occurred_at = now - timedelta(days=days_ago)
                    session.add(
                        ApplicationUpdate(
                            application_id=application.id,
                            update_type=update_type.value,
                            title=title,
                            description=None,
                            occurred_at=occurred_at,
                        )
                    )
                    application.last_update_at = occurred_at

        session.commit()


if __name__ == "__main__":
    seed_database()
    print("Seed data is ready.")
