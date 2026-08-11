from src.rivex.enviroments.discadores.vonix.fluxo_coleta import *
from src.rivex.enviroments.discadores.vonix.fluxo_limpeza import *
from src.rivex.data_processing.Vonix.cleaning_vonix import *
from src.rivex.database.database import DatabaseVonix
import os
import logging
from dotenv import load_dotenv
import time

class PipelineVonix:
    def __init__(self):
        load_dotenv()
        self.data = DateConfig()
        self.login = os.getenv('LOGIN_VONIX')
        self.senha = os.getenv('SENHA_VONIX')
        self.url = os.getenv('URL_BASE_VONIX6')
        self.tempo_espera = os.getenv('TEMPO_VONIX')
        self.vonix_execucao = ExecucaoVonix(
            login=self.login,
            senha=self.senha,
            data=self.data.data_selecionadas(),
            url_base=self.url
        )
        self.db = DatabaseVonix()

    def inicial_config(self):
        token_encontrado = self.vonix_execucao.token_pronto()
        return gerar_lista_de_clientes(html=self.vonix_execucao.get_clientes(token_encontrado)), token_encontrado
    
    def get_dados_sujos(self, cliente, token):
        self.vonix_execucao.get_filtragem(cliente, token)
        return {
            "Totais": self.vonix_execucao.get_chamadas(),
            "Aceitas": self.vonix_execucao.get_chamadas("completed"),
            "Abandonadas": self.vonix_execucao.get_chamadas("abandon"),
            "Recusadas": self.vonix_execucao.get_chamadas("discard"),
            "Agentes": self.vonix_execucao.get_agentes(),
            "config": self.vonix_execucao.coleta_de_agressividade_vonix(cliente, token),
            "Tech": self.vonix_execucao.get_techs()
        }
    
    def execucao_limpeza_chamadas_vonix(self, cliente, totais, aceitas, abandonadas, recusadas, config, tech):
        chamadas_totais = limpar_chamadas(totais.text)
        chamadas_aceitas = limpar_chamadas(aceitas.text)
        chamadas_abandonadas = limpar_chamadas(abandonadas.text)
        chamadas_recusadas = limpar_chamadas(recusadas.text)
        agressividade = get_agressividade(config.text)
        lista_techs = get_lista_techs(tech.text)
        """
        Lista de techs tem o nome um pouco diferente
        precisa criar uma função para tratar, comparar e se o nome do cliente
        for igual ao dict vai retornar a tech daquele dado
        """
        tech = get_tech_vez(lista_techs, cliente)

        dados_cliente = {
            "tech": tech,
            "data": self.data.data_selecionadas(),
            "cliente": cliente,
            "chamadas": chamadas_totais,
            "completas": chamadas_aceitas,
            "recusadas": chamadas_recusadas,
            "abandonadas": chamadas_abandonadas,
            "agressividade": agressividade
        }

        print(dados_cliente)
        return dados_cliente
        
    def execucao_limpeza_agentes_vonix(self, cliente, agentes, tech, data):
        return dict_agentes(agentes.text, tech, cliente, data)        

    def execucao_vonix(self):
        lista_clientes, token = self.inicial_config()
        clientes_validos = [
        cliente
        for cliente in lista_clientes
        if "itelink" not in cliente.lower()
        and not cliente.lower().endswith("manual")
        ]
        logging.info(f"Clientes ativos e válidos (Sem filas manuais): {clientes_validos}")

        for cliente_selecionado in clientes_validos:


            response_dict = self.get_dados_sujos(cliente_selecionado, token)

            print(f"Cliente atual: {cliente_selecionado}")


            cliente = self.execucao_limpeza_chamadas_vonix(cliente_selecionado, response_dict["Totais"], 
                                  response_dict["Aceitas"],
                                  response_dict["Abandonadas"],
                                  response_dict["Recusadas"],
                                  response_dict["config"],
                                  response_dict["Tech"]
            )

            agentes = self.execucao_limpeza_agentes_vonix(cliente["cliente"], response_dict["Agentes"], cliente["tech"], cliente["data"])
            
            print(f"Dados dos clientes: {cliente}")
            print(f"Dados dos agentes: {agentes}")
            self.db.db_vonix(cliente, agentes)
            time.sleep(self.tempo_espera)
        self.db.fechar_db_vonix()

        
