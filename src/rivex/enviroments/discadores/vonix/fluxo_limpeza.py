from src.rivex.utils.beautiful_soup_utils.cleaning_soup import CleaningSoup

class LimpezaVonix:
    def encontrar_tabela(self, html_selecionado):
        # função para trazer apenas as chamadas completas
        cs = CleaningSoup()
        html_chamadas = cs.passar_para_html(html_selecionado)
        # chamadas seguem a hierarquia <table> -> <tr> -> <td>
        tabela_chamadas = html_chamadas.find('table')
        # uma tabela só contém todos os dados(automáticos e manuais. Legados...)
        return tabela_chamadas
    '''endereço chamadas -> 11 = Chamadas totais, 12 -> Chamadas completas
    13 -> Chamadas recusadas, 14 -> Chamadas abandonadas'''

    def chamadas(self, tabela, endereco):
        try:
            linhas = tabela.find_all('tr')

            # Tabela sem linhas (agente offline)
            if not linhas or len(linhas) <= endereco:
                return '0'

            linha_totais = linhas[endereco]
            colunas = linha_totais.find_all('td')

            # Linha sem colunas
            if len(colunas) < 3:
                return '0'

            valor_texto = colunas[2].text.strip().split()

            # Coluna vazia ou sem texto
            if not valor_texto:
                print('Coluna sem valor. Retornando zero.')
                return '0'

            return valor_texto[-1]

        except Exception as e:
            print(f'Erro inesperado em chamadas(): {e}')
            return '0'

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

    def limpeza_de_dados_vonix(self, html_chamadas, html_agentes, html_agressividade, equipe, data):
        # vai executar todas as funções de limpeza de dados e retornar os dados limpos em um dicionário

        # agressividade
        agressividade_da_fila = self.agressividade(html_agressividade)

        # chamadas
        tabela = self.encontrar_tabela(html_chamadas)
        if not tabela:
            return {
                'Discador': 'Vonix',
                'Fila': equipe,
                'Data': data,
                'Chamadas totais': 0,
                'Chamadas completas': 0,
                'Chamadas recusadas': 0,
                'Chamadas abandonadas': 0,
                'Agentes online': 0,
                'Agressividade': agressividade_da_fila,
            }
        '''caso a fila não esteja sendo usada a tabela nem é mostrada. Então vai quebrar o código.
          Para isso vou retornar none na primeira verificação para tornar a execução mais rápida 
          e passar logo para a próxima fila.
          OBS: A agressividade sempre terá valor, então independente do agente fazer ligações ou não
          sempre haverá agressividade'''


        chamadas_totais = self.chamadas(tabela, 11)
        chamadas_aceitas = self.chamadas(tabela, 12)
        chamadas_recusadas = self.chamadas(tabela, 13)
        chamadas_abandonadas = self.chamadas(tabela, 14)

        # agentes validados (fizeram mais de 4 chamadas automáricas)
        tabela_de_agentes = self.encontrar_tabela(html_agentes)
        linha_com_agentes = self.encontrar_linha_do_agente(tabela_de_agentes)
        nome_agente = self.nomes_agente(linha_com_agentes)
        chamadas_por_agente = self.chamadas_por_agentes(linha_com_agentes)
        agentes_filtrados = self.filtrar_agentes_por_chamadas(nome_agente, chamadas_por_agente)


        return {
            'Fila': equipe,
            'Data': data,
            'Chamadas totais': chamadas_totais,
            'Chamadas completas': chamadas_aceitas,
            'Chamadas recusadas': chamadas_recusadas,
            'Chamadas abandonadas': chamadas_abandonadas,
            'agentes_online': agentes_filtrados,
            'agressividade': agressividade_da_fila,
        }