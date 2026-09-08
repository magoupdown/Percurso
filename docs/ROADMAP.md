# Roadmap pós-V1 (SPEC §17.1) — registrado, não implementado

- Imagem de partitura via `verovio` (SVG sem binário externo)
- OCR como fallback para PDFs digitalizados
- Formatos EPUB, XLSX, CSV, PPTX na biblioteca
- Pesquisa web configurável (`WebSearchProvider` já tem interface definida)
- SQLite como cache reconstruível (nunca fonte de verdade)
- Documento curricular próprio do professor (pasta `curriculo/`)
- Frequência individual avançada em turma
- Aplicação web, login, banco remoto, múltiplos dispositivos
- Painel institucional
- Google Calendar / Google Classroom
- NotebookLM (somente se houver API oficial)
- Outros componentes curriculares: Matemática, Português, Ciências, História, Geografia, Educação Infantil (`domains/*`)
- Versão para escolas · app móvel · assinatura · Mercado Pago automatizado · dashboards · acompanhamento de responsáveis
- `sentence-transformers` local já é opt-in; `faiss-cpu` só se o volume justificar

## Não fazer agora (SPEC §17.2)

Servidor obrigatório, SaaS, login central, banco central, paywall, cobrança, app Android/iOS, infraestrutura além de GitHub + Colab + Drive.
