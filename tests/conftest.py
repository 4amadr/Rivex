from __future__ import annotations

import logging
from pathlib import Path

import pytest

from src.rivex.utils.logging_config import logging_config


@pytest.fixture(autouse=True)
def _isolar_diretorio_de_logs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Impede que testes unitários criem ou escrevam arquivos em logging_execution/."""
    log_dir = tmp_path / "logging_execution"
    monkeypatch.setattr(logging_config, "BASE_LOG_DIR", log_dir)

    novos_dirs = {
        chave: log_dir / chave[0] / chave[1]
        for chave in logging_config.SERVICE_DIRECTORIES
    }
    monkeypatch.setattr(logging_config, "SERVICE_DIRECTORIES", novos_dirs)

    yield

    for nome, logger in list(logging.Logger.manager.loggerDict.items()):
        if isinstance(logger, logging.Logger) and nome.startswith("rivex"):
            for handler in list(logger.handlers):
                handler.close()
                logger.removeHandler(handler)
