from src.rivex.utils.infra_utils.date_config import DateConfig
import json
    
    
def _limpar_chamadas(resumo, tipo_chamada: str):
    return resumo["data"][0]["attributes"][tipo_chamada]

def _extrair_ids(campanha):
    return [int(item) for item in campanha[0]]


def processar_dados(dados_brutos_api):
    completa = _limpar_chamadas(dados_brutos_api['resumo'], "outgoing_completed_count")
    recusadas_brutas = _limpar_chamadas(dados_brutos_api['resumo'], "outgoing_missed_count")
    abandonadas = _limpar_chamadas(dados_brutos_api['resumo'], "outgoing_missed_agents_count")
    total = _limpar_chamadas(dados_brutos_api['resumo'], "outgoing_count")
    id_campanha = _extrair_ids(dados_brutos_api['campanha'])

    recusadas = recusadas_brutas - abandonadas
    
    return {
        "Chamadas totais": total,
        "Chamadas aceitas": completa,
        "Chamadas recusadas": recusadas,
        "Chamadas abandonadas": abandonadas,
        "Campanha": id_campanha,
    }
        