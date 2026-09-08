"""Painel de apoio (SPEC §13.3): QR Code + link do Mercado Pago. Nunca interrompe, nunca bloqueia."""
from __future__ import annotations

from pathlib import Path
from hashlib import sha256

import gradio as gr

from ... import config
from ...support import donations
from .. import texts as T
from .. import common as C
from ..session import Sessao


def montar(sessao: Sessao) -> dict:
    link = donations.obter_link(sessao.repo)
    configurado = donations.link_configurado(link)
    with gr.Tab(T.ABA_APOIO, id="apoio") as tab:
        gr.Markdown(f"## {T.APOIO_TITULO}")
        gr.Markdown(T.APOIO_LEMBRETE_CORPO)
        caminho = _qr_path(sessao, link) if configurado else None
        imagem = gr.Image(value=str(caminho) if caminho else None, label=T.APOIO_QR, type="filepath", height=260, interactive=False, buttons=[], visible=configurado)
        contribuir = gr.Button(T.BTN_CONTRIBUIR, link=link if configurado else None, variant="primary", visible=configurado)
        aviso = gr.Markdown(f"_{T.APOIO_LINK_NAO_CONFIGURADO}_", visible=not configurado)
        gr.Markdown(T.APOIO_FINALIDADE)
        gr.Markdown(f"_{T.APOIO_SEM_BLOQUEIO}_")
        with gr.Accordion("Configurar Mercado Pago e ver tutorial", open=not configurado):
            gr.Markdown(T.TUTORIAL_MERCADO_PAGO)
            campo = gr.Textbox(label="Link público de apoio no Mercado Pago", value=link if configurado else "", placeholder="https://link.mercadopago.com.br/seulink", info="Cole o link compartilhável de pagamento. Não é uma chave de API.")
            salvar = gr.Button("Salvar link de apoio", variant="primary")
            mensagem = gr.HTML("")

        def salvar_configuracao(valor):
            try:
                novo = donations.salvar_link(sessao.repo, valor)
            except ValueError as e:
                return C.erro(str(e)), gr.update(), gr.update(), gr.update()
            ativo = donations.link_configurado(novo)
            qr = _qr_path(sessao, novo) if ativo else None
            return (C.ok("Link salvo. Confira o destinatário e o valor na página de pagamento antes de compartilhar." if ativo else "Configuração salva. Ainda não há um link de apoio disponível."),
                    gr.update(value=str(qr) if qr else None, visible=ativo),
                    gr.update(link=novo if ativo else None, visible=ativo), gr.update(visible=not ativo))

        salvar.click(C.protegido(salvar_configuracao), [campo], [mensagem, imagem, contribuir, aviso])
    return {"tab": tab, "link": link, "configurado": configurado}


def _qr_path(sessao: Sessao, link: str):
    try:
        destino = Path(sessao.repo.caminhos.configuracoes) / f"qr_apoio_{sha256(link.encode()).hexdigest()[:16]}.png"
        if not destino.exists():
            donations.salvar_qr(link, destino)
        return destino
    except Exception:
        return None
