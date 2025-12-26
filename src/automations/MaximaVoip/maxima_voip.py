import os
from src.utils.fast_selenium import FastSelenium
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from datetime import timedelta
from datetime import date
from dotenv import load_dotenv
import pandas as pd

load_dotenv()



def selecionar_dia(driver, data_desejada, periodo):
    """Seleciona uma data no calendário do Maxima VoIP."""
    fs = FastSelenium(driver, timeout=20)

    hoje = date.today()
    precisa_voltar_mes = (data_desejada.month != hoje.month or data_desejada.year != hoje.year)

    if precisa_voltar_mes:
        try:
            botao_voltar = f'//*[@id="frmAsrSub:date{periodo}Header"]/table/tbody/tr/td[2]/div'
            fs.click_button(botao_voltar)
            print(f"Voltando mês para selecionar {data_desejada}")
            time.sleep(1.5)
        except Exception as e:
            print(f"Erro ao voltar mês:", e)
            return False

    dia_da_coleta = data_desejada.day

    # XPath que EXCLUI boundary-dates (dias de outros meses)
    xpath_dia_correto = f'//td[contains(@id,"frmAsrSub:date{periodo}DayCell")][normalize-space(text())="{dia_da_coleta}"][contains(@class,"rich-calendar-btn")]'

    try:
        print(f"=== Aguardando dia {data_desejada} estar disponível no DOM ===")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, xpath_dia_correto))
        )
    except Exception as erro_espera:
        print(f'Timeout aguardando o dia {dia_da_coleta} aparecer.')
        return False

    # Buscar apenas elementos com rich-calendar-btn (dias do mês correto)
    elementos = driver.find_elements('xpath', xpath_dia_correto)

    print(f"=== Buscando dia {data_desejada}: {len(elementos)} elementos encontrados ===")

    for elemento in elementos:
        dia = elemento.text.strip()
        if dia == str(dia_da_coleta):
            print(f'Clicando no dia correto: {dia} (data: {data_desejada})')
            try:
                driver.execute_script("arguments[0].scrollIntoView(true);", elemento)
                time.sleep(0.3)
                elemento.click()
                print(f"✓ Dia {data_desejada} selecionado com sucesso!")
                return True
            except Exception as erro_clique:
                print(f'Erro ao clicar:', erro_clique)
                try:
                    driver.execute_script("arguments[0].click();", elemento)
                    print(f"✓ Dia {data_desejada} selecionado via JS!")
                    return True
                except Exception as erro_js:
                    print(f"Erro no JS click:", erro_js)
                    return False

    print(f"Nenhum dia válido {data_desejada} encontrado")
    return False


def selecionar_dia_minutagem_custo(driver, data_desejada, periodo):
    '''Seleciona dia no calendário, voltando mês se necessário'''
    from datetime import date, timedelta

    fs = FastSelenium(driver, timeout=20)

    # Converter para date se for string ou int
    if isinstance(data_desejada, (int, str)):
        # Se passou só o dia, calcular ontem
        data_ontem = date.today() - timedelta(days=1)
        dia_selecionado = int(data_desejada)
        data_desejada = data_ontem  # usar data de ontem para verificar mês
    else:
        # Já é um objeto date
        dia_selecionado = data_desejada.day

    hoje = date.today()
    precisa_voltar_mes = (data_desejada.month != hoje.month or data_desejada.year != hoje.year)

    if precisa_voltar_mes:
        try:
            botao_voltar = f'//*[@id="frmCdr:date{periodo}Header"]/table/tbody/tr/td[2]/div'
            fs.click_button(botao_voltar)
            print(f"Voltando mês para selecionar {data_desejada}")
            time.sleep(1.5)
        except Exception as e:
            print(f"Erro ao voltar mês:", e)
            return False

    # XPath que filtra apenas dias do mês correto
    xpath_dia_correto = f'//td[contains(@id,"frmCdr:date{periodo}DayCell")][normalize-space(text())="{dia_selecionado}"][contains(@class,"rich-calendar-btn")]'

    try:
        print(f"=== Aguardando dia {data_desejada} estar disponível no DOM ===")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, xpath_dia_correto))
        )
    except Exception as erro_espera:
        print(f'Timeout aguardando o dia {dia_selecionado} aparecer.')
        return False

    elementos = driver.find_elements('xpath', xpath_dia_correto)

    print(f"=== Buscando dia {data_desejada}: {len(elementos)} elementos encontrados ===\n")

    for i, elemento in enumerate(elementos):
        classes = elemento.get_attribute('class') or ""
        elem_id = elemento.get_attribute('id')

        print(f"Elemento [{i}]: ID={elem_id}, Classes={classes}")

        if "rich-calendar-btn" in classes and "rich-calendar-boundary-dates" not in classes:
            try:
                time.sleep(0.5)
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elemento)
                time.sleep(0.3)
                driver.execute_script("arguments[0].click();", elemento)
                print(f"✓ Clique executado no elemento [{i}] - dia {data_desejada} selecionado\n")
                return True
            except Exception as e:
                print(f"ERRO ao clicar: {e}")
                continue

    print(f"Nenhum dia válido {data_desejada} encontrado\n")
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

def get_asr_maxima(driver, dia_selecionado, hoje):
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
        selecionar_dia(driver, dia_selecionado, 'to')
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
            chamadas = 0
        return chamadas
    except Exception as erro_asr:
        print('ops, erro durante configuração do asr', erro_asr)


def tratar_dados(minutagem, valor):
    '''função para converter os valores de chamadas e minutagens em float'''

    # Se não houver dados válidos, retorna zeros
    if not minutagem or not valor:
        print("Dados inválidos recebidos. Minutagem ou valor ausente.")
        return 0.0, 0.0

    # Processar valor
    try:
        valor = valor.replace(',', '.')
        valor = round(float(valor), 2)
    except (ValueError, AttributeError):
        print(f"Valor inválido de custo: {valor}")
        valor = 0.0

    # Processar minutagem
    try:
        minutagem_texto = minutagem.strip(':')
        h, m, s = map(int, minutagem_texto.split(':'))
        minutagem_float = h * 60 + m + s / 60
        print(f"Minutagem: {minutagem_float}, Valor: {valor}")
        return minutagem_float, valor
    except (ValueError, AttributeError):
        print(f"Erro no tratamento de minutagem: {minutagem}")
        return 0.0, valor  # Retorna valor processado mesmo se minutagem falhar


def get_min_value_maxima_voip(driver, dia_coleta, hoje):
    '''Função para coletar os valores de custo e minutagem'''
    fs = FastSelenium(driver, timeout=20)
    # ir até chamadas
    fs.click_button('//*[@id="iconfrmMenu:j_id50"]')
    time.sleep(1)
    # selecionar data inicial
    fs.click_button('//*[@id="frmCdr:datefromInputDate"]')
    # voltar o mês
    time.sleep(1)
    selecionar_dia_minutagem_custo(driver, dia_coleta, 'from')

    fs.click_button('//*[@id="frmCdr:datetoInputDate"]')
    time.sleep(1)
    # selecionar data final
    selecionar_dia_minutagem_custo(driver, dia_coleta, 'to')
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

clientes_teste = [
{'email': os.getenv('AGS_TELECOM_EMAIL'), 'senha': os.getenv('AGS_TELECOM_PASSWORD'), 'ID': '2261#02', 'cliente': 'AGS Telecom'},
{'email': os.getenv('IGGO_EMAIL'), 'senha': os.getenv('IGGO_PASSWORD'), 'ID': '2245#01', 'cliente': 'Iggo'}
]
# definir o dia como ontem
hoje = date.today()
dia_semana = hoje.isoweekday()  # dias da semana, começando por 1 = Segunda

# calculo de datas completas
ontem_date = hoje - timedelta(days=1)
dias_ate_sabado = (dia_semana - 6) % 7
ultimo_sabado = hoje - timedelta(days=dias_ate_sabado if dias_ate_sabado != 0 else 7)
ultima_sexta = ultimo_sabado - timedelta(days=1)  # sexta é 1 dia antes do sábado
ontem = ontem_date.day # dia do mês de ontem
sabado = ultimo_sabado.day # dia do mês que foi sabado
dia_selecionado = ontem

url = 'http://cliente.maximavoip.net:8080/SipPulsePortal/pages/login/login.jsf'

dados_gerais_sexta = []
dados_gerais_sabado = []
dados_gerais = []  # dias normais


def coletar_dados(driver, cliente, data_inicio, data_fim):
    """Coleta todos os dados necessários de um cliente para uma data

    Args:
        data_inicio: objeto date com a data a ser consultada
        data_fim: objeto date com a data final do período (geralmente a mesma data)
    """
    print(f"DEBUG: Coletando de {data_inicio} até {data_fim}")
    print(f"Coletando dados do cliente {cliente['cliente']} para o dia {data_inicio.strftime('%d/%m/%Y')}...")

    minutagem_bruto, valor_bruto = get_min_value_maxima_voip(driver, data_inicio, data_fim)
    if minutagem_bruto == '00:00:00': # se não teve minutagem não teve consumo
        chamadas = 0
        print(f'cliente {cliente["cliente"]} zerado. Pulando')
        driver.quit()
        return 0, 0
    else:
        chamadas = get_asr_maxima(driver, data_inicio, data_fim)
        minutagem, valor = tratar_dados(minutagem_bruto, valor_bruto)

    dados = {
        'Data': data_inicio.strftime('%d/%m/%Y'),
        'cliente': cliente['cliente'],
        'Chamadas': chamadas,
        'minutagem': minutagem,
        'custo': valor,
    }
    print(dados)

    return dados


if __name__ == '__main__':
    for cliente in clientes:

        print(f"Coleta atual, Cliente: {cliente['cliente']}")

        driver = FastSelenium.run_driver(url)

        login_maxima(driver, cliente.get('email'), cliente.get('senha'))

        # caso seja segunda feira, vai coletar os ultimos dados da ultima semana
        # vai buscar por dados de sexta e de sabado
        if dia_semana == 1:  # CORRIGIDO: segunda é 1, não 0
            print("É segunda-feira! Coletando sexta e sábado")

            # Sexta
            dados = coletar_dados(driver, cliente, ultima_sexta, ultima_sexta)
            dados_gerais_sexta.append(dados)
            print("Dados de sexta coletados.")

            # Sábado
            dados_sabado = coletar_dados(driver, cliente, ultimo_sabado, ultimo_sabado)
            dados_gerais_sabado.append(dados_sabado)
            print("Dados de sábado coletados.")

        else:
            print("Iniciando coleta de dados comum")
            dados = coletar_dados(driver, cliente, ontem_date, ontem_date)
            dados_gerais.append(dados)
            print("Dados de ontem da Maxima Voip coletados.")

        driver.quit()

    try:
        if dados_gerais_sexta:
            pd.DataFrame(dados_gerais_sexta).to_csv(f'dados_sexta-{ultima_sexta.day}.csv', index=False)
            print("Arquivo de sexta criado.")

        if dados_gerais_sabado:
            pd.DataFrame(dados_gerais_sabado).to_csv(f'dados_sabado-{ultimo_sabado.day}.csv', index=False)
            print("Arquivo de sábado criado.")

        if dados_gerais:
            pd.DataFrame(dados_gerais).to_csv(f'dados_dia-{ontem_date.day}.csv', index=False)
            print("Arquivo de dias normais criado.")

    except Exception as erro_csv:
        print("Erro ao gerar arquivos CSV:", erro_csv)

