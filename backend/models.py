from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    JSON,
    BigInteger,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db import Base

job_application_tags = Table(
    "job_application_tags",
    Base.metadata,
    Column(
        "application_id",
        Integer,
        ForeignKey("job_applications.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        Integer,
        ForeignKey("application_tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class ApplicationStatus(StrEnum):
    SENT_CV = "sent_cv"
    RECRUITER_CALL = "recruiter_call"
    RECEIVE_RESPONSE = "receive_response"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    INTERVIEW_FINISHED = "interview_finished"
    OFFER = "offer"
    REJECTED = "rejected"


class ApplicationUpdateType(StrEnum):
    SENT_CV = ApplicationStatus.SENT_CV.value
    RECRUITER_CALL = ApplicationStatus.RECRUITER_CALL.value
    RECEIVE_RESPONSE = ApplicationStatus.RECEIVE_RESPONSE.value
    INTERVIEW_SCHEDULED = ApplicationStatus.INTERVIEW_SCHEDULED.value
    INTERVIEW_FINISHED = ApplicationStatus.INTERVIEW_FINISHED.value
    OFFER = ApplicationStatus.OFFER.value
    REJECTED = ApplicationStatus.REJECTED.value


APPLICATION_FLOW = tuple(item.value for item in ApplicationUpdateType)
_ALL_STATUSES = tuple(ApplicationStatus)
APPLICATION_STATUS_TRANSITIONS = {
    status: tuple(s for s in _ALL_STATUSES if s != status) for status in _ALL_STATUSES
}


class DocumentType(StrEnum):
    CV = "cv"
    COVER_LETTER = "cover_letter"
    PORTFOLIO = "portfolio"
    OTHER = "other"


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    website: Mapped[str | None] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    applications: Mapped[list["JobApplication"]] = relationship(back_populates="company")


class ApplicationSource(Base):
    __tablename__ = "application_sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    applications: Mapped[list["JobApplication"]] = relationship(back_populates="application_source")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    file_name: Mapped[str] = mapped_column(String(500), index=True)
    display_name: Mapped[str] = mapped_column(String(500))
    path: Mapped[str] = mapped_column(String(1000), unique=True)
    document_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType, name="document_type"), default=DocumentType.OTHER, nullable=False
    )
    mime_type: Mapped[str | None] = mapped_column(String(255))
    size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    applications: Mapped[list["JobApplication"]] = relationship(back_populates="primary_document")


class JobApplication(Base):
    __tablename__ = "job_applications"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    application_source_id: Mapped[int | None] = mapped_column(ForeignKey("application_sources.id"))
    primary_document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id"))
    position_title: Mapped[str] = mapped_column(String(500), index=True)
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(
            ApplicationStatus,
            name="application_status",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        default=ApplicationStatus.SENT_CV,
        index=True,
        nullable=False,
    )
    source_url: Mapped[str | None] = mapped_column(String(1000))
    position_url: Mapped[str | None] = mapped_column(String(1000))
    rejection_reason: Mapped[str | None] = mapped_column(String(500))
    seniority: Mapped[str | None] = mapped_column(String(100))
    contact_url: Mapped[str | None] = mapped_column(String(1000))
    contact_description: Mapped[str | None] = mapped_column(Text)
    recruitment_description: Mapped[str | None] = mapped_column(Text)
    cover_letter: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    raw_position_text: Mapped[str | None] = mapped_column(Text)
    raw_position_source: Mapped[str | None] = mapped_column(String(50))
    expected_salary_min_pln: Mapped[int | None] = mapped_column(Integer)
    expected_salary_max_pln: Mapped[int | None] = mapped_column(Integer)
    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    last_update_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    company: Mapped[Company] = relationship(back_populates="applications")
    application_source: Mapped[ApplicationSource | None] = relationship(
        back_populates="applications"
    )
    primary_document: Mapped[Document | None] = relationship(back_populates="applications")
    updates: Mapped[list["ApplicationUpdate"]] = relationship(
        back_populates="application", cascade="all, delete-orphan"
    )
    tags: Mapped[list["ApplicationTag"]] = relationship(
        secondary=job_application_tags,
        back_populates="applications",
    )


class ApplicationTag(Base):
    __tablename__ = "application_tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    kind: Mapped[str] = mapped_column(String(100), index=True)
    confidence: Mapped[float | None]
    source: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    applications: Mapped[list["JobApplication"]] = relationship(
        secondary=job_application_tags,
        back_populates="tags",
    )


class ApplicationUpdate(Base):
    __tablename__ = "application_updates"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("job_applications.id", ondelete="CASCADE"), index=True
    )
    update_type: Mapped[str] = mapped_column(String(100), index=True)
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    application: Mapped[JobApplication] = relationship(back_populates="updates")


class FeatureMemory(Base):
    __tablename__ = "feature_memories"

    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(Text)
    page_url: Mapped[str] = mapped_column(String(2000))
    page_title: Mapped[str | None] = mapped_column(String(500))
    screenshot_data_url: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)


class GmailAccount(Base):
    __tablename__ = "gmail_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    email_address: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    history_id: Mapped[str | None] = mapped_column(String(100))
    connected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    messages: Mapped[list["GmailMessage"]] = relationship(back_populates="account")


class Prompt(Base):
    __tablename__ = "prompts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class GmailMessage(Base):
    __tablename__ = "gmail_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("gmail_accounts.id"), index=True)
    gmail_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    thread_id: Mapped[str] = mapped_column(String(255), index=True)
    history_id: Mapped[str | None] = mapped_column(String(100))
    sender: Mapped[str | None] = mapped_column(String(1000), index=True)
    recipients: Mapped[str | None] = mapped_column(Text)
    subject: Mapped[str | None] = mapped_column(String(1000), index=True)
    snippet: Mapped[str | None] = mapped_column(Text)
    body_text: Mapped[str | None] = mapped_column(Text)
    label_ids: Mapped[list[str] | None] = mapped_column(JSON)
    internal_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    raw_payload: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    account: Mapped[GmailAccount] = relationship(back_populates="messages")
