"""Percurso — Plataforma de inteligência pedagógica.

Uso no Colab (SPEC §3.3):
    import percurso
    percurso.iniciar()
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

__version__ = "1.0.0"


def preparar(base_path: Optional[Path] = None, plataforma=None, informar=print):
    """Etapas 1–5 de `iniciar()` sem abrir a interface. Devolve a Sessao pronta.

    Usado pelos testes e por `iniciar()`.
    """
    from .platform import base as plat_base
    from .storage.migrations import executar as migrar
    from .storage.repo import Repositorio
    from .support import donations
    from .ui import texts as T
    from .ui.session import Sessao
    from .utils import logging as log_mod

    plataforma = plataforma or plat_base.obter_plataforma()
    plat_base.definir_plataforma(plataforma)
    log = log_mod.configurar(arquivo_runtime=plataforma.caminho_log_runtime())
    log.info("Percurso %s iniciando na plataforma %s", __version__, plataforma.nome)

    informar(T.TRANSPARENCIA_DRIVE)
    base = Path(base_path) if base_path else plataforma.montar_armazenamento()
    primeira_vez = not (Path(base) / "configuracoes").exists()
    repo = Repositorio(base)
    log_mod.configurar(arquivo_diagnostico=repo.caminhos.diagnostico_log)
    mensagens = [T.DRIVE_CONECTADO if plataforma.eh_colab() else f"Pasta de dados: {base}"]

    repo.caminhos.criar_estrutura()
    mensagens.append(T.ESTRUTURA_CRIADA if primeira_vez else T.DADOS_RECUPERADOS)

    acoes = migrar(repo, informar=informar)
    for a in acoes:
        log.info("migração: %s", a)
    if any("migrad" in a for a in acoes):
        mensagens.append("Dados atualizados para a versão atual ✓")

    sessao = Sessao(repo=repo, plataforma=plataforma)
    sessao.mensagens_inicio = mensagens
    sessao.mostrar_lembrete_apoio = donations.verificar_e_marcar(repo, sessao.fuso)
    for m in mensagens:
        informar(m)
    return sessao


def porta_livre(inicio: int = 7860, tentativas: int = 30) -> int:
    import socket

    for p in range(inicio, inicio + tentativas):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", p)) != 0:
                return p
    return inicio


def iniciar(base_path: Optional[Path] = None, inline: bool = True, share: bool = False, **kw):
    """Conecta o Drive (popup do Colab), cria a estrutura, migra, verifica o lembrete e abre a interface."""
    from . import app as app_mod

    sessao = preparar(base_path=base_path)
    demo = app_mod.montar_app(sessao)
    if sessao.plataforma.eh_colab() and "root_path" not in kw:
        porta = int(kw.pop("server_port", 0) or porta_livre())
        url = sessao.plataforma.url_proxy(porta)
        kw["server_port"] = porta
        if url:
            kw["root_path"] = url
    return app_mod.lancar(demo, inline=inline, share=share, **kw)
