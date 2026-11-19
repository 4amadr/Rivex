import pytest
from src.rivex.utils.requests_utils.http_response import HttpResponse

hr = HttpResponse

'''Testes para as respostas de requisições
Regra: O argumeno deve ser o status_code da requisição'''

def test_rate_limit_raises_timeout_error():
    with pytest.raises(TimeoutError):
        hr.analista_de_erros(429)


def test_unauthorized_raises_value_error():
    with pytest.raises(ValueError):
        hr.analista_de_erros(401)


def test_forbidden_raises_permission_error():
    with pytest.raises(PermissionError):
        hr.analista_de_erros(403)
        

def test_server_error_raises_connection_error():
    with pytest.raises(ConnectionError):
        hr.analista_de_erros(500)
        