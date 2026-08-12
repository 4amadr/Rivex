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
        dict_chamadas =  {
            "tech": self.tech,
            "Cliente": self.cliente,
            "Data": self.data,
            "Discador": "Callix",
            "Chamadas totais": self.chamadas,
            "Chamadas aceitas": self.aceitas,
            "Chamadas recusadas": self.recusadas,
            "Chamadas abandonadas": self.abandonadas,
            "Agressividade": self.agressividade
        }
        print("Dicionário  da chamadas: ",dict_chamadas)
        return dict_chamadas
    
    def pacote_agentes(self):
        print("Informação dos agentes: ", self.agentes_info)

        lista_agentes = []

        if not self.agentes_info:
            return [{
                "tech": self.tech,
                "Cliente": self.cliente,
                "discador": "Callix",
                "Data": self.data,
                "Nome do agente": "Sem agente",
                "Chamadas aceitas do agente": 0,
            }]

        for dicionario_agente in self.agentes_info:


            dict_agentes = {
                    "tech": self.tech,
                    "Cliente": self.cliente,
                    "discador": "Callix",
                    "Data": self.data,
                    "Nome do agente": dicionario_agente.get("agente"),
                    "Chamadas aceitas do agente": dicionario_agente.get("Chamadas atendidas", 0),
                }


            lista_agentes.append(dict_agentes)

        print("Dicionário dos agentes: ", lista_agentes)
        return lista_agentes
