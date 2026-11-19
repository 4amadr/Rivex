from __future__ import annotations

import re
import unicodedata
from datetime import date
from html import unescape
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup

from src.rivex.domain.registros import ClienteRegistro, OperadorRegistro


def gerar_html(texto: str) -> BeautifulSoup:
    return BeautifulSoup(texto, "html.parser")


def gerar_lista_clientes(html_agentes: BeautifulSoup):
    return html_agentes.find_all("tr", class_="linha1")


def get_cliente(cliente_html) -> str:
    return cliente_html.find("td", attrs={"nowrap": ""}).get_text()


def get_tech_cliente(cliente: str) -> int:
    match = re.search(r"(\d{4})#(\d{2})", cliente)
    if not match:
        return 0
    return int(f"{match.group(1)}{match.group(2)}")


def get_identificador(cliente_html) -> str:
    href = cliente_html.find("a")["href"]
    return parse_qs(urlparse(href).query)["obj_fila_id"][0]


def select_agressividade(select) -> str:
    return select.find("option", selected=True).get_text()


def get_agressividade(agressividade_html: str) -> float:
    soup = gerar_html(agressividade_html)
    select = soup.find("select", id="obj_fila_valor_overdial")
    if select is None:
        return 0.0
    valor = select_agressividade(select).strip().replace(",", ".")
    return float(valor) if valor else 0.0


def get_chamadas_totais_cliente(chamadas_json: dict) -> int:
    return int(chamadas_json.get("data", {}).get("resultado", {}).get("total", {}).get("qtd", 0) or 0)


def get_chamadas_completas_cliente(chamadas_json: dict) -> int:
    return int(chamadas_json.get("data", {}).get("resultado", {}).get("ATENDIDO", {}).get("qtd", 0) or 0)


def get_chamadas_recusadas_cliente(chamadas_json: dict) -> int:
    resultado = chamadas_json.get("data", {}).get("resultado", {})
    ocupado = int(resultado.get("OCUPADO", {}).get("qtd", 0) or 0)
    sem_resposta = int(resultado.get("SEM_RESPOSTA", {}).get("qtd", 0) or 0)
    desconhecido = int(resultado.get("DESCONHECIDO", {}).get("qtd", 0) or 0)
    return ocupado + sem_resposta + desconhecido


def get_chamadas_abandonadas_cliente(chamadas_json: dict) -> int:
    return int(chamadas_json.get("data", {}).get("resultado", {}).get("CONGESTIONADO", {}).get("qtd", 0) or 0)


def limpar_nome_cliente(time_nome: str) -> str:
    return unescape(time_nome).split(" - ", 1)[0].strip()


def normalizar_nome_comparacao(nome: str) -> str:
    texto = unicodedata.normalize("NFD", unescape(nome or ""))
    sem_acento = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", sem_acento).strip().lower()


def get_operadores(operadores_html: str) -> list[str]:
    soup = gerar_html(operadores_html)
    container = soup.find(id="gridUsuarios") or soup.find(id="intGridUsuarios")
    if not container:
        return []

    operadores = []
    for tabela in container.find_all("table", class_="grid"):
        for linha in tabela.find_all("tr", class_=["linha1", "linha2"]):
            colunas = linha.find_all("td")
            if len(colunas) >= 2 and colunas[1].get_text(strip=True).lower() == "agente":
                operadores.append(colunas[0].get_text(strip=True))
    return list(dict.fromkeys(operadores))


def empacotar_dados_clientes(
    chamadas_json: dict,
    cliente: str,
    data: date,
    agressividade: str,
    operadores: str,
) -> ClienteRegistro:
    operadores_lista = get_operadores(operadores)
    return ClienteRegistro(
        discador="IPBox",
        tech=get_tech_cliente(cliente),
        cliente=cliente,
        data=data,
        chamadas=get_chamadas_totais_cliente(chamadas_json),
        aceitas=get_chamadas_completas_cliente(chamadas_json),
        recusadas=get_chamadas_recusadas_cliente(chamadas_json),
        abandonadas=get_chamadas_abandonadas_cliente(chamadas_json),
        agressividade=get_agressividade(agressividade),
        operadores_contratados=len(operadores_lista),
    )


def chamadas_agente(agente_atendimentos: str | int) -> int:
    if agente_atendimentos == "-" or agente_atendimentos is None:
        return 0
    return int(agente_atendimentos)


def empacotar_dados_agentes(
    agente: dict,
    cliente_reg: ClienteRegistro,
    data: date,
) -> OperadorRegistro:
    return OperadorRegistro(
        id=cliente_reg.id,
        discador="IPBox",
        tech=cliente_reg.tech,
        cliente=cliente_reg.cliente,
        data=data,
        nome_operador=agente["agente"],
        chamada_aceita=chamadas_agente(agente.get("atendimentos")),
    )
