from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv

from src.rivex.data_processing.Vonix.limpeza_vonix import LimpezaVonix
from src.rivex.database.database_raw.raw_data import raw_vonix
from src.rivex.environments.discadores.vonix.fluxo_coleta import GetDadosVonix


class PipelineVonix:
    def __init__(self, url_base: str | None = None) -> None:
        load_dotenv()
        base = url_base or os.getenv("URL_BASE_VONIX6") or ""
        self.get_dados = GetDadosVonix(base)
        self.config_vonix = self.get_dados.config_vonix
        self.limpeza = LimpezaVonix()

    def get_filas_raw(self):
        return self.config_vonix.fluxo_fila()

    def get_filas(self) -> list[str]:
        filas_raw = self.get_filas_raw()
        return self.limpeza.filtrar_filas_disponiveis(filas_raw)

    def coletar(self, equipe: str) -> dict[str, Any]:
        return self.get_dados.get_dados(equipe)

    def carregar_raw(
        self,
        equipe: str,
        dados_raw: dict[str, Any],
        db_raw: raw_vonix | None = None,
    ) -> None:
        queue_edit_raw = dados_raw.get("queue_edit")
        calls_raw = dados_raw.get("calls")
        agents_raw = dados_raw.get("agents")

        if db_raw is not None:
            db_raw.enviar_cliente_raw(
                equipe=equipe,
                queue_edit_raw=queue_edit_raw,
                calls_raw=calls_raw,
            )
            db_raw.enviar_operador_raw(
                equipe=equipe,
                agents_raw=agents_raw,
            )
            return

        with raw_vonix() as db:
            db.enviar_cliente_raw(
                equipe=equipe,
                queue_edit_raw=queue_edit_raw,
                calls_raw=calls_raw,
            )
            db.enviar_operador_raw(
                equipe=equipe,
                agents_raw=agents_raw,
            )

    def carregar(self, dados_silver: dict[str, Any]) -> None:
        from src.rivex.database.database_vonix.database_vonix import DatabaseVonix

        db = DatabaseVonix()
        try:
            db.db_vonix(dados_silver["cliente_registro"], dados_silver["operadores_registro"])
        finally:
            db.fechar_db_vonix()

    def executar(self, persistir_raw: bool = True) -> dict[str, dict[str, Any]]:
        filas_raw = self.get_filas_raw()
        lista_filas = self.limpeza.filtrar_filas_disponiveis(filas_raw)
        resultados: dict[str, dict[str, Any]] = {}

        if persistir_raw:
            with raw_vonix() as db_raw:
                db_raw.enviar_fila_raw(filas_raw)
                for equipe in lista_filas:
                    dados_raw = self.coletar(equipe)
                    self.carregar_raw(equipe=equipe, dados_raw=dados_raw, db_raw=db_raw)
                    resultados[equipe] = dados_raw
            return resultados

        for equipe in lista_filas:
            resultados[equipe] = self.coletar(equipe)
        return resultados
