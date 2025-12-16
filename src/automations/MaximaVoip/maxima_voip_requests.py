import requests
from bs4 import BeautifulSoup
import datetime


class maximaVoip:
    def __init__(self, url_padrao, url_login, asr_url):
        self.url_padrao = url_padrao
        self.url_login = url_login
        self.asr_url = asr_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    def get_viewstate(self, conteudo_html):
        '''função para pegar o viewstate para segurança'''
        soup = BeautifulSoup(conteudo_html, 'html.parser')
        inp = soup.find('input', {'name': 'javax.faces.ViewState'})
        if inp:
            return inp.get('value')
        return None

    def login_maximavoip(self, email, senha):
        '''login para pegar o token'''
        print('logando maxima voip')
        login_get = self.session.get(self.url_login)
        viewstate_login = self.get_viewstate(login_get.text)

        if not viewstate_login:
            print('Viewstate não encontrado, site foda ou atualizado')
            return False

        login_payload = {
            'j_id27': 'j_id27',
            'j_id27:login': email,
            'j_id27:password': senha,
            'j_id27:j_id42': 'Acessar Portal',
            'javax.faces.ViewState': viewstate_login
        }

        print('Enviando credenciais')
        login_post = self.session.post(self.url_login, data=login_payload)

        if "SipPulsePortal/pages/login/login.jsf" in login_post.url and "erro" in login_post.text.lower():
            print('login falhou')
            return False
        print('Logado no maxima voip')
        return True

    def asr_token(self, cliente):
        '''função para o asr'''
        print(f'Entrando no relatório de asr do cliente {cliente}')
        response_asr_page = self.session.get(self.asr_url)
        view_state_asr = self.get_viewstate(response_asr_page.text)

        if not view_state_asr:
            print('Falha na coleta do viewstate verifique o login')
            return None

        print('Coletando dados...')
        asr_payload = {
            'AJAXREQUEST': '_viewRoot',
            'frmAsrSub:datefromInputDate': '26/11/2025 00:00',
            'frmAsrSub:datefromInputCurrentDate': '11/2025',
            'frmAsrSub:datetoInputDate': '26/11/2025 18:27',
            'frmAsrSub:datetoInputCurrentDate': '11/2025',
            'frmAsrSub:pagination': '50',
            'frmAsrSub:filterData': '',
            'frmAsrSub': 'frmAsrSub',
            'autoScroll': '',
            'javax.faces.ViewState': view_state_asr,
            'frmAsrSub:j_id100': 'frmAsrSub:j_id100'
        }

        response_data = self.session.post(self.asr_url, data=asr_payload)
        print(response_data.status_code)
        return response_data

    def limpeza_de_dados(self, response_data):
        '''Função para limpar os dados pós coleta'''
        print('Iniciando limpeza de dados...')

        soup_xml = BeautifulSoup(response_data.text, 'lxml-xml')

        # busca atualizações na tabela
        update_tag = soup_xml.find(id="frmAsrSub:panelDados")

        if update_tag:
            html_tabela = update_tag.text
            soup_tabela = BeautifulSoup(html_tabela, 'html.parser')

            linhas = soup_tabela.find_all('tr')
            dados_completos = []
            for linha in linhas:
                colunas = linha.find_all('td')
                dados = [c.text.strip() for c in colunas]
                if dados:  # Só adiciona se tiver dados
                    dados_completos.append(dados)
                    print(dados)
            return dados_completos
        else:
            print('Sem tabela, verifique o payload')
            print(response_data.text[:500])
            return None

if __name__ == '__name__':
    mv = maximaVoip(
        url_padrao='http://cliente.maximavoip.net:8080/SipPulsePortal',
        url_login='http://cliente.maximavoip.net:8080/SipPulsePortal/pages/login/login.jsf',
        asr_url='http://cliente.maximavoip.net:8080/SipPulsePortal/pages/reports/asrsubscriber.jsf',
    )

    get
