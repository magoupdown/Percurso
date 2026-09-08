"""Interface e sessão: Modo Essencial completo sem Gemini (caso 3), ativação Gemini com mock (casos 4–6)."""
from __future__ import annotations

import pytest

from percurso.core.models import Aula, ConteudoTrabalhado
from percurso.ui import common, texts as T
from percurso.ui.screens import historico
from percurso.ui.session import Sessao

from conftest import aula, registro_piano


def test_app_monta_sem_gemini(sessao: Sessao):
    from percurso import app as app_mod

    demo = app_mod.montar_app(sessao)
    assert demo is not None
    assert sessao.modo_ia == "essencial"
    assert T.MODO_ESSENCIAL in common.badge_modo(sessao)


def test_fluxo_completo_modo_essencial(sessao: Sessao):
    """criar → planejar → registrar → estado → painel de retorno → histórico, tudo sem IA."""
    from percurso.core import planner

    reg = registro_piano(sessao.repo)
    ctx = sessao.carregar(reg.codigo)
    assert T.SEM_AULAS in common.painel_retorno(ctx, sessao)
    plano = planner.gerar_plano(sessao.entrada_planejamento())
    plano = sessao.repo.gravar_plano(plano)
    sessao.ultimo_plano = plano
    form = planner.aula_a_partir_do_plano(plano, ctx.estado)
    a = Aula(id="", data=form["data"], classificacao_conteudos=[ConteudoTrabalhado(conteudo=c["conteudo"], situacao="consolidado") for c in form["classificacao"]], conteudo_realizado=[c["conteudo"] for c in form["classificacao"]], plano_origem=form["plano_origem"], rendimento={"leitura": 3}, observacoes="tendência a acelerar")
    numero = sessao.registrar_aula(a)
    assert numero == 1
    assert sessao.repo.listar_planos(reg.codigo)[0].status == "realizado"
    painel = common.painel_retorno(sessao.contexto, sessao)
    assert "Aula 1" in painel and "acelerar" in painel and "Próximo passo sugerido" in painel
    tabela = historico.tabela(sessao.contexto.aulas, sessao.contexto.numeros)
    assert "| 01 |" in tabela
    assert historico.filtrar(sessao.contexto.aulas, conteudo=plano.tema[:6])
    assert not historico.filtrar(sessao.contexto.aulas, conteudo="inexistente-xyz")
    md = historico.aula_como_markdown(sessao.contexto.aulas[0], 1)
    assert "Consolidado" in md


def test_pseudonimizacao(sessao: Sessao):
    reg = registro_piano(sessao.repo, identificacao="Joana")
    sessao.carregar(reg.codigo)
    import re

    txt = sessao.pseudonimizar("Joana tocou bem; joana acelera. Joanas não.")
    assert not re.search(r"(?<!\w)joana(?!\w)", txt, flags=re.I)
    assert reg.codigo in txt
    assert "Joanas" in txt  # palavra diferente preservada
    assert sessao.restaurar_nomes(txt).startswith("Joana tocou bem")


class _ClienteFalso:
    def __init__(self, chave):
        if chave == "invalida":
            raise RuntimeError("API key not valid. Please pass a valid API key. 400")
        if chave == "rede":
            raise RuntimeError("Connection reset")
        self.chave = chave

    def testar(self):
        return None


def test_gemini_sem_chave(sessao: Sessao):
    from percurso.ai import gemini

    r = gemini.ativar(sessao, fabrica_cliente=_ClienteFalso)
    assert not r.ok and r.motivo == "sem_chave" and sessao.modo_ia == "essencial"


def test_gemini_chave_valida_mock(sessao: Sessao):
    from percurso.ai import gemini

    r = gemini.ativar(sessao, chave_sessao="ok-teste", fabrica_cliente=_ClienteFalso)
    assert r.ok and sessao.modo_ia == "gemini" and sessao.gemini_pronto
    assert T.MODO_INTELIGENTE in common.badge_modo(sessao)
    # a chave fica só em memória
    for p in sessao.repo.base.rglob("*"):
        if p.is_file():
            assert b"ok-teste" not in p.read_bytes()


def test_gemini_chave_invalida_amigavel(sessao: Sessao):
    from percurso.ai import gemini

    r = gemini.ativar(sessao, chave_sessao="invalida", fabrica_cliente=_ClienteFalso)
    assert not r.ok and r.motivo == "chave_invalida" and r.mensagem == T.GEMINI_CHAVE_INVALIDA
    r = gemini.ativar(sessao, chave_sessao="rede", fabrica_cliente=_ClienteFalso)
    assert r.motivo == "rede" and r.mensagem == T.GEMINI_SEM_RESPOSTA
    assert sessao.modo_ia == "essencial"


def test_gemini_via_segredo_da_plataforma(sessao: Sessao, monkeypatch):
    from percurso.ai import gemini

    monkeypatch.setenv("GEMINI_API_KEY", "segredo-ok")
    r = gemini.ativar(sessao, fabrica_cliente=_ClienteFalso)
    assert r.ok
