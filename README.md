# Percurso

**Plataforma de inteligência pedagógica.** *Cada aula começa de onde a anterior terminou.*

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/magoupdown/Percurso/blob/main/Percurso.ipynb)

O Percurso não é um gerador de planos de aula. É um sistema de **memória pedagógica longitudinal**: cada aula é registrada, o estado do aluno é atualizado, e o planejamento seguinte parte exatamente de onde o anterior terminou. Primeira especialização: Música (22 instrumentos e áreas, de piano a prática de conjunto). Gratuito, sem paywall.

## Requisitos

- Uma conta Google (Colab e Drive). Nada para instalar no computador.
- Opcional: uma chave gratuita do Gemini para o Modo Inteligente.

## Como abrir

1. Clique em **Open in Colab** acima.
2. Execute **▶ Inicializar Percurso** (uma vez por sessão). Se falhar por rede, aguarde e execute de novo.
3. Execute **▶ Abrir Percurso**. O Colab pede permissão para o Drive: aceite. O Percurso usa **apenas** a pasta `Meu Drive/Percurso`.
4. A interface aparece abaixo da célula. Não é preciso editar Python, JSON ou pastas.

## Como conectar o Drive

O popup é do próprio Colab. Depois: "Drive conectado ✓ · Estrutura criada ✓" (ou "Seus dados foram recuperados ✓"). Dados de versões antigas são migrados com backup automático.

## Configurar o Gemini (opcional)

Aba **Ajuda → Configurar o Gemini** ou [docs/TUTORIAL_GEMINI.md](docs/TUTORIAL_GEMINI.md): crie a chave no Google AI Studio, guarde nos **Segredos** do Colab como `GEMINI_API_KEY` com "Acesso do notebook" ligado, clique em **USAR GEMINI**. A chave nunca é gravada; nomes de alunos nunca são enviados.

## Usar sem Gemini

Tudo funciona em **Modo Essencial**: registros, turmas, histórico, frequência, rendimento por rubrica, estado pedagógico, planos por modelos pedagógicos (perfis instrumentais editáveis), cronograma validado, biblioteca com busca BM25, base curricular, pesquisa acadêmica, relatórios com gráficos e exportação PDF/DOCX, QR Code, lembrete de apoio.

## Cadastrar aluno e recuperar por código

**Novo registro** → identificação mínima (primeiro nome ou iniciais), instrumento, nível, agenda → **CRIAR REGISTRO** → código `PCR-XXXXXX` + QR. Em qualquer sessão: **Continuar** → código → **CARREGAR** → painel com última aula, consolidado, em desenvolvimento, última observação e **próximo passo sugerido**.

## Adicionar documentos e pesquisar

**Minha biblioteca** aceita PDF, DOCX, TXT e MD (só no seu Drive). Busca exata + BM25 com sinônimos pedagógicos; busca semântica opcional (Gemini ou local). **Pesquisar** consulta 📚 biblioteca, 🏛 BNCC/CRMG e 🎓 OpenAlex/Crossref/Google Books, com origem marcada e cache.

## Gerar aula, frequência e relatório

**Planejar aula** → "O que devo trabalhar agora?" → **GERAR PLANO** (objetivos, cronograma exato, atividades do perfil, avaliação, continuidade, justificativa; com "onde pesquisar" anexa referências verificáveis e habilidades BNCC validadas) → **REGISTRAR AULA A PARTIR DESTE PLANO**. Em **Registrar aula**: frequência (nunca inferida), classificação consolidado/em desenvolvimento/dificuldade, notas 1–5 só no observado. **Relatórios**: frequência, rendimento, pedagógico, completo, institucional, para responsáveis; por período; gráficos; PDF/DOCX/MD/CSV; materiais (folhas, rubrica, ficha, repertório, MIDI/MusicXML).

## Apoiar

**♡ Apoiar o Percurso**: QR Code do Mercado Pago. Lembrete uma vez por mês, na primeira abertura do mês. Nenhuma função é bloqueada.

## Privacidade

Código opera só em `Meu Drive/Percurso/`. Identificação mínima de alunos. **Configurações → Privacidade**: exportar zip, excluir registro (backup 30 dias), excluir biblioteca, apagar dados locais. Pseudonimização em todo prompt; trechos da biblioteca só com consentimento.

## Solução de problemas

[docs/TUTORIAL_PROFESSOR.md](docs/TUTORIAL_PROFESSOR.md) → "Solução de problemas"; botão **DIAGNÓSTICO** em Configurações.

## Para desenvolvedores

```bash
pip install -e ".[dev]"
pytest
```

Docs: [ARCHITECTURE](docs/ARCHITECTURE.md) · [DATA_MODEL](docs/DATA_MODEL.md) · [TESTING](docs/TESTING.md) · [ROADMAP](docs/ROADMAP.md) · [RELATORIO_ENTREGA](docs/RELATORIO_ENTREGA.md) · [SPEC](SPEC.md).

## Estado das entregas

| Entrega | Escopo | Estado |
|---|---|---|
| E1 | Núcleo (Modo Essencial) | concluída |
| E2 | Modo Inteligente (Gemini) | concluída (testada com mock) |
| E3 | Biblioteca | concluída |
| E4 | Currículo e pesquisa acadêmica | concluída (APIs testadas com respostas gravadas) |
| E5 | Relatórios, exportação e fechamento | concluída |

`pytest`: 103 testes verdes em 08/09/2026 (+1 teste `online` com OpenAlex e Crossref reais).

**Último teste no Colab:** 08/09/2026 (Python 3.13.15, Gradio 6.26.0) — abertura pelo badge, inicialização, conexão do Drive, interface inline estilizada e navegação entre abas verificadas. Versões fixadas em `requirements.txt` a partir desse teste. Pendências do proprietário (SPEC §21): link do Mercado Pago em `config/defaults.json` e e-mail para o OpenAlex (opcional).
