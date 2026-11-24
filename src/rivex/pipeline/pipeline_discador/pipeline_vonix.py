from __future__ import annotations

import os
import time
from datetime import date
from typing import Optional

from src.rivex.config.settings import Settings
from src.rivex.data_processing.Vonix.cleaning_vonix import (
    dict_agentes,
    gerar_lista_de_clientes,
    get_agressividade,
    limpar_chamadas,
    resolver_tech_vonix,
)
from src.rivex.data_processing.Vonix.fluxo_limpeza import LimpezaVonix
from src.rivex.database.config_database import conexao_rivex
from src.rivex.database.database_vonix.database_vonix import DatabaseVonix
from src.rivex.database.database_vonix.database_vonix_clientes import DatabaseClientesVonix
from src.rivex.domain.exceptions import ErroAutenticacao
from src.rivex.domain.registros import ClienteRegistro, OperadorRegistro, ResumoExecucao
from src.rivex.environments.discadores.vonix.fluxo_coleta import ExecucaoVonix
from src.rivex.utils.infra_utils.date_config import DateConfig
from src.rivex.utils.logging_config import PipelineLogger, TransformLogger


class PipelineVonix:
    nome = "vonix"

    def __init__(self, settings: Optional[Settings] = None, usar_db: bool = True):
        self.settings = settings
        self.usar_db = usar_db
        self.log = PipelineLogger("vonix")
        self.transform_log = TransformLogger("vonix")

        vonix_cfg = settings.vonix if settings is not None else None
        self.login = vonix_cfg.login if vonix_cfg else (os.getenv("LOGIN_VONIX") or "")
        self.senha = vonix_cfg.password if vonix_cfg else (os.getenv("SENHA_VONIX") or "")
        self.url = vonix_cfg.url if vonix_cfg else (os.getenv("URL_BASE_VONIX6") or "")
        self.tempo_int = vonix_cfg.delay_segundos if vonix_cfg else float(os.getenv("TEMPO_VONIX", "2"))
        self.tempo_backoff_erro = (
            vonix_cfg.backoff_erro_segundos
            if vonix_cfg
            else float(os.getenv("VONIX_BACKOFF_ERRO", "15"))
        )

        self.data_ref: date = DateConfig.ontem()
        self.vonix_execucao = ExecucaoVonix(
            login=self.login,
            senha=self.senha,
            data=DateConfig.data_selecionadas(self.data_ref),
            url_base=self.url,
        )
        self.limpeza_vonix = LimpezaVonix()

    def inicial_config(self) -> tuple[list[str], str]:
        token_encontrado = self.vonix_execucao.token_pronto()
        clientes_html = self.vonix_execucao.get_clientes(token_encontrado)
        return gerar_lista_de_clientes(html=clientes_html), token_encontrado

    def get_dados_sujos(self, cliente: str, token: str) -> dict:
        self.vonix_execucao.get_filtragem(cliente, token)
        return {
            "Totais": self.vonix_execucao.get_chamadas(),
            "Aceitas": self.vonix_execucao.get_chamadas("completed"),
            "Abandonadas": self.vonix_execucao.get_chamadas("abandon"),
            "Recusadas": self.vonix_execucao.get_chamadas("discard"),
            "Agentes": self.vonix_execucao.get_agentes(),
            "config": self.vonix_execucao.coleta_de_agressividade_vonix(cliente, token),
        }

    def execucao_limpeza_chamadas_vonix(
        self,
        cliente: str,
        totais,
        aceitas,
        abandonadas,
        recusadas,
        config,
        mapa_techs: dict[str, int],
    ) -> tuple[ClienteRegistro, bool]:
        chamadas_totais = limpar_chamadas(totais.text)
        chamadas_aceitas = limpar_chamadas(aceitas.text)
        chamadas_abandonadas = limpar_chamadas(abandonadas.text)
        chamadas_recusadas = limpar_chamadas(recusadas.text)
        agressividade = get_agressividade(config.text)
        tech, nova_tech = resolver_tech_vonix(cliente, config.text, mapa_techs)

        dados_cliente = ClienteRegistro(
            discador="Vonix",
            tech=tech,
            cliente=cliente,
            data=self.data_ref,
            chamadas=chamadas_totais,
            aceitas=chamadas_aceitas,
            recusadas=chamadas_recusadas,
            abandonadas=chamadas_abandonadas,
            agressividade=agressividade,
        )

        self.transform_log.registrar_limpeza_chamadas(dados_cliente)
        return dados_cliente, nova_tech

    def execucao_limpeza_agentes_vonix(
        self, cliente_reg: ClienteRegistro, agentes, data: date
    ) -> list[OperadorRegistro]:
        return dict_agentes(agentes.text, cliente_reg, data)

    def execucao_vonix(self, data: Optional[date] = None) -> ResumoExecucao:
        if data is not None:
            self.data_ref = data
            self.vonix_execucao.data = DateConfig.data_selecionadas(data)

        self.log.inicio("Iniciando configuração do servidor Vonix", data=str(self.data_ref))
        registros_para_persistir: list[tuple[ClienteRegistro, list[OperadorRegistro]]] = []
        novas_techs_para_registrar: dict[str, int] = {}
        assinaturas_vistas: set[tuple] = set()
        falhas: list[str] = []
        total_clientes = 0
        mapa_techs: dict[str, int] = {}

        if self.usar_db:
            db_settings = self.settings.db if self.settings is not None else None
            with conexao_rivex(db_settings) as conn:
                db_clientes = DatabaseClientesVonix(conexao_compartilhada=conn)
                mapa_techs = db_clientes.carregar_mapa_techs()

        try:
            clientes_validos, token = self.inicial_config()
            if not clientes_validos:
                raise ErroAutenticacao(
                    "Nenhum cliente encontrado no Vonix (lista vazia ou sessão inválida)."
                )

            total_clientes = len(clientes_validos)

            for idx, cliente_selecionado in enumerate(clientes_validos):
                houve_erro = False
                try:
                    response_dict = self.get_dados_sujos(cliente_selecionado, token)
                    self.log.etapa("Iniciando coleta do cliente", cliente=cliente_selecionado)

                    cliente_reg, nova_tech = self.execucao_limpeza_chamadas_vonix(
                        cliente_selecionado,
                        response_dict["Totais"],
                        response_dict["Aceitas"],
                        response_dict["Abandonadas"],
                        response_dict["Recusadas"],
                        response_dict["config"],
                        mapa_techs,
                    )
                    if nova_tech:
                        mapa_techs[cliente_selecionado] = cliente_reg.tech
                        novas_techs_para_registrar[cliente_selecionado] = cliente_reg.tech

                    assinatura = (
                        cliente_reg.tech,
                        cliente_reg.cliente,
                        cliente_reg.data,
                        cliente_reg.chamadas,
                        cliente_reg.aceitas,
                        cliente_reg.recusadas,
                        cliente_reg.abandonadas,
                    )
                    if assinatura in assinaturas_vistas:
                        self.log.aviso(
                            "Coleta 100% duplicada ignorada no Vonix",
                            cliente=cliente_selecionado,
                            tech=cliente_reg.tech,
                        )
                        continue
                    assinaturas_vistas.add(assinatura)

                    agentes = self.execucao_limpeza_agentes_vonix(
                        cliente_reg,
                        response_dict["Agentes"],
                        cliente_reg.data,
                    )

                    self.transform_log.registrar_limpeza_agente(
                        [a.model_dump() for a in agentes]
                    )
                    registros_para_persistir.append((cliente_reg, agentes))
                except Exception as erro:
                    houve_erro = True
                    falhas.append(f"{cliente_selecionado}: {erro}")
                    self.log.erro(
                        "Erro ao processar cliente Vonix",
                        erro=erro,
                        cliente=cliente_selecionado,
                    )
                finally:
                    if idx < total_clientes - 1:
                        pausa = self.tempo_backoff_erro if houve_erro else self.tempo_int
                        if pausa > 0:
                            time.sleep(pausa)
        finally:
            sessao = getattr(self.vonix_execucao, "session", None)
            if sessao is not None:
                sessao.close()

        persistidos = 0
        if self.usar_db and (registros_para_persistir or novas_techs_para_registrar):
            db_settings = self.settings.db if self.settings is not None else None
            with conexao_rivex(db_settings) as conn:
                if novas_techs_para_registrar:
                    db_clientes = DatabaseClientesVonix(conexao_compartilhada=conn)
                    for equipe, tech in novas_techs_para_registrar.items():
                        db_clientes.registrar_tech(equipe, tech)
                db = DatabaseVonix(conexao_compartilhada=conn)
                for cliente_reg, agentes in registros_para_persistir:
                    try:
                        db.db_vonix(cliente_reg, agentes)
                        persistidos += 1
                    except Exception as erro:
                        falhas.append(f"{cliente_reg.cliente}: {erro}")
                        self.log.erro(
                            "Erro ao persistir cliente Vonix",
                            erro=erro,
                            cliente=cliente_reg.cliente,
                        )

        resumo = ResumoExecucao(
            pipeline=self.nome,
            total=total_clientes,
            persistidos=persistidos,
            falhas=falhas,
        )
        self.log.fim(
            "Pipeline Vonix finalizada",
            total=resumo.total,
            persistidos=resumo.persistidos,
            falhas=len(resumo.falhas),
        )
        return resumo

    def executar(self, data: Optional[date] = None) -> ResumoExecucao:
        return self.execucao_vonix(data=data)
