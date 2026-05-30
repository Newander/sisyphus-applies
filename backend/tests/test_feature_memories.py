from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from backend.api.feature_memories import (
    close_feature_memory,
    create_feature_memory,
    list_feature_memories,
)
from backend.db import Base
from backend.models import FeatureMemory
from backend.schemas import FeatureMemoryCreate


def make_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_feature_memory_lifecycle() -> None:
    session = make_session()
    payload = FeatureMemoryCreate(
        text="Add quick filter",
        page_url="http://localhost:3000/applications",
        page_title="Applications",
        screenshot_data_url="data:image/png;base64,abc",
    )

    created = create_feature_memory(payload, session)
    assert created.id is not None
    assert created.text == "Add quick filter"
    assert created.page_url == "http://localhost:3000/applications"

    assert [memory.id for memory in list_feature_memories(session)] == [created.id]

    response = close_feature_memory(created.id, session)
    assert response.status_code == 204
    assert list_feature_memories(session) == []

    stored = session.scalar(select(FeatureMemory).where(FeatureMemory.id == created.id))
    assert stored is not None
    assert stored.closed_at is not None
