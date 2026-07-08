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