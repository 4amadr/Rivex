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
    return tech_texto.find('option', selected='selected').get_text(strip=True)

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
    return tabela.find_all('tr', class_=["item", "shaded"])

def gerar_dados_agentes(infos_agentes):
    
    dados_agentes = []
    for agente in infos_agentes:
        dict_agentes = {
            "agente": agente.find('td', class_="item").get_text(strip=True),
            "chamadas": agente.find('td', id=lambda x: x and x.startswith("call_counter_AUTO")
                                    ).a.get_text(strip=True)
        }
        
        dados_agentes.append(dict_agentes)
    return dados_agentes
        
    

def dict_agentes(html):
    tabela = encontrar_tabela_agentes(html)
    lista_infos = gerar_lista_infos_agentes(tabela)
    return gerar_dados_agentes(lista_infos)
    


