from src.rivex.enviroments.discadores.vonix.fluxo_coleta import *
from src.rivex.enviroments.discadores.vonix.fluxo_limpeza import *

class PipelineVonix:
    def __init__(self):
        pass
    
    def execucao(self):
        print('Iniciando a coleta de dados no discador Vonix...')
        ev = ExecucaoVonix()
        lv = LimpezaVonix()
        dc = DateConfig()
        database_conf = DatabaseConfig()
        conexao = database_conf.conect_database()
        
        data = dc.data_selecionadas()
        url_vonix = os.getenv('LINK_VONIX6')

        # lista com os dados para agregação
        resultados = []

        for equipes_vonix, times in dict_agentes.items():
            print(f'Coletando dados do equipe ->', equipes_vonix)

            for equipe in times:
                # timer para não quebrar o servidor
                time.sleep(15)
                print('Executanto a fila ->',equipe)
                # primeiro coletamos os dados em formato HTML

                chamadas_totais, chamadas_completas, chamadas_recusadas, chamadas_abandonadas, html_agentes, html_agressividade = ev.execucao_vonix(data=data,
                                                                                                                                                    url=url_vonix, 
                                                                                                                                                    equipe=equipe)
                print('Dados sujos coletados. Executando agora a limpeza de dados')

                # agora a limpeza de dados para trazer apenas os dados limpos para o banco de dados
                dict_vonix_dados = lv.limpeza_de_dados_vonix(chamadas_totais, chamadas_completas, chamadas_recusadas, chamadas_abandonadas, html_agentes, html_agressividade, equipe, data)
            
                # inserir os dados de agentes e suas chamadas no banco
                DatabaseRivex.coleta_agentes(conexao, equipe, data, dict_vonix_dados)
                    
                # inserir dados de chamadas no banco
                DatabaseRivex.coleta_chamadas(conexao, dict_vonix_dados)
                
                resultados.append(dict_vonix_dados)