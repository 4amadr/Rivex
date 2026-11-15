from src.rivex.environments.discadores.vonix.fluxo_coleta import ExecucaoVonix
from src.rivex.environments.discadores.vonix.fluxo_limpeza import LimpezaVonix
from src.rivex.data_processing.Vonix.cleaning_vonix import *
from src.rivex.database.database_vonix.database_vonix import DatabaseVonix
from src.rivex.utils.infra_utils.date_config import DateConfig
import os
import logging
from dotenv import load_dotenv
import time

logger = logging.getLogger(__name__)

formato = logging.Formatter(
    "%(asctime)s - %(levelname)s [%(filename)s:%(lineno)d] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

handler_vonix = logging.FileHandler(f"Log/vonix_log/vonix_dia_{DateConfig.data_selecionadas().replace("/", "-")}.log")
handler_vonix.setFormatter(formato)

logger.addHandler(handler_vonix)

logger.info("Iniciando configuração do servidor Vonix...")

class PipelineVonix:
    def __init__(self, usar_db: bool = True):
        load_dotenv()
        self.data = DateConfig()
        self.login = os.getenv('LOGIN_VONIX')
        self.senha = os.getenv('SENHA_VONIX')
        self.url = os.getenv('URL_BASE_VONIX6')
        self.tempo_espera = os.getenv('TEMPO_VONIX', '35')
        self.tempo_int = int(self.tempo_espera)
        self.vonix_execucao = ExecucaoVonix(
            login=self.login,
            senha=self.senha,
            data=self.data.data_selecionadas(),
            url_base=self.url
        )
        self.limpeza_vonix = LimpezaVonix()
        self.db = DatabaseVonix() if usar_db else None

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

        logger.info(f"Dados do cliente {dados_cliente["cliente"]}: \n{dados_cliente}")
        return dados_cliente
        
    def execucao_limpeza_agentes_vonix(self, cliente, agentes, tech, data):
        return dict_agentes(agentes.text, tech, cliente, data)

    def get_operadores_cliente_sujos(self, cliente, token):
        self.vonix_execucao.get_filtragem(cliente, token)
        return self.vonix_execucao.get_operadores_cliente(token)

    def execucao_limpeza_operadores_cliente(self, operadores_html, cliente=None):
        return self.limpeza_vonix.extrair_operadores_cliente(operadores_html, cliente=cliente)

    def execucao_teste_operadores_vonix(self, clientes_teste=None, limite=3):
        lista_clientes, token = self.inicial_config()
        if clientes_teste is not None:
            alvos = list(clientes_teste)
        else:
            alvos = [
                cliente
                for cliente in lista_clientes
                if "itelink" not in cliente.lower()
                and not cliente.lower().endswith("manual")
                and not cliente.lower().startswith("zz")
            ][:limite]

        resultados = {}
        for cliente_selecionado in alvos:
            logger.info(f"Coletando operadores via /admin/agent_list para o cliente: {cliente_selecionado}")
            resposta_operadores = self.get_operadores_cliente_sujos(cliente_selecionado, token)
            operadores_limpos = self.execucao_limpeza_operadores_cliente(
                resposta_operadores,
                cliente=cliente_selecionado
            )
            resultados[cliente_selecionado] = operadores_limpos
            logger.info(
                f"Operadores coletados para {cliente_selecionado} "
                f"(status={resposta_operadores.status_code}, total={len(operadores_limpos)}): {operadores_limpos}"
            )
        return resultados

    def execucao_vonix(self):
        lista_clientes, token = self.inicial_config()
        clientes_validos = [
        cliente
        for cliente in lista_clientes
        if "itelink" not in cliente.lower()
        and not cliente.lower().endswith("manual")
        ]

        for cliente_selecionado in clientes_validos:


            response_dict = self.get_dados_sujos(cliente_selecionado, token)

            logger.info(f"Iniciando a coleta do cliente: {cliente_selecionado}")


            cliente = self.execucao_limpeza_chamadas_vonix(cliente_selecionado, response_dict["Totais"], 
                                  response_dict["Aceitas"],
                                  response_dict["Abandonadas"],
                                  response_dict["Recusadas"],
                                  response_dict["config"],
                                  response_dict["Tech"]
            )

            agentes = self.execucao_limpeza_agentes_vonix(cliente["cliente"], response_dict["Agentes"], cliente["tech"], cliente["data"])
            
            print(f"Dados dos cliente {cliente["cliente"]} após a coleta e processamento de dados: {cliente}")
            logger.info(f"Dados dos agentes após coleta e processamento de dados: {agentes}")
            
            self.db.db_vonix(cliente, agentes)
            time.sleep(self.tempo_int)
        self.db.fechar_db_vonix()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s [%(filename)s:%(lineno)d] - %(message)s",
    )
    pipeline = PipelineVonix(usar_db=False)
    resultados = pipeline.execucao_teste_operadores_vonix(
        clientes_teste=["realpromotora", "tcrepresentacao03", "oneinvest"]
    )
    for cliente, operadores in resultados.items():
        print(f"\n=== Cliente: {cliente} | Operadores ativos: {len(operadores)} ===")
        for operador in operadores:
            print(operador)
