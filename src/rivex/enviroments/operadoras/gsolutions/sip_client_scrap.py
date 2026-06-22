import requests
from dotenv import load_dotenv
from src.rivex.utils.requests_utils.requests import HttpRequisitions
from src.rivex.enviroments.operadoras.gsolutions.headers_payload import *
import urllib3

load_dotenv()
class SipClient:
    def __init__(self, usuario, password, url, operadora, data):
        self.usuario = usuario
        self.password = password
        self.url = url
        self.hr = HttpRequisitions(session=requests.Session())
        self.operadora = operadora
        self.data = data

    def gerar_url(self, ):
        url_base = self.url
        url_login = f"{url_base}/painel/index.php"
        url_filtragem = f"{url_base}/painel/relatorio_minutos_revenda.php"
        url_get_id = f"{url_base}/painel/cliente_lista.php?cliente=&email=&cpf=&cnpj=&action=Filtrar"
        url_chamadas_tarifadas = f"{url_base}/painel/call_history.php?retorno=listacliente&v="
        url_lista_de_clientes = f"{url_base}/painel/cliente_lista.php"
        url_id_do_cliente = f"{url_base}/painel/buscaDadosClientecomId.php"

        return (
            url_login,
            url_filtragem,
            url_get_id,
            url_chamadas_tarifadas,
            url_lista_de_clientes,
            url_id_do_cliente,
        )

    def login(self, url_de_login):
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        login = self.hr.requisicao_post_com_certificado(payload_post=payload_de_login(self.usuario, self.password),
                                        headers=header_geral(),
                                        url=url_de_login,
                                        verificacao=False
                                        )
        return login

    def filtrar_dados(self, url_filtragem):

        filtro = self.hr.requisicao_post_com_certificado(payload_post=payload_filtragem_custos(self.data),
                                         headers=header_geral(),
                                         url=url_filtragem,
                                        verificacao=False)
        return filtro

    def get_id_do_cliente(self, url_id_do_cliente):
        '''Retornar a lista de ids dos clientes presentes na operadora'''

        id_do_cliente = self.hr.requisicao_post_com_certificado(url=url_id_do_cliente,
                                                                payload_post=payload_get_id_cliente(),
                                                                headers=header_geral(),
                                                                verificacao=False)
        return id_do_cliente

    def execucao_pipeline_sip(self):
        url_de_login, url_filtragem, url_get_id,url_chamadas_tarifadas, url_a_toa, url_id_do_cliente = self.gerar_url()
        self.login(url_de_login=url_de_login)
        consumo = self.filtrar_dados(url_filtragem)
        id_clientes = self.get_id_do_cliente(url_id_do_cliente)
        return consumo, id_clientes

class SipCharged:
    def __init__(self, data, url_base, usuario, password):
        self.data = data
        self.url_base = url_base
        self.url_login = f'{url_base}/painel/index.php'
        self.url_tarifadas = f'{url_base}/painel/call_history.php'
        self.hr = HttpRequisitions(session=requests.Session())
        self.usuario = usuario
        self.password = password
        
        
    def login(self):
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        return self.hr.requisicao_post_com_certificado(payload_post=payload_de_login(self.usuario, self.password),
                                        headers=header_geral(),
                                        url=self.url_login,
                                        verificacao=False
                                        )
    
    def clientes_online(self, cliente_online: list, id_clients: dict):
        '''
        Função para verificar os clientes que tiveram consumo na operadora
        ela vai comparar os dados gerais com os nomes dos clientes online e retornar
        uma lista com os ids dos clientes que tiveram consumo
        OBS: cliente_online é uma lista de dicionários e id_clientes é um dicionário
        '''
        lista_ids_online = []
        for cliente in cliente_online:
                lista_ids_online.append(cliente["id"])
        return lista_ids_online
        
        
    def get_chamadas_tarifadas(self, id_cliente):
        return self.hr.requisicao_get_com_verificado(headers=header_geral(),
                                                                        payload_get=payload_chamadas_tarifadas(id_cliente, self.data),
                                                                        url=self.url_tarifadas,
                                                                        verificacao=False)   
    
    
    def lista_chamadas_tarifadas(self, cliente_online, id_cliente: dict):
        self.login()
        lista_ids_online = self.clientes_online(cliente_online, id_cliente)
        return [self.get_chamadas_tarifadas(identificador) for identificador in lista_ids_online]
        