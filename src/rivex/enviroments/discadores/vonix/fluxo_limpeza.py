from src.rivex.utils.beautiful_soup_utils.cleaning_soup import CleaningSoup
from bs4 import BeautifulSoup

class LimpezaVonix:

    def encontrar_tabela(self, html_selecionado):
        cs = CleaningSoup()
        html_chamadas = cs.passar_para_html(html_selecionado)
        tabela_chamadas = html_chamadas.find('table')
        return tabela_chamadas

    def nova_chamadas(self, html):
        html_convertido = BeautifulSoup(html, 'html.parser')
        div_conteudo = html_convertido.find('div', id='maincontent')
        div_chamadas = div_conteudo.find('div', class_='box-title')
        texto_chamadas = div_chamadas.text

        inicio_dados = texto_chamadas.find("(") + 1
        fim_dados = texto_chamadas.find(")")
        return texto_chamadas[inicio_dados:fim_dados]

    def extrair_chamadas_agentes(self, html):
        """
        Recebe o HTML da tabela de agentes, extrai e retorna
        uma lista de dicionários com o nome do agente e total de chamadas.

        Retorno:
            [{'agente': 'Nome Agente (ramal)', 'chamadas': 259}, ...]
        """
        def get_count(cell):
            link = cell.find('a')
            text = (link or cell).get_text(strip=True)
            return int(text) if text.isdigit() else 0

        soup = BeautifulSoup(html.text, 'html.parser')
        results = []

        for row in soup.find_all('tr', class_=['item', 'shaded']):
            cells = row.find_all('td')
            if len(cells) < 6:
                continue

            agente = cells[0].get_text(strip=True)
            chamadas = get_count(cells[2]) + get_count(cells[3]) + get_count(cells[4])

            results.append({'agente': agente, 'chamadas': chamadas})

        return results

    def agressividade(self, html_agressividade):
        cs = CleaningSoup()
        html_agressividade = cs.passar_para_html(html_agressividade)
        return html_agressividade.find('input', id='dialer_dial_speed')['value']

    def limpeza_de_dados_vonix(self, html_chamadas_totais, html_chamadas_completas, html_chamadas_recusadas, html_chamadas_abandonadas, html_agentes, html_agressividade, equipe, data):
        agressividade_da_fila = self.agressividade(html_agressividade)
        discador = "Vonix"

        tabela = self.encontrar_tabela(html_agentes)
        if not tabela:
            print('Sem consumo na fila: ', equipe)
            
            return {
                'discador': discador,
                'fila': equipe,
                'data': data,
                'chamadas_totais': 0,
                'chamadas_completas': 0,
                'chamadas_recusadas': 0,
                'chamadas_abandonadas': 0,
                'agentes': [],
                'agressividade': agressividade_da_fila,
            }

        dict_dados_limpos = {
            'discador': discador,
            'fila': equipe,
            'data': data,
            'chamadas_totais': self.nova_chamadas(html_chamadas_totais),
            'chamadas_completas': self.nova_chamadas(html_chamadas_completas),
            'chamadas_recusadas': self.nova_chamadas(html_chamadas_recusadas),
            'chamadas_abandonadas': self.nova_chamadas(html_chamadas_abandonadas),
            'agentes': self.extrair_chamadas_agentes(html_agentes),
            'agressividade': agressividade_da_fila,
        }
        return dict_dados_limpos