from bs4 import BeautifulSoup

def limpeza_cdr(cdr_html):
    # passando para HTML
    dados = BeautifulSoup(cdr_html.text, 'html.parser')
    cliente_id = dados.find_all("td", class_="text-left navy")
    elementos = dados.find_all("td", class_="text-center green")
    chamadas_tarifadas = dados.find_all("td", class_="text-center blueviolet")
    
    return cliente_id, elementos, chamadas_tarifadas
  
def listagem_de_elementos(elementos):
    # função para transformar os dados em uma lista para ser desempacotado futuramente
    lista_separada = [item.get_text(strip=True) for item in elementos]
    return lista_separada

def desempacotar_lista(lista_separada):
    # função para desempacotar os dados da lista
    minutagem = lista_separada[0::2]
    custos = lista_separada[1::2]
    
    return minutagem, custos

def remover_html(cliente_id, chamadas_tarifadas):
    
    cliente = [item.get_text(strip=True) for item in cliente_id]
    tarifa = [item.get_text(strip=True) for item in chamadas_tarifadas]
    
    return cliente, tarifa

def gerar_dicionario(clientes, tarifa, minutagem, custos):
    lista_dados = []
    
    for cliente, chamada, minuto, custo in zip(clientes, tarifa, minutagem, custos):
        dict_cliente = {
            'Cliente ID':  cliente,
            'Chamadas tarifadas': chamada,
            'Minutagem': minuto,
            'Custos': custo
        }
        lista_dados.append(dict_cliente)
    return lista_dados
        
def execucao_limpeza(cdr_html):
    cliente_id, elementos, chamadas_tarifadas = limpeza_cdr(cdr_html)
    lista_separada = listagem_de_elementos(elementos)
    minutagem, custos = desempacotar_lista(lista_separada)
    cliente, tarifa = remover_html(cliente_id, chamadas_tarifadas)
    lista_dados = gerar_dicionario(cliente, tarifa, minutagem, custos)
    
    
    
    return lista_dados
    
    
    
    
    