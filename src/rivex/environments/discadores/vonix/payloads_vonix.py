from src.rivex.config.settings import CredenciaisVonix

load_vonix = CredenciaisVonix()


def payload_de_login(token: str) -> dict[str, str | None]:
    return {
        "authenticity_token": token,
        "return_to": "",
        "username": load_vonix.usuario,
        "password": load_vonix.senha,
        "commit": "Entrar",
    }


def headers() -> dict[str, str]:
    return {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
    }


def payload_de_operadores_cliente() -> dict:
    return {}


def headers_operadores_cliente(url_base: str, token: str | None = None) -> dict[str, str]:
    req_headers = headers()
    req_headers.update(
        {
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{url_base}/admin/agents",
        }
    )
    if token:
        req_headers["X-CSRF-Token"] = token
    return req_headers
