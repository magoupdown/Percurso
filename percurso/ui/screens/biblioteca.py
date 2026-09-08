"""Minha biblioteca (SPEC §9.4): adicionar, pesquisar, ver, corrigir metadados, remover, índices."""
from __future__ import annotations

from pathlib import Path
from typing import List

import gradio as gr

from ...library import catalog, embeddings, index, ingest, search
from .. import common as C
from .. import texts as T
from ..session import Sessao


def _tabela(sessao: Sessao) -> str:
    cat = catalog.ler(sessao.repo.caminhos)
    if not cat.documentos:
        return T.BIBLIOTECA_VAZIA
    L = ["| Título | Autor | Ano | Categoria | Instrumento | Páginas | Trechos | Situação |", "|---|---|---|---|---|---|---|---|"]
    for d in sorted(cat.documentos, key=lambda x: x.data_inclusao, reverse=True):
        sit = "sem texto (imagem)" if d.sem_texto else "indexado"
        L.append(f"| {d.titulo or d.nome_original} | {d.autor} | {d.ano} | {d.categoria} | {d.instrumento} | {d.paginas or ''} | {d.n_trechos} | {sit} |")
    return "\n".join(L)


def _opcoes(sessao: Sessao) -> list:
    cat = catalog.ler(sessao.repo.caminhos)
    return [(catalog.descrever(d), d.hash) for d in sorted(cat.documentos, key=lambda x: x.data_inclusao, reverse=True)]


def _status_indice(sessao: Sessao) -> str:
    cam = sessao.repo.caminhos
    idx = index.ler(cam)
    man = idx["manifesto"]
    partes = [f"Índice BM25: {man.get('n_trechos', 0)} trechos · atualizado em {man.get('data_indexacao') or '—'}"]
    g = embeddings.ler(cam, "gemini")["manifesto"]
    if g.get("n_trechos"):
        partes.append(f"Índice semântico Gemini: {g['n_trechos']} trechos ({g.get('modelo')})")
    l = embeddings.ler(cam, "local")["manifesto"]
    if l.get("n_trechos"):
        partes.append(f"Índice semântico local: {l['n_trechos']} trechos")
    if index.precisa_atualizar_versao(cam):
        partes.append(f"⚠ {T.INDICE_DESATUALIZADO}")
    return " · ".join(partes)


def _semantica(sessao: Sessao):
    """Função de busca semântica disponível nesta sessão, ou None."""
    cam = sessao.repo.caminhos
    if sessao.modo_ia == "gemini" and sessao.gemini_pronto and sessao.cliente_gemini is not None and embeddings.ler(cam, "gemini")["itens"]:
        emb = embeddings.embutir_gemini(sessao.cliente_gemini)
        return lambda q, n: embeddings.buscar(cam, "gemini", emb, q, n)
    if getattr(sessao, "semantica_local", False) and embeddings.ler(cam, "local")["itens"]:
        emb = embeddings.embutir_local()
        if emb is not None:
            return lambda q, n: embeddings.buscar(cam, "local", lambda ts: emb(ts), q, n)
    return None


def montar(sessao: Sessao) -> dict:
    cam = sessao.repo.caminhos
    with gr.Tab(T.ABA_BIBLIOTECA, id="biblioteca") as tab:
        gr.Markdown(f"## {T.BIBLIOTECA_TITULO}")
        status = gr.Markdown(_status_indice(sessao))
        with gr.Tabs():
            with gr.Tab(T.BTN_ADICIONAR_MATERIAL):
                arquivos = gr.File(label=T.BIBLIOTECA_UPLOAD, file_count="multiple", file_types=[".pdf", ".docx", ".txt", ".md"], type="filepath")
                btn_add = gr.Button(T.BTN_ADICIONAR_MATERIAL, variant="primary")
                add_msg = gr.Markdown("")

                def adicionar(lista):
                    if not lista:
                        return C.aviso(T.BIBLIOTECA_UPLOAD), _status_indice(sessao)
                    linhas: List[str] = []
                    for caminho in lista:
                        p = Path(caminho)
                        try:
                            r = ingest.adicionar(cam, p, nome_original=p.name, fuso=sessao.fuso)
                            icone = "✓" if r.ok else "✗"
                            linhas.append(f"- {icone} **{p.name}** — {r.mensagem}")
                        except Exception as e:  # noqa: BLE001 — um arquivo ruim não derruba os demais
                            C.log.error("ingestão falhou %s: %s", p.name, e)
                            linhas.append(f"- ✗ **{p.name}** — {ingest.MSG_CORROMPIDO}")
                    return "\n".join(linhas), _status_indice(sessao)

                btn_add.click(C.protegido(adicionar, T.ERRO_GRAVACAO), [arquivos], [add_msg, status])

            with gr.Tab(T.BTN_PESQUISAR):
                consulta = gr.Textbox(label=T.BIBLIOTECA_BUSCA, placeholder=T.BIBLIOTECA_BUSCA_DICA)
                btn_buscar = gr.Button(T.BTN_BUSCAR, variant="primary")
                resultados = gr.Markdown("")

                def buscar(q):
                    q = (q or "").strip()
                    if not q:
                        return T.BIBLIOTECA_BUSCA_DICA
                    sin = sessao.adaptador().sinonimos_pedagogicos()
                    res = search.buscar(cam, q, sin, limite=10, semantica=_semantica(sessao))
                    termos = search.expandir(q, sin)
                    cab = f"_Termos usados: {', '.join(termos[:20])}_\n\n"
                    return cab + search.formatar(res)

                btn_buscar.click(C.protegido(buscar), [consulta], [resultados])
                consulta.submit(C.protegido(buscar), [consulta], [resultados])

            with gr.Tab(T.BTN_VER_BIBLIOTECA):
                tabela = gr.Markdown(_tabela(sessao))
                with gr.Accordion(T.BIBLIOTECA_METADADOS, open=False):
                    sel = gr.Dropdown(label=T.BIBLIOTECA_SELECIONE, choices=_opcoes(sessao), value=None)
                    with gr.Row():
                        m_titulo = gr.Textbox(label=T.BIBLIOTECA_TITULO_DOC)
                        m_autor = gr.Textbox(label=T.BIBLIOTECA_AUTOR)
                        m_ano = gr.Textbox(label=T.BIBLIOTECA_ANO)
                    with gr.Row():
                        m_cat = gr.Dropdown(label=T.BIBLIOTECA_CATEGORIA, choices=catalog.CATEGORIAS, value="outros")
                        m_inst = gr.Dropdown(label=T.BIBLIOTECA_INSTRUMENTO, choices=[("—", "")] + C.opcoes_instrumentos(sessao), value="")
                        m_nivel = gr.Dropdown(label=T.BIBLIOTECA_NIVEL, choices=[("—", "")] + T.opcoes(T.NIVEIS), value="")
                        m_tipo = gr.Dropdown(label=T.BIBLIOTECA_TIPO, choices=catalog.TIPOS_DOCUMENTO, value="outro")
                    m_obs = gr.Textbox(label=T.BIBLIOTECA_OBS)
                    btn_meta = gr.Button(T.BTN_SALVAR_METADADOS, variant="primary")
                    meta_msg = gr.HTML("")

                    def carregar_meta(sha):
                        d = catalog.ler(cam).por_hash(sha or "")
                        if d is None:
                            return "", "", "", "outros", "", "", "outro", ""
                        return d.titulo, d.autor, d.ano, d.categoria, d.instrumento, d.nivel, d.tipo_documento, d.observacoes

                    sel.change(carregar_meta, [sel], [m_titulo, m_autor, m_ano, m_cat, m_inst, m_nivel, m_tipo, m_obs])

                    def salvar_meta(sha, ti, au, an, ca, ins, ni, tp, ob):
                        if not sha:
                            return C.aviso(T.BIBLIOTECA_SELECIONE), _tabela(sessao), gr.update()
                        ingest.atualizar_metadados(cam, sha, titulo=ti, autor=au, ano=an, categoria=ca, instrumento=ins, nivel=ni, tipo_documento=tp, observacoes=ob)
                        return C.ok(T.METADADOS_SALVOS), _tabela(sessao), gr.update(choices=_opcoes(sessao))

                    btn_meta.click(C.protegido(salvar_meta, T.ERRO_GRAVACAO), [sel, m_titulo, m_autor, m_ano, m_cat, m_inst, m_nivel, m_tipo, m_obs], [meta_msg, tabela, sel])

            with gr.Tab(T.BTN_REMOVER_MATERIAL):
                sel_rm = gr.Dropdown(label=T.BIBLIOTECA_SELECIONE, choices=_opcoes(sessao), value=None)
                btn_rm = gr.Button(T.BTN_REMOVER_MATERIAL, variant="stop")
                lista_rm = gr.Markdown("")
                with gr.Row(visible=False) as linha_conf:
                    btn_conf = gr.Button(T.BTN_CONFIRMAR, variant="stop")
                    btn_canc = gr.Button(T.BTN_CANCELAR)
                rm_msg = gr.HTML("")

                def pedir_rm(sha):
                    itens = ingest.descrever_remocao(cam, sha or "")
                    if not itens:
                        return C.aviso(T.BIBLIOTECA_SELECIONE), "", gr.update(visible=False)
                    return C.aviso(T.REMOCAO_CONFIRMAR), "\n".join(f"- {i}" for i in itens), gr.update(visible=True)

                def confirmar_rm(sha):
                    apagados = ingest.remover(cam, sha or "")
                    return C.ok(T.DOCUMENTO_REMOVIDO + " " + "; ".join(apagados)), "", gr.update(visible=False), gr.update(choices=_opcoes(sessao), value=None), _status_indice(sessao)

                btn_rm.click(C.protegido(pedir_rm), [sel_rm], [rm_msg, lista_rm, linha_conf])
                btn_conf.click(C.protegido(confirmar_rm, T.ERRO_GRAVACAO), [sel_rm], [rm_msg, lista_rm, linha_conf, sel_rm, status])
                btn_canc.click(lambda: ("", "", gr.update(visible=False)), None, [rm_msg, lista_rm, linha_conf])

            with gr.Tab("Índices"):
                gr.Markdown("A busca por palavras (BM25) funciona sempre. A busca semântica é opcional.")
                btn_idx = gr.Button(T.BTN_ATUALIZAR_INDICE)
                btn_gemini_idx = gr.Button(T.BTN_INDEXAR_GEMINI)
                btn_local = gr.Button(T.BTN_INSTALAR_LOCAL)
                idx_msg = gr.HTML("")

                def atualizar_idx():
                    if index.precisa_atualizar_versao(cam):
                        cam.indice_bm25.unlink(missing_ok=True)
                    index.atualizar(cam, fuso=sessao.fuso)
                    return C.ok(T.INDICE_ATUALIZADO), _status_indice(sessao)

                def indexar_gemini():
                    if not (sessao.modo_ia == "gemini" and sessao.gemini_pronto and sessao.cliente_gemini is not None):
                        return C.aviso(T.SOMENTE_MODO_INTELIGENTE), _status_indice(sessao)
                    if not sessao.consentimento_trechos:
                        return C.aviso(T.CONSENTIMENTO_TRECHOS + " Responda SIM na tela inicial para indexar."), _status_indice(sessao)
                    try:
                        embeddings.atualizar(cam, "gemini", embeddings.embutir_gemini(sessao.cliente_gemini), sessao.cliente_gemini.modelo_embeddings if hasattr(sessao.cliente_gemini, "modelo_embeddings") else "gemini", sessao.fuso)
                    except Exception as e:  # noqa: BLE001
                        C.log.warning("embeddings Gemini falharam: %s", e)
                        return C.erro(T.GEMINI_SEM_RESPOSTA), _status_indice(sessao)
                    return C.ok(T.BUSCA_SEMANTICA_ATIVA.format(metodo="Gemini")), _status_indice(sessao)

                def instalar_local():
                    if not embeddings.instalar_local():
                        return C.aviso(T.SEMANTICA_LOCAL_FALHOU), _status_indice(sessao)
                    emb = embeddings.embutir_local()
                    if emb is None:
                        return C.aviso(T.SEMANTICA_LOCAL_FALHOU), _status_indice(sessao)
                    embeddings.atualizar(cam, "local", emb, embeddings.MODELO_LOCAL, sessao.fuso)
                    sessao.semantica_local = True  # type: ignore[attr-defined]
                    return C.ok(T.SEMANTICA_LOCAL_OK), _status_indice(sessao)

                btn_idx.click(C.protegido(atualizar_idx), None, [idx_msg, status])
                btn_gemini_idx.click(C.protegido(indexar_gemini), None, [idx_msg, status])
                btn_local.click(C.protegido(instalar_local), None, [idx_msg, status])

        def ao_selecionar():
            return _status_indice(sessao), _tabela(sessao), gr.update(choices=_opcoes(sessao)), gr.update(choices=_opcoes(sessao))

        tab.select(ao_selecionar, None, [status, tabela, sel, sel_rm])

    return {"tab": tab}
