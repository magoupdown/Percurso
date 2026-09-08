"""Planejar aula (SPEC §8): próximo passo sugerido, plano completo, adaptação de duração, registro a partir do plano."""
from __future__ import annotations

import gradio as gr

from ...core import planner, schedule
from ...utils import dates
from .. import common as C
from .. import texts as T
from ..session import Sessao


def montar(sessao: Sessao) -> dict:
    with gr.Tab(T.ABA_PLANEJAR, id="planejar") as tab:
        cabecalho = gr.HTML(C.cabecalho_registro(sessao))
        gr.Markdown(f"## {T.PLANEJAR_TITULO}")
        with gr.Row():
            tipo_aula = gr.Dropdown(label=T.PLANEJAR_TIPO, choices=[(v, k) for k, v in T.TIPOS_AULA.items() if k != "retroativa"], value="continuidade")
            duracao = gr.Number(label=T.PLANEJAR_DURACAO, value=50, precision=0, minimum=5, maximum=300)
            data = gr.Textbox(label=T.AULA_DATA, value=dates.hoje(sessao.fuso).isoformat())
        with gr.Row():
            conteudo = gr.Textbox(label=T.PLANEJAR_CONTEUDO, scale=3)
            btn_sugerir = gr.Button(T.BTN_SUGERIR, scale=1)
        sugestao = gr.Markdown("")
        with gr.Row():
            objetivo = gr.Textbox(label=T.PLANEJAR_OBJETIVO)
            nova_unidade = gr.Textbox(label=T.PLANEJAR_NOVA_UNIDADE)
        recursos = gr.CheckboxGroup(label=T.PLANEJAR_RECURSOS, choices=T.opcoes(T.RECURSOS), value=[])
        observacoes = gr.Textbox(label=T.PLANEJAR_OBS, lines=2)
        onde = gr.CheckboxGroup(label=T.PLANEJAR_ONDE, choices=[("Minha Biblioteca", "biblioteca"), ("Base Curricular", "curricular"), ("Pesquisa Acadêmica", "academica")], value=[], visible=False)
        btn_gerar = gr.Button(T.BTN_GERAR_PLANO, variant="primary")
        status = gr.HTML("")
        plano_md = gr.Markdown(T.NENHUM_PLANO)
        with gr.Row():
            nova_duracao = gr.Number(label=T.PLANEJAR_DURACAO, value=50, precision=0, minimum=5, maximum=300)
            btn_adaptar = gr.Button(T.BTN_ADAPTAR_DURACAO)
        with gr.Row():
            btn_registrar = gr.Button(T.BTN_REGISTRAR_A_PARTIR_DO_PLANO, variant="primary")
            btn_descartar = gr.Button(T.BTN_DESCARTAR_PLANO)

        def ao_selecionar():
            ctx = sessao.recarregar()
            dur = ctx.registro.agenda.duracao_min if ctx else 50
            rec = list(ctx.registro.recursos_habituais) if ctx else []
            md = planner.plano_como_markdown(sessao.ultimo_plano, rubricas=sessao.repo.ler_rubricas()) if sessao.ultimo_plano else T.NENHUM_PLANO
            return C.cabecalho_registro(sessao), gr.update(value=dur), gr.update(value=dur), gr.update(value=rec), md, gr.update(visible=_pesquisa_disponivel())

        tab.select(ao_selecionar, None, [cabecalho, duracao, nova_duracao, recursos, plano_md, onde])

        def sugerir():
            if sessao.contexto is None:
                return C.aviso(T.NENHUM_REGISTRO_CARREGADO)
            s = planner.sugerir_proximo_passo(sessao.entrada_planejamento())
            return f"**{T.PROXIMO_PASSO_SUGERIDO}:** {s.conteudo}\n\n_{s.justificativa}_"

        btn_sugerir.click(C.protegido(sugerir), None, [sugestao])

        def gerar(tipo_v, dur_v, data_v, cont_v, obj_v, nu_v, rec_v, obs_v, onde_v):
            if sessao.contexto is None:
                return C.aviso(T.NENHUM_REGISTRO_CARREGADO), T.NENHUM_PLANO
            try:
                d = dates.parse_data(data_v)
            except ValueError:
                return C.erro(T.AULA_DATA_INVALIDA), T.NENHUM_PLANO
            extra = _pesquisar(sessao, cont_v, onde_v)
            entrada = sessao.entrada_planejamento(
                tipo_aula=tipo_v,
                conteudo=(cont_v or "").strip(),
                objetivo=(obj_v or "").strip(),
                duracao_min=int(dur_v or 50),
                recursos=list(rec_v or []),
                observacoes=(obs_v or "").strip(),
                data=d.isoformat(),
                nova_unidade=(nu_v or "").strip(),
                referencias=extra.get("referencias", []),
                consultas_realizadas=extra.get("consultas", []),
                habilidades_validadas=extra.get("habilidades", []),
            )
            plano = _gerar_plano(sessao, entrada)
            plano = sessao.repo.gravar_plano(plano)
            sessao.ultimo_plano = plano
            return C.ok(T.PLANO_SALVO), planner.plano_como_markdown(plano, rubricas=sessao.repo.ler_rubricas())

        btn_gerar.click(C.protegido(gerar), [tipo_aula, duracao, data, conteudo, objetivo, nova_unidade, recursos, observacoes, onde], [status, plano_md])

        def adaptar(nd):
            p = sessao.ultimo_plano
            if p is None:
                return C.aviso(T.NENHUM_PLANO), T.NENHUM_PLANO
            novos = schedule.adaptar_duracao(p.cronograma, int(nd or p.duracao_min))
            p.cronograma = novos
            p.duracao_min = int(nd or p.duracao_min)
            for a in p.atividades:
                for b in novos:
                    if a.bloco == b.etapa and a.bloco != "alternativa":
                        a.duracao_min = b.fim_min - b.inicio_min
                        break
            schedule.exigir_valido(p.cronograma, p.duracao_min)
            sessao.repo.gravar_plano(p)
            return C.ok(T.PLANO_SALVO), planner.plano_como_markdown(p, rubricas=sessao.repo.ler_rubricas())

        btn_adaptar.click(C.protegido(adaptar), [nova_duracao], [status, plano_md])

        def registrar():
            p = sessao.ultimo_plano
            if p is None or sessao.contexto is None:
                return C.aviso(T.NENHUM_PLANO)
            sessao.formulario_aula = planner.aula_a_partir_do_plano(p, sessao.contexto.estado)
            return C.ok(T.PLANO_PREENCHIDO)

        btn_registrar.click(C.protegido(registrar), None, [status])

        def descartar():
            p = sessao.ultimo_plano
            if p is None:
                return C.aviso(T.NENHUM_PLANO), T.NENHUM_PLANO
            p.status = "descartado"
            sessao.repo.gravar_plano(p)
            sessao.ultimo_plano = None
            return C.ok(T.PLANO_DESCARTADO), T.NENHUM_PLANO

        btn_descartar.click(C.protegido(descartar), None, [status, plano_md])

    return {"tab": tab, "tipo_aula": tipo_aula, "btn_registrar": btn_registrar, "status": status}


def _pesquisa_disponivel() -> bool:
    try:
        from ...research import integracao  # noqa: F401

        return True
    except Exception:
        return False


def _pesquisar(sessao: Sessao, tema: str, onde: list) -> dict:
    """Integra biblioteca/currículo/pesquisa acadêmica quando disponíveis (E3/E4). Nunca falha o plano."""
    if not onde:
        return {}
    try:
        from ...research import integracao

        return integracao.pesquisar_para_plano(sessao, tema, onde)
    except Exception as e:  # pragma: no cover
        C.log.warning("pesquisa integrada indisponível: %s", e)
        return {}


def _gerar_plano(sessao: Sessao, entrada):
    """Modo Inteligente gera plano contextual com validação; senão, modelo pedagógico."""
    if sessao.modo_ia == "gemini" and sessao.gemini_pronto:
        try:
            from ...ai import planning

            return planning.gerar_plano_gemini(sessao, entrada)
        except Exception as e:  # pragma: no cover
            C.log.warning("plano Gemini indisponível, usando modelo pedagógico: %s", e)
    return planner.gerar_plano(entrada)
