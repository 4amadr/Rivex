from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
import re

def get_clientes(clientes):
    clientes_html = BeautifulSoup(clientes.text, 'html.parser')

    lista_clientes = []
    clientes = clientes_html.find_all('td', nowrap="")
    for cliente in clientes:
        lista_clientes.append(cliente.get_text())
    return lista_clientes

def limpeza_lista_clientes(lista_clientes):
    termos_sujos = [' Sim', ' Ativo ', ' Descricao'] # termos que foram parar na lista de clientes padrão e vão ser removidos
    lista_nova = [cliente for cliente in lista_clientes if cliente not in termos_sujos]
    return lista_nova

def extrair_ids_filas(html: str) -> list[int]:
    """
    Extrai todos os IDs únicos de filas presentes nos hrefs das tags <a>.
    """

    lista_ids = []

    soup = BeautifulSoup(html.text, "html.parser")

    td_tags = soup.find_all("td", class_="botao")

    for td in td_tags:

        link = td.find("a", href=True)

        if not link:
            continue

        href = link["href"]

        query = urlparse(href).query
        params = parse_qs(query)

        fila_id = params.get("obj_fila_id", [None])[0]

        if fila_id:
            lista_ids.append(int(fila_id))

    return lista_ids

def dicionario_clientes(lista_clientes, lista_ids):
    lista_info_cliente = []

    for cliente, identificador in zip(lista_clientes, lista_ids):
        dict_cliente = {
            "Cliente": cliente,
            "ID Cliente": identificador,
        }
        lista_info_cliente.append(dict_cliente)
    return lista_info_cliente


def filtragem_lista(clientes):
    lista_suja_clientes = get_clientes(clientes)
    lista_pronta = limpeza_lista_clientes(lista_suja_clientes)
    lista_de_ids = extrair_ids_filas(clientes)
    lista_final = dicionario_clientes(lista_pronta, lista_de_ids)
    return lista_final

def limpeza_agressividade(agressividade_html):
    html = BeautifulSoup(agressividade_html, "html.parser")

    select_tag = html.find('select', attrs={'id': 'obj_fila_valor_overdial'})
    opcao = select_tag.find('option', selected=True)
    valor = opcao['value']

    return valor

def limpeza_chamadas_ipbox(chamadas_json):
    resultados_chamadas = chamadas_json['data']['resultado']
    chamadas_aceitas = resultados_chamadas['ATENDIDO']
    chamadas_totais = resultados_chamadas['total']
    
    return chamadas_aceitas['qtd'], chamadas_totais['qtd']

def limpeza_agentes_ipbox(agentes_json):
    agentes_json