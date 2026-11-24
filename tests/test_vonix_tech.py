from __future__ import annotations

from contextlib import contextmanager
from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.rivex.data_processing.Vonix.cleaning_vonix import (
    extrair_tech_queue_edit,
    resolver_tech_vonix,
)
from src.rivex.database.database_vonix.database_vonix_clientes import DatabaseClientesVonix
from src.rivex.domain.exceptions import ErroTechNaoEncontrada
from src.rivex.domain.registros import ClienteRegistro, OperadorRegistro
from src.rivex.pipeline.pipeline_discador.pipeline_vonix import PipelineVonix


def _html_queue_edit(lcr_text: str | None, dial_speed: str = "3.5") -> str:
    option = (
        f'<option value="62" selected="selected">{lcr_text}</option>'
        if lcr_text is not None
        else '<option value="1">Padrao</option>'
    )
    return f"""
    <form>
      <select id="queue_lcr_profile_id" name="queue[lcr_profile_id]">
        <option value="18">Venditore</option>
        {option}
      </select>
      <input id="dialer_dial_speed" value="{dial_speed}" />
    </form>
    """


def test_extrair_tech_queue_edit_com_e_sem_hifen():
    assert extrair_tech_queue_edit(_html_queue_edit("1404#01 - TC Representação")) == 140401
    assert extrair_tech_queue_edit(_html_queue_edit("2333#01 Multbank X")) == 233301
    assert extrair_tech_queue_edit(_html_queue_edit("2302#01-GestãoGlobal Tarifado")) == 230201
    assert extrair_tech_queue_edit(_html_queue_edit("Venditore")) is None
    assert extrair_tech_queue_edit(_html_queue_edit("Padrao")) is None
    assert extrair_tech_queue_edit(_html_queue_edit(None)) is None


def test_resolver_tech_vonix_prioriza_tabela_imutavel_sobre_lcr():
    html_outra_tech = _html_queue_edit("9999#99 - Outro Perfil")
    tech, nova = resolver_tech_vonix(
        "tcrepresentacao",
        html_outra_tech,
        {"tcrepresentacao": 140401},
    )
    assert tech == 140401
    assert nova is False


def test_resolver_tech_vonix_sem_tech_levanta_erro_explicito():
    with pytest.raises(ErroTechNaoEncontrada):
        resolver_tech_vonix("wine", _html_queue_edit("Agitel - SMP"), {})


def test_registros_vonix_rejeitam_tech_zero():
    with pytest.raises(ValueError, match="Vonix"):
        ClienteRegistro(
            discador="Vonix",
            tech=0,
            cliente="serrana",
            data=date(2026, 11, 24),
            chamadas=10,
            aceitas=5,
            recusadas=3,
            abandonadas=2,
            agressividade=2.0,
        )

    with pytest.raises(ValueError, match="Vonix"):
        OperadorRegistro(
            id=12345,
            discador="Vonix",
            tech=0,
            cliente="serrana",
            data=date(2026, 11, 24),
            nome_operador="Maria",
            chamada_aceita=3,
        )


def test_database_clientes_vonix_cria_estrutura_carrega_e_registra_imutavel():
    cursor = MagicMock()
    conexao = MagicMock()
    conn_compartilhada = SimpleNamespace(cursor=cursor, conexao=conexao)

    db = DatabaseClientesVonix(conexao_compartilhada=conn_compartilhada)

    sqls_init = [call.args[0] for call in cursor.execute.call_args_list]
    assert any("CREATE SCHEMA IF NOT EXISTS clientes" in s for s in sqls_init)
    assert any("CREATE TABLE IF NOT EXISTS clientes.clientes_vonix" in s for s in sqls_init)
    assert any("CHECK (tech > 0)" in s for s in sqls_init)
    assert any("vw_clientes_vonix_ativos" in s for s in sqls_init)

    cursor.fetchall.return_value = [("realpromotora", 101001), ("tcrepresentacao", 140401)]
    mapa = db.carregar_mapa_techs()
    assert mapa == {"realpromotora": 101001, "tcrepresentacao": 140401}

    cursor.fetchone.return_value = (140401,)
    tech_salva = db.registrar_tech("tcrepresentacao", 999999)
    assert tech_salva == 140401
    assert any("ON CONFLICT (equipe) DO NOTHING" in str(c.args[0]) for c in cursor.execute.call_args_list)


def test_pipeline_vonix_registra_nova_tech_e_rejeita_cliente_sem_tech():
    pipeline = PipelineVonix(usar_db=True)
    pipeline.tempo_int = 0
    pipeline.tempo_backoff_erro = 0

    html_chamadas = '<div id="maincontent"><div class="box-title">Chamadas (10)</div></div>'
    html_agentes = '<table class="grid"></table>'

    def fake_get_dados_sujos(cliente: str, token: str) -> dict:
        if cliente == "tcrepresentacao":
            config_html = _html_queue_edit("1404#01 - TC Representação")
        elif cliente == "realpromotora":
            config_html = _html_queue_edit("Venditore")
        else:
            config_html = _html_queue_edit("Agitel - SMP")
        return {
            "Totais": SimpleNamespace(text=html_chamadas),
            "Aceitas": SimpleNamespace(text=html_chamadas),
            "Abandonadas": SimpleNamespace(text=html_chamadas),
            "Recusadas": SimpleNamespace(text=html_chamadas),
            "Agentes": SimpleNamespace(text=html_agentes),
            "config": SimpleNamespace(text=config_html),
        }

    fake_conn = SimpleNamespace(cursor=MagicMock(), conexao=MagicMock())

    @contextmanager
    def fake_conexao_rivex(_settings=None):
        yield fake_conn

    mock_db_clientes = MagicMock()
    mock_db_clientes.carregar_mapa_techs.return_value = {"realpromotora": 101001}
    mock_db_vonix = MagicMock()

    with (
        patch.object(
            pipeline,
            "inicial_config",
            return_value=(["realpromotora", "tcrepresentacao", "wine"], "tok"),
        ),
        patch.object(pipeline, "get_dados_sujos", side_effect=fake_get_dados_sujos),
        patch(
            "src.rivex.pipeline.pipeline_discador.pipeline_vonix.conexao_rivex",
            side_effect=fake_conexao_rivex,
        ),
        patch(
            "src.rivex.pipeline.pipeline_discador.pipeline_vonix.DatabaseClientesVonix",
            return_value=mock_db_clientes,
        ),
        patch(
            "src.rivex.pipeline.pipeline_discador.pipeline_vonix.DatabaseVonix",
            return_value=mock_db_vonix,
        ),
    ):
        resumo = pipeline.execucao_vonix(data=date(2026, 11, 24))

    assert resumo.total == 3
    assert resumo.persistidos == 2
    assert len(resumo.falhas) == 1
    assert "wine" in resumo.falhas[0]

    # Auto-descoberta persistiu tcrepresentacao em clientes.clientes_vonix
    mock_db_clientes.registrar_tech.assert_called_once_with("tcrepresentacao", 140401)
    assert mock_db_vonix.db_vonix.call_count == 2
    techs_persistidas = [c.args[0].tech for c in mock_db_vonix.db_vonix.call_args_list]
    assert techs_persistidas == [101001, 140401]
