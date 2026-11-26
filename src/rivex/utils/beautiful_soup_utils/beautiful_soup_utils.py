from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup


def parsear_html(conteudo: Any) -> BeautifulSoup:
    """Converte uma resposta HTTP ou string HTML em um objeto BeautifulSoup."""
    texto = conteudo.text if hasattr(conteudo, "text") else conteudo
    if not isinstance(texto, str):
        texto = ""
    return BeautifulSoup(texto, "html.parser")


def extrair_filas_html(soup: BeautifulSoup) -> list[dict[str, str]]:
    """Extrai todas as filas (id e nome) presentes no HTML de /admin/queues."""
    filas: list[dict[str, str]] = []
    menu = soup.find("ul", id="queues_menu")

    if menu is not None:
        for inp in menu.find_all("input", attrs={"name": "queue_id[]"}):
            queue_id = str(inp.get("value") or "").strip()
            nome = inp.parent.get_text(" ", strip=True) if inp.parent else ""
            if queue_id:
                filas.append({"id": queue_id, "nome": nome})
        return filas

    for row in soup.find_all("tr", id=lambda x: x and x.startswith("queue_")):
        queue_id = str(row["id"]).replace("queue_", "", 1).strip()
        primeira_celula = row.find("td")
        nome = primeira_celula.get_text(" ", strip=True) if primeira_celula else ""
        if queue_id:
            filas.append({"id": queue_id, "nome": nome})

    return filas
