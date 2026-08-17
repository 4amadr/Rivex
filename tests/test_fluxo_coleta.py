import pytest
from unittest.mock import MagicMock, patch
from src.rivex.environments.discadores.vonix.fluxo_coleta import ExecucaoVonix

def test_get_clientes_ambiente_calls_requisicao_get_with_correct_url():
    # Setup mock dependencies
    login = "test_login"
    senha = "test_password"
    data = "2026-07-14"
    url_base = "http://mock-vonix.com"
    
    with patch("src.rivex.environments.discadores.vonix.fluxo_coleta.HttpRequisitions") as MockHttpRequisitions:
        mock_http_instance = MagicMock()
        MockHttpRequisitions.return_value = mock_http_instance
        
        # Instantiate ExecucaoVonix
        execucao = ExecucaoVonix(login, senha, data, url_base)
        
        # Call get_clientes_ambiente()
        execucao.get_clientes_ambiente()
        
        # Verify requisicao_get was called with expected url (which comes from url._url_base())
        mock_http_instance.requisicao_get.assert_called_once_with(
            payload_get={},
            headers={},
            url="http://mock-vonix.com"
        )
