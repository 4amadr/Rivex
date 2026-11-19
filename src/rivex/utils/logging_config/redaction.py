import logging
import re
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

REDACTED = "***OCULTO***"

SENSITIVE_KEYS = frozenset({
    "authorization",
    "proxy-authorization",
    "x-api-key",
    "api-key",
    "apikey",
    "api_key",
    "token",
    "access_token",
    "refresh_token",
    "usersessiontoken",
    "user_session_token",
    "session_token",
    "password",
    "passwd",
    "senha",
    "secret",
    "client_secret",
    "cookie",
    "set-cookie",
    "x-auth-token",
    "senha_db",
    "db_password",
})

_AUTH_HEADER_RE = re.compile(
    r"(?i)\b(bearer|basic|token)\s+[A-Za-z0-9\-._~+/]+=*"
)
_URI_CREDENTIAL_RE = re.compile(
    r"(?i)([a-z][a-z0-9+.\-]*://[^:\s/@]+:)([^@\s/]+)(@)"
)
_KEY_VALUE_SECRET_RE = re.compile(
    r"(?i)\b(password|passwd|senha|token|api[_-]?key|secret|authorization|usersessiontoken)\b(\s*[:=]\s*)([^\s,;'\"}]+)"
)


def _is_sensitive_key(key: Any) -> bool:
    normalized = str(key).strip().lower()
    if normalized in SENSITIVE_KEYS:
        return True
    return any(
        marker in normalized
        for marker in ("token", "password", "senha", "secret", "apikey", "api_key", "authorization")
    )


def redact_url(url: str) -> str:
    """Remove ou mascara parâmetros sensíveis na query string e credenciais embutidas na URL."""
    if not isinstance(url, str) or not url:
        return url

    sanitized = _URI_CREDENTIAL_RE.sub(rf"\1{REDACTED}\3", url)
    try:
        parts = urlsplit(sanitized)
    except ValueError:
        return sanitized

    if not parts.query:
        return sanitized

    query_items = parse_qsl(parts.query, keep_blank_values=True)
    redacted_query = [
        (k, REDACTED if _is_sensitive_key(k) else v)
        for k, v in query_items
    ]
    return urlunsplit((
        parts.scheme,
        parts.netloc,
        parts.path,
        urlencode(redacted_query),
        parts.fragment,
    ))


def redact_text(text: str) -> str:
    """Mascara tokens, senhas e credenciais URI dentro de strings livres."""
    if not isinstance(text, str) or not text:
        return text

    result = _URI_CREDENTIAL_RE.sub(rf"\1{REDACTED}\3", text)
    result = _AUTH_HEADER_RE.sub(lambda m: f"{m.group(1)} {REDACTED}", result)
    result = _KEY_VALUE_SECRET_RE.sub(rf"\1\2{REDACTED}", result)
    return result


def redact_value(value: Any, _depth: int = 0) -> Any:
    """Redige recursivamente credenciais em dicionários, listas, tuplas e strings."""
    if _depth > 8:
        return "[TRUNCATED]"

    if isinstance(value, dict):
        cleaned = {}
        for k, v in value.items():
            if _is_sensitive_key(k):
                cleaned[k] = REDACTED
            else:
                cleaned[k] = redact_value(v, _depth + 1)
        return cleaned

    if isinstance(value, list):
        return [redact_value(item, _depth + 1) for item in value]

    if isinstance(value, tuple):
        return tuple(redact_value(item, _depth + 1) for item in value)

    if isinstance(value, str):
        return redact_text(value)

    return value


class SensitiveDataFilter(logging.Filter):
    """Filtro de logging que garante redação de credenciais antes da gravação em arquivo."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact_text(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = redact_value(record.args)
            elif isinstance(record.args, tuple):
                record.args = tuple(redact_value(arg) for arg in record.args)
            else:
                record.args = redact_value(record.args)
        return True
