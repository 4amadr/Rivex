from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from src.rivex.utils.logging_config.redaction import (
    SensitiveDataFilter,
    redact_text,
    redact_url,
    redact_value,
)

_REPO_ROOT = Path(__file__).resolve().parents[4]
BASE_LOG_DIR = Path(os.getenv("RIVEX_LOG_DIR", str(_REPO_ROOT / "logging_execution")))
_EXECUTION_STARTED_AT = datetime.now()

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

SERVICE_DIRECTORIES: dict[tuple[str, str], Path] = {
    ("extract", "callix"): BASE_LOG_DIR / "extract" / "callix",
    ("extract", "ipbox"): BASE_LOG_DIR / "extract" / "ipbox",
    ("extract", "vonix"): BASE_LOG_DIR / "extract" / "vonix",
    ("transform", "callix"): BASE_LOG_DIR / "transform" / "callix",
    ("transform", "ipbox"): BASE_LOG_DIR / "transform" / "ipbox",
    ("transform", "vonix"): BASE_LOG_DIR / "transform" / "vonix",
    ("load", "callix"): BASE_LOG_DIR / "load" / "callix",
    ("load", "ipbox"): BASE_LOG_DIR / "load" / "ipbox",
    ("load", "vonix"): BASE_LOG_DIR / "load" / "vonix",
    ("load", "database"): BASE_LOG_DIR / "load" / "database",
    ("pipeline", "executions"): BASE_LOG_DIR / "pipeline" / "executions",
    ("pipeline", "errors"): BASE_LOG_DIR / "pipeline" / "errors",
    ("system", "scheduler"): BASE_LOG_DIR / "system" / "scheduler",
    ("system", "database"): BASE_LOG_DIR / "system" / "database",
}

_SENSITIVE_FILTER = SensitiveDataFilter()
_FORMATTER = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)


def _normalize_service_name(servico: str) -> str:
    return (servico or "geral").strip().lower().replace(" ", "_")


def build_log_filepath(
    categoria: str,
    servico: str,
    base_dir: Optional[Path] = None,
    execution_dt: Optional[datetime] = None,
) -> Path:
    """
    Constrói o caminho do arquivo de log no formato:
    <base_dir>/<categoria>/<servico>/log_<categoria>_<servico>_<dia>_<horario>.log
    """
    resolved_base = base_dir if base_dir is not None else BASE_LOG_DIR
    dt = execution_dt or _EXECUTION_STARTED_AT
    cat = categoria.strip().lower()
    srv = _normalize_service_name(servico)
    target_dir = SERVICE_DIRECTORIES.get((cat, srv), resolved_base / cat / srv)
    if resolved_base != BASE_LOG_DIR:
        target_dir = resolved_base / cat / srv

    target_dir.mkdir(parents=True, exist_ok=True)
    dia = dt.strftime("%Y-%m-%d")
    horario = dt.strftime("%H%M%S")
    filename = f"log_{cat}_{srv}_{dia}_{horario}.log"
    return target_dir / filename


def _get_or_create_error_handler(
    base_dir: Optional[Path] = None,
    execution_dt: Optional[datetime] = None,
) -> logging.FileHandler:
    error_logger = logging.getLogger("rivex.pipeline.errors")
    error_path = build_log_filepath("pipeline", "errors", base_dir=base_dir, execution_dt=execution_dt)

    for handler in error_logger.handlers:
        if isinstance(handler, logging.FileHandler) and Path(handler.baseFilename) == error_path.resolve():
            return handler

    handler = logging.FileHandler(error_path, encoding="utf-8", delay=True)
    handler.setLevel(logging.ERROR)
    handler.setFormatter(_FORMATTER)
    handler.addFilter(_SENSITIVE_FILTER)
    error_logger.setLevel(logging.ERROR)
    error_logger.propagate = False
    error_logger.addHandler(handler)
    return handler


def get_service_logger(
    categoria: str,
    servico: str,
    level: int = logging.INFO,
    base_dir: Optional[Path] = None,
    execution_dt: Optional[datetime] = None,
    mirror_errors: bool = True,
) -> logging.Logger:
    """
    Retorna um logger isolado por categoria e serviço com redação automática de credenciais
    e espelhamento opcional de erros críticos para pipeline/errors.
    """
    cat = categoria.strip().lower()
    srv = _normalize_service_name(servico)
    logger_name = f"rivex.{cat}.{srv}"
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    logger.propagate = False

    log_path = build_log_filepath(cat, srv, base_dir=base_dir, execution_dt=execution_dt)
    resolved_path = log_path.resolve()

    has_service_handler = any(
        isinstance(h, logging.FileHandler) and Path(h.baseFilename) == resolved_path
        for h in logger.handlers
    )
    if not has_service_handler:
        file_handler = logging.FileHandler(log_path, encoding="utf-8", delay=True)
        file_handler.setLevel(level)
        file_handler.setFormatter(_FORMATTER)
        file_handler.addFilter(_SENSITIVE_FILTER)
        logger.addHandler(file_handler)

    if mirror_errors and not (cat == "pipeline" and srv == "errors"):
        error_handler = _get_or_create_error_handler(base_dir=base_dir, execution_dt=execution_dt)
        error_path = Path(error_handler.baseFilename)
        has_error_handler = any(
            isinstance(h, logging.FileHandler) and Path(h.baseFilename) == error_path
            for h in logger.handlers
        )
        if not has_error_handler:
            logger.addHandler(error_handler)

    return logger


class LoggingConfig:
    """Wrapper base para logging estruturado de um serviço específico."""

    def __init__(self, categoria: str, servico: str, level: int = logging.INFO):
        self.categoria = categoria
        self.servico = _normalize_service_name(servico)
        self.log = get_service_logger(categoria, self.servico, level=level)

    def log_info(self, operacao: str, detalhes: Any = None) -> None:
        if detalhes is not None:
            self.log.info("%s | detalhes=%s", operacao, redact_value(detalhes))
        else:
            self.log.info("%s", operacao)

    def log_warning(self, operacao: str, detalhes: Any = None) -> None:
        if detalhes is not None:
            self.log.warning("%s | detalhes=%s", operacao, redact_value(detalhes))
        else:
            self.log.warning("%s", operacao)

    def log_erro(self, operacao: str, erro: Any = None, contexto: Any = None) -> None:
        erro_seguro = redact_text(str(erro)) if erro is not None else None
        ctx_seguro = redact_value(contexto) if contexto is not None else None
        if erro_seguro and ctx_seguro is not None:
            self.log.error(
                "%s | erro=%s | contexto=%s",
                operacao,
                erro_seguro,
                ctx_seguro,
                exc_info=isinstance(erro, BaseException),
            )
        elif erro_seguro:
            self.log.error(
                "%s | erro=%s",
                operacao,
                erro_seguro,
                exc_info=isinstance(erro, BaseException),
            )
        else:
            self.log.error("%s", operacao)


class ExtractLogger:
    """Logger para requisições HTTP e falhas de extração por discador."""

    def __init__(self, servico: str = "callix"):
        self.servico = _normalize_service_name(servico)
        self.log_conf = LoggingConfig("extract", self.servico)

    def registrar_requisicao(
        self,
        url: str,
        status_code: int,
        headers: Optional[Dict[str, Any]] = None,
        payload: Any = None,
        metodo: str = "REQUEST",
        duration_ms: Optional[float] = None,
    ) -> None:
        url_segura = redact_url(url)
        headers_seguros = redact_value(headers or {})
        payload_seguro = redact_value(payload)
        duracao = f"{duration_ms:.1f}ms" if duration_ms is not None else "n/a"

        self.log_conf.log.info(
            "HTTP_OK | servico=%s | metodo=%s | status=%s | duracao=%s | url=%s | headers=%s | payload=%s",
            self.servico,
            metodo,
            status_code,
            duracao,
            url_segura,
            headers_seguros,
            payload_seguro,
        )

    def registrar_falha(
        self,
        url: str,
        status_code: Optional[int],
        headers: Optional[Dict[str, Any]] = None,
        payload: Any = None,
        erro: Optional[BaseException] = None,
        metodo: str = "REQUEST",
        duration_ms: Optional[float] = None,
    ) -> None:
        url_segura = redact_url(url)
        headers_seguros = redact_value(headers or {})
        payload_seguro = redact_value(payload)
        duracao = f"{duration_ms:.1f}ms" if duration_ms is not None else "n/a"
        erro_msg = redact_text(str(erro)) if erro else "HTTP status de erro"

        self.log_conf.log.error(
            "HTTP_FAIL | servico=%s | metodo=%s | status=%s | duracao=%s | url=%s | headers=%s | payload=%s | erro=%s",
            self.servico,
            metodo,
            status_code,
            duracao,
            url_segura,
            headers_seguros,
            payload_seguro,
            erro_msg,
            exc_info=isinstance(erro, BaseException),
        )


class TransformLogger:
    """Logger para validação, limpeza e empacotamento de dados por discador."""

    def __init__(self, servico: str = "callix"):
        self.servico = _normalize_service_name(servico)
        self.log_conf = LoggingConfig("transform", self.servico)

    def registrar_limpeza_chamadas(self, pacote: Any) -> None:
        if hasattr(pacote, "model_dump"):
            dados = pacote.model_dump()
            resumo = {
                "id": dados.get("id"),
                "cliente": dados.get("cliente"),
                "tech": dados.get("tech"),
                "data": str(dados.get("data")),
                "chamadas": dados.get("chamadas"),
            }
        else:
            resumo = {
                "cliente": pacote.get("cliente") or pacote.get("cliente_nome"),
                "tech": pacote.get("tech"),
                "data": pacote.get("data"),
                "chamadas": pacote.get("chamadas"),
            }
        self.log_conf.log.info(
            "TRANSFORM_CHAMADAS | servico=%s | resumo=%s",
            self.servico,
            redact_value(resumo),
        )

    def registrar_limpeza_agente(self, dados_agente: list[Dict[str, Any]] | Dict[str, Any]) -> None:
        total = len(dados_agente) if isinstance(dados_agente, list) else 1
        self.log_conf.log.info(
            "TRANSFORM_AGENTES | servico=%s | total_registros=%s",
            self.servico,
            total,
        )

    def registrar_erro_transformacao(self, etapa: str, erro: BaseException, cliente: Optional[str] = None) -> None:
        self.log_conf.log_erro(
            f"TRANSFORM_FAIL | servico={self.servico} | etapa={etapa}",
            erro=erro,
            contexto={"cliente": cliente} if cliente else None,
        )


class LoadLogger:
    """Logger para operações de persistência no banco de dados por discador ou módulo."""

    def __init__(self, servico: str = "database"):
        self.servico = _normalize_service_name(servico)
        self.log_conf = LoggingConfig("load", self.servico)

    def registrar_envio_db(self, operacao: str, total_agentes: int = 0, cliente: Optional[str] = None) -> None:
        self.log_conf.log.info(
            "DB_LOAD_OK | servico=%s | operacao=%s | cliente=%s | agentes=%s",
            self.servico,
            operacao,
            cliente or "n/a",
            total_agentes,
        )

    def registrar_erro_db(self, operacao: str, erro: BaseException, cliente: Optional[str] = None) -> None:
        self.log_conf.log_erro(
            f"DB_LOAD_FAIL | servico={self.servico} | operacao={operacao}",
            erro=erro,
            contexto={"cliente": cliente} if cliente else None,
        )


class PipelineLogger:
    """Logger para ciclo de vida das pipelines (início, progresso, resumo e falhas)."""

    def __init__(self, servico: str = "executions"):
        self.servico = _normalize_service_name(servico)
        self.log_conf = LoggingConfig("pipeline", "executions")

    def inicio(self, mensagem: str, **campos: Any) -> None:
        self.log_conf.log.info(
            "PIPELINE_START | pipeline=%s | %s | contexto=%s",
            self.servico,
            mensagem,
            redact_value(campos) if campos else {},
        )

    def etapa(self, mensagem: str, **campos: Any) -> None:
        self.log_conf.log.info(
            "PIPELINE_STEP | pipeline=%s | %s | contexto=%s",
            self.servico,
            mensagem,
            redact_value(campos) if campos else {},
        )

    def aviso(self, mensagem: str, **campos: Any) -> None:
        self.log_conf.log.warning(
            "PIPELINE_WARN | pipeline=%s | %s | contexto=%s",
            self.servico,
            mensagem,
            redact_value(campos) if campos else {},
        )

    def erro(self, mensagem: str, erro: Optional[BaseException] = None, **campos: Any) -> None:
        self.log_conf.log_erro(
            f"PIPELINE_ERROR | pipeline={self.servico} | {mensagem}",
            erro=erro,
            contexto=campos if campos else None,
        )

    def fim(self, mensagem: str, **campos: Any) -> None:
        self.log_conf.log.info(
            "PIPELINE_END | pipeline=%s | %s | contexto=%s",
            self.servico,
            mensagem,
            redact_value(campos) if campos else {},
        )


class SystemLogger:
    """Logger para infraestrutura de sistema (database, scheduler/retry)."""

    def __init__(self, servico: str = "database"):
        self.servico = _normalize_service_name(servico)
        self.log_conf = LoggingConfig("system", self.servico)

    def info(self, mensagem: str, **campos: Any) -> None:
        self.log_conf.log_info(f"SYSTEM | servico={self.servico} | {mensagem}", campos or None)

    def aviso(self, mensagem: str, **campos: Any) -> None:
        self.log_conf.log_warning(f"SYSTEM_WARN | servico={self.servico} | {mensagem}", campos or None)

    def erro(self, mensagem: str, erro: Optional[BaseException] = None, **campos: Any) -> None:
        self.log_conf.log_erro(f"SYSTEM_ERROR | servico={self.servico} | {mensagem}", erro=erro, contexto=campos or None)


class LoggingDatabaseConfig:
    """Facade compatível para logs de configuração e operações de banco de dados."""

    def __init__(self, servico: str = "database"):
        self.system_log = SystemLogger("database")
        self.load_log = LoadLogger(servico)

    def conexao_aberta(self, host: Optional[str] = None, database: Optional[str] = None) -> None:
        self.system_log.info("Conexão com banco de dados estabelecida", host=host, database=database)

    def conexao_fechada(self) -> None:
        self.system_log.info("Conexão com banco de dados encerrada")

    def erro_configuracao(self, erro: BaseException) -> None:
        self.system_log.erro("Erro de configuração ou criação de objeto no banco de dados", erro=erro)

    def registro_erro_envio(self, erro: BaseException) -> None:
        self.load_log.registrar_erro_db("enviar_dados_telefonia", erro)

    def erro_db_comentado(self, comentario: str, erro: BaseException) -> None:
        self.load_log.registrar_erro_db(comentario, erro)

    def conferencia_dados(self, total_registros: Any = None) -> None:
        self.load_log.registrar_envio_db("conferencia_dados", total_agentes=total_registros if isinstance(total_registros, int) else 0)

    def erro_consulta(self, operacao: str, erro: BaseException) -> None:
        self.system_log.erro("Erro durante consulta no banco de dados", erro=erro, operacao=operacao)
