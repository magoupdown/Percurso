"""Plataforma Google Colab. Único módulo que importa google.colab (SPEC D9)."""
from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Optional

from .base import Plataforma

PONTO_MONTAGEM = "/content/drive"
PASTA_PERCURSO = "/content/drive/MyDrive/Percurso"


class PlataformaColab(Plataforma):
    nome = "colab"

    def eh_colab(self) -> bool:
        return True

    def montar_armazenamento(self) -> Path:
        from google.colab import drive  # type: ignore

        if not os.path.isdir(os.path.join(PONTO_MONTAGEM, "MyDrive")):
            drive.mount(PONTO_MONTAGEM)
        base = Path(PASTA_PERCURSO)
        base.mkdir(parents=True, exist_ok=True)
        return base

    def obter_segredo(self, nome: str) -> Optional[str]:
        try:
            from google.colab import userdata  # type: ignore

            valor = userdata.get(nome)
            return valor if valor else None
        except Exception:
            # SecretNotFoundError, NotebookAccessError ou ambiente sem userdata
            return None

    def caminho_log_runtime(self) -> Path:
        return Path("/content/percurso.log")

    def limpar_dados_locais(self) -> list:
        removidos = []
        for alvo in ["/content/percurso.log", "/content/percurso_tmp"]:
            try:
                if os.path.isdir(alvo):
                    shutil.rmtree(alvo, ignore_errors=True)
                    removidos.append(alvo)
                elif os.path.isfile(alvo):
                    os.remove(alvo)
                    removidos.append(alvo)
            except OSError:
                pass
        return removidos
