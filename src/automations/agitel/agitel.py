import os
import time
from bs4 import BeautifulSoup
from webdriver_manager.core import driver
from src.utils.fast_selenium import FastSelenium
from datetime import timedelta
from datetime import date
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

class OperadorasLogin:
    def __init__(self, login, password, url, operadora):
        self.login = login
        self.password = password
        self.url = url
        self.operadora = operadora

    def login_agitel(self, login, password, operadora):
        '''Login function'''

        fs = FastSelenium(driver, timeout=20)
        print(f'iniciando o login {operadora}')
        try:

            fs.type_text('//*[@id="login"]', login)
            fs.type_text('//*[@id="senha"]', password)
            fs.click_button('//*[@id="bt-login"]/input')
            print(f'Login in {operadora}')
            return True

        except Exception as erro_login:
            print(f'Error: Login in {operadora} erro: {erro_login}')
            return False

    def pag_dados(self):
        '''Road to data'''

        fs = FastSelenium(driver, timeout=20)

        try:
            fs.click_button('//*[@id="4"]')
            fs.click_button('//*[@id="4_1"]')

        except Exception as erro_pag:
            print(f'Erro ao entrar na página de dados {erro_pag}')
            return False

    def selecionar_data(self):
        '''Função para definir a data a ser inserida no filtro da operadora'''
        hoje = date.today()
        ontem = hoje - timedelta(days=1)
        mes = ontem.month
        dia = ontem.day
        ano = ontem.year
        data_completa = f'{dia}/{mes}/{ano}'
        print('Dia selecionado', data_completa)
        return data_completa

    def config_date(self, operadora):
        '''Select date function'''

        fs = FastSelenium(driver, timeout=20)
        ol = OperadorasLogin
        ontem = ol.selecionar_data(self)

        try:
            fs.click_button('//*[@id="periodopre"]')
            fs.click_button('//*[@id="periodopre"]/option[5]')

            # selecionei o período customizado para dar maior controle sobre a data
            fs.type_text('//*[@id="periodocustom"]/input[1]', ontem)
            time.sleep(1)
            fs.type_text('//*[@id="periodocustom"]/input[3]', ontem)
            print(f'Definindo a data como {ontem}')
            fs.click_button('//*[@id="site"]/form/table/tbody/tr[5]/td/div/input')
            print(f' {operadora} com Dados filtrados')
            return True
        except Exception as erro_config:
            print(f'Erro na operadora {operadora} ao filtrar os dias: {erro_config}')
            return False

    def coletar_fonte_pagina(self):
        '''function to get agent data'''
        # pegar para pegar a tabela
        time.sleep(4)
        html = driver.page_source
        return html

    def coletar_tabela(self, html):
        try:
            soup = BeautifulSoup(html, 'html.parser')
            tabela = soup.select('table.tabela_azul')[1]
            if tabela:
                df = pd.read_html(str(tabela), match='Minutos', header=1)[0]
                print(df.columns)
                print(df.shape)
                print(df.head(3))
                return df
            else:
                print('Não existe tabela')
                return False

        except Exception as erro_tabela:
            print('Erro durante a tentativa de transformar a tabela', erro_tabela)
            return False


if __name__ == '__main__':
    hoje = date.today()
    dia_semana = hoje.isoweekday()
    # calculo de datas completas
    ontem_date = hoje - timedelta(days=1)
    dias_ate_sabado = (dia_semana - 6) % 7
    ultimo_sabado = hoje - timedelta(days=dias_ate_sabado if dias_ate_sabado != 0 else 7)
    ultima_sexta = ultimo_sabado - timedelta(days=1)  # sexta é 1 dia antes do sábado
    ontem = ontem_date.day  # dia do mês de ontem
    sabado = ultimo_sabado.day  # dia do mês que foi sabado
    dia_selecionado = ontem



    print('Iniciando coleta de dados da Agitel...')
    login = os.getenv('agitel_user')
    password = os.getenv('agilel_password')
    url_agitel = os.getenv('agitel_url')
    operadora = 'Agitel'
    try:
        ol = OperadorasLogin(login, password, url_agitel, operadora)
        driver = FastSelenium.run_driver(url_agitel)
        ol.login_agitel(login, password, operadora)
        ol.pag_dados()
        cookies = ol.config_date(operadora)
        html = ol.coletar_fonte_pagina()
        df = ol.coletar_tabela(html)
        driver.quit()
        print('Iniciando a criação do arquivo.csv')
        df.to_csv(f'Agitel-{ontem}.csv')

    except Exception as erro_login:
        print(f'Erro {erro_login} Durante a coleta de dados')



