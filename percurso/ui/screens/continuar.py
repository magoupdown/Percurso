"""Continuar aluno ou turma (SPEC §6.3)."""
from __future__ import annotations

import gradio as gr

from ...core import codes
from ...storage.repo import RegistroNaoEncontrado
from .. import common as C
from .. import texts as T
from ..session import Sessao


def montar(sessao: Sessao) -> dict:
    with gr.Tab(T.ABA_CONTINUAR, id="continuar") as tab:
        with gr.Row():
            codigo = gr.Textbox(label=T.DIGITE_CODIGO, placeholder=T.PLACEHOLDER_CODIGO, scale=3)
            btn_carregar = gr.Button(T.BTN_CARREGAR, variant="primary", scale=1)
        recentes = gr.Dropdown(label="Ou escolha um registro já criado neste Drive", choices=_recentes(sessao), value=None)
        mensagem = gr.HTML("")
        painel = gr.Markdown(_painel_atual(sessao))
        with gr.Row(visible=sessao.contexto is not None and sessao.contexto.estado.total_aulas > 0) as acoes_com_aulas:
            btn_continuar = gr.Button(T.BTN_CONTINUAR_DE_ONDE_PARAMOS, variant="primary")
            btn_revisao = gr.Button(T.BTN_FAZER_REVISAO)
            btn_nova_unidade = gr.Button(T.BTN_NOVA_UNIDADE)
            btn_extra = gr.Button(T.BTN_EXTRAORDINARIA)
        with gr.Row(visible=sessao.contexto is not None and sessao.contexto.estado.total_aulas > 0) as acoes_com_aulas2:
            btn_alterar = gr.Button(T.BTN_ALTERAR_PLANEJAMENTO)
            btn_historico = gr.Button(T.BTN_VER_HISTORICO)
            btn_relatorio = gr.Button(T.BTN_GERAR_RELATORIO)
        with gr.Row(visible=sessao.contexto is not None and sessao.contexto.estado.total_aulas == 0) as acoes_sem_aulas:
            btn_primeira = gr.Button(T.BTN_PRIMEIRA_AULA, variant="primary")
            btn_retroativa = gr.Button(T.BTN_AULA_JA_REALIZADA)

        def carregar(texto, escolhido):
            alvo = (texto or "").strip() or (escolhido or "")
            if not alvo:
                return C.aviso(T.DIGITE_CODIGO), _painel_atual(sessao), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(choices=_recentes(sessao))
            try:
                cod = codes.normalizar_e_validar(alvo)
            except ValueError:
                return C.erro(T.CODIGO_INVALIDO), _painel_atual(sessao), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(choices=_recentes(sessao))
            try:
                ctx = sessao.carregar(cod)
            except RegistroNaoEncontrado:
                return C.erro(T.CODIGO_NAO_ENCONTRADO), _painel_atual(sessao), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(choices=_recentes(sessao))
            tem = ctx.estado.total_aulas > 0
            return (
                C.ok(T.DADOS_RECUPERADOS),
                C.painel_retorno(ctx, sessao),
                gr.update(visible=tem),
                gr.update(visible=tem),
                gr.update(visible=not tem),
                gr.update(choices=_recentes(sessao)),
            )

        saidas = [mensagem, painel, acoes_com_aulas, acoes_com_aulas2, acoes_sem_aulas, recentes]
        btn_carregar.click(C.protegido(carregar), [codigo, recentes], saidas)
        codigo.submit(C.protegido(carregar), [codigo, recentes], saidas)

        def ao_selecionar():
            ctx = sessao.recarregar()
            tem = ctx is not None and ctx.estado.total_aulas > 0
            return (
                _painel_atual(sessao),
                gr.update(visible=tem),
                gr.update(visible=tem),
                gr.update(visible=ctx is not None and not tem),
                gr.update(choices=_recentes(sessao)),
            )

        tab.select(ao_selecionar, None, [painel, acoes_com_aulas, acoes_com_aulas2, acoes_sem_aulas, recentes])

    return {
        "tab": tab,
        "codigo": codigo,
        "painel": painel,
        "mensagem": mensagem,
        "btn_continuar": btn_continuar,
        "btn_revisao": btn_revisao,
        "btn_nova_unidade": btn_nova_unidade,
        "btn_extra": btn_extra,
        "btn_alterar": btn_alterar,
        "btn_historico": btn_historico,
        "btn_relatorio": btn_relatorio,
        "btn_primeira": btn_primeira,
        "btn_retroativa": btn_retroativa,
        "atualizar": ao_selecionar,
        "saidas_atualizar": [painel, acoes_com_aulas, acoes_com_aulas2, acoes_sem_aulas, recentes],
    }


def _painel_atual(sessao: Sessao) -> str:
    if sessao.contexto is None:
        return T.NENHUM_REGISTRO_CARREGADO
    return C.painel_retorno(sessao.contexto, sessao)


def _recentes(sessao: Sessao) -> list:
    saida = []
    for cod in sessao.repo.listar_codigos():
        try:
            reg = sessao.repo.ler_registro(cod)
            quem = reg.identificacao or (reg.turma.nome if reg.turma else "") or cod
            saida.append((f"{cod} · {quem}", cod))
        except Exception:
            saida.append((cod, cod))
    return saida
