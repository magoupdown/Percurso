"""Escrita atômica de JSON (SPEC §4.4).

arquivo.json.tmp → validar (parse + validador opcional) → os.replace → manter arquivo.json.bak (1 cópia).
"""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any, Callable, Optional


class ErroEscrita(Exception):
    pass


def _serializar(dados: Any) -> str:
    return json.dumps(dados, ensure_ascii=False, indent=2, sort_keys=False, default=str)


def escrever_json(caminho: Path, dados: Any, validador: Optional[Callable[[Any], None]] = None) -> None:
    """Grava `dados` em `caminho` de forma atômica.

    `validador(obj)` recebe o objeto relido do .tmp e deve levantar exceção se inválido
    (ex.: `Modelo.model_validate`). Em caso de falha, o .tmp é removido e o original permanece.
    """
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    tmp = caminho.with_name(caminho.name + ".tmp")
    bak = caminho.with_name(caminho.name + ".bak")
    try:
        texto = _serializar(dados)
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            f.write(texto)
            f.flush()
            os.fsync(f.fileno())
        with open(tmp, "r", encoding="utf-8") as f:
            relido = json.load(f)
        if validador is not None:
            validador(relido)
        if caminho.exists():
            try:
                shutil.copy2(caminho, bak)
            except OSError:
                pass
        os.replace(tmp, caminho)
    except Exception as e:
        try:
            if tmp.exists():
                tmp.unlink()
        except OSError:
            pass
        raise ErroEscrita(f"Falha ao gravar {caminho.name}: {e}") from e


def ler_json(caminho: Path, padrao: Any = None) -> Any:
    """Lê JSON; se ausente devolve `padrao`. Se corrompido, tenta o .bak antes de falhar."""
    caminho = Path(caminho)
    if not caminho.exists():
        return padrao
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        bak = caminho.with_name(caminho.name + ".bak")
        if bak.exists():
            with open(bak, "r", encoding="utf-8") as f:
                return json.load(f)
        raise


def copiar_pasta_backup(origem: Path, pasta_backups: Path, carimbo: str, motivo: str) -> Path:
    """Cópia da pasta afetada em backups/<timestamp>_<motivo>/ (SPEC §4.4)."""
    destino = pasta_backups / f"{carimbo}_{motivo}" / origem.name
    destino.parent.mkdir(parents=True, exist_ok=True)
    if destino.exists():
        shutil.rmtree(destino)
    shutil.copytree(origem, destino, ignore=shutil.ignore_patterns("*.tmp"))
    return destino.parent
