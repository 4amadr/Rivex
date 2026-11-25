from dotenv import load_dotenv
import os

class UrlGetClients:
    def __init__(self):
        load_dotenv()

        self.url_contech = os.getenv('URL_CALLIX_GERAL')

        if not self.url_contech:
            raise RuntimeError("URL_CALLIX_GERAL não foi definida.")
    def url_login_servidor_contech(self):
        return f"{self.url_contech}/api/v4/auth/session"
    
    def url_get_clients(self):
        return f'{self.url_contech}/api/v4/tenants/sub-accounts'

    def url_sub_accounts_v1(self):
        return f'{self.url_contech}/api/v1/sub_accounts'
    
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

    def url_create_tokens(self, cliente):
        return f"https://{cliente}.callix.com.br/api/v4/entities/api-tokens"

    def url_info_produto(self, cliente):
        return f"https://{cliente}.callix.com.br/api/v4/user-context"

    def url_users_v1(cliente):
        return f'https://{cliente}.callix.com.br/api/v1/users'

    def url_sdk_user_session(cliente):
        return f'https://{cliente}.callix.com.br/sdk/v1/server/user-session'

    

    def url_agressividade(self, cliente, id_campanha):
        lista_de_urls_de_agressividade = []
        for campanha in id_campanha:
            url_agressividade = f'https://{cliente}.callix.com.br/api/v4/entities/campaigns/{campanha}'
            lista_de_urls_de_agressividade.append(url_agressividade)
        return  lista_de_urls_de_agressividade
            
