from __future__ import annotations

from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.rivex.database.database_indicadores.database_desempenho import (
    DatabaseDesempenhoPipeline,
    normalizar_coluna_pipeline,
)
from src.rivex.domain.registros import ResumoExecucao
from src.rivex.utils.infra_utils.execution_timer import (
    CronometroPipelines,
    medir_tempo_execucao,
)


def test_cronometro_mede_multiplas_pipelines_e_soma_total():
    instantes = iter([10.0, 22.35, 22.35, 30.1, 30.1, 35.6])
    cronometro = CronometroPipelines(relogio=lambda: next(instantes))

    with cronometro.medir_pipeline("callix"):
        pass
    with cronometro.medir_pipeline("ipbox"):
        pass
    with cronometro.medir_pipeline("nova_pipeline"):
        pass

    assert cronometro.obter_tempos() == {
        "callix": 12.35,
        "ipbox": 7.75,
        "nova_pipeline": 5.5,
    }
    assert cronometro.tempo_total == 25.6
    assert cronometro.gerar_resumo(date(2026, 11, 23)) == {
        "data": date(2026, 11, 23),
        "tempos": {"callix": 12.35, "ipbox": 7.75, "nova_pipeline": 5.5},
        "total": 25.6,
    }


def test_cronometro_registra_tempo_mesmo_com_excecao():
    instantes = iter([100.0, 104.25])
    cronometro = CronometroPipelines(relogio=lambda: next(instantes))

    with pytest.raises(RuntimeError, match="falha"):
        with cronometro.medir_pipeline("vonix"):
            raise RuntimeError("falha")

    assert cronometro.obter_tempo("vonix") == 4.25
    assert cronometro.tempo_total == 4.25


def test_medir_tempo_execucao_retorna_resultado_e_duracao():
    instantes = iter([5.0, 8.75])
    resultado, duracao = medir_tempo_execucao(
        lambda x, y: x + y, 2, 3, relogio=lambda: next(instantes)
    )
    assert resultado == 5
    assert duracao == 3.75


def test_normalizar_coluna_pipeline():
    assert normalizar_coluna_pipeline("Callix") == "callix"
    assert normalizar_coluna_pipeline("Nova Pipeline-2") == "nova_pipeline_2"
    assert normalizar_coluna_pipeline("3cplus") == "p_3cplus"

    with pytest.raises(ValueError):
        normalizar_coluna_pipeline("   ")
    with pytest.raises(ValueError):
        normalizar_coluna_pipeline("data")
    with pytest.raises(ValueError):
        normalizar_coluna_pipeline("total")


def test_database_desempenho_adiciona_colunas_dinamicas_e_faz_upsert():
    fake_cursor = MagicMock()
    fake_cursor.fetchall.return_value = [("callix",), ("ipbox",), ("nova_pipeline",)]
    fake_conn = MagicMock()
    fake_db = SimpleNamespace(cursor=fake_cursor, conexao=fake_conn)

    db = DatabaseDesempenhoPipeline(conexao_compartilhada=fake_db)
    db.enviar_desempenho(
        data_ref=date(2026, 11, 23),
        tempos_pipelines={"ipbox": 14.5, "nova_pipeline": 6.25},
        total=20.75,
    )

    assert fake_conn.commit.call_count == 2  # garantir_estrutura + upsert
    # A última chamada do cursor deve ser o INSERT ... ON CONFLICT (data) DO UPDATE
    ultima_chamada = fake_cursor.execute.call_args_list[-1]
    query_obj, params = ultima_chamada[0]
    assert params == [date(2026, 11, 23), 14.5, 6.25, 20.75]
    # Verifica se houve ALTER TABLE ADD COLUMN IF NOT EXISTS para cada coluna de pipeline
    assert fake_cursor.execute.call_count >= 9


def test_main_mede_e_envia_desempenho_de_todas_as_pipelines():
    import main

    fake_settings = SimpleNamespace(max_falhas_pipeline=0, db=SimpleNamespace(host="h"))
    with (
        patch("sys.argv", ["main.py", "--pipeline", "all", "--data", "2026-11-22"]),
        patch("main.carregar_settings", return_value=fake_settings),
        patch(
            "main._executar_pipeline",
            side_effect=lambda nome, cls, cfg, dt: ResumoExecucao(
                pipeline=nome, total=1, persistidos=1, falhas=[]
            ),
        ),
        patch("main.enviar_desempenho_pipeline") as mock_enviar,
    ):
        exit_code = main.main()

    assert exit_code == 0
    mock_enviar.assert_called_once()
    kwargs = mock_enviar.call_args.kwargs
    assert kwargs["data_ref"] == date(2026, 11, 22)
    assert set(kwargs["tempos_pipelines"].keys()) == {"callix", "ipbox", "vonix"}
    assert kwargs["total"] == round(sum(kwargs["tempos_pipelines"].values()), 2)
    assert kwargs["db_settings"] is fake_settings.db
