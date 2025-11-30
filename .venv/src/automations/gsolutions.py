import os
from selenium.common import NoSuchElementException
from utils.fast_selenium import FastSelenium
from selenium import webdriver
from dotenv import load_dotenv
import time
from selenium.webdriver.common.by import By

load_dotenv()
class GSolutionsData:
    def __init__(self, user_login, password_login, url):
        self.user=user_login
        self.password=password_login
        self.url=url

    def login_gs(self, user, password):
        fs = FastSelenium(driver, timeout=20)
        try:
            #user
            fs.type_text('/html/body/div[1]/div[2]/div[1]/div/form/input[2]', user)
            #password
            fs.type_text('/html/body/div[1]/div[2]/div[1]/div/form/input[3]', password)
            # wait until user and password get tiped
            fs.click_button('//*[@id="bt-login"]/input')
            print('Logged in GSOLUTIONS')
            time.sleep(1)
            return True
        except Exception as e:
            print(f'Error on login(GSOLUTIONS), type error: {e}')
            return False

    def get_data_gs(self, driver):
        '''Function to get data from gs page'''
        try:
            fs = FastSelenium(driver, timeout=20)
            lista_cliente_operadora = []
            lista_minutagem = []
            lista_valor = []
            # road to page of data
            fs.click_button('//*[@id="4"]')
            fs.click_button('//*[@id="4_0"]')
            fs.click_button('//*[@id="periodopre"]/option[2]')
    def go_to_calls_gs(self, driver):
        '''Função para ir até as chamadas tarifadas'''
        fs = FastSelenium(driver, timeout=20)
        try:
            fs.click_button('//*[@id="2"]')
            fs.click_button('//*[@id="2_0"]')
            print('\nChegamos nas chamadas tarifadas')
            return True
        except Exception as erro_caminho_chamadas_tarifadas:
            print('Erro ao tentar chegar nas chamadas tarifadas', erro_caminho_chamadas_tarifadas)
            return False
    def get_chamadas_tarifadas(driver, lista_cliente):
        '''Função para coletar as chamadas tarifadas de cada cliente'''
        fs = FastSelenium(driver, timeout=20)
        for cliente_listado in lista_cliente:
            # para pesquisar por nome do cliente
            time.sleep(3)
            fs.click_button('//*[@id="auto"]')
            time.sleep(3)
            fs.type_text('//*[@id="auto"]', cliente_listado)
            time.sleep(3)
            fs.click_button('//*[@id="site"]/form/table/tbody/tr[4]/td/div/input')
            time.sleep(3)
            fs.click_button('//*[@id="site"]/table/tbody/tr/td/table/tbody/tr[3]/td[7]')
            print('final do código')
            
            print('opção selecionada')
            time.sleep(5)
            # falta terminar, está indo até o botão de opções após filtrar.............

if __name__ == '__main__':
    print('Iniciando coleta de dados da GSolutions...')
    login_gs = os.getenv('gsolutions_user')
    password_gs = os.getenv('gsolutions_password')
    url_gs = os.getenv('gsolutions_url')
    try:
        gs = GSolutionsData(login_gs, password_gs, url_gs)
        driver = FastSelenium.run_driver(url_gs)
        gs.login_gs(login_gs, password_gs)
        lista_cliente, lista_minutagem, lista_valor = gs.get_data_gs(driver)
        #gs.go_to_calls_gs(driver)
       # gs.get_chamadas_tarifadas(lista_cliente)
        print("Coleta finalizada com sucesso!")
    except Exception as e:
        print(f'ERRO: {e} ao coletar dados da Gsolutions')
        
    # em desenvolvimento...