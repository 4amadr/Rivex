from bs4 import BeautifulSoup

def mapeamento_clientes(json_clientes):
    return {info['value']: info['id'] for info in json_clientes}
        

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