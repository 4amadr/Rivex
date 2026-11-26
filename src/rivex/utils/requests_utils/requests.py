from __future__ import annotations

from typing import Any

import requests


class HttpRequisitions:
    def __init__(self, session: requests.Session, servico: str, timeout: int = 20):
        self.servico = servico
        self.session = session
        self.timeout = timeout

    def requisicao(
        self,
        url: str,
        method: str = "GET",
        headers: dict[str, str] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> requests.Response:
        http_method = method.upper()
        kwargs: dict[str, Any] = {
            "headers": headers,
            "timeout": self.timeout,
        }
        if http_method == "GET":
            kwargs["params"] = payload
        else:
            kwargs["data"] = payload

        return self.session.request(method=http_method, url=url, **kwargs)

    def req_get(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> requests.Response:
        return self.requisicao(url=url, method="GET", headers=headers, payload=payload)

    def req_post(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> requests.Response:
        return self.requisicao(url=url, method="POST", headers=headers, payload=payload)


