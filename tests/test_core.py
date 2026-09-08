"""Códigos, cronograma, frequência, rendimento (SPEC §16.2 casos 9, 12, 13)."""
from __future__ import annotations

import pytest

from percurso.core import attendance, codes, grading, schedule
from percurso.core.models import Aula, BlocoCronograma, Registro, Rubricas

from conftest import aula


# ---------------------------------------------------------------- códigos
def test_codigo_formato_e_alfabeto():
    for _ in range(200):
        c = codes.gerar()
        assert codes.valido(c)
        assert not any(ch in c[4:] for ch in "0O1I")


def test_codigo_sem_colisao():
    existentes = {"PCR-AAAAAA"}
    c = codes.gerar(existe=lambda x: x in existentes)
    assert c not in existentes


def test_codigo_normalizacao():
    assert codes.normalizar("pcr7k4m2q") == "PCR-7K4M2Q"
    assert codes.normalizar(" PCR 7K4M2Q ") == "PCR-7K4M2Q"
    assert codes.normalizar("7k4m2q") == "PCR-7K4M2Q"
    with pytest.raises(ValueError):
        codes.normalizar_e_validar("PCR-0O1I00")
    with pytest.raises(ValueError):
        codes.normalizar_e_validar("abc")


# ------------------------------------------------------------- cronograma
def _blocos():
    return [
        BlocoCronograma(inicio_min=0, fim_min=5, titulo="Acolhimento", etapa="acolhimento"),
        BlocoCronograma(inicio_min=5, fim_min=12, titulo="Retomada", etapa="introducao"),
        BlocoCronograma(inicio_min=12, fim_min=22, titulo="Exploração", etapa="exploracao"),
        BlocoCronograma(inicio_min=22, fim_min=37, titulo="Prática", etapa="pratica"),
        BlocoCronograma(inicio_min=37, fim_min=45, titulo="Aplicação", etapa="aplicacao"),
        BlocoCronograma(inicio_min=45, fim_min=47, titulo="Avaliação", etapa="avaliacao"),
        BlocoCronograma(inicio_min=47, fim_min=50, titulo="Fechamento", etapa="fechamento"),
    ]


def test_cronograma_valido_soma_exata():
    assert schedule.validar_cronograma(_blocos(), 50) is None
    assert schedule.validar_cronograma(_blocos(), 57) == "soma 50, esperado 57"


def test_cronograma_erros_especificos():
    b = _blocos()
    b[2].inicio_min = 13
    assert "começa em 13" in schedule.validar_cronograma(b, 50)
    b = _blocos()
    b[0].inicio_min = 2
    assert "esperado 0" in schedule.validar_cronograma(b, 50)
    assert schedule.validar_cronograma([], 50) == "cronograma vazio"


@pytest.mark.parametrize("nova", [20, 30, 45, 60, 75, 90, 120, 15, 10])
def test_adaptar_duracao_mantem_estrutura_e_minimos(nova):
    b = _blocos()
    novos = schedule.adaptar_duracao(b, nova)
    assert schedule.validar_cronograma(novos, nova) is None
    assert [x.titulo for x in novos] == [x.titulo for x in b]  # nenhuma atividade cortada
    assert [x.etapa for x in novos] == [x.etapa for x in b]
    ultimo = novos[-1]
    assert ultimo.fim_min - ultimo.inicio_min >= 1
    if nova >= sum(schedule.MINIMOS.values()):
        for x in novos:
            assert x.fim_min - x.inicio_min >= schedule.MINIMOS[x.etapa]


def test_adaptar_duracao_residuo_vai_para_pratica():
    novos = schedule.adaptar_duracao(_blocos(), 53)
    pratica = next(x for x in novos if x.etapa == "pratica")
    assert pratica.fim_min - pratica.inicio_min >= 15


def test_montar_de_template():
    tpl = [{"etapa": "acolhimento", "titulo": "A", "minutos": 5}, {"etapa": "pratica", "titulo": "P", "minutos": 20}, {"etapa": "fechamento", "titulo": "F", "minutos": 5}]
    blocos = schedule.montar_de_template(tpl, 45)
    assert schedule.validar_cronograma(blocos, 45) is None


# ------------------------------------------------------------- frequência
def test_frequencia_percentuais_com_canceladas_e_reposicoes():
    aulas = [
        aula("2026-03-01", frequencia="presente"),
        aula("2026-03-08", frequencia="falta"),
        aula("2026-03-15", frequencia="falta_justificada"),
        aula("2026-03-22", frequencia="reposicao"),
        aula("2026-03-29", frequencia="cancelada_instituicao"),
        aula("2026-04-05", frequencia="cancelada_professor"),
        aula("2026-04-12", frequencia="aula_extra"),
        aula("2026-04-19", frequencia="presente"),
    ]
    r = attendance.calcular(aulas)
    assert r.aulas_registradas == 8
    assert r.canceladas_instituicao == 1 and r.canceladas_professor == 1
    assert r.aulas_previstas == 6  # 8 − 1 instituição − 1 professor
    assert r.presencas == 2 and r.reposicoes == 1 and r.aulas_extras == 1
    assert r.frequencia_percentual == round(100 * 4 / 6, 1)
    assert r.tempo_total_min == 4 * 50
    r2 = attendance.calcular(aulas, penalizar_cancelada_professor=True)
    assert r2.aulas_previstas == 7
    r3 = attendance.calcular(aulas, inicio="2026-04-01")
    assert r3.aulas_registradas == 3


def test_frequencia_turma_por_aluno():
    from percurso.core.models import AlunoTurma, FrequenciaTurma, Turma

    reg = Registro(codigo="PCR-ABCDEF", tipo="turma", modalidade="turma", instrumento="percepcao_musical", turma=Turma(nome="2A", quantidade_alunos=2, alunos=[AlunoTurma(id="A01", identificacao="Ana"), AlunoTurma(id="A02", identificacao="Bruno")]))
    aulas = [
        aula("2026-03-01", frequencia_turma=FrequenciaTurma(presentes=["A01", "A02"], ausentes=[])),
        aula("2026-03-08", frequencia_turma=FrequenciaTurma(presentes=["A01"], ausentes=["A02"])),
        aula("2026-03-15", frequencia="cancelada_instituicao"),
    ]
    r = attendance.calcular(aulas, registro=reg)
    assert r.por_aluno["A01"]["percentual"] == 100.0
    assert r.por_aluno["A02"]["percentual"] == 50.0


# -------------------------------------------------------------- rendimento
def test_rendimento_nunca_inventado():
    a = Aula(id="x", data="2026-01-01", rendimento={"leitura": 3, "ritmo": None, "tecnica": ""})
    assert a.rendimento == {"leitura": 3}
    assert grading.validar_rendimento({"a": 6, "b": 0, "c": "4"}) == {"c": 4}


def test_evolucao_e_recentes():
    aulas = [aula("2026-01-0%d" % i, rendimento={"leitura": i}) for i in range(1, 6)]
    ev = grading.evolucao(aulas)
    assert [n for _, n in ev["leitura"]] == [1, 2, 3, 4, 5]
    assert grading.recentes(aulas, 3) == {"leitura": [3, 4, 5]}
    assert grading.tendencia([3, 4, 5]) == "subindo"


def test_criterios_ativos_com_rubrica_propria():
    reg = Registro(codigo="PCR-ABCDEF")
    rub = Rubricas(criterios_proprios={"expressao": "Expressão"})
    crit = grading.criterios_ativos(reg, ["leitura", "ritmo"], rub)
    assert crit == ["leitura", "ritmo", "expressao"]
    assert grading.rotulo("expressao", rub) == "Expressão"
    reg.rubrica_ativa = False
    assert grading.criterios_ativos(reg, ["leitura"], rub) == []
