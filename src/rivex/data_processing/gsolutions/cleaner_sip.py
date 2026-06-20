from bs4 import BeautifulSoup
import json
import re 

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
    Recebe o HTML da página e 
    retorna uma lista de dicts: cliente, minutagem, custo
    '''
    soup = BeautifulSoup(html_consumo, 'html.parser')
    
    tabelas = soup.find_all("table", class_="tabela_azul")
    
    resultado = []
    
    for tabela in tabelas:
        linhas = tabela.find_all("tr")
        
        for linha in linhas:
            celulas = linha.find_all("td")
            
            if len(celulas) != 8:
                continue
            cliente = celulas[0].get_text(strip=True)
            minutagem = celulas[2].get_text(strip=True)
            custo = celulas[4].get_text(strip=True)
            
            resultado.append({
                "Cliente": cliente,
                "Minutagem": minutagem,
                "Custo": custo,
            })
    return resultado

def limpeza_tarifadas(lista_html):
    '''
    Deve ser executada separadamente pois a função precisa esperar a coleta de chamadas tarifadas 
    ser executada para funcionar
    '''
    resultados = []
    
    for html in lista_html:
        soup = BeautifulSoup(html, 'html.parser')
        tag = soup.find(id='total_registros_texto')
        if tag:
            numero = re.search(r'\d+', tag.get_text())
            resultados.append(numero.group() if numero else None)
        if tag == None:
            tag = 0
            resultados.append(tag)

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
    tarifadas = limpeza_tarifadas(lista_html)
    return tarifadas
    