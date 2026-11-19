import logging
from datetime import datetime
from pathlib import Path

from src.rivex.utils.logging_config import (
    REDACTED,
    build_log_filepath,
    get_service_logger,
    redact_text,
    redact_url,
    redact_value,
)


def test_build_log_filepath_format(tmp_path: Path):
    dt = datetime(2026, 11, 18, 19, 30, 45)
    path = build_log_filepath("extract", "callix", base_dir=tmp_path, execution_dt=dt)

    assert path == tmp_path / "extract" / "callix" / "log_extract_callix_2026-11-18_193045.log"
    assert path.parent.is_dir()


def test_redact_value_masks_sensitive_keys_recursively():
    payload = {
        "cliente": "acme",
        "headers": {
            "Authorization": "Bearer super-secret-token",
            "X-API-Key": "key-123",
            "Content-Type": "application/json",
        },
        "nested": [{"senha": "123456", "userSessionToken": "tok-xyz", "ok": 42}],
    }
    cleaned = redact_value(payload)

    assert cleaned["cliente"] == "acme"
    assert cleaned["headers"]["Authorization"] == REDACTED
    assert cleaned["headers"]["X-API-Key"] == REDACTED
    assert cleaned["headers"]["Content-Type"] == "application/json"
    assert cleaned["nested"][0]["senha"] == REDACTED
    assert cleaned["nested"][0]["userSessionToken"] == REDACTED
    assert cleaned["nested"][0]["ok"] == 42


def test_redact_url_and_text_mask_credentials():
    url = "https://user:pass123@api.example.com/v1/calls?token=abc999&date=2026-11-18"
    cleaned_url = redact_url(url)
    assert "pass123" not in cleaned_url
    assert "abc999" not in cleaned_url
    assert "date=2026-11-18" in cleaned_url

    msg = "Falha com Bearer eyJhbGciOiJIUzI1NiJ9 e password=segredo_forte"
    cleaned_msg = redact_text(msg)
    assert "eyJhbGciOiJIUzI1NiJ9" not in cleaned_msg
    assert "segredo_forte" not in cleaned_msg
    assert REDACTED in cleaned_msg


def test_service_logger_isolates_logs_and_mirrors_errors(tmp_path: Path):
    dt = datetime(2026, 11, 18, 20, 0, 0)
    logger_name = "rivex.extract.ipbox"
    error_logger_name = "rivex.pipeline.errors"

    # Limpa handlers prévios para isolar o teste
    logging.getLogger(logger_name).handlers.clear()
    logging.getLogger(error_logger_name).handlers.clear()

    log = get_service_logger("extract", "ipbox", base_dir=tmp_path, execution_dt=dt)
    log.info("HTTP_OK | token=secret_abc | status=200")

    service_file = tmp_path / "extract" / "ipbox" / "log_extract_ipbox_2026-11-18_200000.log"
    error_file = tmp_path / "pipeline" / "errors" / "log_pipeline_errors_2026-11-18_200000.log"

    assert service_file.exists()
    assert not error_file.exists()

    log.error("HTTP_FAIL | password=minha_senha | status=500")

    for h in log.handlers:
        h.flush()
        h.close()
    log.handlers.clear()
    logging.getLogger(error_logger_name).handlers.clear()

    service_content = service_file.read_text(encoding="utf-8")
    error_content = error_file.read_text(encoding="utf-8")

    assert "secret_abc" not in service_content
    assert "minha_senha" not in service_content
    assert "minha_senha" not in error_content
    assert "HTTP_OK" in service_content
    assert "HTTP_FAIL" in service_content
    assert "HTTP_FAIL" in error_content
    assert "HTTP_OK" not in error_content
