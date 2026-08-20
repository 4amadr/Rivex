import logging
from datetime import datetime
import os


os.makedirs("Log/req-log", exist_ok=True)


data_execucao = datetime.now().strftime("%Y-%m-%d")
arquivo_log = f"Log/req-log/registro-exec-dia{data_execucao}.log"

formato = logging.Formatter(
    "&(asctime)s | %(levelname)-8s | [%(filename)s:%(lineno)d] &(message)s",
    datefmt="%y-%m-%d %H:%M:%S"
)

logger = logging.getLogger("Req")
logger.setLevel(logging.INFO)

file_os = logging.FileHandler(arquivo_log, encoding="utf-8")
file_os.setFormatter(formato)

# exibir no termonal
console_exibir = logging.StreamHandler()
console_exibir.setFormatter(formato)

logger.addHandler(file_os)
logger.addHandler(console_exibir)


log = logging.getLogger(__name__)

headers_sensiveis = {'Authorization', 'Token', 'X-API-Key', 'Cookie'}

def limpar_headers(headers_sensiveis, headers):
    headers_protegidos = headers.copy()

    header_lower = {
        header.lower()
        for header in headers_sensiveis
    }

    for header in headers_sensiveis:
        if header.lower() in header_lower:
            headers_protegidos[header] = "*******"
    return headers_protegidos

def req_log(url, headers, payload):
    """
    Corpo da requisição
    """
    log.info("Corpo da requisição:\n" \
    f"[URL]: {url}\n" \
    f"[HEADER]: {headers}\n" 
    f"[PAYLOAD]: {payload}\n")

def res_log(response):
    """
    Resposta do ambiente
    """
    log.info("Registro da resposta: \n" \
    f" Resposta da requisição: {response.status_code}\n")

