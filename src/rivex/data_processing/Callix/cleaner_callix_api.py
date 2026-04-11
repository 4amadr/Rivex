from src.rivex.utils.infra_utils.date_config import DateConfig

class LimpezaCallixAPI:
    def limpeza_contagens(self, chamadas_completas):
        return int(chamadas_completas.get("meta", {}).get("count", 0))
    
    def calcular_recusadas(self, recusadas, abandonadas):
        return max(recusadas - abandonadas, 0)
        
    def limpeza_agressividade(self, agressividade):
        if not agressividade:
            return None
        ultimo = agressividade[-1]
        return ultimo["data"]["attributes"].get("powerAggressiveness")
    
    def extrair_ids(self, campanha):
        return [item['id'] for item in campanha.get('data', [])]
    
    def limpeza_callix(self, chamadas_aceitas, chamadas_recusadas, chamadas_abandonadas, campanha):
        
        completa = self.limpeza_contagens(chamadas_aceitas)
        recusadas_brutas = self.limpeza_contagens(chamadas_recusadas)
        abandonadas = self.limpeza_contagens(chamadas_abandonadas)
        recusadas = self.calcular_recusadas(recusadas_brutas, abandonadas)
        total = completa + recusadas_brutas
        id_campanha = self.extrair_ids(campanha)
        
        # Tratamento apenas das chamadas de cada cliente
        print(total)
        print(completa)
        print(recusadas)
        print(abandonadas)
        print(id_campanha)
        
        return {
            "Chamadas totais": total,
            "Chamadas aceitas": completa,
            "Chamadas recusadas": recusadas,
            "Chamadas abandonadas": abandonadas,
            "Campanha": id_campanha,
        }
        