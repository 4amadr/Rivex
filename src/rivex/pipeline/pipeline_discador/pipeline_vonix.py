from src.rivex.enviroments.discadores.vonix.fluxo_coleta import *
from src.rivex.enviroments.discadores.vonix.fluxo_limpeza import *
from src.rivex.data_processing.Vonix.cleaning_vonix import *
import os
from dotenv import load_dotenv
import time

class PipelineVonix:
    def __init__(self):
        load_dotenv()
        self.data = DateConfig()
        self.login = os.getenv('LOGIN_VONIX')
        self.senha = os.getenv('SENHA_VONIX')
        self.url = os.getenv('URL_BASE_VONIX6')
        self.vonix_execucao = ExecucaoVonix(
            login=self.login,
            senha=self.senha,
            data=self.data.data_selecionadas(),
            url_base=self.url
        )

    def inicial_config(self):
        token_encontrado = self.vonix_execucao.token_pronto()
        return gerar_lista_de_clientes(html=self.vonix_execucao.get_clientes(token_encontrado)), token_encontrado
    
    def get_dados_sujos(self, cliente, token):
        return {
            "Totais": self.vonix_execucao.get_chamadas(),
            "Aceitas": self.vonix_execucao.get_chamadas("completed"),
            "Abandonadas": self.vonix_execucao.get_chamadas("abandon"),
            "Recusadas": self.vonix_execucao.get_chamadas("discard"),
            "Agentes": self.vonix_execucao.get_agentes(),
            "config": self.vonix_execucao.coleta_de_agressividade_vonix(cliente, token)
        }
    
    def execucao_limpeza_chamadas_vonix(self, totais, aceitas, abandonadas, recusadas, config):
        chamadas_totais = limpar_chamadas(totais.text)
        chamadas_aceitas = limpar_chamadas(aceitas.text)
        chamadas_abandonadas = limpar_chamadas(abandonadas.text)
        chamadas_recusadas = limpar_chamadas(recusadas.text)
        agressividade = get_agressividade(config.text)
        tech = get_tech(config.text)
        return {
            "Tech": tech,
            "Data": self.data,
            "chamadas": chamadas_totais,
            "aceitas": chamadas_aceitas,
            "recusadas": chamadas_recusadas,
            "abandonadas": chamadas_abandonadas,
            "agressividade": agressividade
        }
        
    def execucao_limpeza_agentes_vonix(self, agentes):
        tabela = dict_agentes(agentes.text)
        print(tabela)
        return tabela
        
        

    def execucao_vonix(self):
        lista_clientes, token = self.inicial_config()
        for cliente in lista_clientes:
            response_dict = self.get_dados_sujos(cliente, token)
            aceitas = self.execucao_limpeza_chamadas_vonix(response_dict["Totais"], 
                                  response_dict["Aceitas"],
                                  response_dict["Abandonadas"],
                                  response_dict["Recusadas"],
                                  response_dict["config"],
            )
            tabela = self.execucao_limpeza_agentes_vonix(response_dict["Agentes"])
            time.sleep(4)

        
