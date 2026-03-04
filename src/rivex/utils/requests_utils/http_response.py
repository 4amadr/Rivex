class HttpResponse:
    def analista_de_erros(response):
        '''Centraliza todas as funções de tratamento de erros
        e explica como o código deve se comportar a partir desses erros'''
        match response:
            case 429:
                raise TimeoutError('Servidor bloqueado por excesso de requisições. Aguarde alguns instantes...')
            case 401:
                raise ValueError('Ops, dados incorretos. Revise as credenciais e tente novamente')
            case 403:
                raise PermissionError('Usuário sem permissão para acessar essa página')
            case 500:
                raise ConnectionError('Erro de servidor')
            case 200:
                print()
                
                
        
        
        