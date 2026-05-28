from functools import wraps
import logging
import time

logger = logging.getLogger(__name__)


def tentar_novamente(tentativas=3, atraso=20):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for tentativa in range(1, tentativas + 1):
                try:
                    return func(*args, **kwargs)
                except ConnectionError as e:
                    logger.warning(f"Falha na tentativa {tentativa} de {tentativas} para {func.__name__}. Erro: {e}")
                    if tentativa == tentativas:
                        logger.error("Totas as tentativas falharam")
                        raise
                    time.sleep(atraso)
        return wrapper
    return decorator

