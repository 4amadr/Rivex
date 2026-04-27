from bs4 import BeautifulSoup

def mapeamento_clientes(json_clientes):
    return [
        {"Cliente": info['value'],
         "id": info['id'],
        }
         for info in json_clientes]
        
def limpeza_custo(html_custos):
    '''
    Recebe o HTML da página e 
    retorna uma lista de dicts: cliente, minutagem, custo
    '''
    soup = BeautifulSoup(html_custos, 'html.parser')
    
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
            import re
            numero = re.search(r'\d+', tag.get_text())
            resultados.append(numero.group() if numero else None)
        else:
            resultados.append(None)
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
    resultado_custos = limpeza_custo(html_custos)
   
    return clientes_mapeados, resultado_custos

def limpeza_de_dados_final(lista_html, resultado_custos: dict):
    tarifadas = limpeza_tarifadas(lista_html)
    dict_dados = junta_clientes(tarifadas, resultado_custos)
    return dict_dados
    