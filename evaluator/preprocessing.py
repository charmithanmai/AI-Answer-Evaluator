def clean_text(text: str) -> str:
    """Normalize whitespace. Will grow on Day 3."""
    if not text:
        return ""
    return " ".join(text.split()).strip()