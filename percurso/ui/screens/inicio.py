"""Tela inicial (SPEC §6.2): identidade, modo ativo, atalhos, onboarding e pergunta sobre Gemini."""
from __future__ import annotations

import gradio as gr

from .. import common as C
from .. import texts as T
from ..session import Sessao


def montar(sessao: Sessao) -> dict:
    with gr.Tab(T.ABA_INICIO, id="inicio") as tab:
        with gr.Column(elem_classes=["percurso-identidade"]):
            badge = gr.HTML(C.badge_modo(sessao), elem_classes=["percurso-status"])
            gr.HTML(
                f"<h1 class='percurso-titulo'>{T.APP_NOME}</h1>"
                f"<p class='percurso-subtitulo'>{T.APP_SUBTITULO}</p>"
                f"<p class='percurso-frase'>{T.APP_FRASE}</p>"
            )

        with gr.Column(elem_classes=["percurso-acoes"]):
            gr.Markdown(f"## {T.INICIO_ACOES}\n\n{T.INICIO_INTRO}")
            with gr.Row(elem_classes=["percurso-acoes-principais"]):
                btn_continuar = gr.Button("Continuar aluno ou turma", variant="primary")
                btn_novo = gr.Button("Novo registro")
                btn_planejar = gr.Button("Planejar aula")
            gr.Markdown(f"### {T.INICIO_ORGANIZACAO}", elem_classes=["percurso-divisor"])
            with gr.Row(elem_classes=["percurso-utilidades"]):
                btn_pesquisar = gr.Button("Pesquisar")
                btn_biblioteca = gr.Button("Minha biblioteca")
                btn_relatorios = gr.Button("Relatórios")
                btn_config = gr.Button("Configurações")

        # --- pergunta sobre Gemini (nunca persistida) ---
        with gr.Group(elem_classes=["percurso-gemini"]) as grupo_gemini:
            gr.Markdown(f"### {T.INICIO_GEMINI}")
            with gr.Accordion("Como obter e configurar a chave do Gemini", open=False):
                gr.Markdown(T.TUTORIAL_GEMINI)
            gr.Markdown(f"**{T.PERGUNTA_GEMINI}**")
            with gr.Row():
                btn_usar_gemini = gr.Button("Usar Gemini", variant="primary")
                btn_sem_gemini = gr.Button("Continuar sem Gemini", variant="secondary")
            with gr.Group(visible=False) as grupo_chave:
                gr.Markdown(f"**{T.GEMINI_NAO_CONFIGURADO}**")
                chave_sessao = gr.Textbox(label=T.GEMINI_CHAVE_SESSAO, type="password", placeholder="Cole somente a chave criada no Google AI Studio", info="Uso temporário. Para reutilizar em outras sessões, salve como GEMINI_API_KEY nos Segredos do Colab.")
                with gr.Row():
                    btn_usar_chave = gr.Button("Usar Gemini", variant="primary")
                    btn_aprender = gr.Button(T.BTN_APRENDER_CONFIGURAR, variant="secondary")
                    btn_sem_gemini2 = gr.Button("Continuar sem Gemini", variant="secondary")
        resultado_gemini = gr.HTML("")
        with gr.Row():
            btn_reconfigurar = gr.Button("Configurar ou trocar chave Gemini", size="sm")
            btn_desconectar = gr.Button("Desconectar Gemini", size="sm")
        btn_reconfigurar.click(lambda: (gr.update(visible=True), gr.update(visible=True)), None, [grupo_gemini, grupo_chave])

        # --- consentimento de envio de trechos da biblioteca (SPEC §7.6) — só com Gemini ativo ---
        with gr.Group(visible=False) as grupo_consentimento:
            gr.Markdown(f"**{T.CONSENTIMENTO_TRECHOS}**")
            with gr.Row():
                btn_consentir_sim = gr.Button(T.BTN_CONSENTIR_TRECHOS_SIM, variant="primary")
                btn_consentir_nao = gr.Button(T.BTN_CONSENTIR_TRECHOS_NAO, variant="secondary")
            consentimento_msg = gr.HTML("")

        def consentir(valor: bool):
            def _f():
                sessao.consentimento_trechos = valor
                return C.ok(T.CONSENTIMENTO_REGISTRADO + (" Trechos poderão ser enviados." if valor else " Nenhum trecho da biblioteca será enviado."))

            return _f

        btn_consentir_sim.click(consentir(True), None, [consentimento_msg])
        btn_consentir_nao.click(consentir(False), None, [consentimento_msg])

        with gr.Accordion(T.INICIO_DADOS, open=False):
            mensagens = gr.Markdown(_mensagens_iniciais(sessao))
        tab.select(lambda: (_mensagens_iniciais(sessao), C.badge_modo(sessao)), None, [mensagens, badge])

        # --- lembrete mensal de apoio (uma vez por mês; já gravado antes de exibir) ---
        with gr.Group(visible=sessao.mostrar_lembrete_apoio) as lembrete:
            gr.Markdown(f"### {T.APOIO_LEMBRETE_TITULO}\n\n{T.APOIO_LEMBRETE_CORPO}")
            with gr.Row():
                btn_lembrete_apoiar = gr.Button(T.BTN_APOIAR_MP, variant="secondary")
                btn_lembrete_fechar = gr.Button(T.BTN_CONTINUAR_NO_PERCURSO, variant="primary")
            gr.Markdown(f"_{T.APOIO_SEM_BLOQUEIO}_")

        with gr.Row(elem_classes=["percurso-apoio"]):
            btn_apoiar = gr.Button(T.BTN_APOIAR, size="sm")

    return {
        "tab": tab,
        "btn_desconectar": btn_desconectar,
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
        "grupo_consentimento": grupo_consentimento,
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
