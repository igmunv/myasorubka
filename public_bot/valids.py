import re, validators
from urllib.parse import urlparse


INVISIBLE_CHARS_RE = re.compile(r"[\u200b-\u200d\ufeff\u2800]")
HORIZONTAL_SPACE_RE = re.compile(r"[^\S\n\r]+")
HAS_ALNUM_RE = re.compile(r"[a-zA-Zа-яА-ЯёЁ0-9]")
LINK_OR_MENTION_RE = re.compile(
    r"(https?://\S+|www\.\S+|t\.me/\S+|@[a-zA-Z0-9_]{3,})",
    re.IGNORECASE,
)
CYRILLIC_SINGLE_UPPER_RE = re.compile(r"^[А-ЯЁ](?![А-ЯЁ])")

def normalize_text(text: str, lowercase_leading_ru: bool = True) -> str:
    """Убирает невидимые символы, схлопывает пробелы и табы, но сохраняет переносы для валидации."""
    cleaned = INVISIBLE_CHARS_RE.sub("", text)
    cleaned = HORIZONTAL_SPACE_RE.sub(" ", cleaned).strip()
    cleaned = cleaned.rstrip(".").strip()

    if lowercase_leading_ru and CYRILLIC_SINGLE_UPPER_RE.match(cleaned):
        cleaned = cleaned[0].lower() + cleaned[1:]

    return cleaned


def validate_text(text: str, min_len: int, max_len: int,forbid_links: bool = True,) -> str | None:
    """
        Возвращает текст причины отказа для шаблона '❗️ Не могу принять ответ: {reason}\n\nПопробуй ещё раз:'
        или None, если текст прошёл проверку.
    """

    if "\n" in text:
        return "пиши сплошным текстом без переносов строк"

    if forbid_links and LINK_OR_MENTION_RE.search(text):
        return "не пиши ссылки и @username здесь — для ссылки есть свой шаг"

    if not HAS_ALNUM_RE.search(text):
        return "не увидел ни одной буквы"

    if len(text) < min_len:
        return f"слишком коротко (минимум {min_len} симв., сейчас {len(text)})"

    if len(text) > max_len:
        return f"слишком длинно (максимум {max_len} симв., сейчас {len(text)})" 

    return None


def normalize_portfolio_url(raw_text: str) -> str:
    """Нормализует ссылку на профиль/канал/сайт, включая @username."""
    cleaned = INVISIBLE_CHARS_RE.sub("", raw_text).strip()
    if not cleaned:
        return ""

    if cleaned.startswith("@") and "/" not in cleaned and " " not in cleaned:
        username = cleaned[1:]
        if username:
            return f"https://t.me/{username}"

    return normalize_url(cleaned)


def normalize_url(raw_text: str) -> str:
    """Чистит невидимые символы и добавляет https://, если схема не указана."""
    cleaned = INVISIBLE_CHARS_RE.sub("", raw_text).strip()
    if not cleaned:
        return ""

    # Если юзер написал без схемы (например, github.com/igmunv/myasorubka), добавляем https://
    if "://" not in cleaned and not cleaned.startswith(("http:", "https:")):
        cleaned = f"https://{cleaned}"

    return cleaned


def validate_project_url(url: str, max_len: int = 200) -> str | None:
    """Возвращает причину отказа или None, если ссылка валидна."""
    if not url:
        return "не увидел ссылку"

    if len(url) > max_len:
        return f"ссылка слишком длинная (максимум {max_len} симв.)"

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return "разрешены только ссылки с http:// или https://"

    if not parsed.netloc or "." not in parsed.netloc:
        return "некорректный адрес ссылки"

    try:
        is_valid = bool(validators.url(url))
    except Exception:
        is_valid = False

    if not is_valid:
        return "некорректный адрес ссылки"

    return None