import logging
import os
import logging.config

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

class ExtractLogger:
    def __init__(self, execution_id: str = ""):
        self.logger = logging.getLogger("etl.extract")
        self.execution_id = execution_id
        
    def registrar_requisicao(self, url, status_code, headers, payload, response_text):
        preview = response_text[:200] if response_text else ""
        self.logger.info(
            "[%s] REQ HTTP | STATUS: %s | URL: %s | HEADERS: %s | PAYLOAD: %s | PREVIEW: %s",
            self.execution_id, status_code, url, headers, payload, preview
        )
        
    def registrar_falha(self, url, status_code, headers, payload):
        self.logger.error("[%s] REQ FAIL | URL: %s | STATUS: %s | HEADERS %s | PAYLOAD %s",
                          self.execution_id, url, status_code, headers, payload)
        

    
    
        