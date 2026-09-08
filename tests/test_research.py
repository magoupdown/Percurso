"""Pesquisa acadêmica (caso 16): provedores, fallback quando um cai, deduplicação, cache, rastreabilidade, expansão."""
from __future__ import annotations

import json

from percurso.core.models import Fonte
from percurso.research import academic, cache, expand, integracao, trace
from percurso.research.providers import provedores_padrao
from percurso.research.providers.websearch import WebSearchProvider

from conftest import registro_piano
from mocks.providers import HTTPFalso


def _provs(http):
    return provedores_padrao(mailto="teste@exemplo.org", chave_semantic_scholar=None, http=http)


def test_expansao_pt_en():
    cons = expand.expandir("articulação", "flauta_doce", "iniciante")
    assert len(cons) >= 4
    assert any("articulation" in c.lower() or "tonguing" in c.lower() for c in cons)
    assert any("flauta doce" in c.lower() for c in cons)


def test_provedores_e_deduplicacao(repo):
    http = HTTPFalso()
    r = academic.pesquisar_consultas(repo.caminhos, ["recorder articulation"], _provs(http), limite=8)
    titulos = [f.titulo.lower() for f in r.fontes]
    assert "recorder articulation pedagogy for beginners" in titulos
    assert titulos.count("recorder articulation pedagogy for beginners") == 1  # DOI repetido em OpenAlex e Crossref
    assert titulos.count("steady beat and pulse perception in children") == 1  # repetido em OpenAlex e Semantic Scholar
    assert any("swanwick" in (f.autor or "").lower() for f in r.fontes)
    f = next(x for x in r.fontes if "recorder" in x.titulo.lower())
    assert f.doi == "10.1000/rec.2018.1" and f.id_origem == "doi:10.1000/rec.2018.1" and f.tipo == "academica" and f.data_consulta
    assert not r.avisos
    assert any("mailto" in p and p["mailto"] == "teste@exemplo.org" for _, p in http.chamadas)


def test_provedor_fora_do_ar_nao_derruba_pesquisa(repo):
    http = HTTPFalso(fora_do_ar={"openalex"})
    r = academic.pesquisar_consultas(repo.caminhos, ["pulse perception"], _provs(http), limite=8)
    assert r.fontes and any("OpenAlex temporariamente indisponível" in a for a in r.avisos)
    assert any("swanwick" in (f.autor or "").lower() for f in r.fontes)


def test_cache_por_hash_e_validade(repo):
    http = HTTPFalso()
    provs = _provs(http)
    academic.pesquisar_consultas(repo.caminhos, ["Pulse Perception"], provs, limite=8)
    n1 = len(http.chamadas)
    r2 = academic.pesquisar_consultas(repo.caminhos, ["pulse  perception"], provs, limite=8)  # normalizada → mesma chave
    assert len(http.chamadas) == n1 and r2.do_cache == ["pulse  perception"]
    arquivos = list(repo.caminhos.pesquisas_cache.glob("*.json"))
    assert len(arquivos) == 1
    dados = json.loads(arquivos[0].read_text(encoding="utf-8"))
    assert dados["provedores"] and dados["resultados"] and dados["data"]
    # cache antigo: ainda existe e serve de fallback quando a rede cai
    dados["data"] = "2020-01-01T00:00:00-03:00"
    arquivos[0].write_text(json.dumps(dados), encoding="utf-8")
    assert not cache.valido(dados)
    http2 = HTTPFalso(fora_do_ar={"openalex", "crossref", "googlebooks", "semanticscholar"})
    r3 = academic.pesquisar_consultas(repo.caminhos, ["pulse perception"], _provs(http2), limite=8)
    assert r3.fontes and r3.do_cache


def test_websearch_desativado():
    assert not WebSearchProvider().disponivel() and WebSearchProvider().buscar("x") == []


def test_rastreabilidade_rejeita_fonte_fora_do_conjunto():
    f = Fonte(titulo="Inventada", tipo="academica", id_origem="doi:10.9/xyz")
    ok, rejeitadas = trace.filtrar_verificadas([f], ["doi:10.1000/rec.2018.1"])
    assert not ok and rejeitadas == [f]
    assert "🎓" in trace.formatar(Fonte(titulo="T", tipo="academica"))
    assert "🏛" in trace.formatar(Fonte(titulo="T", tipo="curricular"))


def test_onde_pesquisar_integrado_ao_plano(sessao, monkeypatch):
    from percurso.core import planner
    from percurso.library import ingest
    from pathlib import Path

    reg = registro_piano(sessao.repo)
    sessao.carregar(reg.codigo)
    ingest.adicionar(sessao.repo.caminhos, Path(__file__).parent / "fixtures" / "pedagogia_pulsacao.pdf")
    monkeypatch.setattr(academic, "provedores_da_sessao", lambda s: _provs(HTTPFalso()))
    extra = integracao.pesquisar_para_plano(sessao, "pulsação", ["biblioteca", "curricular", "academica"])
    tipos = {f.tipo for f in extra["referencias"]}
    assert {"biblioteca", "curricular", "academica"} <= tipos
    assert extra["habilidades"] and all(h.startswith("EF15AR") for h in extra["habilidades"])
    assert extra["consultas"]
    entrada = sessao.entrada_planejamento(conteudo="pulsação", referencias=extra["referencias"], consultas_realizadas=extra["consultas"], habilidades_validadas=extra["habilidades"])
    plano = planner.gerar_plano(entrada)
    assert plano.referencias and plano.habilidades_curriculares == extra["habilidades"] and plano.consultas_realizadas
    md = planner.plano_como_markdown(plano)
    assert "📚" in md and "🏛" in md and "🎓" in md


def test_user_agent_ascii():
    from percurso.research.providers.base import ClienteHTTP

    ua = ClienteHTTP().user_agent
    assert ua and ua.isascii()
    assert ClienteHTTP(user_agent="Percurso pedagógica").user_agent.isascii()


import pytest


@pytest.mark.online
def test_provedores_reais_openalex_crossref():
    """Integração real (opcional): `pytest -m online`. Falha de rede não é erro do Percurso."""
    from percurso.research.providers import CrossrefProvider, OpenAlexProvider

    fontes = OpenAlexProvider(mailto="").buscar("recorder articulation pedagogy", limite=3)
    assert fontes and all(f.titulo and f.tipo == "academica" for f in fontes)
    fontes2 = CrossrefProvider(mailto="").buscar("music education pulse", limite=3)
    assert fontes2 and all(f.id_origem for f in fontes2)
