from bs4 import BeautifulSoup
import json
import re 
import logging

from pandas.io.formats.format import return_docstring

log = logging.getLogger(__name__)

def mapeamento_clientes(clientes_html):
    dados = json.loads(clientes_html)

    return [
        {"Tech": re.sub(r"\D", "",dado["value"]),
         "Cliente": dado["value"],
         "id": dado["id"]
         }
        for dado in dados
        ]
    
    
def limpeza_consumo(html_consumo):
    '''
    Recebe o HTML da página e retorna uma lista de dicts:
    tech, cliente, minutagem, custo.

    O campo "Tech" é extraído por regex do próprio texto do cliente,
    da mesma forma que mapeamento_clientes() faz — garantindo que
    as duas fontes de dado possam ser combinadas por uma chave comum,
    em vez de por posição na lista.
    '''
    soup = BeautifulSoup(html_consumo, 'html.parser')
    tabelas = soup.find_all("table", class_="tabela_azul")

    resultado = []

    for tabela in tabelas:
        linhas = tabela.find_all("tr")

        for linha in linhas:
            celulas = linha.find_all("td")

            if len(celulas) != 8:
                log.warning(
                    "Linha de consumo ignorada — esperado 8 células, "
                    "encontrado %d. Conteúdo: %r",
                    len(celulas), [c.get_text(strip=True) for c in celulas]
                )
                continue

            cliente = celulas[0].get_text(strip=True)
            minutagem = celulas[2].get_text(strip=True)
            custo = celulas[4].get_text(strip=True)

            resultado.append({
                "Tech": re.sub(r"\D", "", cliente),
                "Cliente": cliente,
                "Minutagem": minutagem,
                "Custo": custo,
            })

    return resultado

def processar_tarifas_com_resiliencia(lista_chamadas_tarifadas: list) -> list[int]:
    """
    Processa a limpeza de tarifas de todos os clientes coletados.

    Cada cliente é processado de forma isolada: se um falhar,
    os demais continuam sendo processados normalmente.
    """
    resultados = []

    for indice, tarifa_html in enumerate(lista_chamadas_tarifadas):
        try:
            valor_limpo = limpeza_de_dados_final(tarifa_html)
            resultados.append(valor_limpo)
        except Exception as e:
            log.error(
                "Falha ao processar tarifa do cliente índice %d: %s",
                indice, e, exc_info=True
            )
            resultados.append(0)

    return resultados

def junta_clientes(tarifadas: list, resultado_custos: dict):
    list_dados = []
    for i, cliente in enumerate(resultado_custos):
        list_dados.append({
        "Cliente": cliente.get("Cliente"),
        "Chamadas Tarifadas": tarifadas[i] if i < len(tarifadas) else None,
        "Minutagem": cliente.get("Minutagem"),
        "Custo": cliente.get("Custo")
    })
    return list_dados
    
def limpeza_de_dados_base(json_clientes, html_custos):
    clientes_mapeados = mapeamento_clientes(json_clientes)
    consumo = limpeza_consumo(html_custos)
    print("CLIENTES MAPEADOS: ", clientes_mapeados)
   
    return clientes_mapeados, consumo

def limpeza_de_dados_final(lista_html):
    tarifadas = processar_tarifas_com_resiliencia(lista_html)
    return tarifadas
    