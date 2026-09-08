# Testes

```bash
pip install -e ".[dev]"
pytest            # 102 testes, sem rede
pytest -m online  # integrações reais (opcional; hoje não há testes marcados)
```

## Infraestrutura (SPEC §16.1)

- `tests/conftest.py`: fixture `base` aponta `PERCURSO_BASE_PATH` para `tmp_path` e instala `PlataformaLocal`; `repo` e `sessao` derivam dela. `registro_com_14_aulas` cria o registro de exemplo (piano, 14 aulas, 1 falta, 1 cancelada, dificuldade recorrente).
- `tests/mocks/gemini.py`: `ClienteFalso` com roteiro de respostas (válidas, inválidas, referência inventada, falha de rede) e embeddings determinísticos.
- `tests/mocks/providers.py`: `HTTPFalso` com respostas gravadas em `tests/fixtures/providers/*.json`; `fora_do_ar` simula queda de provedor.
- `tests/fixtures/`: PDF com texto (3 páginas), PDF só imagem, PDF corrompido, DOCX, MD. Dados v0 para migração são gerados dentro de `test_storage.py`.

## Mapa dos casos obrigatórios (SPEC §16.2)

| # | Caso | Teste |
|---|------|-------|
| 1 | Primeira abertura | `test_storage.test_primeira_abertura_cria_estrutura_e_versao` |
| 2 | Nova sessão com pasta existente | `test_storage.test_reabrir_recupera_dados_sem_alteracao` |
| 3 | Gemini desativado | `test_app.test_app_monta_sem_gemini`, `test_fluxo_completo_modo_essencial` |
| 4 | Gemini com chave válida (mock) | `test_app.test_gemini_chave_valida_mock`, `test_gemini.*` |
| 5 | Gemini sem chave | `test_app.test_gemini_sem_chave` |
| 6 | Chave inválida | `test_app.test_gemini_chave_invalida_amigavel` |
| 7 | Upload de PDF | `test_library.test_upload_pdf_extrai_indexa_cataloga_persiste` |
| 8 | Upload duplicado | `test_library.test_upload_duplicado_nao_duplica` |
| 9 | Criar registro | `test_core.test_codigo_*`, `test_storage.test_criar_registro_cria_arquivos_base` |
| 10 | Fechar e reabrir | `test_storage.test_reabrir_recupera_dados_sem_alteracao` |
| 11 | Segunda aula usa o estado | `test_state_planner.test_segunda_aula_nao_repete_consolidado` |
| 12 | Frequência | `test_core.test_frequencia_*`, `test_reports.test_todos_os_tipos_e_exportacoes` |
| 13 | Cronograma | `test_core.test_cronograma_*`, `test_adaptar_duracao_*` |
| 14 | Relatório PDF/DOCX | `test_reports.*` |
| 15 | Lembrete de apoio | `test_donations.*` |
| 16 | API acadêmica fora do ar | `test_research.test_provedor_fora_do_ar_nao_derruba_pesquisa` |
| 17 | Arquivo corrompido | `test_library.test_arquivo_corrompido_nao_quebra_os_demais` |
| 18 | Histórico antigo (migração) | `test_storage.test_migracao_v0_sem_perda_com_backup` |
| 19 | Pseudonimização | `test_gemini.test_nenhum_nome_no_prompt`, `test_app.test_pseudonimizacao` |
| 20 | Validação de habilidade | `test_curriculum.*` |
| 21 | Referência inventada | `test_gemini.test_referencia_inventada_reenvia_e_depois_aceita`, `test_tres_falhas_caem_no_modelo_pedagogico` |
| 22 | Numeração de aulas | `test_state_planner.test_registro_retroativo_reordena_numeracao` |

## Testes manuais (SPEC §16.3)

Roteiro no Colab antes de cada entrega ao beta: piano (3 aulas + reabertura + 4ª aula), turma de percepção (16 alunos, 3 encontros, relatórios), biblioteca (PDF + DOCX, busca, persistência), Modo Essencial × Modo Inteligente na mesma aula. Registrar a data no README ("Último teste no Colab").

## Teste local da interface

```bash
PERCURSO_BASE_PATH=./dados_locais/Percurso python -c "import percurso; percurso.iniciar(inline=False)"
```
