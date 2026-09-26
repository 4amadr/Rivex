import logging
import os
import logging.config
from typing import Dict, Any, Optional
from src.rivex.utils.infra_utils.date_config import DateConfig
import uuid

LOG_DIRS = {
    "extract": os.path.join("Log", "extract"),
    "transform": os.path.join("Log", "transform"),
    "load": os.path.join("Log", "load"),
}

for path in LOG_DIRS.values():
    os.makedirs(path, exist_ok=True)

# 2. Configuração centralizada dos Loggers e Arquivos
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "detailed": {
            "format": "%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        }
    },
    "handlers": {
        "extract_file": {
            "class": "logging.FileHandler",
            "filename": os.path.join(LOG_DIRS["extract"], "extract.log"),
            "formatter": "detailed",
            "encoding": "utf-8"
        },
        "transform_file": {
            "class": "logging.FileHandler",
            "filename": os.path.join(LOG_DIRS["transform"], "transform.log"),
            "formatter": "detailed",
            "encoding": "utf-8"
        },
        "load_file": {
            "class": "logging.FileHandler",
            "filename": os.path.join(LOG_DIRS["load"], "load.log"),
            "formatter": "detailed",
            "encoding": "utf-8"
        },
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "detailed",
            "level": "INFO"
        }
    },
    "loggers": {
        "etl.config": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False
        },
        
        "etl.extract": {
            "level": "INFO",
            "handlers": ["extract_file"],
            "propagate": False
        },
        "etl.transform": {
            "level": "INFO",
            "handlers": ["transform_file"],
            "propagate": False
        },
        "etl.load": {
            "level": "INFO",
            "handlers": ["load_file"],
            "propagate": False
        }
    }
}

logging.config.dictConfig(LOGGING_CONFIG)

class LoggingConfig:
    def __init__(self, subdiretorio):
        self.log = logging.getLogger()
        self.data_exec = DateConfig.data_selecionadas()
        self.sufixo_arquivo = self.data_exec
        self.subdiretorio = subdiretorio
    
    def infos_logging(self):
        self.log.info(f"Data da coleta de dados Rivex {self.data_exec}")
        self.log.info(f"Subdiretório: {self.subdiretorio}")      

class ExtractLogger:
    def __init__(self):
        self.log_conf = LoggingConfig("extract")
        
    def _ocultar_dados_sensiveis(self, dados: Any) -> Any:
        """Substitui valores de chaves sensíveis por um texto de redacção."""
        if not isinstance(dados, dict):
            return dados
        
        chaves_sensiveis = {"authorization", "token", "password", "secret", "apikey", "api_key"}
        dados_limpos = dados.copy()
        
        for chave in dados_limpos:
            if str(chave).lower() in chaves_sensiveis:
                dados_limpos[chave] = "***OCULTO***"
        return dados_limpos

        
    def registrar_requisicao(
        self, 
        url: str, 
        status_code: int, 
        headers: Dict[str, Any], 
        payload: Any, 
        response_text: Optional[str] = None
    ) -> None:
        headers_seguros = self._ocultar_dados_sensiveis(headers)
        payload_seguro = self._ocultar_dados_sensiveis(payload) if isinstance(payload, dict) else payload
        preview = str(response_text)[:200] if response_text else ""

        self.log_conf.log.info(
            "[%s] REQ HTTP | STATUS: %s | URL: %s | HEADERS: %s | PAYLOAD: %s | PREVIEW: %s",
            self.log_conf.data_exec, status_code, url, headers_seguros, payload_seguro, preview
        )

    def registrar_falha(
        self, 
        url: str, 
        status_code: Optional[int], 
        headers: Dict[str, Any], 
        payload: Any, 
        erro: Optional[Exception] = None
    ) -> None:
        headers_seguros = self._ocultar_dados_sensiveis(headers)
        payload_seguro = self._ocultar_dados_sensiveis(payload) if isinstance(payload, dict) else payload
        

        self.logger.error(
            "Exec[%s] REQ FAIL | URL: %s | STATUS: %s | HEADERS: %s | PAYLOAD: %s | ERRO: %s",
            self.log_conf.data_exec, url, status_code, headers_seguros, payload_seguro, erro,
            exc_info=True(erro)  # Grava o traceback completo no log se houver uma exceção
        )
        
class TransformLogger:
    def __init__(self):
        self.log_conf = LoggingConfig('transform')
        
    def registrar_limpeza_chamadas(self, cliente, chamadas, aceitas, recusadas, abandonadas, agressividade):
        self.log_conf.log.info("Exec[%s] DATA CLIENT %s | CHAMADAS: %s | ACEITAS: %s | RECUSADAS: %s | ABANDONADAS: %s | AGRESSIVIDADE: %s", self.log_conf.data_exec, cliente, chamadas, aceitas, recusadas, abandonadas, agressividade)
        
    def registrar_limpeza_rota(self, dados_cliente_rota):
        self.log_conf.log.info("Exec[%s] ROUTE CLEAN DATA: %s",self.log_conf.data_exec, dados_cliente_rota)
        
    def registrar_limpeza_agente(self, dados_agente):
        self.log_conf.log.info("Exec[%s] OPERATOR DATA: %s", self.log_conf.data_exec, dados_agente)
        
class LoadLogger:
    def __init__(self):
        self.log_conf = LoggingConfig("load")
        
    def registrar_envio_db(self, query, dados):
        self.log_conf.log.info("Exec[%s] LOADING DB | QUERY: %s | DADOS INSERIDOS %s", self.log_conf.data_exec, query, dados)
        
        
    def registrar_erro_db(self, query, dados, erro: Exception):
        self.log_conf.log.info("[%s] ERROR LOADING DB | QUERY: %s | ERRO %s | DADOS %s", self.log_conf.data_exec, query, erro, dados)
        
class LoggingDatabaseConfig:
    def __init__(self):
        self.log_conf = LoggingConfig("database_config")
        
    def verificar_query(query):
        self.log.debug(f"QUERY UTILIZADA {query}")

    def erro_configuracao(self, erro):
        self.log.error("ERROR DB CONFIG: %s", erro, exc_info=True)

    def decode_erro(self, erro_decode):
        self.log.error(f"DECODE ERROR: {erro_decode}")
        