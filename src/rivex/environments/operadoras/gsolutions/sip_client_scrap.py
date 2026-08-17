import requests
from dotenv import load_dotenv
from src.rivex.utils.requests_utils.requests import HttpRequisitions
from src.rivex.environments.operadoras.gsolutions.headers_payload import *
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
        return consumo.text, id_clientes.text

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
    
        
     
    def get_chamadas_tarifadas(self, id_cliente):
        return self.hr.requisicao_get_com_verificado(headers=header_geral(),
                                                                        payload_get=payload_chamadas_tarifadas(id_cliente, self.data),
                                                                        url=self.url_tarifadas,
                                                                        verificacao=False)   
    
    
    def lista_chamadas_tarifadas(self, id_cliente):
        self.login()
        return [self.get_chamadas_tarifadas(identificador) for identificador in id_cliente]


class EmpacotamentoAgitel:
    def __init__(self, data_db, lista_tech, lista_clientes, lista_minutagem, lista_custo, lista_tarifadas):
        self.data = data_db
        self.techs = lista_tech
        self.clientes = lista_clientes
        self.operadoras="Agitel"
        self.minutagens = lista_minutagem
        self.custos = lista_custo
        self.chamadas_tarifadas = lista_tarifadas

    def preparar_dados(self):
        """
        Deve retornar uma lista de dicionários prontos para o banco de dados
        """
        lista_pronta = []
        tamanhos = [
            len(self.techs),
            len(self.clientes),
            len(self.minutagens),
            len(self.custos),
            len(self.chamadas_tarifadas)
        ]

        if len(set(tamanhos)) != 1:
            raise ValueError(f"Listas com tamanhos diferentes: {tamanhos}")
        for tech, cliente, minutagem, custo, tarifa in zip(self.techs, self.clientes, self.minutagens, self.custos, self.chamadas_tarifadas):
            print("GIRANDO LOOP")
            dict_pronto = {
                "tech": tech or -1,
                "cliente": cliente,
                "operadora": self.operadoras,
                "data": self.data,
                "custo": custo,
                "minutagem": minutagem,
                "chamadas_tarifadas": tarifa
            }
            lista_pronta.append(dict_pronto)
        print(lista_pronta)
        return lista_pronta