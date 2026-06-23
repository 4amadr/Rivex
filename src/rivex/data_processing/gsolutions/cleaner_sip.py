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
                    minutagem.append(int(float(valor.replace(".", "").replace(",", "."))))
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
                    custos.append(int(float(valor.replace(".", "").replace(",", "."))))
                except ValueError:
                    log.warning("Alteração na tabela de custos. Requer verificação no processamento de dados")
                    continue

        return custos
    
    def get_tech(self, lista_clientes):
        print("QUANTIDADE DE CLIENTES: ",len(lista_clientes))
        for cliente in lista_clientes:
            print("CLIENTE PARA SER FILTRADO! ", cliente)
            tech = "".join(filter(str.isdigit, cliente))
            print(tech)
        return tech
    
    def clean_id(self):
        dados = json.loads(self.id_clientes)
        lista_id = [identificador["id"] for identificador in dados if identificador]
        lista_clientes = [identificador["value"] for identificador in dados if identificador]
        
        return lista_id, lista_clientes
    
    def lista_comparadora(self, lista_id, lista_clientes):
        """Função que vai criar uma lista de dicts
        posteriormente vai comparar ["cliente"] com os clientes online
        enviar os ids para uma nova lista e diminuir a quantidade de requisição"""
        lista_identificador = []
        
        for identificador, cliente in zip(lista_id, lista_clientes):
            dict_comparativo = {
                "id": identificador,
                "cliente": cliente 
            }
            lista_identificador.append(dict_comparativo)
        return lista_identificador


    def get_clientes_tarifados(self, lista_identificador, lista_clientes_online):
        """Função para filtrar apenas os clientes que tiveram consumo para diminuir a quantidade de requisições"""
        lista_identificadores_online = []

        for identificador in lista_identificador:
            if identificador["cliente"] in lista_clientes_online:
                lista_identificadores_online.append(identificador["id"]) 
        return lista_identificadores_online
    
    def limpar_html_tarifadas(self, chamadas_tarifadas_html):
        html = chamadas_tarifadas_html.text
        parseado = BeautifulSoup(html, "html.parser")
        elemento = parseado.find("div", id="total_registros_texto")

        return elemento
        
    def retornar_tarifadas(self, tarifadas_em_html):
        texto = tarifadas_em_html.get_text(strip=True)
        numero = int(re.search(r"\d+", texto).group())
        return numero
        

    
    def limpar_consumo(self):
        tabela = self.gerar_tabela_consumo()
        cliente = self.gerar_clientes(tabela)
        minutagem = self.gerar_minutagem(tabela)
        custo = self.gerar_custos(tabela)

        
  

        return cliente, minutagem, custo
    
    def gerar_ids_tarifadas(self, lista_clientes_com_consumo):
        lista_id_cliente, lista_clientes_total = self.clean_id()
        list_comparador = self.lista_comparadora(lista_id_cliente, lista_clientes_total)
        lista_ids_online = self.get_clientes_tarifados(list_comparador, lista_clientes_com_consumo)
        tech = self.get_tech(lista_clientes_com_consumo)

        
        return tech, lista_ids_online
    
    def limpar_chamadas_tarifadas(self, html_tarifadas): 
        elemento_html = self.limpar_html_tarifadas(html_tarifadas)
        chamadas_tarifadas = self.retornar_tarifadas(elemento_html)
        return chamadas_tarifadas

