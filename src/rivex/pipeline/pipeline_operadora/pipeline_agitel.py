from src.rivex.environments.operadoras.gsolutions.sip_client_scrap import *
import os
from src.rivex.utils.infra_utils.date_config import *
from src.rivex.database.database_dados_chamadas import *
#from src.rivex.data_processing.gsolutions. import *
import time

class ExecAgitel():
      
    def pipeline_agitel(self):
        dc = DateConfig()
        data = dc.data_selecionadas()
        print(f"Coleta do dia {data} na agitel")
        sc = SipClient(usuario=os.getenv('AGITEL_USER'),
                    password=os.getenv('AGITEL_PASSWORD'),
                    url=os.getenv('AGITEL_URL'),
                    operadora='Agitel',
                    data=data)
        sch = SipCharged(
            data=data,
            url_base=os.getenv('AGITEL_URL'),
            usuario=os.getenv('AGITEL_USER'),
            password=os.getenv('AGITEL_PASSWORD'),
            
        )

        # execução
        consumo_por_cliente, dict_id_clientes = sc.execucao_pipeline_sip()
        
        # limpeza
        limpar_sip = CleanerSip(consumo=consumo_por_cliente,
                             id_clientes=dict_id_clientes)
        lista_cliente, lista_minutagem, lista_custo = limpar_sip.limpar_consumo()
        
        # segunda execução
        lista_techs, lista_ids_online = limpar_sip.gerar_ids_tarifadas(lista_cliente)
        lista_tarifadas_html = sch.lista_chamadas_tarifadas(lista_ids_online)

        # segunda limpeza
        tarifa_limpa = [limpar_sip.limpar_chamadas_tarifadas(tarifa) for tarifa in lista_tarifadas_html]

        # empacotamento
        pacote_agitel = EmpacotamentoAgitel(
            data_db=dc.data_callix(),
            lista_tech=lista_techs,
            lista_clientes=lista_cliente,
            lista_minutagem=lista_minutagem,
            lista_custo=lista_custo,
            lista_tarifadas=tarifa_limpa

        )
        # carregamento
        db = DatabaseRivex()
        cursor, conexao = db.abrir_banco()
        lista_dados = pacote_agitel.preparar_dados()
        print("LISTA DE DADOS QUE VAI SER ENVIADA PARA O BANCO: ", lista_dados)
        for dado_db in lista_dados:
            print("Conferencia de dados que irão para o banco!")
            print(dado_db)
            time.sleep(5)
            db.enviar_banco_operadoras(dado_db, cursor)
        db.fechar_db(cursor=cursor, conexao=conexao)