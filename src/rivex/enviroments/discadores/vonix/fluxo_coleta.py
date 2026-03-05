import os
import requests
from dotenv import load_dotenv
from src.rivex.utils.infra_utils.date_config import DateConfig
from src.rivex.utils.requests_utils.requests import HttpRequisitions
from src.rivex.enviroments.discadores.vonix.payloads_vonix import PayloadsVonix
from src.rivex.enviroments.discadores.vonix.equipes_vonix import dict_agentes
from src.rivex.utils.infra_utils.vonix_processing import ClientSimulator

'''Classe feita para executar cada etapa do discador vonix contando com
Login + TOKEN -> Filtragem + TOKEN -> Chamadas + TOKEN -> Agentes online + TOKEN -> Agressividade + TOKEN'''

class ExecucaoVonix:


    load_dotenv()
    
    def execucao_login_vonix(self, url_base):
        # função responsável por todo processo de login no discador
        session = requests.Session()
        hr = HttpRequisitions(session=session)
        cs = ClientSimulator(session)
        pv = PayloadsVonix()

        url_login = f'{url_base}/login/signin'
        user_vonix = os.getenv('LOGIN_VONIX')
        password_vonix = os.getenv('PASSWORD_VONIX')
        
        # processo de coletar o token para acessar o ambiente
        headers_login, html_login, token_login = cs.gerador_de_requisitos(url_login)
        payload_postagem_login = pv.payload_de_login(user_vonix, password_vonix, token_login)


        # login
        login = hr.requisicao_post(payload_postagem_login, headers_login, url_login)
        return session
    
    def execucao_filtragem_vonix(self, url_base, equipe, session):
        # função que executa todo o processo de filtragem do vonix
        url_filtro = f'{url_base}/login/set_show_queue'
        hr = HttpRequisitions(session=session)
        cs = ClientSimulator(session)
        pv = PayloadsVonix()

        headers_filtragem, html_filtragem, token_filtragem = cs.gerador_de_requisitos(url_filtro)

        filtragem = hr.requisicao_post(pv.payload_de_filtragem(token_filtragem, equipe), headers_filtragem, url_filtro)
        print(f'Equipe filtrada {equipe}')
        return filtragem, equipe

    def nova_coleta_chamadas_voix(self, data, url_base, session, tipo_chamada: str | None = None):
        # coletar as chamadas feitas por uma equipe

        if tipo_chamada is None:
            tipo_chamada = ''

        url_chamadas = f'{url_base}/calls'

        hr = HttpRequisitions(session=session)
        cs = ClientSimulator(session)
        pv = PayloadsVonix()

        headers_chamadas, html_chamadas, token_chamadas = cs.gerador_de_requisitos(url_chamadas)
        payload_para_chamadas = pv.payload_de_chamadas(data, tipo_de_chamada=tipo_chamada)
        
        chamadas = hr.requisicao_get(payload_get=payload_para_chamadas, headers=headers_chamadas, url=url_chamadas)
        print(payload_para_chamadas)
        return chamadas.text

    
    def coleta_de_chamadas_vonix(self, data, url_base, session):
        # função para coletar todas as chamadas feitas por uma equipe
        
        url_chamadas = f'{url_base}/overview'

        

        hr = HttpRequisitions(session=session)
        cs = ClientSimulator(session)
        pv = PayloadsVonix()

        headers_chamadas, html_chamadas, token_chamadas = cs.gerador_de_requisitos(url_chamadas)
        payload_para_chamadas = pv.payload_de_chamadas(data, token_chamadas)
        
        chamadas = hr.requisicao_get(payload_get=payload_para_chamadas, headers=headers_chamadas, url=url_chamadas)
        return chamadas
    
    def coleta_de_agentes_vonix(self, data, url_base, session):
        # função para coletar dados de agentes feitas por uma equipe
        url_agentes = f'{url_base}/agents/calls_overview'

        hr = HttpRequisitions(session=session)
        cs = ClientSimulator(session)
        pv = PayloadsVonix()

        headers_agentes, html_agentes, token_agentes = cs.gerador_de_requisitos(url_agentes)
        parload_para_agentes = pv.payload_de_agentes(data)
        
        agentes = hr.requisicao_get(parload_para_agentes, headers_agentes, url_agentes)
        return agentes
    
    def coleta_de_agressividade_vonix(self, cliente, url_base, session):
        # função para coletar informações de agressividade por equipe
        url_agressividade = f'{url_base}/admin/queue_edit/{cliente}'
        
        hr = HttpRequisitions(session=session)
        cs = ClientSimulator(session)
        pv = PayloadsVonix()

        headers_agressividade, html_agressividade, token_agressividade = cs.gerador_de_requisitos(url_agressividade)
        payload_para_agressividade = pv.payload_de_agressividade(token_agressividade)
        
        agressividade = hr.requisicao_get(payload_para_agressividade, headers_agressividade, url_agressividade)
        return agressividade

    def execucao_vonix(self, data, url, equipe):
        session = self.execucao_login_vonix(url)

        filtragem = self.execucao_filtragem_vonix(url, equipe, session)

        # tipos de chamadas
        totais = ''
        completas = 'completed'
        abandonadas = 'abandon'
        descartadas = 'discard'

        # HTML de chamadas
        chamadas_totais = self.nova_coleta_chamadas_voix(data, url, session, totais)
        chamadas_completas = self.nova_coleta_chamadas_voix(data, url, session, completas)
        chamadas_abandonadas = self.nova_coleta_chamadas_voix(data, url, session, abandonadas)
        chamadas_recusadas = self.nova_coleta_chamadas_voix(data, url, session, descartadas)


        agentes = self.coleta_de_agentes_vonix(data, url, session)
        agressividade = self.coleta_de_agressividade_vonix(equipe, url, session)

        return chamadas_totais, chamadas_completas, chamadas_recusadas, chamadas_abandonadas, agentes, agressividade
        

        
