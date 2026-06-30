from bs4 import BeautifulSoup
import re

def limpeza_cdr(cdr_html):
    # passando para HTML
    dados = BeautifulSoup(cdr_html.text, 'html.parser')
    return dados

def lista_clientes(dados):
    tags_clientes = dados.find_all("td", class_="text-left navy")
    return [td.text.replace("#", "") for td in tags_clientes]

def elementos_html(dados):
    return dados.find_all("td", class_="text-center green")

def limpeza_chamadas_tarifadas(dados):
    return [
        td.get_text(strip=True)
        for td in dados.find_all("td", class_="text-center blueviolet")
    ]
  
def gerar_minutagem_texto(elementos):
    return [item.get_text(strip=True) for item in elementos][::2]

def converter_minutagem(minutagens):
    return [
        int(match.group(1).replace(".", "")) + int(match.group(2)) / 60
        for tempo in minutagens
        if (match := re.match(r'([\d\.]+)\s*min\s*(\d+)\s*seg', tempo))
    ]


def gerar_custos(elementos):
    return [
    float(td.text.strip().replace(",","."))
    for td in elementos
    if re.fullmatch(r"\d+,\d+", td.text.strip())
]

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
    dados = limpeza_cdr(cdr_html)
    lista_tech_clientes = lista_clientes(dados)
    elementos = elementos_html(dados)
    chamadas_tarifadas = limpeza_chamadas_tarifadas(dados)
    minutagem_texto = gerar_minutagem_texto(elementos)
    custos = gerar_custos(elementos)
    minutagem = converter_minutagem(minutagem_texto)

    lista_dados = gerar_dicionario(lista_tech_clientes, chamadas_tarifadas, minutagem, custos)
    print("[TESTE LISTA DE DADOS]")
    print(lista_dados)

    return lista_dados
    
    
    
    
    
    
    