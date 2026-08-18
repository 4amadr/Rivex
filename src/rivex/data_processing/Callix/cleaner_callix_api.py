from src.rivex.utils.infra_utils.date_config import DateConfig
import json
    
    
def _limpeza_contagens(chamadas):
    return int(chamadas.get("meta", {}).get("count", 0))

def _limpeza_abandonadas(chamadas_abandonadas: list) -> int:
    causas_abandonadas = {9}

    return sum(
        1 for item in chamadas_abandonadas
        if item.get("attributes", {}).get("failure_cause") in causas_abandonadas
    )

def _calcular_recusadas(recusadas, abandonadas):
    return max(recusadas - abandonadas, 0)


def _limpeza_agressividade(agressividade):
    if not agressividade:
        return None
    ultimo = agressividade[-1]
    return ultimo["data"]["attributes"].get("powerAggressiveness")


def _extrair_ids(campanha):
    return [int(item) for item in campanha[0]]


def processar_dados(chamadas_aceitas, chamadas_recusadas, campanha):
    
    completa = _limpeza_contagens(chamadas_aceitas)
    recusadas_brutas = _limpeza_contagens(chamadas_recusadas)
    abandonadas = _limpeza_abandonadas(chamadas_recusadas.get("data", []))
    recusadas = _calcular_recusadas(recusadas_brutas, abandonadas)
    total = completa + recusadas_brutas
    id_campanha = _extrair_ids(campanha)
    
    # Tratamento apenas das chamadas de cada cliente
    print("Chamadas totais: ", total)
    print("Chamadas completas: ",completa)
    print("Chamadas recusadas: ", recusadas)
    print("Chamadas abandonadas:", abandonadas)
    print("ID da campanha: ", id_campanha)
    
    return {
        "Chamadas totais": total,
        "Chamadas aceitas": completa,
        "Chamadas recusadas": recusadas,
        "Chamadas abandonadas": abandonadas,
        "Campanha": id_campanha,
    }
        