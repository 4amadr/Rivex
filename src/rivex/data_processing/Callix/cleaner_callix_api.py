from src.rivex.utils.infra_utils.date_config import DateConfig

class LimpezaCallixAPI:
    def limpeza_contagens(self, chamadas_completas):
        return int(raw.get("meta", {}).get("count", 0))
    
    def calcular_recusadas(self, recusadas, abandonadas):
        return max(recusadas - abandonadas, 0)
    
    def limpeza_performace(self, performace):
        return [
            {
                "Id agente": performace['id'],
                "chamadas": performace['attributes']['answered_count'],
            }
            for agente in performace.get("data", [])
        ]
        
    def limpeza_agressividade(self, agressividade):
        if not agressividade:
            return None
        ultimo = agressividade[-1]
        return ultimo["data"]["attributes"].get("powerAggressiveness")
    
    def contador_chamadas_totais(self, chamadas_aceitas, chamadas_recusadas, chamadas_abandonadas, agressividade_coletada):
        pass
    
    def limpar_dados_callix(self, chamadas_aceitas, chamadas_recusadas, chamadas_abandonadas, performace):
        
        completa = self.limpeza_contagens(chamadas_aceitas)
        recusadas_brutas = self.limpeza_contagens(chamadas_recusadas)
        abandonadas = self.limpeza_contagens(chamadas_abandonadas)
        recusadas = self.calcular_recusadas(recusadas_brutas, abandonadas)
        total = completa + recusadas_brutas
        
        agentes = self.limpeza_performace(performace)
        agressividade = self.limpeza_agressividade(agressividade_coletada)
        
        
        return {
            "Agressividade": agressividade,
            "Chamadas totais": total,
            "Chamadas aceitas": completa,
            "Chamadas recusadas": recusadas,
            "Chamadas abandonadas": abandonadas,
            "Agentes online": agentes,
        }