# Arquitetura

```
                         PERCURSO
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
   percurso/ui          percurso/core      percurso/storage
   (Gradio)          planejamento, estado,   base_path → JSON
                     progressão, relatórios   escrita atômica
                            │
     ┌───────────┬──────────┼──────────┬──────────────┐
     │           │          │          │              │
 domains/music  research   curriculum  library        ai
 music21        OpenAlex   BNCC Arte   PDF/DOCX/MD    google-genai
 perfis instr.  Crossref   BNCC EI     BM25           pydantic
 progressões    G. Books   CRMG        catálogo       pseudonimização
                            │
                  percurso/platform (colab | local)
```

## Princípios (SPEC §1.3, §2)

- `dados → regras → validação → IA`. Python calcula frequência, cronograma, códigos curriculares, tonalidade; Gemini só redige, interpreta e sintetiza.
- **Notebook fino** (2 células); todo o código está no pacote `percurso/`, instalado com `pip install -e`.
- **Plataforma isolada**: apenas `platform/colab.py` importa `google.colab`. `platform/local.py` oferece o mesmo contrato (montar armazenamento, ler segredo, log de runtime).
- **Storage com `base_path`**: `storage/paths.py` define a estrutura; `storage/atomic.py` grava `.tmp → validar → os.replace → .bak`; `storage/repo.py` é o único ponto de leitura/escrita das entidades. JSON é a fonte de verdade (D4).
- **Núcleo independente de domínio**: `core/` fala com `domains/base.DomainAdapter`. `domains/music/` concentra perfis instrumentais, progressões, exercícios, vocabulário e music21.
- **Interface**: `ui/texts.py` concentra o PT-BR; `ui/screens/*` monta uma aba cada; `app.py` liga navegação e Gemini. Abas de entregas posteriores só aparecem quando o módulo existe.

## Fluxo de uma aula

1. `Continuar` carrega `registros/<código>/` → `Sessao.contexto` (perfil, estado, resumo, aulas numeradas, repertório).
2. `Planejar` → `core/planner.gerar_plano` (Modo Essencial) ou `ai/planning.gerar_plano_gemini` (Modo Inteligente, com fallback). O plano passa por `core/schedule.validar_cronograma`. Se "onde pesquisar" foi marcado, `research/integracao` anexa referências verificáveis (📚 biblioteca, 🏛 currículo, 🎓 acadêmica) e habilidades validadas.
3. `Registrar aula` grava `aulas/<data>_<id>.json` e chama `core/state.atualizar_apos_aula`, que recalcula `estado_atual.json` e `resumo_pedagogico.json` a partir de todas as aulas (numeração derivada; retroativas reordenam).
4. `Relatórios` → `reports/builder.montar` (frequência/rendimento em Python; pedagógico por template, narrativa opcional por Gemini) → `export_pdf`/`export_docx`/`export_text`.

## Segurança e LGPD (SPEC §14)

- Código opera apenas em `<base_path>` (= `MyDrive/Percurso`); `Caminhos.dentro_da_base` bloqueia escrita fora dela.
- Chave Gemini: Colab Secrets (`GEMINI_API_KEY`) ou campo de sessão em memória. Nunca gravada, logada (`utils/logging.FiltroSegredos`), exportada ou enviada a outro serviço.
- Pseudonimização (`ai/anonymize.Pseudonimizador`) em todo prompt; o validador rejeita prompts que contenham o nome real. Trechos de biblioteca só com consentimento da sessão (`Sessao.consentimento_trechos`).
- Direitos: exportar zip, excluir registro (backup em `backups/` por 30 dias), excluir biblioteca, apagar dados locais. Exclusões pedem confirmação e listam o que será removido.

## Pesquisa (SPEC §11)

- Provedores em `research/providers/` com contrato `buscar(consulta) -> [Fonte]`, `disponivel()`. HTTP via `httpx` (timeout 15 s) e `tenacity` (3 tentativas com backoff). Falha de um provedor gera aviso e a pesquisa continua.
- `research/expand.py` gera consultas PT/EN pelo vocabulário do adaptador.
- `research/cache.py`: `pesquisas/cache/<hash>.json`, 90 dias; cache antigo serve de fallback quando a rede cai.
- `research/trace.py`: toda fonte carrega tipo, título, autor, ano, fonte, URL/DOI, página, data de consulta; `filtrar_verificadas` rejeita o que não tem origem verificável. `ai/planning` recusa referências fora do conjunto fornecido ao modelo.

## Modo Inteligente (SPEC §7)

`ai/gemini.ClienteGemini` (SDK `google-genai`, modelo em `config/gemini.json`), saída estruturada por `response_schema` (`ai/schemas.py`), ciclo `ai/validate_loop.executar` (gera → valida → reenvia com erro → 3 tentativas → fallback). Contexto mínimo em `ai/context.py`. Cache por hash do prompt em memória de sessão.

## Roadmap e limites

Ver `docs/ROADMAP.md`. Sem servidor, login, banco central ou paywall.
