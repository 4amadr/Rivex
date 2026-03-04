from datetime import date, timedelta, datetime

class DateConfig:

    @staticmethod
    def data_selecionadas():
        data_ref = date.today() - timedelta(days=2)
        data_formatada = data_ref.strftime("%d/%m/%Y")
        print('Dia selecionado: ', data_formatada)
        return data_formatada
    
    def data_callix():
        data_ref = date.today() - timedelta(days=2)
        data_formatada = data_ref.strftime("%Y-%m-%d")
        print('Dia selecionado: ', data_formatada)
        return data_formatada
    
    