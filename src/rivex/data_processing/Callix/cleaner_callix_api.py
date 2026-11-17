from src.rivex.utils.infra_utils.date_config import DateConfig
import json
    
    
def _limpar_chamadas(resumo, tipo_chamada: str) -> int:
    dados = resumo.get("data") or []
    return sum(
        item.get("attributes", {}).get(tipo_chamada, 0) or 0
        for item in dados
    )


def _extrair_ids(campanha) -> list[int]:
    if not campanha:
        return []
    if isinstance(campanha[0], (list, tuple)):
        return [int(item) for item in campanha[0]]
    return [int(item) for item in campanha]


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


        