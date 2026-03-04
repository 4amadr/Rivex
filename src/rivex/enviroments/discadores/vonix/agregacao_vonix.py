from src.rivex.enviroments.discadores.vonix.fluxo_limpeza import LimpezaVonix
from src.rivex.enviroments.discadores.vonix.equipes_vonix import dict_agentes
import pandas as pd

class AgregacaoVonix:
    def agregacao_vonix(self, dados_sem_prefixo):
        equipes_agregadas = {}

        for dados in dados_sem_prefixo:
            fila          = dados['Fila']
            totais        = dados['Chamadas totais']
            completas     = dados['Chamadas completas']
            recusadas     = dados['Chamadas recusadas']
            agentes       = dados['Agentes']
            agressividade = dados['Agressividade']

            if fila in equipes_agregadas:
                equipes_agregadas[fila]['Chamadas totais']    += totais
                equipes_agregadas[fila]['Chamadas completas'] += completas
                equipes_agregadas[fila]['Chamadas recusadas'] += recusadas
                equipes_agregadas[fila]['Agentes']            += agentes
                equipes_agregadas[fila]['_contagem']          += 1
            else:
                equipes_agregadas[fila] = {
                    'Chamadas totais'    : totais,
                    'Chamadas completas' : completas,
                    'Chamadas recusadas' : recusadas,
                    'Agentes'            : agentes,
                    'Agressividade'      : agressividade,
                    '_contagem'          : 1
                }

        # Calcula a média de agentes e remove o campo auxiliar
        for fila in equipes_agregadas:
            equipes_agregadas[fila]['Agentes'] /= equipes_agregadas[fila]['_contagem']
            del equipes_agregadas[fila]['_contagem']

        return equipes_agregadas