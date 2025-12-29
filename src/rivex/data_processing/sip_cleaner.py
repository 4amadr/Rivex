import pandas as pd
from rivex.automations.gsolutions.sip_client_scrap import SipClient
import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()

class SipCleaner:
    # teste com a Gsolutions
    sip = SipClient(usuario=os.getenv('GSOLUTIONS_LOGIN'), password=os.getenv('GSOLUTIONS_PASSWORD'), url=os.getenv('GSOLUTIONS_URL'), operadora='Gsolutions')
    operadora = 'Gsolutions'
    data = '2025-12-15'
    html_dados = sip.execucao_pipeline_sip(sip.url, sip.usuario, sip.password, operadora, data)
    
    def limpeza_beautiful_soup(self, html_dados):
        '''Função para tratar os dados HTML coletados do beautiful soup'''
        tabelas = html_dados.find_all("table", class_="tabela_azul")
        
        tabela_select = None
        
        for tabela in tabelas:
            cabecalho = tabela.find("th")
            if cabecalho and "Minutagem da Revenda" in cabecalho.get_text():
                tabela_select = tabela
                break
        return tabela_select
        if tabela_select is None:
            raise RuntimeError("Minutagem da revenda não encontrada")
            return None
    
    def get_linhas(self, tabela_select):
        tr = tabela_select.find_all('tr', class_=['cinza1', 'cinza2'])
        print(tr)
        
        
        
limpador = SipCleaner()
sip = SipClient(usuario=os.getenv('GSOLUTIONS_LOGIN'), password=os.getenv('GSOLUTIONS_PASSWORD'), url=os.getenv('GSOLUTIONS_URL'), operadora='Gsolutions')
operadora = 'Gsolutions'
data = '2025-12-15'
html_dados = sip.execucao_pipeline_sip(sip.url, sip.usuario, sip.password, operadora, data)
tabela = limpador.limpeza_beautiful_soup(html_dados)
tr = limpador.get_linhas(tabela)