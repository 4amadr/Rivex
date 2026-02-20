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

    
# execução de função para coletar o html (bruto)    

equipes = ['tcrepresentacao', 'tcrepresentacao01', 'tcrepresentacao02', 'tcrepresentacao03', 'tcrepresentacao04']
vs = VonixSip
vc = VonixCleaner

for equipe in equipes:
    all_calls, agents, agressividade = vs.execucao_geral(equipe)
    html_chamadas = vc.transformar_resonse_em_html(all_calls)
    
    tabela = html_chamadas.find('table', class_='grid')
    
    if tabela is None:
        print(f'{equipe}: 0')
        continue
    
    # ocorrencia=0 pega Discadas, ocorrencia=1 pega Automáticas
    linha_total_automaticas = vc.buscar_linha_por_nome(tabela, 'Total', ocorrencia=1)
    
    if linha_total_automaticas is None:
        print(f'{equipe}: 0')
        continue
    
    colunas = linha_total_automaticas.find_all('td')
    valor = colunas[1].text.split()[0] if len(colunas) > 1 else 0
    print(f'{equipe}: {valor}')