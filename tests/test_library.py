"""Biblioteca (casos 7, 8, 17): upload, duplicado, PDF sem texto, corrompido, busca, índice incremental, remoção."""
from __future__ import annotations

import json
from pathlib import Path

from percurso.library import catalog, embeddings, extract, index, ingest, search
from percurso.domains import obter_adaptador

from mocks.gemini import ClienteFalso

FX = Path(__file__).parent / "fixtures"


def test_extracao_por_formato():
    e = extract.extrair(FX / "pedagogia_pulsacao.pdf")
    assert e.n_paginas == 3 and "pulsação" in e.texto.lower()
    assert e.metadados["titulo"] == "Pedagogia da pulsação no piano" and e.metadados["autor"] == "Maria Silva"
    d = extract.extrair(FX / "orff_flauta.docx")
    assert "Sol, Lá e Si" in d.texto and "sonoridade" in d.texto  # tabela incluída
    m = extract.extrair(FX / "notas_percepcao.md")
    assert m.metadados["titulo"] == "Notas sobre percepção musical"


def test_trechos_com_pagina_e_sobreposicao():
    texto = " ".join(f"palavra{i}." for i in range(1500))
    ex = extract.Extracao(paginas=[extract.Pagina(1, texto), extract.Pagina(2, "curto")], n_paginas=2)
    tr = extract.dividir_em_trechos(ex)
    assert len(tr) >= 3 and tr[0]["pagina"] == 1 and tr[-1]["pagina"] == 2
    assert all(len(t["texto"]) <= extract.TOKENS_TRECHO * extract.CHARS_POR_TOKEN + 5 for t in tr)
    # sobreposição: o fim de um trecho reaparece no início do seguinte
    assert tr[0]["texto"][-30:].split()[-1] in tr[1]["texto"]


def test_upload_pdf_extrai_indexa_cataloga_persiste(repo):
    cam = repo.caminhos
    r = ingest.adicionar(cam, FX / "pedagogia_pulsacao.pdf")
    assert r.ok and r.documento is not None and r.documento.n_trechos >= 1 and r.documento.paginas == 3
    assert r.documento.categoria == "pedagogia musical" and r.documento.instrumento == "piano" and r.documento.ano == "2019"
    sha = r.documento.hash
    assert cam.arquivo_biblioteca(sha, "pdf").exists() and cam.texto_biblioteca(sha).exists()
    cat = catalog.ler(cam)
    assert cat.por_hash(sha) is not None
    idx = index.ler(cam)
    assert idx["manifesto"]["n_trechos"] == r.documento.n_trechos and sha in idx["manifesto"]["hash_por_documento"]
    # nova "sessão": tudo é lido do disco
    from percurso.storage.repo import Repositorio

    repo2 = Repositorio(repo.base)
    assert catalog.ler(repo2.caminhos).por_hash(sha).titulo == "Pedagogia da pulsação no piano"


def test_upload_duplicado_nao_duplica(repo):
    cam = repo.caminhos
    r1 = ingest.adicionar(cam, FX / "notas_percepcao.md")
    r2 = ingest.adicionar(cam, FX / "notas_percepcao.md")
    assert r1.ok and not r2.ok and r2.duplicado and r2.mensagem == ingest.MSG_DUPLICADO
    assert len(catalog.ler(cam).documentos) == 1
    assert index.ler(cam)["manifesto"]["n_trechos"] == r1.documento.n_trechos


def test_pdf_digitalizado_entra_marcado_sem_texto(repo):
    r = ingest.adicionar(repo.caminhos, FX / "digitalizado.pdf")
    assert r.ok and r.sem_texto and r.mensagem == ingest.MSG_SEM_TEXTO
    d = catalog.ler(repo.caminhos).documentos[0]
    assert d.sem_texto and d.n_trechos == 0
    assert index.ler(repo.caminhos)["manifesto"]["n_trechos"] == 0


def test_arquivo_corrompido_nao_quebra_os_demais(repo):
    cam = repo.caminhos
    ok = ingest.adicionar(cam, FX / "orff_flauta.docx")
    ruim = ingest.adicionar(cam, FX / "corrompido.pdf")
    assert ok.ok and not ruim.ok and ruim.mensagem == ingest.MSG_CORROMPIDO
    assert not any(p.suffix == ".pdf" for p in cam.biblioteca_arquivos.iterdir())
    sin = obter_adaptador("musica").sinonimos_pedagogicos()
    assert search.buscar(cam, "articulação flauta doce", sin)


def test_formato_invalido(repo, tmp_path):
    p = tmp_path / "x.xlsx"
    p.write_bytes(b"abc")
    assert ingest.adicionar(repo.caminhos, p).mensagem == ingest.MSG_FORMATO


def test_busca_exata_bm25_e_expansao(repo):
    cam = repo.caminhos
    ingest.adicionar(cam, FX / "pedagogia_pulsacao.pdf")
    ingest.adicionar(cam, FX / "orff_flauta.docx")
    ingest.adicionar(cam, FX / "notas_percepcao.md")
    sin = obter_adaptador("musica").sinonimos_pedagogicos()
    termos = search.expandir("desenvolvimento da pulsação", sin)
    assert "beat" in termos and "pulso" in termos
    ex = search.buscar_exata(cam, "Tecla Repetida No Pulso")
    assert ex and ex[0].pagina == 1 and ex[0].metodo == "exata"
    bm = search.buscar_bm25(cam, "desenvolvimento da pulsação", sin)
    assert bm and bm[0].titulo == "Pedagogia da pulsação no piano"
    res = search.buscar(cam, "ear training", sin)
    assert any("percepção" in r.titulo.lower() for r in res)
    f = res[0].como_fonte()
    assert f.tipo == "biblioteca" and f.id_origem and f.data_consulta
    assert "📚" in search.formatar(res)


def test_indice_incremental_so_reprocessa_novos(repo, monkeypatch):
    cam = repo.caminhos
    ingest.adicionar(cam, FX / "notas_percepcao.md")
    man1 = index.ler(cam)["manifesto"]
    chamadas = []
    original = catalog.ler_trechos

    def espiao(c, sha):
        chamadas.append(sha)
        return original(c, sha)

    monkeypatch.setattr(index.catalog, "ler_trechos", espiao)
    index.atualizar(cam)  # nada novo → nenhum documento relido
    assert chamadas == []
    r = ingest.adicionar(cam, FX / "orff_flauta.docx")
    assert chamadas == [r.documento.hash]  # só o novo
    man2 = index.ler(cam)["manifesto"]
    assert man2["n_trechos"] > man1["n_trechos"] and len(man2["hash_por_documento"]) == 2


def test_remocao_apaga_arquivo_texto_e_indice(repo):
    cam = repo.caminhos
    r = ingest.adicionar(cam, FX / "orff_flauta.docx")
    sha = r.documento.hash
    itens = ingest.descrever_remocao(cam, sha)
    assert any("arquivos" in i for i in itens) and any("texto" in i for i in itens)
    apagados = ingest.remover(cam, sha)
    assert len(apagados) >= 3
    assert not cam.arquivo_biblioteca(sha, "docx").exists() and not cam.texto_biblioteca(sha).exists()
    assert catalog.ler(cam).por_hash(sha) is None and index.ler(cam)["manifesto"]["n_trechos"] == 0


def test_metadados_corrigidos_pelo_professor(repo):
    cam = repo.caminhos
    r = ingest.adicionar(cam, FX / "notas_percepcao.md")
    ingest.atualizar_metadados(cam, r.documento.hash, autor="Eu", categoria="percepção", nivel="iniciante")
    d = catalog.ler(cam).por_hash(r.documento.hash)
    assert d.autor == "Eu" and d.categoria == "percepção" and d.nivel == "iniciante"


def test_embeddings_gemini_incremental_e_busca(repo):
    cam = repo.caminhos
    ingest.adicionar(cam, FX / "pedagogia_pulsacao.pdf")
    cli = ClienteFalso()
    emb = embeddings.embutir_gemini(cli)
    idx = embeddings.atualizar(cam, "gemini", emb, "mock-emb")
    n = idx["manifesto"]["n_trechos"]
    assert n >= 1 and cam.indice_emb_gemini.exists()
    idx2 = embeddings.atualizar(cam, "gemini", emb, "mock-emb")
    assert idx2["manifesto"]["n_trechos"] == n  # incremental: nada novo
    res = embeddings.buscar(cam, "gemini", emb, "pulsação corporal", 3)
    assert res and res[0].metodo == "semantica"
    sin = obter_adaptador("musica").sinonimos_pedagogicos()
    comb = search.buscar(cam, "pulsação", sin, semantica=lambda q, n: embeddings.buscar(cam, "gemini", emb, q, n))
    assert comb
    ingest.remover(cam, catalog.ler(cam).documentos[0].hash)
    assert embeddings.ler(cam, "gemini")["manifesto"]["n_trechos"] == 0


def test_versao_do_indice_detectada(repo):
    cam = repo.caminhos
    ingest.adicionar(cam, FX / "notas_percepcao.md")
    dados = json.loads(cam.indice_bm25.read_text(encoding="utf-8"))
    dados["manifesto"]["versao_indice"] = 0
    cam.indice_bm25.write_text(json.dumps(dados), encoding="utf-8")
    assert index.precisa_atualizar_versao(cam)
    cam.indice_bm25.unlink()
    idx = index.atualizar(cam)
    assert idx["manifesto"]["versao_indice"] == index.VERSAO_INDICE and idx["manifesto"]["n_trechos"] >= 1
