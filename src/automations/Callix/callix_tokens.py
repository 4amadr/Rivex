from datetime import time
from selenium import webdriver
from utils.fast_selenium import FastSelenium
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine
import time
from selenium.webdriver.common.keys import Keys
import psycopg2
import pandas as pd

load_dotenv()

class TokenCallix:

    def __init__(self, cliente_site, username, passwords):
        # tratamento de erros
        self.credenciais = []
        for cliente in cliente_site:
            if cliente:
                credenciais = os.getenv(cliente)
                self.credenciais.append(credenciais)
            else:
                self.credenciais.append(None)
                print('Erro de append none, erro no arquivo .env')
                return False
        self.username_callix = []
        for username in username:
            if username:
                users = os.getenv(username)
                self.username_callix.append(users)
            else:
                self.credenciais.append(None)
                print('Erro de append none(username), erro no arquivo .env')
        self.passwords_callix = []
        for password in passwords:
            if password:
                passwords = os.getenv(password)
                self.passwords_callix.append(passwords)
            else:
                self.credenciais.append(None)
                print('Erro de append none(password), erro no arquivo .env)')


    def login_callix(self, user, password):
        '''Função para logar no callix'''
        fs = FastSelenium(driver, timeout=20)
        time.sleep(5)
        # login
        fs.type_text('/html/body/div/router-view/div/clx-input-row[1]/div[1]/clx-text-input/clx-input-group/div/div[2]/input', user)
        # senha
        fs.type_text('/html/body/div/router-view/div/clx-input-row[2]/div[1]/clx-text-input/clx-input-group/div/div[2]/input', password)
        # logar
        fs.click_button('/html/body/div/router-view/div/button/span[1]')
        time.sleep(3)
        return cliente_site

    def go_to_api_session(self):
        '''função para ir até o caminho da api'''
        fs = FastSelenium(driver, timeout=20)
        # vou ir até a pesquisa e digitar a sessão exata pois vou ter muito mais trabalho indo ao local manualmente
        # clique no botão de pesquisa
        fs.click_button('/html/body/div[1]/clx-menu/div[2]/div[1]/div/i')
        # clicar na caixa de texto de pesquisa
        fs.click_button('/html/body/div[1]/clx-command-menu/react-wrapper/div/section/div/input')
        # digitar o valor
        fs.type_text('/html/body/div[1]/clx-command-menu/react-wrapper/div/section/div/input', 'Acesso à API')
        # clique
        time.sleep(2)
        fs.click_button('/html/body/div[1]/clx-command-menu/react-wrapper/div/section/ol/li/span[2]')
        return True

    def get_api_callix(self):
        '''Função para pegar uma API se ela existir, se não existir ele vai criar e pegar'''
        fs = FastSelenium(driver, timeout=20)
        token_callix = fs.xpath_data('//*[@id="router-view"]/clx-page/div[2]/clx-data-table/div/table/tbody/tr/td[1]/a')
        if token_callix:
            return token_callix
        else:
            # se não houver token vai criar uma nova
            print('Não tem token, criando um...')
            time.sleep(3)
            fs.click_button('//*[@id="router-view"]/clx-page/div[1]/div/div[2]/div/button')
            fs.click_button('//*[@id="select2-imiu-container"]')
            time.sleep(2)
            fs.click_button('/html/body/ux-dialog-container/div/div/clx-dialog/clx-panel-section/form')
            fs.xpath_data('/html/body/ux-dialog-container/div/div/clx-dialog/clx-panel-section/form/div/button/i')
            return token_callix

    def create_df(self, token_callix, cliente_site):
        '''Função para transformar os tokens + links de clientes em dataframe
        posteriormentes vão ser levadas para o banco de dados'''
        try:
            dados = {
                'cliente': [cliente_site],
                'token': [token_callix],
            }
            df = pd.DataFrame(dados, index=[0])
            return df
            print('Dataframe criado!')
        except Exception as e:
            print('Erro durante a criação do dataframe com os tokens!',e)
            return False


    def create_database_tokens(self, df):
        '''cria o banco de dados para armazenar os tokens do callix'''
        engine = None
        connection = None
        
        try:
            db_url = 'postgresql://postgres@localhost:5432/contech_data'
            engine = create_engine(db_url)
            
            print('Iniciando a conexção...')
            df.to_sql('callix_tokens', engine, if_exists='append', index=False)
            time.sleep(2)
            print('Tokens enviados para o banco de dados!')
            return True
        except Exception as error:
            print('Erro ao enviar tokens para o banco de dados')
            return False
        finally:
            if 'engine' in locals():
                engine.dispose()

cliente_site = [
                    'informacred',
                    'connection', 'ello_consultoria',
                    'essence', 'investe_mais', 'corplar',
                    'quality', 'lunart3', 'valm',
                    'datateck', 'rdf', 'credbi', 'money_solutions'
                ]

users = [
            'login_informacred', 'login_connection', 'login_ello_consultoria',
            'login_callix_essence', 'login_callix_investe_mais', 'login_callix_corplar',
            'login_callix_quality','login_callix_lunart3', 'login_callix_valm',
             'login_callix_datateck',
            'login_callix_rdf', 'login_callix_credbi', 'login_callix_money_solutions'
         ]

passwords = [
                'senha_informacred', 'senha_connection', 'senha_ello_consultoria',
                'senha_callix_essence', 'senha_callix_inteste_mais', 'senha_callix_corplar',
                'senha_callix_quality', 'senha_callix_lunart3', 'senha_callix_valm',
                'senha_callix_datateck',
                'senha_callix_rdf', 'senha_callix_credbi','senha_callix_money_solutions'

]


tc = TokenCallix(cliente_site, users, passwords)
print(tc.credenciais)
if __name__ == '__main__':
    for cliente, user, password in zip(tc.credenciais, tc.username_callix, tc.passwords_callix):
        try:
            print(f'Iniciando o processo de coleta de tokens do callix no site {cliente}')
            driver = FastSelenium.run_driver(f'https://{cliente}')
            tc.login_callix(user, password)
            tc.go_to_api_session()
            token_callix = tc.get_api_callix()
            database = tc.create_df(token_callix, cliente)
            tc.create_database_tokens(database)
            print(f'\nTokens coletados com sucesso no site {cliente}')
            driver.quit()
            time.sleep(3)
        except Exception as e:
            print(f'\nERRO: ao coletar os tokens do callix no site {cliente}', e)
            continue
            driver.quit()

print('Driver fechado!')

