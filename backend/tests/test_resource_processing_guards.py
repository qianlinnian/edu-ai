from workers import embedding_task


def test_unsupported_resource_type_is_rejected():
    try:
        embedding_task.ensure_supported_resource_type("zip")
    except ValueError as exc:
        assert "Unsupported file type: zip" in str(exc)
    else:
        raise AssertionError("Expected unsupported file type to raise ValueError")


def test_blank_pdf_content_has_actionable_error_without_ocr(monkeypatch):
    monkeypatch.setattr(embedding_task.settings, "DASHSCOPE_API_KEY", "")

    try:
        embedding_task.ensure_readable_content("", file_type="pdf")
    except ValueError as exc:
        assert "Upload a text-based PDF or configure DASHSCOPE_API_KEY for OCR." in str(exc)
    else:
        raise AssertionError("Expected blank PDF content to raise ValueError")


def test_blank_docx_content_has_actionable_error():
    try:
        embedding_task.ensure_readable_content(" \n\n ", file_type="docx")
    except ValueError as exc:
        assert "No readable text could be extracted from DOCX." == str(exc)
    else:
        raise AssertionError("Expected blank DOCX content to raise ValueError")
