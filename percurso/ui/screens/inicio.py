"""Tela inicial (SPEC §6.2): identidade, modo ativo, atalhos, onboarding e pergunta sobre Gemini."""
from __future__ import annotations

import gradio as gr

from .. import common as C
from .. import texts as T
from ..session import Sessao


def montar(sessao: Sessao) -> dict:
    with gr.Tab(T.ABA_INICIO, id="inicio") as tab:
        gr.HTML(
            f"<p class='percurso-titulo'>{T.APP_NOME}</p>"
            f"<p class='percurso-subtitulo'>{T.APP_SUBTITULO}</p>"
            f"<p class='percurso-frase'>«{T.APP_FRASE}»</p>"
        )
        badge = gr.HTML(C.badge_modo(sessao))
        mensagens = gr.Markdown(_mensagens_iniciais(sessao))

        # --- lembrete mensal de apoio (uma vez por mês; já gravado antes de exibir) ---
        with gr.Group(visible=sessao.mostrar_lembrete_apoio) as lembrete:
            gr.Markdown(f"### {T.APOIO_LEMBRETE_TITULO}\n\n{T.APOIO_LEMBRETE_CORPO}")
            with gr.Row():
                btn_lembrete_apoiar = gr.Button(T.BTN_APOIAR_MP, variant="secondary")
                btn_lembrete_fechar = gr.Button(T.BTN_CONTINUAR_NO_PERCURSO, variant="primary")
            gr.Markdown(f"_{T.APOIO_SEM_BLOQUEIO}_")

        # --- pergunta sobre Gemini (nunca persistida) ---
        with gr.Group() as grupo_gemini:
            gr.Markdown(f"**{T.PERGUNTA_GEMINI}**")
            with gr.Row():
                btn_usar_gemini = gr.Button(T.BTN_USAR_GEMINI, variant="primary")
                btn_sem_gemini = gr.Button(T.BTN_SEM_GEMINI, variant="secondary")
            with gr.Group(visible=False) as grupo_chave:
                gr.Markdown(f"**{T.GEMINI_NAO_CONFIGURADO}**")
                chave_sessao = gr.Textbox(label=T.GEMINI_CHAVE_SESSAO, type="password")
                with gr.Row():
                    btn_usar_chave = gr.Button(T.BTN_USAR_GEMINI, variant="primary")
                    btn_aprender = gr.Button(T.BTN_APRENDER_CONFIGURAR, variant="secondary")
                    btn_sem_gemini2 = gr.Button(T.BTN_SEM_GEMINI, variant="secondary")
            resultado_gemini = gr.HTML("")

        gr.Markdown("### O que você quer fazer?")
        with gr.Row():
            btn_continuar = gr.Button(T.BTN_CONTINUAR, variant="primary")
            btn_novo = gr.Button(T.BTN_NOVO_REGISTRO)
            btn_planejar = gr.Button(T.BTN_PLANEJAR)
        with gr.Row():
            btn_pesquisar = gr.Button(T.BTN_PESQUISAR)
            btn_biblioteca = gr.Button(T.BTN_BIBLIOTECA)
            btn_relatorios = gr.Button(T.BTN_RELATORIOS)
            btn_config = gr.Button(T.BTN_CONFIGURACOES)
        with gr.Row(elem_classes=["percurso-apoio"]):
            btn_apoiar = gr.Button(T.BTN_APOIAR, size="sm")

    return {
        "tab": tab,
        "badge": badge,
        "mensagens": mensagens,
        "lembrete": lembrete,
        "btn_lembrete_apoiar": btn_lembrete_apoiar,
        "btn_lembrete_fechar": btn_lembrete_fechar,
        "grupo_gemini": grupo_gemini,
        "grupo_chave": grupo_chave,
        "chave_sessao": chave_sessao,
        "btn_usar_gemini": btn_usar_gemini,
        "btn_sem_gemini": btn_sem_gemini,
        "btn_usar_chave": btn_usar_chave,
        "btn_aprender": btn_aprender,
        "btn_sem_gemini2": btn_sem_gemini2,
        "resultado_gemini": resultado_gemini,
        "btn_continuar": btn_continuar,
        "btn_novo": btn_novo,
        "btn_planejar": btn_planejar,
        "btn_pesquisar": btn_pesquisar,
        "btn_biblioteca": btn_biblioteca,
        "btn_relatorios": btn_relatorios,
        "btn_config": btn_config,
        "btn_apoiar": btn_apoiar,
    }


def _mensagens_iniciais(sessao: Sessao) -> str:
    L = []
    if sessao.mensagens_inicio:
        L.append(" · ".join(sessao.mensagens_inicio))
    if not sessao.repo.professor_existe() or not sessao.repo.ler_professor().onboarding_concluido:
        L.append(f"### {T.BOAS_VINDAS}\n\n{T.ONBOARDING_INTRO}\n\n{T.ONBOARDING_PERFIL}")
    else:
        est = sessao.repo.estatisticas()
        L.append(f"Você tem **{est['registros']}** registro(s) e **{est['aulas']}** aula(s) guardados no seu Drive.")
    if sessao.modo_ia != "gemini":
        L.append(f"_{T.AVISO_ESSENCIAL}_")
    return "\n\n".join(L)
