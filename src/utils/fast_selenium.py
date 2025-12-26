from datetime import time

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
import time
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

class FastSelenium:

    def __init__(self, driver: webdriver, timeout=20):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 10)

    def xpath_data_com_tratamento(self, xpath):
        """"Function to get data from xpath com tratamento"""
        try:
            element = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            return element.text
        except NoSuchElementException:
            print("Valor não encontrado, será atribuido zero")
            element = 0
            return ""

    def click_button(self, xpath):
        """Function to click in any button on the page"""
        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            element.click()
            return True
        except TimeoutException:
            print('Timeout error trying to click, error type:', e)
            return False
        except NoSuchElementException:
            print(f'No elements found: {e}')
            return False
        except Exception as e:
            print(f'Error trying to click, error type: {e}')
            return False

    def find_class(self, class_name):
        """Function to find a class by name"""
        try:
            element = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, class_name))
            )
            return element.text
        except Exception as e:
            print(f'Error finding class: {e}')
        
    def xpath_data(self, xpath):
        """"Function to get data from xpath"""
        try:
            element = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            return element.text
        except Exception as e:
            print(f'Error geting xpath: {e}')
            return ""

    def cluck_button(self, xpath):
        """Function to press enter"""
        try:
            element = WebDriverWait(self.driver, 20).until(
                EC.presence_of_all_elements_located((By.XPATH, xpath))
            )
            element.click()
        except Exception as e:
            print(f'Timeout error trying to click, error type: {e}')

    def type_text(self, xpath, message):
        """"Function to type text"""
        try:
            type = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            # verifica se tem texto antes de apagar
            value_atual = type.get_attribute("value")
            if value_atual and value_atual.strip() != "":
            # delete all before type
                type.send_keys(Keys.CONTROL, 'a')
                type.send_keys(Keys.DELETE)
                time.sleep(2)
            else:
                pass
            type.send_keys(message)
        except TimeoutException:
            print(f'Timeout error trying to click, error type: {e}')
            return False
        except NoSuchElementException:
            print(f'No elements found to type: {e}')
            return False
        except Exception as e:
            print(f'Error type: {e}')
            
    def press_enter(self, xpath: str, key_command):
        try:
            # Bloco Try-Except
            element = ...
            element.send_keys(key_command) 
            print(f"Comando de tecla enviado: {key_command}")
            return True  # <--- CORRETO: Indentado dentro do 'try' e, portanto, da função
        except Exception as e:
            print(f'Erro ao enviar comando de tecla: {e}')
            return False # <--- CORRETO: Indentado dentro do 'except' e, portanto, da função
        # Note que a linha acima é a última linha da função. Não há mais nada desalinhado.
        

    def run_driver(url):
        chrome_options = Options()
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--allow-insecure-localhost')
        chrome_options.add_argument('--disable-ssl-version-warning')
        chrome_options.add_argument('--allow-running-insecure-content')
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        return driver

    def get_multiple_data(self, container_xpath, tag):
        """"Function to get multiple data from xpath"""
        data_table = []
        try:
            container = WebDriverWait(self.driver, 20).until(
                EC.presence_of_all_elements_located((By.XPATH, container_xpath))
            )
            for line in container:
                line_data = []
                elements_columns = line.find_elements(By.TAG_NAME, tag)
                for element in elements_columns:
                    line_data.append(element.text)
                data_table.append(line_data)
                #print(data_table)
            # formating
            for form_line in data_table:
                print(" | ".join(form_line))
            return data_table
        except Exception as e:
            print(f'Error getting multiple data from xpath: {e}')
            return []

    def clique_com_css(self, seletor_css):
        """Função para clicar com o seletor css"""
        try:
            # Wait for the element to be visible and clickable
            # This is crucial for handling dynamic content and ensuring the element is ready for interaction
            element = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, seletor_css))
            )

            # Click the element
            element.click()

            print("Element clicked successfully!")
        except Exception as e:
            print(f"An error occurred: {e}")

    def coletar_dados_com_seletor_css(self, seletor_css_dados):
        try:
            element = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, seletor_css_dados))
            )
            print(element.text)
            return True
        except Exception as e:
            print(f'Error geting data with seletor css: {e}')





