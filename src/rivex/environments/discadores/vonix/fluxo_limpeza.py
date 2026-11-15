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

    def extrair_operadores_cliente(self, html_operadores, cliente: str | None = None):
        """
        Recebe a resposta HTML (requests.Response ou str) de GET /admin/agent_list
        e retorna apenas os operadores ativos vinculados ao cliente filtrado na sessão.
        """
        conteudo = html_operadores.text if hasattr(html_operadores, 'text') else html_operadores
        if not isinstance(conteudo, str) or not conteudo.strip():
            return []

        soup = BeautifulSoup(conteudo, 'html.parser')
        tbody = soup.find('tbody', id='agents') or soup
        operadores = []

        for row in tbody.find_all('tr', id=lambda x: x and x.startswith('agent_')):
            classes = row.get('class') or []
            if 'inactive_agent' in classes:
                continue

            cells = row.find_all('td')
            if len(cells) < 5:
                continue

            nome = cells[1].get_text(strip=True)
            matricula = cells[2].get_text(strip=True)
            ultimo_login = cells[3].get_text(strip=True)
            filas_texto = cells[4].get_text(' ', strip=True)
            filas = [fila.strip() for fila in filas_texto.split(',') if fila.strip()]
            tag_padrao = cells[4].find('u')
            fila_padrao = tag_padrao.get_text(strip=True) if tag_padrao else None

            registro = {
                'matricula': matricula,
                'nome': nome,
                'ultimo_login': ultimo_login,
                'filas': filas,
                'fila_padrao': fila_padrao,
            }
            if cliente is not None:
                registro['cliente'] = cliente

            operadores.append(registro)

        return operadores

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