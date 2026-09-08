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
        body_text_color="#0f172a",
    )


CSS = """
.percurso-titulo { font-size: 2rem; font-weight: 800; letter-spacing: -0.02em; margin: 0; color: #0f172a; }
.percurso-subtitulo { font-size: 1.05rem; color: #334155; margin: 0 0 0.25rem 0; }
.percurso-frase { font-size: 0.95rem; color: #64748b; font-style: italic; margin: 0 0 0.75rem 0; }
.percurso-modo { display: inline-block; padding: 0.25rem 0.75rem; border-radius: 999px; font-weight: 600; font-size: 0.9rem; }
.percurso-modo-essencial { background: #e2e8f0; color: #0f172a; }
.percurso-modo-gemini { background: #ccfbf1; color: #134e4a; }
.percurso-painel { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 1rem 1.25rem; }
.percurso-apoio button { background: transparent !important; color: #b45309 !important; border: 1px solid #fcd34d !important; box-shadow: none !important; }
.percurso-aviso { background: #fffbeb; border-left: 4px solid #f59e0b; padding: 0.5rem 0.75rem; border-radius: 6px; }
.percurso-ok { background: #ecfdf5; border-left: 4px solid #10b981; padding: 0.5rem 0.75rem; border-radius: 6px; }
.percurso-erro { background: #fef2f2; border-left: 4px solid #ef4444; padding: 0.5rem 0.75rem; border-radius: 6px; }
footer { display: none !important; }
@media (max-width: 720px) { .percurso-titulo { font-size: 1.5rem; } }
"""
