class CallixClientData:
    '''
    classe que vai retornar dois dicionários 
    1 - Dict cliente: id, fila, chamadas totais, chamadas aceitas, chamadas recusadas, chamadas abandonadas, agressividade e data
    2 - Dict agente: id, fila, nome agente, chamadas_aceitas_agente
    '''
    def __init__(self, cliente, chamadas, aceitas, recusadas, abandonadas, agressividade, data, agentes_info):
        self.cliente = cliente
        self.chamadas = chamadas
        self.aceitas = aceitas
        self.recusadas = recusadas
        self.abandonadas = abandonadas
        self.agressividade = agressividade
        self.data = data
        self.agentes_info = agentes_info
        self.data = data


    def pacote_chamadas(self):
        dict_chamadas =  {
            "Cliente": self.cliente,
            "Data": self.data,
            "Chamadas totais": self.chamadas,
            "Chamadas aceitas": self.aceitas,
            "Chamadas recusadas": self.recusadas,
            "Chamadas abandonadas": self.abandonadas,
            "Agressividade": self.agressividade
        }
        print("Dicionário  da chamadas: ",dict_chamadas)
        return dict_chamadas
    
    def pacote_agentes(self):
        for dicionario_agente in self.agentes_info:
            for agente, chamada_aceita in dicionario_agente.items():
                dict_agentes = {
                    "Cliente": self.cliente,
                    "Data": self.data,
                    "Nome do agente": agente["agente"],
                    "Chamadas aceitas do agente": chamada_aceita["Chamadas atendidas"],
                }
                lista_agentes = [dict_agentes]
        print("Dicionário dos dos agentes: ", dict_agentes)
        return lista_agentes
