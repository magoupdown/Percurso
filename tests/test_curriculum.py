"""Base curricular (caso 20): existência, etapa, componente, relação com Música; sugestão por tema; fontes 🏛."""
from __future__ import annotations

from percurso.curriculum import bncc, consulta, crmg, validate
from percurso.core.models import Registro, Turma


def test_bases_carregam_com_metadados_oficiais():
    for base in (bncc.bncc_arte(), bncc.bncc_infantil(), crmg.crmg_arte()):
        assert base.documento and base.fonte_oficial and base.url and base.data_obtencao
        assert base.habilidades
    arte = bncc.bncc_arte()
    h = arte.por_codigo("EF15AR14")
    assert h and h.unidade_tematica == "Música" and h.musica and "altura, intensidade, timbre" in h.texto
    assert arte.por_codigo("EF69AR20").objeto == "Materialidades"
    assert len([h for h in arte.habilidades if h.unidade_tematica == "Música"]) == 13
    assert bncc.bncc_infantil().por_codigo("EI03TS03").musica


def test_validacao_codigo_inexistente_e_etapa_errada():
    reg10 = Registro(codigo="PCR-ABC234", idade=10, curriculo="bncc")
    assert validate.validar_codigo("EF15AR14", reg10) == (True, "")
    assert validate.validar_codigo("EF99XX99", reg10)[0] is False
    ok, motivo = validate.validar_codigo("EI03TS03", reg10)
    assert not ok and "etapa" in motivo
    ok, motivo = validate.validar_codigo("EF15AR01", reg10)  # artes visuais
    assert not ok and "Música" in motivo
    reg16 = Registro(codigo="PCR-ABC235", idade=16)
    assert validate.validar_codigo("EM13LGG603", reg16)[0]
    assert not validate.validar_codigo("EF15AR14", reg16)[0]
    r = validate.validar_lista(["EF15AR14", "ef15ar15", "EF99XX99", "EF15AR14"], reg10)
    assert r.validos == ["EF15AR14", "EF15AR15"] and len(r.removidos) == 1
    assert "1 habilidade sugerida não foi validada e foi removida" == r.mensagem_professor


def test_sem_idade_nao_restringe_etapa():
    reg = Registro(codigo="PCR-ABC236")
    assert validate.validar_codigo("EI03TS03", reg)[0] and validate.validar_codigo("EF69AR20", reg)[0]


def test_crmg_so_com_curriculo_bncc_crmg():
    reg = Registro(codigo="PCR-ABC237", idade=8, curriculo="bncc_crmg")
    base = validate.base_para(reg)
    assert any(getattr(h, "documento", "") == "CRMG" for h in base.values()) or base["EF15AR14"].codigo == "EF15AR14"
    assert validate.validar_codigo("EF15AR14", reg)[0]


def test_sugerir_para_tema_e_fonte():
    reg = Registro(codigo="PCR-ABC238", idade=10)
    hab = consulta.sugerir_para_tema("desenvolvimento da pulsação e ritmo", reg)
    assert hab and all(h.etapa == "EF" and h.musica for h in hab)
    assert any(h.codigo == "EF15AR14" for h in hab)
    hab_ei = consulta.sugerir_para_tema("qualidades do som", Registro(codigo="PCR-ABC239", idade=4))
    assert hab_ei and hab_ei[0].codigo.startswith("EI")
    f = consulta.como_fonte(hab[0])
    assert f.tipo == "curricular" and f.id_origem == f"hab:{hab[0].codigo}" and f.url
    assert consulta.listar(Registro(codigo="PCR-ABC240", tipo="turma", turma=Turma(nome="x", faixa_etaria="4 a 5 anos")))[0].etapa == "EI"
