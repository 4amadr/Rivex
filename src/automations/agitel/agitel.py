import os

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

    def login(self, login, password, operadora):
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

    def config_date(self, operadora):
        '''Select date function'''
        fs = FastSelenium(driver, timeout=20)

        data_hoje = date.today()
        ontem = data_hoje - timedelta(days=1)

        try:
            fs.click_button('//*[@id="periodopre"]')
            fs.click_button('//*[@id="periodopre"]/option[5]')

            # selecionei o periodo customizado para dar maior controle sobre a data
            fs.type_text('//*[@id="periodocustom"]/input[1]', ontem)
            fs.type_text('//*[@id="periodocustom"]/input[3]', ontem)
            fs.click_button('//*[@id="site"]/form/table/tbody/tr[5]/td/div/input')
            print(f' {operadora} com Dados filtrados')
            cookies = driver.get_cookies()
            return cookies

        except Exception as erro_config:
            print(f'Erro na operadora {operadora}ao filtrar os dias: {erro_config}')
            return False

    def get_agent_data(self, cookies, url):
        '''function to get agent data'''

        response = requests.get(url, cookies=cookies)

        if response.status_code == 200:
            dados_operadora = response.text
            return dados_operadora
        else:
            print(f'Requisição mal feita {response.status_code}')


if __name__ == '__main__':
    print('Iniciando coleta de dados da Agitel...')
    login = os.getenv('agitel_user')
    password = os.getenv('agilel_password')
    url_agitel = os.getenv('agitel_url')
    operadora = 'Agitel'
    try:
        ol = OperadorasLogin(login, password, url_agitel, operadora)
        driver = FastSelenium.run_driver(url_agitel)
        ol.login(login, password, operadora)
        ol.pag_dados()
        cookies = ol.config_date(operadora)
        ol.get_agent_data(cookies, url_agitel)
    except Exception as erro_login:
        print(f'Erro {erro_login} Durante a coleta de dados')



