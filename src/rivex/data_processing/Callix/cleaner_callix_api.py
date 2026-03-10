from src.rivex.utils.infra_utils.date_config import DateConfig

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
        '''Função para retornar um dicionário com os agentes e quantas chamadas cada agente fez respectivamente'''
        agentes = None
        chamadas = None
        return agentes, chamadas
    
    def limpeza_agressividade(self, agressividade_json):
    # limpar a agressividade se houver valor
        if agressividade_json:
            valor_agressividade = [
                agressividade_json['attributes']['propertiesChanged']['$serialized']['powerAggressiveness']['value']
                for item in agressividade_convertida['data']
                if 'propertiesChanged' in item['attributes']
                and '$serialized' in item['attributes']['propertiesChanged']
                and 'powerAggressiveness' in item['attributes']['propertiesChanged']['$serialized']
            ]
            return valor_agressividade
        else:
            print('Sem agressividade alterada para ser tratada')
            return None

    def execucao_limpeza(self, cliente, completas_bruto, recusadas_bruto, abandonadas_bruto, performace_suja, agressividade_json):
        '''Vai executar a limpeza de dados de forma centralizada'''
        dc = DateConfig()
        data = dc.data_selecionadas
        
        
        completas = self.tratamento_chamadas(completas_bruto)
        recusadas_semi_bruto = self.tratamento_chamadas(recusadas_bruto)
        abandonadas = self.tratamento_chamadas(abandonadas_bruto)
        recusadas = self.chamadas_recusadas(recusadas_semi_bruto, abandonadas)
        totais = self.agregar_dados(completas, recusadas_semi_bruto)
        chamadas, agente = self.limpeza_performace_json(performace_suja)
        chamadas_completas = self.logica_chamadas(chamadas)
        agressividade = self.limpeza_agressividade(agressividade_json)

        return {
            "Discador": "Callix",
            "Data": data,
            "Fila": cliente,
            "completas": completas,
            "recusadas": recusadas,
            "abandonadas": abandonadas,
            "totais": totais,
            "Agressividade": agressividade,
            "Agentes": agentes,
            "Chamadas": chamadas
        }
