import base64
import logging
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.config import Settings, get_settings
from backend.db import SessionLocal
from backend.models import GmailAccount, GmailMessage
from backend.schemas import GmailStatus, GmailSyncResult

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
logger = logging.getLogger(__name__)


def ensure_credentials_dir(settings: Settings) -> None:
    logger.debug(
        "Ensuring Gmail credential directories client_secret_dir=%s token_dir=%s",
        settings.google_client_secret_path.parent,
        settings.google_gmail_token_path.parent,
    )
    settings.google_client_secret_path.parent.mkdir(parents=True, exist_ok=True)
    settings.google_gmail_token_path.parent.mkdir(parents=True, exist_ok=True)


def load_credentials(settings: Settings) -> Credentials | None:
    token_path = settings.google_gmail_token_path
    logger.debug("Loading Gmail credentials token_path=%s", token_path)
    if not token_path.exists():
        logger.info("Gmail token file does not exist token_path=%s", token_path)
        return None

    credentials = Credentials.from_authorized_user_file(str(token_path), GMAIL_SCOPES)
    if credentials.expired and credentials.refresh_token:
        logger.info("Refreshing expired Gmail credentials")
        credentials.refresh(Request())
        save_credentials(settings, credentials)

    return credentials


def save_credentials(settings: Settings, credentials: Credentials) -> None:
    ensure_credentials_dir(settings)
    settings.google_gmail_token_path.write_text(credentials.to_json(), encoding="utf-8")
    logger.info("Gmail credentials saved token_path=%s", settings.google_gmail_token_path)


def get_gmail_service(settings: Settings):
    logger.debug("Creating Gmail service")
    credentials = load_credentials(settings)
    if credentials is None or not credentials.valid:
        logger.warning("Gmail service requested without valid credentials")
        raise RuntimeError("Gmail is not connected. Run scripts/connect-gmail.ps1 first.")
    return build("gmail", "v1", credentials=credentials)


def connect_gmail() -> str:
    settings = get_settings()
    logger.info(
        "Starting Gmail connection client_secret_path=%s",
        settings.google_client_secret_path,
    )
    ensure_credentials_dir(settings)
    if not settings.google_client_secret_path.exists():
        logger.warning("Gmail client secret missing path=%s", settings.google_client_secret_path)
        raise FileNotFoundError(
            f"Google client secret file not found: {settings.google_client_secret_path}"
        )

    flow = InstalledAppFlow.from_client_secrets_file(
        str(settings.google_client_secret_path),
        GMAIL_SCOPES,
    )
    credentials = flow.run_local_server(port=0)
    save_credentials(settings, credentials)

    service = get_gmail_service(settings)
    profile = service.users().getProfile(userId="me").execute()
    email_address = profile["emailAddress"]
    history_id = profile.get("historyId")

    with SessionLocal() as session:
        upsert_account(session, email_address=email_address, history_id=history_id)
        session.commit()

    logger.info("Gmail connected email_address=%s history_id=%s", email_address, history_id)
    return email_address


def upsert_account(session: Session, email_address: str, history_id: str | None) -> GmailAccount:
    logger.debug(
        "Upserting Gmail account email_address=%s history_id=%s",
        email_address,
        history_id,
    )
    account = session.scalar(
        select(GmailAccount).where(GmailAccount.email_address == email_address)
    )
    if account is None:
        account = GmailAccount(email_address=email_address, history_id=history_id)
        session.add(account)
        session.flush()
        logger.info(
            "Gmail account created account_id=%s email_address=%s",
            account.id,
            email_address,
        )
    else:
        account.history_id = history_id or account.history_id
        logger.debug(
            "Gmail account updated account_id=%s email_address=%s",
            account.id,
            email_address,
        )
    return account


def get_gmail_status(session: Session, settings: Settings) -> GmailStatus:
    logger.debug("Reading Gmail status")
    account = session.scalar(select(GmailAccount).order_by(GmailAccount.connected_at.desc()))
    messages_count = session.scalar(select(func.count(GmailMessage.id))) or 0

    return GmailStatus(
        connected=account is not None and settings.google_gmail_token_path.exists(),
        email_address=account.email_address if account else None,
        last_sync_at=account.last_sync_at if account else None,
        messages_count=messages_count,
        token_file_exists=settings.google_gmail_token_path.exists(),
        client_secret_file_exists=settings.google_client_secret_path.exists(),
        sync_query=settings.gmail_initial_sync_query,
    )


def header_value(headers: list[dict[str, str]], name: str) -> str | None:
    normalized = name.lower()
    for header in headers:
        if header.get("name", "").lower() == normalized:
            return header.get("value")
    return None


def decode_body_data(data: str | None) -> str:
    if not data:
        return ""
    padded = data + "=" * (-len(data) % 4)
    try:
        return base64.urlsafe_b64decode(padded).decode("utf-8", errors="replace")
    except ValueError:
        return ""


def collect_text_parts(payload: dict[str, Any]) -> list[str]:
    mime_type = payload.get("mimeType")
    body = payload.get("body", {})
    parts = payload.get("parts", [])

    if mime_type == "text/plain":
        text = decode_body_data(body.get("data"))
        return [text] if text else []

    collected: list[str] = []
    for part in parts:
        collected.extend(collect_text_parts(part))
    return collected


def parse_message_datetime(
    message: dict[str, Any],
    headers: list[dict[str, str]],
) -> datetime | None:
    if message.get("internalDate"):
        return datetime.fromtimestamp(int(message["internalDate"]) / 1000, UTC)

    date_header = header_value(headers, "Date")
    if not date_header:
        return None

    parsed = parsedate_to_datetime(date_header)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def upsert_message(
    session: Session,
    account: GmailAccount,
    message: dict[str, Any],
) -> tuple[bool, bool]:
    payload = message.get("payload", {})
    headers = payload.get("headers", [])
    gmail_id = message["id"]
    logger.debug(
        "Upserting Gmail message gmail_id=%s thread_id=%s",
        gmail_id,
        message.get("threadId"),
    )
    existing = session.scalar(select(GmailMessage).where(GmailMessage.gmail_id == gmail_id))

    body_text = "\n\n".join(collect_text_parts(payload)).strip()
    internal_date = parse_message_datetime(message, headers)
    values = {
        "account_id": account.id,
        "gmail_id": gmail_id,
        "thread_id": message["threadId"],
        "history_id": message.get("historyId"),
        "sender": header_value(headers, "From"),
        "recipients": header_value(headers, "To"),
        "subject": header_value(headers, "Subject"),
        "snippet": message.get("snippet"),
        "body_text": body_text[:20000] if body_text else None,
        "label_ids": message.get("labelIds"),
        "internal_date": internal_date,
        "received_at": internal_date,
        "raw_payload": payload,
    }

    if existing is None:
        session.add(GmailMessage(**values))
        logger.debug("Gmail message created gmail_id=%s subject=%s", gmail_id, values["subject"])
        return True, False

    for key, value in values.items():
        setattr(existing, key, value)
    logger.debug("Gmail message updated gmail_id=%s subject=%s", gmail_id, values["subject"])
    return False, True


def sync_gmail_messages(max_results: int = 50) -> GmailSyncResult:
    settings = get_settings()
    logger.info(
        "Gmail sync service started max_results=%s query=%s",
        max_results,
        settings.gmail_initial_sync_query,
    )
    service = get_gmail_service(settings)
    profile = service.users().getProfile(userId="me").execute()
    email_address = profile["emailAddress"]
    query = settings.gmail_initial_sync_query

    response = (
        service.users()
        .messages()
        .list(userId="me", q=query, maxResults=max_results)
        .execute()
    )
    message_refs = response.get("messages", [])
    logger.info(
        "Gmail message refs received count=%s email_address=%s history_id=%s",
        len(message_refs),
        email_address,
        profile.get("historyId"),
    )

    imported_count = 0
    updated_count = 0
    with SessionLocal() as session:
        account = upsert_account(
            session,
            email_address=email_address,
            history_id=profile.get("historyId"),
        )

        for message_ref in message_refs:
            logger.debug("Fetching Gmail message gmail_id=%s", message_ref["id"])
            message = (
                service.users()
                .messages()
                .get(userId="me", id=message_ref["id"], format="full")
                .execute()
            )
            imported, updated = upsert_message(session, account, message)
            imported_count += int(imported)
            updated_count += int(updated)

        account.last_sync_at = datetime.now(UTC)
        account.history_id = profile.get("historyId") or account.history_id
        session.commit()

    logger.info(
        "Gmail sync service finished imported_count=%s updated_count=%s scanned_count=%s",
        imported_count,
        updated_count,
        len(message_refs),
    )
    return GmailSyncResult(
        imported_count=imported_count,
        updated_count=updated_count,
        scanned_count=len(message_refs),
        email_address=email_address,
    )
