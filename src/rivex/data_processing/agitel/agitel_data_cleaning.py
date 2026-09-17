from bs4 import BeautifulSoup
from src.rivex.utils.beautiful_soup_utils.cleaning_soup import CleaningSoup
import re

class CleaningAgitel:
    def __init__(self):
        self.soup = CleaningSoup()
        
        
    def _linhas_clientes(self, pagina_inicial):
        print(f"PAGINA INICIAL AGITEL: {pagina_inicial.text}")
        """Retorna as linhas da tabela de minutagem que representam clientes."""
        soup_html = self.soup.passar_para_html(pagina_inicial)

        linhas = []

        for tr in soup_html.find_all("tr"):
            colunas = tr.find_all("td")

            # A linha de cliente possui 8 colunas
            if len(colunas) >= 5:
                cliente = colunas[0].get_text(strip=True)

                # Ignora linhas que não representam clientes
                if cliente and cliente.lower() != "total:":
                    linhas.append(colunas)

        return linhas


    def get_cliente(self, pagina_inicial):
        """
        Retorna uma lista de dicionários contendo apenas
        o nome de cada cliente.
        """

        linhas = self._linhas_clientes(pagina_inicial)



        return [
            {
                "cliente": linha[0].get_text(strip=True)
            }
            for linha in linhas
        ]


    def get_tech(self, pagina_inicial):
        """
        Retorna uma lista de dicionários contendo a TECH
        de cada cliente.
        """

        linhas = self._linhas_clientes(pagina_inicial)

        resultado = []

        for linha in linhas:
            cliente_completo = linha[0].get_text(" ", strip=True)

            # Pega tudo que aparece antes do nome do cliente.
            # Exemplo: "1404#01 - TC Representação" -> "1404#01"
            match = re.match(r"^(\d+#\d+)\s*[-]?\s*", cliente_completo)

            tech = match.group(1) if match else None

            resultado.append({
                "tech": tech
            })

        return resultado


    def get_custo(self, pagina_inicial):
        """
        Retorna uma lista de dicionários contendo o custo
        de cada cliente.
        """

        linhas = self._linhas_clientes(pagina_inicial)

        return [
            {
                "custo": linha[4].get_text(strip=True)
            }
            for linha in linhas
        ]


    def get_minutagem(self, pagina_inicial):
        """
        Retorna uma lista de dicionários contendo a minutagem
        de cada cliente.
        """

        linhas = self._linhas_clientes(pagina_inicial)

        return [
            {
                "minutagem": linha[2].get_text(strip=True)
            }
            for linha in linhas
        ]
        


    def dados_agitel(self, pagina_inicial):
        """
        Executa todas as funções de coleta e consolida
        os dados em uma única lista de dicionários.
        """

        clientes = self.get_cliente(pagina_inicial)
        techs = self.get_tech(pagina_inicial)
        custos = self.get_custo(pagina_inicial)
        minutagens = self.get_minutagem(pagina_inicial)

        dados = []

        for cliente, tech, custo, minutagem in zip(
            clientes,
            techs,
            custos,
            minutagens
        ):
            dados.append({
                "cliente": cliente["cliente"],
                "tech": tech["tech"],
                "custo": custo["custo"],
                "minutagem": minutagem["minutagem"]
            })

        return dados