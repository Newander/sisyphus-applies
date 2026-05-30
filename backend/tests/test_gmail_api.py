from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.api.gmail import delete_gmail_message, list_gmail_messages_page
from backend.db import Base
from backend.models import GmailAccount, GmailMessage


def make_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_delete_gmail_message_removes_row() -> None:
    session = make_session()
    account = GmailAccount(email_address="user@example.com")
    session.add(account)
    session.flush()
    message = GmailMessage(
        account_id=account.id,
        gmail_id="gmail-1",
        thread_id="thread-1",
        subject="Hello",
    )
    session.add(message)
    session.commit()

    response = delete_gmail_message(message.id, session)

    assert response.status_code == 204
    assert session.get(GmailMessage, message.id) is None


def test_gmail_messages_page_sorts_and_paginates() -> None:
    session = make_session()
    account = GmailAccount(email_address="user@example.com")
    session.add(account)
    session.flush()
    messages = [
        GmailMessage(
            account_id=account.id,
            gmail_id=f"gmail-{index}",
            thread_id=f"thread-{index}",
            subject=subject,
        )
        for index, subject in enumerate(["Bravo", "Alpha", "Charlie"])
    ]
    session.add_all(messages)
    session.commit()

    page = list_gmail_messages_page(
        session=session,
        page=2,
        page_size=1,
        sort="subject",
        direction="asc",
    )

    assert page.total == 3
    assert [message.subject for message in page.items] == ["Bravo"]
