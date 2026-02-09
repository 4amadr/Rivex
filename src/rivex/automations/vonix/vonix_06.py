import requests
from br4 import BeautifulSoup
from dotenv import load_dotenv


class VonixSip:
    
    def headers_config(url_headers):
        '''function to config headers'''
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': url_headers
        }
        return headers
    
    def get_page(url_page):
        '''function to get url and create the access'''
        session = requests.Session()
        
        headers = headers_config(url_page)
        
        get_new_page = session.get(url_page, headers=headers)
        soup_page = BeautifulSoup(get_new_page.text, 'html.parser')
        
        token_page = soup_page.find('input', {'name': 'authenticity_token'})['value']
        if token_page:
            return token_page
        else:
            print('no token')
            return False
    
    def login_vonix(username, password):
        '''login in vonix with requests'''
    
        url_login = 'http://contech6.vonixcc.com.br/login/signin'
        
        token = get_page(url_login)
        
        headers = headers_config(url_login)
        
        payload_login = {
            'authenticity_token': token,
            'return_to': '',
            'username': username,
            'password': password,
            'commit': 'Entrar'
        }
        
        headers = headers_config(url_login)
        
        session.headers.uptate(headers)
        
        login = session.post(url_login, data=payload_login)
        
        if login.status_code != 200:
            print(f'Error {login.status_code} in vonix login')
        else:
            print('login completed in vonix')
            return session
    
    def filter_data(queue_client: dict):
        '''function to filter the data'''
    
        url_filter = 'http://contech6.vonixcc.com.br/login/set_show_queue'
        
        headers = headers_config(url_filter)
        
        token = get_page(url_filter)
        
        payload_filter = {
            'authenticity_token': token,
            'return_to': '/overview',
            'queue_id[]': queue_client['tean']
        }
        
        filter = session.post(url_filter, data=payload_filter, headers=headers)
        
        if filter.status_code != 200:
            print(f'error: {filter.status_code} in the vonix filter')
        else:
            print('filter in vonix aplied')
            return filter
    
    def get_calls(date):
        '''function to get the calls from vonix'''

        calls_url = 'http://contech6.vonixcc.com.br/overview'
        
        payload = {
            'base_date': date
        }
        
        headers = headers_config(calls_url)
        
        data = session.get(calls_url, data=payload, headers=headers)
        
        if data.status_code != 200:
            print(f'error{data.status_code} trying to get data from vonix.')
            return False
        else:
            print('Data colected from vonix')
            return data
        
    def get_agents():
        '''function to get agents'''
        url_agents = 'http://contech6.vonixcc.com.br/agents/calls_overview'
        
        headers = headers_config(url_agents)
        
        payload_agentes = {
            'interval[select]': 'custom',
            'interval[start_date]': data,
            'interval[end_date]': data,
        }
        
        agents = session.get(url_agents, data=payload_agentes, headers=headers)
        
        if agents.status_code != 200:
            print(f'Error: {agents.status_code} trying to get agent data from vonix')
        else:
            print('agents data colected from vonix')
            return agents
    
    def get_agressividade(cliente):
        # pegar agressividade
        token = get_page(url_agressividade)
        
        url_agressividade = f'http://contech6.vonixcc.com.br/admin/queue_edit/{cliente}?authenticity_token={token}'

        payload = {
            'authenticity_token': token
        }

        headers = headers_config(url_agressividade)

        agressividade = session.get(url_agressividade, data=payload, headers=headers)

        if agressividade.status_code != 200:
            print(f'erro na coleta de agressividade {agressividade.status_code}')
        else:
            print('agressividade coletada no vonix')
            return agressividade
    
    def execucao_geral():
        session = login_vonix(username, password)
        filter = filter_data(queue_client['tean'])
        all_calls = get_calls(date)
        agents = get_agents()
        agressividade = get_agressividade()
        
        return all_calls, agents, agressividade
        