import os

class PayloadsVonix:

    def payload_de_login(self, username, password, token):
        payload_login = {
            'authenticity_token': token,
            'return_to': '',
            'username': username,
            'password': password,
            'commit': 'Entrar'
        }

        return payload_login

    def credenciais_vonix(self):
        user = os.getenv('LOGIN_VONIX')
        password = os.getenv('PASSWORD_VONIX')
        return user, password

    def payload_de_filtragem(self, token, queue_client):
        # para aplicar o filtro
        payload_filtro = {
            'authenticity_token': token,
            'return_to': '/overview',
            'queue_id[]': queue_client # queue_client representa uma equipe entre os clientes
            }
        
        return payload_filtro 
    
    def payload_de_chamadas(self, data, tipo_de_chamada: str | None=None):

        if tipo_de_chamada is None:
            tipo_de_chamada = "" # configuração para retornar todas as chamadas de uma fila

        payload_chamadas = {
            'interval[select]': 'custom',
            'interval[start_date]': data,
            'interval[start_time]': '00:00:00',
            'interval[end_date]': data,
            'interval[end_time]': '23:59:59',
            'queue[direction]': 'ALL',
            'directions[]': 'AUTO',
            'waits': 'Igual',
            'duration': 'Igual',
            'status[select]': tipo_de_chamada
        }
        
        return payload_chamadas 
    
    def payload_de_agentes(self, data):
        payload_agentes = {
            'interval[select]': 'custom',
            'interval[start_date]': data,
            'interval[end_date]': data,
        }
        return payload_agentes
        
    def payload_de_agressividade(self, token):
        payload = {
            'authenticity_token': token
        }
        return payload