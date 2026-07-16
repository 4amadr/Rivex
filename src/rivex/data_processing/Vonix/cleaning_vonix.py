from bs4 import BeautifulSoup
import re

def get_html(html):
    return BeautifulSoup(html, "html.parser")

def get_token(html_token):
    token = html_token.find("input", attrs={"name": "authenticity_token"})["value"]
    return token

def remover_javascript(pagina):
    for script in pagina(['script', 'style']):
        script.decompose()
    return pagina

def get_lista_clientes(clientes_html):
    return [item["id"] for item in clientes_html.find_all(
        "li",
        id=lambda x: x and x.startswith("container_")
    )]

def limpar_nome_lista(lista_clientes):
    return [cliente.replace("container_", "") for cliente in lista_clientes]

def gerar_lista_de_clientes(html):
    html_clientes = get_html(html)
    html_puro = remover_javascript(html_clientes)
    lista_clientes = get_lista_clientes(html_puro)
    return limpar_nome_lista(lista_clientes)

def entrar_na_div(html):
    return html.find('div', id='maincontent')

def remover_texto_chamadas(chamadas):
    inicio_dados = chamadas.find("(") + 1
    fim_dados = chamadas.find(")")
    return chamadas[inicio_dados:fim_dados]

def chamadas_em_texto(div):
    return div.find("div", class_="box-title")

def limpar_chamadas(html):
    chamadas_html = get_html(html)
    div_dados = entrar_na_div(chamadas_html)
    chamadas_com_texto = chamadas_em_texto(div_dados)
    return remover_texto_chamadas(chamadas_com_texto.text)

def filtra_agressividade(agressividade_html):
    return agressividade_html.find('input', id='dialer_dial_speed')['value']


def get_agressividade(html):
    agressividade_html = get_html(html)
    return filtra_agressividade(agressividade_html)

def get_techs_texto(tech_html):
    return tech_html.find("select", id="queue_lcr_profile_id")

def get_tech_selecionada(tech_texto):
    tech = tech_texto.find('option', selected='selected').get_text(strip=True)
    return tech

def get_tech_numerico(tech_selecionada):
    return re.sub(r"\D", "", tech_selecionada.split(" - ")[0])


def get_tech(html):
    tech_html = get_html(html)
    techs_texto = get_techs_texto(tech_html)
    tech_selecionada_texto = get_tech_selecionada(techs_texto)
    return get_tech_numerico(tech_selecionada_texto)

def encontrar_tabela_agentes(html):
    tabela_html = get_html(html)
    return tabela_html.find('table', class_="grid")

def gerar_lista_infos_agentes(tabela):
    if tabela is None:
        return None
    return tabela.find_all('tr', class_=["item", "shaded"])

def gerar_dados_agentes(infos_agentes):
    dados_agentes = []
    if not infos_agentes:
        dados_agentes.append({
            "agente": "Sem agente",
            "chamadas": 0,
        })
    else:
        for agente in infos_agentes:
            td_nome = agente.find("td", class_="item")

            td_chamadas = agente.find(
                "td",
                id=lambda x: x and x.startswith("call_counter_AUTO")
            )

            nome = td_nome.get_text(strip=True) if td_nome else "Desconhecido"

            if td_chamadas:
                if td_chamadas.a:
                    chamadas = td_chamadas.a.get_text(strip=True)
                else:
                    chamadas = td_chamadas.get_text(strip=True)
            else:
                chamadas = "0"

            dados_agentes.append({
                "agente": nome,
                "chamadas": chamadas
            })
    return dados_agentes

def dict_agentes(html):
    tabela = encontrar_tabela_agentes(html)
    lista_infos = gerar_lista_infos_agentes(tabela)
    return gerar_dados_agentes(lista_infos)

def find_name(html_cliente):
    elemento = html_cliente.find('input', id='queue_name')
    return elemento['value'] if elemento else None

def get_cliente_nome(html):
    html_cliente = get_html(html)
    cliente = find_name(html_cliente)
    return cliente

def find_html_tech(tech_convertida):
    return [tech.get_text(strip=True) for tech in tech_convertida]

def get_lista_techs(tech_html):
    tech_convertida = get_html(tech_html)
    select = tech_convertida.find("select", {"id": "lcr_profile"})

    clientes = []
    
    for option in select.find_all("option"):
        value = option['value']
        text = option.get_text(strip=True)
        match = re.match(r"^(\d{4}#\d{2})\s*[-–]\s*(.+)$", text)
        if match:
            clientes.append({
                "lcr_profile_id": value,  # ID interno do sistema
                "tech": match.group(1),   # Ex: "1010#01" — IDENTIFICADOR ÚNICO
                "nome": match.group(2).strip()
            })
    return clientes
    


