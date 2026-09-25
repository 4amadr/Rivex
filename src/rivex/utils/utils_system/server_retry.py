from functools import wraps
import logging
import time
import requests

logger = logging.getLogger(__name__)


def tentar_novamente(tentativas=3, atraso_inicial=1, backoff=2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for tentativa in range(1, tentativas + 1):
                try:
                    return func(*args, **kwargs)
                except (ConnectionError, TimeoutError, requests.exceptions.RequestException) as e:
                    if i == tentativas:
                        raise
            espera = atraso_inicial * (backoff ** (i - 1))
            logger.warning(f"Tentativa {i}/{tentativas} falhou. Aguardando {espera}s...")
            time.sleep(espera)
        return wrapper
    return decorator

