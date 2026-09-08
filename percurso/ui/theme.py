"""Tema visual do Percurso (SPEC §1.1, §6.1): limpo, educacional, acolhedor, sem logotipo (tipografia)."""
from __future__ import annotations


def tema():
    import gradio as gr

    return gr.themes.Soft(
        primary_hue=gr.themes.colors.teal,
        secondary_hue=gr.themes.colors.amber,
        neutral_hue=gr.themes.colors.slate,
        font=["Segoe UI", "Arial", "sans-serif"],
        font_mono=["Consolas", "monospace"],
        radius_size=gr.themes.sizes.radius_md,
        text_size=gr.themes.sizes.text_md,
    ).set(
        button_primary_background_fill="#146c60",
        button_primary_background_fill_hover="#115e59",
        button_primary_text_color="#ffffff",
        button_secondary_background_fill="#ffffff",
        button_secondary_text_color="#20564d",
        block_title_text_weight="600",
        body_background_fill="#ffffff",
        body_text_color="#203b35",
        background_fill_primary="#ffffff",
        background_fill_secondary="#f7f9f8",
        block_background_fill="#ffffff",
        border_color_primary="#d5e1dd",
        body_text_color_subdued="#526b63",

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


# Escopo restrito ao aplicativo: não altera o notebook hospedeiro.
CSS += """
#percurso-app { max-width: 1440px; margin: 0 auto; padding: 0 32px 24px; }
#percurso-app .tab-nav { gap: 2px; flex-wrap: wrap; border-bottom: 1px solid #d5e1dd; padding: 0 0 4px; }
#percurso-app .tab-nav button { font-size: 14px; padding: 15px 12px; font-weight: 500; border-radius: 0; }
#percurso-app .tab-nav button.selected { color: #146c60; border-bottom: 3px solid #146c60; background: transparent; }
#percurso-app .tabitem { border: none; padding: 24px 0; }
#percurso-app .percurso-identidade { position: relative; padding: 22px 0 20px; gap: 0; text-align: center; }
#percurso-app .percurso-status { position: absolute; right: 0; top: 4px; width: auto; }
#percurso-app .percurso-modo { border: none; background: transparent; padding: 0; color: #146c60; font-size: 13px; font-weight: 500; }
#percurso-app .percurso-titulo { font: 700 clamp(48px, 5.5vw, 82px)/1.05 Georgia, serif; letter-spacing: -4px; margin: 0 0 2px; color: #163c33; }
#percurso-app .percurso-subtitulo { font: 21px/1.5 Georgia, serif; color: #203b35; opacity: 1; }
#percurso-app .percurso-frase { font: italic 20px/1.7 Georgia, serif; margin: 0; color: #405f55; }
#percurso-app .percurso-acoes { background: #f7f9f8; padding: 28px 32px; border-radius: 8px; gap: 22px; }
#percurso-app .percurso-acoes h2 { font: 600 34px/1.2 Georgia, serif; color: #163c33; margin: 0 0 6px; }
#percurso-app .percurso-acoes p { font: 20px/1.5 Georgia, serif; color: #405f55; }
#percurso-app h3 { font: 600 26px/1.3 Georgia, serif; margin: 0; }
#percurso-app button { transition: background-color .15s ease, border-color .15s ease; }
#percurso-app .percurso-acoes-principais button { min-height: 65px; font: 600 21px/1.3 Georgia, serif; border: 1px solid #146c60; }
#percurso-app .percurso-utilidades button { min-height: 57px; font: 20px/1.3 Georgia, serif; background: transparent; }
#percurso-app .percurso-divisor { border-top: 1px solid #d5e1dd; padding-top: 22px; margin-top: 8px; }
#percurso-app .percurso-gemini { background: #eff8f5; padding: 23px 32px; border: none; border-radius: 8px; margin: 6px 0; }
#percurso-app .percurso-gemini p { color: #405f55; }
#percurso-app .percurso-gemini > .form { background: transparent; }
#percurso-app .percurso-gemini button { min-height: 44px; }
#percurso-app .percurso-gemini .row { max-width: 570px; }
#percurso-app .percurso-apoio button { border: none !important; color: #146c60 !important; min-height: 44px; }
#percurso-app .percurso-painel { border-left: 3px solid #146c60; border-radius: 6px; padding: 16px 20px; }
#percurso-app button:focus-visible, #percurso-app input:focus-visible, #percurso-app textarea:focus-visible { outline: 3px solid #238b77; outline-offset: 3px; }
#percurso-app button { min-height: 44px; }
#percurso-app input, #percurso-app textarea { font-size: 16px; }
#percurso-app .prose { overflow-wrap: anywhere; }
#percurso-app .prose table { display: block; max-width: 100%; overflow-x: auto; }
.dark #percurso-app { background: #ffffff; color-scheme: light; --body-text-color: #203b35; --body-text-color-subdued: #526b63; --background-fill-primary: #ffffff; --background-fill-secondary: #f7f9f8; --block-background-fill: #ffffff; --input-background-fill: #ffffff; --input-text-color: #203b35; --block-label-text-color: #405f55; --border-color-primary: #d5e1dd; --button-secondary-background-fill: #ffffff; --button-secondary-text-color: #20564d; }
@media (max-width: 720px) {
 #percurso-app { padding: 0 14px 20px; }
 #percurso-app .tab-nav { gap: 0; }
 #percurso-app .tab-nav button { font-size: 13px; padding: 9px 10px; }
 #percurso-app .percurso-identidade { padding: 24px 0 16px; }
 #percurso-app .percurso-status { position: static; margin-bottom: 12px; }
 #percurso-app .percurso-titulo { letter-spacing: -2px; }
 #percurso-app .percurso-subtitulo { font-size: 17px; }
 #percurso-app .percurso-frase { font-size: 17px; }
 #percurso-app .percurso-acoes, #percurso-app .percurso-gemini { padding: 22px 18px; }
 #percurso-app .percurso-acoes h2 { font-size: 28px; }
 #percurso-app .percurso-acoes p { font-size: 18px; }
 #percurso-app .percurso-acoes-principais, #percurso-app .percurso-utilidades { flex-direction: column; }
 #percurso-app .percurso-acoes-principais button, #percurso-app .percurso-utilidades button { width: 100%; min-width: 0; flex-basis: auto !important; }
}
@media (prefers-reduced-motion: reduce) { #percurso-app * { transition: none !important; animation: none !important; } }
"""
