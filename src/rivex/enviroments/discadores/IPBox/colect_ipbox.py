from src.rivex.utils.requests_utils.requests import HttpRequisitions
from src.rivex.enviroments.discadores.IPBox.payloads_ipbox import *
from src.rivex.data_processing.IPBox.limpeza_ipbox import *
import requests

class IpboxInit:
    def __init__(self, url, login, senha, data):
        self.url = url
        self.login = login
        self.senha = senha
        self.data = data
        self.hr = HttpRequisitions(session=requests.session())
        
    def gerar_url(self):
        url_login = f'{self.url}/contech/autenticacao.php'
        url_relatorio_chamadas = f'{self.url}/contech/viewRelatTelefoniaAtivo.php'

        return url_login, url_relatorio_chamadas
        
    def login_ipbox(self, url_login):
        login = self.hr.requisicao_post(payload_post=payload_login_ipbox(self.login, self.senha),
                                        headers=headers_ipbox(),
                                        url=url_login)
        print('Login finalizado', login.status_code)
        print("Credenciais usadas: ", url_login, payload_login_ipbox(self.login, self.senha))
        
        return self.hr.session
    
    def get_clientes(self):
        '''Requisição para coletar os clientes presentes no discador'''
        url_get_clientes = f'{self.url}/contech/listFila.php'
        print('Coletando clientes')
        cliente_ipbox = self.hr.requisicao_get(payload_get=payload_get_clientes,
                                            headers=headers_ipbox(),
                                            url=url_get_clientes)
        print('Clientes coletados')
        id_clientes = filtragem_lista(cliente_ipbox) # FUNÇÃO RETORNANDO OS IDS ERRADOS !!!!
        print('Clientes coletados e limpos em uma lista de dicionários')
        return id_clientes
    
    def execucao_base_ipbox(self):
        url_login, url_relatorio_chamadas = self.gerar_url()
        login = self.login_ipbox(url_login)
        cliente_ipbox = self.get_clientes()
        print('Base ipbox finalizada')
        return login, cliente_ipbox


class IpboxClientConfig:

    def __init__(self, url, login, senha, data, id_cliente, nome_cliente, sessao_anterior, token):
        self.url = url
        self.login = login
        self.senha = senha
        self.data = data
        self.id_cliente = id_cliente # para não ter a necessidade de repetir o login
        self.nome_cliente = nome_cliente # nome do cliente para buscar os valores
        self.session = sessao_anterior
        self.hr = HttpRequisitions(session=requests.session())
        self.token = token

    def gerador_de_url_configs(self):
        url_agressividade = f'{self.url}/contech/editFila.php?act=alter&obj_fila_id={self.id_cliente}'
        url_relatorio_chamadas = f'{self.url}ipbox/api/getTA1'
        url_relatorio_agentes = f'{self.url}ipbox/api/getPA1'

        return url_agressividade, url_relatorio_chamadas, url_relatorio_agentes

    def get_agressividade(self, url_agressividade):
        '''
        Vai ser executado em loop de iteração para retornar um cliente de cada vez
        o retorno esperado é o HTML da página de configuração de clientes onde o valor desejado
        é o valor de overdial
        '''
        agressividade = self.hr.requisicao_get(headers=headers_ipbox(),
                                               url=url_agressividade,
                                               payload_get={}) # ID corrigido, o erro 404 é outro
        print("Cliente buscado", self.nome_cliente)
        print("ID usado na verificação", self.id_cliente)
        print("url usada na agressividade", url_agressividade)
        print("Histórico: ", agressividade.history)
        print("Resposta da agressividade", agressividade.status_code)
        return agressividade

    def get_relatorio_chamadas(self, url_relatorio_chamadas): # coleta feita com API disponibilizada na documentação do ambiente
        chamadas = self.hr.requisicao_get(headers=headers_api_telefonia(self.token),
                                          payload_get=payload_api_telefonia(self.data, self.nome_cliente),
                                          url=url_relatorio_chamadas)

        print("RESPOSTA DAS CHAMADAS: ",chamadas.status_code)
        return chamadas

    def get_relatorio_agente(self, url_relatorio_agentes):
        agentes = self.hr.requisicao_get(headers=headers_api_telefonia(self.token),
                                         payload_get=payload_api_agentes(self.data),
                                         url=url_relatorio_agentes)
        print("RESPOSTA DAS AGENTE: ",agentes.status_code)
        return agentes

    def execucao_ipbox(self):
        url_agressividade, url_relatorio_chamadas, url_relatorio_agentes = self.gerador_de_url_configs()
        agressividade = self.get_agressividade(url_agressividade)
        chamadas = self.get_relatorio_chamadas(url_relatorio_chamadas)
        agentes = self.get_relatorio_agente(url_relatorio_agentes)

        return agressividade.text, chamadas.text, agentes.text

