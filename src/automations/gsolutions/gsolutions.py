import os
from datetime import datetime, date, timedelta
import requests
from utils.fast_selenium import FastSelenium
from dotenv import load_dotenv
import time
from bs4 import BeautifulSoup

load_dotenv()
class GSolutionsData:
    def __init__(self, user_login, password_login, url, operadora):
        self.user=user_login
        self.password=password_login
        self.url=url

    def login_gs(self, user, password, operadora):
        fs = FastSelenium(driver, timeout=20)
        try:
            #user
            fs.type_text('/html/body/div[1]/div[2]/div[1]/div/form/input[2]', user)
            #password
            fs.type_text('/html/body/div[1]/div[2]/div[1]/div/form/input[3]', password)
            # wait until user and password get tiped
            fs.click_button('//*[@id="bt-login"]/input')
            print(f'Logged in {operadora}')
            time.sleep(1)

        except Exception as e:
            print(f'Error on login(GSOLUTIONS), type error: {e}')
            return False

    def get_data_gs(self, driver, operadora):
        '''Function to get data from gs page'''
        try:
            fs = FastSelenium(driver, timeout=20)
            # caminho até a página de clientes, minutagem e custos
            fs.click_button('//*[@id="4"]')
            fs.click_button('//*[@id="4_0"]')
            # seleção do período
            #fs.click_button('//*[@id="periodopre"]')
            fs.click_button('//*[@id="periodopre"]/option[5]')
            gs.select_date()
            fs.click_button('//*[@id="site"]/form/table/tbody/tr[5]/td/div/input')


            # para pegar o html da página
            html = driver.page_source
            return html
        except Exception as erro:
            print(f'Erro no caminho de minutagem e custos {operadora}', erro)
            return False

    def select_date(self):
        '''Função para fazer a seleção de data'''

        # definindo a data
        mes = int(datetime.today().month)
        ano = int(datetime.today().year)
        hoje = date.today()
        ontem = hoje - timedelta(days=1)


        fs = FastSelenium(driver, timeout=20)
        try:
            #fs.click_button('//*[@id="periodocustom"]/input[1]')
            fs.type_text('//*[@id="periodocustom"]/input[1]', f'{ontem}')
            print('Dia selecionado')
            time.sleep(1)
            fs.type_text('//*[@id="periodocustom"]/input[3]', f'{ontem}')
            print(f'Definindo a data como {ontem}-{mes}-{ano}')
        except Exception as e:
            print(f'Erro ao selecionar o dia {ontem}', e)

    def req_dados(self, operadora):
        """Função para pegar o html da página"""
        print(f'Iniciando tratamento de dados para a operadora {operadora}')
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        linhas = soup.find_all("tr")
        return linhas

    def tratamento_html(self, linhas, operadora):
        '''Função para pegar apenas os dados que precisamos do HTML'''
        print(f'iniciando tratamento de html para a operadora {operadora}')

        for linha in linhas:
            tabelas = linha.find_all('table')
            for tabela in tabelas:
                linhas_dados = tabela.find_all('td')
                print(linhas_dados)
                return linhas_dados

    def remover_html(self, linhas_dados, operadora):
        '''Função para transformar os dados e remover a marcação HTML deles'''
        valores = [td.get_text(strip=True) for td in linhas_dados]
        print(valores)
        return True

        print(f'Iniciando o tratamento de linhas de dados para a operadora {operadora}')

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
    operadora = 'Gsolutions'
    try:
        gs = GSolutionsData(login_gs, password_gs, url_gs, operadora)
        driver = FastSelenium.run_driver(url_gs)
        gs.login_gs(login_gs, password_gs, operadora)
        html = gs.get_data_gs(driver, operadora)
        linhas = gs.req_dados(operadora)
        linha_dados = gs.tratamento_html(linhas, operadora)
        gs.remover_html(linha_dados, operadora)
        #gs.go_to_calls_gs(driver)
       # gs.get_chamadas_tarifadas(lista_cliente)
        print("Coleta finalizada com sucesso!")
    except Exception as e:
        print(f'ERRO: {e} ao coletar dados da Gsolutions')
        
    # em desenvolvimento...