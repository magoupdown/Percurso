"""Plano contextual no Modo Inteligente (SPEC §7.2, §7.5, §8).

Gemini gera → pydantic → cronograma → habilidades → fontes → instrumento → apresentar.
Falha após 3 tentativas → plano do modelo pedagógico (Modo Essencial) com aviso.
"""
from __future__ import annotations

from typing import Any, Dict, List

from .. import config
from ..core import planner, schedule
from ..core.models import Atividade, BlocoCronograma, Fonte, Justificativa, Plano, ProximoPasso
from ..ui import texts as T
from ..utils.logging import obter
from . import context, prompts, schemas, validate_loop
from .anonymize import Pseudonimizador
from .gemini import hash_prompt

log = obter("planning")
ROTULO_GEMINI = "gerado com apoio de IA (Gemini) e validado pelo Percurso"


def _validador_cronograma(duracao: int):
    def _v(obj: schemas.PlanoSaida):
        blocos = [BlocoCronograma(**b.model_dump()) for b in obj.cronograma]
        erro = schedule.validar_cronograma(blocos, duracao)
        if erro:
            raise validate_loop.FalhaValidacao(f"cronograma inválido: {erro}")

    return _v


def _validador_fontes(ids_permitidos: List[str]):
    def _v(obj: schemas.PlanoSaida):
        invalidas = [r.id_origem for r in obj.referencias if r.id_origem not in ids_permitidos]
        if invalidas:
            raise validate_loop.FalhaValidacao(
                f"referências inexistentes: {', '.join(invalidas[:5])}. Use apenas ids da lista 'fontes disponíveis' ou deixe 'referencias' vazia."
            )

    return _v


def _validador_instrumento(perfil: Dict[str, Any], adaptador):
    nome = (perfil.get("nome") or "").lower()

    def _v(obj: schemas.PlanoSaida):
        if not obj.atividades:
            raise validate_loop.FalhaValidacao("o plano precisa ter ao menos uma atividade")
        etapas = {b.etapa for b in obj.cronograma}
        for a in obj.atividades:
            if a.bloco and a.bloco not in etapas:
                raise validate_loop.FalhaValidacao(f"a atividade '{a.titulo}' aponta para o bloco '{a.bloco}', que não existe no cronograma")
        texto = " ".join([obj.tema, obj.objetivo_geral] + [a.descricao for a in obj.atividades])
        avisos = adaptador.validar_conteudo(texto)
        if avisos:
            raise validate_loop.FalhaValidacao("conteúdo musical incorreto: " + " ".join(avisos))
        if not obj.justificativa_pedagogica.estrutura.strip() or not obj.justificativa_pedagogica.adequacao.strip():
            raise validate_loop.FalhaValidacao("a justificativa pedagógica precisa responder às duas perguntas")
        _ = nome

    return _v


def gerar_plano_gemini(sessao, entrada: planner.EntradaPlanejamento) -> Plano:
    """Plano contextual. Se o ciclo falhar, devolve o plano do modelo pedagógico com aviso."""
    base = planner.gerar_plano(entrada)  # fallback pronto e também fonte de estrutura/critérios/sugestão
    cliente = sessao.cliente_gemini
    if cliente is None:
        base.avisos.append(T.GEMINI_FALLBACK)
        return base

    reg = entrada.registro
    ps = Pseudonimizador(reg)
    adaptador = sessao.adaptador(reg.dominio)
    perfil = adaptador.perfil_especialidade(reg.instrumento)
    numeros = {a.id: i + 1 for i, a in enumerate([x for x in entrada.aulas if not x.cancelada])}
    fontes = list(entrada.referencias)
    ids_fontes = [f.id_origem for f in fontes if f.id_origem]
    habilidades = list(entrada.habilidades_validadas)
    quem = f"a turma {reg.codigo}" if reg.eh_turma else f"o aluno {reg.codigo}"

    def montar(erro_anterior: str) -> str:
        return prompts.preencher(
            "plano",
            quem=quem,
            perfil=context.descrever_perfil(reg, perfil.get("nome", reg.instrumento), ps),
            estado=context.descrever_estado(entrada.estado.model_dump(), ps),
            resumo=ps.aplicar(entrada.resumo.texto or "(sem resumo)"),
            ultimas_aulas=context.descrever_aulas(entrada.aulas, numeros, ps),
            perfil_instrumento=context.descrever_perfil_instrumento(perfil, adaptador.tema_do_conteudo(perfil, base.tema)),
            tipo_aula=T.TIPOS_AULA.get(entrada.tipo_aula, entrada.tipo_aula),
            conteudo=ps.aplicar(entrada.conteudo) or "",
            sugestao=f"{base.proximo_passo_sugerido.conteudo} — {base.proximo_passo_sugerido.justificativa}",
            objetivo=ps.aplicar(entrada.objetivo) or "(não indicado)",
            duracao=base.duracao_min,
            recursos=", ".join(base.recursos),
            metodologias=base.metodologia,
            adaptacoes=ps.aplicar(base.adaptacoes),
            observacoes=ps.aplicar(entrada.observacoes) or "(nenhuma)",
            estrutura=" · ".join(f"{b.etapa} {b.fim_min - b.inicio_min} min" for b in base.cronograma),
            habilidades=", ".join(habilidades) if habilidades else "(nenhuma)",
            fontes=context.descrever_fontes(fontes),
            erro_anterior=validate_loop.bloco_erro_para_prompt(erro_anterior),
        )

    sistema = prompts.carregar("sistema")
    chave_cache = hash_prompt("plano", montar(""), habilidades, ids_fontes)
    if chave_cache in sessao.cache_ia:
        dados = sessao.cache_ia[chave_cache]
        return _montar_plano(base, dados, fontes, [])
    removidas: List[str] = []

    def gerar(prompt: str) -> Dict[str, Any]:
        if ps.contem_nome(prompt):
            raise validate_loop.FalhaValidacao("prompt contém nome real (bloqueado pelo Percurso)")
        return cliente.gerar_json(prompt, schemas.PlanoSaida, sistema=sistema)

    def validador_hab(obj):
        invalidas = [h for h in obj.habilidades_curriculares if h not in habilidades]
        if invalidas:
            removidas.extend(invalidas)
            obj.habilidades_curriculares = [h for h in obj.habilidades_curriculares if h in habilidades]

    r = validate_loop.executar(
        gerar,
        montar,
        schemas.PlanoSaida,
        [_validador_cronograma(base.duracao_min), validador_hab, _validador_fontes(ids_fontes), _validador_instrumento(perfil, adaptador)],
        max_tentativas=config.gemini().get("max_tentativas_validacao", 3),
    )
    if not r.ok or r.dados is None:
        base.avisos.append(T.GEMINI_FALLBACK)
        base.avisos.extend(f"tentativa {i + 1}: {e[:200]}" for i, e in enumerate(r.erros))
        log.info("plano Gemini falhou após %d tentativa(s); fallback ao modelo pedagógico", r.tentativas)
        return base
    sessao.cache_ia[chave_cache] = r.dados
    return _montar_plano(base, r.dados, fontes, removidas, tentativas=r.tentativas)


def _montar_plano(base: Plano, d: Dict[str, Any], fontes: List[Fonte], removidas: List[str], tentativas: int = 1) -> Plano:
    por_id = {f.id_origem: f for f in fontes}
    refs = [por_id[r["id_origem"]] for r in d.get("referencias", []) if r.get("id_origem") in por_id]
    avisos = list(base.avisos)
    if removidas:
        avisos.append(f"{len(removidas)} habilidade(s) sugerida(s) não foi(ram) validada(s) e foi(ram) removida(s): {', '.join(removidas)}")
    if tentativas > 1:
        avisos.append(f"A resposta da IA precisou de {tentativas} tentativas para passar na validação.")
    plano = base.model_copy(deep=True)
    plano.origem = "gemini"
    plano.rotulo = ROTULO_GEMINI
    plano.tema = d["tema"]
    plano.objetivo_geral = d["objetivo_geral"]
    plano.objetivos_especificos = d["objetivos_especificos"]
    plano.conteudos = d["conteudos"]
    plano.competencias = d["competencias"]
    plano.habilidades_curriculares = d.get("habilidades_curriculares", [])
    plano.metodologia = d["metodologia"] or base.metodologia
    plano.cronograma = [BlocoCronograma(**b) for b in d["cronograma"]]
    plano.atividades = [Atividade(**a, conteudo=d["tema"]) for a in d["atividades"]]
    plano.intervencoes_professor = d["intervencoes_professor"]
    plano.possiveis_dificuldades = d["possiveis_dificuldades"]
    plano.adaptacoes = d["adaptacoes"] or base.adaptacoes
    plano.avaliacao = d["avaliacao"] or base.avaliacao
    plano.continuidade = d["continuidade"]
    plano.referencias = refs
    plano.justificativa_pedagogica = Justificativa(**d["justificativa_pedagogica"])
    if d.get("proximo_passo_sugerido"):
        plano.proximo_passo_sugerido = ProximoPasso(conteudo=d["proximo_passo_sugerido"], justificativa=d.get("proximo_passo_justificativa", ""), tema=base.proximo_passo_sugerido.tema)
    plano.avisos = avisos
    schedule.exigir_valido(plano.cronograma, plano.duracao_min)
    return plano
