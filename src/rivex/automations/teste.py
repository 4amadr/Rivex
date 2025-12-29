from datetime import timedelta, date
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

from rivex.automations.MaximaVoip.maxima_voip import login_maxima


class SipPulseConnector:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "http://cliente.maximavoip.net:8080/SipPulsePortal/pages/login/login.jsf"
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Origin': 'http://cliente.maximavoip.net:8080',
            'Referer': self.base_url,  # Avisa que viemos da própria página de login
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Content-Type': 'application/x-www-form-urlencoded'
        })
    def get_viewstate(self, url=None):
        # url opicional, se não houver url vai usar a de login
        if url is None:
            url = self.base_url

        response = self.session.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        inputs = soup.find_all('input')

        id_form = None
        botao_login = None
        for input in inputs:
            nome_input = input.get('name')
            login_input = input.get('value')
            print(nome_input)
            if nome_input.endswith('login'):
                print('login aqui ',nome_input)
                partes = nome_input.split(':')
                id_form = partes[0]
            elif login_input and login_input.endswith('Connect'):
                botao_login = nome_input
                print('Botão aqui ', botao_login)

        viewstate = soup.find('input', id="javax.faces.ViewState")
        if viewstate:
            return {
                'viewstate': viewstate.get('value') if viewstate else None,
                'id_form': id_form,
                'botao_login': botao_login
            }
        else:
            print("ALERTA: ViewState não encontrado! Salvando HTML para análise...")
            with open("pagina_erro.html", "w", encoding="utf-8") as f:
                f.write(soup.prettify())
        return None

    def login_maximavoip(self, email, senha, usuario):
        # token de segurança atualizado
        dados_pagina = self.get_viewstate()

        if not dados_pagina:
            print('Erro, não conseguimos mapear a pagina de login')
            return False

        viewstate = dados_pagina['viewstate']
        id_form = dados_pagina['id_form']
        botao_login = dados_pagina['botao_login']

        payload = {
            id_form: id_form,
            f'{id_form}:login': email, # email
            f'{id_form}:password': senha, # senha
             botao_login: 'Connect',
            'javax.faces.ViewState': viewstate,
        }

        print(f'Enviando login para {email}')


        resposta = self.session.post(self.base_url, data=payload)
        if "logoff" not in resposta.url:
            print(f'Login SUCESSO! Redirecionado para: {resposta.url}')
            return True
        else:
            print(f'Login FALHOU. Continuamos na página de login.')
            print("Salvando página de erro para análise: erro_login.html")
            with open("erro_login.html", "w", encoding="utf-8") as f:
                f.write(resposta.text)
            return False


    def buscar_chamadas(self, data_inicio, data_fim):
        url = "http://cliente.maximavoip.net:8080/SipPulsePortal/pages/reports/asrsubscriber.jsf"

        # debug temporário
        print('Pagina de relatórios')
        resposta_relatorio = self.session.get(url)
        with open("pagina_relatorio.html", "w", encoding="utf-8") as f:
            f.write(resposta_relatorio.text)
        print('HTML do relatório salva')

        viewstate = self.get_viewstate(url)

        if not viewstate:
            print(f'Erro: viewstate não encontrado na url {url}')
            return None
        viewstate_token = viewstate['viewstate']
        payload = {
            'frmCdr': 'frmCdr',
            'frmCdr:panelDados': 'tabFilter',
            'frmAsrSub:datefromInputDate': data_inicio,
            'frmAsrSub:datetoInputDate': data_fim,
            'frmCdr:j_id101': 'Gerar Relatório',
            'javax.faces.ViewState': viewstate_token
        }
        print(f'Buscando dados no periodo {data_inicio} - {data_fim}')
        resposta = self.session.post(url, data=payload)

        print(f"DEBUG GET ViewState: Status {resposta.status_code} | URL: {resposta.url}")

        return resposta.text

    def processar_dados(self, html_content):
        '''função para limpar o HTML da página coletada'''
        from io import StringIO
        html_io = StringIO(html_content)
        dfs = pd.read_html(html_io, match='Duração', header=1)

        return dfs

if __name__ == '__main__':
    clientes = [
        {'email': os.getenv('AGS_TELECOM_EMAIL'), 'senha': os.getenv('AGS_TELECOM_PASSWORD'), 'ID': '2261#02',
         'cliente': 'AGS Telecom'},
        {'email': os.getenv('IGGO_EMAIL'), 'senha': os.getenv('IGGO_PASSWORD'), 'ID': '2245#01', 'cliente': 'Iggo'}
    ]

    sipp = SipPulseConnector()
    hoje = date.today()
    ontem = hoje - timedelta(days=1)
    data_inicio = ontem.strftime('%d/%m/%Y')
    data_fim = data_inicio

    dados_clientes = []

    for cliente in clientes:
        print(f'\nIniciando coleta de dados para o cliente {cliente["cliente"]}')
        login = sipp.login_maximavoip(cliente['email'], cliente['senha'], cliente['cliente'])
        if not login:
            print(f'login no cliente {cliente["cliente"]} falhou, passando para o próximo')
            continue
        chamadas = sipp.buscar_chamadas(data_inicio, data_fim)
        dataframe = sipp.processar_dados(chamadas)
        dados_clientes.append(dataframe)

        print(f'Coleta finalizada para o cliente {cliente["cliente"]}')
if dados_clientes:
    df_final = pd.concat(dados_clientes)
    data_arquivo = data_inicio.replace('/', '-')
    df_final.to_csv(f'clientes_{data_arquivo}.csv', index=False)
else:
    print('Nenhum dado foi coletado. Verifique os erros de login.')