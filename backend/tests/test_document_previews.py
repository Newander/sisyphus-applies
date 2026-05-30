import zipfile
from pathlib import Path

from backend.services.documents import create_text_document, read_document_preview


def write_docx(path: Path, paragraphs: list[str]) -> None:
    paragraph_xml = "".join(
        f"<w:p><w:r><w:t>{paragraph}</w:t></w:r></w:p>" for paragraph in paragraphs
    )
    document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>{paragraph_xml}</w:body>
</w:document>
"""
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", document_xml)


def test_reads_docx_preview(tmp_path: Path) -> None:
    path = tmp_path / "resume.docx"
    write_docx(path, ["First paragraph", "Second paragraph"])

    preview = read_document_preview(path)

    assert preview.lines == ["First paragraph", "Second paragraph"]
    assert preview.line_count == 2
    assert preview.truncated is False
    assert preview.unsupported_reason is None


def test_truncates_docx_preview(tmp_path: Path) -> None:
    path = tmp_path / "resume.docx"
    write_docx(path, [f"Line {index}" for index in range(55)])

    preview = read_document_preview(path)

    assert preview.lines == [f"Line {index}" for index in range(50)]
    assert preview.line_count == 50
    assert preview.truncated is True


def test_creates_text_document_with_metadata(tmp_path: Path) -> None:
    document = create_text_document(
        tmp_path,
        file_name="My CV",
        text="Hello\nWorld",
        document_type="cv",
        company_id=12,
        company_name="Acme",
    )

    path = tmp_path / "My CV.txt"
    assert path.read_text(encoding="utf-8") == "Hello\nWorld"
    assert (tmp_path / "My CV.txt.meta.json").is_file()
    assert document.name == "My CV.txt"
    assert document.document_type == "cv"
    assert document.company_id == 12
    assert document.company_name == "Acme"
