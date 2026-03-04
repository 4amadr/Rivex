from bs4 import BeautifulSoup

class CleaningSoup:
    def passar_para_html(self, sopa):
        sopa_convertida_html = BeautifulSoup(sopa.text, 'html.parser')
        return sopa_convertida_html

    def marcacao_html(self, sopa, html: str):
        marcacao_encontrada = sopa.find(html)
        return marcacao_encontrada.text
    
    def lista_marcacao_html(self, sopa, html: str):
        # vai encontrar todas as marcações e retornar elas dentro de uma lista
        marcacao_encontrada = sopa.find_all(html)
        return marcacao_encontrada

    def encontrar_marcacao_index(self, sopa, html: str, endereco: int):
        marcacao_por_index = sopa.find(html)
        return marcacao_por_index
    
    
    def marcacao_html_com_classe(self, sopa, html:str, classe):
        classe_encontrada = sopa.find(html, class_=classe)
        return classe_encontrada

    def marcacao_html_com_classe_index(self, sopa, html: str, classe: str, index: int):
        marcacoes = sopa.find_all(html, class_=classe)
        return marcacoes[index]
    
    
    def lista_marcacao_html_com_classe(self, sopa, html:str, classe):
        classe_encontrada = sopa.find_all(html, class_=classe)
        return classe_encontrada
    
    def marcacao_html_com_id(self, sopa, html:str, identificador):
        id_encontrado = sopa.find(html, id=identificador)
        return id_encontrado.text
    
    
    def lista_marcacao_html_com_id(self, sopa, html:str, identificador):
        id_encontrado = sopa.find_all(html, id=identificador)
        return id_encontrado
    
    def encontrar_td_depois_de_th(self, sopa, texto: str):
        # para classes que mudam, mas que mantém a estrutura
        for th in sopa.find_all('th'):
            if texto in th.ged_text():
                td = th.find_text_sibling("td")
                return td.get_text(strip=True)
            
    def classes_dinamicas(self, sopa, marcacao: str, classe: str):
        # para classes que tem um prefixo definido e o resto é indefinido
        sopa.find_all(
            marcacao,
            class_=lambda c: c and c.startswith(classe)
        )