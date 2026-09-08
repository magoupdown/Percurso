"""Cronograma de aula (SPEC §8.2).

Blocos contíguos: inicio_min do primeiro = 0; fim_min de cada = inicio_min do seguinte;
fim_min do último = duração. Nenhum plano é apresentado sem passar por `validar_cronograma`.
"""
from __future__ import annotations

from typing import List, Optional, Sequence

from .models import BlocoCronograma

# Estrutura pedagógica canônica e mínimos por bloco (minutos).
ETAPAS = ["acolhimento", "introducao", "exploracao", "pratica", "aplicacao", "avaliacao", "fechamento"]
MINIMOS = {
    "acolhimento": 2,
    "introducao": 3,
    "exploracao": 4,
    "pratica": 5,
    "aplicacao": 3,
    "avaliacao": 2,
    "fechamento": 2,
}
MINIMO_GENERICO = 2
BLOCO_RESIDUO = "pratica"


class ErroCronograma(ValueError):
    pass


def validar_cronograma(blocos: Sequence[BlocoCronograma], duracao: int) -> Optional[str]:
    """Devolve None se válido; senão, mensagem específica do erro (em PT-BR)."""
    if duracao <= 0:
        return f"duração inválida: {duracao}"
    if not blocos:
        return "cronograma vazio"
    if blocos[0].inicio_min != 0:
        return f"o primeiro bloco começa em {blocos[0].inicio_min}, esperado 0"
    for i, b in enumerate(blocos):
        if b.fim_min <= b.inicio_min:
            return f"bloco '{b.titulo}' termina em {b.fim_min}, antes ou igual ao início {b.inicio_min}"
        if i > 0 and b.inicio_min != blocos[i - 1].fim_min:
            return (
                f"bloco '{b.titulo}' começa em {b.inicio_min}, "
                f"mas o anterior termina em {blocos[i - 1].fim_min}"
            )
    soma = sum(b.fim_min - b.inicio_min for b in blocos)
    if soma != duracao:
        return f"soma {soma}, esperado {duracao}"
    if blocos[-1].fim_min != duracao:
        return f"o último bloco termina em {blocos[-1].fim_min}, esperado {duracao}"
    return None


def exigir_valido(blocos: Sequence[BlocoCronograma], duracao: int) -> None:
    erro = validar_cronograma(blocos, duracao)
    if erro:
        raise ErroCronograma(erro)


def _minimo(bloco: BlocoCronograma) -> int:
    return MINIMOS.get(bloco.etapa or "", MINIMO_GENERICO)


def adaptar_duracao(blocos: Sequence[BlocoCronograma], nova_duracao: int) -> List[BlocoCronograma]:
    """Redistribui proporcionalmente preservando a estrutura e os mínimos por bloco.

    Resíduo de arredondamento vai ao bloco de prática (ou ao maior bloco, se não houver prática).
    Nunca corta a última atividade. Se a nova duração for menor que a soma dos mínimos,
    reduz proporcionalmente os mínimos, mantendo ao menos 1 minuto por bloco.
    """
    if nova_duracao <= 0:
        raise ErroCronograma(f"duração inválida: {nova_duracao}")
    if not blocos:
        raise ErroCronograma("cronograma vazio")
    n = len(blocos)
    if nova_duracao < n:
        raise ErroCronograma(f"duração {nova_duracao} menor que o número de blocos ({n})")

    atual = sum(b.fim_min - b.inicio_min for b in blocos)
    if atual <= 0:
        raise ErroCronograma("cronograma com duração zero")

    minimos = [_minimo(b) for b in blocos]
    if sum(minimos) > nova_duracao:
        # escala os mínimos, garantindo 1 min por bloco
        fator = nova_duracao / sum(minimos)
        minimos = [max(1, int(m * fator)) for m in minimos]
        while sum(minimos) > nova_duracao:
            i = max(range(n), key=lambda k: minimos[k])
            minimos[i] -= 1

    brutos = [(b.fim_min - b.inicio_min) * nova_duracao / atual for b in blocos]
    novos = [max(minimos[i], int(round(brutos[i]))) for i in range(n)]

    # índice do bloco que absorve o resíduo
    idx_residuo = next((i for i, b in enumerate(blocos) if (b.etapa or "") == BLOCO_RESIDUO), None)
    if idx_residuo is None:
        idx_residuo = max(range(n), key=lambda k: brutos[k])

    residuo = nova_duracao - sum(novos)
    if residuo > 0:
        novos[idx_residuo] += residuo
    elif residuo < 0:
        # remover minutos: primeiro do bloco de resíduo, depois dos maiores, respeitando mínimos
        faltam = -residuo
        ordem = [idx_residuo] + sorted(
            (i for i in range(n) if i != idx_residuo), key=lambda k: -novos[k]
        )
        while faltam > 0:
            reduziu = False
            for i in ordem:
                if faltam == 0:
                    break
                if novos[i] > minimos[i]:
                    novos[i] -= 1
                    faltam -= 1
                    reduziu = True
            if not reduziu:
                # mínimos já reduzidos acima garantem que isso não ocorre; proteção contra loop
                raise ErroCronograma("não foi possível redistribuir a duração")

    saida: List[BlocoCronograma] = []
    cursor = 0
    for b, d in zip(blocos, novos):
        saida.append(
            BlocoCronograma(
                inicio_min=cursor, fim_min=cursor + d, titulo=b.titulo, descricao=b.descricao, etapa=b.etapa
            )
        )
        cursor += d
    exigir_valido(saida, nova_duracao)
    return saida


def montar_de_template(template: Sequence[dict], duracao: int) -> List[BlocoCronograma]:
    """Constrói blocos a partir de um template [{etapa, titulo, minutos, descricao}] e ajusta à duração."""
    blocos: List[BlocoCronograma] = []
    cursor = 0
    for item in template:
        minutos = int(item.get("minutos", 5))
        blocos.append(
            BlocoCronograma(
                inicio_min=cursor,
                fim_min=cursor + minutos,
                titulo=item.get("titulo", item.get("etapa", "Bloco")),
                descricao=item.get("descricao", ""),
                etapa=item.get("etapa", ""),
            )
        )
        cursor += minutos
    if cursor != duracao:
        blocos = adaptar_duracao(blocos, duracao)
    exigir_valido(blocos, duracao)
    return blocos


def descrever(blocos: Sequence[BlocoCronograma]) -> str:
    linhas = []
    for b in blocos:
        linhas.append(f"{b.inicio_min:02d}–{b.fim_min:02d} min · {b.titulo}" + (f" — {b.descricao}" if b.descricao else ""))
    return "\n".join(linhas)
