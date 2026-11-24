from __future__ import annotations

import re
from datetime import date
from typing import Mapping, Optional

from bs4 import BeautifulSoup

from src.rivex.domain.exceptions import ErroTechNaoEncontrada
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


def extrair_tech_queue_edit(config_html: str) -> Optional[int]:
    """Extrai a Tech diretamente de ``<select id="queue_lcr_profile_id">`` em ``/admin/queue_edit/{cliente}``."""
    soup = get_html(config_html)
    select = soup.find("select", id="queue_lcr_profile_id")
    if select is None:
        return None

    option_selected = select.find("option", selected=True)
    if option_selected is None:
        return None

    texto = option_selected.get_text(strip=True)
    match = re.match(r"^(\d{4})#(\d{2})(?:\b|\s|[-–])", texto)
    if not match:
        return None

    return int(f"{match.group(1)}{match.group(2)}")


def resolver_tech_vonix(
    cliente: str,
    config_html: str,
    mapa_techs: Mapping[str, int],
) -> tuple[int, bool]:
    """Resolve a Tech imutável da equipe Vonix sem fallback para 0 ou ID randômico.

    Prioridade:
    1. Vínculo persistido em ``clientes.clientes_vonix`` (imutável).
    2. Perfil LCR direto em ``/admin/queue_edit/{cliente}`` (sinaliza registro automático).
    3. Caso ausente em ambos, levanta ``ErroTechNaoEncontrada``.
    """
    tech_salva = mapa_techs.get(cliente)
    if tech_salva is not None and int(tech_salva) > 0:
        return int(tech_salva), False

    tech_extraida = extrair_tech_queue_edit(config_html)
    if tech_extraida is not None and tech_extraida > 0:
        return tech_extraida, True

    raise ErroTechNaoEncontrada(
        f"Tech não encontrada para a equipe Vonix '{cliente}' em "
        "clientes.clientes_vonix nem no perfil LCR de /admin/queue_edit."
    )
