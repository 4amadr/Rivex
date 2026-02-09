from bs4 import BeautifulSoup
from rivex.automations.vonix.vonix_06 import VonixSip

class VonixCleaner:
    def gerar_soup_chamadas(dados):
        '''Função para transformar em sopa os dados coletados com requests'''
        # passando para o formato HTML para melhorar a conversão de dados
        soup = BeautifulSoup(dados.text, 'html.parser')
        # os dados estão dentro de td
        sopa_chamadas = soup.find_all('td')
        return sopa_chamadas
    
    def gerar_soup_agentes(dados_agentes):
        '''Função de tratamento de dados em HTML que tem 
        processo distinto do tratamento de chamadas'''
        sopa_agentes = BeautifulSoup(dados_agentes.text, 'html.parser')
        agentes_online = sopa_agentes.find_all('div', class_='box-title')
        return agentes_online
    
    def limpador_chamadas(sopa, endereco: int):
        '''função para limpar as chamadas totais. Os dados chegam em formato html bruto
        e serão transformados em dados tratados já prontos para analise'''
        chamadas = sopa_chamadas[endereco]
        chamadas_tratadas = chamadas.text.split()
        
        # alguns dados vem em formato de lista e isso vai verificar
        if isinstance(chamadas_tratadas, list):
            chamadas_tratadas = chamadas_tratadas[0]
            return chamadas_tratadas
        else:
            return chamadas_tratadas
        
    def tratar_agentes(sopa_agentes):
        '''Função para gerar dados tratados dos agentes a partir do HTML coletado
        com requests'''
        separacao = list(sopa_agentes[1])
        agentes_online_bruto = separacao[1]
        return agentes_online_bruto
    
    def chamadas_agentes(sopa_chamadas_de_agentes):
        '''Função para coletar quantas chamadas cada agente fez'''
        sopa_chamadas = sopa_chamadas_de_agentes.find_all('div', class_='progress-bar')
        chamadas_todos = [
            int(a.text.strip())
            for chamada in sopa_chamadas
            for a in chamada.find_all('a', href=True)
        ]
        return chamadas_todos
        
    def agressividade(agressividade_html):
        '''Função para transformar o HTML bruto em dado limpo tratado de agressividade'''
        agressividade = BeautifulSoup(agressividade_html.text, 'html.parser')
        dial_speed = agressividade.find("input", id="dialer_dial_speed").get("value")
        return dial_speed  
    
    def execucao_vonix():
        chamadas = gerar_soup_chamadas()
        sopa_agentes = gerar_soup_agentes()
        chamadas_totais = limpador_chamadas()
        chamadas_completas = limpador_chamadas()
        chamadas_recusadas = limpador_chamadas()
        chamadas_abandonadas = limpador_chamadas()
        agentes_online = tratar_agentes()
        chamadas_todos = chamadas_agentes()
        dial_speed = agressividade()
    return chamadas_totais, chamadas_completas, chamadas_recusadas, chamadas_abandonadas, agentes_online, chamadas_agentes, dial_speed
        