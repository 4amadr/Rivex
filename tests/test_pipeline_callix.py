from contextlib import contextmanager
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from src.rivex.database.database_callix.database_callix_clientes import DatabaseClientes
from src.rivex.domain.registros import ClienteRegistro, OperadorRegistro
from src.rivex.pipeline.pipeline_discador.pipeline_callix import PipelineCallix


def _make_pipeline():
    """Cria uma instância de PipelineCallix com dependências externas mockadas."""
    pipeline = PipelineCallix()
    mock_db_callix = MagicMock()
    mock_db_clientes = MagicMock()
    return pipeline, {
        "db_callix": mock_db_callix,
        "db_clientes": mock_db_clientes,
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
    def test_limpar_dados_extrai_ids_campanha_e_valor_cliente(self):
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
        assert metricas_req["operadores_contratados"] == 10
        assert metricas_req["valor_cliente"] == Decimal("1500.00")
        assert metricas_req["rota_cliente"] == "1036#01 - Pentagono (Tech: 103601)"

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
    def test_empacotar_dados_sucesso_com_pydantic(self):
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
            "operadores_contratados": 5,
            "valor_cliente": Decimal("750.00"),
            "rota_cliente": "1036#01 - Pentagono (Tech: 103601)",
        }

        cliente_reg, lista_agentes = pipeline.empacotar_dados(
            dict_limpeza, metricas_req, "pentagonocontech"
        )

        assert isinstance(cliente_reg, ClienteRegistro)
        assert cliente_reg.cliente == "pentagono"
        assert cliente_reg.tech == 103601
        assert cliente_reg.operadores_contratados == 5
        assert cliente_reg.lucro_empresa == Decimal("750.00")
        assert lista_agentes is not None
        assert len(lista_agentes) == 1
        assert isinstance(lista_agentes[0], OperadorRegistro)
        assert lista_agentes[0].nome_operador == "Maria"
        assert lista_agentes[0].id == cliente_reg.id


class TestPipelineCallixExecutar:
    def test_executar_fluxo_completo_e_fechamento_conexoes(self):
        pipeline, mocks = _make_pipeline()
        mocks["db_clientes"].consultar_view.return_value = [
            {"cliente": "pentagono", "token": "tok-1"},
            {"cliente": "sem_token", "token": None},
        ]

        @contextmanager
        def _fake_conn(_settings=None):
            yield MagicMock()

        with (
            patch("src.rivex.pipeline.pipeline_discador.pipeline_callix.conexao_rivex", _fake_conn),
            patch("src.rivex.pipeline.pipeline_discador.pipeline_callix.DatabaseClientes", return_value=mocks["db_clientes"]),
            patch("src.rivex.pipeline.pipeline_discador.pipeline_callix.DatabaseCallix", return_value=mocks["db_callix"]),
            patch("src.rivex.pipeline.pipeline_discador.pipeline_callix.CallixAPICollector") as mock_api_cls,
            patch("src.rivex.pipeline.pipeline_discador.pipeline_callix.CAllixRequisition") as mock_req_cls,
        ):
            mock_api_cls.return_value.api_callix.return_value = _sample_dados_brutos_api()
            mock_req_cls.return_value.requisicao_callix.return_value = _sample_dados_brutos_req()

            resumo = pipeline.executar()

        mocks["db_callix"].db_callix.assert_called_once()
        assert resumo.total == 2
        assert resumo.persistidos == 1
        assert len(resumo.falhas) == 1

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

        @contextmanager
        def _fake_conn(_settings=None):
            yield MagicMock()

        with (
            patch("src.rivex.pipeline.pipeline_discador.pipeline_callix.conexao_rivex", _fake_conn),
            patch("src.rivex.pipeline.pipeline_discador.pipeline_callix.DatabaseClientes", return_value=mocks["db_clientes"]),
            patch("src.rivex.pipeline.pipeline_discador.pipeline_callix.DatabaseCallix", return_value=mocks["db_callix"]),
            patch("src.rivex.pipeline.pipeline_discador.pipeline_callix.CallixAPICollector") as mock_api_cls,
            patch("src.rivex.pipeline.pipeline_discador.pipeline_callix.CAllixRequisition") as mock_req_cls,
        ):
            mock_api_cls.return_value.api_callix.return_value = _sample_dados_brutos_api()
            mock_req_cls.return_value.requisicao_callix.side_effect = _req_side_effect

            resumo = pipeline.executar()

        mocks["db_callix"].db_callix.assert_called_once()
        assert resumo.persistidos == 1
        assert len(resumo.falhas) == 1

    def test_executar_sem_clientes_ativos_levanta_erro(self):
        pipeline, mocks = _make_pipeline()
        mocks["db_clientes"].consultar_view.return_value = []

        @contextmanager
        def _fake_conn(_settings=None):
            yield MagicMock()

        with (
            patch("src.rivex.pipeline.pipeline_discador.pipeline_callix.conexao_rivex", _fake_conn),
            patch("src.rivex.pipeline.pipeline_discador.pipeline_callix.DatabaseClientes", return_value=mocks["db_clientes"]),
            pytest.raises(RuntimeError, match="Nenhum cliente ativo"),
        ):
            pipeline.executar()

    def test_coletar_clientes_paralelo_loga_aviso_sem_token(self):
        pipeline, _ = _make_pipeline()
        clientes = [{"cliente": "sem_token", "token": None}]

        with patch.object(pipeline.log, "aviso") as mock_aviso:
            resultados, falhas = pipeline.coletar_clientes_paralelo(clientes)

        assert resultados == []
        assert falhas == ["sem_token: sem token"]
        mock_aviso.assert_called_once()
        assert mock_aviso.call_args.kwargs["cliente"] == "sem_token"


class TestDatabaseClientes:
    def test_consultar_view_mapeia_colunas_corretas(self):
        with patch(
            "src.rivex.database.database_callix.database_callix_clientes.ConexaoDatabaseRivex"
        ) as mock_conn_cls:
            mock_conn = mock_conn_cls.return_value
            mock_conn.cursor.fetchall.return_value = [
                ("afsilvacontech", "tok-123"),
            ]

            db_clientes = DatabaseClientes()
            resultado = db_clientes.consultar_view()

        assert resultado == [{"cliente": "afsilvacontech", "token": "tok-123"}]
