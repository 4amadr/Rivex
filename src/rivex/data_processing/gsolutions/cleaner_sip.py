from bs4 import BeautifulSoup
import json
import re 
import logging
from pandas.io.formats.format import return_docstring

log = logging.getLogger(__name__)

class CleanerSip:
    def __init__(self, consumo, id_clientes):
        self.consumo = consumo
        self.id_clientes = id_clientes

    def gerar_tabela_consumo(self):
        sopa = BeautifulSoup(self.consumo, "html.parser")
        tabela = sopa.find("div", id="site")
        return tabela

    
    def gerar_clientes(self, tabela):
        tr_dados = tabela.find_all("tr", class_=["cinza1", "cinza2"])
        lista_clientes = []
        for tr in tr_dados:
            td_cliente = tr.find("td", attrs={"align": "left"})
            if td_cliente:
                lista_clientes.append(td_cliente.text.strip())
        return lista_clientes
    
    def gerar_minutagem(self, tabela):
        minutagem = [] 

        tr_dados = tabela.find_all("tr", class_=["cinza1", "cinza2"])

        for tr in tr_dados:
            tds = tr.find_all("td")

            if len(tds) >= 3:
                valor = tds[2].text.strip()

                try:
                    float(valor.replace(".", "").replace(",", "."))
                    minutagem.append(valor)
                except ValueError:
                    log.warning("Alteração na coluna de minutagem na agitel. Requer modificação!")
                    continue
        return minutagem

    def gerar_custos(self, tabela):
        custos = []

        tr_dados = tabela.find_all("tr", class_=["cinza1", "cinza2"])

        for tr in tr_dados:
            tds = tr.find_all("td")

            if len(tds) >= 4:
                valor = tds[3].get_text(strip=True)

                try:
                    float(valor.replace(".", "").replace(",", "."))
                    custos.append(valor)
                except ValueError:
                    log.warning("Alteração na tabela de custos. Requer verificação no processamento de dados")
                    continue

        return custos
    
    def clean_id(self):
        dados = json.loads(self.id_clientes)
        lista_id = [identificador["id"] for identificador in dados if identificador]
        lista_clientes = [identificador["value"] for identificador in dados if identificador]
    



    
    def limpar_consumo(self):
        tabela = self.gerar_tabela_consumo()
        cliente = self.gerar_clientes(tabela)
        minutagem = self.gerar_minutagem(tabela)
        custo = self.gerar_custos(tabela)

        print(cliente)
        print(minutagem)
        print(custo)
        return cliente, minutagem, custo
    
    def gerar_chamadas_tarifadas(self):
        id_cliente = self.clean_id()

