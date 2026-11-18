from src.rivex.utils.beautiful_soup_utils.cleaning_soup import CleaningSoup
from bs4 import BeautifulSoup

class LimpezaVonix:

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