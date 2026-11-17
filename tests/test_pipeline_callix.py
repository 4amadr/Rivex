from unittest.mock import MagicMock, patch
import pytest

from src.rivex.pipeline.pipeline_discador.pipeline_callix import PipelineCallix
from src.rivex.data_processing.Callix.callix_clients import (
    get_clientes_servidor_callix,
    separar_clientes,
)
from src.rivex.environments.discadores.Callix.callix_get_clients import GetTokenCallix
from src.rivex.environments.discadores.Callix.sincronizar_clientes import SincroniaCallix
from src.rivex.utils.environments_utils.discador.callix.get_url_callix import UrlGetData


def _make_pipeline():
    """Cria uma instância de PipelineCallix com dependências externas (DB/HTTP/env) mockadas."""
    with (
        patch("src.rivex.pipeline.pipeline_discador.pipeline_callix.load_dotenv"),
        patch("src.rivex.pipeline.pipeline_discador.pipeline_callix.DatabaseCallix") as mock_db_callix,
        patch("src.rivex.pipeline.pipeline_discador.pipeline_callix.CallixGetClients") as mock_get_clients,
        patch("src.rivex.pipeline.pipeline_discador.pipeline_callix.SincroniaCallix") as mock_sincronia,
        patch("src.rivex.pipeline.pipeline_discador.pipeline_callix.CallixAPICollector") as mock_api,
        patch("src.rivex.pipeline.pipeline_discador.pipeline_callix.CAllixRequisition") as mock_req,
        patch.dict(
            "os.environ",
            {
                "USUARIO_CALLIX_GERAL": "admin",
                "SENHA_CALLIX_GERAL": "secret",
                "URL_CALLIX_GERAL": "https://contechsystem.callix.com.br",
                "TOKEN_CALLIX": "tok-geral",
            },
        ),
    ):
        pipeline = PipelineCallix()
        return pipeline, {
            "db_callix": mock_db_callix.return_value,
            "get_clients": mock_get_clients.return_value,
            "sincronia": mock_sincronia.return_value,
            "api": mock_api.return_value,
            "req": mock_req.return_value,
        }


def _sample_dados_brutos_api(campanhas=None, resumo_data=None):
    if campanhas is None:
        campanhas = ["101", "202"]
    if resumo_data is None:
        resumo_data = [
            {
                "attributes": {
                    "outgoing_count": 100,
                    "outgoing_completed_count": 60,
                    "outgoing_missed_count": 40,
                    "outgoing_missed_agents_count": 10,
                }
            }
        ]
    return {
        "resumo": {"data": resumo_data},
        "campanha": campanhas,
    }


def _sample_dados_brutos_req(tech_route="1036#01 - Pentagono (Tech: 103601)"):
    return {
        "accounts": {
            "data": [
                {
                    "attributes": {
                        "simultaneousWebAccessPaidQty": 10,
                        "simultaneousWebAccessPrice": 150.0,
                    }
                }
            ]
        },
        "campanhas": {
            "data": [
                {"attributes": {"powerAggressiveness": 2.5}},
                {"attributes": {"powerAggressiveness": 3.5}},
            ]
        },
        "audit_logs": {"data": []},
        "outbound_routes": {
            "data": [
                {"id": "r1", "attributes": {"name": tech_route}},
            ]
        },
        "chamadas_completas": {
            "data": [
                {"attributes": {"legs": [{"routeId": "r1"}]}}
            ]
        },
        "user_performance_histories": {
            "included": [
                {"id": "u1", "type": "users", "attributes": {"name": "Maria"}}
            ],
            "data": [
                {
                    "relationships": {"user": {"data": {"id": "u1"}}},
                    "attributes": {"answeredCount": 12},
                }
            ],
        },
    }


class TestPipelineCallixLimpeza:
    def test_limpar_dados_extrai_ids_campanha_corretamente(self):
        pipeline, _ = _make_pipeline()
        dados_api = _sample_dados_brutos_api(campanhas=["101", "202"])
        dados_req = _sample_dados_brutos_req()

        dict_limpeza, metricas_req = pipeline.limpar_dados(dados_api, dados_req)

        assert dict_limpeza is not None, "limpar_dados falhou com dados válidos de campanha"
        assert metricas_req is not None
        assert dict_limpeza["Campanha"] == [101, 202]
        assert dict_limpeza["Chamadas totais"] == 100
        assert dict_limpeza["Chamadas aceitas"] == 60
        assert dict_limpeza["Chamadas recusadas"] == 30
        assert dict_limpeza["Chamadas abandonadas"] == 10
        assert metricas_req["tech"] == "103601"
        assert metricas_req["agressividade"] == 3.0

    def test_limpar_dados_sem_campanhas(self):
        pipeline, _ = _make_pipeline()
        dados_api = _sample_dados_brutos_api(campanhas=[])
        dados_req = _sample_dados_brutos_req()

        dict_limpeza, metricas_req = pipeline.limpar_dados(dados_api, dados_req)

        assert dict_limpeza is not None, "limpar_dados não deveria falhar quando não há campanhas"
        assert dict_limpeza["Campanha"] == []

    def test_limpar_dados_resumo_vazio(self):
        pipeline, _ = _make_pipeline()
        dados_api = _sample_dados_brutos_api(resumo_data=[])
        dados_req = _sample_dados_brutos_req()

        dict_limpeza, metricas_req = pipeline.limpar_dados(dados_api, dados_req)

        assert dict_limpeza is not None, "limpar_dados não deveria falhar quando resumo['data'] está vazio"
        assert dict_limpeza["Chamadas totais"] == 0
        assert dict_limpeza["Chamadas aceitas"] == 0
        assert dict_limpeza["Chamadas recusadas"] == 0
        assert dict_limpeza["Chamadas abandonadas"] == 0


class TestPipelineCallixColeta:
    def test_coletar_dados_sucesso_e_fechamento_sessoes(self):
        pipeline, _ = _make_pipeline()

        with (
            patch("src.rivex.pipeline.pipeline_discador.pipeline_callix.CallixAPICollector") as mock_api_cls,
            patch("src.rivex.pipeline.pipeline_discador.pipeline_callix.CAllixRequisition") as mock_req_cls,
        ):
            mock_api_inst = mock_api_cls.return_value
            mock_req_inst = mock_req_cls.return_value
            mock_api_inst.api_callix.return_value = _sample_dados_brutos_api()
            mock_req_inst.requisicao_callix.return_value = _sample_dados_brutos_req()

            resultado = pipeline.coletar_dados("empresa.contech.callix.com.br", "tok-1")

        assert resultado["erro"] is None
        assert resultado["cliente"] == "empresa"
        assert resultado["dados_brutos_api"] is not None
        assert resultado["dados_brutos_req"] is not None
        mock_api_inst.session.close.assert_called_once()
        mock_req_inst.session.close.assert_called_once()

    def test_coletar_dados_erro_retorna_dict_com_erro(self):
        pipeline, _ = _make_pipeline()

        with (
            patch("src.rivex.pipeline.pipeline_discador.pipeline_callix.CallixAPICollector") as mock_api_cls,
            patch("src.rivex.pipeline.pipeline_discador.pipeline_callix.CAllixRequisition") as mock_req_cls,
        ):
            mock_api_cls.return_value.api_callix.side_effect = RuntimeError("API timeout")
            resultado = pipeline.coletar_dados("empresa.contech.callix.com.br", "tok-1")

        assert resultado["cliente"] == "empresa"
        assert resultado["dados_brutos_api"] is None
        assert resultado["dados_brutos_req"] is None
        assert isinstance(resultado["erro"], RuntimeError)
        mock_api_cls.return_value.session.close.assert_called_once()
        mock_req_cls.return_value.session.close.assert_called_once()


class TestPipelineCallixEmpacotamento:
    def test_empacotar_dados_sucesso(self):
        pipeline, _ = _make_pipeline()
        dict_limpeza = {
            "Chamadas totais": 100,
            "Chamadas aceitas": 60,
            "Chamadas recusadas": 30,
            "Chamadas abandonadas": 10,
            "Campanha": [101],
        }
        metricas_req = {
            "agressividade": 2.5,
            "chamadas_agentes": [{"agente": "Maria", "Chamadas atendidas": 12}],
            "tech": "103601",
        }

        dict_chamadas, lista_agentes = pipeline.empacotar_dados(
            dict_limpeza, metricas_req, "pentagonocontech"
        )

        assert dict_chamadas is not None
        assert dict_chamadas["cliente"] == "pentagono"
        assert dict_chamadas["tech"] == 103601
        assert len(lista_agentes) == 1
        assert lista_agentes[0]["nome_agente"] == "Maria"


class TestPipelineCallixExecutar:
    def test_executar_fluxo_completo_com_fallback_e_fechamento_conexoes(self):
        pipeline, mocks = _make_pipeline()
        mocks["get_clients"].get_infos_callix.side_effect = RuntimeError("API central fora")
        mocks["sincronia"].consultar_clientes_ativos.return_value = [
            {"cliente": "pentagono", "token": "tok-1"},
            {"cliente": "sem_token", "token": None},
        ]

        with (
            patch("src.rivex.pipeline.pipeline_discador.pipeline_callix.CallixAPICollector") as mock_api_cls,
            patch("src.rivex.pipeline.pipeline_discador.pipeline_callix.CAllixRequisition") as mock_req_cls,
        ):
            mock_api_cls.return_value.api_callix.return_value = _sample_dados_brutos_api()
            mock_req_cls.return_value.requisicao_callix.return_value = _sample_dados_brutos_req()

            pipeline.executar()

        mocks["db_callix"].db_callix.assert_called_once()
        mocks["db_callix"].fechar.assert_called_once()

    def test_executar_sem_clientes_ativos_levanta_erro_e_fecha_banco(self):
        pipeline, mocks = _make_pipeline()
        mocks["get_clients"].get_infos_callix.side_effect = RuntimeError("API central fora")
        mocks["sincronia"].consultar_clientes_ativos.return_value = []

        with pytest.raises(RuntimeError, match="Nenhum cliente ativo"):
            pipeline.executar()

        mocks["db_callix"].fechar.assert_called_once()

    def test_coletar_clientes_paralelo_loga_aviso_sem_token(self, caplog):
        pipeline, _ = _make_pipeline()
        clientes = [{"cliente": "sem_token", "token": None}]

        with caplog.at_level("WARNING"):
            resultados = pipeline.coletar_clientes_paralelo(clientes)

        assert resultados == []
        assert "sem_token" in caplog.text


class TestCallixTokenSync:
    def test_login_cliente_header_nao_duplica_contech(self):
        url_data = UrlGetData()
        assert url_data.login_cliente_header("valmcontech") == "https://valmcontech.callix.com.br/login"

    def test_login_callix_sem_chave_token_levanta_value_error_claro(self):
        with (
            patch("src.rivex.environments.discadores.Callix.callix_get_clients.HttpRequisitions") as mock_hr,
            patch.dict(
                "os.environ",
                {
                    "USUARIO_CALLIX_GERAL": "admin",
                    "SENHA_CALLIX_GERAL": "secret",
                    "TOKEN_CALLIX": "tok",
                },
            ),
        ):
            resposta = MagicMock()
            resposta.status_code = 401
            resposta.ok = False
            resposta.json.return_value = {"message": "Invalid captchaToken"}
            mock_hr.return_value.requisicao_post_json.return_value = resposta

            token_client = GetTokenCallix()
            with pytest.raises(ValueError, match="401"):
                token_client.login_callix("valmcontech")

    def test_sincronizar_nao_atribui_token_errado_quando_um_cliente_falha(self):
        with (
            patch("src.rivex.environments.discadores.Callix.sincronizar_clientes.DatabaseClientes") as mock_db_cls,
            patch("src.rivex.environments.discadores.Callix.sincronizar_clientes.GetTokenCallix") as mock_gt_cls,
        ):
            mock_db = mock_db_cls.return_value
            mock_db.buscar_clientes_sem_token.return_value = ["cli_falha", "cli_ok"]
            mock_db.consultar_view.return_value = []

            sinc = SincroniaCallix()
            # Simula fluxo_de_tokens real com GetTokenCallix real-like onde cli_falha falha e cli_ok retorna tok-ok
            mock_gt_cls.return_value.fluxo_de_tokens.return_value = {"cli_ok": "tok-ok"}

            sinc.sincronizar_clientes([{"cliente": "cli_falha", "status": 3}, {"cliente": "cli_ok", "status": 3}])

            mock_db.adicionar_token_ao_db.assert_called_once_with("tok-ok", "cli_ok")

    def test_verificar_status_clientes_trata_active_inactive_e_legado(self):
        with (
            patch("src.rivex.environments.discadores.Callix.sincronizar_clientes.DatabaseClientes"),
            patch("src.rivex.environments.discadores.Callix.sincronizar_clientes.GetTokenCallix"),
        ):
            sinc = SincroniaCallix()
            resultado = sinc.verificar_status_clientes([
                {"cliente": "cli_ativo_v1", "status": "active"},
                {"cliente": "cli_inativo_v1", "status": "inactive"},
                {"cliente": "cli_ativo_v4", "status": 3},
                {"cliente": "cli_inativo_v4", "status": 4},
            ])

        assert resultado == [
            {"cliente": "cli_ativo_v1", "ativo": True},
            {"cliente": "cli_inativo_v1", "ativo": False},
            {"cliente": "cli_ativo_v4", "ativo": True},
            {"cliente": "cli_inativo_v4", "ativo": False},
        ]

    def test_get_clientes_servidor_callix_usa_subdomain_e_separar_clientes(self):
        payload_sub_accounts = {
            "data": [
                {
                    "attributes": {
                        "name": "Contech - Nome Comercial",
                        "subdomain": "subrealcontech",
                        "status": "active",
                    }
                },
                {
                    "attributes": {
                        "name": "Contech - Inativo",
                        "subdomain": "inativocontech",
                        "status": "inactive",
                    }
                },
            ]
        }

        clientes = get_clientes_servidor_callix(payload_sub_accounts)
        assert clientes == [
            {"cliente": "subrealcontech", "status": "active"},
            {"cliente": "inativocontech", "status": "inactive"},
        ]

        ativos, inativos = separar_clientes(clientes)
        assert ativos == ["subrealcontech"]
        assert inativos == ["inativocontech"]
