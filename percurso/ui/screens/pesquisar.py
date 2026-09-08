"""Pesquisar (SPEC §11.1): 📚 biblioteca · 🏛 base curricular · 🎓 acadêmica, com rastreabilidade; e consulta à base curricular."""
from __future__ import annotations

import gradio as gr

from ...curriculum import bncc, consulta as cur, validate
from ...library import search
from ...research import academic, trace
from .. import common as C
from .. import texts as T
from ..session import Sessao


def montar(sessao: Sessao) -> dict:
    with gr.Tab(T.ABA_PESQUISAR, id="pesquisar") as tab:
        gr.Markdown(f"## {T.PESQUISAR_TITULO}")
        with gr.Row():
            tema = gr.Textbox(label=T.PESQUISAR_TEMA, scale=3)
            instrumento = gr.Dropdown(label=T.PESQUISAR_INSTRUMENTO, choices=C.opcoes_instrumentos(sessao), value=_instrumento_padrao(sessao))
            nivel = gr.Dropdown(label=T.PESQUISAR_NIVEL, choices=T.opcoes(T.NIVEIS), value=_nivel_padrao(sessao))
        onde = gr.CheckboxGroup(label=T.PESQUISAR_ONDE, choices=[("Minha Biblioteca", "biblioteca"), ("Base Curricular", "curricular"), ("Pesquisa Acadêmica", "academica")], value=["biblioteca", "curricular", "academica"])
        gr.Markdown(f"_{T.PESQUISAR_EXTERNA_DESATIVADA}_")
        btn = gr.Button(T.BTN_PESQUISAR, variant="primary")
        avisos = gr.HTML("")
        consultas_md = gr.Markdown("")
        res_bib = gr.Markdown("")
        res_cur = gr.Markdown("")
        res_acad = gr.Markdown("")

        def pesquisar(t, inst, niv, onde_v):
            t = (t or "").strip()
            if not t:
                return C.aviso(T.PESQUISAR_SEM_TEMA), "", "", "", ""
            adaptador = sessao.adaptador()
            consultas = adaptador.expandir_consulta(t, inst or "outro", niv or "iniciante")
            partes_bib = partes_cur = partes_acad = ""
            avisos_txt = []
            if "biblioteca" in onde_v:
                res = search.buscar(sessao.repo.caminhos, t, adaptador.sinonimos_pedagogicos(), limite=8)
                partes_bib = f"### {T.PESQUISAR_RESULTADOS_BIB}\n\n" + search.formatar(res)
            if "curricular" in onde_v:
                reg = sessao.contexto.registro if sessao.contexto else None
                hab = cur.sugerir_para_tema(t, reg, limite=5)
                partes_cur = f"### {T.PESQUISAR_RESULTADOS_CUR}\n\n" + ("\n\n".join(cur.descrever(h) for h in hab) if hab else T.PESQUISAR_SEM_RESULTADO)
            if "academica" in onde_v:
                r = academic.pesquisar_consultas(sessao.repo.caminhos, consultas, academic.provedores_da_sessao(sessao), limite=8, fuso=sessao.fuso)
                avisos_txt.extend(r.avisos)
                if r.do_cache:
                    avisos_txt.append("Resultados do cache para: " + "; ".join(r.do_cache))
                partes_acad = f"### {T.PESQUISAR_RESULTADOS_ACAD}\n\n" + trace.formatar_lista(r.fontes)
            aviso_html = C.aviso("<br>".join(avisos_txt)) if avisos_txt else ""
            return aviso_html, f"**{T.PESQUISAR_CONSULTAS}:** " + " · ".join(consultas), partes_bib, partes_cur, partes_acad

        btn.click(C.protegido(pesquisar), [tema, instrumento, nivel, onde], [avisos, consultas_md, res_bib, res_cur, res_acad])
        tema.submit(C.protegido(pesquisar), [tema, instrumento, nivel, onde], [avisos, consultas_md, res_bib, res_cur, res_acad])

        gr.Markdown(f"## {T.CURRICULO_TITULO}")
        with gr.Row():
            etapa = gr.Dropdown(label=T.CURRICULO_ETAPA, choices=[("Educação Infantil", "EI"), ("Ensino Fundamental", "EF"), ("Ensino Médio", "EM"), ("Todas", "")], value="EF")
            so_musica = gr.Checkbox(label=T.CURRICULO_APENAS_MUSICA, value=True)
            btn_listar = gr.Button(T.BTN_LISTAR_HABILIDADES)
        lista = gr.Markdown("")
        with gr.Row():
            codigos = gr.Textbox(label=T.CURRICULO_VALIDAR, placeholder="EF15AR14, EF69AR20")
            btn_validar = gr.Button(T.BTN_VALIDAR_CODIGOS)
        validacao = gr.Markdown("")
        gr.Markdown(f"**{T.CURRICULO_VERSOES}:** " + " · ".join(f"{v['documento']} — {v['versao']} ({v['n']} habilidades, obtida em {v['data_obtencao']})" for v in bncc.versoes()))

        def listar(et, sm):
            reg = sessao.contexto.registro if sessao.contexto else None
            hab = cur.listar(reg, apenas_musica=bool(sm), etapa=et or None)
            return "\n\n".join(cur.descrever(h) for h in hab) if hab else T.PESQUISAR_SEM_RESULTADO

        def validar(txt):
            reg = sessao.contexto.registro if sessao.contexto else None
            cods = [c.strip() for c in (txt or "").replace(";", ",").split(",") if c.strip()]
            r = validate.validar_lista(cods, reg)
            L = [f"- ✓ {c}" for c in r.validos] + [f"- ✗ {c}: {m}" for c, m in r.removidos]
            return "\n".join(L) if L else T.CURRICULO_VALIDAR

        btn_listar.click(C.protegido(listar), [etapa, so_musica], [lista])
        btn_validar.click(C.protegido(validar), [codigos], [validacao])

        def ao_selecionar():
            return gr.update(value=_instrumento_padrao(sessao)), gr.update(value=_nivel_padrao(sessao))

        tab.select(ao_selecionar, None, [instrumento, nivel])

    return {"tab": tab}


def _instrumento_padrao(sessao: Sessao) -> str:
    return sessao.contexto.registro.instrumento if sessao.contexto else "piano"


def _nivel_padrao(sessao: Sessao) -> str:
    return sessao.contexto.registro.nivel if sessao.contexto else "iniciante"
