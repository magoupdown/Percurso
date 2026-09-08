"""Monta e lança a interface Gradio (SPEC D1, §6)."""
from __future__ import annotations

from typing import Optional

from .ui import texts as T
from .ui import theme
from .ui.session import Sessao
from .utils.logging import obter

log = obter("app")


def montar_app(sessao: Sessao):
    import gradio as gr

    from .ui import common as C
    from .ui.screens import ajuda, apoio, aula, configuracoes, continuar, historico, inicio, novo_registro, planejar

    with gr.Blocks(title=f"{T.APP_NOME} — {T.APP_SUBTITULO}") as demo:
        with gr.Tabs() as abas:
            s_inicio = inicio.montar(sessao)
            s_continuar = continuar.montar(sessao)
            s_novo = novo_registro.montar(sessao)
            s_planejar = planejar.montar(sessao)
            s_aula = aula.montar(sessao)
            s_historico = historico.montar(sessao)
            s_biblioteca = _montar_opcional("biblioteca", sessao)
            s_pesquisar = _montar_opcional("pesquisar", sessao)
            s_relatorios = _montar_opcional("relatorios", sessao)
            s_config = configuracoes.montar(sessao)
            s_apoio = apoio.montar(sessao)
            s_ajuda = ajuda.montar(sessao)

        # ---------------------------------------------------------- navegação
        def ir(aba_id: str):
            return lambda: gr.update(selected=aba_id)

        s_inicio["btn_continuar"].click(ir("continuar"), None, [abas])
        s_inicio["btn_novo"].click(ir("novo"), None, [abas])
        s_inicio["btn_planejar"].click(ir("planejar"), None, [abas])
        s_inicio["btn_config"].click(ir("config"), None, [abas])
        s_inicio["btn_apoiar"].click(ir("apoio"), None, [abas])
        s_inicio["btn_lembrete_apoiar"].click(ir("apoio"), None, [abas])
        s_inicio["btn_lembrete_fechar"].click(lambda: gr.update(visible=False), None, [s_inicio["lembrete"]])
        s_inicio["btn_pesquisar"].click(ir("pesquisar" if s_pesquisar else "ajuda"), None, [abas])
        s_inicio["btn_biblioteca"].click(ir("biblioteca" if s_biblioteca else "ajuda"), None, [abas])
        s_inicio["btn_relatorios"].click(ir("relatorios" if s_relatorios else "ajuda"), None, [abas])
        s_inicio["btn_aprender"].click(ir("ajuda"), None, [abas])

        # botões do painel de retorno → planejar com tipo pré-selecionado
        def planejar_com(tipo: str):
            def _f():
                return gr.update(selected="planejar"), gr.update(value=tipo)

            return _f

        s_continuar["btn_continuar"].click(planejar_com("continuidade"), None, [abas, s_planejar["tipo_aula"]])
        s_continuar["btn_revisao"].click(planejar_com("revisao"), None, [abas, s_planejar["tipo_aula"]])
        s_continuar["btn_nova_unidade"].click(planejar_com("nova_unidade"), None, [abas, s_planejar["tipo_aula"]])
        s_continuar["btn_extra"].click(planejar_com("extraordinaria"), None, [abas, s_planejar["tipo_aula"]])
        s_continuar["btn_alterar"].click(planejar_com("continuidade"), None, [abas, s_planejar["tipo_aula"]])
        s_continuar["btn_primeira"].click(planejar_com("continuidade"), None, [abas, s_planejar["tipo_aula"]])
        s_continuar["btn_historico"].click(ir("historico"), None, [abas])
        s_continuar["btn_relatorio"].click(ir("relatorios" if s_relatorios else "historico"), None, [abas])

        def aula_retroativa():
            sessao.formulario_aula = {"tipo_aula": "retroativa"}
            return gr.update(selected="aula")

        s_continuar["btn_retroativa"].click(aula_retroativa, None, [abas])
        s_planejar["btn_registrar"].click(lambda: gr.update(selected="aula"), None, [abas])

        # ----------------------------------------------------------- Gemini
        def usar_gemini():
            from .ai import gemini

            r = gemini.ativar(sessao)
            if r.ok:
                return C.ok(T.GEMINI_ATIVADO), gr.update(visible=False), C.badge_modo(sessao), gr.update(visible=False)
            if r.motivo == "sem_chave":
                return "", gr.update(visible=True), C.badge_modo(sessao), gr.update(visible=True)
            return C.erro(r.mensagem), gr.update(visible=True), C.badge_modo(sessao), gr.update(visible=True)

        def usar_chave(chave):
            from .ai import gemini

            r = gemini.ativar(sessao, chave_sessao=(chave or "").strip() or None)
            if r.ok:
                return C.ok(T.GEMINI_ATIVADO), gr.update(visible=False), C.badge_modo(sessao), gr.update(visible=False), ""
            return C.erro(r.mensagem), gr.update(visible=True), C.badge_modo(sessao), gr.update(visible=True), ""

        def sem_gemini():
            sessao.modo_ia = "essencial"
            sessao.gemini_pronto = False
            return C.aviso(T.AVISO_ESSENCIAL), gr.update(visible=False), C.badge_modo(sessao), gr.update(visible=False)

        saidas_g = [s_inicio["resultado_gemini"], s_inicio["grupo_chave"], s_inicio["badge"], s_inicio["grupo_gemini"]]
        s_inicio["btn_usar_gemini"].click(_seguro(usar_gemini), None, saidas_g)
        s_inicio["btn_usar_chave"].click(_seguro(usar_chave), [s_inicio["chave_sessao"]], saidas_g + [s_inicio["chave_sessao"]])
        s_inicio["btn_sem_gemini"].click(sem_gemini, None, saidas_g)
        s_inicio["btn_sem_gemini2"].click(sem_gemini, None, saidas_g)

    return demo


def _seguro(fn):
    import gradio as gr

    def _w(*a):
        try:
            return fn(*a)
        except Exception as e:  # noqa: BLE001
            log.error("erro Gemini: %s", e)
            from .ui import common as C

            return C.erro(T.GEMINI_SEM_RESPOSTA), gr.update(), gr.update(), gr.update()

    return _w


def _montar_opcional(nome: str, sessao: Sessao) -> Optional[dict]:
    """Abas de entregas posteriores (E3–E5). Só aparecem quando o módulo existe — nunca 'Em breve'."""
    try:
        if nome == "biblioteca":
            from .ui.screens import biblioteca as m
        elif nome == "pesquisar":
            from .ui.screens import pesquisar as m
        elif nome == "relatorios":
            from .ui.screens import relatorios as m
        else:
            return None
    except ImportError:
        return None
    return m.montar(sessao)


def lancar(demo, inline: bool = True, share: bool = False, **kw):
    """Lança inline no Colab (D1) ou em janela local."""
    return demo.launch(
        inline=inline,
        share=share,
        theme=theme.tema(),
        css=theme.CSS,
        quiet=True,
        show_error=True,
        **kw,
    )
