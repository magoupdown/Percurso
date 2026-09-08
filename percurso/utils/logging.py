"""Logging técnico do Percurso.

Regras (SPEC §14.4, §15):
- Nunca gravar chaves de API. Um filtro remove padrões que se pareçam com chaves.
- Arquivo de runtime em /content/percurso.log (Colab) ou <base>/percurso.log (local).
- Arquivo de diagnóstico opcional em <base_path>/configuracoes/diagnostico.log, rotativo (<= 1 MB).
"""
from __future__ import annotations

import logging
import os
import re
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

_PADROES_SEGREDO = [
    re.compile(r"AIza[0-9A-Za-z_\-]{20,}"),  # chaves Google
    re.compile(r"(?i)(api[_\- ]?key|token|secret|senha|password)\s*[:=]\s*\S+"),
    re.compile(r"sk-[0-9A-Za-z]{16,}"),
]


class FiltroSegredos(logging.Filter):
    """Substitui qualquer coisa que se pareça com chave/segredo por [REDIGIDO]."""

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003
        try:
            msg = record.getMessage()
        except Exception:  # pragma: no cover
            return True
        novo = redigir(msg)
        if novo != msg:
            record.msg = novo
            record.args = ()
        return True


def redigir(texto: str) -> str:
    for padrao in _PADROES_SEGREDO:
        texto = padrao.sub("[REDIGIDO]", texto)
    return texto


_LOGGER_NOME = "percurso"
_configurado = False


def configurar(arquivo_runtime: Optional[Path] = None, arquivo_diagnostico: Optional[Path] = None) -> logging.Logger:
    """Configura o logger. Pode ser chamado novamente para acrescentar o arquivo de diagnóstico."""
    global _configurado
    logger = logging.getLogger(_LOGGER_NOME)
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    filtro = FiltroSegredos()

    if not _configurado:
        logger.propagate = False
        _configurado = True

    existentes = {getattr(h, "_percurso_alvo", None) for h in logger.handlers}

    if arquivo_runtime is not None and str(arquivo_runtime) not in existentes:
        try:
            arquivo_runtime.parent.mkdir(parents=True, exist_ok=True)
            h = logging.FileHandler(arquivo_runtime, encoding="utf-8")
            h.setFormatter(fmt)
            h.addFilter(filtro)
            h._percurso_alvo = str(arquivo_runtime)  # type: ignore[attr-defined]
            logger.addHandler(h)
        except OSError:  # pragma: no cover
            pass

    if arquivo_diagnostico is not None and str(arquivo_diagnostico) not in existentes:
        try:
            arquivo_diagnostico.parent.mkdir(parents=True, exist_ok=True)
            h = RotatingFileHandler(arquivo_diagnostico, maxBytes=1_000_000, backupCount=1, encoding="utf-8")
            h.setFormatter(fmt)
            h.addFilter(filtro)
            h._percurso_alvo = str(arquivo_diagnostico)  # type: ignore[attr-defined]
            logger.addHandler(h)
        except OSError:  # pragma: no cover
            pass
    return logger


def obter(nome: str = "") -> logging.Logger:
    return logging.getLogger(_LOGGER_NOME if not nome else f"{_LOGGER_NOME}.{nome}")


def ultimas_linhas(arquivo: Path, n: int = 60) -> str:
    """Últimas linhas do log para o botão DIAGNÓSTICO. Sempre redigidas."""
    try:
        if not arquivo.exists():
            return "Nenhum registro de diagnóstico ainda."
        linhas = arquivo.read_text(encoding="utf-8", errors="replace").splitlines()
        return redigir("\n".join(linhas[-n:]))
    except OSError:
        return "Não foi possível ler o arquivo de diagnóstico."


def caminho_runtime_padrao() -> Path:
    if os.path.isdir("/content"):
        return Path("/content/percurso.log")
    return Path(os.environ.get("PERCURSO_LOG", "percurso.log"))
