"""Fixtures comuns (SPEC §16.1). Tudo roda sem rede; PERCURSO_BASE_PATH aponta para tmp_path."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from percurso.core.models import Agenda, Aula, ConteudoTrabalhado, Registro  # noqa: E402
from percurso.platform.base import definir_plataforma  # noqa: E402
from percurso.platform.local import PlataformaLocal  # noqa: E402
from percurso.storage.repo import Repositorio  # noqa: E402


@pytest.fixture
def base(tmp_path, monkeypatch) -> Path:
    b = tmp_path / "Percurso"
    monkeypatch.setenv("PERCURSO_BASE_PATH", str(b))
    definir_plataforma(PlataformaLocal(b))
    from percurso.domains import limpar_cache

    limpar_cache()
    yield b
    definir_plataforma(None)


@pytest.fixture
def repo(base) -> Repositorio:
    return Repositorio(base)


@pytest.fixture
def sessao(base):
    import percurso

    return percurso.preparar(plataforma=PlataformaLocal(base), informar=lambda m: None)


def registro_piano(repo: Repositorio, identificacao: str = "João") -> Registro:
    return repo.criar_registro(
        Registro(
            codigo="",
            identificacao=identificacao,
            idade=10,
            instrumento="piano",
            nivel="iniciante",
            agenda=Agenda(dia_habitual="terca", inicio="15:00", termino="15:50", duracao_min=50),
            recursos_habituais=["instrumentos", "quadro"],
            metodologias=["orff"],
        )
    )


def aula(data: str, conteudos=None, frequencia="presente", dificuldades=None, rendimento=None, proximo="", obs="", **kw) -> Aula:
    cls = [ConteudoTrabalhado(conteudo=c, situacao=s) for c, s in (conteudos or [])]
    return Aula(
        id="",
        data=data,
        frequencia=frequencia,
        duracao_prevista_min=50,
        duracao_real_min=50 if frequencia in ("presente", "reposicao", "aula_extra") else 0,
        classificacao_conteudos=cls,
        conteudo_realizado=[c for c, _ in (conteudos or [])],
        dificuldades=dificuldades or [],
        rendimento=rendimento or {},
        proximo_passo=proximo,
        observacoes=obs,
        **kw,
    )


@pytest.fixture
def registro_com_14_aulas(repo):
    """Registro de exemplo com 14 aulas (SPEC §16.1)."""
    from percurso.core import state

    reg = registro_piano(repo)
    prog = [
        "Corpo: pulso com palmas, passos e balanço",
        "Nota única: tecla repetida no pulso",
        "Cinco dedos: posição fixa tocada no pulso",
        "Alternância de mãos mantendo o pulso",
        "Pequena estrutura: frase de 4 compassos no pulso",
    ]
    datas = [f"2026-{m:02d}-{d:02d}" for m, d in [(5, 5), (5, 12), (5, 19), (5, 26), (6, 2), (6, 9), (6, 16), (6, 23), (6, 30), (7, 7), (7, 14), (7, 21), (7, 28), (8, 4)]]
    for i, d in enumerate(datas):
        idx = min(i // 3, len(prog) - 1)
        atual = prog[idx]
        anterior = prog[idx - 1] if idx > 0 else None
        cls = [(atual, "em_desenvolvimento" if i % 3 != 2 else "consolidado")]
        if anterior:
            cls.append((anterior, "consolidado"))
        freq = "presente" if i not in (4, 9) else ("falta" if i == 4 else "cancelada_instituicao")
        dif = ["acelera no final das frases"] if i in (6, 7, 10) else []
        rend = {"leitura": 2 + (i // 5), "ritmo": 3 + (i // 7)} if freq == "presente" else {}
        repo.gravar_aula(reg.codigo, aula(d, cls, freq, dif, rend, proximo=prog[min(idx + 1, len(prog) - 1)] if i % 3 == 2 else "", obs="tendência a acelerar no final das frases" if i == 10 else ""))
    state.atualizar_apos_aula(repo, reg.codigo)
    return reg
