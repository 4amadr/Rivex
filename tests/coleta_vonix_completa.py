"""
Script completo de coleta de dados do Vonix.
Demonstra o fluxo correto: Login → Filtrar fila → Coletar dados.

A causa raiz do problema é que o Vonix requer seleção de fila ANTES
de qualquer consulta de dados. Sem esse passo, retorna a página inicial
(que contém authenticity_token e parece ser a página de login).
"""
import os
import json
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from urllib.parse import urljoin

load_dotenv()

URL_BASE = os.getenv('LINK_VONIX6', 'http://contech6.vonixcc.com.br')
LOGIN = os.getenv('LOGIN_VONIX')
PASSWORD = os.getenv('PASSWORD_VONIX')


class VonixCollector:
    def __init__(self, url_base, login, password):
        self.url_base = url_base
        self.login = login
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })

    def _url(self, path):
        return urljoin(self.url_base, path)

    def _get_token(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        token_input = soup.find('input', {'name': 'authenticity_token'})
        if token_input:
            return token_input['value']
        return None

    def _is_logged_in(self, html):
        """Detecta se estamos logados verificando conteúdo da página."""
        soup = BeautifulSoup(html, 'html.parser')
        # Se encontrar elemento de navegação do dashboard, está logado
        nav_items = soup.find_all('a', href=True)
        logged_indicators = [a for a in nav_items if any(x in a.get('href', '') for x in ['/overview', '/calls', '/agents'])]
        # Se encontrar campo de password, é tela de login real
        password_field = soup.find('input', {'name': 'password', 'type': 'password'})
        return len(logged_indicators) > 0 or password_field is None

    def fazer_login(self):
        """Etapa 1: Login no ambiente."""
        url_login = self._url('/login/signin')
        print(f"[LOGIN] GET {url_login}")
        resp = self.session.get(url_login)
        token = self._get_token(resp.text)

        payload = {
            'authenticity_token': token,
            'return_to': '',
            'username': self.login,
            'password': self.password,
            'commit': 'Entrar'
        }

        print(f"[LOGIN] POST {url_login}")
        resp_post = self.session.post(
            url_login,
            data=payload,
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': url_login,
                'Origin': self.url_base,
            },
            allow_redirects=True
        )

        # Verificar login
        soup = BeautifulSoup(resp_post.text, 'html.parser')
        password_field = soup.find('input', {'name': 'password', 'type': 'password'})
        if password_field:
            print("[LOGIN] FALHOU - Ainda na tela de login")
            return False

        print(f"[LOGIN] OK - Redirecionado para: {resp_post.url}")
        print(f"[LOGIN] Cookies: {list(self.session.cookies.keys())}")
        return True

    def filtrar_fila(self, queue_id):
        """Etapa 2: Selecionar fila (OBRIGATÓRIO antes de qualquer coleta)."""
        url_filtro = self._url('/login/set_show_queue')

        # GET para pegar token
        print(f"\n[FILTRO] GET {url_filtro}")
        resp_get = self.session.get(url_filtro, allow_redirects=True)
        token = self._get_token(resp_get.text)

        if not token:
            # Tentar pegar do HTML redirecionado
            resp_home = self.session.get(self._url('/'), allow_redirects=True)
            token = self._get_token(resp_home.text)

        payload = {
            'authenticity_token': token,
            'return_to': '/overview',
            'queue_id[]': queue_id
        }

        print(f"[FILTRO] POST {url_filtro} (fila: {queue_id})")
        resp_post = self.session.post(
            url_filtro,
            data=payload,
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': self._url('/'),
                'Origin': self.url_base,
            },
            allow_redirects=True
        )
        print(f"[FILTRO] Status: {resp_post.status_code} - URL: {resp_post.url}")
        return resp_post

    def coletar_chamadas(self, data, tipo_chamada=''):
        """Etapa 3: Coletar dados de chamadas."""
        url_calls = self._url('/calls')

        print(f"\n[CHAMADAS] GET {url_calls} (tipo: {tipo_chamada or 'TODAS'})")
        
        params = {
            'interval[select]': 'custom',
            'interval[start_date]': data,
            'interval[start_time]': '00:00:00',
            'interval[end_date]': data,
            'interval[end_time]': '23:59:59',
            'terminal': '',
            'agent': '',
            'queue[direction]': 'ALL',
            'sort': '',
            'to_excel': '0',
            'to_csv': '0',
            'x': '10',
            'y': '10',
            'locality': '',
            'call_type_id': '',
            'carrier_id': '',
            'trunking_id': '',
            'directions[]': 'AUTO',
            'waits': 'Igual',
            'call_waiting': '',
            'duration': 'Igual',
            'duration_call': '',
            'status[select]': tipo_chamada,
            'substatus[select]': ''
        }

        resp = self.session.get(
            url_calls,
            params=params,
            headers={
                'Referer': self._url('/overview'),
            },
            allow_redirects=True
        )

        print(f"[CHAMADAS] Status: {resp.status_code}")
        return resp.text

    def extrair_total_chamadas(self, html):
        """Extrai o total de chamadas do HTML."""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Verificar se é página de login (falha de sessão)
        password_field = soup.find('input', {'name': 'password', 'type': 'password'})
        if password_field:
            return "ERRO: Sessão expirada - retornou tela de login"

        div_conteudo = soup.find('div', id='maincontent')
        if div_conteudo:
            div_chamadas = div_conteudo.find('div', class_='box-title')
            if div_chamadas:
                texto = div_chamadas.text
                inicio = texto.find("(") + 1
                fim = texto.find(")")
                if inicio > 0 and fim > 0:
                    return texto[inicio:fim]

        return "N/A"

    def coletar_agentes(self, data):
        """Coleta dados de agentes online."""
        url_agents = self._url('/agents/calls_overview')
        
        print(f"\n[AGENTES] GET {url_agents}")
        params = {
            'interval[select]': 'custom',
            'interval[start_date]': data,
            'interval[end_date]': data,
        }

        resp = self.session.get(
            url_agents,
            params=params,
            headers={'Referer': self._url('/overview')},
            allow_redirects=True
        )
        print(f"[AGENTES] Status: {resp.status_code}")
        return resp

    def extrair_dados_agentes(self, resp):
        """Extrai nome e chamadas de cada agente."""
        soup = BeautifulSoup(resp.text, 'html.parser')
        results = []

        for row in soup.find_all('tr', class_=['item', 'shaded']):
            cells = row.find_all('td')
            if len(cells) < 6:
                continue
            
            agente = cells[0].get_text(strip=True)
            
            def get_count(cell):
                link = cell.find('a')
                text = (link or cell).get_text(strip=True)
                return int(text) if text.isdigit() else 0

            chamadas = get_count(cells[2]) + get_count(cells[3]) + get_count(cells[4])
            results.append({'agente': agente, 'chamadas': chamadas})

        return results

    def coletar_agressividade(self, queue_id):
        """Coleta valor de agressividade da fila."""
        url = self._url(f'/admin/queue_edit/{queue_id}')
        
        print(f"\n[AGRESSIVIDADE] GET {url}")
        resp = self.session.get(url, allow_redirects=True)
        print(f"[AGRESSIVIDADE] Status: {resp.status_code}")

        soup = BeautifulSoup(resp.text, 'html.parser')
        input_speed = soup.find('input', id='dialer_dial_speed')
        if input_speed:
            return input_speed['value']
        return "N/A"

    def listar_filas(self):
        """Lista todas as filas disponíveis no ambiente."""
        resp = self.session.get(self._url('/'), allow_redirects=True)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        filas = []
        # Buscar opções de fila no formulário
        for option in soup.find_all('input', {'name': 'queue_id[]'}):
            value = option.get('value', '')
            label_tag = option.find_next('label') or option.find_next_sibling(string=True)
            label = ''
            if label_tag:
                label = label_tag.get_text(strip=True) if hasattr(label_tag, 'get_text') else str(label_tag).strip()
            if value:
                filas.append({'id': value, 'nome': label})
        
        return filas


# ============================================================
# EXECUÇÃO
# ============================================================
if __name__ == '__main__':
    from datetime import date
    
    collector = VonixCollector(URL_BASE, LOGIN, PASSWORD)
    
    # 1. Login
    if not collector.fazer_login():
        print("Login falhou. Abortando.")
        exit(1)
    
    # 2. Listar filas disponíveis
    print("\n" + "=" * 60)
    print("FILAS DISPONÍVEIS")
    print("=" * 60)
    filas = collector.listar_filas()
    for f in filas[:20]:  # Primeiras 20
        print(f"  ID: {f['id']:<30} Nome: {f['nome']}")
    print(f"  ... Total: {len(filas)} filas")

    # 3. Testar com uma fila específica (tcrepresentacao)
    fila_teste = 'tcrepresentacao'
    data_teste = date.today().strftime('%Y-%m-%d')
    
    print(f"\n{'=' * 60}")
    print(f"TESTE DE COLETA - Fila: {fila_teste} | Data: {data_teste}")
    print(f"{'=' * 60}")
    
    # Filtrar fila
    collector.filtrar_fila(fila_teste)
    
    # Coletar chamadas
    html_totais = collector.coletar_chamadas(data_teste, '')
    html_completas = collector.coletar_chamadas(data_teste, 'completed')
    html_abandonadas = collector.coletar_chamadas(data_teste, 'abandon')
    html_recusadas = collector.coletar_chamadas(data_teste, 'discard')
    
    total_totais = collector.extrair_total_chamadas(html_totais)
    total_completas = collector.extrair_total_chamadas(html_completas)
    total_abandonadas = collector.extrair_total_chamadas(html_abandonadas)
    total_recusadas = collector.extrair_total_chamadas(html_recusadas)
    
    print(f"\n{'=' * 60}")
    print(f"RESULTADOS")
    print(f"{'=' * 60}")
    print(f"  Chamadas Totais:      {total_totais}")
    print(f"  Chamadas Aceitas:     {total_completas}")
    print(f"  Chamadas Abandonadas: {total_abandonadas}")
    print(f"  Chamadas Recusadas:   {total_recusadas}")
    
    # Agentes
    resp_agentes = collector.coletar_agentes(data_teste)
    agentes = collector.extrair_dados_agentes(resp_agentes)
    print(f"\n  Agentes online ({len(agentes)}):")
    for a in agentes:
        print(f"    {a['agente']:<40} Chamadas: {a['chamadas']}")
    
    # Agressividade
    agressividade = collector.coletar_agressividade(fila_teste)
    print(f"\n  Agressividade: {agressividade}")
    
    print(f"\n{'=' * 60}")
    print(f"DIAGNÓSTICO CONCLUÍDO COM SUCESSO")
    print(f"{'=' * 60}")
