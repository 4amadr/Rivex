import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv


class VonixSip:
    
    @staticmethod
    def headers_config(url_headers):
        # função para configurar os headers. São usados muitas vezes
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': url_headers,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        return headers
    
    @staticmethod
    def get_page(url_page, session=None):  # recebe session
        '''Função para coletar o token'''
        
        if session is None:  # se não tem session, cria uma nova
            session = requests.Session()
        
        vs = VonixSip
        headers = vs.headers_config(url_page)
        
        get_new_page = session.get(url_page, headers=headers)
        soup_page = BeautifulSoup(get_new_page.text, 'html.parser')
        
        token_page = soup_page.find('input', {'name': 'authenticity_token'})['value']
        
        return token_page, session  #retorna a session
    
    def login_vonix(username, password):
        '''login in vonix with requests'''
    
        url_login = 'http://contech6.vonixcc.com.br/login/signin'
        
        
        vs = VonixSip
        headers = vs.headers_config(url_login)
        token_login, session = vs.get_page(url_login)
        
        
        payload_login = {
            'authenticity_token': token_login,
            'return_to': '',
            'username': username,
            'password': password,
            'commit': 'Entrar'
        }
        
        login = session.post(url_login, data=payload_login, headers=headers)
        
        if login.status_code != 200:
            print(f'Erro {login.status_code} ao logar no vonix')
        else:
            print('Logado no vonix!')
            return session
    
    def filter_data(session, queue_client):
        '''Função para filtrar os dados antes de realizar a coleta
        se essa função não for executada a automação vai coletar os dados de todas as equipes juntas'''
        vs = VonixSip
        
        url_filter = 'http://contech6.vonixcc.com.br/login/set_show_queue'
        
        headers = vs.headers_config(url_filter)
        token_filter, session = vs.get_page(url_filter, session)
        
        payload_filter = {
            'authenticity_token': token_filter,
            'return_to': '/overview',
            'queue_id[]': queue_client
        }
        
        
        filter = session.post(url_filter, data=payload_filter, headers=headers)
        
        if filter.status_code != 200:
            print(f'erro: {filter.status_code} na filtragem de dados no vonix')
        else:
            print(f'filtro aplicado. Equipe: {queue_client}')
            return filter
    
    def get_calls(session, date):
        # função para coletar o HTML da página que contém os dados de chamadas
        vs = VonixSip
        
        calls_url = 'http://contech6.vonixcc.com.br/overview'
        
        token_calls, session = vs.get_page(calls_url, session)
        
        payload = {
            'base_date': date,
            'set-cookie': token_calls
        }
        
        
        headers = vs.headers_config(calls_url)
        
        data = session.get(calls_url, params=payload, headers=headers)
        
        if data.status_code != 200:
            print(f'erro {data.status_code} tentando coletar dados no vonix.')
            return False
        else:
            print('Dados coletados no vonix')
            return data
        
    def get_agents(session, data):
        # função para coletar a quantidade de agentes que realizaram ligações em um dia
        url_agents = 'http://contech6.vonixcc.com.br/agents/calls_overview'
        vs = VonixSip
        
        page, session = vs.get_page(url_agents, session)
        
        headers = vs.headers_config(url_agents)
        
        payload_agentes = {
            'interval[select]': 'custom',
            'interval[start_date]': data,
            'interval[end_date]': data,
        }
        
        agents = session.get(url_agents, data=payload_agentes, headers=headers)
        
        if agents.status_code != 200:
            print(f'Erro: {agents.status_code} tentando coletar agentes no vonix')
        else:
            print('quantidade de agentes colectados do vonix')
            return agents
    
    def get_agressividade(session, cliente):
        # pegar agressividade
        vs = VonixSip
        url_agressividade_sem_token = f'http://contech6.vonixcc.com.br/admin/queue_edit/{cliente}?'

        
        token, session = vs.get_page(url_agressividade_sem_token, session)
        
        
        url_agressividade = f'http://contech6.vonixcc.com.br/admin/queue_edit/{cliente}?authenticity_token={token}'


        payload = {
            'authenticity_token': token
        }

        headers = vs.headers_config(url_agressividade)

        agressividade = session.get(url_agressividade, data=payload, headers=headers)

        if agressividade.status_code != 200:
            print(f'erro na coleta de agressividade {agressividade.status_code}')
        else:
            print('agressividade coletada no vonix')
            return agressividade
    
    def execucao_geral(equipes):
        username = 'victor'
        password = '1801'
        date = '19/02/2026'
        vs = VonixSip
        login = vs.login_vonix(username, password)
        filter = vs.filter_data(login, equipes)
        all_calls = vs.get_calls(login, date)
        agents = vs.get_agents(login, date)
        agressividade =  vs.get_agressividade(login, equipes)
        return all_calls, agents, agressividade
    
'''vs = VonixSip
equipes = ['tcrepresentacao', 'tcrepresentacao01', 'tcrepresentacao02', 'tcrepresentacao03', 'tcrepresentacao04']
for equipe in equipes:
    all_calls, agents, agressividade = vs.execucao_geral(equipe)'''