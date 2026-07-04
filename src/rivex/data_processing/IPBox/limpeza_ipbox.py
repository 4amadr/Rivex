from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from html import unescape
import re
import json

def gerar_html(texto):
    return BeautifulSoup(texto, "html.parser")

def gerar_lista_clientes(html_agentes):
    return html_agentes.find_all('tr', class_='linha1')

def get_cliente(cliente_html):
    return cliente_html.find('td', attrs={"nowrap": ""}).get_text()

def get_tech_cliente(cliente):
    numeros = re.findall(r"\d", cliente)
    return "".join(numeros[:6])

def get_identificador(cliente_html):
    href = cliente_html.find("a")["href"]
    return parse_qs(urlparse(href).query)["obj_fila_id"][0]

def get_agressividade(agressividade_html):
    agressividade_html = gerar_html(agressividade_html)
    select = agressividade_html.find('select', id='obj_fila_valor_overdial')
    return select.find("option", selected=True).get_text()

def get_chamadas_totais_cliente(chamadas_json):
    return chamadas_json.get('data', {}).get('resultado', {}).get('total', {}).get('qtd', 0)
    
def get_chamadas_completas_cliente(chamadas_json):
    return chamadas_json.get('data', {}).get('resultado', {}).get('ATENDIDO', {}).get('qtd', 0)


def get_chamadas_recusadas_cliente(chamadas_json):
    ocupado = int(chamadas_json.get('data', {}).get('resultado', {}).get('OCUPADO', {}).get('qtd', 0))
    sem_resposta = int(chamadas_json.get('data', {}).get('resultado', {}).get('SEM_RESPOSTA', {}).get('qtd', 0))
    desconhecido = int(chamadas_json.get('data', {}).get('resultado', {}).get('DESCONHECIDO', {}).get('qtd', 0))
    
    return ocupado + sem_resposta + desconhecido

def get_chamadas_abandonadas_cliente(chamadas_json):
    return chamadas_json.get('data', {}).get('resultado', {}).get('CONGESTIONADO', {}).get('qtd', 0)
  
  
def get_lista_agentes(agentes_json):
    return [dados["agente"] for dados in agentes_json["data"]]          
        
        
def limpar_nome_cliente(time):
    return unescape(time).split(" - ", 1)[1]
    
        

def get_chamadas_completas_agente(agentes_json):
    return agentes_json['atendimentos']

def empacotar_dados_clientes(chamadas_json, cliente, data, agressividade):
    return {
        "cliente": cliente,
        "tech": get_tech_cliente(cliente),
        "data": data,
        "discador": "Vonix",
        "chamadas totais": get_chamadas_totais_cliente(chamadas_json),
        "chamadas completas": get_chamadas_completas_cliente(chamadas_json),
        "chamadas recusadas": get_chamadas_recusadas_cliente(chamadas_json),
        "chamadas abandonadas": get_chamadas_abandonadas_cliente(chamadas_json),
        "agressividade": get_agressividade(agressividade)
    }
    

    
def empacotar_dados_agentes(agente, cliente, data):
    return {
        "tech": get_tech_cliente(cliente),
        "cliente": cliente,
        "data": data,
        "nome agente": agente["agente"],
        "chamadas do agente": agente["atendimentos"]
    }
     
    
    



    

