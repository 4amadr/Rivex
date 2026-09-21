class CallixClientData:
    '''
    classe que vai retornar dois dicionários 
    1 - Dict cliente: id, fila, chamadas totais, chamadas aceitas, chamadas recusadas, chamadas abandonadas, agressividade e data
    2 - Dict agente: id, fila, nome agente, chamadas_aceitas_agente
    '''
    def __init__(self, cliente, chamadas, aceitas, recusadas, abandonadas, agressividade, data, agentes_info, tech):
        self.tech = tech
        self.cliente = cliente
        self.chamadas = chamadas
        self.aceitas = aceitas
        self.recusadas = recusadas
        self.abandonadas = abandonadas
        self.agressividade = agressividade
        self.data = data
        self.agentes_info = agentes_info


    def pacote_chamadas(self):
        return  {
            "tech": self.tech,
            "cliente_nome": self.cliente,
            "data": self.data,
            "Discador": "Callix",
            "Chamadas": self.chamadas,
            "Chamadas_aceitas": self.aceitas,
            "Chamadas_recusadas": self.recusadas,
            "Chamadas_abandonadas": self.abandonadas,
            "agressividade": self.agressividade
        }
        
    
    def pacote_agentes(self):
        print("Informação dos agentes: ", self.agentes_info)

        lista_agentes = []

        if not self.agentes_info:
            return [{
                "tech": self.tech,
                "cliente": self.cliente,
                "discador": "Callix",
                "data": self.data,
                "nome_agente": "Sem agente",
                "chamadas_aceitas_agente": 0,
            }]

        for dicionario_agente in self.agentes_info:


            dict_agentes = {
                    "tech": self.tech,
                    "cliente": self.cliente,
                    "discador": "Callix",
                    "data": self.data,
                    "nome_agente": dicionario_agente.get("agente"),
                    "chamadas_aceitas_agente": dicionario_agente.get("Chamadas atendidas", 0),
                }


            lista_agentes.append(dict_agentes)
        return lista_agentes
