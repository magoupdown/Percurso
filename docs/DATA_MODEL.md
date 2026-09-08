# Modelo de dados

Fonte de verdade: JSON por entidade em `Meu Drive/Percurso/` (SPEC D4). Modelos pydantic em `percurso/core/models.py`. Todo arquivo carrega `schema_version`. Campos desconhecidos são preservados (`extra="allow"`); nas migrações, o que o modelo não conhece vai para `_extra`.

## Estrutura

```
Percurso/
├── configuracoes/   professor.json · apoio.json · versao.json · rubricas.json · perfis/<instrumento>.json · diagnostico.log
├── registros/<PCR-XXXXXX>/   perfil.json · estado_atual.json · resumo_pedagogico.json · repertorio.json
│                             aulas/<data>_<id4>.json · planos/<data>_<id4>.json · materiais/
├── biblioteca/      catalogo.json · arquivos/<sha256>.<ext> · texto/<sha256>.json
├── indices/         biblioteca_bm25.json (+ manifesto) · biblioteca_emb_gemini.json
├── pesquisas/cache/<hash>.json
├── curriculo/ · relatorios/ · exportacoes/ · backups/<timestamp>_<motivo>/
```

## Códigos de registro

`PCR-` + 6 caracteres de `ABCDEFGHJKLMNPQRSTUVWXYZ23456789` (sem 0/O/1/I), gerados com `secrets.choice`, com verificação de colisão em `registros/`. Digitação sem hífen e em minúsculas é normalizada.

## Escrita atômica

`arquivo.json.tmp` → releitura + validação pydantic → `os.replace` → `arquivo.json.bak` (1 cópia). Leitura corrompida cai no `.bak`. Antes de migração ou exclusão: cópia da pasta em `backups/<timestamp>_<motivo>/`.

## Numeração de aulas

**Derivada, nunca armazenada.** Aula N = posição na lista ordenada por (`data`, `criado_em`, `id`), excluindo `cancelada_professor` e `cancelada_instituicao`. Registro retroativo reordena automaticamente.

## Regra de frequência (`core/attendance.py`)

```
numerador   = presenças + reposições + aulas extras
denominador = aulas registradas no período
              − canceladas pela instituição
              − canceladas pelo professor      (padrão; penalizar_cancelada_professor=False)
frequência % = numerador ÷ denominador × 100   (1 casa decimal; 0 se denominador = 0)
```

- `falta` e `falta_justificada` contam no denominador e não no numerador.
- `tempo_total_min` soma `duracao_real_min` (ou prevista, se real ausente) das aulas realizadas.
- Turma com lista de alunos: frequência individual = presenças do aluno ÷ encontros não cancelados. Sem lista: coletiva = Σ n_presentes ÷ Σ quantidade_alunos.

## Regra de estado (`core/state.py`)

O estado é **recalculado a partir de todas as aulas** (ordem cronológica) a cada gravação/exclusão:

1. Para cada conteúdo classificado (`classificacao_conteudos`), o estado mais recente vence: `consolidado` → `conteudos_consolidados`; `em_desenvolvimento` e `dificuldade` → `em_desenvolvimento`.
2. Aula sem classificação: `conteudo_realizado` conta como `em_desenvolvimento`.
3. `dificuldades_recorrentes` = dificuldades (texto livre ou conteúdo marcado como dificuldade) citadas em ≥ 2 aulas.
4. `dificuldades_recentes` = dificuldades da última aula.
5. `proximo_objetivo` = último `proximo_passo` não vazio; `ultima_observacao` = últimas `observacoes` (ou avaliação qualitativa).
6. `rendimento_recente` = últimas 3 notas por critério (só o registrado).
7. `unidade_atual` = última `unidade` informada numa aula ou plano.

Pré-preenchimento da classificação no formulário: consolidado se já consolidado; dificuldade se recorrente/recente; senão em desenvolvimento.

## Resumo pedagógico

Texto ≤ 1500 caracteres + últimos 5 encontros (data, número, conteúdo, situação, 1 linha). Template no Modo Essencial; reescrito por Gemini no Modo Inteligente (`gerado_por = gemini`), editável pelo professor (`professor`). Quando gerado por Gemini/professor, o recálculo preserva o texto e atualiza só a lista de encontros.

## Planos

`planos/<data>_<id>.json` com `status: gerado | realizado | descartado`. Aula registrada a partir de um plano aponta `plano_origem` e o plano recebe `realizado`.

## Migração

`configuracoes/versao.json` = versão global. Sem `versao.json` e com registros → v0 (formato da especificação v1: `nome`→`identificacao`, `conteudo`→`conteudo_realizado`, `presenca`→`frequencia`). `storage/migrations/v0_to_v1.py` renomeia, adiciona `schema_version` e guarda o resto em `_extra`. Backup obrigatório antes.
