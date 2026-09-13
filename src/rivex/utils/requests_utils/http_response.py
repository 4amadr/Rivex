
def analista_de_erros(response):
    '''Centraliza todas as funções de tratamento de erros
    e explica como o código deve se comportar a partir desses erros'''
    match response:
        case response if 200 <= response < 300:
            return True
        case 404:
            raise ValueError("Recurso não encontrado! 404")
        case response if 500 <= response < 600:
            raise ValueError(f'Erro de servidor {response}') 
            
    
    
    