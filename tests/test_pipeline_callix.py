from unittest.mock import MagicMock, patch
import pytest

from src.rivex.pipeline.pipeline_discador.pipeline_callix import PipelineCallix
from src.rivex.database.database_callix.database_callix_clientes import DatabaseClientes


def _make_pipeline():
    """Cria uma instância de PipelineCallix com dependências externas (DB/HTTP/env) mockadas."""
    with (
        patch("src.rivex.pipeline.pipeline_discador.pipeline_callix.load_dotenv"),
        patch("src.rivex.pipeline.pipeline_discador.pipeline_callix.DatabaseCallix") as mock_db_callix,
        patch("src.rivex.pipeline.pipeline_discador.pipeline_callix.DatabaseClientes") as mock_db_clientes,
    ):
        pipeline = PipelineCallix()
        return pipeline, {
            "db_callix": mock_db_callix.return_value,
            "db_clientes": mock_db_clientes.return_value,
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

        assert dict_limpeza is not None
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

        dict_limpeza, _ = pipeline.limpar_dados(dados_api, dados_req)

        assert dict_limpeza is not None
        assert dict_limpeza["Campanha"] == []

    def test_limpar_dados_resumo_vazio(self):
        pipeline, _ = _make_pipeline()
        dados_api = _sample_dados_brutos_api(resumo_data=[])
        dados_req = _sample_dados_brutos_req()

        dict_limpeza, _ = pipeline.limpar_dados(dados_api, dados_req)

        assert dict_limpeza is not None
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
    def test_executar_fluxo_completo_e_fechamento_conexoes(self):
        pipeline, mocks = _make_pipeline()
        mocks["db_clientes"].consultar_view.return_value = [
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
        mocks["db_clientes"].fechar.assert_called_once()

    def test_executar_ignora_cliente_com_erro_e_persiste_validos(self):
        pipeline, mocks = _make_pipeline()
        mocks["db_clientes"].consultar_view.return_value = [
            {"cliente": "gabrielcontech", "token": "tok-403"},
            {"cliente": "pentagonocontech", "token": "tok-ok"},
        ]

        def _req_side_effect(cliente, token):
            if cliente == "gabrielcontech":
                raise ValueError("Server SDK não retornou userSessionToken (status=403)")
            return _sample_dados_brutos_req()

        with (
            patch("src.rivex.pipeline.pipeline_discador.pipeline_callix.CallixAPICollector") as mock_api_cls,
            patch("src.rivex.pipeline.pipeline_discador.pipeline_callix.CAllixRequisition") as mock_req_cls,
        ):
            mock_api_cls.return_value.api_callix.return_value = _sample_dados_brutos_api()
            mock_req_cls.return_value.requisicao_callix.side_effect = _req_side_effect

            pipeline.executar()

        mocks["db_callix"].db_callix.assert_called_once()
        mocks["db_callix"].fechar.assert_called_once()
        mocks["db_clientes"].fechar.assert_called_once()

    def test_executar_sem_clientes_ativos_levanta_erro_e_fecha_banco(self):
        pipeline, mocks = _make_pipeline()
        mocks["db_clientes"].consultar_view.return_value = []

        with pytest.raises(RuntimeError, match="Nenhum cliente ativo"):
            pipeline.executar()

        mocks["db_callix"].fechar.assert_called_once()
        mocks["db_clientes"].fechar.assert_called_once()

    def test_coletar_clientes_paralelo_loga_aviso_sem_token(self, caplog):
        pipeline, _ = _make_pipeline()
        clientes = [{"cliente": "sem_token", "token": None}]

        with caplog.at_level("WARNING"):
            resultados = pipeline.coletar_clientes_paralelo(clientes)

        assert resultados == []
        assert "sem_token" in caplog.text


class TestDatabaseClientes:
    def test_consultar_view_mapeia_colunas_corretas(self):
        with (
            patch("src.rivex.database.database_callix.database_callix_clientes.ConexaoDatabaseRivex") as mock_conn_cls,
            patch("src.rivex.database.database_callix.database_callix_clientes.DatabaseTelefonia"),
        ):
            mock_conn = mock_conn_cls.return_value
            mock_conn.cursor.fetchall.return_value = [
                ("afsilvacontech", "tok-123"),
            ]

            db_clientes = DatabaseClientes()
            resultado = db_clientes.consultar_view()

        assert resultado == [{"cliente": "afsilvacontech", "token": "tok-123"}]
