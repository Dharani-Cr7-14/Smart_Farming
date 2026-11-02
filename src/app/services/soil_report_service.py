import re
from io import BytesIO

from pypdf import PdfReader


class SoilReportError(Exception):
    """Raised when a soil report cannot be read or parsed."""


FIELD_PATTERNS = {
    "pH": (r"\b(?:soil\s*)?p\s*\.?\s*h\b", "pH"),
    "N": (r"\b(?:available\s*)?(?:nitrogen|n)\b", "N"),
    "P": (r"\b(?:available\s*)?(?:phosphorus|phosphate|phosphorous|p)\b", "P"),
    "K": (r"\b(?:available\s*)?(?:potassium|potash|k)\b", "K"),
    "Organic_Carbon": (r"\borganic\s+carbon\b", "Organic Carbon"),
    "Electrical_Conductivity": (r"\b(?:electrical\s+conductivity|ec)\b", "Electrical Conductivity"),
}


def _number_after_label(text: str, label_pattern: str) -> float | None:
    match = re.search(
        rf"{label_pattern}\s*(?:\([^)]*\)|[:=\-])?\s*([0-9]+(?:\.[0-9]+)?)",
        text,
        flags=re.IGNORECASE,
    )
    return float(match.group(1)) if match else None


def extract_soil_report(file_bytes: bytes, filename: str) -> dict:
    """Extract supported soil metrics from a text-based PDF report."""
    if not filename.lower().endswith(".pdf"):
        raise SoilReportError("Please upload a PDF soil report.")
    try:
        reader = PdfReader(BytesIO(file_bytes))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as exc:
        raise SoilReportError("The PDF could not be read. Please upload a valid report.") from exc

    if not text.strip():
        raise SoilReportError("This PDF has no selectable text. Scanned-image reports are not supported yet.")

    values = {}
    for field, (pattern, _) in FIELD_PATTERNS.items():
        value = _number_after_label(text, pattern)
        if value is not None:
            values[field] = value

    required = ("pH", "N", "P", "K")
    missing = [field for field in required if field not in values]
    if missing:
        labels = ", ".join(FIELD_PATTERNS[field][1] for field in missing)
        raise SoilReportError(f"Could not find these required values in the report: {labels}.")

    return {"values": values, "filename": filename}
