from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from src.rivex.utils.beautiful_soup_utils.beautiful_soup_utils import (
    extrair_filas_html,
    parsear_html as _parsear_html_bs4,
)


class LimpezaVonix:
    def parsear_html(self, conteudo: Any) -> BeautifulSoup:
        """1 - Parseia a resposta ou string para BeautifulSoup."""
        return _parsear_html_bs4(conteudo)

    def listar_filas(self, conteudo: Any) -> list[dict[str, str]]:
        """2 - Retorna a lista completa de filas extraídas do HTML."""
        soup = conteudo if isinstance(conteudo, BeautifulSoup) else self.parsear_html(conteudo)
        return extrair_filas_html(soup)

    def filtrar_filas_disponiveis(self, conteudo: Any) -> list[str]:
        """3 - Retorna apenas os IDs das filas disponíveis (sem manuais e sem ZzDisponivel/ZzInativado)."""
        filas = self.listar_filas(conteudo)
        disponiveis: list[str] = []

        for fila in filas:
            queue_id = fila["id"].strip()
            nome_lower = fila["nome"].strip().lower()
            id_lower = queue_id.lower()

            if nome_lower.startswith("zz") or id_lower.startswith("zz"):
                continue
            if "manual" in nome_lower or "manual" in id_lower:
                continue

            disponiveis.append(queue_id)

        return disponiveis
