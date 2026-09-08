"""Rendimento com rubrica (SPEC §5.3, §12.3). Somente dados registrados; IA nunca preenche."""
from __future__ import annotations

from typing import Dict, List, Optional, Sequence

from .models import Aula, Registro, Rubricas

ROTULOS = {
    "leitura": "Leitura",
    "ritmo": "Ritmo",
    "tecnica": "Técnica",
    "coordenacao": "Coordenação",
    "percepcao": "Percepção",
    "autonomia": "Autonomia",
    "sonoridade": "Sonoridade",
    "afinacao": "Afinação",
    "respiracao": "Respiração",
    "articulacao": "Articulação",
    "postura": "Postura",
    "participacao": "Participação",
    "expressividade": "Expressividade",
    "memoria": "Memória",
    "criatividade": "Criatividade",
    "cooperacao": "Cooperação",
    "escuta": "Escuta",
    "pulso": "Pulso",
    "dinamica": "Dinâmica",
    "improvisacao": "Improvisação",
    "fraseado": "Fraseado",
    "conjunto": "Conjunto",
    "independencia": "Independência",
    "notacao": "Notação",
    "analise": "Análise",
    "ditado": "Ditado",
    "solfejo": "Solfejo",
    "harmonia": "Harmonia",
    "movimento": "Movimento",
    "vocabulario": "Vocabulário",
    "teoria": "Teoria",
    "criterio_proprio": "Critério próprio",
}
ESCALA_PADRAO = 5


def rotulo(id_criterio: str, rubricas: Optional[Rubricas] = None) -> str:
    if rubricas and id_criterio in rubricas.criterios_proprios:
        return rubricas.criterios_proprios[id_criterio]
    return ROTULOS.get(id_criterio, id_criterio.replace("_", " ").capitalize())


def criterios_ativos(registro: Registro, padrao_do_perfil: Sequence[str], rubricas: Optional[Rubricas] = None) -> List[str]:
    """Critérios do registro (se definidos) ou do perfil; mais os próprios do professor."""
    if not registro.rubrica_ativa:
        return []
    base = list(registro.rubrica) if registro.rubrica else list(padrao_do_perfil)
    if rubricas:
        for cid in rubricas.criterios_proprios:
            if cid not in base and (not registro.rubrica or cid in registro.rubrica):
                base.append(cid)
    return base


def validar_rendimento(rendimento: Dict[str, int], escala_max: int = ESCALA_PADRAO) -> Dict[str, int]:
    """Mantém só notas informadas dentro da escala. Nunca inventa valor."""
    saida: Dict[str, int] = {}
    for k, v in (rendimento or {}).items():
        if v is None or v == "":
            continue
        try:
            n = int(v)
        except (TypeError, ValueError):
            continue
        if 1 <= n <= escala_max:
            saida[k] = n
    return saida


def evolucao(aulas: Sequence[Aula]) -> Dict[str, List[tuple]]:
    """{criterio: [(data, nota), ...]} apenas com notas registradas, em ordem cronológica."""
    saida: Dict[str, List[tuple]] = {}
    for a in sorted(aulas, key=lambda x: x.data):
        if a.cancelada:
            continue
        for crit, nota in a.rendimento.items():
            saida.setdefault(crit, []).append((a.data, nota))
    return saida


def recentes(aulas: Sequence[Aula], n: int = 3) -> Dict[str, List[int]]:
    """Últimas n notas por critério (para estado_atual.rendimento_recente)."""
    ev = evolucao(aulas)
    return {c: [nota for _, nota in v[-n:]] for c, v in ev.items()}


def medias(aulas: Sequence[Aula]) -> Dict[str, float]:
    ev = evolucao(aulas)
    return {c: round(sum(nota for _, nota in v) / len(v), 2) for c, v in ev.items() if v}


def tendencia(notas: Sequence[int]) -> str:
    """'subindo' | 'estavel' | 'caindo' | 'sem_dados' — comparação simples das últimas notas."""
    if len(notas) < 2:
        return "sem_dados"
    if notas[-1] > notas[0]:
        return "subindo"
    if notas[-1] < notas[0]:
        return "caindo"
    return "estavel"
