from __future__ import annotations

import re
import unicodedata
from datetime import date

from bs4 import BeautifulSoup

from src.rivex.domain.registros import ClienteRegistro, OperadorRegistro


def get_html(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def remover_javascript(pagina: BeautifulSoup) -> BeautifulSoup:
    for script in pagina(["script", "style"]):
        script.decompose()
    return pagina


def get_lista_clientes(clientes_html: BeautifulSoup) -> list[str]:
    return [
        item["id"]
        for item in clientes_html.find_all("li", id=lambda x: x and x.startswith("container_"))
    ]


def limpar_nome_lista(lista_clientes: list[str]) -> list[str]:
    return [cliente.replace("container_", "") for cliente in lista_clientes]


def filtrar_clientes_vonix(lista_clientes: list[str]) -> list[str]:
    """Filtro único de filas ativas/automáticas do Vonix."""
    return [
        cliente
        for cliente in lista_clientes
        if "itelink" not in cliente.lower()
        and not cliente.lower().endswith("manual")
        and not cliente.lower().startswith("zz")
    ]


def gerar_lista_de_clientes(html: str) -> list[str]:
    html_clientes = get_html(html)
    html_puro = remover_javascript(html_clientes)
    lista_clientes = get_lista_clientes(html_puro)
    return filtrar_clientes_vonix(limpar_nome_lista(lista_clientes))


def entrar_na_div(html: BeautifulSoup):
    return html.find("div", id="maincontent")


def remover_texto_chamadas(chamadas: str) -> int:
    inicio_dados = chamadas.find("(") + 1
    fim_dados = chamadas.find(")")
    if inicio_dados <= 0 or fim_dados < inicio_dados:
        return 0
    valor = re.sub(r"\D", "", chamadas[inicio_dados:fim_dados])
    return int(valor) if valor else 0


def chamadas_em_texto(div):
    return div.find("div", class_="box-title") if div else None


def limpar_chamadas(html: str) -> int:
    chamadas_html = get_html(html)
    div_dados = entrar_na_div(chamadas_html)
    chamadas_com_texto = chamadas_em_texto(div_dados)
    if chamadas_com_texto is None:
        return 0
    return remover_texto_chamadas(chamadas_com_texto.text)


def filtra_agressividade(agressividade_html: BeautifulSoup) -> float:
    campo = agressividade_html.find("input", id="dialer_dial_speed")
    if campo is None or not campo.get("value"):
        return 0.0
    return float(str(campo["value"]).strip().replace(",", "."))


def get_agressividade(html: str) -> float:
    agressividade_html = get_html(html)
    return filtra_agressividade(agressividade_html)


def encontrar_tabela_agentes(html: str):
    tabela_html = get_html(html)
    return tabela_html.find("table", class_="grid")


def gerar_lista_infos_agentes(tabela):
    if tabela is None:
        return None
    return tabela.find_all("tr", class_=["item", "shaded"])


def gerar_dados_agentes(
    infos_agentes,
    cliente_reg: ClienteRegistro,
    data: date,
) -> list[OperadorRegistro]:
    dados_agentes: list[OperadorRegistro] = []
    if not infos_agentes:
        dados_agentes.append(
            OperadorRegistro(
                id=cliente_reg.id,
                discador="Vonix",
                tech=cliente_reg.tech,
                cliente=cliente_reg.cliente,
                data=data,
                nome_operador="Sem agente",
                chamada_aceita=0,
            )
        )
        return dados_agentes

    for agente in infos_agentes:
        td_nome = agente.find("td", class_="item")
        td_chamadas = agente.find("td", id=lambda x: x and x.startswith("call_counter_AUTO"))

        nome = td_nome.get_text(strip=True) if td_nome else "Desconhecido"
        if td_chamadas:
            chamadas_txt = (
                td_chamadas.a.get_text(strip=True)
                if td_chamadas.a
                else td_chamadas.get_text(strip=True)
            )
        else:
            chamadas_txt = "0"

        chamadas_int = int(re.sub(r"\D", "", chamadas_txt) or "0")

        dados_agentes.append(
            OperadorRegistro(
                id=cliente_reg.id,
                discador="Vonix",
                tech=cliente_reg.tech,
                cliente=cliente_reg.cliente,
                data=data,
                nome_operador=nome,
                chamada_aceita=chamadas_int,
            )
        )
    return dados_agentes


def dict_agentes(
    html: str,
    cliente_reg: ClienteRegistro,
    data: date,
) -> list[OperadorRegistro]:
    tabela = encontrar_tabela_agentes(html)
    lista_infos = gerar_lista_infos_agentes(tabela)
    return gerar_dados_agentes(lista_infos, cliente_reg, data)


def get_lista_techs(tech_html: str) -> list[dict]:
    tech_convertida = get_html(tech_html)
    select = tech_convertida.find("select", {"id": "lcr_profile"})
    if select is None:
        return []

    clientes = []
    for option in select.find_all("option"):
        value = option.get("value", "")
        text = option.get_text(strip=True)
        match = re.match(r"^(\d{4}#\d{2})\s*[-–]\s*(.+)$", text)
        if match:
            clientes.append(
                {
                    "lcr_profile_id": value,
                    "tech": match.group(1),
                    "nome": match.group(2).strip(),
                }
            )
    return clientes


def tratar_nome_cliente(cliente: str) -> str:
    cliente = (cliente or "").lower()
    cliente = "".join(
        c for c in unicodedata.normalize("NFD", cliente) if unicodedata.category(c) != "Mn"
    )
    cliente = cliente.replace("tarifado", "")
    cliente = cliente.replace("manual", "")
    cliente = cliente.replace(" e ", "")
    cliente = re.sub(r"[^a-z0-9]", "", cliente)
    cliente = re.sub(r"\d+$", "", cliente)
    return cliente


def get_tech_vez(lista_techs: list[dict], cliente: str) -> int:
    """Resolve a Tech por igualdade normalizada ou correspondência unívoca; retorna 0 se ambígua/ausente."""
    cliente_norm = tratar_nome_cliente(cliente)
    if not cliente_norm:
        return 0

    for tech in lista_techs:
        nome_tech = tratar_nome_cliente(tech["nome"])
        if nome_tech and cliente_norm == nome_tech:
            return int(tech["tech"].replace("#", ""))

    candidatos = [
        int(tech["tech"].replace("#", ""))
        for tech in lista_techs
        if (nome_tech := tratar_nome_cliente(tech["nome"]))
        and (cliente_norm in nome_tech or nome_tech in cliente_norm)
    ]
    unicos = list(dict.fromkeys(candidatos))
    if len(unicos) == 1:
        return unicos[0]

    return 0
