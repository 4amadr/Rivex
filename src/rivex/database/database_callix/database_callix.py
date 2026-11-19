from __future__ import annotations

from typing import Optional

from src.rivex.config.settings import DatabaseSettings
from src.rivex.database.config_database import ConexaoDatabaseRivex, DatabaseBase
from src.rivex.domain.registros import ClienteRegistro, OperadorRegistro


def _migracao_renomear_para_equipe(tabela: str) -> str:
    return f"""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'dados_discador'
                  AND table_name = '{tabela}'
                  AND column_name = 'cliente_nome'
            ) AND NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'dados_discador'
                  AND table_name = '{tabela}'
                  AND column_name = 'equipe'
            ) THEN
                ALTER TABLE dados_discador.{tabela} RENAME COLUMN cliente_nome TO equipe;
            END IF;
        END $$;
    """


class DatabaseCallix:
    def __init__(
        self,
        conexao_compartilhada: Optional[ConexaoDatabaseRivex] = None,
        db_settings: Optional[DatabaseSettings] = None,
    ):
        self.query_criar_tabela_chamadas = """
            CREATE TABLE IF NOT EXISTS dados_discador.chamadas_cliente_callix (
                id INTEGER,
                tech INTEGER NOT NULL,
                equipe TEXT NOT NULL,
                data DATE NOT NULL,
                chamadas INTEGER NOT NULL,
                completas INTEGER NOT NULL,
                recusadas INTEGER NOT NULL,
                abandonadas INTEGER NOT NULL,
                agressividade FLOAT NOT NULL,
                operadores_contratados INTEGER NOT NULL DEFAULT 0,
                valor_cliente NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
                rota_cliente TEXT,
                PRIMARY KEY (tech, equipe, data)
            );
        """
        self.query_criar_tabela_agentes = """
            CREATE TABLE IF NOT EXISTS dados_discador.chamadas_agente_callix (
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
            _migracao_renomear_para_equipe("chamadas_cliente_callix"),
            _migracao_renomear_para_equipe("chamadas_agente_callix"),
            "ALTER TABLE dados_discador.chamadas_cliente_callix ADD COLUMN IF NOT EXISTS id INTEGER;",
            "ALTER TABLE dados_discador.chamadas_cliente_callix ADD COLUMN IF NOT EXISTS operadores_contratados INTEGER NOT NULL DEFAULT 0;",
            "ALTER TABLE dados_discador.chamadas_cliente_callix ADD COLUMN IF NOT EXISTS valor_cliente NUMERIC(12, 2) NOT NULL DEFAULT 0.00;",
            "ALTER TABLE dados_discador.chamadas_cliente_callix ADD COLUMN IF NOT EXISTS rota_cliente TEXT;",
            "ALTER TABLE dados_discador.chamadas_agente_callix ADD COLUMN IF NOT EXISTS id INTEGER;",
        ]
        self.query_chamadas = """
            INSERT INTO dados_discador.chamadas_cliente_callix (
                id, tech, equipe, data, chamadas, completas, recusadas,
                abandonadas, agressividade, operadores_contratados, valor_cliente, rota_cliente
            )
            VALUES (
                %(id)s, %(tech)s, %(cliente)s, %(data)s, %(chamadas)s, %(aceitas)s,
                %(recusadas)s, %(abandonadas)s, %(agressividade)s,
                %(operadores_contratados)s, %(lucro_empresa)s, %(rota_cliente)s
            )
            ON CONFLICT (tech, equipe, data) DO UPDATE SET
                id = EXCLUDED.id,
                chamadas = EXCLUDED.chamadas,
                completas = EXCLUDED.completas,
                recusadas = EXCLUDED.recusadas,
                abandonadas = EXCLUDED.abandonadas,
                agressividade = EXCLUDED.agressividade,
                operadores_contratados = EXCLUDED.operadores_contratados,
                valor_cliente = EXCLUDED.valor_cliente,
                rota_cliente = EXCLUDED.rota_cliente;
        """
        self.query_agentes = """
            INSERT INTO dados_discador.chamadas_agente_callix (
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
            servico="callix",
            conexao_compartilhada=conexao_compartilhada,
            db_settings=db_settings,
        )
        self.db.criar_tabelas(
            query_tabela_chamadas=self.query_criar_tabela_chamadas,
            query_tabela_agentes=self.query_criar_tabela_agentes,
            migracoes=self.migracoes,
        )

    def db_callix(self, dados_chamadas: ClienteRegistro, agentes: list[OperadorRegistro]) -> None:
        self.db.enviar_dados(dados_chamadas, agentes)

    def fechar(self) -> None:
        self.db.fechar_db()
