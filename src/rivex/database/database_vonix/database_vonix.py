from __future__ import annotations

from typing import Optional

from src.rivex.config.settings import DatabaseSettings
from src.rivex.database.config_database import ConexaoDatabaseRivex, DatabaseBase
from src.rivex.database.database_callix.database_callix import _migracao_renomear_para_equipe
from src.rivex.domain.registros import ClienteRegistro, OperadorRegistro


class DatabaseVonix:
    def __init__(
        self,
        conexao_compartilhada: Optional[ConexaoDatabaseRivex] = None,
        db_settings: Optional[DatabaseSettings] = None,
    ):
        self.query_criar_tabela_chamadas = """
            CREATE TABLE IF NOT EXISTS dados_discador.chamadas_cliente_vonix (
                id INTEGER,
                tech_cliente INTEGER NOT NULL,
                equipe TEXT NOT NULL,
                data DATE NOT NULL,
                chamadas INTEGER NOT NULL,
                completas INTEGER NOT NULL,
                recusadas INTEGER NOT NULL,
                abandonadas INTEGER NOT NULL,
                agressividade FLOAT NOT NULL,
                PRIMARY KEY (tech_cliente, equipe, data)
            );
        """
        self.query_criar_tabela_agentes = """
            CREATE TABLE IF NOT EXISTS dados_discador.chamadas_agente_vonix (
                id INTEGER,
                tech INTEGER NOT NULL,
                equipe TEXT NOT NULL,
                data DATE NOT NULL,
                nome_agente TEXT NOT NULL,
                chamadas_agente INTEGER NOT NULL,
                PRIMARY KEY (tech, equipe, data, nome_agente)
            );
        """
        self.migracoes = [
            _migracao_renomear_para_equipe("chamadas_cliente_vonix"),
            _migracao_renomear_para_equipe("chamadas_agente_vonix"),
            "ALTER TABLE dados_discador.chamadas_cliente_vonix ADD COLUMN IF NOT EXISTS id INTEGER;",
            "ALTER TABLE dados_discador.chamadas_agente_vonix ADD COLUMN IF NOT EXISTS id INTEGER;",
        ]
        self.query_chamadas = """
            INSERT INTO dados_discador.chamadas_cliente_vonix (
                id, tech_cliente, equipe, data, chamadas, completas,
                recusadas, abandonadas, agressividade
            )
            VALUES (
                %(id)s, %(tech)s, %(cliente)s, %(data)s, %(chamadas)s, %(aceitas)s,
                %(recusadas)s, %(abandonadas)s, %(agressividade)s
            )
            ON CONFLICT (tech_cliente, equipe, data) DO UPDATE SET
                id = EXCLUDED.id,
                chamadas = EXCLUDED.chamadas,
                completas = EXCLUDED.completas,
                recusadas = EXCLUDED.recusadas,
                abandonadas = EXCLUDED.abandonadas,
                agressividade = EXCLUDED.agressividade;
        """
        self.query_agentes = """
            INSERT INTO dados_discador.chamadas_agente_vonix (
                id, tech, equipe, data, nome_agente, chamadas_agente
            )
            VALUES (
                %(id)s, %(tech)s, %(cliente)s, %(data)s, %(nome_operador)s, %(chamada_aceita)s
            )
            ON CONFLICT (tech, equipe, data, nome_agente) DO UPDATE SET
                id = EXCLUDED.id,
                chamadas_agente = EXCLUDED.chamadas_agente;
        """

        self.db = DatabaseBase(
            query_insert_chamada=self.query_chamadas,
            query_insert_operador=self.query_agentes,
            servico="vonix",
            conexao_compartilhada=conexao_compartilhada,
            db_settings=db_settings,
        )
        self.db.criar_tabelas(
            self.query_criar_tabela_chamadas,
            self.query_criar_tabela_agentes,
            migracoes=self.migracoes,
        )

    def db_vonix(self, dados_chamadas: ClienteRegistro, agentes: list[OperadorRegistro]) -> None:
        self.db.enviar_dados(dados_chamadas, agentes)

    def fechar_db_vonix(self) -> None:
        self.db.fechar_db()
