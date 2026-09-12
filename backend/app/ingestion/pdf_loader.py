from __future__ import annotations


class PDFInspectionError(ValueError):
    pass


def inspect_pdf(path) -> dict:
    try:
        import fitz
        document = fitz.open(path)
    except Exception as exc:
        raise PDFInspectionError(f"The PDF could not be opened: {exc}") from exc
    try:
        if document.needs_pass:
            raise PDFInspectionError("Password-protected PDFs are not supported")
        if document.page_count < 1:
            raise PDFInspectionError("The PDF contains no pages")
        return {"page_count": document.page_count, "metadata": document.metadata or {}}
    finally:
        document.close()

