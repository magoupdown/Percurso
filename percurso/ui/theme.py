"""Tema visual do Percurso (SPEC §1.1, §6.1): limpo, educacional, acolhedor, sem logotipo (tipografia)."""
from __future__ import annotations


def tema():
    import gradio as gr

    return gr.themes.Soft(
        primary_hue=gr.themes.colors.teal,
        secondary_hue=gr.themes.colors.amber,
        neutral_hue=gr.themes.colors.slate,
        font=[gr.themes.GoogleFont("Nunito"), "Segoe UI", "Arial", "sans-serif"],
        font_mono=["Consolas", "monospace"],
        radius_size=gr.themes.sizes.radius_md,
        text_size=gr.themes.sizes.text_md,
    ).set(
        button_primary_background_fill="#0f766e",
        button_primary_background_fill_hover="#115e59",
        button_primary_text_color="#ffffff",
        button_secondary_background_fill="#f1f5f9",
        button_secondary_text_color="#0f172a",
        block_title_text_weight="600",
    )


CSS = """
.percurso-titulo { font-size: 2rem; font-weight: 800; letter-spacing: -0.02em; margin: 0; color: var(--body-text-color); }
.percurso-subtitulo { font-size: 1.05rem; color: var(--body-text-color); opacity: 0.85; margin: 0 0 0.25rem 0; }
.percurso-frase { font-size: 0.95rem; color: var(--body-text-color-subdued); font-style: italic; margin: 0 0 0.75rem 0; }
.percurso-modo { display: inline-block; padding: 0.25rem 0.75rem; border-radius: 999px; font-weight: 600; font-size: 0.9rem; border: 1px solid var(--border-color-primary); }
.percurso-modo-essencial { background: var(--background-fill-secondary); color: var(--body-text-color); }
.percurso-modo-gemini { background: #ccfbf1; color: #134e4a; }
.percurso-painel { background: var(--background-fill-secondary); border: 1px solid var(--border-color-primary); border-radius: 10px; padding: 1rem 1.25rem; color: var(--body-text-color); }
.percurso-apoio button { background: transparent !important; color: #d97706 !important; border: 1px solid #fcd34d !important; box-shadow: none !important; }
.percurso-aviso { background: rgba(245, 158, 11, 0.12); border-left: 4px solid #f59e0b; padding: 0.5rem 0.75rem; border-radius: 6px; color: var(--body-text-color); }
.percurso-ok { background: rgba(16, 185, 129, 0.12); border-left: 4px solid #10b981; padding: 0.5rem 0.75rem; border-radius: 6px; color: var(--body-text-color); }
.percurso-erro { background: rgba(239, 68, 68, 0.12); border-left: 4px solid #ef4444; padding: 0.5rem 0.75rem; border-radius: 6px; color: var(--body-text-color); }
footer { display: none !important; }
@media (max-width: 720px) { .percurso-titulo { font-size: 1.5rem; } }
"""
