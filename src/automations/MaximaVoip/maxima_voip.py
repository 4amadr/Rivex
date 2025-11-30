import os
from dateutil.rrule import weekday
from selenium.common import NoSuchElementException
from utils.fast_selenium import FastSelenium
from selenium import webdriver
import dotenv
import time
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from datetime import datetime, timedelta
from datetime import date
from dotenv import load_dotenv
import pandas as pd
import re

load_dotenv()


def select_date():
    hoje = date.today()
    dia_semana = hoje.weekday()  # segunda = 0

    if dia_semana == 0:  # se for segunda feira vai dar a lógica para coleta de dados para sexta e sabado
        sexta = hoje - timedelta(days=3)
        sabado = hoje - timedelta(days=2)
        ontem = hoje - timedelta(days=1)
    else:
        ontem = hoje - timedelta(days=1)
        sexta = ontem - timedelta(days=(ontem.weekday() - 4) % 7)
        sabado = ontem - timedelta(days=(ontem.weekday() - 5) % 7)
    return sexta, sabado, ontem, dia_semana



def selecionar_dia(driver, dia_da_coleta, periodo):
    """Seleciona o dia de ontem no calendário do Maxima VoIP."""
    fs = FastSelenium(driver, timeout=20)
    elementos = driver.find_elements('xpath', f'//td[contains(@id,"frmAsrSub:date{periodo}DayCell")][normalize-space(text())="{dia_da_coleta}"]')
    for elemento in elementos:
        dia = elemento.text.strip()
        if dia == str(dia_da_coleta):
            print(f'Elemento do dia:{dia}, dia selecionado {dia_da_coleta}, quantidade de elementos {len(elementos)}')
            try:
                elemento.click()
            except Exception as e:
                print("Nem o JS conseguiu clicar, aí é derrota total:", e)
                return False


def selecionar_dia_minutagem_custo(driver, periodo, dia_selecionado):
    '''Seleciona dia do mês atual'''
    fs = FastSelenium(driver, timeout=20)

    xpath = f'//td[contains(@id,"frmCdr:date{periodo}DayCell") and normalize-space()="{dia_selecionado}"]'
    elementos = driver.find_elements('xpath', xpath)

    print(f"=== Buscando dia {dia_selecionado}: {len(elementos)} elementos encontrados ===\n")

    for i, elemento in enumerate(elementos):
        classes = elemento.get_attribute('class') or ""
        elem_id = elemento.get_attribute('id')

        print(f"Elemento [{i}]: ID={elem_id}, Classes={classes}")

        # FILTRO: Apenas dias com rich-calendar-btn E SEM boundary-dates
        if "rich-calendar-btn" in classes and "rich-calendar-boundary-dates" not in classes:
            try:
                time.sleep(0.5)
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elemento)
                time.sleep(0.3)
                driver.execute_script("arguments[0].click();", elemento)
                print(f"✓ Clique executado no elemento [{i}] - dia {dia_selecionado} do mês atual\n")
                return True
            except Exception as e:
                print(f"ERRO ao clicar: {e}")
                continue

    print(f"Nenhum dia válido {dia_selecionado} encontrado\n")
    return False


def login_maxima(driver, user_mail, password):
    '''Simple login function'''
    fs = FastSelenium(driver, timeout=20)
    try:
        # login info
        login = fs.type_text('//*[@id="j_id27:login"]', user_mail)
        # password info
        password = fs.type_text('//*[@id="j_id27:password"]', password)
        # login click
        login_click = fs.click_button('//*[@id="j_id27:j_id28_body"]/table/tbody/tr[3]/td[2]/div/input')
        return 'login heeel yeah'
    except Exception as e:
        print('ops, error', e)

def get_asr_maxima(driver, dia_selecionado):
    '''Function to get data from maximavoip rs'''
    fs = FastSelenium(driver, timeout=20)
    try:
        # clica na opção de asr
        fs.click_button('//*[@id="iconfrmMenu:j_id49"]')
        # selecionar o imput data inicial
        fs.click_button('//*[@id="frmAsrSub:datefromInputDate"]')
        try:
            selecionar_dia(driver, dia_selecionado, 'from')
        except Exception as erro_dia:
            print('Erro ao selecionar o dia', erro_dia)
        # selecionar data final
        fs.click_button('//*[@id="frmAsrSub:datetoInputDate"]')
        selecionar_dia(driver, dia_selecionado,'to')
        time.sleep(1)
        # clicar de novo no calendario
        fs.click_button('//*[@id="frmAsrSub:datetoInputDate"]')
        # clicar em horario
        fs.click_button('//*[@id="frmAsrSub:datetoFooter"]/table/tbody/tr/td[3]/div')
        # digitar hora 23
        hora_final = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#frmAsrSub\\:datetoTimeHours'))
        )
        hora_final.clear()
        hora_final.send_keys("23")
        minuto_final = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#frmAsrSub\\:datetoTimeMinutes'))
        )
        minuto_final.clear()
        minuto_final.send_keys("59")
        #ok
        fs.click_button('//*[@id="frmAsrSub:datetoTimeEditorButtonOk"]/span')
        # ultimo ok
        fs.click_button('//*[@id="frmAsrSub:j_id100"]')
        # pegar os dados que interessam
        chamadas = fs.xpath_data('//*[@id="frmAsrSub:listAsrs:0:j_id113"]')
        # convertendo para texto
        if chamadas:
            # converter para string
            chamadas_texto = chamadas.strip()
            # converte para inteiro
            chamadas = int(chamadas_texto)
        else:
            print("elemento não encontrado")
        return chamadas
    except Exception as erro_asr:
        print('ops, erro durante configuração do asr', erro_asr)

def tratar_dados(minutagem, valor):
    '''função para converter os valores de chamadas e minutagens em float'''
    if minutagem and valor: # verificação basica se os valores existem
        if valor:
            valor = valor.replace(',', '.') # trocar por ponto para facilitar a converção para float
            try:
                valor = round(float(valor), 2) # convertendo para float
            except ValueError:
                print("Valor invalido de minutagem: ", valor)
                valor = 0.0
        else:
            valor = 0.0
        print("Valor: ", valor)

        # convertendo a minutagem para float
        if minutagem:
            minutagem_texto = minutagem.strip(':')
            try:
                h, m, s = map(int, minutagem_texto.split(':'))
                minutagem_float = h * 60 + m + s / 60
                print("Minutagem: ", minutagem_float)
                return minutagem_float, valor
            except ValueError:
                print("Erro no tratamento de minutagem: ", minutagem_texto)
                return False


def get_min_value_maxima_voip(driver, dia_coleta):
    '''Função para coletar os valores de custo e minutagem'''
    fs = FastSelenium(driver, timeout=20)
    # ir até chamadas
    fs.click_button('//*[@id="iconfrmMenu:j_id50"]')
    time.sleep(1)
    # selecionar data inicial
    fs.click_button('//*[@id="frmCdr:datefromInputDate"]')
    time.sleep(1)
    selecionar_dia_minutagem_custo(driver, 'from', dia_coleta)
    fs.click_button('//*[@id="frmCdr:datetoInputDate"]')
    time.sleep(1)
    # selecionar data final
    selecionar_dia_minutagem_custo(driver, 'to', dia_coleta)
    #sair
    fs.click_button('//*[@id="frmCdr:tabFilter"]/table/tbody/tr/td')
    # ok
    fs.click_button('//*[@id="frmCdr:tabFilter"]/table/tbody/tr/td/div/input[2]')
    try:
        minutagem_suja = fs.xpath_data('/html/body/table/tbody/tr[4]/td/table/tbody/tr/td[2]/form/table/tbody/tr[2]/td/table/tbody/tr/td/table[2]/tfoot/tr/td[2]')
        minutagem = minutagem_suja.strip(':')
        valor_sujo = fs.xpath_data('/html/body/table/tbody/tr[4]/td/table/tbody/tr/td[2]/form/table/tbody/tr[2]/td/table/tbody/tr/td/table[2]/tfoot/tr/td[3]')
        valor = valor_sujo.strip()
        print("Minutagem e custo coletados!")
    except ValueError:
        print("Erro durante a coleta de minutagem e custo(ANTES DO TRATAMENTO), tipo de erro: Valores invalidos")
        minutagem_suja = 0.0
        valor_sujo = 0.0
        return False
    return minutagem, valor

def virada_mes_asr(driver):
    """Função simples utilizada apenas para virar o mês
    caso a coleta seja realizada entre os dias 1, 2, 3"""
    fs = FastSelenium(driver, timeout=20)
    # clique para voltar ao mês anterior
    try:
        # clica na opção de asr
        fs.click_button('//*[@id="iconfrmMenu:j_id49"]')
        # selecionar data inicial
        fs.click_button('//*[@id="frmAsrSub:datefromInputDate"]')
        time.sleep(1)
        # seleciona o mês anterior
        fs.click_button('/html/body/table/tbody/tr[4]/td/table/tbody/tr/td[2]/form/table/tbody/tr[2]/td/table/tbody/tr/td/table[1]/tbody/tr[1]/td[2]/div/table/tbody/tr[1]/td/table/tbody/tr/td[2]/div')
        fs.click_button('//*[@id="frmAsrSub:datefromDayCell33"]')
        time.sleep(1)
        # selecionar data final
        fs.click_button('//*[@id="frmAsrSub:datetoInputDate"]')
        time.sleep(1)
        fs.click_button('//*[@id="frmAsrSub:datetoHeader"]/table/tbody/tr/td[2]/div')
        # selecionar ultimo dia do mês
        fs.click_button('//*[@id="frmAsrSub:datetoDayCell33"]')

        # clicar de novo no calendario
        fs.click_button('//*[@id="frmAsrSub:datetoInputDate"]')
        # clicar em horario
        fs.click_button('//*[@id="frmAsrSub:datetoFooter"]/table/tbody/tr/td[3]/div')
        # digitar hora 23
        hora_final = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#frmAsrSub\\:datetoTimeHours'))
        )
        hora_final.clear()
        hora_final.send_keys("23")
        minuto_final = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#frmAsrSub\\:datetoTimeMinutes'))
        )
        minuto_final.clear()
        minuto_final.send_keys("59")
        time.sleep(3)
        #ok
        fs.click_button('//*[@id="frmAsrSub:datetoTimeEditorButtonOk"]/span')
        # ultimo ok
        fs.click_button('//*[@id="frmAsrSub:j_id100"]')
        # pegar os dados que interessam
        chamadas = fs.xpath_data('//*[@id="frmAsrSub:listAsrs:0:j_id113"]')
        # convertendo para texto
        if chamadas:
            # converter para string
            chamadas_texto = chamadas.strip()
            # converte para inteiro
            chamadas = int(chamadas_texto)
            return chamadas
        else:
            print("elemento não encontrado")
        return 0
    except Exception as e:
        print('ops, error', e)

def virada_mes_minutagem_custo(driver):
    '''Função para coletar dados de custo e minutagem
    em viradas de mês'''
    fs = FastSelenium(driver, timeout=20)
    # ir até chamadas
    fs.click_button('//*[@id="iconfrmMenu:j_id50"]')
    time.sleep(1)
    # selecionar data inicial
    fs.click_button('//*[@id="frmCdr:datefromInputDate"]')
    time.sleep(2)
    # seleciona o mês anterior
    fs.click_button('/html/body/table/tbody/tr[4]/td/table/tbody/tr/td[2]/form/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr[1]/td[2]/div/table/tbody/tr[1]/td/table/tbody/tr/td[2]/div')
    # selecionar o ultimo dia do mes
    fs.click_button('//*[@id="frmCdr:datefromDayCell33"]')
    # selecionar data final
    fs.click_button('/html/body/table/tbody/tr[4]/td/table/tbody/tr/td[2]/form/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr[1]/td[4]/div/span/input[1]')
    time.sleep(1)
    # seleciona o mês anterior
    fs.click_button('/html/body/table/tbody/tr[4]/td/table/tbody/tr/td[2]/form/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr[1]/td[4]/div/table/tbody/tr[1]/td/table/tbody/tr/td[2]/div')
    fs.click_button('//*[@id="frmCdr:datetoDayCell33"]')
    # selecionar data maxima
    # sair
    fs.click_button('//*[@id="frmCdr:tabFilter"]/table/tbody/tr/td')
    # ok
    fs.click_button('//*[@id="frmCdr:tabFilter"]/table/tbody/tr/td/div/input[2]')
    try:
        minutagem_suja = fs.xpath_data(
            '/html/body/table/tbody/tr[4]/td/table/tbody/tr/td[2]/form/table/tbody/tr[2]/td/table/tbody/tr/td/table[2]/tfoot/tr/td[2]')
        minutagem = minutagem_suja.strip(':')
        valor_sujo = fs.xpath_data(
            '/html/body/table/tbody/tr[4]/td/table/tbody/tr/td[2]/form/table/tbody/tr[2]/td/table/tbody/tr/td/table[2]/tfoot/tr/td[3]')
        valor = valor_sujo.strip()
        print("Minutagem e custo coletados!")
    except ValueError:
        print("Erro durante a coleta de minutagem e custo(ANTES DO TRATAMENTO), tipo de erro: Valores invalidos")
        minutagem_suja = 0.0
        valor_sujo = 0.0
        return False
    return minutagem, valor


clientes = [

    {'email': os.getenv('INVESTE_MAIS_CONSULTORIA_EMAIL'), 'senha': os.getenv('INVESTE_MAIS_CONSULTORIA_PASSWORD'), 'ID': '1097#01', 'cliente': 'Investe Mais'},
    {'email': os.getenv('ESSENCE_MULTISERVICOS_EMAIL'), 'senha': os.getenv('ESSENCE_MULTISERVICOS_PASSWORD'), 'ID': '1036#01', 'cliente': 'Essence Multiserviços'},
    {'email': os.getenv('APLEXX_EMAIL'), 'senha': os.getenv('APLEXX_PASSWORD'), 'ID': '1065#01', 'cliente': 'Aplexx'},
    {'email': os.getenv('COIN_EMAIL'), 'senha': os.getenv('COIN_PASSWORD'), 'ID': '1955#01', 'cliente': 'Coin'},
    {'email': os.getenv('ASSIS_E_MOLLERKE_EMAIL'), 'senha': os.getenv('ASSIS_E_MOLLERKE_PASSWORD'), 'ID': '1160#1', 'cliente': 'Assis e Mollerke'},
    {'email': os.getenv('QUALITY_ASSESSORIA_EMAIL'), 'senha': os.getenv('QUALITY_ASSESSORIA_PASSWORD'), 'ID': '1270#01', 'cliente': 'Quality Assessoria'},
    {'email': os.getenv('SUPERMED_EMAIL'), 'senha': os.getenv('SUPERMED_PASSWORD'), 'ID': '1469#01', 'cliente': 'Supermed'},
    {'email': os.getenv('VALM_SOLUCOES_EMAIL'), 'senha': os.getenv('VALM_SOLUCOES_PASSWORD'), 'ID': '1596#01', 'cliente': 'V.A.L.M Soluções'},
    {'email': os.getenv('AGS_TELECOM_EMAIL'), 'senha': os.getenv('AGS_TELECOM_PASSWORD'), 'ID': '2261#02', 'cliente': 'AGS Telecom'},
    {'email': os.getenv('STEFANY_OLIVEIRA_EMAIL'), 'senha': os.getenv('STEFANY_OLIVEIRA_PASSWORD'), 'ID': '2115#01', 'cliente': 'Stefany Oliveira'},
    {'email': os.getenv('ZEN_SEGUROS_EMAIL'), 'senha': os.getenv('ZEN_SEGUROS_PASSWORD'), 'ID': '2244#01', 'cliente': 'Zen Seguros'},
    {'email': os.getenv('RECOVERY_EMAIL'), 'senha': os.getenv('RECOVERY_PASSWORD'), 'ID': '2191#01', 'cliente': 'Recovery'},
    {'email': os.getenv('RECOMECAR_EMAIL'), 'senha': os.getenv('RECOMECAR_PASSWORD'), 'ID': '1683#01', 'cliente': 'Recomeçar'},
    {'email': os.getenv('AGUIA_EMAIL'), 'senha': os.getenv('AGUIA_PASSWORD'), 'ID': '1039#03', 'cliente': 'Águia'},
    {'email': os.getenv('DIBRANDES_SOLUCOES_FINANCEIRAS_EMAIL'), 'senha': os.getenv('DIBRANDES_SOLUCOES_FINANCEIRAS_PASSWORD'), 'ID': '1888#01', 'cliente': 'Dibrandes Soluções Financeiras'},
    {'email': os.getenv('ACPRUDENTE_EMAIL'), 'senha': os.getenv('ACPRUDENTE_PASSWORD'), 'ID': '2249#01', 'cliente': 'Acprudente'},
    {'email': os.getenv('DIBRANDES_EMAIL'), 'senha': os.getenv('DIBRANDES_PASSWORD'), 'ID': '1888#01', 'cliente': 'Dibrandes'},
    {'email': os.getenv('MILHOES_EMAIL'), 'senha': os.getenv('MILHOES_PASSWORD'), 'ID': '2282#01', 'cliente': 'Milhões'},
    {'email': os.getenv('DEN01_E_DEN02_FACILE_EMAIL'), 'senha': os.getenv('DEN01_E_DEN02_FACILE_PASSWORD'), 'ID': '2274#01', 'cliente': 'Den01 e Den02 (Facile)'},
    {'email': os.getenv('P_P_FINANCEIRA_EMAIL'), 'senha': os.getenv('P_P_FINANCEIRA_PASSWORD'), 'ID': '2284#01', 'cliente': 'P&P Financeira'},
    {'email': os.getenv('CLUBE_TECNOLOGIA_EMAIL'), 'senha': os.getenv('CLUBE_TECNOLOGIA_PASSWORD'), 'ID': '1596#02', 'cliente': 'Clube Tecnologia'},
    {'email': os.getenv('TC_REPRESENTACAO_EMAIL'), 'senha': os.getenv('TC_REPRESENTACAO_PASSWORD'), 'ID': '1404#01', 'cliente': 'TC Representacao'},
    {'email': os.getenv('THCONSIG_EMAIL'), 'senha': os.getenv('THCONSIG_PASSWORD'), 'ID': '2287#01', 'cliente': 'THconsig'},
    {'email': os.getenv('TOQUIO_EMAIL'), 'senha': os.getenv('TOQUIO_PASSWORD'), 'ID': '1907#01', 'cliente': 'Tóquio'},
    {'email': os.getenv('IGGO_EMAIL'), 'senha': os.getenv('IGGO_PASSWORD'), 'ID': '2245#01', 'cliente': 'Iggo'},
    {'email': os.getenv('RDF_CONSULTORIA_EMAIL'), 'senha': os.getenv('RDF_CONSULTORIA_PASSWORD'), 'ID': '2131#01', 'cliente': 'RDF Consultoria'},
    {'email': os.getenv('GRAFICA_DOIS_IRMAOS_EMAIL'), 'senha': os.getenv('GRAFICA_DOIS_IRMAOS_PASSWORD'), 'ID': '215501#', 'cliente': 'Gráfica Dois Irmãos'},
    {'email': os.getenv('IRON_ASSESSORIA_EMAIL'), 'senha': os.getenv('IRON_ASSESSORIA_PASSWORD'), 'ID': '1146#01', 'cliente': 'Iron Assessoria'},
    {'email': os.getenv('INVEST_MAIS_FACILE_EMAIL'), 'senha': os.getenv('INVEST_MAIS_FACILE_PASSWORD'), 'ID': '2275#01', 'cliente': 'Invest Mais (Facile)'},
    {'email': os.getenv('rx_gestao_empresarial_facile_email'), 'senha': os.getenv('rx_gestao_empresarial_facile_senha'), 'ID': '1086#01', 'cliente': 'RX Gestão Empresarial (Facile)'},
    {'email': os.getenv('rsl_seguros_email'), 'senha': os.getenv('rsl_seguros_senha'), 'ID': '2035#01', 'cliente': 'RSL Seguros'},
    {'email': os.getenv('connection_email'), 'senha': os.getenv('connection_senha'), 'ID': '1790#01', 'cliente': 'Connection'},
    {'email': os.getenv('informa_cred_facile_email'), 'senha': os.getenv('informa_cred_facile_senha'), 'ID': '1705#01', 'cliente': 'Informa Cred (Facile)'},
    {'email': os.getenv('fenice_email'), 'senha': os.getenv('fenice_senha'), 'ID': ' 1773#01', 'cliente': 'Fenice'},
    {'email': os.getenv('rc_email'), 'senha': os.getenv('rc_senha'), 'ID': '2237#01', 'cliente': 'RC'},
    {'email': os.getenv('francisco_facile_email'), 'senha': os.getenv('francisco_facile_senha'), 'ID': '1651#01', 'cliente': 'Francisco (Facile)'},
    {'email': os.getenv('will_cred_facile_email'), 'senha': os.getenv('will_cred_facile_senha'), 'ID': '2204#01', 'cliente': 'Will Cred (Facile)'},
    {'email': os.getenv('cr_financas_email'), 'senha': os.getenv('cr_financas_senha'), 'ID': '2277#01', 'cliente': 'CR Finanças'},
    {'email': os.getenv('hayelli_consultoria_e_venda_email'), 'senha': os.getenv('hayelly_consultoria_e_venda_senha'), 'ID': '1780#01', 'cliente': 'Hayelli Consultoria e Venda'},
    {'email': os.getenv('consultoria_e_solucoes_finance_email'), 'senha': os.getenv('consultoria_e_solucoes_finance_senha'), 'ID': '1102#01', 'cliente': 'Consultoria e Soluções Finance'},
    {'email': os.getenv('intense_consultoria_email'), 'senha': os.getenv('intense_consultoria_senha'), 'ID': '1606#01', 'cliente': 'Intense Consultoria'},
    {'email': os.getenv('luiz_gustavo_email'), 'senha': os.getenv('luiz_gustavo_senha'), 'ID': '2299#01', 'cliente': 'Luiz Gustavo'},
    {'email': os.getenv('over_email'), 'senha': os.getenv('over_senha'), 'ID': '2110#01', 'cliente': 'Over'},
    {'email': os.getenv('LeA_finance_email'), 'senha': os.getenv('LeA_finance_senha'), 'ID': '2290#01', 'cliente': 'L&A Finance'},
    {'email': os.getenv('gab_email'), 'senha': os.getenv('gab_senha'), 'ID': '2300#01', 'cliente': 'Gab'},
    {'email': os.getenv('ferreira_email'), 'senha': os.getenv('ferreira_senha'), 'ID': '2270#02', 'cliente': 'Ferreira'},
    {'email': os.getenv('kleberson_email'), 'senha': os.getenv('kleberson_senha'), 'ID': '1492#01', 'cliente': 'Kleberson'},
    {'email': os.getenv('avante_facile_email'), 'senha': os.getenv('avante_facile_senha'), 'ID': '1665#01', 'cliente': 'Avante'},
    {'email': os.getenv('teste_email'), 'senha': os.getenv('teste_senha'), 'ID': '0002#85', 'cliente': 'Teste Contech'},
    {'email': os.getenv('fenix_thaciene_email'), 'senha': os.getenv('fenix_thaciene_senha'), 'ID': '2304#01', 'cliente': 'Fênix Thaciene'},
    {'email': os.getenv('cred_consig_facile_email'), 'senha': os.getenv('cred_consig_facile_senha'), 'ID': '1720#01', 'cliente': 'Cred Consig (Facile)'},

]

# definir o dia como ontem
hoje = date.today()
dia_semana = hoje.isoweekday()  # dias da semana, começando por 1 = Segunda
ontem_date = hoje - timedelta(days=1)
dias_ate_sabado = (dia_semana - 6) % 7
ultimo_sabado = hoje - timedelta(days=dias_ate_sabado if dias_ate_sabado != 0 else 7)
ontem = ontem_date.day # dia do mês de ontem
sabado = ultimo_sabado.day # dia do mês que foi sabado

dia_selecionado = ontem

url = 'http://cliente.maximavoip.net:8080/SipPulsePortal/pages/login/login.jsf'

dados_gerais_sexta = []
dados_gerais_sabado = []
dados_gerais = []  # dias normais

def coletar_dados(driver, cliente, data_alvo):
    """Coleta todos os dados necessários de um cliente para uma data"""
    print(f"Coletando dados do cliente {cliente['cliente']} para o dia {data_alvo}...")

    minutagem_bruto, valor_bruto = get_min_value_maxima_voip(driver, data_alvo)
    chamadas = get_asr_maxima(driver, data_alvo)
    minutagem, valor = tratar_dados(minutagem_bruto, valor_bruto)

    return {
        'cliente': cliente['cliente'],
        'Chamadas': chamadas,
        'minutagem': minutagem,
        'custo': valor,
    }


if __name__ == '__main__':
    for cliente in clientes:

        print(f"Coleta atual, Cliente: {cliente['cliente']}")

        driver = FastSelenium.run_driver(url)
        sexta, sabado, ontem, dia_semana = select_date()

        login_maxima(driver, cliente.get('email'), cliente.get('senha'))

        # caso seja segunda feira, vai coletar os ultimos dados da ultima semana
        # vai buscar por dados de sexta e de sabado
        if dia_semana == 0:
            print("coletando sexta e sábado")

            # Sexta
            dados = coletar_dados(driver, cliente, sexta)
            dados_gerais_sexta.append(dados)
            print("Dados de sexta coletados.")

            # Sábado
            dados_sabado = coletar_dados(driver, cliente, sabado)
            dados_gerais_sabado.append(dados_sabado)
            print("Dados de sábado coletados.")


        else:
            print("Iniciando coleta de dados comum")
            dados = coletar_dados(driver, cliente, ontem.day)
            dados_gerais.append(dados)
            print("Dados de ontem da Maxima Voip coletados.")

        driver.quit()


    try:
        if dados_gerais_sexta:
            pd.DataFrame(dados_gerais_sexta).to_csv(f'dados_sexta-{sexta}.csv', index=False)
            print("Arquivo de sexta criado.")

        if dados_gerais_sabado:
            pd.DataFrame(dados_gerais_sabado).to_csv(f'dados_sabado-{sabado}.csv', index=False)
            print("Arquivo de sábado criado.")

        if dados_gerais:
            pd.DataFrame(dados_gerais).to_csv(f'dados_dia-{ontem}.csv', index=False)
            print("Arquivo de dias normais criado.")

    except Exception as erro_csv:
        print("Erro ao gerar arquivos CSV:", erro_csv)


