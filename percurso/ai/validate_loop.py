"""Ciclo de geração → validação → reenvio com erro → fallback (SPEC §7.5).

Gemini gera → pydantic valida → cronograma somado → habilidades verificadas → fontes verificadas
→ instrumento coerente → apresentar. Máximo de 3 tentativas; nunca aceita resposta malformada; nunca loop.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Type

from pydantic import BaseModel, ValidationError

from .. import config
from ..ui import texts as T
from ..utils.logging import obter

log = obter("validacao")


class FalhaValidacao(Exception):
    """Erro específico devolvido ao modelo no reenvio."""


@dataclass
class ResultadoCiclo:
    ok: bool
    dados: Optional[Dict[str, Any]] = None
    tentativas: int = 0
    erros: List[str] = field(default_factory=list)
    mensagens: List[str] = field(default_factory=list)  # mensagens para o professor


def executar(
    gerar: Callable[[str], Dict[str, Any]],
    montar_prompt: Callable[[str], str],
    schema: Type[BaseModel],
    validadores: List[Callable[[BaseModel], None]],
    max_tentativas: Optional[int] = None,
) -> ResultadoCiclo:
    """`gerar(prompt)` chama o modelo; `montar_prompt(erro_anterior)` reconstrói o prompt com o erro."""
    limite = int(max_tentativas or config.gemini().get("max_tentativas_validacao", 3))
    r = ResultadoCiclo(ok=False)
    erro_anterior = ""
    for tentativa in range(1, limite + 1):
        r.tentativas = tentativa
        prompt = montar_prompt(erro_anterior)
        try:
            bruto = gerar(prompt)
        except Exception as e:  # noqa: BLE001 — rede/API: não adianta reenviar o mesmo prompt
            log.warning("Gemini falhou na tentativa %d: %s", tentativa, e.__class__.__name__)
            r.erros.append(f"falha de rede/API: {e.__class__.__name__}")
            r.mensagens.append(T.GEMINI_SEM_RESPOSTA)
            return r
        try:
            obj = schema.model_validate(bruto)
            for v in validadores:
                v(obj)
        except (ValidationError, FalhaValidacao, ValueError) as e:
            erro_anterior = _formatar_erro(e)
            r.erros.append(erro_anterior)
            log.info("resposta inválida (tentativa %d): %s", tentativa, erro_anterior[:300])
            r.mensagens.append(T.GEMINI_VALIDANDO)
            continue
        r.ok = True
        r.dados = obj.model_dump()
        return r
    r.mensagens.append(T.GEMINI_FALLBACK)
    return r


def _formatar_erro(e: Exception) -> str:
    if isinstance(e, ValidationError):
        partes = []
        for err in e.errors()[:6]:
            loc = ".".join(str(x) for x in err.get("loc", []))
            partes.append(f"{loc}: {err.get('msg')}")
        return "JSON inválido para o schema: " + "; ".join(partes)
    return str(e)


def bloco_erro_para_prompt(erro_anterior: str) -> str:
    if not erro_anterior:
        return ""
    return (
        "## ATENÇÃO — a resposta anterior foi rejeitada pelo validador\n"
        f"Erro: {erro_anterior}\n"
        "Corrija exatamente este problema e devolva o JSON completo novamente."
    )
