from __future__ import annotations

import time
from typing import Any, Optional

import requests

from src.rivex.domain.exceptions import ErroHttpDiscador
from src.rivex.utils.logging_config import ExtractLogger


def _obter_espera_retry_after(resposta: requests.Response, padrao: float) -> float:
    valor = resposta.headers.get("Retry-After")
    if valor:
        try:
            segundos = float(valor)
            if segundos > 0:
                return segundos
        except ValueError:
            pass
    return padrao


class HttpRequisitions:
    """Cliente HTTP centralizado com logging redigido e política de retry/erro."""

    def __init__(
        self,
        session: requests.Session,
        servico: str = "callix",
        retry_429_wait: float = 60.0,
        retry_429_max: int = 5,
        retry_5xx_max: int = 3,
        backoff_5xx_inicial: float = 1.0,
    ):
        self.session = session
        self.extract_logger = ExtractLogger(servico=servico)
        self.retry_429_wait = retry_429_wait
        self.retry_429_max = retry_429_max
        self.retry_5xx_max = retry_5xx_max
        self.backoff_5xx_inicial = backoff_5xx_inicial

    def _requisitar(
        self,
        metodo: str,
        url: str,
        headers: dict,
        params: Optional[dict] = None,
        data: Optional[dict] = None,
        json: Optional[dict] = None,
        cookies: Optional[str] = None,
        verify: bool = True,
    ) -> requests.Response:
        payload_log: Any = params if params is not None else (data if data is not None else json)
        tentativas_429 = 0
        tentativas_5xx_ou_rede = 0

        while True:
            inicio = time.perf_counter()
            try:
                resposta = self.session.request(
                    metodo,
                    url,
                    params=params,
                    data=data,
                    json=json,
                    headers=headers,
                    cookies=cookies,
                    verify=verify,
                    timeout=(10, 60),
                )
            except requests.RequestException as erro:
                duracao_ms = (time.perf_counter() - inicio) * 1000
                self.extract_logger.registrar_falha(
                    url, None, headers, payload_log, erro=erro, metodo=metodo, duration_ms=duracao_ms
                )
                if tentativas_5xx_ou_rede >= self.retry_5xx_max:
                    raise
                espera = self.backoff_5xx_inicial * (2 ** tentativas_5xx_ou_rede)
                tentativas_5xx_ou_rede += 1
                self.extract_logger.log_conf.log_warning(
                    f"Erro de rede em {url}; aguardando {espera:.1f}s (retry {tentativas_5xx_ou_rede}/{self.retry_5xx_max})"
                )
                time.sleep(espera)
                continue

            duracao_ms = (time.perf_counter() - inicio) * 1000

            if resposta.status_code == 429:
                self.extract_logger.registrar_falha(
                    url, resposta.status_code, headers, payload_log, metodo=metodo, duration_ms=duracao_ms
                )
                if tentativas_429 >= self.retry_429_max:
                    raise ErroHttpDiscador(
                        429,
                        url,
                        f"Rate limit (429) persistente após {self.retry_429_max} retries",
                    )
                espera = _obter_espera_retry_after(resposta, self.retry_429_wait)
                tentativas_429 += 1
                self.extract_logger.log_conf.log_warning(
                    f"HTTP 429 em {url}; aguardando {espera:.1f}s (retry {tentativas_429}/{self.retry_429_max})"
                )
                time.sleep(espera)
                continue

            if 500 <= resposta.status_code < 600:
                self.extract_logger.registrar_falha(
                    url, resposta.status_code, headers, payload_log, metodo=metodo, duration_ms=duracao_ms
                )
                if tentativas_5xx_ou_rede >= self.retry_5xx_max:
                    raise ErroHttpDiscador(
                        resposta.status_code,
                        url,
                        f"Erro de servidor após {self.retry_5xx_max} retries",
                    )
                espera = self.backoff_5xx_inicial * (2 ** tentativas_5xx_ou_rede)
                tentativas_5xx_ou_rede += 1
                self.extract_logger.log_conf.log_warning(
                    f"HTTP {resposta.status_code} em {url}; aguardando {espera:.1f}s (retry {tentativas_5xx_ou_rede}/{self.retry_5xx_max})"
                )
                time.sleep(espera)
                continue

            if resposta.status_code >= 400:
                self.extract_logger.registrar_falha(
                    url, resposta.status_code, headers, payload_log, metodo=metodo, duration_ms=duracao_ms
                )
                raise ErroHttpDiscador(resposta.status_code, url, "Resposta HTTP de erro")

            self.extract_logger.registrar_requisicao(
                url, resposta.status_code, headers, payload_log, metodo=metodo, duration_ms=duracao_ms
            )
            return resposta

    def requisicao_post_com_certificado(
        self, payload_post: dict, headers: dict, url: str, verificacao: bool
    ) -> requests.Response:
        return self._requisitar("POST", url, headers, data=payload_post, verify=verificacao)

    def requisicao_post(self, payload_post: dict, headers: dict, url: str) -> requests.Response:
        return self._requisitar("POST", url, headers, data=payload_post)

    def requisicao_post_json(self, payload_post: dict, headers: dict, url: str) -> requests.Response:
        return self._requisitar("POST", url, headers, json=payload_post)

    def requisicao_get(
        self,
        headers: dict,
        url: str,
        payload_get: dict,
        cookies_requisicao: Optional[str] = None,
    ) -> requests.Response:
        return self._requisitar("GET", url, headers, params=payload_get, cookies=cookies_requisicao)

    def requisicao_delete(
        self,
        headers: dict,
        url: str,
        cookies_requisicao: Optional[str] = None,
    ) -> requests.Response:
        return self._requisitar("DELETE", url, headers, cookies=cookies_requisicao)
