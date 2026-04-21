import requests
from dotenv import load_dotenv
from src.rivex.utils.requests_utils.requests import HttpRequisitions
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

    def gerar_url(self):
        url_base = self.url
        url_login = f'{url_base}/painel/index.php'
        url_filtragem = f'{url_base}/painel/relatorio_minutos_revenda.php'
        url_get_id = f'{url_base}/painel/cliente_lista.php?cliente=&email=&cpf=&cnpj=&action=Filtrar'
        url_chamadas_tarifadas = f'{url_base}/painel/call_history.php?retorno=listacliente&v='
        url_lista_de_clientes = f'{url_base}/painel/cliente_lista.php'
        url_id_do_cliente = f'{url_base}/painel/buscaDadosClientecomId.php'


        return url_login, url_filtragem, url_get_id, url_chamadas_tarifadas, url_lista_de_clientes, url_id_do_cliente


    def login(self, url_de_login):
        print(f'login: {self.operadora}')
        print(f'url: {url_de_login}')


        payload = {
            'login': self.usuario,
            'senha': self.password,
            'Submit': "Entrar"
        }

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
        }

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        login = self.hr.requisicao_post_com_certificado(payload_post=payload,
                                        headers=headers,
                                        url=url_de_login,
                                        verificacao=False
                                        )
        return login

    def filtrar_dados(self):
        url = f'{self.url}/painel/relatorio_minutos_revenda.php'
        payload = {
            'filtro': 1, # seleção personalizada
            'periodopre': 0,
            'data_inicio': self.data, # formato AAAA-MM-DD
            'horario_inicio': 00,
            'data_fim': self.data, # formato AAAA-MM-DD
            'horario_fim': 23,
            'cliente_filtro': '',
            'tipochamadas': 'todas',
            'action': 'Filtrar'
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
        }
        filtro = self.hr.requisicao_post_com_certificado(payload_post=payload,
                                         headers=headers,
                                         url=url,
                                        verificacao=False)
        return filtro

    def get_id_do_cliente(self, url_id_do_cliente):
        '''Retornar a lista de ids dos clientes presentes na operadora'''
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
        }

        payload = {
            'nome_cliente ': ""
        }

        id_do_cliente = self.hr.requisicao_post_com_certificado(url=url_id_do_cliente,
                                                                payload_post=payload,
                                                                headers=headers,
                                                                verificacao=False)
        return id_do_cliente

    def get_chamadas_tarifadas(self, data, url_chamadas_tarifadas, id_cliente):
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
        }

        payload = {
            'customer_id': f'{id_cliente}',
            'startDate': f'{data}',
            'finalDate': f'{data}',
            'sipcode': 200,
            'tipo_exibicao': 'tela',
            'checkbox_columns': '1',
            'exibir_totais': '1',
            'action': 'buscar'
        }

        chamadas_tarifadas = self.hr.requisicao_get_com_verificado(headers=headers,
                                                                   payload_get=payload,
                                                                   url=url_chamadas_tarifadas,
                                                                   verificacao=False)
        return chamadas_tarifadas

    def execucao_pipeline_sip(self):
        url_de_login, url_filtragem, url_get_id, url_chamadas_tarifadas, url_a_toa, url_id_do_cliente = self.gerar_url()
        login_sip = self.login(url_de_login=url_de_login)
        custo_minutagem = self.filtrar_dados()
        id_clientes = self.get_id_do_cliente(url_id_do_cliente)
        print(id_clientes.json())
        return custo_minutagem, id_clientes
        
sc = SipClient(usuario='fbm.revenda',
               password='Bill23ADM$',
               url='https://sip3.solutionsvoip.com.br',
               operadora='Gsolutions',
               data='2026-04-15')

custo_minutagem = sc.execucao_pipeline_sip()


