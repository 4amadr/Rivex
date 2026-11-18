from src.rivex.database.database_callix.database_callix_clientes import DatabaseClientes
from src.rivex.environments.discadores.Callix.callix_get_clients import GetTokenCallix

class SincroniaCallix():
    def __init__(self):
        self.db_clientes=DatabaseClientes()  
        self.get_token = GetTokenCallix()
    
    def verificar_status_clientes(self, clientes_totais):
        return [
            {
                "cliente": c["cliente"],
                "ativo": (
                    c["status"].strip().lower() == "active"
                    if isinstance(c["status"], str)
                    else c["status"] == 3
                ),
            }
            for c in clientes_totais
        ]
    
    def inserir_clientes(self, status_cliente):
        """comparar a lista atual com o banco e inserir a diferença entre os dois no banco"""
        for cliente in status_cliente:
            self.db_clientes.cadastrar_cliente(cliente)
            
    def buscar_clientes_sem_token(self):
        return self.db_clientes.buscar_clientes_sem_token()

    def adicionar_token_ao_db(self, lista_tokens_novos, lista_clientes_sem_token=None):
        if isinstance(lista_tokens_novos, dict):
            for cliente, token in lista_tokens_novos.items():
                self.db_clientes.adicionar_token_ao_db(token, cliente)
            return

        for token, cliente in zip(lista_tokens_novos, lista_clientes_sem_token or []):
            self.db_clientes.adicionar_token_ao_db(token, cliente)

    def coletar_tokens(self, cliente_sem_token):
        if not cliente_sem_token:
            return []

        lista_tokens = self.get_token.fluxo_de_tokens(cliente_sem_token)
        return lista_tokens

    def consultar_clientes_ativos(self):
        return self.db_clientes.consultar_view()
    
        
    def sincronizar_clientes(self, clientes_totais):
        
        status_cliente = self.verificar_status_clientes(clientes_totais)
        self.inserir_clientes(status_cliente)
        
        clientes_sem_token = self.buscar_clientes_sem_token()
        lista_tokens = self.coletar_tokens(clientes_sem_token)
        
        self.adicionar_token_ao_db(lista_tokens, clientes_sem_token)
        
        return self.db_clientes.consultar_view()  