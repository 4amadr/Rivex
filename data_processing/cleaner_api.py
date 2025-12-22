from src.automations.Callix.callix import CallixAPI
from src.automations.Callix.callix_token_db import CallixDB
from datetime import datetime, timedelta, date
import pandas as pd


class LimpezaCallixAPI:

    def chamadas_recusadas(self, recusadas_semi_bruto, abandonadas):
        '''Função para calcular o valor limpo das chamadas recusadas'''
        recusadas = max(recusadas_semi_bruto - abandonadas, 0)
        return recusadas

    def tratamento_chamadas(self, dados_chamadas):
        '''função para pegar o arquivo e filtrar apenas os dados que
        serão necessários'''
        chamadas = int(dados_chamadas.get("meta", {}).get("count", 0))
        return chamadas

    def agregar_dados(self, completas, recusadas):
        '''Função para obter o total de chamadas em um dia'''
        chamadas_totais = completas + recusadas
        return chamadas_totais


    def limpeza_performace_json(self, performace_suja):
        '''Função para limpar o arquivo .json pegando apenas os dados que importam
        nesse caso em especifico o ID do agente + quantas chamadas ele fez'''
        dados = performace_suja.get("data", [])
        chamadas_respondidas_lista = [
            item.get("attributes", {}).get("answered_count", 0)
            for item in dados
        ]
        return chamadas_respondidas_lista

    def logica_chamadas(self, dados_agente):
        '''função para filtrar apenas os agentes que fizeram mais de 4 chamadas o retorno vai ser o len() da lista de agentes após a lógica'''
        chamadas_tratadas = sum(1 for chamadas in dados_agente if chamadas > 4)
        return chamadas_tratadas

    def execucao_limpeza(self, completas_bruto, recusadas_bruto, abandonadas_bruto, performace_suja):
        '''Vai executar a limpeza de dados de forma centralizada'''
        completas = self.tratamento_chamadas(completas_bruto)
        recusadas_semi_bruto = self.tratamento_chamadas(recusadas_bruto)
        abandonadas = self.tratamento_chamadas(abandonadas_bruto)
        recusadas = self.chamadas_recusadas(recusadas_semi_bruto, abandonadas)
        totais = self.agregar_dados(completas, recusadas_semi_bruto)
        chamadas = self.limpeza_performace_json(performace_suja)
        chamadas_completas = self.logica_chamadas(chamadas)

        return {
            "completas": completas,
            "recusadas": recusadas,
            "abandonadas": abandonadas,
            "totais": totais,
            "agentes_validos": chamadas_completas,
        }
