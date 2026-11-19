from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv

from src.rivex.domain.exceptions import ErroConfiguracao


@dataclass(frozen=True)
class DatabaseSettings:
    host: str
    port: int
    database: str
    user: str
    password: str


@dataclass(frozen=True)
class CallixSettings:
    max_workers: int = 5
    retry_429_wait: int = 60
    retry_429_max: int = 5


@dataclass(frozen=True)
class IpboxSettings:
    url: str
    login: str
    password: str
    token: str
    delay_segundos: float = 5.0


@dataclass(frozen=True)
class VonixSettings:
    url: str
    login: str
    password: str
    delay_segundos: float = 2.0
    backoff_erro_segundos: float = 15.0


@dataclass(frozen=True)
class Settings:
    db: DatabaseSettings
    callix: CallixSettings = field(default_factory=CallixSettings)
    ipbox: Optional[IpboxSettings] = None
    vonix: Optional[VonixSettings] = None
    max_falhas_pipeline: int = 0


def _exigir_variaveis(nomes: list[str]) -> dict[str, str]:
    valores: dict[str, str] = {}
    ausentes: list[str] = []
    for nome in nomes:
        valor = os.getenv(nome)
        if valor is None or not valor.strip():
            ausentes.append(nome)
        else:
            valores[nome] = valor.strip()
    if ausentes:
        raise ErroConfiguracao(
            f"Variáveis de ambiente obrigatórias ausentes: {', '.join(ausentes)}"
        )
    return valores


def carregar_settings(pipeline_alvo: str = "all") -> Settings:
    """Carrega .env uma única vez e valida as variáveis exigidas para o alvo."""
    load_dotenv()

    db_env = _exigir_variaveis(["HOST_DB", "DATABASE_CONTECH", "USER_DB"])
    porta_str = os.getenv("PORT_DB") or "5432"
    senha_db = os.getenv("SENHA_DB") or ""

    db_settings = DatabaseSettings(
        host=db_env["HOST_DB"],
        port=int(porta_str),
        database=db_env["DATABASE_CONTECH"],
        user=db_env["USER_DB"],
        password=senha_db,
    )

    callix_settings = CallixSettings(
        max_workers=int(os.getenv("CALLIX_MAX_WORKERS", "5")),
        retry_429_wait=int(os.getenv("CALLIX_RETRY_429_WAIT", "60")),
        retry_429_max=int(os.getenv("CALLIX_RETRY_429_MAX", "5")),
    )

    ipbox_settings: Optional[IpboxSettings] = None
    if pipeline_alvo in ("all", "ipbox"):
        ipbox_env = _exigir_variaveis(
            ["URL_IPBOX", "IPBOX_LOGIN", "IPBOX_PASSWORD", "IPBOX_TOKEN"]
        )
        ipbox_settings = IpboxSettings(
            url=ipbox_env["URL_IPBOX"],
            login=ipbox_env["IPBOX_LOGIN"],
            password=ipbox_env["IPBOX_PASSWORD"],
            token=ipbox_env["IPBOX_TOKEN"],
            delay_segundos=float(os.getenv("TEMPO_IPBOX", "5")),
        )

    vonix_settings: Optional[VonixSettings] = None
    if pipeline_alvo in ("all", "vonix"):
        vonix_env = _exigir_variaveis(["URL_BASE_VONIX6", "LOGIN_VONIX", "SENHA_VONIX"])
        vonix_settings = VonixSettings(
            url=vonix_env["URL_BASE_VONIX6"],
            login=vonix_env["LOGIN_VONIX"],
            password=vonix_env["SENHA_VONIX"],
            delay_segundos=float(os.getenv("TEMPO_VONIX", "2")),
            backoff_erro_segundos=float(os.getenv("VONIX_BACKOFF_ERRO", "15")),
        )

    return Settings(
        db=db_settings,
        callix=callix_settings,
        ipbox=ipbox_settings,
        vonix=vonix_settings,
        max_falhas_pipeline=int(os.getenv("MAX_FALHAS_PIPELINE", "0")),
    )
