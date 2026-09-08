"""Histórico (SPEC §6.6): lista de aulas, busca estruturada, abrir/excluir aula, repertório."""
from __future__ import annotations

from typing import List, Optional

import gradio as gr

from ...core import grading, state as state_mod
from ...core.models import Aula, ItemRepertorio
from ...utils import dates
from .. import common as C
from .. import texts as T
from ..session import Sessao


def _norm(t: str) -> str:
    return " ".join((t or "").lower().split())


def filtrar(aulas: List[Aula], conteudo: str = "", dificuldade: str = "", inicio: str = "", fim: str = "", situacao: str = "") -> List[Aula]:
    saida = []
    for a in aulas:
        if inicio and a.data < inicio:
            continue
        if fim and a.data > fim:
            continue
        if conteudo:
            txt = _norm(" ".join(a.conteudo_realizado + a.conteudo_planejado + [c.conteudo for c in a.classificacao_conteudos]))
            if _norm(conteudo) not in txt:
                continue
        if dificuldade:
            txt = _norm(" ".join(a.dificuldades + [c.conteudo for c in a.classificacao_conteudos if c.situacao == "dificuldade"]))
            if _norm(dificuldade) not in txt:
                continue
        if situacao:
            if situacao in T.FREQUENCIAS:
                if a.frequencia != situacao:
                    continue
            elif situacao in T.SITUACOES:
                if not any(c.situacao == situacao for c in a.classificacao_conteudos):
                    continue
        saida.append(a)
    return saida


def aula_como_markdown(a: Aula, numero: int, rubricas=None) -> str:
    L = [f"### Aula {numero:02d} · {dates.formatar_data_br(a.data)} ({T.DIAS.get(a.dia_semana, a.dia_semana)})" if numero else f"### {dates.formatar_data_br(a.data)}"]
    L.append(f"**Situação:** {T.FREQUENCIAS.get(a.frequencia, a.frequencia)} · **Tipo:** {T.TIPOS_AULA.get(a.tipo_aula, a.tipo_aula)} · **Duração:** {a.duracao_real_min or a.duracao_prevista_min} min")
    if a.horario_real.inicio:
        L.append(f"**Horário:** previsto {a.horario_previsto.inicio}–{a.horario_previsto.termino} · real {a.horario_real.inicio}–{a.horario_real.termino}")
    if a.unidade:
        L.append(f"**Unidade:** {a.unidade}")
    if a.frequencia_turma:
        ft = a.frequencia_turma
        if ft.n_presentes is not None:
            L.append(f"**Presentes:** {ft.n_presentes}")
        elif ft.presentes or ft.ausentes:
            L.append(f"**Presentes:** {', '.join(ft.presentes) or '—'} · **Ausentes:** {', '.join(ft.ausentes) or '—'}")
    if a.conteudo_planejado:
        L.append("**Planejado:** " + "; ".join(a.conteudo_planejado))
    if a.classificacao_conteudos:
        L.append("**Trabalhado:** " + " · ".join(f"{c.conteudo} ({T.SITUACOES.get(c.situacao, c.situacao)})" for c in a.classificacao_conteudos))
    elif a.conteudo_realizado:
        L.append("**Trabalhado:** " + "; ".join(a.conteudo_realizado))
    if a.objetivos:
        L.append("**Objetivos:** " + "; ".join(a.objetivos))
    if a.atividades:
        L.append("**Atividades:** " + "; ".join(a.atividades))
    if a.rendimento:
        L.append("**Rendimento:** " + " · ".join(f"{grading.rotulo(k, rubricas)} {v}" for k, v in a.rendimento.items()))
    if a.avaliacao_qualitativa:
        L.append(f"**Avaliação:** {a.avaliacao_qualitativa}")
    if a.dificuldades:
        L.append("**Dificuldades:** " + "; ".join(a.dificuldades))
    if a.conquistas:
        L.append("**Conquistas:** " + "; ".join(a.conquistas))
    if a.repertorio_trabalhado:
        L.append("**Repertório:** " + "; ".join(a.repertorio_trabalhado))
    if a.tarefas:
        L.append("**Tarefas:** " + "; ".join(a.tarefas))
    if a.observacoes:
        L.append(f"**Observações:** {a.observacoes}")
    if a.proximo_passo:
        L.append(f"**Próximo passo:** {a.proximo_passo}")
    if a.habilidades_curriculares:
        L.append("**Habilidades curriculares:** " + ", ".join(a.habilidades_curriculares))
    if a.fontes_utilizadas:
        L.append("**Fontes:** " + "; ".join(f"{T.ORIGENS_FONTE.get(f.tipo, '')} {f.titulo}" for f in a.fontes_utilizadas))
    L.append(f"_Registrada em modo {a.modo_ia}_" + (f" · plano de origem: {a.plano_origem}" if a.plano_origem else ""))
    return "\n\n".join(L)


def tabela(aulas: List[Aula], numeros: dict) -> str:
    if not aulas:
        return T.HISTORICO_VAZIO
    L = ["| Aula | Data | Situação | Conteúdo | Resumo |", "|---|---|---|---|---|"]
    for a in aulas:
        n = numeros.get(a.id, 0)
        cont = ", ".join(c.conteudo for c in a.classificacao_conteudos) or ", ".join(a.conteudo_realizado)
        res = (a.observacoes or a.avaliacao_qualitativa or a.proximo_passo or "").split("\n")[0]
        L.append(f"| {n:02d} | {dates.formatar_data_br(a.data)} | {T.FREQUENCIAS.get(a.frequencia, a.frequencia)} | {cont[:60]} | {res[:60]} |" if n else f"| — | {dates.formatar_data_br(a.data)} | {T.FREQUENCIAS.get(a.frequencia, a.frequencia)} | {cont[:60]} | {res[:60]} |")
    return "\n".join(L)


def montar(sessao: Sessao) -> dict:
    with gr.Tab(T.ABA_HISTORICO, id="historico") as tab:
        cabecalho = gr.HTML(C.cabecalho_registro(sessao))
        gr.Markdown(f"## {T.HISTORICO_TITULO}")
        with gr.Accordion(T.HISTORICO_BUSCA, open=False):
            with gr.Row():
                b_conteudo = gr.Textbox(label=T.HISTORICO_BUSCA_CONTEUDO)
                b_dificuldade = gr.Textbox(label=T.HISTORICO_BUSCA_DIFICULDADE)
            with gr.Row():
                b_inicio = gr.Textbox(label=T.HISTORICO_BUSCA_INICIO)
                b_fim = gr.Textbox(label=T.HISTORICO_BUSCA_FIM)
                b_situacao = gr.Dropdown(label=T.HISTORICO_BUSCA_SITUACAO, choices=[("Todas", "")] + T.opcoes(T.FREQUENCIAS) + T.opcoes(T.SITUACOES), value="")
            btn_buscar = gr.Button(T.BTN_BUSCAR)
            with gr.Group(visible=False) as grupo_livre:
                pergunta = gr.Textbox(label=T.HISTORICO_PERGUNTA_LIVRE)
                btn_perguntar = gr.Button(T.BTN_BUSCAR)
                resposta_livre = gr.Markdown("")
        lista = gr.Markdown(_tabela_atual(sessao))
        with gr.Row():
            escolha = gr.Dropdown(label=T.HISTORICO_SELECIONE, choices=C.opcoes_aulas(sessao.contexto), value=None, scale=3)
            btn_abrir = gr.Button(T.BTN_ABRIR_AULA, scale=1)
        detalhe = gr.Markdown("")
        with gr.Row():
            btn_excluir = gr.Button(T.BTN_EXCLUIR_AULA, variant="stop")
            btn_confirmar_excluir = gr.Button(T.BTN_CONFIRMAR, variant="stop", visible=False)
        msg = gr.HTML("")

        gr.Markdown(f"## {T.REPERTORIO_TITULO}")
        rep_lista = gr.Markdown(_repertorio_md(sessao))
        with gr.Row():
            rep_obra = gr.Textbox(label=T.REPERTORIO_OBRA)
            rep_comp = gr.Textbox(label=T.REPERTORIO_COMPOSITOR)
            rep_arr = gr.Textbox(label=T.REPERTORIO_ARRANJO)
            rep_nivel = gr.Textbox(label=T.REPERTORIO_NIVEL)
            rep_estado = gr.Dropdown(label=T.REPERTORIO_ESTADO, choices=T.opcoes(T.ESTADOS_REPERTORIO), value="em_estudo")
        with gr.Row():
            btn_rep_add = gr.Button(T.BTN_ADICIONAR_REPERTORIO)
            rep_sel = gr.Dropdown(label=T.REPERTORIO_OBRA, choices=_rep_opcoes(sessao), value=None)
            rep_novo_estado = gr.Dropdown(label=T.REPERTORIO_ESTADO, choices=T.opcoes(T.ESTADOS_REPERTORIO), value="concluido")
            btn_rep_upd = gr.Button(T.BTN_ATUALIZAR_REPERTORIO)
        rep_msg = gr.HTML("")

        def ao_selecionar():
            sessao.recarregar()
            return C.cabecalho_registro(sessao), _tabela_atual(sessao), gr.update(choices=C.opcoes_aulas(sessao.contexto), value=None), "", _repertorio_md(sessao), gr.update(choices=_rep_opcoes(sessao)), gr.update(visible=sessao.modo_ia == "gemini" and sessao.gemini_pronto)

        saidas_sel = [cabecalho, lista, escolha, detalhe, rep_lista, rep_sel, grupo_livre]
        tab.select(ao_selecionar, None, saidas_sel)

        def buscar(c, d, i, f, s):
            ctx = sessao.contexto
            if ctx is None:
                return T.NENHUM_REGISTRO_CARREGADO
            try:
                i = dates.parse_data(i).isoformat() if (i or "").strip() else ""
                f = dates.parse_data(f).isoformat() if (f or "").strip() else ""
            except ValueError:
                return T.AULA_DATA_INVALIDA
            return tabela(filtrar(ctx.aulas, c, d, i, f, s), ctx.numeros)

        btn_buscar.click(C.protegido(buscar), [b_conteudo, b_dificuldade, b_inicio, b_fim, b_situacao], [lista])

        def perguntar(q):
            if sessao.contexto is None:
                return T.NENHUM_REGISTRO_CARREGADO
            try:
                from ...ai import historico as ai_hist

                return ai_hist.perguntar(sessao, q)
            except Exception as e:
                C.log.warning("pergunta livre falhou: %s", e)
                return T.GEMINI_SEM_RESPOSTA

        btn_perguntar.click(perguntar, [pergunta], [resposta_livre])

        def abrir(id_aula):
            ctx = sessao.contexto
            if ctx is None or not id_aula:
                return "", gr.update(visible=False)
            for a in ctx.aulas:
                if a.id == id_aula:
                    return aula_como_markdown(a, ctx.numeros.get(a.id, 0), sessao.repo.ler_rubricas()), gr.update(visible=False)
            return T.HISTORICO_VAZIO, gr.update(visible=False)

        btn_abrir.click(abrir, [escolha], [detalhe, btn_confirmar_excluir])
        escolha.change(abrir, [escolha], [detalhe, btn_confirmar_excluir])

        def pedir_confirmacao(id_aula):
            if not id_aula:
                return C.aviso(T.HISTORICO_SELECIONE), gr.update(visible=False)
            return C.aviso(T.CONFIRMAR_EXCLUSAO + " a aula selecionada."), gr.update(visible=True)

        btn_excluir.click(pedir_confirmacao, [escolha], [msg, btn_confirmar_excluir])

        def confirmar_excluir(id_aula):
            ctx = sessao.contexto
            if ctx is None or not id_aula:
                return C.aviso(T.HISTORICO_SELECIONE), gr.update(visible=False), _tabela_atual(sessao), gr.update(), ""
            sessao.repo.excluir_aula(ctx.codigo, id_aula)
            state_mod.atualizar_apos_aula(sessao.repo, ctx.codigo)
            sessao.recarregar()
            return C.ok(T.AULA_EXCLUIDA), gr.update(visible=False), _tabela_atual(sessao), gr.update(choices=C.opcoes_aulas(sessao.contexto), value=None), ""

        btn_confirmar_excluir.click(C.protegido(confirmar_excluir, T.ERRO_GRAVACAO), [escolha], [msg, btn_confirmar_excluir, lista, escolha, detalhe])

        def rep_add(obra, comp, arr, niv, est):
            ctx = sessao.contexto
            if ctx is None:
                return C.aviso(T.NENHUM_REGISTRO_CARREGADO), _repertorio_md(sessao), gr.update()
            if not (obra or "").strip():
                return C.aviso(T.REPERTORIO_OBRA), _repertorio_md(sessao), gr.update()
            rep = sessao.repo.ler_repertorio(ctx.codigo)
            rep.itens.append(ItemRepertorio(obra=obra.strip(), compositor=(comp or "").strip(), arranjo=(arr or "").strip(), nivel=(niv or "").strip(), estado=est or "em_estudo", inicio=dates.hoje(sessao.fuso).isoformat()))
            sessao.repo.gravar_repertorio(ctx.codigo, rep)
            sessao.recarregar()
            return C.ok(T.REPERTORIO_SALVO), _repertorio_md(sessao), gr.update(choices=_rep_opcoes(sessao))

        btn_rep_add.click(C.protegido(rep_add, T.ERRO_GRAVACAO), [rep_obra, rep_comp, rep_arr, rep_nivel, rep_estado], [rep_msg, rep_lista, rep_sel])

        def rep_upd(idx, novo):
            ctx = sessao.contexto
            if ctx is None or idx is None or idx == "":
                return C.aviso(T.REPERTORIO_OBRA), _repertorio_md(sessao)
            rep = sessao.repo.ler_repertorio(ctx.codigo)
            i = int(idx)
            if 0 <= i < len(rep.itens):
                rep.itens[i].estado = novo
                if novo == "concluido":
                    rep.itens[i].fim = dates.hoje(sessao.fuso).isoformat()
                sessao.repo.gravar_repertorio(ctx.codigo, rep)
                sessao.recarregar()
            return C.ok(T.REPERTORIO_SALVO), _repertorio_md(sessao)

        btn_rep_upd.click(C.protegido(rep_upd, T.ERRO_GRAVACAO), [rep_sel, rep_novo_estado], [rep_msg, rep_lista])

    return {"tab": tab, "atualizar": ao_selecionar, "saidas_atualizar": saidas_sel}


def _tabela_atual(sessao: Sessao) -> str:
    ctx = sessao.contexto
    if ctx is None:
        return T.NENHUM_REGISTRO_CARREGADO
    return tabela(ctx.aulas, ctx.numeros)


def _repertorio_md(sessao: Sessao) -> str:
    ctx = sessao.contexto
    if ctx is None or not ctx.repertorio.itens:
        return "_Nenhuma obra registrada._"
    L = ["| Obra | Compositor | Arranjo | Nível | Estado | Início | Fim |", "|---|---|---|---|---|---|---|"]
    for i in ctx.repertorio.itens:
        L.append(f"| {i.obra} | {i.compositor} | {i.arranjo} | {i.nivel} | {T.ESTADOS_REPERTORIO.get(i.estado, i.estado)} | {dates.formatar_data_br(i.inicio) if i.inicio else ''} | {dates.formatar_data_br(i.fim) if i.fim else ''} |")
    return "\n".join(L)


def _rep_opcoes(sessao: Sessao) -> list:
    ctx = sessao.contexto
    if ctx is None:
        return []
    return [(f"{i.obra} ({T.ESTADOS_REPERTORIO.get(i.estado, i.estado)})", str(k)) for k, i in enumerate(ctx.repertorio.itens)]
