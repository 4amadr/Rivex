import logging
import os
import logging.config
from typing import Dict, Any, Optional

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
        "etl.extract": {
            "level": "INFO",
            "handlers": ["extract_file", "console"],
            "propagate": False
        },
        "etl.transform": {
            "level": "INFO",
            "handlers": ["transform_file", "console"],
            "propagate": False
        },
        "etl.load": {
            "level": "INFO",
            "handlers": ["load_file", "console"],
            "propagate": False
        }
    }
}

logging.config.dictConfig(LOGGING_CONFIG)

class ExtractLogger:
    def __init__(self, execution_id: str = ""):
        self.logger = logging.getLogger("etl.extract")
        self.execution_id = execution_id
        
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

        self.logger.info(
            "[%s] REQ HTTP | STATUS: %s | URL: %s | HEADERS: %s | PAYLOAD: %s | PREVIEW: %s",
            self.execution_id, status_code, url, headers_seguros, payload_seguro, preview
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
            "[%s] REQ FAIL | URL: %s | STATUS: %s | HEADERS: %s | PAYLOAD: %s | ERRO: %s",
            self.execution_id, url, status_code, headers_seguros, payload_seguro, erro,
            exc_info=bool(erro)  # Grava o traceback completo no log se houver uma exceção
        )
        
class TransformLogger:
    def __init__(self, execution_id: str = ""):
        self.logger = logging.getLogger("etl.transform")
        self.execution_id = execution_id
        
    def registrar_limpeza_chamadas(self, cliente, chamadas, aceitas, recusadas, abandonadas, agressividade):
        self.logger.info("[%s] DADOS LIMPOS DO CLIENTE %s | CHAMADAS: %s | ACEITAS: %s | RECUSADAS: %s | ABANDONADAS: %s | AGRESSIVIDADE: %s", self.execution_id, cliente, chamadas, aceitas, recusadas, abandonadas, agressividade)
        

    def registrar_limpeza_rota(self, dados_cliente_rota):
        self.logger.info("[%s] DADOS LIMPOS DA ROTA: %s",self.execution_id, dados_cliente_rota)
        
    def registrar_limpeza_agente(self, dados_agente):
        self.logger.info("[%s] DADOS DO OPERADOR: %s", self.execution_id, dados_agente)
        
class LoadLogger:
    def __init__(self, execution_id: str = ""):
        self.logger = logging.getLogger("etl.load")
        self.execution_id = execution_id
        
    def registrar_envio_db(self, query, dados):
        self.logger.info("[%s] CARREGAMENTO DB | QUERY: %s | DADOS INSERIDOS %s", self.execution_id, query, dados)
        
        
    def registrar_erro_db(self, query, dados, erro: Exception):
        self.logger.error("[%s] ERRO AO CARREGAR DADOS NO BANCO | QUERY: %s | ERRO %s | DADOS %s", self.execution_id, query, erro, dados)
        
    
        