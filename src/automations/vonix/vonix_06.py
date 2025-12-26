from src.utils.fast_selenium import FastSelenium
import time


def vonix_login(driver, user, password, number_vonix):
    fs = FastSelenium(driver, timeout=20)
    try:
        #user
        fs.type_text('//*[@id="username"]', user)
        #password
        fs.type_text('//*[@id="password"]', password)
        # wait until user and password get tiped
        fs.click_button('//*[@id="wrapper"]/div/form/dl/dd[3]/input')
        print(f'Logado no VONIX {number_vonix}!')
        return True
    except Exception as e:
        print(f'Erro durante o Login no vonix {number_vonix}, type error: {e}')
        return False

def choose_vonix_client(driver):
    '''Function to choose the client and the tean in vonix'''
    # list with all teans
    all_teans_list = []
    equipes_ativas = []
    fs = FastSelenium(driver, timeout=20)
    fs.click_button('//*[@id="select_queues"]')
    # aqui eu pego todas as equipes na lista de equipes para filtrar apenas as equipes ativas
    teans = driver.find_elements('xpath', '//*[@id="queues_menu"]/li')
    for tean in teans:
        time_nome = tean.text
        all_teans_list.append((time_nome, tean))
    equipes_desativadas = ['z00', 'zdisponivel', 'manual', 'disponivel', 'disponive', 'zz', 'selecionar', 'teste',
                               'inativos', '00']
    for equipe, elemento_equipe in all_teans_list:
        texto = equipe.lower()
        if not any(palavra in texto for palavra in equipes_desativadas):
            equipes_ativas.append((equipe, elemento_equipe))
            print('Equipes ativas atualmente: ', equipe)
    try:

        for tamanho, (equipe_nome, elemento) in enumerate(equipes_ativas): # iterate the list for get any data with clients
            print(f'Processando... {equipe_nome}')
            # click in performance option
            fs.click_button('//*[@id="maintabs"]/li[4]/a')
            # abrir o menu suspenso de clientes
            fs.click_button('//*[@id="select_queues"]')

            # aqui o clique duplo é para remover todos os clientes
            fs.click_button('//*[@id="queues_menu"]/li[1]/a/label')
            #fs.click_button('//*[@id="queues_menu"]/li[1]/a/label/i')
            # selecionar apenas a equipe iterada
            elemento_atualizado = driver.find_element('xpath', f'//*[@id="queues_menu"]/li[contains(., "{equipe_nome}")]')
            elemento_atualizado.click()
            time.sleep(3)
            # clique em um campo vazio para atualizar a lista de clientes
            fs.click_button('//*[@id="search"]')
            # aqui vou adicionar um tratamento de erros para lidar com páginas vazias
            # se há data, se esse campo não aparecer a automação deve ignorar o cliente e seguir para o próximo
            campo_data = fs.xpath_data('//*[@id="maincontent"]/table/tbody/tr[10]/th[2]')
            if not campo_data:
                print(f'Campos em branco para o cliente {equipe_nome} !!')
                return None
            else:
                print(f'cliente selecionado!, {equipe_nome}')
                # find yersterday data
                date = fs.xpath_data_com_tratamento('//*[@id="maincontent"]/table/tbody/tr[10]/th[3]')
                todas_as_chamadas_brutas = fs.xpath_data_com_tratamento('//*[@id="maincontent"]/table/tbody/tr[12]/td[3]')
                completadas_brutas = fs.xpath_data_com_tratamento('//*[@id="maincontent"]/table/tbody/tr[13]/td[3]')
                fracasadas_brutas = fs.xpath_data_com_tratamento('//*[@id="maincontent"]/table/tbody/tr[14]/td[3]')
                abandonadas_brutas = fs.xpath_data_com_tratamento('//*[@id="maincontent"]/table/tbody/tr[15]/td[3]')

                # vou passar os dados para str para poder ser tratados posteriormente
                all_calls = str(todas_as_chamadas_brutas)
                finished_calls = str(completadas_brutas)
                fail_calls = str(fracasadas_brutas)
                abandoned_calls = str(abandonadas_brutas)

        # dicionário para armazenar os valores
        calls_data = {
            'date': equipe_nome,
            'all_calls': all_calls,
            'finished_calls': finished_calls,
            'fail_calls': fail_calls,
            'abandoned_calls': abandoned_calls,
        }
        print(calls_data)
        return calls_data
    except Exception as e:
        print(f"Erro durante a coleta de dados do Vonix {number_vonix}: {e}!!!!!!!!")
        return False

def agregar_equipes(driver, number_vonix, calls_data):
    '''Função para agregar dados do Vonix
    caso as equipes sejam do mesmo cliente'''
    equipes_iguais = []
    try:

        for time in calls_data:
            equipes_iguais.append(calls_data[time]['equipe'])
            print(equipes_iguais)
            return equipes_iguais
    except Exception as e:
        print(f"Erro ao agregar dados no Vonix {number_vonix}, type error: {e}")
        return False

user = 'victor.amador'
password = '1801'
url = 'http://contech6.vonixcc.com.br/'
number_vonix = 6

if __name__ == '__main__':
    driver = FastSelenium.run_driver(url)
    vonix_login(driver, user, password, number_vonix)
    calls_data = choose_vonix_client(driver)
    agregar_equipes(driver, number_vonix, calls_data)
# em desenvolvimento...
