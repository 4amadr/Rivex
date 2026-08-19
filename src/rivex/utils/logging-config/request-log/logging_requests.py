import logging
from typing import Optional, Dict, Any

log = logging.getLogger(__name__)

headers_sensiveis = {'Authorization', 'Token', 'X-API-Key', 'Cookie'}

def req_log(response, url, headers, payload):
    log.info("Informações da requisição:\n" \
    f"[URL]: {url}\n" \
    f"[HEADER]: {headers}\n" 
    f"[PAYLOAD]: {payload}\n"
    f"[JSON]: {response.json()}\n"
    f"[TEXTO]: {response.text}")