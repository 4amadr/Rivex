from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

def gerar_html(texto):
    return BeautifulSoup(texto, "html.parser")

def gerar_lista_clientes(html_agentes):
    return html_agentes.find_all('tr', class_='linha1')

def get_cliente(cliente_html):
    return cliente_html.find('td', attrs={"nowrap": ""}).get_text()

def get_identificador(cliente_html):
    href = cliente_html.find("a")["href"]
    return parse_qs(urlparse(href).query)["obj_fila_id"][0]

def get_agressividade(agressividade_html):
    agressividade_html = gerar_html(agressividade_html)
    select = agressividade_html.find('select', id='obj_fila_valor_overdial')
    return select.find("option", selected=True).get_text()

def get_chamadas_totais(chamadas_json):
    dados = chamadas_json['data']

