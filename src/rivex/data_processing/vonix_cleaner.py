from bs4 import BeautifulSoup
from rivex.automations.vonix.vonix_06 import VonixSip

class VonixCleaner:
    def transformar_resonse_em_html(resposta):
        # função para converter em sopa o response das chamadas
        sopa_convertida = BeautifulSoup(resposta.text, 'html.parser')
        return sopa_convertida
    
    def limpar_chamadas(sopa_convertida, index_de_tabela: int, index_de_linha: int, index_de_resultado: int):
    
        tabelas = sopa_convertida.find_all('table', class_='grid')
        
        if len(tabelas) <= index_de_tabela:
            return 0
        
        tabela_chamadas = tabelas[index_de_tabela]
        linhas = tabela_chamadas.find_all('tr')
        
        if len(linhas) <= index_de_linha:
            return 0
        
        colunas = linhas[index_de_linha].find_all('td')
        
        if len(colunas) <= 1:
            return 0
        
        valor = colunas[1].text.split()
        
        if len(valor) <= index_de_resultado:
            return 0
        
        return valor[index_de_resultado]
        
    def buscar_linha_por_nome(tabela, nome_da_linha: str, ocorrencia: int = 0):
        resultados = []
        for linha in tabela.find_all('tr'):
            primeira_coluna = linha.find('td')
            if primeira_coluna and nome_da_linha in primeira_coluna.text:
                resultados.append(linha)
        
        if len(resultados) <= ocorrencia:
            return None
        return resultados[ocorrencia]
   
    def limpeza_de_agentes(html_agentes):
       # função para limpar os dados dos agentes que vem em formato HTML
       # busca a tabela onde tem os agentes
        tabela_agentes = html_agentes.find('table', class_='grid')
        
        lista_agentes = []
        
        # se a tabela estiver vazia(sem agentes) vai retornar a lista vazia
        if tabela_agentes is None:
            return lista_agentes
            
        # encontrar todos os tr que representam uma linha de agente
        lista_agentes = []

        for linha in tabela_agentes.find_all('tr'):
            # verifica as marcações td que tem classe =item (exatamente a marcação que representa os agentes)
            colunas = linha.find('td', class_='item')
            # se existir coluna vai mandar todos os agentes para a lista de agentes
            if colunas:
                for coluna in colunas:
                    lista_agentes.append(coluna)
        return lista_agentes
    
    def coletar_chamadas_de_agentes(html_agentes):
        tabela_chamadas = html_agentes.find('table', class_='grid')
        if not tabela_chamadas:
            return []

        chamadas_auto = tabela_chamadas.find_all(
            'td',
            id=lambda i: i and i.startswith('call_counter_AUTO_')
        )

        valores = [
            td.get_text(strip=True)
            for td in chamadas_auto
        ]

        print(valores)
        return valores
    
                
       
# execução de função para coletar o html (bruto)    
equipes = ['tcrepresentacao', 'tcrepresentacao01', 'tcrepresentacao02', 'tcrepresentacao03', 'tcrepresentacao04']
vs = VonixSip
vc = VonixCleaner

for equipe in equipes:
    all_calls, agents, agressividade = vs.execucao_geral(equipe)
    html_chamadas = vc.transformar_resonse_em_html(all_calls)
    html_agentes = vc.transformar_resonse_em_html(agents)
    
    tabela = html_chamadas.find('table', class_='grid')
    
    if tabela is None:
        print(f'{equipe}: 0')
        continue
    lista_agentes = vc.limpeza_de_agentes(html_agentes)
    lista_chamadas = vc.coletar_chamadas_de_agentes(html_agentes=html_agentes)
    print(lista_agentes)
    
    # ocorrencia=0 pega Discadas, ocorrencia=1 pega Automáticas
    linha_total_automaticas = vc.buscar_linha_por_nome(tabela, 'Total', ocorrencia=1)
    
    if linha_total_automaticas is None:
        print(f'{equipe}: 0')
        continue
    
    colunas = linha_total_automaticas.find_all('td')
    valor = colunas[1].text.split()[0] if len(colunas) > 1 else 0
    print(f'{equipe}: {valor}')