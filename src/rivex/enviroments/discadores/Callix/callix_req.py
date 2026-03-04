import requests

class CallixReq:
    def __init__(self, user, password, url, cliente, url_agentes, url_agressividade):
        self.user=user
        self.password=password
        self.url=url
        self.cliente=cliente
        self.url_agentes=url_agentes
        self.url_agressividade=url_agressividade
        
        
    def login_callix(self):
        '''Função para realizar o login no callix utilizando requests'''
        print(f'Tentando realizar o login em {self.cliente}')
        self.Session = requests.Session()

        credenciais = {
            'username': self.user,
            'password': self.password
        }

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"
        }

        response = self.Session.post(self.url, json=credenciais, headers=headers)
        if response.status_code != 200:
            raise RuntimeError(f'Erro no login: {response.status_code}')

        else:
            print(f'Logado com sucesso em {self.cliente}')

    def get_agentes(self):
        '''Função para coletar a quantidade de agentes e validar eles'''
        print(f'Começando a coletar os agentes online em {self.cliente}')

cr = CallixReq(
    user = "victor.amador",
    password = "123456789Aa@",
    url = 'https://qualitycontech.callix.com.br/api/v4/auth/session',
    cliente = 'Quality'
    
)

cr.login_callix()

        