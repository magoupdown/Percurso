# Relatório de entrega — Percurso V1 (E1–E5)

Formato da SPEC §19.4. Data: 08/09/2026.

## O que foi desenvolvido

- **E1 — Núcleo (Modo Essencial):** notebook fino (2 células), plataforma colab/local, storage com escrita atômica e `.bak`, estrutura do Drive, onboarding e perfil do professor, registros com código `PCR-XXXXXX` (individual, dupla, turma), registrar aula (inclusive retroativa), frequência, rendimento com rubrica (padrão do perfil + critérios próprios), estado atual e resumo determinísticos, histórico com busca estruturada, planejador por modelos pedagógicos com 22 perfis instrumentais editáveis, cronograma validado e adaptável, aula extraordinária/revisão/nova unidade, repertório, apoio (QR + lembrete mensal), LGPD (exportar/excluir/apagar locais), migração v0→v1 com backup, README.
- **E2 — Modo Inteligente:** chave via Colab Secrets ou sessão, tutorial, schemas pydantic, ciclo de validação (3 tentativas + fallback), pseudonimização, consentimento de trechos, plano contextual, resumo narrativo editável, busca livre no histórico, proposta de classificação.
- **E3 — Biblioteca:** PDF/DOCX/TXT/MD, hash e duplicidade, extração (PyMuPDF → pypdf → python-docx), trechos com página, metadados detectados e corrigíveis, catálogo, busca exata + BM25 com sinônimos pedagógicos, índice incremental com manifesto, embeddings Gemini e busca local opt-in, remoção com confirmação, integração ao plano.
- **E4 — Currículo e pesquisa:** BNCC Arte (61 habilidades EF transcritas do documento oficial + 4 EM), BNCC EI (15 objetivos), CRMG (recorte Arte), validação em cadeia, sugestão por tema, provedores OpenAlex/Crossref/Google Books (+ Semantic Scholar opcional), expansão PT/EN, cache com validade, rastreabilidade, tela Pesquisar.
- **E5 — Relatórios e fechamento:** 6 tipos de relatório por período, gráficos matplotlib, PDF/DOCX/MD/CSV, materiais (folhas, exercícios, rubrica, ficha, repertório, MIDI/MusicXML, QR), diagnóstico, docs (ARCHITECTURE, DATA_MODEL, TESTING, TUTORIAL_PROFESSOR, TUTORIAL_GEMINI, ROADMAP), README com badge.

## Como abrir

GitHub → **Open in Colab** (`Percurso.ipynb`) → célula 1 → célula 2. Ou localmente: `pip install -e .` e `python -c "import percurso; percurso.iniciar(inline=False)"`.

## Como testar

`pytest` (103 testes, sem rede; `pytest -m online` exercita OpenAlex e Crossref reais). Roteiro manual em `docs/TESTING.md`.

## Configuração do Drive

Automática: popup do Colab na célula 2; pasta `Meu Drive/Percurso` criada com a estrutura da SPEC §4.1. Mensagem de transparência exibida antes.

## Configuração do Gemini

`docs/TUTORIAL_GEMINI.md` (aba Ajuda). Secret `GEMINI_API_KEY` ou campo de sessão. Modelo em `config/gemini.json` (`gemini-2.5-flash`).

## Biblioteca · Cadastro de aluno · Continuidade · Relatórios · Mercado Pago

Descritos em `README.md` e `docs/TUTORIAL_PROFESSOR.md`. Link do Mercado Pago em `config/defaults.json` (placeholder até o proprietário preencher a SPEC §21).

## Dependências

`gradio`, `pydantic>=2`, `pandas`, `numpy`, `PyMuPDF`, `pypdf`, `python-docx`, `rank-bm25`, `music21`, `matplotlib`, `reportlab`, `qrcode`, `Pillow`, `httpx`, `tenacity`, `google-genai`; opcional `sentence-transformers`. Versões **fixadas** em `requirements.txt` a partir do ambiente do Colab testado em 08/09/2026 (SPEC §18).

## Limitações conhecidas

1. **Teste no Colab realizado em 08/09/2026** (abertura pelo GitHub, célula 1 e 2, Drive montado, interface inline estilizada, aba Novo registro aberta por clique). O roteiro pedagógico completo da SPEC §16.3 (3 aulas de piano, turma, biblioteca, Gemini) ainda deve ser percorrido por um professor no Colab.
2. **Chamadas reais ao Gemini não exercitadas**: o cliente usa o SDK `google-genai` conforme a documentação atual, mas só foi testado com mock. Verificar `response_schema` com pydantic no modelo configurado.
3. **CRMG**: a base contém o recorte equivalente à BNCC (mesmos códigos). Habilidades complementares específicas de Minas Gerais, se existirem no documento vigente, precisam ser acrescentadas após confirmação do proprietário (SPEC §21).
4. **BNCC EI e EM** transcritas de conhecimento consolidado, não por extração automática do PDF oficial: conferir contra o documento oficial antes do beta.
5. **APIs acadêmicas** testadas com respostas gravadas; formatos de resposta reais podem variar (o código tolera campos ausentes).
6. **Frequência individual em turma** existe no relatório; "avançada" (por conteúdo/aluno) fica no roadmap.
7. **Aba Ajuda** renderiza Markdown dos tutoriais; sem imagens (por decisão da SPEC §7.4).
8. Placeholders da SPEC §21 ainda abertos: link do Mercado Pago e e-mail OpenAlex. Repositório GitHub publicado: https://github.com/magoupdown/Percurso.

## Testes realizados (evidência)

- `pytest`: **103 passed** em 08/09/2026 (Windows 11, Python 3.13.15).
- Navegação real no navegador (servidor local Gradio): tela inicial → NOVO REGISTRO → registro criado com QR → Continuar (painel) → CRIAR PRIMEIRA AULA → GERAR PLANO (cronograma 50 min válido, atividades do perfil de piano) → REGISTRAR AULA A PARTIR DESTE PLANO → SALVAR AULA (Aula 1) → segunda aula com rendimento pelo menu (ritmo 4) → painel de retorno com "Aula 1/2", consolidado, dificuldade recorrente, última observação, próximo passo sugerido → Histórico com tabela. Erro de validação (aula sem conteúdo) exibido em PT-BR. Código digitado em minúsculas e sem hífen (`pcr4a6gvw`) aceito.
- Aba Pesquisar no navegador com APIs reais: OpenAlex e Crossref devolveram fontes brasileiras sobre flauta doce com DOI, autor, ano e data de consulta; Google Books (HTTP 429) e Semantic Scholar indisponíveis geraram o aviso "temporariamente indisponível. Continuando com outras fontes." sem interromper a pesquisa. Base curricular sugeriu EF15AR14/15 e objetivos da EI para "pulsação"; LISTAR HABILIDADES exibiu as 13 de Música + Artes integradas.
- Aba Relatórios no navegador: relatório de frequência gerado (100 %, 2 aulas, tabela por aula), PDF (37 KB) e DOCX (63 KB) oferecidos para download; material "folha do professor" sem plano na sessão exibiu a orientação correta.
- `pytest -m online`: teste real de OpenAlex e Crossref passou em 08/09/2026.
- Bug encontrado e corrigido durante a verificação: cabeçalho User-Agent com acento derrubava todos os provedores (`UnicodeEncodeError`); agora forçado a ASCII, com teste de regressão.
- Colab (08/09/2026), dois bugs encontrados e corrigidos pelo próprio teste: (a) `pip install -e` não é visto pelo kernel sem reiniciar → o notebook acrescenta `/content/Percurso` ao `sys.path`; (b) atrás do proxy do Colab o Gradio calculava a URL raiz com um host interno inalcançável (tema e API não carregavam) → `percurso.iniciar()` obtém a URL pública com `google.colab.kernel.proxyPort` e a passa como `root_path`. Versões instaladas no Colab registradas em `requirements.txt`.

## Melhorias recomendadas

- Preencher o link do Mercado Pago (SPEC §21).
- Percorrer o roteiro pedagógico manual (piano, turma, biblioteca, Gemini) com um professor no Colab.
- Considerar `verovio` (imagem de partitura) e OCR como primeiros itens do roadmap.
