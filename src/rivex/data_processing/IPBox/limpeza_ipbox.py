from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
import re
from collections import namedtuple
from typing import List, Any, Dict
import logging

logger = logging.getLogger(__name__)
ClienteInfo = namedtuple("ClienteInfo", ["nome_cliente", "id_cliente"])
EstatisticasChamadas = namedtuple("EstatisticasChamadas", ["aceitas", "totais", "recusadas"])
DesempenhoAgente = namedtuple("DesempenhoAgente", ["cliente", "chamadas_completas"])
ClienteIdFila = namedtuple("ClienteIdFila", ["id_cliente", "fila"])
RelatorioAgente = namedtuple("RelatorioAgente", [
    "id_time", "equipe", "estatisticas_chamadas", "chamadas_abandonadas", "agressividade"
])


def parse_id_clientes(clientes_http: Any) -> List[str]:
    clientes_html = BeautifulSoup(clientes_http.text, 'html.parser')
    tds_clientes = clientes_html.find_all('td', nowrap='')

    return [td.get_text() for td in tds_clientes]


def limpeza_lista_clientes(lista_clientes: List[str]) -> List[str]:
    '''
    Filtra e remove termos indesejados da lista de clientes
    '''
    termos_sujos = {' Sim', ' Ativo ', ' Descricao'}
    return [cliente for cliente in lista_clientes if cliente not in termos_sujos]

def extrair_ids_filas(html: Any) -> list[int]:
    """
    Extrai todos os IDs únicos de filas presentes nos hrefs das tags <a>.
    """
    soup = BeautifulSoup(html.text, "html.parser")
    td_tags = soup.find_all("td", class_="botao")

    lista_ids = []
    for td in td_tags:
        link = td.find("a", href=True)
        if link:
            href = link['href']
            params = parse_qs(urlparse(href).query)
            fila_id = params.get("obj_fila_id", [None])[0]
            if fila_id:
                lista_ids.append(int(fila_id))
    return lista_ids

def dicionario_clientes(lista_clientes: List[str], lista_ids: List[int]) -> List[ClienteInfo]:
    
    if len(lista_clientes) != len(lista_ids):
        logger.warning("Atenção: Quantidade de clientes e ids distinta")
    return [
        ClienteInfo(nome_cliente=cliente, id_cliente=identificador)
        for cliente, identificador in zip(lista_clientes, lista_ids)
    ]
    
def lista_de_clientes_para_filtragem(clientes_http: Any):
    clientes_sem_html = parse_id_clientes(clientes_http)
    lista_de_clientes = limpeza_lista_clientes(clientes_sem_html)
    ids_de_clientes_limpos = extrair_ids_filas(clientes_http)
    return dicionario_clientes(lista_clientes=lista_de_clientes, lista_ids=ids_de_clientes_limpos)


def limpeza_agressividade(agressividade_html: str) -> str:
    html = BeautifulSoup(agressividade_html, "html.parser")

    select_tag = html.find('select', attrs={'id': 'obj_fila_valor_overdial'})
    if not select_tag:
        logger.warning("Agressividade não encotnrada")
        return "0"
    opcao = select_tag.find('option', selected=True)
    if opcao:
        return opcao.get('value', '0')
    
    logger.warning("Tag de agressividade não encontrada")
    return '0'

def limpeza_chamadas_ipbox(chamadas_json):
    try:
        resultados = chamadas_json.get('data', {}).get('resultado', {})

        aceitas_qtd = resultados.get('ATENDIDO', {}).get('qtd', 0)
        totais_qtd = resultados.get('total', {}).get('qtd', 0)
        recusadas = totais_qtd - aceitas_qtd

        return EstatisticasChamadas(aceitas=aceitas_qtd, totais=totais_qtd, recusadas=recusadas)
    
    except Exception as e:
        logger.error(f"Erro ao limpar dados json {e}", exc_info=True)
        raise

def limpeza_agentes_ipbox(agentes_json: Dict[str, Any]) -> List[DesempenhoAgente]:
    """
    Retorna uma lista de dicionários com o desempenho de cada agente 
    e as chamadas completas de cada agente 
    """
    dados_json = agentes_json.get('data', [])

    return [
        DesempenhoAgente(
            cliente=dados.get("times", ""),
            chamadas_completas=dados.get("atendimentos", 0)
        )
        for dados in dados_json
    ]

def relatorio_completo_agente(id_time_ipbox: str,
                               fila_ipbox: str,
                               chamadas_abandonadas: int,
                                 agressividade: str,
                                   stats: EstatisticasChamadas) -> RelatorioAgente:
    
    return RelatorioAgente(
        id_time=id_time_ipbox,
        equipe=fila_ipbox,
        estatisticas_chamadas=stats,
        chamadas_abandonadas=chamadas_abandonadas,
        agressividade=agressividade
    )

def limpeza_clientes_ipbox(dict_cliente: dict[str, Any]) -> List[ClienteIdFila]:
    '''
    função para retornar o id do cliente separado da fila
    Como os ambientes geram 1234#01
    como deve ficar -> id = 1234; fila = 01
    '''
    identificadores = dict_cliente.get("ID Cliente", [])
    lista_id_clientes = []
    
    for cliente in identificadores:
        id_completo = cliente.get("ID Cliente", "")

        if '#' in id_completo:
            id_cliente, fila = id_completo.split('#', 1)
            lista_id_clientes.append(ClienteIdFila(id_cliente=id_cliente, fila=fila))
        else:
            logger.warning(f"Formato inesperado para o cliente: {id_completo}")

    return lista_id_clientes
    