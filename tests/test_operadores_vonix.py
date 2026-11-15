from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.rivex.environments.discadores.vonix.fluxo_limpeza import LimpezaVonix
from src.rivex.environments.discadores.vonix.payloads_vonix import (
    headers_operadores_cliente,
    payload_de_operadores_cliente,
)
from src.rivex.pipeline.pipeline_discador.pipeline_vonix import PipelineVonix


SAMPLE_AGENT_LIST_HTML = """
<table class="grid" style="width: 100%">
  <tbody id="agents">
    <tr id="agent_9901" class="item ">
      <td class=" item"><input class="checkbox agent_checkbox" id="agent_9901_checkbox" /></td>
      <td style="text-align: left;" class=" item">Operador Exemplo 01</td>
      <td style="text-align: left;">9901</td>
      <td style="text-align: left;" nowrap>1 dia</td>
      <td style="text-align: left;">21 ONE INVEST, <u>21 ONE INVEST MANUAL</u></td>
      <td style="text-align: right;" nowrap></td>
    </tr>
    <tr id="agent_9908" class=" inactive_agent" style="display: none">
      <td class="dim item"><input class="checkbox agent_checkbox" disabled="disabled" /></td>
      <td style="text-align: left;" class="dim item">Operador Inativo</td>
      <td style="text-align: left;" class="dim">9908</td>
      <td style="text-align: left;" class="dim" nowrap>173 dias</td>
      <td style="text-align: left;" class="dim"></td>
      <td style="text-align: right;" nowrap></td>
    </tr>
  </tbody>
</table>
"""


def test_payload_e_headers_operadores_cliente():
    assert payload_de_operadores_cliente() == {}
    req_headers = headers_operadores_cliente("http://mock-vonix.com", token="tok123")
    assert req_headers["X-Requested-With"] == "XMLHttpRequest"
    assert req_headers["Referer"] == "http://mock-vonix.com/admin/agents"
    assert req_headers["X-CSRF-Token"] == "tok123"
    assert "user-agent" in req_headers


def test_limpeza_extrair_operadores_cliente_filtra_inativos():
    limpeza = LimpezaVonix()
    resp_mock = SimpleNamespace(text=SAMPLE_AGENT_LIST_HTML)
    operadores = limpeza.extrair_operadores_cliente(resp_mock, cliente="oneinvest")

    assert len(operadores) == 1
    assert operadores[0] == {
        "matricula": "9901",
        "nome": "Operador Exemplo 01",
        "ultimo_login": "1 dia",
        "filas": ["21 ONE INVEST", "21 ONE INVEST MANUAL"],
        "fila_padrao": "21 ONE INVEST MANUAL",
        "cliente": "oneinvest",
    }


def test_limpeza_extrair_operadores_cliente_vazio():
    limpeza = LimpezaVonix()
    assert limpeza.extrair_operadores_cliente("") == []
    assert limpeza.extrair_operadores_cliente(None) == []


def test_pipeline_vonix_execucao_teste_operadores_mockada():
    with patch("src.rivex.pipeline.pipeline_discador.pipeline_vonix.ExecucaoVonix") as MockExec:
        mock_exec = MagicMock()
        MockExec.return_value = mock_exec
        mock_exec.token_pronto.return_value = "tok_test"
        mock_exec.get_clientes.return_value = '<li id="container_oneinvest"></li>'
        mock_exec.get_operadores_cliente.return_value = SimpleNamespace(
            status_code=200,
            text=SAMPLE_AGENT_LIST_HTML,
        )

        pipeline = PipelineVonix(usar_db=False)
        resultado = pipeline.execucao_teste_operadores_vonix(clientes_teste=["oneinvest"])

        mock_exec.get_filtragem.assert_called_once_with("oneinvest", "tok_test")
        mock_exec.get_operadores_cliente.assert_called_once_with("tok_test")
        assert "oneinvest" in resultado
        assert len(resultado["oneinvest"]) == 1
        assert resultado["oneinvest"][0]["matricula"] == "9901"
