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
                except (ConnectionError, TimeoutError, requests.exceptions.RequestException) as e:
                        logger.error("Totas as tentativas falharam")
                        raise
        return wrapper
    return decorator

