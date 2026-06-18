from datetime import date, timedelta, datetime

class DateConfig:

    @staticmethod
    def data_selecionadas():
        data_ref = date.today() - timedelta(days=1)
        data_formatada = data_ref.strftime("%d/%m/%Y")
        print('Dia selecionado: ', data_formatada)
        return data_formatada
    
    def data_callix(self):
        data_ref = date.today() - timedelta(days=2)
        data_formatada = data_ref.strftime("%Y-%m-%d")
        print('Dia de coleta: ', data_formatada)
        return data_formatada

    def data_ipbox(self, dias_atras=1):
        data_ref = date.today() - timedelta(days=dias_atras)

        print(
            'Dia selecionado:',
            data_ref.strftime('%d/%m/%Y')
        )

        return data_ref.strftime('%Y%m%d')
    
    def data_ipbox_payload(self, dias_atras=1):
        """
        Gera o payload no formato:
        de=YYYYMMDD000000&ate=YYYYMMDD235959

        O horário permanece fixo:
        - início do dia -> 000000
        - fim do dia -> 235959
        """

        # Define a data base
        data_ref = date.today() - timedelta(days=dias_atras)

        # Formata apenas a parte da data
        data_formatada = data_ref.strftime("%Y%m%d")

        # Monta o payload usando a MESMA variável de data
        payload = {
            "de": f"{data_formatada}000000",
            "ate": f"{data_formatada}235959"
            
        }

        return payload
    
    