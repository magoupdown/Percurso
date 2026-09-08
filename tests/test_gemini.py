"""Modo Inteligente com mock (casos 4, 19, 21): pseudonimização, ciclo de validação, fallback."""
from __future__ import annotations

import re

from percurso.ai import classificacao, historico as ai_hist, planning, resumo as ai_resumo
from percurso.ai.anonymize import Pseudonimizador
from percurso.core import state
from percurso.core.models import AlunoTurma, Fonte, Registro, Turma
from percurso.ui import texts as T

from conftest import aula, registro_piano
from mocks.gemini import ClienteFalso, plano_valido


def _ligar(sessao, roteiro):
    sessao.cliente_gemini = ClienteFalso(roteiro)
    sessao.modo_ia = "gemini"
    sessao.gemini_pronto = True
    return sessao.cliente_gemini


def _preparar(sessao, nome="Joana"):
    reg = registro_piano(sessao.repo, identificacao=nome)
    sessao.repo.gravar_aula(reg.codigo, aula("2026-08-01", [("Corpo: pulso com palmas, passos e balanço", "consolidado")], dificuldades=["acelera no final das frases"], obs=f"{nome} acelera no final das frases", rendimento={"ritmo": 3}))
    sessao.repo.gravar_aula(reg.codigo, aula("2026-08-08", [("Nota única: tecla repetida no pulso", "em_desenvolvimento")], dificuldades=["acelera no final das frases"], proximo="Cinco dedos"))
    state.atualizar_apos_aula(sessao.repo, reg.codigo)
    sessao.carregar(reg.codigo)
    return reg


# --------------------------------------------------------- caso 19: pseudonimização
def test_nenhum_nome_no_prompt(sessao):
    reg = _preparar(sessao, "Joana")
    cli = _ligar(sessao, [plano_valido()])
    plano = planning.gerar_plano_gemini(sessao, sessao.entrada_planejamento(observacoes="Joana gosta de tocar rápido"))
    assert plano.origem == "gemini"
    assert cli.prompts, "o mock deveria ter recebido um prompt"
    for p in cli.prompts + cli.sistemas:
        assert not re.search(r"(?<!\w)joana(?!\w)", p, flags=re.I)
        assert reg.codigo in p or p == cli.sistemas[0]
    assert "acelera" in cli.prompts[0]  # o histórico vai, o nome não


def test_pseudonimizador_turma_e_restauracao():
    reg = Registro(codigo="PCR-ABC234", tipo="turma", identificacao="Percepção 2A", turma=Turma(nome="Percepção 2A", alunos=[AlunoTurma(id="A01", identificacao="Ana"), AlunoTurma(id="A02", identificacao="Ana Clara")]))
    ps = Pseudonimizador(reg)
    t = ps.aplicar("Ana Clara e Ana cantaram na Percepção 2A.")
    assert "Ana Clara" not in t and "aluno A02" in t and "aluno A01" in t and "a turma PCR-ABC234" in t
    assert not ps.contem_nome(t)
    assert ps.restaurar(t) == "Ana Clara e Ana cantaram na Percepção 2A."


# ------------------------------------------------- caso 21: referência inventada
def test_referencia_inventada_reenvia_e_depois_aceita(sessao):
    _preparar(sessao)
    fontes = [Fonte(titulo="Pedagogia do piano", autor="Autora X", ano="2019", tipo="biblioteca", id_origem="doc1", trecho="pulso")]
    cli = _ligar(sessao, [plano_valido(refs=["inventada-123"]), plano_valido(refs=["doc1"])])
    plano = planning.gerar_plano_gemini(sessao, sessao.entrada_planejamento(referencias=fontes))
    assert plano.origem == "gemini"
    assert [r.id_origem for r in plano.referencias] == ["doc1"]
    assert len(cli.prompts) == 2
    assert "rejeitada pelo validador" in cli.prompts[1] and "inventada-123" in cli.prompts[1]
    assert any("2 tentativas" in a for a in plano.avisos)


def test_tres_falhas_caem_no_modelo_pedagogico(sessao):
    _preparar(sessao)
    ruim = plano_valido()
    ruim["cronograma"][-1]["fim_min"] = 57  # soma errada
    cli = _ligar(sessao, [ruim, ruim, ruim, plano_valido()])
    plano = planning.gerar_plano_gemini(sessao, sessao.entrada_planejamento())
    assert plano.origem == "modelo_pedagogico"
    assert T.GEMINI_FALLBACK in plano.avisos
    assert len(cli.prompts) == 3  # nunca loop
    assert any("soma 57, esperado 50" in a for a in plano.avisos)


def test_falha_de_rede_nao_reenvia(sessao):
    _preparar(sessao)
    cli = _ligar(sessao, [ConnectionError("rede"), plano_valido()])
    plano = planning.gerar_plano_gemini(sessao, sessao.entrada_planejamento())
    assert plano.origem == "modelo_pedagogico" and len(cli.prompts) == 1


def test_habilidade_invalida_removida_com_aviso(sessao):
    _preparar(sessao)
    _ligar(sessao, [plano_valido(habilidades=["EF15AR14", "EF99XX99"])])
    plano = planning.gerar_plano_gemini(sessao, sessao.entrada_planejamento(habilidades_validadas=["EF15AR14"]))
    assert plano.habilidades_curriculares == ["EF15AR14"]
    assert any("não foi(ram) validada" in a and "EF99XX99" in a for a in plano.avisos)


def test_json_malformado_e_cache(sessao):
    _preparar(sessao)
    cli = _ligar(sessao, [{"tema": "só isso"}, plano_valido()])
    plano = planning.gerar_plano_gemini(sessao, sessao.entrada_planejamento())
    assert plano.origem == "gemini" and len(cli.prompts) == 2
    assert "JSON inválido" in cli.prompts[1]
    # mesmo pedido de novo → cache de sessão, sem nova chamada
    plano2 = planning.gerar_plano_gemini(sessao, sessao.entrada_planejamento())
    assert plano2.tema == plano.tema and len(cli.prompts) == 2


def test_plano_gemini_valida_conteudo_musical(sessao):
    _preparar(sessao)
    errado = plano_valido()
    errado["objetivo_geral"] = "Tocar a escala de Sol maior com as notas Sol, Lá, Si, Dó, Ré, Mi, Fá."
    cli = _ligar(sessao, [errado, plano_valido()])
    plano = planning.gerar_plano_gemini(sessao, sessao.entrada_planejamento())
    assert plano.origem == "gemini" and "Fá♯" in cli.prompts[1]


# ------------------------------------------------------------- resumo narrativo
def test_resumo_narrativo_restaura_nome_e_preserva_em_recalculo(sessao):
    reg = _preparar(sessao, "Joana")
    _ligar(sessao, [{"texto": f"O aluno {reg.codigo} consolidou o pulso corporal e ainda acelera no final das frases."}])
    novo = ai_resumo.reescrever(sessao)
    assert novo.gerado_por == "gemini" and novo.texto.startswith("Joana consolidou")
    sessao.repo.gravar_aula(reg.codigo, aula("2026-08-15", [("Cinco dedos: posição fixa tocada no pulso", "em_desenvolvimento")]))
    state.atualizar_apos_aula(sessao.repo, reg.codigo)
    r = sessao.repo.ler_resumo(reg.codigo)
    assert r.gerado_por == "gemini" and r.texto.startswith("Joana") and len(r.ultimos_encontros) == 3
    ai_resumo.salvar_edicao(sessao, "Texto do professor.")
    assert sessao.repo.ler_resumo(reg.codigo).gerado_por == "professor"


def test_resumo_longo_reenviado(sessao):
    _preparar(sessao)
    cli = _ligar(sessao, [{"texto": "x" * 1600}, {"texto": "curto"}])
    novo = ai_resumo.reescrever(sessao)
    assert novo.texto == "curto" and "1600" in cli.prompts[1]


# --------------------------------------------------------- classificação proposta
def test_classificacao_proposta_confere_lista(sessao):
    _preparar(sessao)
    conteudos = ["Nota única: tecla repetida no pulso", "Cinco dedos"]
    cli = _ligar(sessao, [
        {"itens": [{"conteudo": "Nota única: tecla repetida no pulso", "situacao": "consolidado", "motivo": "estável"}]},
        {"itens": [{"conteudo": "Nota única: tecla repetida no pulso", "situacao": "consolidado", "motivo": "estável"}, {"conteudo": "Cinco dedos", "situacao": "dificuldade", "motivo": "instável"}]},
    ])
    prop = classificacao.propor(sessao, conteudos, dificuldades=["troca dedos 3 e 4"])
    assert [p["situacao"] for p in prop] == ["consolidado", "dificuldade"]
    assert "confirme" in prop[1]["motivo"] and len(cli.prompts) == 2


def test_classificacao_sem_gemini_usa_estado(sessao):
    _preparar(sessao)
    sessao.cliente_gemini = None
    prop = classificacao.propor(sessao, ["Corpo: pulso com palmas, passos e balanço", "Novo"])
    assert [p["situacao"] for p in prop] == ["consolidado", "em_desenvolvimento"]


# ------------------------------------------------------------- pergunta livre
def test_pergunta_livre_valida_datas(sessao):
    reg = _preparar(sessao, "Joana")
    cli = _ligar(sessao, [
        {"resposta": "Sim.", "aulas_citadas": ["2030-01-01"], "confianca": "alta"},
        {"resposta": f"O aluno {reg.codigo} acelerou nas duas aulas.", "aulas_citadas": ["2026-08-01", "2026-08-08"], "confianca": "alta"},
    ])
    r = ai_hist.perguntar(sessao, "Joana acelera?")
    assert r.startswith("Joana acelerou") and "01/08/2026" in r and len(cli.prompts) == 2
    assert not re.search(r"(?<!\w)joana(?!\w)", cli.prompts[0], flags=re.I)
