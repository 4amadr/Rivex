from src.automations.Callix.callix import CallixAPI
from src.automations.Callix.callix_token_db import CallixDB
from src.data_processing.cleaner_api import LimpezaCallixAPI
from src.database_converter.callix_converter import CallixCSVConverter


def main_callix():

    db = CallixDB()
    tokens_clientes = db.get_token_and_client_from_db()
    db.close()

    if not tokens_clientes:
        raise RuntimeError('Sem clientes ou tokens no banco')

    api = CallixAPI()
    limpeza = LimpezaCallixAPI()

    resultados = []
    data = api.data_selecionadas()
    for cliente, token in tokens_clientes.items():
        try:
            print('Coletando dados do cliente', cliente)

            dados_brutos = api.execucao_por_cliente(cliente, data, token=token)
            dados_limpos = limpeza.execucao_limpeza(
                completas_bruto=dados_brutos["completas"],
                recusadas_bruto=dados_brutos["recusadas"],
                abandonadas_bruto=dados_brutos["abandonadas"],
                performace_suja=dados_brutos["performance"]
            )
            print(type(dados_limpos), dados_limpos)

            resultados.append({
                'cliente': cliente,
                "Data": data,
                **dados_limpos
            })

        except Exception as e:
            print(f'Erro na execução do cliente {cliente}: {e}')

    converter = CallixCSVConverter()
    caminho = converter.save_csv(resultados)
    print(f'Coleta completamente acabada\n dados salvos em {caminho}')
    return resultados
main_callix()
