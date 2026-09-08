"""Painel de apoio (SPEC §13.3): QR Code + link do Mercado Pago. Nunca interrompe, nunca bloqueia."""
from __future__ import annotations

from pathlib import Path

import gradio as gr

from ... import config
from ...support import donations
from .. import texts as T
from ..session import Sessao


def montar(sessao: Sessao) -> dict:
    link = config.link_apoio()
    configurado = donations.link_configurado(link)
    with gr.Tab(T.ABA_APOIO, id="apoio") as tab:
        gr.Markdown(f"## {T.APOIO_TITULO}")
        gr.Markdown(T.APOIO_LEMBRETE_CORPO)
        if configurado:
            caminho = _qr_path(sessao, link)
            gr.Image(value=str(caminho) if caminho else None, label=T.APOIO_QR, type="filepath", height=260, show_download_button=False)
            gr.Button(T.BTN_CONTRIBUIR, link=link, variant="primary")
        else:
            gr.Markdown(f"_{T.APOIO_LINK_NAO_CONFIGURADO}_")
        gr.Markdown(T.APOIO_FINALIDADE)
        gr.Markdown(f"_{T.APOIO_SEM_BLOQUEIO}_")
    return {"tab": tab, "link": link, "configurado": configurado}


def _qr_path(sessao: Sessao, link: str):
    try:
        destino = Path(sessao.repo.caminhos.configuracoes) / "qr_apoio.png"
        if not destino.exists():
            donations.salvar_qr(link, destino)
        return destino
    except Exception:
        return None
