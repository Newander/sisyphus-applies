from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


class Page[T](BaseModel):
    items: list[T]
    total: int
    page: int
    page_size: int
    sort: str
    direction: Literal["asc", "desc"]


class SeniorityLevel(StrEnum):
    MIDDLE_DEVELOPER = "Middle Developer"
    SENIOR_DEVELOPER = "Senior Developer"
    PRINCIPAL_DEVELOPER = "Principal Developer"
    MIDDLE_DATA_ENGINEER = "Middle Data Engineer"
    SENIOR_DATA_ENGINEER = "Senior Data Engineer"
    PRINCIPAL_DATA_ENGINEER = "Principal Data Engineer"
    SOFTWARE_ARCHITECT = "Software Architect"
    DATA_ARCHITECT = "Data Architect"
    MIDDLE_MANAGER = "Middle Manager"
    SENIOR_MANAGER = "Senior Manager"


class DashboardStats(BaseModel):
    applications_total: int
    updates_total: int
    applications_today: int
    updates_today: int
    applications_last_30_days: int
    updates_last_30_days: int


class SeniorityCount(BaseModel):
    seniority: str | None
    count: int


class RecentCompany(BaseModel):
    company_id: int
    latest_application_id: int
    company_name: str
    applications_count: int
    latest_position: str
    latest_status: str
    latest_added_at: datetime
    latest_applied_at: datetime


class DocumentItem(BaseModel):
    id: str
    name: str
    path: str
    size_bytes: int
    modified_at: datetime
    document_type: str = "other"
    company_id: int | None = None
    company_name: str | None = None


class DocumentCreate(BaseModel):
    file_name: str = Field(min_length=1, max_length=255)
    text: str = Field(min_length=1)
    document_type: Literal["cv", "cover_letter", "other"]
    company_id: int | None = None


class DocumentPreview(BaseModel):
    lines: list[str]
    line_count: int
    truncated: bool
    unsupported_reason: str | None = None


class TimelinePoint(BaseModel):
    date: str
    applications: int
    updates: int


class DashboardResponse(BaseModel):
    stats: DashboardStats
    seniority_all_time: list[SeniorityCount]
    seniority_today: list[SeniorityCount]
    recent_companies: list[RecentCompany]
    documents: list[DocumentItem]
    storage_dir: str
    timeline: list[TimelinePoint]


class CodexStatusResponse(BaseModel):
    command: list[str]
    cwd: str
    timeout_seconds: int


class CodexAskRequest(BaseModel):
    mode: Literal["text", "url"] = "text"
    question: str = Field(min_length=1, max_length=8000)
    context: str | None = Field(default=None, max_length=12000)
    context_url: str | None = Field(default=None, max_length=1000)


class CodexAskResponse(BaseModel):
    answer: str
    stderr: str | None = None
    context_source: str
    warnings: list[str] = Field(default_factory=list)


class FeatureMemoryCreate(BaseModel):
    text: str = Field(min_length=1, max_length=8000)
    page_url: HttpUrl
    page_title: str | None = Field(default=None, max_length=500)
    screenshot_data_url: str = Field(min_length=1)


class FeatureMemoryUpdate(BaseModel):
    text: str = Field(min_length=1, max_length=8000)
    page_title: str | None = Field(default=None, max_length=500)


class FeatureMemoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    page_url: str
    page_title: str | None = None
    screenshot_data_url: str
    created_at: datetime
    closed_at: datetime | None = None


class CompanyBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    website: str | None = Field(default=None, max_length=500)
    notes: str | None = None


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(CompanyBase):
    pass


class CompanyRead(CompanyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    applications_count: int = 0


class ApplicationSourceBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class ApplicationSourceCreate(ApplicationSourceBase):
    pass


class ApplicationSourceRead(ApplicationSourceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    applications_count: int = 0


class ApplicationBase(BaseModel):
    company_id: int
    application_source_id: int | None = None
    primary_document_id: int | None = None
    position_title: str = Field(min_length=1, max_length=500)
    status: str = "sent_cv"
    source_url: str | None = Field(default=None, max_length=1000)
    position_url: str | None = Field(default=None, max_length=1000)
    rejection_reason: str | None = Field(default=None, max_length=500)
    seniority: SeniorityLevel | None = None
    contact_url: str | None = Field(default=None, max_length=1000)
    contact_description: str | None = None
    recruitment_description: str | None = None
    cover_letter: str | None = None
    notes: str | None = None
    raw_position_text: str | None = None
    raw_position_source: str | None = Field(default=None, max_length=50)
    expected_salary_min_pln: int | None = Field(default=None, ge=0)
    expected_salary_max_pln: int | None = Field(default=None, ge=0)
    applied_at: datetime
    last_update_at: datetime | None = None

    @model_validator(mode="after")
    def validate_expected_salary_range(self) -> "ApplicationBase":
        if (
            self.expected_salary_min_pln is not None
            and self.expected_salary_max_pln is not None
            and self.expected_salary_min_pln > self.expected_salary_max_pln
        ):
            raise ValueError("Expected salary minimum cannot be greater than maximum")
        return self


class ApplicationTagPayload(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    kind: str = Field(default="keyword", max_length=100)
    confidence: float | None = None
    source: str | None = None


class ApplicationCreate(ApplicationBase):
    tags: list[ApplicationTagPayload] = Field(default_factory=list)


class ApplicationUpdateRequest(ApplicationBase):
    tags: list[ApplicationTagPayload] = Field(default_factory=list)


class ApplicationRejectionUpdate(BaseModel):
    rejection_reason: str = Field(min_length=1, max_length=500)


class ApplicationTagRead(ApplicationTagPayload):
    model_config = ConfigDict(from_attributes=True)

    id: int


class ApplicationRead(ApplicationBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_name: str
    application_source_name: str | None = None
    created_at: datetime
    updated_at: datetime
    tags: list[ApplicationTagRead] = Field(default_factory=list)


class ApplicationScrapeRequest(BaseModel):
    url: str = Field(min_length=1, max_length=1000)


class ApplicationTextPreviewRequest(BaseModel):
    text: str = Field(min_length=1)
    source_url: str | None = Field(default=None, max_length=1000)


class ApplicationScrapePreview(BaseModel):
    source_url: str
    company_name: str | None = None
    position_title: str | None = None
    position_description: str | None = None
    location: str | None = None
    remote_policy: str | None = None
    seniority: SeniorityLevel | None = None
    employment_type: str | None = None
    salary: str | None = None
    contact_url: str | None = None
    contact_description: str | None = None
    recruitment_description: str | None = None
    tags: list[ApplicationTagPayload] = Field(default_factory=list)
    raw_text: str
    raw_source: str = "url"
    warnings: list[str] = Field(default_factory=list)


class GmailStatus(BaseModel):
    connected: bool
    email_address: str | None = None
    last_sync_at: datetime | None = None
    messages_count: int = 0
    token_file_exists: bool = False
    client_secret_file_exists: bool = False
    sync_query: str


class GmailMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    gmail_id: str
    thread_id: str
    sender: str | None = None
    recipients: str | None = None
    subject: str | None = None
    snippet: str | None = None
    internal_date: datetime | None = None
    received_at: datetime | None = None


class GmailSyncResult(BaseModel):
    imported_count: int
    updated_count: int
    scanned_count: int
    email_address: str


class PromptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    content: str
    created_at: datetime
    updated_at: datetime


class PromptCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    content: str = Field(min_length=1)


class PromptUpdate(BaseModel):
    description: str | None = None
    content: str = Field(min_length=1)


class CoverLetterRequest(BaseModel):
    position_title: str
    company_name: str
    notes: str | None = None
    raw_position_text: str | None = None


class CoverLetterResponse(BaseModel):
    content: str
