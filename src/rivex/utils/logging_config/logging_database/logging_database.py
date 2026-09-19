import logging
import os
from src.rivex.utils.infra_utils.date_config import DateConfig

class LoggingDatabase:
    def __init__(self, logger_name: str = "rivex.database"):
        # 1. Obtém e formata a data para o arquivo de log
        self.data_config = DateConfig()
        self.data_log = self.data_config.data_callix().replace("/", "-")
        
        # 2. Define e cria a estrutura de diretórios se não existir
        self.diretorio = os.path.join("Log", "database-log")
        os.makedirs(self.diretorio, exist_ok=True)
        
        # 3. Define o caminho do arquivo de log
        self.caminho = os.path.join(self.diretorio, f"database-day{self.data_log}.log")
        
        # 4. Instancia e configura o logger
        self.log = logging.getLogger(logger_name)
        self.log.setLevel(logging.INFO)
        
        # 5. Adiciona os handlers apenas se ainda não foram configurados (evita duplicação)
        if not self.log.handlers:
            formatter = logging.Formatter(
                fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            # Handler para gravar em arquivo
            file_handler = logging.FileHandler(self.caminho, encoding='utf-8')
            file_handler.setFormatter(formatter)
            self.log.addHandler(file_handler)
            
            # Handler para exibir também no console/terminal (opcional)
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.log.addHandler(console_handler)

    def conferencia_dados(self, dados):
        # Interpolação tardia (%s) em vez de f-string
        self.log.info("Dados enviados ao banco: %s", dados)

    def registro_erro_envio(self, dados, erro):
        # exc_info=True inclui a pilha de erro (traceback) no log
        self.log.error("Erro ao enviar os dados %s ao banco de dados. Erro: %s", dados, erro, exc_info=True)

    def erro_configuracao(self, erro):
        self.log.error("Erro de configuração do banco: %s", erro, exc_info=True)

