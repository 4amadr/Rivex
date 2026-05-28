from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
import re

def parse_id_clientes(clientes):
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
    chamadas_recusadas = chamadas_totais - chamadas_aceitas
    print(chamadas_recusadas)
    
    return chamadas_aceitas['qtd'], chamadas_totais['qtd'], chamadas_recusadas

def limpeza_agentes_ipbox(agentes_json):
    """
    Retorna uma lista de dicionários com o desempenho de cada agente 
    e as chamadas completas de cada agente 
    """
    dados_json = agentes_json['data']
    
    lista_de_dicionarios_agentes = []
    
    for dados in dados_json:
        dict_agentes_ipbox = {
        "Cliente": dados["times"],
        "Chamadas completas": dados["atendimentos"],

        }
        print("Dicionário de agentes: ",dict_agentes_ipbox)
        lista_de_dicionarios_agentes.append(dict_agentes_ipbox)
        
    return lista_de_dicionarios_agentes

def relatorio_completo_agente(id_time_ipbox,
                              fila_ipbox,
                              chamada,
                              chamadas_aceitas,
                              chamadas_recusadas,
                              chamadas_abandonadas,
                              agressividade
                              ):
    dict_agentes = {
        "ID": id_time_ipbox,
        "Equipe": fila_ipbox,
        "Chamadas totais": chamadas,
        "Chamadas aceitas": chamadas_aceitas,
        "Chamadas recusadas": chamadas_recusadas,
        "Chamadas abandonadas": chamadas_abandonadas,
        "Agressividade": agressividade
    }
    return dict_agentes

def limpeza_clientes_ipbox(dict_cliente):
    '''
    função para retornar o id do cliente separado da fila
    Como os ambientes geram 1234#01
    como deve ficar -> id = 1234; fila = 01
    '''
    
    # execução de um loop pois a intenção é desempacotar uma lista
    lista_id_clientes = []
    
    identificador_de_clientes = dict_cliente["ID Cliente"]
    
    for cliente in identificador_de_clientes:    
        dict_cliente_com_id = {
        "ID Cliente": cliente["ID Cliente"][:4],
        "Fila": cliente["ID Cliente"][5:]
    } 
        lista_id_clientes.append(dict_cliente_com_id)
    
    return lista_id_clientes
    