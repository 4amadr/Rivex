from src.rivex.utils.logging_config.logging_config import *

class ErroHttpDiscador:
    def __init__(self) -> None:
        self.log = LoggingConfig('Req', 'HTTP', 0)
        pass


    def acesso_restrito(self, status_code, url):
        if status_code in(401, 403):
            self.log.log_erro(url, '[REQ]', 'Acesso restrito, verifique o token de acesso')

    def erro_cliente(self, status_code, url):
        if status_code in(400, 404, 422):
            self.log.log_erro(url, '[REQ]', 'Erro de envio de dados')

    def req_bloqueada(self, status_code):
        if status_code == 429:
            self.log.log_info('[REQ]', 'Servidor bloqueado por excesso de requisições. Realizando retry...')

    def erro_servidor(self, status_code, url):
        if status_code in(500, 502, 503, 504):
            self.log.log_erro(url, '[REQ]', 'Erro de servidor, Realizando Retry...')

    def analisar_erros(self, status_code: int, url: str):
        self.acesso_restrito(status_code, url)
        self.erro_cliente(status_code, url)
        self.req_bloqueada(status_code)
        self.erro_servidor(status_code, url)
    
            