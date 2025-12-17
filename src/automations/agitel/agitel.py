import os
import time

import selenium
from sqlalchemy.ext.horizontal_shard import set_shard_id
from webdriver_manager.core import driver
import requests
from utils.fast_selenium import FastSelenium
import dotenv
from datetime import datetime, timedelta
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

    def coletar_tabela(self):
        '''function to get agent data'''
        fs = FastSelenium(driver, timeout=20)

        # pegar para pegar a tabela
        tabela_dados = fs.xpath_data('//*[@id="site"]/table/tbody/tr/td/table')
        print(tabela_dados)
        return tabela_dados


if __name__ == '__main__':
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
        tabela = ol.coletar_tabela()
    except Exception as erro_login:
        print(f'Erro {erro_login} Durante a coleta de dados')



