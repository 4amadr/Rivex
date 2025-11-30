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
from webdriver_manager.core import driver
from selenium import webdriver

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

def get_asr_maxima(driver):
    '''Function to get data from maximavoip rs'''
    fs = FastSelenium(driver, timeout=20)
    try:
        # clica na opção de asr
        fs.click_button('//*[@id="iconfrmMenu:j_id49"]')
        # selecionar o imput data inicial
        fs.click_button('//*[@id="frmAsrSub:datefromInputDate"]')
        fs.click_button('//*[@id="frmAsrSub:datefromDayCell24"]')
        # selecionar data final
        fs.click_button('//*[@id="frmAsrSub:datetoInputDate"]')
        fs.click_button('//*[@id="frmAsrSub:datetoDayCell24"]')
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
            chamadas = chamadas_texto
        else:
            print("elemento não encontrado")
        return chamadas
    except Exception as e:
        print('ops, error', e)


def tratar_dados(minutagem_texto, valor_texto):
    '''
    Função que realmente converte as coisas em vez de só fingir.
    Retorna: (float, float) -> (minutagem_em_minutos, valor_em_reais)
    '''
    # === Tratamento do Valor (R$) ===
    valor_final = 0.0
    if valor_texto:
        # Troca vírgula por ponto e tenta converter. Se falhar, é zero.
        # O replace é seguro, se já for ponto, não faz mal.
        try:
            limpo = str(valor_texto).replace(',', '.').replace('R$', '').strip()
            valor_final = round(float(limpo), 2)
        except ValueError:
            print(f"⚠️ Valor inválido encontrado: {valor_texto}. Assumindo 0.0")
            valor_final = 0.0

    # === Tratamento da Minutagem (HH:MM:SS) ===
    minutagem_final = 0.0
    if minutagem_texto:
        try:
            # Remove espaços e sujeira
            t = str(minutagem_texto).strip()
            # Quebra em H, M, S
            h, m, s = map(int, t.split(':'))
            # Converte tudo para minutos (float)
            minutagem_final = h * 60 + m + (s / 60)
            # Arredonda pra ficar bonito no Excel depois
            minutagem_final = round(minutagem_final, 2)
        except Exception as e:
            print(f"⚠️ Erro ao converter minutagem '{minutagem_texto}': {e}")
            minutagem_final = 0.0

    print(f"   -> Dados Tratados: {minutagem_final} min | R$ {valor_final}")
    return minutagem_final, valor_final

def get_min_value_maxima_voip(driver):
    '''Função para coletar os valores de custo e minutagem'''
    fs = FastSelenium(driver, timeout=20)
    # ir até chamadas
    fs.click_button('//*[@id="iconfrmMenu:j_id50"]')
    time.sleep(1)
    # selecionar data inicial
    fs.click_button('//*[@id="frmCdr:datefromInputDate"]')
    time.sleep(1)
    fs.click_button('//*[@id="frmCdr:datefromDayCell24"]')
    #selecionar_dia(driver, 'from')
    fs.click_button('//*[@id="frmCdr:datetoInputDate"]')
    time.sleep(1)
    # selecionar data final
    fs.click_button('//*[@id="frmCdr:datetoDayCell24"]')
    #sair
    fs.click_button('//*[@id="frmCdr:tabFilter"]/table/tbody/tr/td')
    # ok
    fs.click_button('//*[@id="frmCdr:tabFilter"]/table/tbody/tr/td/div/input[2]')
    #minutagem = fs.coletar_dados_com_seletor_css('#frmCdr\\:listCdrsTotal\:j_id128')
    #valor = fs.coletar_dados_com_seletor_css('#frmCdr\\:listCdrsTotal\:j_id131')
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



clientes = [

    {'email': os.getenv('INVESTE_MAIS_CONSULTORIA_EMAIL'), 'senha': os.getenv('INVESTE_MAIS_CONSULTORIA_PASSWORD'), 'ID': '1097#01', 'cliente': 'Investe Mais Consultoria'},
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
    {'email': os.getenv('avante_facile_email'), 'senha': os.getenv('avante_facile_senha'), 'ID': '1665#01', 'cliente': 'Avante (Facile)'},
    {'email': os.getenv('teste_email'), 'senha': os.getenv('teste_senha'), 'ID': '0002#85', 'cliente': 'Teste Contech'},
    {'email': os.getenv('fenix_thaciene_email'), 'senha': os.getenv('fenix_thaciene_senha'), 'ID': '2304#01', 'cliente': 'Fênix Thaciene'},
    {'email': os.getenv('cred_consig_facile_email'), 'senha': os.getenv('cred_consig_facile_senha'), 'ID': '1720#01', 'cliente': 'Cred Consig (Facile)'},

]


url = 'http://cliente.maximavoip.net:8080/SipPulsePortal/pages/login/login.jsf'
dados = []

for cliente in clientes:
    try:
        driver = FastSelenium.run_driver(url)
        print(f"Coletando dados do cliente {cliente['cliente']}")

        login_maxima(driver, cliente.get('email'), cliente.get('senha'))

        chamadas = get_asr_maxima(driver)
        minutagem_texto, custo_texto = get_min_value_maxima_voip(driver)
        minutagem, custo = tratar_dados(minutagem_texto, custo_texto)

        dados.append({
            'Cliente': cliente['cliente'],
            'Chamadas': int(chamadas) if chamadas is not None else 0,
            'Minutagem': str(minutagem),
            'Custo': str(custo)
        })
    except Exception as e:
        print(f"Erro ao processar cliente {cliente['cliente']}: {e}")
    finally:
        if driver:
            driver.quit()

df = pd.DataFrame(dados)
df.to_csv('dados_clientes.csv', sep=';', index=False, encoding='utf-8-sig')

print("CSV gerado com sucesso.")
