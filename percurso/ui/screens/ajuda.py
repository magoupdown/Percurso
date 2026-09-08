"""Aba Ajuda: renderiza docs/TUTORIAL_PROFESSOR.md e docs/TUTORIAL_GEMINI.md (SPEC §7.4, §19.1)."""
from __future__ import annotations

from pathlib import Path

import gradio as gr

from ... import config
from .. import texts as T
from ..session import Sessao


def ler_doc(nome: str) -> str:
    caminho = config.RAIZ / "docs" / nome
    try:
        return caminho.read_text(encoding="utf-8")
    except OSError:
        return f"_O arquivo {nome} não foi encontrado nesta instalação._"


def montar(sessao: Sessao) -> dict:
    with gr.Tab(T.ABA_AJUDA, id="ajuda") as tab:
        with gr.Tabs():
            with gr.Tab("Como usar o Percurso"):
                gr.Markdown(ler_doc("TUTORIAL_PROFESSOR.md"))
            with gr.Tab("Configurar o Gemini") as tab_gemini:
                gr.Markdown(ler_doc("TUTORIAL_GEMINI.md"))
    return {"tab": tab, "tab_gemini": tab_gemini}
