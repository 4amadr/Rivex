from __future__ import annotations

import os
import time
from datetime import date
from typing import Optional

from src.rivex.config.settings import Settings
from src.rivex.data_processing.IPBox.limpeza_ipbox import (
    empacotar_dados_agentes,
    empacotar_dados_clientes,
    gerar_html,
    gerar_lista_clientes,
    get_cliente,
    get_identificador,
    limpar_nome_cliente,
    normalizar_nome_comparacao,
)
from src.rivex.database.config_database import conexao_rivex
from src.rivex.database.database_ipbox.database_ipbox import DatabaseIpbox
from src.rivex.domain.exceptions import ErroAutenticacao
from src.rivex.domain.registros import ClienteRegistro, OperadorRegistro, ResumoExecucao
from src.rivex.environments.discadores.IPBox.colect_ipbox import IpboxClientConfig, IpboxInit
from src.rivex.utils.infra_utils.date_config import DateConfig
from src.rivex.utils.logging_config import PipelineLogger, TransformLogger


class PipelineIpbox:
    """Orquestra extração, limpeza e carga de dados do discador IPBox."""

    nome = "ipbox"

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings
        self.log = PipelineLogger("ipbox")
        self.transform_log = TransformLogger("ipbox")

        ipbox_cfg = settings.ipbox if settings is not None else None
        self.url = ipbox_cfg.url if ipbox_cfg else (os.getenv("URL_IPBOX") or "")
        self.login = ipbox_cfg.login if ipbox_cfg else (os.getenv("IPBOX_LOGIN") or "")
        self.senha = ipbox_cfg.password if ipbox_cfg else (os.getenv("IPBOX_PASSWORD") or "")
        self.token = ipbox_cfg.token if ipbox_cfg else (os.getenv("IPBOX_TOKEN") or "")
        self.delay_segundos = ipbox_cfg.delay_segundos if ipbox_cfg else float(os.getenv("TEMPO_IPBOX", "5"))

        self.data_ref: date = DateConfig.ontem()
        self.data_ipbox = DateConfig.data_ipbox(data_ref=self.data_ref)
        self.data_agentes = DateConfig.data_ipbox_payload(data_ref=self.data_ref)

    def autenticar_e_listar_clientes(self):
        ipbox_init = IpboxInit(
            url=self.url,
            login=self.login,
            senha=self.senha,
            data=self.data_ipbox,
        )
        return ipbox_init.execucao_base_ipbox()

    def processar_cliente(
        self, cliente: str, ipbox_client: IpboxClientConfig, id_cliente: str
    ) -> Optional[ClienteRegistro]:
        try:
            dados_sujos = ipbox_client.execucao_ipbox(
                nome_cliente=cliente, id_cliente=id_cliente
            )
            return empacotar_dados_clientes(
                dados_sujos["Chamadas"],
                cliente,
                self.data_ref,
                dados_sujos["Agressividade"],
                dados_sujos["Operadores"],
            )
        except Exception as erro:
            self.log.erro("Erro ao processar cliente IPBox", erro=erro, cliente=cliente)
            return None

    def executar(self, data: Optional[date] = None) -> ResumoExecucao:
        if data is not None:
            self.data_ref = data
            self.data_ipbox = DateConfig.data_ipbox(data_ref=data)
            self.data_agentes = DateConfig.data_ipbox_payload(data_ref=data)

        self.log.inicio("Iniciando configuração do servidor IPBOX", data=str(self.data_ref))
        sessao_logada = None
        registros_para_persistir: list[tuple[ClienteRegistro, list[OperadorRegistro]]] = []
        falhas: list[str] = []
        total_clientes = 0

        try:
            sessao_logada, clientes_texto = self.autenticar_e_listar_clientes()
            self.log.etapa("Sessão IPBOX autenticada; iniciando coleta de dados dos clientes")

            execucao_ipbox = IpboxClientConfig(
                url=self.url,
                login=self.login,
                senha=self.senha,
                data=self.data_ipbox,
                data_agentes=self.data_agentes,
                sessao_anterior=sessao_logada,
                token=self.token,
            )

            html_clientes = gerar_html(clientes_texto)
            lista_clientes = gerar_lista_clientes(html_clientes)
            if not lista_clientes:
                raise ErroAutenticacao(
                    "Nenhum cliente encontrado no IPBox (lista vazia ou sessão inválida)."
                )

            total_clientes = len(lista_clientes)
            agentes_json = execucao_ipbox.get_relatorio_agente().json()

            for idx, cliente in enumerate(lista_clientes):
                cliente_coletado = get_cliente(cliente)
                id_cliente = get_identificador(cliente)

                dados_cliente = self.processar_cliente(
                    cliente_coletado,
                    execucao_ipbox,
                    id_cliente,
                )
                if dados_cliente is None:
                    falhas.append(f"{cliente_coletado}: falha na coleta/limpeza")
                    continue

                cliente_norm = normalizar_nome_comparacao(limpar_nome_cliente(cliente_coletado))
                lista_agentes: list[OperadorRegistro] = []

                for agente in agentes_json.get("data", []):
                    if agente.get("agente") == "TOTAIS":
                        continue

                    times = agente.get("times") or []
                    if not times:
                        continue

                    nome_time_norm = normalizar_nome_comparacao(limpar_nome_cliente(times[0]))
                    if nome_time_norm != cliente_norm:
                        continue

                    lista_agentes.append(
                        empacotar_dados_agentes(
                            agente,
                            dados_cliente,
                            self.data_ref,
                        )
                    )

                self.transform_log.registrar_limpeza_chamadas(dados_cliente)
                self.transform_log.registrar_limpeza_agente([a.model_dump() for a in lista_agentes])
                registros_para_persistir.append((dados_cliente, lista_agentes))

                if idx < total_clientes - 1 and self.delay_segundos > 0:
                    time.sleep(self.delay_segundos)
        finally:
            if sessao_logada is not None:
                sessao_logada.close()

        persistidos = 0
        if registros_para_persistir:
            db_settings = self.settings.db if self.settings is not None else None
            with conexao_rivex(db_settings) as conn:
                banco_ipbox = DatabaseIpbox(conexao_compartilhada=conn)
                for dados_cliente, lista_agentes in registros_para_persistir:
                    try:
                        banco_ipbox.db_ipbox(dados_cliente, lista_agentes)
                        persistidos += 1
                    except Exception as erro:
                        falhas.append(f"{dados_cliente.cliente}: {erro}")
                        self.log.erro(
                            "Erro ao persistir cliente IPBox",
                            erro=erro,
                            cliente=dados_cliente.cliente,
                        )

        resumo = ResumoExecucao(
            pipeline=self.nome,
            total=total_clientes,
            persistidos=persistidos,
            falhas=falhas,
        )
        self.log.fim(
            "Pipeline IPBox finalizada",
            total=resumo.total,
            persistidos=resumo.persistidos,
            falhas=len(resumo.falhas),
        )
        return resumo
