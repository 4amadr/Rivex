import time
from datetime import datetime, timedelta, date

class DateConfig:
        
    def data_selecionadas():
        data_ref = date.today() - timedelta(days=1)
        data_formatada = data_ref.strftime("%Y-%m-%d")
        print('Dia: ', data_formatada)
        print(type(data_formatada))
        return data_formatada
    
dc = DateConfig
data = dc.data_selecionadas
print(data)