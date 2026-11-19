from __future__ import annotations

from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.rivex.data_processing.IPBox.limpeza_ipbox import (
    empacotar_dados_agentes,
    empacotar_dados_clientes,
)
from src.rivex.data_processing.Vonix.cleaning_vonix import get_tech_vez
from src.rivex.domain.exceptions import ErroAutenticacao, ErroHttpDiscador
from src.rivex.domain.registros import ClienteRegistro, OperadorRegistro, ResumoExecucao
from src.rivex.environments.discadores.Callix.callix_req import CAllixRequisition
from src.rivex.environments.discadores.IPBox.colect_ipbox import IpboxInit
from src.rivex.environments.discadores.vonix.fluxo_coleta import ExecucaoVonix
from src.rivex.utils.requests_utils.requests import HttpRequisitions


def test_callix_req_finally_falha_no_logout_nao_descarta_dados():
    req = CAllixRequisition(data="2026-11-17")
    with (
        patch.object(req, "criar_sessao_usuario", return_value="sess-tok"),
        patch.object(
            req,
            "requisicao_get_sessao",
            return_value=SimpleNamespace(json=lambda: {"data": []}),
        ),
        patch.object(
            req,
            "encerrar_sessao_usuario",
            side_effect=RuntimeError("503 no logout"),
        ),
    ):
        dados = req.requisicao_callix("empresa", "tok-api")

    assert set(dados.keys()) == {
        "accounts",
        "campanhas",
        "outbound_routes",
        "chamadas_completas",
        "user_performance_histories",
    }


def test_http_429_espera_60s_e_tenta_ate_5_vezes():
    session = MagicMock()
    resp_429 = SimpleNamespace(status_code=429, headers={})
    resp_200 = SimpleNamespace(status_code=200, headers={})
    session.request.side_effect = [resp_429, resp_429, resp_200]

    hr = HttpRequisitions(session=session, servico="callix", retry_429_wait=60, retry_429_max=5)
    with patch("src.rivex.utils.requests_utils.requests.time.sleep") as mock_sleep:
        resp = hr.requisicao_get(headers={}, url="https://api.test/v1", payload_get={})

    assert resp.status_code == 200
    assert mock_sleep.call_count == 2
    mock_sleep.assert_called_with(60.0)


def test_http_429_esgota_5_retries_e_levanta_erro():
    session = MagicMock()
    session.request.return_value = SimpleNamespace(status_code=429, headers={})

    hr = HttpRequisitions(session=session, servico="callix", retry_429_wait=60, retry_429_max=5)
    with (
        patch("src.rivex.utils.requests_utils.requests.time.sleep") as mock_sleep,
        pytest.raises(ErroHttpDiscador) as exc_info,
    ):
        hr.requisicao_get(headers={}, url="https://api.test/v1", payload_get={})

    assert exc_info.value.status_code == 429
    assert session.request.call_count == 6
    assert mock_sleep.call_count == 5


@pytest.mark.parametrize("status_code", [400, 401, 403, 404])
def test_http_4xx_levanta_erro_tipado_sem_retry(status_code: int):
    session = MagicMock()
    session.request.return_value = SimpleNamespace(status_code=status_code, headers={})

    hr = HttpRequisitions(session=session, servico="callix")
    with pytest.raises(ErroHttpDiscador) as exc_info:
        hr.requisicao_get(headers={}, url="https://api.test/v1", payload_get={})

    assert exc_info.value.status_code == status_code
    assert session.request.call_count == 1


def test_pydantic_cliente_sem_tech_gera_id_5_digitos_e_casa_com_operador():
    cliente = ClienteRegistro(
        discador="Vonix",
        tech=0,
        cliente="cliente_sem_tech",
        data=date(2026, 11, 17),
        chamadas=10,
        aceitas=5,
        recusadas=3,
        abandonadas=2,
        agressividade=1.5,
    )
    assert 10000 <= cliente.id <= 99999
    assert cliente.tech == cliente.id

    operador = OperadorRegistro(
        id=cliente.id,
        discador="Vonix",
        tech=cliente.tech,
        cliente=cliente.cliente,
        data=cliente.data,
        nome_operador="Joao",
        chamada_aceita=5,
    )
    assert operador.id == cliente.id
    assert operador.tech == cliente.tech


def test_ipbox_empacotar_operadores_contratados_e_id_casado():
    html_op = """
    <div id="gridUsuarios">
      <table class="grid">
        <tr class="linha1"><td>Ana</td><td>Agente</td></tr>
        <tr class="linha2"><td>Bruno</td><td>Agente</td></tr>
        <tr class="linha1"><td>Supervisor</td><td>Admin</td></tr>
      </table>
    </div>
    <select id="obj_fila_valor_overdial"><option selected="selected">3.2</option></select>
    """
    chamadas_json = {
        "data": {
            "resultado": {
                "total": {"qtd": 50},
                "ATENDIDO": {"qtd": 20},
                "OCUPADO": {"qtd": 10},
                "SEM_RESPOSTA": {"qtd": 5},
                "DESCONHECIDO": {"qtd": 5},
                "CONGESTIONADO": {"qtd": 10},
            }
        }
    }
    cliente_reg = empacotar_dados_clientes(
        chamadas_json=chamadas_json,
        cliente="Cliente Sem Tech",
        data=date(2026, 11, 17),
        agressividade=html_op,
        operadores=html_op,
    )
    assert cliente_reg.operadores_contratados == 2
    assert 10000 <= cliente_reg.id <= 99999

    op_reg = empacotar_dados_agentes(
        {"agente": "Ana", "atendimentos": "12"},
        cliente_reg,
        date(2026, 11, 17),
    )
    assert op_reg.id == cliente_reg.id
    assert op_reg.tech == cliente_reg.tech


def test_login_invalido_ipbox_e_vonix_levantam_erro_autenticacao():
    ipbox = IpboxInit(login="u", senha="p", data="20261117", url="http://ipbox.test")
    with (
        patch.object(
            ipbox.http_client,
            "requisicao_post",
            return_value=SimpleNamespace(
                url="http://ipbox.test/contech/autenticacao.php",
                text='<form><input name="doLogin" /></form>',
            ),
        ),
        pytest.raises(ErroAutenticacao),
    ):
        ipbox.login_ipbox()

    vonix = ExecucaoVonix(login="u", senha="p", data="17/11/2026", url_base="http://vonix.test")
    with (
        patch.object(
            vonix.http_requisitions,
            "requisicao_post",
            return_value=SimpleNamespace(url="http://vonix.test/login/signin", text="Login"),
        ),
        pytest.raises(ErroAutenticacao),
    ):
        vonix.login_vonix("tok")


def test_vonix_get_tech_vez_exato_e_ambiguo():
    techs = [
        {"tech": "1010#01", "nome": "Real Promotora"},
        {"tech": "1010#02", "nome": "Real Cred"},
    ]
    assert get_tech_vez(techs, "realpromotora") == 101001
    # "real" casa com duas techs -> não adivinha, retorna 0 para acionar ID randômico
    assert get_tech_vez(techs, "real") == 0


def test_main_retorna_exit_code_1_quando_pipeline_falha():
    import main

    fake_settings = SimpleNamespace(max_falhas_pipeline=0)
    with (
        patch("sys.argv", ["main.py", "--pipeline", "callix", "--data", "2026-11-17"]),
        patch("main.carregar_settings", return_value=fake_settings),
        patch(
            "main._executar_pipeline",
            return_value=ResumoExecucao(pipeline="callix", total=1, persistidos=0, falhas=["err"]),
        ),
    ):
        assert main.main() == 1


def test_logger_respeita_isolamento_em_testes(tmp_path):
    from src.rivex.utils.logging_config.logging_config import BASE_LOG_DIR, get_service_logger

    logger = get_service_logger("extract", "callix")
    caminhos = [h.baseFilename for h in logger.handlers if hasattr(h, "baseFilename")]
    assert caminhos
    assert all(str(BASE_LOG_DIR) in c for c in caminhos)

