"""Registrar aula (SPEC §6.5), inclusive retroativa, com classificação de conteúdos e rubrica."""
from __future__ import annotations

from typing import Any, Dict, List

import gradio as gr

from ...core import grading, state as state_mod
from ...core.models import Aula, BlocoCronograma, ConteudoTrabalhado, Fonte, FrequenciaTurma, Horario
from ...utils import dates
from .. import common as C
from .. import texts as T
from ..session import Sessao

MAX_CRITERIOS = 8
MAX_CLASSIFICACAO = 12


def _criterios(sessao: Sessao) -> List[str]:
    ctx = sessao.contexto
    if ctx is None:
        return []
    reg = ctx.registro
    ad = sessao.adaptador(reg.dominio)
    return grading.criterios_ativos(reg, ad.rubrica_padrao(reg.instrumento, reg.modalidade, reg.idade), sessao.repo.ler_rubricas())[:MAX_CRITERIOS]


def montar(sessao: Sessao) -> dict:
    with gr.Tab(T.ABA_AULA, id="aula") as tab:
        cabecalho = gr.HTML(C.cabecalho_registro(sessao))
        gr.Markdown(f"## {T.AULA_TITULO}")
        with gr.Row():
            data = gr.Textbox(label=T.AULA_DATA, value=dates.hoje(sessao.fuso).isoformat())
            tipo_aula = gr.Dropdown(label=T.AULA_TIPO, choices=T.opcoes(T.TIPOS_AULA), value="continuidade")
            frequencia = gr.Dropdown(label=T.AULA_FREQUENCIA, choices=T.opcoes(T.FREQUENCIAS), value=None)
        with gr.Row():
            previsto_info = gr.Markdown("")
            manter = gr.Radio(label=T.AULA_HORARIO_PREVISTO, choices=[(T.AULA_MANTER, "manter"), (T.AULA_ALTERAR, "alterar")], value="manter")
        with gr.Row():
            inicio_real = gr.Textbox(label=T.AULA_INICIO_REAL)
            termino_real = gr.Textbox(label=T.AULA_TERMINO_REAL)
        with gr.Group(visible=False) as grupo_turma:
            presentes = gr.CheckboxGroup(label=T.AULA_FREQUENCIA_TURMA, choices=[])
            n_presentes = gr.Number(label=T.AULA_N_PRESENTES, value=None, precision=0, minimum=0)
        unidade = gr.Textbox(label=T.AULA_UNIDADE)
        with gr.Row():
            conteudo_planejado = gr.Textbox(label=T.AULA_CONTEUDO_PLANEJADO, lines=3)
            conteudo_realizado = gr.Textbox(label=T.AULA_CONTEUDO_REALIZADO, lines=3)
        with gr.Row():
            btn_classificar = gr.Button(T.BTN_CLASSIFICAR)
            btn_propor = gr.Button(T.BTN_PROPOR_CLASSIFICACAO)
        proposta_msg = gr.HTML("")
        gr.Markdown(f"**{T.AULA_CLASSIFICACAO}**")
        classificacoes = []
        with gr.Group():
            for i in range(MAX_CLASSIFICACAO):
                with gr.Row(visible=False) as linha:
                    nome = gr.Textbox(label="Conteúdo", interactive=False, scale=2)
                    sit = gr.Radio(label="Situação", choices=T.opcoes(T.SITUACOES), value="em_desenvolvimento", scale=3)
                classificacoes.append((linha, nome, sit))
        with gr.Row():
            objetivos = gr.Textbox(label=T.AULA_OBJETIVOS, lines=2)
            atividades = gr.Textbox(label=T.AULA_ATIVIDADES, lines=2)
            materiais = gr.Textbox(label=T.AULA_MATERIAIS, lines=2)
        gr.Markdown(f"**{T.AULA_RENDIMENTO}**")
        notas = []
        with gr.Row():
            for i in range(MAX_CRITERIOS):
                notas.append(gr.Dropdown(label=f"Critério {i + 1}", choices=["", "1", "2", "3", "4", "5"], value="", visible=False))
        avaliacao = gr.Textbox(label=T.AULA_AVALIACAO, lines=2)
        with gr.Row():
            dificuldades = gr.Textbox(label=T.AULA_DIFICULDADES, lines=2)
            conquistas = gr.Textbox(label=T.AULA_CONQUISTAS, lines=2)
        with gr.Row():
            observacoes = gr.Textbox(label=T.AULA_OBSERVACOES, lines=2)
            tarefas = gr.Textbox(label=T.AULA_TAREFAS, lines=2)
        with gr.Row():
            proximo_passo = gr.Textbox(label=T.AULA_PROXIMO_PASSO)
            repertorio = gr.Textbox(label=T.AULA_REPERTORIO, lines=2)
        plano_origem = gr.Textbox(visible=False)
        btn_salvar = gr.Button(T.BTN_SALVAR_AULA, variant="primary")
        resultado = gr.HTML("")

        # ------------------------------------------------------------ helpers
        def _horario_previsto(dt: str):
            ctx = sessao.contexto
            if ctx is None:
                return "", "", ""
            ag = ctx.registro.agenda
            ini = ag.inicio or ""
            fim = ag.termino or (dates.somar_minutos(ini, ag.duracao_min) if ini else "")
            info = f"Horário previsto pela agenda: **{ini}–{fim}** ({ag.duracao_min} min)" if ini else "Sem horário na agenda."
            return info, ini, fim

        def preencher_formulario():
            """Preenche a partir de sessao.formulario_aula (vindo de um plano) ou dos padrões da agenda."""
            ctx = sessao.contexto
            f = sessao.formulario_aula or {}
            info, ini, fim = _horario_previsto("")
            crit = _criterios(sessao)
            rub = sessao.repo.ler_rubricas()
            notas_upd = []
            for i in range(MAX_CRITERIOS):
                if i < len(crit):
                    notas_upd.append(gr.update(visible=True, label=grading.rotulo(crit[i], rub), value=""))
                else:
                    notas_upd.append(gr.update(visible=False, value=""))
            cls = f.get("classificacao") or []
            cls_upd = []
            for i in range(MAX_CLASSIFICACAO):
                if i < len(cls):
                    cls_upd += [gr.update(visible=True), gr.update(value=cls[i]["conteudo"]), gr.update(value=cls[i]["situacao"])]
                else:
                    cls_upd += [gr.update(visible=False), gr.update(value=""), gr.update(value="em_desenvolvimento")]
            eh_turma = ctx is not None and ctx.registro.eh_turma
            alunos = [(a.identificacao, a.id) for a in (ctx.registro.turma.alunos if ctx and ctx.registro.turma else [])]
            saida = [
                C.cabecalho_registro(sessao),
                gr.update(value=f.get("data") or dates.hoje(sessao.fuso).isoformat()),
                gr.update(value=f.get("tipo_aula") or "continuidade"),
                info,
                gr.update(value=ini),
                gr.update(value=fim),
                gr.update(visible=eh_turma),
                gr.update(choices=alunos, value=[]),
                gr.update(value=f.get("unidade") or ""),
                C.juntar(f.get("conteudo_planejado") or []),
                C.juntar([c["conteudo"] for c in cls]),
                C.juntar(f.get("objetivos") or []),
                C.juntar(f.get("atividades") or []),
                C.juntar(f.get("materiais") or []),
                f.get("plano_origem") or "",
            ]
            return saida + notas_upd + cls_upd + [None, None, "", "", "", "", "", "", "", ""]

        saidas_preencher = [cabecalho, data, tipo_aula, previsto_info, inicio_real, termino_real, grupo_turma, presentes, unidade, conteudo_planejado, conteudo_realizado, objetivos, atividades, materiais, plano_origem] + notas + [c for tri in classificacoes for c in tri] + [frequencia, n_presentes, avaliacao, dificuldades, conquistas, observacoes, tarefas, proximo_passo, repertorio, resultado]
        tab.select(preencher_formulario, None, saidas_preencher)

        def classificar(texto):
            ctx = sessao.contexto
            itens = C.linhas(texto)[:MAX_CLASSIFICACAO]
            pre = state_mod.classificacao_pre_preenchida(ctx.estado if ctx else state_mod.EstadoAtual(), itens)
            upd = []
            for i in range(MAX_CLASSIFICACAO):
                if i < len(pre):
                    upd += [gr.update(visible=True), gr.update(value=pre[i]["conteudo"]), gr.update(value=pre[i]["situacao"])]
                else:
                    upd += [gr.update(visible=False), gr.update(value=""), gr.update(value="em_desenvolvimento")]
            return upd

        btn_classificar.click(classificar, [conteudo_realizado], [c for tri in classificacoes for c in tri])

        def propor(texto, aval, dif, conq, obs):
            """Proposta da IA (SPEC §4.3): o modelo propõe, o professor confirma. Sem Gemini, usa o estado."""
            ctx = sessao.contexto
            itens = C.linhas(texto)[:MAX_CLASSIFICACAO]
            if ctx is None:
                return [C.aviso(T.NENHUM_REGISTRO_CARREGADO)] + classificar(texto)
            if not (sessao.modo_ia == "gemini" and sessao.gemini_pronto):
                return [C.aviso(T.SOMENTE_MODO_INTELIGENTE)] + classificar(texto)
            from ...ai import classificacao as ai_cls

            prop = ai_cls.propor(sessao, itens, avaliacao=aval or "", dificuldades=C.linhas(dif), conquistas=C.linhas(conq), observacoes=obs or "")
            upd = []
            for i in range(MAX_CLASSIFICACAO):
                if i < len(prop):
                    upd += [gr.update(visible=True), gr.update(value=prop[i]["conteudo"], info=prop[i].get("motivo", "")), gr.update(value=prop[i]["situacao"])]
                else:
                    upd += [gr.update(visible=False), gr.update(value="", info=""), gr.update(value="em_desenvolvimento")]
            return [C.ok(T.CLASSIFICACAO_PROPOSTA)] + upd

        btn_propor.click(C.protegido(propor), [conteudo_realizado, avaliacao, dificuldades, conquistas, observacoes], [proposta_msg] + [c for tri in classificacoes for c in tri])

        def salvar(*valores):
            ctx = sessao.contexto
            if ctx is None:
                return C.aviso(T.NENHUM_REGISTRO_CARREGADO)
            v = list(valores)
            (data_v, tipo_v, freq_v, manter_v, ini_v, fim_v, pres_v, npres_v, unid_v, cplan_v, creal_v, obj_v, ativ_v, mat_v, aval_v, dif_v, conq_v, obs_v, tar_v, prox_v, rep_v, plano_v) = v[:22]
            if freq_v not in T.FREQUENCIAS:
                return C.aviso("Escolha a frequência antes de salvar a aula.")
            notas_v = v[22:22 + MAX_CRITERIOS]
            cls_v = v[22 + MAX_CRITERIOS:]
            try:
                d = dates.parse_data(data_v)
            except ValueError:
                return C.erro(T.AULA_DATA_INVALIDA)
            ag = ctx.registro.agenda
            prev_ini, prev_fim = ag.inicio or "", ag.termino or ""
            try:
                if manter_v == "manter" and prev_ini:
                    real_ini, real_fim = prev_ini, prev_fim
                else:
                    real_ini, real_fim = (ini_v or "").strip(), (fim_v or "").strip()
                    if real_ini:
                        dates.parse_hora(real_ini)
                    if real_fim:
                        dates.parse_hora(real_fim)
            except ValueError:
                return C.erro(T.AULA_HORA_INVALIDA)
            dur_prev = ag.duracao_min or (dates.minutos_entre(prev_ini, prev_fim) if prev_ini and prev_fim else 50)
            dur_real = dates.minutos_entre(real_ini, real_fim) if real_ini and real_fim else dur_prev
            conteudos = C.linhas(creal_v)
            realizada = freq_v in ("presente", "reposicao", "aula_extra")
            if realizada and not conteudos:
                return C.erro(T.AULA_CONTEUDO_OBRIGATORIO)
            # classificação: usa as linhas visíveis cujo nome bate com os conteúdos
            mapa_cls = {}
            for i in range(MAX_CLASSIFICACAO):
                nome_i = (cls_v[i * 2] or "").strip()
                sit_i = cls_v[i * 2 + 1] or "em_desenvolvimento"
                if nome_i:
                    mapa_cls[nome_i.lower()] = sit_i
            classificacao = [ConteudoTrabalhado(conteudo=c, situacao=mapa_cls.get(c.lower(), "em_desenvolvimento")) for c in conteudos]
            crit = _criterios(sessao)
            rendimento = {}
            for i, cid in enumerate(crit):
                val = notas_v[i] if i < len(notas_v) else ""
                if val not in ("", None):
                    rendimento[cid] = int(val)
            freq_turma = None
            if ctx.registro.eh_turma:
                alunos_ids = [a.id for a in (ctx.registro.turma.alunos if ctx.registro.turma else [])]
                if alunos_ids:
                    pres = list(pres_v or [])
                    freq_turma = FrequenciaTurma(presentes=pres, ausentes=[a for a in alunos_ids if a not in pres])
                elif npres_v not in (None, ""):
                    freq_turma = FrequenciaTurma(n_presentes=int(npres_v))
            fontes = [Fonte.model_validate(f) for f in (sessao.formulario_aula or {}).get("fontes_utilizadas", [])]
            crono = [BlocoCronograma.model_validate(b) for b in (sessao.formulario_aula or {}).get("cronograma", [])]
            aula = Aula(
                id="",
                data=d.isoformat(),
                dia_semana=dates.dia_semana(d),
                horario_previsto=Horario(inicio=prev_ini, termino=prev_fim),
                horario_real=Horario(inicio=real_ini, termino=real_fim) if realizada else Horario(),
                duracao_prevista_min=dur_prev,
                duracao_real_min=dur_real if realizada else 0,
                frequencia=freq_v,
                frequencia_turma=freq_turma,
                tipo_aula=tipo_v,
                conteudo_planejado=C.linhas(cplan_v),
                conteudo_realizado=conteudos,
                classificacao_conteudos=classificacao,
                objetivos=C.linhas(obj_v),
                atividades=C.linhas(ativ_v),
                materiais=C.linhas(mat_v),
                cronograma=crono,
                rendimento=rendimento,
                avaliacao_qualitativa=(aval_v or "").strip(),
                dificuldades=C.linhas(dif_v),
                conquistas=C.linhas(conq_v),
                observacoes=(obs_v or "").strip(),
                tarefas=C.linhas(tar_v),
                proximo_passo=(prox_v or "").strip(),
                repertorio_trabalhado=C.linhas(rep_v),
                habilidades_curriculares=list((sessao.formulario_aula or {}).get("habilidades_curriculares", [])),
                fontes_utilizadas=fontes,
                modo_ia="gemini" if sessao.modo_ia == "gemini" and sessao.gemini_pronto else "essencial",
                plano_origem=(plano_v or "").strip() or None,
                unidade=(unid_v or "").strip(),
            )
            numero = sessao.registrar_aula(aula)
            sessao.formulario_aula = {}
            return C.ok(T.AULA_SALVA.format(numero=numero, codigo=ctx.codigo))

        entradas = [data, tipo_aula, frequencia, manter, inicio_real, termino_real, presentes, n_presentes, unidade, conteudo_planejado, conteudo_realizado, objetivos, atividades, materiais, avaliacao, dificuldades, conquistas, observacoes, tarefas, proximo_passo, repertorio, plano_origem] + notas + [c for (_, n, s) in classificacoes for c in (n, s)]
        btn_salvar.click(C.protegido(salvar, T.ERRO_GRAVACAO), entradas, [resultado])

    return {"tab": tab, "preencher": preencher_formulario, "saidas_preencher": saidas_preencher, "tipo_aula": tipo_aula}
