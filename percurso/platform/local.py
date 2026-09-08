"""Plataforma local: desenvolvimento e testes. base_path vem de PERCURSO_BASE_PATH."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from .base import Plataforma


class PlataformaLocal(Plataforma):
    nome = "local"

    def __init__(self, base_path: Optional[Path] = None):
        self._base = Path(base_path) if base_path else None

    def montar_armazenamento(self) -> Path:
        if self._base is None:
            env = os.environ.get("PERCURSO_BASE_PATH")
            self._base = Path(env) if env else Path.cwd() / "dados_locais" / "Percurso"
        self._base.mkdir(parents=True, exist_ok=True)
        return self._base

    def obter_segredo(self, nome: str) -> Optional[str]:
        valor = os.environ.get(nome)
        return valor if valor else None

    def caminho_log_runtime(self) -> Path:
        base = self._base or Path.cwd()
        return base / "percurso.log"

    def limpar_dados_locais(self) -> list:
        return []
