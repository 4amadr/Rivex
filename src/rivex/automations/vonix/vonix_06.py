import requests
from br4 import BeautifulSoup


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
    
    def login_vonix(username, password, token, headers, queue_client: dict):
        '''login in vonix with requests'''
    
        url_login = 'http://contech6.vonixcc.com.br/login/signin'
        
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
    
    def filter_data(client):
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
    
    def get_calls():
        '''function to get the calls from vonix'''

        calls_url = 'http://contech6.vonixcc.com.br/overview'
        
        headers = headers_config(calls_url)
        
        data = session.get(calls_url, headers=headers)
        
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
        
        agents = session.get(url_agents, headers=headers)
        
        if agents.status_code != 200:
            print(f'Error: {agents.status_code} trying to get agent data from vonix')
        else:
            print('agents data colected from vonix')
            return agents