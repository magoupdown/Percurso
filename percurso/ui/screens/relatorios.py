"""Relatórios (SPEC §12) e materiais (SPEC §8.5)."""
from __future__ import annotations

from pathlib import Path

import gradio as gr

from ...core import grading
from ...reports import builder, materials
from ...utils import dates
from .. import common as C
from .. import texts as T
from ..session import Sessao


def montar(sessao: Sessao) -> dict:
    with gr.Tab(T.ABA_RELATORIOS, id="relatorios") as tab:
        cabecalho = gr.HTML(C.cabecalho_registro(sessao))
        gr.Markdown(f"## {T.RELATORIOS_TITULO}")
        with gr.Row():
            tipo = gr.Dropdown(label=T.RELATORIO_TIPO, choices=[(v, k) for k, v in builder.TIPOS.items()], value="frequencia")
            inicio = gr.Textbox(label=T.RELATORIO_INICIO)
            fim = gr.Textbox(label=T.RELATORIO_FIM)
        with gr.Row():
            formatos = gr.CheckboxGroup(label=T.RELATORIO_FORMATOS, choices=[("PDF", "pdf"), ("DOCX", "docx"), ("Markdown", "md"), ("CSV", "csv")], value=["pdf", "docx"])
            com_ia = gr.Checkbox(label=T.RELATORIO_COM_IA, value=True)
        btn = gr.Button(T.BTN_GERAR, variant="primary")
        msg = gr.HTML("")
        arquivos = gr.File(label=T.BTN_BAIXAR, file_count="multiple", visible=False)
        pasta_md = gr.Markdown("")
        previa = gr.Markdown("")

        def gerar(t, i, f, fmts, ia):
            ctx = sessao.contexto
            if ctx is None:
                return C.aviso(T.NENHUM_REGISTRO_CARREGADO), gr.update(visible=False), "", ""
            try:
                i = dates.parse_data(i).isoformat() if (i or "").strip() else None
                f = dates.parse_data(f).isoformat() if (f or "").strip() else None
            except ValueError:
                return C.erro(T.AULA_DATA_INVALIDA), gr.update(visible=False), "", ""
            rel = builder.montar(sessao, t, i, f, com_ia=bool(ia))
            pasta = sessao.repo.caminhos.relatorios / ctx.codigo
            nome = f"{t}_{ctx.codigo}_{dates.carimbo_arquivo(sessao.fuso)}"
            saida = builder.exportar(rel, pasta, nome, list(fmts or ["pdf"]))
            caminhos = [p for lst in saida.values() for p in lst]
            previa_md = rel.como_markdown()
            # gráficos: mostra caminhos relativos na prévia
            return C.ok(T.RELATORIO_GERADO), gr.update(value=caminhos, visible=bool(caminhos)), T.RELATORIO_PASTA.format(pasta=str(pasta)), previa_md

        btn.click(C.protegido(gerar, T.ERRO_GRAVACAO), [tipo, inicio, fim, formatos, com_ia], [msg, arquivos, pasta_md, previa])

        gr.Markdown(f"## {T.MATERIAIS_TITULO}")
        with gr.Row():
            mat_tipo = gr.Dropdown(label=T.MATERIAL_TIPO, choices=[(v, k) for k, v in materials.TIPOS.items()], value="folha_professor")
            mat_fmt = gr.CheckboxGroup(label=T.MATERIAL_FORMATOS, choices=[("PDF", "pdf"), ("DOCX", "docx")], value=["pdf"])
            btn_mat = gr.Button(T.BTN_GERAR_MATERIAL)
        mat_msg = gr.HTML("")
        mat_arquivos = gr.File(label=T.BTN_BAIXAR, file_count="multiple", visible=False)

        def gerar_material(t, fmts):
            ctx = sessao.contexto
            if ctx is None:
                return C.aviso(T.NENHUM_REGISTRO_CARREGADO), gr.update(visible=False)
            reg = ctx.registro
            rubricas = sessao.repo.ler_rubricas()
            plano = sessao.ultimo_plano
            if t in ("folha_professor", "folha_aluno", "exercicios") and plano is None:
                return C.aviso(T.MATERIAL_PRECISA_PLANO), gr.update(visible=False)
            if t == "folha_professor":
                rel = materials.folha_professor(reg, plano, sessao.fuso, rubricas)
            elif t == "folha_aluno":
                rel = materials.folha_aluno(reg, plano, sessao.fuso)
            elif t == "exercicios":
                rel = materials.exercicios(reg, plano, sessao.fuso)
            elif t == "rubrica":
                ad = sessao.adaptador(reg.dominio)
                crit = grading.criterios_ativos(reg, ad.rubrica_padrao(reg.instrumento, reg.modalidade, reg.idade), rubricas)
                rel = materials.rubrica(reg, crit, sessao.fuso, rubricas)
            elif t == "ficha":
                rel = materials.ficha(reg, ctx.estado, sessao.fuso, sessao.adaptador(reg.dominio).nome_especialidade(reg.instrumento))
            else:
                rel = materials.lista_repertorio(reg, ctx.repertorio, sessao.fuso)
            saida = materials.salvar(rel, sessao.repo.caminhos.materiais(reg.codigo), f"{t}_{dates.carimbo_arquivo(sessao.fuso)}", list(fmts or ["pdf"]))
            return C.ok(T.MATERIAL_GERADO.format(codigo=reg.codigo)), gr.update(value=list(saida.values()), visible=True)

        btn_mat.click(C.protegido(gerar_material, T.ERRO_GRAVACAO), [mat_tipo, mat_fmt], [mat_msg, mat_arquivos])

        gr.Markdown(f"### {T.EXEMPLO_TITULO}")
        with gr.Row():
            ex_tipo = gr.Dropdown(label=T.EXEMPLO_TIPO, choices=[("Escala", "escala"), ("Arpejo", "arpejo"), ("Padrão rítmico", "padrao_ritmico")], value="escala")
            ex_tonica = gr.Textbox(label=T.EXEMPLO_TONICA, value="C")
            ex_escala = gr.Dropdown(label=T.EXEMPLO_ESCALA, choices=["maior", "menor_natural", "menor_harmonica", "menor_melodica", "pentatonica_maior", "pentatonica_menor", "cromatica"], value="maior")
            ex_qual = gr.Dropdown(label=T.EXEMPLO_QUALIDADE, choices=["maior", "menor"], value="maior")
            ex_oitava = gr.Number(label=T.EXEMPLO_OITAVA, value=4, precision=0, minimum=1, maximum=7)
        with gr.Row():
            ex_compasso = gr.Textbox(label=T.EXEMPLO_COMPASSO, value="4/4")
            ex_figuras = gr.Textbox(label=T.EXEMPLO_FIGURAS, value="1, 1, 0.5, 0.5, 1")
            btn_ex = gr.Button(T.BTN_GERAR_EXEMPLO)
        ex_msg = gr.HTML("")
        ex_arquivos = gr.File(label=T.BTN_BAIXAR, file_count="multiple", visible=False)

        def gerar_exemplo(t, ton, esc, qual, oit, comp, figs):
            ctx = sessao.contexto
            pasta = sessao.repo.caminhos.materiais(ctx.codigo) if ctx else sessao.repo.caminhos.exportacoes
            params = {"tonica": (ton or "C").strip().replace("b", "-") if len((ton or "").strip()) > 1 else (ton or "C").strip(), "tipo_escala": esc, "qualidade": qual, "oitava": int(oit or 4), "compasso": comp or "4/4", "figuras": [float(x) for x in (figs or "1").replace(";", ",").split(",") if x.strip()]}
            r = materials.exemplo_musical(sessao.adaptador(), pasta, t, params)
            return C.ok(T.EXEMPLO_GERADO.format(descricao=r["descricao"])), gr.update(value=list(r["arquivos"].values()), visible=True)

        btn_ex.click(C.protegido(gerar_exemplo), [ex_tipo, ex_tonica, ex_escala, ex_qual, ex_oitava, ex_compasso, ex_figuras], [ex_msg, ex_arquivos])

        def ao_selecionar():
            sessao.recarregar()
            return C.cabecalho_registro(sessao), gr.update(value=sessao.modo_ia == "gemini" and sessao.gemini_pronto)

        tab.select(ao_selecionar, None, [cabecalho, com_ia])

    return {"tab": tab}
