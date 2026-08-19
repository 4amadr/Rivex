from dotenv import load_dotenv
import os

class UrlGetClients:
    def __init__(self):
        self.url_contech = os.getenv('URL_CALLIX_GERAL')
        load_dotenv()
    
    def url_login_servidor_contech(self):
        return f"{self.url_contech}/api/v4/auth/session"
    
    def url_get_clients(self):
        return f'{self.url_contech}/api/v4/tenants/sub-accounts'
    
class UrlGetData:
    
    def login_cliente_header(self, cliente):
        return f'https://{cliente}contech.callix.com.br/login'
    
    def login_cliente(self, cliente):
        return f'https://{cliente}.callix.com.br/api/v4/auth/session'
    
    def url_tokens(self, cliente):
        return f'https://{cliente}.callix.com.br/api/v4/entities/api-tokens'

    def url_get_tech(self, cliente):
        return f"https://{cliente}.callix.com.br/api/v4/entities/outbound-routes"

    def teste_url_agressividade(self, cliente):
        return f"https://{cliente}.callix.com.br/campaign-report"

    def url_agressividade(self, cliente, id_campanha):
        lista_de_urls_de_agressividade = []
        for campanha in id_campanha:
            url_agressividade = f'https://{cliente}.callix.com.br/api/v4/entities/campaigns/{campanha}'
            lista_de_urls_de_agressividade.append(url_agressividade)
        return  lista_de_urls_de_agressividade
            
