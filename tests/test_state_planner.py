"""Estado determinístico, numeração derivada, continuidade real do planejamento (casos 11, 22)."""
from __future__ import annotations

from percurso.core import planner, schedule, state
from percurso.core.models import EstadoAtual
from percurso.domains import obter_adaptador

from conftest import aula, registro_piano


# ------------------------------------------------------------------ estado
def test_estado_deterministico_e_recorrencia(repo):
    reg = registro_piano(repo)
    repo.gravar_aula(reg.codigo, aula("2026-08-01", [("pulsação corporal", "consolidado"), ("nota única", "em_desenvolvimento")], dificuldades=["acelera no final"], proximo="cinco dedos", obs="obs 1"))
    repo.gravar_aula(reg.codigo, aula("2026-08-08", [("nota única", "consolidado"), ("cinco dedos", "dificuldade")], dificuldades=["acelera no final"], rendimento={"ritmo": 4}))
    est = state.atualizar_apos_aula(repo, reg.codigo)
    assert est.total_aulas == 2
    assert est.conteudos_consolidados == ["pulsação corporal", "nota única"]
    assert est.em_desenvolvimento == ["cinco dedos"]
    assert est.dificuldades_recorrentes == ["acelera no final"]  # citada em 2 aulas
    assert est.proximo_objetivo == "cinco dedos"
    assert est.ultima_observacao == "obs 1"
    assert est.rendimento_recente == {"ritmo": [4]}
    resumo = repo.ler_resumo(reg.codigo)
    assert len(resumo.texto) <= 1500 and "2 aula" in resumo.texto
    assert len(resumo.ultimos_encontros) == 2 and resumo.ultimos_encontros[-1].numero == 2


def test_classificacao_pre_preenchida():
    est = EstadoAtual(conteudos_consolidados=["A"], dificuldades_recorrentes=["B"])
    pre = state.classificacao_pre_preenchida(est, ["a", "B", "C"])
    assert [p["situacao"] for p in pre] == ["consolidado", "dificuldade", "em_desenvolvimento"]


# ------------------------------------------------ caso 22: numeração derivada
def test_registro_retroativo_reordena_numeracao(repo):
    reg = registro_piano(repo)
    a1 = repo.gravar_aula(reg.codigo, aula("2026-08-08", [("x", "consolidado")]))
    a2 = repo.gravar_aula(reg.codigo, aula("2026-08-15", [("y", "consolidado")]))
    assert repo.numero_da_aula(reg.codigo, a1.id) == 1 and repo.numero_da_aula(reg.codigo, a2.id) == 2
    retro = repo.gravar_aula(reg.codigo, aula("2026-08-01", [("w", "consolidado")], tipo_aula="retroativa"))
    canc = repo.gravar_aula(reg.codigo, aula("2026-08-10", frequencia="cancelada_professor"))
    assert repo.numero_da_aula(reg.codigo, retro.id) == 1
    assert repo.numero_da_aula(reg.codigo, a1.id) == 2
    assert repo.numero_da_aula(reg.codigo, canc.id) == 0  # canceladas não numeram
    assert repo.numero_da_aula(reg.codigo, a2.id) == 3
    est = state.atualizar_apos_aula(repo, reg.codigo)
    assert est.total_aulas == 3
    # nenhum arquivo guarda o número
    for arq in repo.caminhos.aulas(reg.codigo).glob("*.json"):
        assert '"numero"' not in arq.read_text(encoding="utf-8")


def test_excluir_aula_recalcula(repo):
    reg = registro_piano(repo)
    a = repo.gravar_aula(reg.codigo, aula("2026-08-08", [("x", "consolidado")]))
    state.atualizar_apos_aula(repo, reg.codigo)
    assert repo.excluir_aula(reg.codigo, a.id)
    est = state.atualizar_apos_aula(repo, reg.codigo)
    assert est.total_aulas == 0 and est.conteudos_consolidados == []


# ------------------------------------------- caso 11: segunda aula usa o estado
def _entrada(repo, reg, **kw):
    return planner.EntradaPlanejamento(
        registro=repo.ler_registro(reg.codigo),
        estado=repo.ler_estado(reg.codigo),
        resumo=repo.ler_resumo(reg.codigo),
        aulas=repo.listar_aulas(reg.codigo),
        repertorio=repo.ler_repertorio(reg.codigo),
        pasta_perfis_editados=repo.caminhos.perfis_editados,
        **kw,
    )


def test_segunda_aula_nao_repete_consolidado(repo):
    reg = registro_piano(repo)
    ad = obter_adaptador("musica", repo.caminhos.perfis_editados)
    prog = ad.perfil_especialidade("piano")["progressoes"]["pulsacao"]
    plano1 = planner.gerar_plano(_entrada(repo, reg))
    assert plano1.tema == prog[0]  # sem histórico: primeiro passo da progressão
    assert schedule.validar_cronograma(plano1.cronograma, plano1.duracao_min) is None
    assert plano1.rotulo == planner.ROTULO_ESSENCIAL
    assert plano1.justificativa_pedagogica.estrutura and plano1.justificativa_pedagogica.adequacao

    repo.gravar_aula(reg.codigo, aula("2026-08-01", [(prog[0], "consolidado")]))
    state.atualizar_apos_aula(repo, reg.codigo)
    plano2 = planner.gerar_plano(_entrada(repo, reg))
    assert plano2.tema == prog[1]
    assert prog[0] not in plano2.conteudos
    assert prog[0] in plano2.conhecimentos_previos
    assert "1 aula(s) anteriores" in plano2.justificativa_pedagogica.estrutura


def test_plano_usa_dificuldade_recorrente_e_proximo_objetivo(repo, registro_com_14_aulas):
    reg = registro_com_14_aulas
    est = repo.ler_estado(reg.codigo)
    assert est.total_aulas == 13  # 14 registradas − 1 cancelada (a falta conta como aula)
    assert "acelera no final das frases" in est.dificuldades_recorrentes
    plano = planner.gerar_plano(_entrada(repo, reg))
    assert plano.tema not in est.conteudos_consolidados
    assert any("acelera" in d for d in plano.possiveis_dificuldades)
    assert any("acelera" in i for i in plano.intervencoes_professor)
    md = planner.plano_como_markdown(plano)
    assert "Justificativa pedagógica" in md and "Cronograma" in md


def test_plano_revisao_prioriza_dificuldades(repo, registro_com_14_aulas):
    reg = registro_com_14_aulas
    plano = planner.gerar_plano(_entrada(repo, reg, tipo_aula="revisao"))
    assert plano.tipo_aula == "revisao"
    assert plano.conteudos[0] == "acelera no final das frases" or "acelera" in plano.objetivo_geral


def test_plano_extraordinaria_nao_altera_unidade(repo, registro_com_14_aulas):
    reg = registro_com_14_aulas
    plano = planner.gerar_plano(_entrada(repo, reg, tipo_aula="extraordinaria", conteudo="Parabéns pra você para apresentação", duracao_min=30))
    assert plano.tipo_aula == "extraordinaria" and plano.duracao_min == 30
    assert schedule.validar_cronograma(plano.cronograma, 30) is None
    assert plano.tema == "Parabéns pra você para apresentação"


def test_plano_respeita_recursos_e_idade(repo):
    reg = registro_piano(repo)
    plano = planner.gerar_plano(_entrada(repo, reg, recursos=["nenhum"]))
    for a in plano.atividades:
        assert not (set(a.recursos) - {"nenhum"}), a


def test_aula_a_partir_do_plano(repo):
    reg = registro_piano(repo)
    plano = repo.gravar_plano(planner.gerar_plano(_entrada(repo, reg)))
    form = planner.aula_a_partir_do_plano(plano, repo.ler_estado(reg.codigo))
    assert form["plano_origem"] == f"planos/{plano.nome_arquivo()}"
    assert form["classificacao"][0]["conteudo"] == plano.tema


# ------------------------------------------------ diferenciação por instrumento
def test_pulsacao_diferente_por_instrumento():
    ad = obter_adaptador("musica")
    p = {i: ad.perfil_especialidade(i)["progressoes"]["pulsacao"] for i in ["piano", "flauta_doce", "percussao"]}
    assert "cinco dedos" in " ".join(p["piano"]).lower()
    assert "respira" in " ".join(p["flauta_doce"]).lower() and "sol" in " ".join(p["flauta_doce"]).lower()
    assert "ostinato" in " ".join(p["percussao"]).lower()
    assert len({tuple(v) for v in p.values()}) == 3


def test_todos_os_instrumentos_da_secao_1_4():
    ad = obter_adaptador("musica")
    ids = {e["id"] for e in ad.listar_especialidades()}
    esperados = {"piano", "teclado", "violao", "guitarra", "flauta_doce", "flauta_transversal", "clarinete", "saxofone", "trompete", "trombone", "violino", "viola", "violoncelo", "canto", "coral", "bateria", "percussao", "percepcao_musical", "musicalizacao", "teoria_musical", "pratica_conjunto", "outro"}
    assert esperados <= ids


def test_perfil_editado_pelo_professor(repo):
    ad = obter_adaptador("musica", repo.caminhos.perfis_editados)
    base = ad.perfil_especialidade("piano")
    repo.gravar_perfil_editado("piano", {"id": "piano", "dificuldades_frequentes": ["minha dificuldade"]})
    from percurso.domains import limpar_cache

    limpar_cache()
    ad2 = obter_adaptador("musica", repo.caminhos.perfis_editados)
    p = ad2.perfil_especialidade("piano")
    assert p["dificuldades_frequentes"] == ["minha dificuldade"] and p.get("editado_pelo_professor")
    assert p["progressoes"] == base["progressoes"]  # o resto vem do original


def test_music21_deterministico(tmp_path):
    from percurso.domains.music import theory

    assert theory.notas_escala("G", "maior")[:7] == ["G4", "A4", "B4", "C5", "D5", "E5", "F#5"]
    assert theory.tonalidade_pt("G") == "Sol maior" and theory.tonalidade_pt("e") == "Mi menor"
    assert theory.intervalo("C4", "G4")["nome"] == "P5"
    assert theory.acorde(["C4", "E4", "G4"])["qualidade"] == "major"
    ad = obter_adaptador("musica")
    r = ad.gerar_material_deterministico("escala", {"tonica": "G", "tipo_escala": "maior", "oitava": 4, "destino": str(tmp_path), "nome_base": "sol_maior"})
    assert (tmp_path / "sol_maior.mid").exists() and (tmp_path / "sol_maior.musicxml").exists()
    avisos = theory.validar_texto_musical("A escala de Sol maior tem as notas Sol, Lá, Si, Dó, Ré, Mi, Fá.")
    assert avisos and "Fá♯" in avisos[0]
