import os
from .pdf_parser import parse_pdf
from .docx_parser import parse_docx
from .xlsx_parser import parse_xlsx


def parse_file(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return parse_pdf(file_path)
    elif ext in (".docx", ".doc"):
        return parse_docx(file_path)
    elif ext in (".xlsx", ".xls"):
        return parse_xlsx(file_path)
    elif ext == ".txt":
        try:
            with open(file_path, "r", errors="ignore") as f:
                return f.read()
        except Exception:
            return ""
    else:
        # Image files handled by OCR mock in Phase 6
        return ""


def merge_documents(file_paths: list[str]) -> str:
    parts = []
    for path in file_paths:
        text = parse_file(path)
        if text.strip():
            filename = os.path.basename(path)
            parts.append(f"--- Document: {filename} ---\n{text}")
    return "\n\n".join(parts)
