from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
import re

def get_clientes(clientes):
    clientes_html = BeautifulSoup(clientes.text, 'html.parser')
    print(clientes_html)

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
    Captura tanto 'obj_fila_id' quanto 'filaId' como parâmetros de query.
    """
    soup = BeautifulSoup(html.text, "html.parser")

    parametros_alvo = {"obj_fila_id", "filaid"}  # lowercase para comparação case-insensitive
    ids_encontrados = set()

    for tag in soup.find_all("a", href=True):
        query = parse_qs(urlparse(tag["href"]).query)

        for chave, valores in query.items():
            if chave.lower() in parametros_alvo:
                ids_encontrados.update(int(v) for v in valores if v.isdigit())

    return sorted(ids_encontrados)

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
    print("FIIIIM", lista_final)
    return lista_final
