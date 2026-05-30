import logging
import zipfile
from pathlib import Path
from xml.etree import ElementTree

import ollama as ollama_client
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from backend.config import Settings
from backend.models import DocumentChunk

logger = logging.getLogger(__name__)

CHUNK_SIZE = 600
CHUNK_OVERLAP = 100
TOP_K = 5


# ── Text extraction ────────────────────────────────────────────────────────

def _extract_docx_text(path: Path) -> str:
    try:
        with zipfile.ZipFile(path) as archive:
            xml = archive.read("word/document.xml")
    except (KeyError, zipfile.BadZipFile, OSError):
        return ""
    try:
        root = ElementTree.fromstring(xml)
    except ElementTree.ParseError:
        return ""
    ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    paragraphs = []
    for p in root.iter(f"{ns}p"):
        text = "".join(node.text or "" for node in p.iter(f"{ns}t"))
        if text.strip():
            paragraphs.append(text)
    return "\n".join(paragraphs)


def _extract_pdf_text(path: Path) -> str:
    try:
        from pypdf import PdfReader

        reader = PdfReader(path)
        return "\n\n".join(
            page.extract_text() for page in reader.pages if page.extract_text()
        )
    except Exception as exc:
        logger.warning("PDF text extraction failed path=%s err=%s", path, exc)
        return ""


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".docx":
        return _extract_docx_text(path)
    if suffix == ".pdf":
        return _extract_pdf_text(path)
    for encoding in ("utf-8-sig", "utf-8", "cp1251", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except (UnicodeDecodeError, OSError):
            continue
    return ""


# ── Chunking ───────────────────────────────────────────────────────────────

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if len(current) + len(paragraph) + 2 <= chunk_size:
            current = f"{current}\n\n{paragraph}".strip() if current else paragraph
        else:
            if current:
                chunks.append(current)
            if len(paragraph) <= chunk_size:
                current = paragraph
            else:
                for i in range(0, len(paragraph), chunk_size - overlap):
                    chunks.append(paragraph[i : i + chunk_size])
                current = ""
    if current:
        chunks.append(current)
    return chunks


# ── Embedding ──────────────────────────────────────────────────────────────

async def _embed(texts: list[str], settings: Settings) -> list[list[float]]:
    client = ollama_client.AsyncClient(host=settings.ollama_base_url)
    response = await client.embed(model=settings.ollama_embed_model, input=texts)
    return response.embeddings


# ── Core index / delete ────────────────────────────────────────────────────

async def _index_text(document_id: str, text: str, settings: Settings, session: Session) -> int:
    session.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))
    if not text.strip():
        session.commit()
        return 0
    chunks = chunk_text(text)
    if not chunks:
        session.commit()
        return 0
    embeddings = await _embed(chunks, settings)
    for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings, strict=True)):
        session.add(DocumentChunk(
            document_id=document_id,
            chunk_index=idx,
            content=chunk,
            embedding=embedding,
        ))
    session.commit()
    logger.info("Indexed document_id=%s chunks=%s", document_id, len(chunks))
    return len(chunks)


def delete_document_index(document_id: str, session: Session) -> None:
    session.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))
    session.commit()


# ── Public indexing API ────────────────────────────────────────────────────

async def index_document(
    document_id: str, path: Path, settings: Settings, session: Session
) -> int:
    return await _index_text(document_id, extract_text(path), settings, session)


async def index_application(application_id: int, settings: Settings, session: Session) -> None:
    from backend.models import Company, JobApplication

    application = session.get(JobApplication, application_id)
    if application is None:
        return
    company = session.get(Company, application.company_id)
    parts = [
        f"Position: {application.position_title}",
        f"Company: {company.name if company else ''}",
    ]
    if application.raw_position_text:
        parts.append(f"Job posting:\n{application.raw_position_text}")
    if application.notes:
        parts.append(f"Notes:\n{application.notes}")
    if application.contact_description:
        parts.append(f"Contact:\n{application.contact_description}")
    if application.recruitment_description:
        parts.append(f"Recruitment:\n{application.recruitment_description}")
    await _index_text(f"app:{application_id}", "\n\n".join(parts), settings, session)


async def index_company(company_id: int, settings: Settings, session: Session) -> None:
    from backend.models import Company

    company = session.get(Company, company_id)
    if company is None:
        return
    parts = [f"Company: {company.name}"]
    if company.website:
        parts.append(f"Website: {company.website}")
    if company.notes:
        parts.append(f"Notes:\n{company.notes}")
    await _index_text(f"company:{company_id}", "\n\n".join(parts), settings, session)


# ── Search & retrieval ─────────────────────────────────────────────────────

async def search_similar(
    query: str, settings: Settings, session: Session, top_k: int = TOP_K
) -> list[str]:
    embeddings = await _embed([query], settings)
    query_vec = embeddings[0]
    rows = (
        session.query(DocumentChunk.content)
        .order_by(DocumentChunk.embedding.cosine_distance(query_vec))
        .limit(top_k)
        .all()
    )
    return [str(row[0]) for row in rows]


async def index_missing(settings: Settings, session: Session) -> dict[str, int]:
    """Find records with no document_chunks entries and index them."""
    from pathlib import Path

    from backend.models import Company, JobApplication
    from backend.services.documents import list_storage_documents

    indexed: set[str] = set(
        session.scalars(select(DocumentChunk.document_id).distinct())
    )

    counts: dict[str, int] = {"applications": 0, "companies": 0, "files": 0}

    for app_id in session.scalars(select(JobApplication.id)):
        if f"app:{app_id}" not in indexed:
            try:
                await index_application(app_id, settings, session)
                counts["applications"] += 1
            except Exception as exc:
                logger.warning("Startup index failed app_id=%s err=%s", app_id, exc)

    for company_id in session.scalars(select(Company.id)):
        if f"company:{company_id}" not in indexed:
            try:
                await index_company(company_id, settings, session)
                counts["companies"] += 1
            except Exception as exc:
                logger.warning("Startup index failed company_id=%s err=%s", company_id, exc)

    for doc in list_storage_documents(settings.storage_dir, limit=None):
        if doc.id not in indexed:
            try:
                await index_document(doc.id, Path(doc.path), settings, session)
                counts["files"] += 1
            except Exception as exc:
                logger.warning("Startup index failed doc_id=%s err=%s", doc.id, exc)

    logger.info("Missing index check complete counts=%s", counts)
    return counts


async def build_rag_context(query: str, settings: Settings, session: Session) -> str | None:
    chunks = await search_similar(query, settings, session)
    if not chunks:
        return None
    joined = "\n\n---\n\n".join(chunks)
    return f"Relevant excerpts from your documents:\n\n{joined}"
