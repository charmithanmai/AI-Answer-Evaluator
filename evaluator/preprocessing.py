import re
import unicodedata

_ZERO_WIDTH = re.compile(r"[\u200b\u200c\u200d\ufeff]")
_QUOTES = str.maketrans({
    "\u2018": "'", "\u2019": "'",
    "\u201c": '"', "\u201d": '"',
})


def clean_text(text) -> str:
    """Normalize text without changing its meaning.

    Handles None, non-string input, invisible characters, curly quotes and
    messy whitespace. Casing is kept on purpose: the embedding model and the
    LLM judge both work fine with it.
    """
    if text is None:
        return ""
    text = str(text)
    text = unicodedata.normalize("NFKC", text)
    text = _ZERO_WIDTH.sub("", text)
    text = text.translate(_QUOTES)
    return " ".join(text.split())