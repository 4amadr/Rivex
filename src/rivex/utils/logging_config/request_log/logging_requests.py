import logging
import os
from datetime import datetime

HEADERS_SENSIVEIS = {'Authorization', 'Token', 'X-API-Key', 'Cookie'}

os.makedirs("Log/req-log", exist_ok=True)

data_execucao = datetime.now().strftime("%Y-%m-%d")
arquivo_log = f"Log/req-log/registro-exec-dia-{data_execucao}.log"

formato = logging.Formatter(
    "%(asctime)s | %(levelname)-8s | [%(filename)s:%(lineno)d] %(message)s",
    datefmt="%y-%m-%d %H:%M:%S"
)

# Único logger do módulo. Tudo que precisar logar (req_log, res_log,
# ou qualquer outra função aqui) usa ESTE objeto, não um novo
# getLogger(__name__) desconectado dos handlers.
log = logging.getLogger("Req")
log.setLevel(logging.INFO)
log.propagate = False  # evita log duplicado caso o root logger também tenha handler

if not log.handlers:  # evita handler duplicado se o módulo for importado mais de uma vez
    file_handler = logging.FileHandler(arquivo_log, encoding="utf-8")
    file_handler.setFormatter(formato)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formato)

    log.addHandler(file_handler)
    log.addHandler(console_handler)


def limpar_headers(headers: dict, sensiveis: set = HEADERS_SENSIVEIS) -> dict:
    """
    Retorna uma cópia do dict de headers com os valores sensíveis mascarados,
    comparando por nome sem diferenciar maiúsculas/minúsculas.
    """
    sensiveis_lower = {nome.lower() for nome in sensiveis}
    return {
        chave: ("*******" if chave.lower() in sensiveis_lower else valor)
        for chave, valor in headers.items()
    }


def req_log(url, headers, payload):
    """Corpo da requisição"""
    headers_limpos = limpar_headers(headers)
    log.info(
        "Corpo da requisição:\n"
        f"[URL]: {url}\n"
        f"[HEADER]: {headers_limpos}\n"
        f"[PAYLOAD]: {payload}\n"
    )


def res_log(response):
    """Resposta do ambiente"""
    log.info(f"Registro da resposta:\nResposta da requisição: {response.status_code}\n")