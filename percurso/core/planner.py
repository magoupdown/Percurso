"""Planejamento de aula no Modo Essencial (SPEC §8). Motor de templates + perfis instrumentais.

O núcleo obtém o adaptador por `percurso.domains.obter_adaptador` e nunca importa `domains.music`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .. import config
from ..domains import obter_adaptador
from ..utils import dates
from . import grading, schedule, state as state_mod
from .models import (
    Atividade,
    Aula,
    BlocoCronograma,
    EstadoAtual,
    Fonte,
    Justificativa,
    Plano,
    ProximoPasso,
    Registro,
    Repertorio,
    ResumoPedagogico,
)

ROTULO_ESSENCIAL = "gerado por modelo pedagógico (sem IA)"

METODOLOGIAS_NOME = {
    "dalcroze": "Dalcroze (movimento e rítmica)",
    "orff": "Orff (exploração, instrumental e fala rítmica)",
    "kodaly": "Kodály (canto, solfa e leitura)",
    "gordon": "Gordon (audiação e padrões)",
    "swanwick": "Swanwick (composição, apreciação e performance)",
    "propria": "abordagem própria do professor",
    "combinacao": "combinação de abordagens",
    "sem_preferencia": "sem preferência metodológica declarada",
}

CONTEXTO_NOME = {
    "escola": "escola",
    "conservatorio": "conservatório",
    "aula_particular": "aula particular",
    "projeto_social": "projeto social",
    "curso_livre": "curso livre",
    "outro": "outro contexto",
}


@dataclass
class EntradaPlanejamento:
    registro: Registro
    estado: EstadoAtual
    resumo: ResumoPedagogico
    aulas: List[Aula]
    repertorio: Repertorio = field(default_factory=Repertorio)
    tipo_aula: str = "continuidade"
    conteudo: str = ""  # vazio = "O que devo trabalhar agora?"
    objetivo: str = ""
    duracao_min: Optional[int] = None
    recursos: Optional[List[str]] = None
    observacoes: str = ""
    referencias: List[Fonte] = field(default_factory=list)
    consultas_realizadas: List[str] = field(default_factory=list)
    habilidades_validadas: List[str] = field(default_factory=list)
    data: str = ""
    pasta_perfis_editados: Any = None
    nova_unidade: str = ""
    rubricas_professor: Any = None


def _faixa_etaria(registro: Registro) -> str:
    if registro.eh_turma and registro.turma and registro.turma.faixa_etaria:
        return registro.turma.faixa_etaria
    if registro.idade is not None:
        return f"{registro.idade} anos"
    return "não informada"


def _idade_ref(registro: Registro) -> Optional[int]:
    if registro.idade is not None:
        return registro.idade
    if registro.eh_turma and registro.turma and registro.turma.faixa_etaria:
        import re

        m = re.search(r"\d+", registro.turma.faixa_etaria)
        if m:
            return int(m.group())
    return None


def _chave_template(registro: Registro, tipo_aula: str) -> str:
    if tipo_aula in ("revisao", "extraordinaria"):
        return tipo_aula
    if registro.tipo == "turma":
        return "turma"
    if registro.tipo == "dupla":
        return "dupla"
    return "individual"


def _repertorio_pendente(rep: Repertorio) -> List[str]:
    return [i.obra for i in rep.itens if i.estado in ("em_estudo", "revisao", "apresentacao")]


def sugerir_proximo_passo(entrada: EntradaPlanejamento) -> ProximoPasso:
    adaptador = obter_adaptador(entrada.registro.dominio, entrada.pasta_perfis_editados)
    perfil = adaptador.perfil_especialidade(entrada.registro.instrumento)
    sug = adaptador.progressao_sugerida(entrada.estado.model_dump(), perfil, entrada.registro.curriculo)
    return ProximoPasso(conteudo=sug.get("conteudo", ""), tema=sug.get("tema", ""), justificativa=sug.get("justificativa", ""))


def gerar_plano(entrada: EntradaPlanejamento) -> Plano:
    """Gera um plano completo (SPEC §8.4) validado pelo cronograma (§8.2)."""
    reg = entrada.registro
    est = entrada.estado
    adaptador = obter_adaptador(reg.dominio, entrada.pasta_perfis_editados)
    perfil = adaptador.perfil_especialidade(reg.instrumento)
    duracao = int(entrada.duracao_min or reg.agenda.duracao_min or config.defaults().get("duracao_padrao_min", 50))
    recursos = list(entrada.recursos) if entrada.recursos is not None else list(reg.recursos_habituais)
    idade = _idade_ref(reg)
    tipo = entrada.tipo_aula
    avisos: List[str] = []

    # 1) conteúdo
    sugestao = sugerir_proximo_passo(entrada)
    if tipo == "revisao":
        conteudos = _conteudos_revisao(est, entrada.repertorio)
        conteudo_principal = entrada.conteudo.strip() or (conteudos[0] if conteudos else sugestao.conteudo)
        if not conteudos:
            conteudos = [conteudo_principal]
    else:
        conteudo_principal = entrada.conteudo.strip() or sugestao.conteudo
        conteudos = [conteudo_principal]
        # continuidade: retoma o que está em desenvolvimento sem repetir o consolidado
        for c in est.em_desenvolvimento[-2:]:
            if c.lower() != conteudo_principal.lower() and c not in conteudos:
                conteudos.append(c)
    consolidados_norm = {c.lower() for c in est.conteudos_consolidados}
    conteudos = [c for c in conteudos if c.lower() not in consolidados_norm or c.lower() == conteudo_principal.lower()]
    if conteudo_principal.lower() in consolidados_norm and tipo not in ("revisao", "extraordinaria"):
        avisos.append(f"'{conteudo_principal}' já consta como consolidado; a aula o usa como base para ampliar.")

    tema = adaptador.tema_do_conteudo(perfil, conteudo_principal) or sugestao.tema or ""

    # 2) cronograma
    template = config.template_cronograma(_chave_template(reg, tipo))
    cronograma = schedule.montar_de_template(template, duracao)
    erro = schedule.validar_cronograma(cronograma, duracao)
    if erro:
        raise schedule.ErroCronograma(erro)

    # 3) atividades = exercícios do perfil filtrados por recursos e idade, distribuídos nos blocos
    exercicios = adaptador.exercicios_para(perfil, conteudo_principal, recursos, idade, maximo=4)
    # exercícios exatos para o conteúdo que ficaram de fora por falta de recurso → aviso ao professor
    sem_filtro = adaptador.exercicios_para(perfil, conteudo_principal, [], idade, maximo=6)
    titulos = {e.get("titulo") for e in exercicios}
    for e in sem_filtro:
        if e.get("titulo") not in titulos and any(c.lower() == conteudo_principal.lower() for c in e.get("conteudos", [])):
            faltam = [r for r in e.get("recursos", []) if r not in (recursos or [])]
            if faltam:
                avisos.append(f"O exercício '{e.get('titulo')}' seria o mais direto para este conteúdo, mas exige {', '.join(faltam)}.")
    atividades = _distribuir_atividades(cronograma, exercicios, conteudo_principal, est, reg, tipo, entrada)

    # 4) avaliação = rubrica ativa
    criterios = grading.criterios_ativos(
        reg, adaptador.rubrica_padrao(reg.instrumento, reg.modalidade, idade), entrada.rubricas_professor
    )
    avaliacao = _texto_avaliacao(criterios, adaptador, entrada.rubricas_professor)

    # 5) continuidade = próximo item da progressão após o conteúdo atual
    continuidade = _continuidade(perfil, tema, conteudo_principal, est, adaptador)

    # 6) referências = pesquisa (se solicitada) — só o que veio verificado
    referencias = list(entrada.referencias)

    objetivos_esp = _objetivos_especificos(conteudo_principal, est, tipo, perfil, tema)
    objetivo_geral = entrada.objetivo.strip() or _objetivo_geral(conteudo_principal, tipo, reg)
    dificuldades = _dificuldades(est, adaptador, perfil, conteudo_principal)
    intervencoes = _intervencoes(est, conteudo_principal, tipo, perfil)
    justificativa = _justificativa(reg, est, perfil, conteudo_principal, tema, tipo, exercicios, sugestao, duracao)

    metodologia = ", ".join(METODOLOGIAS_NOME.get(m, m) for m in reg.metodologias) or METODOLOGIAS_NOME["sem_preferencia"]
    unidade = entrada.nova_unidade.strip() if tipo == "nova_unidade" and entrada.nova_unidade else est.unidade_atual

    plano = Plano(
        id="",
        codigo_registro=reg.codigo,
        data=entrada.data or dates.hoje().isoformat(),
        status="gerado",
        origem="modelo_pedagogico",
        tipo_aula=tipo,  # type: ignore[arg-type]
        tema=conteudo_principal,
        contexto=CONTEXTO_NOME.get(reg.contexto, reg.contexto),
        faixa_etaria=_faixa_etaria(reg),
        nivel=reg.nivel,
        instrumento=reg.nome_instrumento_exibicao if reg.instrumento == "outro" else perfil.get("nome", reg.instrumento),
        duracao_min=duracao,
        objetivo_geral=objetivo_geral,
        objetivos_especificos=objetivos_esp,
        conhecimentos_previos=list(reg.conhecimentos_previos) + [c for c in est.conteudos_consolidados[-5:] if c not in reg.conhecimentos_previos],
        conteudos=conteudos,
        competencias=_competencias(tema, perfil),
        habilidades_curriculares=list(entrada.habilidades_validadas),
        recursos=recursos or ["nenhum recurso específico"],
        metodologia=metodologia,
        cronograma=cronograma,
        atividades=atividades,
        intervencoes_professor=intervencoes,
        possiveis_dificuldades=dificuldades,
        adaptacoes=reg.adaptacoes or "Nenhuma adaptação registrada pelo professor.",
        avaliacao=avaliacao,
        criterios=criterios,
        continuidade=continuidade,
        referencias=referencias,
        justificativa_pedagogica=justificativa,
        proximo_passo_sugerido=sugestao,
        consultas_realizadas=list(entrada.consultas_realizadas),
        unidade=unidade,
        avisos=avisos,
        rotulo=ROTULO_ESSENCIAL,
    )
    schedule.exigir_valido(plano.cronograma, plano.duracao_min)
    return plano


# --------------------------------------------------------------------------- auxiliares
def _conteudos_revisao(est: EstadoAtual, rep: Repertorio) -> List[str]:
    """Revisão prioriza: dificuldades recorrentes, conteúdos instáveis, pré-requisitos, repertório pendente."""
    saida: List[str] = []
    for c in est.dificuldades_recorrentes + est.dificuldades_recentes + est.em_desenvolvimento:
        if c not in saida:
            saida.append(c)
    for obra in _repertorio_pendente(rep)[:2]:
        item = f"repertório: {obra}"
        if item not in saida:
            saida.append(item)
    return saida[:5]


def _distribuir_atividades(
    cronograma: List[BlocoCronograma],
    exercicios: List[Dict[str, Any]],
    conteudo: str,
    est: EstadoAtual,
    reg: Registro,
    tipo: str,
    entrada: EntradaPlanejamento,
) -> List[Atividade]:
    atividades: List[Atividade] = []
    fila = list(exercicios)
    ultimo_conteudo = est.conteudos_trabalhados_recentes[:2]
    for bloco in cronograma:
        dur = bloco.fim_min - bloco.inicio_min
        etapa = bloco.etapa
        if etapa == "acolhimento":
            desc = "Chegada, afinação/ajuste do instrumento, breve aquecimento corporal ou vocal."
            if reg.eh_turma:
                desc = "Roda inicial, atividade corporal curta com pulso e organização do espaço."
            atividades.append(Atividade(titulo=bloco.titulo, descricao=desc, duracao_min=dur, bloco=etapa))
        elif etapa == "introducao":
            if tipo == "revisao":
                desc = "Retomar rapidamente os pontos instáveis: " + (", ".join(est.dificuldades_recorrentes[:3] + est.dificuldades_recentes[:2]) or conteudo) + "."
            elif ultimo_conteudo:
                desc = "Retomar " + ", ".join(ultimo_conteudo) + " em execução curta, observando o que se manteve desde a última aula."
            else:
                desc = f"Apresentar o conteúdo de hoje ({conteudo}) e relacioná-lo com o que o aluno já faz."
            atividades.append(Atividade(titulo=bloco.titulo, descricao=desc, duracao_min=dur, bloco=etapa, conteudo=conteudo))
        elif etapa in ("exploracao", "pratica", "aplicacao"):
            if fila:
                ex = fila.pop(0)
                atividades.append(
                    Atividade(
                        titulo=ex.get("titulo", bloco.titulo),
                        descricao=ex.get("descricao", ""),
                        duracao_min=dur,
                        bloco=etapa,
                        recursos=list(ex.get("recursos") or []),
                        conteudo=conteudo,
                    )
                )
            else:
                generico = {
                    "exploracao": f"Explorar {conteudo} por imitação e experimentação guiada, sem partitura, antes de formalizar.",
                    "pratica": f"Praticar {conteudo} em repetições curtas com variação (andamento lento, mão/voz isolada, trechos pequenos).",
                    "aplicacao": f"Aplicar {conteudo} em um trecho de repertório ou canção conhecida.",
                }[etapa]
                atividades.append(Atividade(titulo=bloco.titulo, descricao=generico, duracao_min=dur, bloco=etapa, conteudo=conteudo))
        elif etapa == "avaliacao":
            atividades.append(
                Atividade(
                    titulo=bloco.titulo,
                    descricao="Observar e registrar os critérios da rubrica; classificar o conteúdo como consolidado, em desenvolvimento ou dificuldade.",
                    duracao_min=dur,
                    bloco=etapa,
                )
            )
        elif etapa == "fechamento":
            atividades.append(
                Atividade(
                    titulo=bloco.titulo,
                    descricao="Recapitular o que foi feito, combinar a tarefa de casa e anunciar o próximo passo.",
                    duracao_min=dur,
                    bloco=etapa,
                )
            )
        else:
            atividades.append(Atividade(titulo=bloco.titulo, descricao=bloco.descricao, duracao_min=dur, bloco=etapa))
    # exercícios restantes viram alternativas
    for ex in fila:
        atividades.append(
            Atividade(
                titulo=f"Alternativa: {ex.get('titulo', '')}",
                descricao=ex.get("descricao", ""),
                duracao_min=int(ex.get("duracao_min", 0) or 0),
                bloco="alternativa",
                recursos=list(ex.get("recursos") or []),
                conteudo=conteudo,
            )
        )
    return atividades


def _texto_avaliacao(criterios: List[str], adaptador, rubricas) -> str:
    if not criterios:
        return "Rubrica desativada para este registro. Avaliação qualitativa apenas."
    rot = [grading.rotulo(c, rubricas) for c in criterios]
    return "Observação durante a prática, com registro de 1 a 5 nos critérios: " + ", ".join(rot) + ". Só registrar o que foi efetivamente observado."


def _continuidade(perfil: Dict[str, Any], tema: str, conteudo: str, est: EstadoAtual, adaptador) -> str:
    progressoes = perfil.get("progressoes") or {}
    etapas = progressoes.get(tema, []) if tema else []
    proximo = ""
    if etapas:
        norm = [e.lower() for e in etapas]
        try:
            i = norm.index(conteudo.lower())
            if i + 1 < len(etapas):
                proximo = etapas[i + 1]
        except ValueError:
            proximo = next((e for e in etapas if e.lower() not in {c.lower() for c in est.conteudos_consolidados}), "")
    if proximo:
        return f"Se '{conteudo}' se mostrar estável, a próxima aula avança para '{proximo}'. Caso contrário, repete-se com variação."
    return f"Reavaliar '{conteudo}' na próxima aula; avançar somente quando estiver consolidado."


def _objetivo_geral(conteudo: str, tipo: str, reg: Registro) -> str:
    if tipo == "revisao":
        return f"Consolidar conteúdos instáveis, com foco em {conteudo}."
    if tipo == "extraordinaria":
        return f"Preparar {conteudo} para o encontro/apresentação específica, sem alterar a unidade em andamento."
    if tipo == "nova_unidade":
        return f"Iniciar nova unidade de trabalho a partir de {conteudo}."
    return f"Desenvolver {conteudo} com continuidade em relação ao percurso anterior."


def _objetivos_especificos(conteudo: str, est: EstadoAtual, tipo: str, perfil: Dict[str, Any], tema: str) -> List[str]:
    saida = [f"Executar {conteudo} com regularidade em andamento confortável."]
    if est.dificuldades_recorrentes:
        saida.append(f"Reduzir a dificuldade recorrente: {est.dificuldades_recorrentes[0]}.")
    if est.em_desenvolvimento:
        saida.append(f"Manter em prática: {', '.join(est.em_desenvolvimento[-2:])}.")
    if tema == "leitura":
        saida.append("Relacionar o que é tocado com a notação correspondente.")
    elif tema == "percepcao":
        saida.append("Reconhecer auditivamente o conteúdo antes de executá-lo.")
    elif tema == "repertorio":
        saida.append("Aplicar o conteúdo em trecho de repertório.")
    return saida[:4]


def _competencias(tema: str, perfil: Dict[str, Any]) -> List[str]:
    base = {
        "pulsacao": ["senso de pulsação", "coordenação motora", "escuta"],
        "leitura": ["leitura musical", "relação som–símbolo", "autonomia"],
        "tecnica": ["técnica instrumental", "postura", "controle motor"],
        "percepcao": ["percepção auditiva", "memória musical", "escuta ativa"],
        "repertorio": ["expressividade", "fraseado", "autonomia"],
    }
    return base.get(tema, ["escuta", "execução", "autonomia"])


def _dificuldades(est: EstadoAtual, adaptador, perfil: Dict[str, Any], conteudo: str) -> List[str]:
    saida = list(est.dificuldades_recorrentes[:2]) + [d for d in est.dificuldades_recentes[:2] if d not in est.dificuldades_recorrentes]
    for d in adaptador.dificuldades_esperadas(perfil, conteudo):
        if d not in saida:
            saida.append(d)
    return saida[:5]


def _intervencoes(est: EstadoAtual, conteudo: str, tipo: str, perfil: Dict[str, Any]) -> List[str]:
    saida = [
        "Demonstrar antes de explicar; pedir imitação em trechos curtos.",
        "Reduzir o andamento ao primeiro sinal de instabilidade, em vez de repetir com erro.",
    ]
    if est.ultima_observacao:
        saida.append(f"Atenção à observação anterior: {est.ultima_observacao}")
    if est.dificuldades_recorrentes:
        saida.append(f"Isolar '{est.dificuldades_recorrentes[0]}' em exercício de 1–2 compassos antes de reinserir no contexto.")
    if tipo == "revisao":
        saida.append("Não introduzir conteúdo novo; encerrar cada bloco com uma execução estável.")
    return saida[:5]


def _justificativa(reg: Registro, est: EstadoAtual, perfil: Dict[str, Any], conteudo: str, tema: str, tipo: str, exercicios: List[Dict[str, Any]], sugestao: ProximoPasso, duracao: int) -> Justificativa:
    inst = perfil.get("nome", reg.instrumento)
    estrutura = (
        f"A aula de {duracao} minutos segue a estrutura acolhimento → retomada → exploração → prática → aplicação → avaliação → fechamento"
        if tipo not in ("revisao", "extraordinaria")
        else f"A aula de {duracao} minutos é organizada como {tipo}, priorizando prática focada"
    )
    estrutura += f", porque o registro indica {est.total_aulas} aula(s) anteriores"
    if est.em_desenvolvimento:
        estrutura += f", com '{est.em_desenvolvimento[-1]}' ainda em desenvolvimento"
    if est.dificuldades_recorrentes:
        estrutura += f" e a dificuldade recorrente '{est.dificuldades_recorrentes[0]}'"
    estrutura += f". O conteúdo central ('{conteudo}') foi escolhido assim: {sugestao.justificativa or 'indicação direta do professor.'}"
    if exercicios:
        nomes = ", ".join(e.get("titulo", "") for e in exercicios[:3])
        adequacao = (
            f"Os exercícios ({nomes}) vêm do perfil pedagógico de {inst} para o tema '{tema or conteudo}', "
            f"respeitam a tessitura e as técnicas fundamentais do instrumento e foram filtrados pelos recursos disponíveis e pela idade "
            f"({_faixa_etaria(reg)}). São hipóteses pedagógicas editáveis, não prescrições."
        )
    else:
        adequacao = f"Não há exercícios específicos no perfil de {inst} para '{conteudo}'; as atividades genéricas seguem a progressão do instrumento e podem ser ajustadas no perfil editável."
    return Justificativa(estrutura=estrutura, adequacao=adequacao)


def plano_como_markdown(plano: Plano, adaptador=None, rubricas=None) -> str:
    """Renderização textual do plano (PT-BR) para tela e exportação."""
    L: List[str] = []
    L.append(f"# Plano de aula — {plano.tema}")
    L.append(f"*{plano.rotulo}* · {dates.formatar_data_br(plano.data)} · {plano.tipo_aula.replace('_', ' ')}")
    L.append("")
    L.append(f"**Contexto:** {plano.contexto} · **Faixa etária:** {plano.faixa_etaria} · **Nível:** {plano.nivel} · **Instrumento/área:** {plano.instrumento} · **Duração:** {plano.duracao_min} min")
    if plano.unidade:
        L.append(f"**Unidade:** {plano.unidade}")
    L.append("")
    L.append(f"## Objetivo geral\n{plano.objetivo_geral}")
    L.append("## Objetivos específicos\n" + "\n".join(f"- {o}" for o in plano.objetivos_especificos))
    if plano.conhecimentos_previos:
        L.append("## Conhecimentos prévios\n" + "\n".join(f"- {c}" for c in plano.conhecimentos_previos))
    L.append("## Conteúdos\n" + "\n".join(f"- {c}" for c in plano.conteudos))
    L.append("## Competências\n" + ", ".join(plano.competencias))
    if plano.habilidades_curriculares:
        L.append("## Habilidades curriculares (validadas)\n" + ", ".join(plano.habilidades_curriculares))
    L.append("## Recursos\n" + ", ".join(plano.recursos))
    L.append(f"## Metodologia\n{plano.metodologia}")
    L.append("## Cronograma\n" + "\n".join(f"- {b.inicio_min:02d}–{b.fim_min:02d} min · {b.titulo}" for b in plano.cronograma))
    L.append("## Atividades")
    for a in plano.atividades:
        rec = f" _(recursos: {', '.join(a.recursos)})_" if a.recursos else ""
        L.append(f"- **{a.titulo}** ({a.duracao_min} min){rec}: {a.descricao}")
    L.append("## Intervenções do professor\n" + "\n".join(f"- {i}" for i in plano.intervencoes_professor))
    L.append("## Possíveis dificuldades\n" + "\n".join(f"- {d}" for d in plano.possiveis_dificuldades))
    L.append(f"## Adaptações\n{plano.adaptacoes}")
    L.append(f"## Avaliação\n{plano.avaliacao}")
    if plano.criterios:
        L.append("## Critérios\n" + ", ".join(grading.rotulo(c, rubricas) for c in plano.criterios))
    L.append(f"## Continuidade\n{plano.continuidade}")
    L.append("## Referências")
    if plano.referencias:
        for f in plano.referencias:
            marca = {"biblioteca": "📚", "curricular": "🏛", "academica": "🎓", "externa": "🌐"}.get(f.tipo, "")
            partes = [f.titulo]
            if f.autor:
                partes.append(f.autor)
            if f.ano:
                partes.append(str(f.ano))
            if f.pagina:
                partes.append(f"p. {f.pagina}")
            if f.doi:
                partes.append(f"DOI {f.doi}")
            elif f.url:
                partes.append(f.url)
            L.append(f"- {marca} " + " · ".join(partes))
    else:
        L.append("_Nenhuma referência solicitada para este plano._")
    L.append("## Justificativa pedagógica")
    L.append(f"**Por que esta aula foi estruturada assim?** {plano.justificativa_pedagogica.estrutura}")
    L.append(f"**Por que este exercício é adequado ao instrumento e ao estágio?** {plano.justificativa_pedagogica.adequacao}")
    if plano.proximo_passo_sugerido.conteudo:
        L.append(f"\n**Próximo passo sugerido:** {plano.proximo_passo_sugerido.conteudo} — {plano.proximo_passo_sugerido.justificativa}")
    if plano.avisos:
        L.append("\n" + "\n".join(f"> ⚠ {a}" for a in plano.avisos))
    return "\n\n".join(L)


def aula_a_partir_do_plano(plano: Plano, estado: EstadoAtual) -> Dict[str, Any]:
    """Pré-preenche o formulário de registro de aula a partir de um plano."""
    return {
        "data": plano.data,
        "tipo_aula": plano.tipo_aula if plano.tipo_aula != "retroativa" else "continuidade",
        "conteudo_planejado": list(plano.conteudos),
        "objetivos": list(plano.objetivos_especificos),
        "atividades": [a.titulo for a in plano.atividades if a.bloco != "alternativa"],
        "materiais": list(plano.recursos),
        "cronograma": [b.model_dump() for b in plano.cronograma],
        "classificacao": state_mod.classificacao_pre_preenchida(estado, plano.conteudos),
        "habilidades_curriculares": list(plano.habilidades_curriculares),
        "fontes_utilizadas": [f.model_dump() for f in plano.referencias],
        "duracao_prevista_min": plano.duracao_min,
        "plano_origem": f"planos/{plano.nome_arquivo()}",
        "unidade": plano.unidade,
    }
