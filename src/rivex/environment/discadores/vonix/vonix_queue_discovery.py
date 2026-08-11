"""
Módulo de descoberta automática de filas do Vonix CC.

Este módulo resolve o problema de não saber quais clientes estão no sistema.
Ele extrai dinamicamente todas as filas disponíveis diretamente do HTML
da página principal pós-login, eliminando a necessidade de manter uma
lista hardcoded (como equipes_vonix.py).

Uso:
    discovery = VonixQueueDiscovery(session, url_base)
    filas = discovery.descobrir_filas()
    # filas = [{'id': 'tcrepresentacao', 'nome': '09 TC - Banda Larga'}, ...]
    
    # Filtrar apenas filas ativas (sem as "ZzDisponivel")
    ativas = discovery.filas_ativas()
"""
from bs4 import BeautifulSoup


class VonixQueueDiscovery:
    """
    Descobre automaticamente todas as filas/clientes cadastrados no Vonix CC.
    
    O Vonix armazena a lista de filas em um formulário HTML na página principal
    após login. Cada fila é um checkbox <input name="queue_id[]"> dentro de
    <form action="/login/set_show_queue">.
    
    Atributos:
        session: requests.Session com login já realizado
        url_base: URL base do Vonix (ex: http://contech6.vonixcc.com.br)
    """
    
    # Prefixos de filas que devem ser ignoradas (inativas/disponíveis)
    PREFIXOS_INATIVOS = ['zz', 'Zz', 'ZZ', '- equipe de teste']
    
    # Sufixos que indicam fila manual (duplicata da fila automática)
    SUFIXO_MANUAL = 'manual'
    
    def __init__(self, session, url_base):
        self.session = session
        self.url_base = url_base
        self._cache_filas = None
    
    def descobrir_filas(self, forcar_reload=False):
        """
        Descobre todas as filas do sistema via scraping do HTML.
        
        Retorna:
            Lista de dicts: [{'id': 'queue_id', 'nome': 'Nome Visível'}, ...]
            
        O resultado é cacheado para evitar requests desnecessários.
        Use forcar_reload=True para forçar nova consulta.
        """
        if self._cache_filas and not forcar_reload:
            return self._cache_filas
        
        # GET na página principal (pós-login)
        resp = self.session.get(f"{self.url_base}/", allow_redirects=True)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Encontrar o form de seleção de filas
        form = soup.find('form', action='/login/set_show_queue')
        if not form:
            raise RuntimeError(
                "Formulário de seleção de filas não encontrado. "
                "Verifique se o login foi realizado corretamente."
            )
        
        # Extrair filas dos checkboxes
        filas = []
        for checkbox in form.find_all('input', {'name': 'queue_id[]'}):
            queue_id = checkbox.get('value', '')
            # O nome está no <label> que é parent do <input>
            label = checkbox.parent
            nome = label.get_text(strip=True) if label else ''
            
            if queue_id and nome:
                filas.append({
                    'id': queue_id,
                    'nome': nome
                })
        
        self._cache_filas = filas
        return filas
    
    def filas_ativas(self, incluir_manuais=True, forcar_reload=False):
        """
        Retorna apenas filas ativas (remove as marcadas como "ZzDisponivel"
        e filas de teste).
        
        Args:
            incluir_manuais: Se True, inclui filas manuais. Se False, 
                             exclui filas cujo nome contém 'MANUAL'.
            forcar_reload: Se True, força nova consulta ao servidor.
            
        Retorna:
            Lista de dicts com filas ativas.
        """
        todas = self.descobrir_filas(forcar_reload)
        
        ativas = []
        for fila in todas:
            nome_lower = fila['nome'].lower()
            
            # Pular filas inativas/disponíveis
            if any(nome_lower.startswith(p.lower()) for p in self.PREFIXOS_INATIVOS):
                continue
            
            # Pular filas com "0 USUARIOS INATIVOS"
            if 'inativos' in nome_lower:
                continue
            
            # Opcionalmente pular filas manuais
            if not incluir_manuais and self.SUFIXO_MANUAL in nome_lower:
                continue
            
            ativas.append(fila)
        
        return ativas
    
    def filas_automaticas(self, forcar_reload=False):
        """
        Retorna apenas filas automáticas (exclui manuais e inativas).
        Útil para coleta principal de dados.
        """
        return self.filas_ativas(incluir_manuais=False, forcar_reload=forcar_reload)
    
    def buscar_fila(self, termo):
        """
        Busca filas pelo nome ou ID (busca parcial, case-insensitive).
        
        Args:
            termo: Texto para buscar (ex: 'TC', 'assis', 'real')
            
        Retorna:
            Lista de filas que correspondem ao termo.
        """
        todas = self.descobrir_filas()
        termo_lower = termo.lower()
        
        return [
            f for f in todas
            if termo_lower in f['id'].lower() or termo_lower in f['nome'].lower()
        ]
    
    def ids_das_filas(self, apenas_ativas=True, incluir_manuais=True):
        """
        Retorna apenas os IDs das filas (para uso direto nas requisições).
        
        Retorna:
            Lista de strings: ['tcrepresentacao', 'assismollerke', ...]
        """
        if apenas_ativas:
            filas = self.filas_ativas(incluir_manuais=incluir_manuais)
        else:
            filas = self.descobrir_filas()
        
        return [f['id'] for f in filas]
    
    def resumo(self):
        """
        Imprime um resumo das filas encontradas.
        """
        todas = self.descobrir_filas()
        ativas = self.filas_ativas()
        automaticas = self.filas_automaticas()
        
        print(f"{'='*60}")
        print(f"RESUMO DE FILAS DO VONIX")
        print(f"{'='*60}")
        print(f"  Total de filas:      {len(todas)}")
        print(f"  Filas ativas:        {len(ativas)}")
        print(f"  Filas automáticas:   {len(automaticas)}")
        print(f"  Filas inativas:      {len(todas) - len(ativas)}")
        print()
        
        print("FILAS AUTOMÁTICAS (para coleta):")
        for f in automaticas:
            print(f"  {f['id']:<35} {f['nome']}")
        
        return {
            'total': len(todas),
            'ativas': len(ativas),
            'automaticas': len(automaticas),
        }
