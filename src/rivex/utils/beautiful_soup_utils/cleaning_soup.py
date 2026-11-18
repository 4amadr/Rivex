from bs4 import BeautifulSoup

class CleaningSoup:
    def passar_para_html(self, sopa):
        sopa_convertida_html = BeautifulSoup(sopa.text, 'html.parser')
        return sopa_convertida_html