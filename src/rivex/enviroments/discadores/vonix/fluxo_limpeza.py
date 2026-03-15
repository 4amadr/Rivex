from src.rivex.utils.beautiful_soup_utils.cleaning_soup import CleaningSoup
from bs4 import BeautifulSoup

class LimpezaVonix:
    def encontrar_tabela(self, html_selecionado):
        # função para gerar tabelas
        cs = CleaningSoup()
        html_chamadas = cs.passar_para_html(html_selecionado)
        tabela_chamadas = html_chamadas.find('table')
        return tabela_chamadas
    
    def nova_chamadas(self, html):
        #limpeza de dados de chamadas
        html_convertido = BeautifulSoup(html, 'html.parser')
        div_conteudo = html_convertido.find('div', id='maincontent')
        div_chamadas = div_conteudo.find('div', class_='box-title')
        texto_chamadas = div_chamadas.text

        # limpar a resposta
        inicio_coleta = "("
        fim_coleta = ")"

        inicio_dados = texto_chamadas.find(inicio_coleta) + len(inicio_coleta)
        fim_dados = texto_chamadas.find(fim_coleta)
        resultado = texto_chamadas[inicio_dados:fim_dados] 

        return resultado

    def encontrar_linha_do_agente(self, tabela):
        # função para encontrar a linha que contém o nome e as chamadas do agente
        if not tabela:
            return None
        linha = tabela.find_all('tr', class_=['item', 'shaded'])
        return linha

    def nomes_agente(self, linhas):
        # se não houver linhas deve retornar lista vazia = 0
        if not linhas:
            return []
        
        agentes_online = []
        for linha in linhas:
            agente_nome = linha.find('td', class_='item')  
            if agente_nome:
                agentes_online.append(agente_nome.get_text())
        return agentes_online

    def chamadas_por_agentes(self, linhas):
        if not linhas:
            return []
        chamadas_por_agentes = []
        for chamada in linhas:  # itera sobre cada <tr> normalmente
            div_chamadas = chamada.find('td', id=lambda c: c and c.startswith('call_counter_AUTO_'))
            if div_chamadas:
                chamadas_na_div = div_chamadas.find('a')
                if chamadas_na_div:
                    chamadas_por_agentes.append(chamadas_na_div)
        return chamadas_por_agentes

    def filtrar_agentes_por_chamadas(self, agentes, chamadas):
        '''Regra de negócio para excluir agentes que fizeram até 4 chamadas'''
        agentes_filtrados = []
        for agente, chamada in zip(agentes, chamadas):
            quantidade = int(chamada.get_text())
            if quantidade > 4:
                agentes_filtrados.append(agente)

        quantidade_agentes_validos = len(agentes_filtrados)
        return quantidade_agentes_validos

    def agressividade(self, html_agressividade):
        cs = CleaningSoup()
        html_agressividade = cs.passar_para_html(html_agressividade)
        agressividade = html_agressividade.find('input', id='dialer_dial_speed')['value']
        return agressividade

    def limpeza_de_dados_vonix(self, html_chamadas_totais, html_chamadas_completas, html_chamadas_recusadas, html_chamadas_abandonadas, html_agentes, html_agressividade, equipe, data):
        # vai executar todas as funções de limpeza de dados e retornar os dados limpos em um dicionário

        # agressividade
        agressividade_da_fila = self.agressividade(html_agressividade)

        # chamadas
        tabela = self.encontrar_tabela(html_agentes)
        discador = "Vonix"
        if not tabela:
            return {
                'discador': discador,
                'fila': equipe,
                'data': data,
                'chamadas_totais': 0,
                'chamadas_completas': 0,
                'chamadas_recusadas': 0,
                'chamadas_abandonadas': 0,
                'agentes_online': 0,
                'agressividade': agressividade_da_fila,
            }
        '''A agressividade sempre terá valor, então independente do agente fazer ligações ou não
          sempre haverá agressividade'''


        chamadas_totais = self.nova_chamadas(html_chamadas_totais)
        chamadas_aceitas = self.nova_chamadas(html_chamadas_completas)
        chamadas_recusadas = self.nova_chamadas(html_chamadas_recusadas)
        chamadas_abandonadas = self.nova_chamadas(html_chamadas_abandonadas)
        
        # agentes validados (fizeram mais de 4 chamadas automáricas)
        tabela_de_agentes = self.encontrar_tabela(html_agentes)
        linha_com_agentes = self.encontrar_linha_do_agente(tabela_de_agentes)
        nome_agente = self.nomes_agente(linha_com_agentes)
        chamadas_por_agente = self.chamadas_por_agentes(linha_com_agentes)
        agentes_filtrados = self.filtrar_agentes_por_chamadas(nome_agente, chamadas_por_agente)


        return {
            'discador': 'Vonix',
            'fila': equipe,
            'data': data,
            'chamadas_totais': chamadas_totais,
            'chamadas_completas': chamadas_aceitas,
            'chamadas_recusadas': chamadas_recusadas,
            'chamadas_abandonadas': chamadas_abandonadas,
            'agentes_online': agentes_filtrados,
            'agressividade': agressividade_da_fila,
        }