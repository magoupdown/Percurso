# PERCURSO
## Plataforma de inteligência pedagógica

**Especificação de arquitetura e desenvolvimento — versão 2 (reestruturada)**

Infraestrutura da primeira versão: GitHub + Google Colab + Google Drive do professor.
Primeira especialização pedagógica: Música (módulo interno; a marca é somente **Percurso**).

---

## 0. COMO USAR ESTE DOCUMENTO (INSTRUÇÃO AO AGENTE)

Este arquivo é a fonte única de requisitos. Ele substitui a especificação v1 (142 seções), preservando todos os seus requisitos e reorganizando-os em ordem de implementação.

Regras de trabalho:

1. Ler o documento inteiro antes de escrever código.
2. Desenvolver **por entregas** (Seção 17: E1 → E5). Cada entrega precisa passar nos seus critérios de aceitação antes da próxima começar. A E1 sozinha já deve ser utilizável por professores reais.
3. Nunca remover funcionalidade silenciosamente. Se algo parecer excessivo, propor reordenação usando o formato "MELHORIA PROPOSTA" (Seção 20).
4. Decisões técnicas já tomadas na Seção 2 **não** devem ser reabertas sem uma razão nova e concreta.
5. Não simular funcionalidade. Botão presente = botão funcional. Sem "Em breve", sem TODO em função essencial, sem API inexistente, sem afirmar teste que não rodou.
6. Nunca pedir chave de API por chat. Orientar: Colab Secrets.
7. Ao concluir cada entrega, produzir o relatório da Seção 19.4.

Prioridade em caso de conflito (nesta ordem):
1. integridade dos dados · 2. segurança · 3. funcionamento · 4. simplicidade para o professor · 5. qualidade pedagógica · 6. rastreabilidade · 7. desempenho · 8. aparência.

Sugestão de uso no Claude Code: salvar este arquivo como `SPEC.md` na raiz do repositório e criar um `CLAUDE.md` curto:
```
Leia SPEC.md integralmente. Trabalhe pela ordem de entregas da Seção 17.
Rode `pytest` antes de considerar qualquer tarefa concluída.
Não altere decisões da Seção 2 sem propor via formato da Seção 20.
```

---

## 1. PRODUTO E PRINCÍPIOS

### 1.1 Identidade
- Nome: **Percurso**. Subtítulo: **Plataforma de inteligência pedagógica**.
- Frase conceitual (uso opcional): «Cada aula começa de onde a anterior terminou.»
- Proibido: "Percurso Música", "Percurso Musical", "Música Percurso", "Percurso Educação Musical".
- Identidade visual: limpa, contemporânea, educacional, acolhedora, não infantilizada, não "dashboard corporativo". Sem logotipo até o proprietário fornecer um; usar tipografia.

### 1.2 Princípio central
O Percurso não é um gerador de planos de aula. É um sistema de **memória pedagógica longitudinal**:

```
AULA → REGISTRO → ANÁLISE → ESTADO PEDAGÓGICO ATUAL → PESQUISA → PLANEJAMENTO → PRÓXIMA AULA
```

O sistema deve responder, para qualquer registro: onde o aluno estava, o que foi trabalhado, o que consolidou, que dificuldade permanece, qual objetivo está em desenvolvimento, qual progressão é adequada, o que deve acontecer na próxima aula.

O histórico **modifica** o planejamento futuro. Não é documentação passiva.

### 1.3 Princípio de confiabilidade
```
dados → regras → validação → IA
```
Nunca "IA decide tudo". O que Python calcula (percentual de frequência, soma de cronograma, código BNCC, tonalidade via music21) nunca é delegado ao modelo. IA entra onde linguagem, interpretação e síntese acrescentam valor.

### 1.4 Público inicial
~20 professores beta, predominantemente de Música: piano, teclado, violão, guitarra, flauta doce, flauta transversal, clarinete, saxofone, trompete, trombone, violino, viola, violoncelo, canto, coral, bateria, percussão, percepção musical, musicalização, teoria musical, prática de conjunto, **outro (preenchimento manual)**.

### 1.5 Experiência do professor
O professor não deve perceber que usa Python. Nunca exigir: editar código, variáveis, caminhos, JSON, banco de dados, instalar bibliotecas, terminal, organizar pastas no Drive. Interface 100% em Português do Brasil. Linguagem simples, contraste adequado, sem depender só de cor, funcional em telas menores.

### 1.6 Gratuidade
O Percurso é gratuito. Sem paywall, sem contagem de sessões, sem bloqueio de função. Apoio voluntário via Mercado Pago (Seção 13).

---

## 2. DECISÕES DE ARQUITETURA (TOMADAS)

Cada decisão abaixo altera algo da v1 e traz sua justificativa. Elas preservam a experiência e os objetivos; mudam o meio.

### D1 — Interface em Gradio, não ipywidgets
- **Problema:** ipywidgets no Colab tem eventos instáveis, layout frágil e não oferece abas/formulários dignos de "pequeno aplicativo".
- **Mudança:** interface construída com `gradio` (Blocks + Tabs), lançada inline dentro do Colab (`demo.launch(inline=True, share=False)`). Upload de arquivo via `gr.File`, evitando `files.upload()`.
- **Benefício:** experiência de app real, PT-BR, funciona em tela menor, upload nativo.
- **Impacto:** o `drive.mount()` não pode ser disparado de dentro do Gradio (o popup de autorização é do próprio Colab). A Célula 2 do notebook passa a fazer "Conectar Drive + Abrir Percurso". A experiência conceitual da v1 §6 se mantém: um clique, mensagem de sucesso, app aberto.

### D2 — Notebook fino, código no pacote
- `Percurso.ipynb` contém 2 células (Seção 3.3). Todo o código vive no pacote `percurso/` no repositório. O notebook clona/instala o repositório na inicialização.
- **Benefício:** atualização automática para os 20 testadores, testes com `pytest`, o agente trabalha em `.py`.

### D3 — Camada de armazenamento com `base_path` configurável
- Toda persistência passa por `percurso/storage/` que recebe um `base_path`. No Colab: `/content/drive/MyDrive/Percurso`. Local/testes: qualquer pasta (`PERCURSO_BASE_PATH`).
- **Benefício:** o sistema inteiro roda e é testado fora do Colab; Drive é só um diretório.

### D4 — JSON é a fonte de verdade; sem SQLite na V1
- 20 professores × dezenas de registros não justificam índice relacional. JSON por entidade + leitura por glob.
- SQLite fica reservado ao roadmap, sempre como cache reconstruível, nunca como fonte de verdade.

### D5 — BM25 primário; embeddings opcionais
- **Problema:** `multilingual-e5` + FAISS custam 500 MB–1 GB de download por sessão e indexação lenta em CPU.
- **Mudança:** busca na biblioteca = busca textual exata + BM25 (`rank_bm25`) com expansão de sinônimos pedagógicos (Seção 9.5). Busca semântica por embeddings da API Gemini quando o Modo Inteligente estiver ativo. `sentence-transformers` apenas como opt-in explícito ("Instalar busca semântica local nesta sessão").
- **Benefício:** biblioteca pesquisável em segundos em qualquer sessão, sem download pesado. A pesquisa nunca para.

### D6 — SDK `google-genai` + Colab Secrets
- Usar o SDK oficial atual (`google-genai`), nunca `google-generativeai` (descontinuado). Verificar a documentação no momento da implementação. Nome do modelo em `config/gemini.json`, nunca fixo no código.
- Chave: `userdata.get("GEMINI_API_KEY")` do Colab Secrets. Alternativa: campo tipo senha no app, "usar apenas nesta sessão", guardado somente em memória.

### D7 — Pseudonimização antes de qualquer chamada à IA
- Nomes de alunos nunca vão ao Gemini. No prompt, o aluno é referido pelo código do registro (ex.: "o aluno PCR-7K4M2Q"). O texto retornado tem o código substituído pelo nome na tela. Turmas: nomes dos alunos substituídos por índices.

### D8 — music21 sem renderização de partitura na V1
- **Limitação de plataforma:** renderizar partitura em imagem exige MuseScore/LilyPond, ausentes no Colab. A V1 gera **MIDI e MusicXML**; imagem de partitura entra na Fase 2 via `verovio` (renderiza SVG sem binário externo).

### D9 — Tudo que é Colab fica isolado em um módulo
- `percurso/platform/colab.py` concentra `drive.mount`, `userdata`, detecção de ambiente. `percurso/platform/local.py` oferece o mesmo contrato para desenvolvimento e testes. Nenhum outro módulo importa `google.colab`.

### D10 — Escopo cortado da V1 sem perda dos requisitos da v1 §116
Ficam para o roadmap: pesquisa web ampla (§25), OCR (§17), formatos EPUB/XLSX/CSV/PPTX na biblioteca, `pretty_midi`/`librosa`/`pydub`, SQLite, imagem de partitura, Semantic Scholar como provedor obrigatório (vira opcional).

---

## 3. ARQUITETURA TÉCNICA

### 3.1 Visão geral
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
 perfis instr.  Crossref   CRMG        BM25           pydantic
 progressões    G. Books   validação   catálogo       pseudonimização
                            │
                  percurso/platform (colab | local)
```

### 3.2 Estrutura do repositório
```
Percurso/
├── Percurso.ipynb            # 2 células, fino
├── README.md
├── SPEC.md                   # este documento
├── CLAUDE.md
├── requirements.txt
├── pyproject.toml
├── LICENSE
├── percurso/
│   ├── __init__.py           # iniciar(), versão
│   ├── app.py                # monta e lança a UI
│   ├── platform/             # colab.py, local.py, base.py
│   ├── storage/              # paths.py, atomic.py, repo.py, migrations/
│   ├── core/                 # models.py (pydantic), codes.py, schedule.py,
│   │                         # state.py, planner.py, attendance.py, grading.py
│   ├── domains/
│   │   ├── base.py           # DomainAdapter (interface)
│   │   └── music/            # adapter.py, theory.py (music21),
│   │       └── instrument_profiles/*.json
│   ├── library/              # ingest.py, extract.py, catalog.py, search.py
│   ├── research/             # providers/*.py, expand.py, cache.py, trace.py
│   ├── curriculum/           # bncc.py, crmg.py, validate.py, data/*.json
│   ├── ai/                   # gemini.py, prompts/, schemas.py, validate_loop.py, anonymize.py
│   ├── reports/              # attendance.py, performance.py, pedagogical.py,
│   │                         # charts.py, export_pdf.py, export_docx.py
│   ├── support/              # donations.py (QR, lembrete mensal)
│   ├── ui/                   # screens/*.py, texts.py (todo texto PT-BR), theme.py
│   └── utils/                # logging.py, hashing.py, dates.py
├── config/                   # gemini.json, defaults.json
├── docs/                     # ARCHITECTURE.md, DATA_MODEL.md, TESTING.md, TUTORIAL_PROFESSOR.md
├── tests/                    # pytest, fixtures/, mocks/
└── assets/                   # tipografia, ícones simples
```

### 3.3 Notebook e bootstrap
**Célula 1 — INICIALIZAR PERCURSO** (título em Markdown acima, código recolhido)
```python
#@title ▶ Inicializar Percurso (executar uma vez por sessão)
import subprocess, sys, os
REPO = "https://github.com/<CONTA>/Percurso.git"   # preencher (Seção 21)
if not os.path.exists("/content/Percurso"):
    subprocess.run(["git", "clone", "--depth", "1", REPO, "/content/Percurso"], check=True)
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-e", "/content/Percurso"], check=True)
print("✓ Percurso pronto. Execute a célula abaixo.")
```
**Célula 2 — ABRIR PERCURSO**
```python
#@title ▶ Abrir Percurso
import percurso
percurso.iniciar()   # conecta o Drive (popup do Colab), cria estrutura, abre a interface
```
`percurso.iniciar()`:
1. detecta plataforma (colab/local);
2. mostra a mensagem de transparência (Seção 14.1) e monta o Drive;
3. cria/verifica a estrutura `Percurso/` (Seção 4.1);
4. detecta versão de schema e migra se necessário (backup antes);
5. verifica lembrete mensal de apoio (Seção 13.4);
6. lança a interface Gradio inline.

Se `git clone` falhar (rede), mostrar mensagem clara em PT-BR e instrução de tentar novamente. Nunca exigir Git manual.

### 3.4 Sessão do Colab
O runtime é temporário. Regra absoluta: **toda ação do professor grava no Drive imediatamente** (escrita atômica). Nada relevante fica apenas em memória. Estado de sessão (Gemini ligado, chave temporária, consentimento de envio de trechos) vive só em memória e morre com o runtime.

---

## 4. MODELO DE DADOS E PERSISTÊNCIA

### 4.1 Estrutura no Drive
```
Meu Drive/Percurso/
├── configuracoes/
│   ├── professor.json
│   ├── apoio.json                  # {"ultimo_mes_lembrete_apoio": "2026-09"}
│   └── versao.json                 # {"schema_version": 1}
├── registros/
│   └── PCR-7K4M2Q/
│       ├── perfil.json
│       ├── estado_atual.json
│       ├── resumo_pedagogico.json
│       ├── repertorio.json
│       ├── aulas/
│       │   ├── 2026-08-01_a3f9.json
│       │   └── 2026-08-08_b71c.json
│       ├── planos/                 # planos gerados (ainda não realizados)
│       └── materiais/
├── biblioteca/
│   ├── catalogo.json
│   ├── arquivos/<sha256>.<ext>
│   └── texto/<sha256>.json         # texto extraído em trechos
├── indices/
│   └── biblioteca_bm25.json        # + manifesto (hash, data, versão, modelo, n_trechos)
├── pesquisas/
│   └── cache/<hash_query>.json
├── curriculo/                      # documentos curriculares próprios (futuro)
├── relatorios/
├── exportacoes/
└── backups/
    └── 2026-09-06T10-15_pre-migracao-v2/
```
O código só opera dentro de `Percurso/`. Nunca varrer o Drive inteiro.

### 4.2 Códigos de registro
- Formato `PCR-XXXXXX`, 6 caracteres do alfabeto `ABCDEFGHJKLMNPQRSTUVWXYZ23456789` (sem 0/O/1/I — o professor digita à mão), gerados com `secrets.choice`.
- Verificar colisão em `registros/` antes de aceitar.
- O código nunca revela nome, idade, instrumento ou turma.
- Aceitar digitação sem hífen e em minúsculas; normalizar.

### 4.3 Entidades (pydantic em `core/models.py`, todas com `schema_version`)

**Professor** (`configuracoes/professor.json`) — todos opcionais: nome, instituição, cidade, estado, área principal, níveis de ensino, duração padrão de aula, currículo padrão, preferências pedagógicas, metodologias preferidas, fuso horário (padrão `America/Sao_Paulo`), e-mail de contato (opcional). Nunca: CPF, RG, endereço, dados bancários.

**Registro** (`perfil.json`):
```json
{
  "schema_version": 1,
  "codigo": "PCR-7K4M2Q",
  "tipo": "individual | dupla | turma",
  "modalidade": "individual | dupla | turma | coral | banda | percepcao_musical | musicalizacao | oficina | pratica_conjunto | outro",
  "modalidade_outro": null,
  "dominio": "musica",
  "identificacao": "João",              // primeiro nome, iniciais ou pseudônimo (Seção 14.3)
  "idade": 10,                           // opcional; para turma: faixa etária
  "instrumento": "piano",               // id de instrument_profiles ou "outro"
  "instrumento_outro": null,
  "nivel": "iniciante | basico | intermediario | avancado",
  "contexto": "escola | conservatorio | aula_particular | projeto_social | curso_livre | outro",
  "curriculo": "bncc | bncc_crmg | proprio | curso_livre | conservatorio | nenhum",
  "agenda": {"dia_habitual": "terca", "inicio": "15:00", "termino": "15:50", "duracao_min": 50},
  "conhecimentos_previos": [],
  "objetivos": [],
  "adaptacoes": "",                      // texto livre; sem inferência médica
  "recursos_habituais": ["quadro", "instrumentos"],
  "metodologias": ["orff", "propria"],
  "observacoes": "",
  "turma": null,                         // preenchido quando tipo = turma (abaixo)
  "criado_em": "2026-09-06T10:00:00-03:00",
  "atualizado_em": "..."
}
```
Para `tipo = turma`, o campo `turma`:
```json
{"nome": "Percepção 2A", "quantidade_alunos": 16, "nivel_geral": "iniciante",
 "alunos": [{"id": "A01", "identificacao": "Ana"}, {"id": "A02", "identificacao": "Bruno"}]}
```
A lista de alunos é opcional; sem ela, a frequência é coletiva (n presentes de N).

**Aula** (`aulas/<data>_<id4>.json`):
```json
{
  "schema_version": 1,
  "id": "a3f9",
  "data": "2026-08-01",
  "dia_semana": "sexta",
  "horario_previsto": {"inicio": "15:00", "termino": "15:50"},
  "horario_real": {"inicio": "15:05", "termino": "15:50"},
  "duracao_prevista_min": 50,
  "duracao_real_min": 45,
  "frequencia": "presente | falta | falta_justificada | reposicao | aula_extra | cancelada_professor | cancelada_instituicao",
  "frequencia_turma": {"presentes": ["A01","A03"], "ausentes": ["A02"]},  // ou {"n_presentes": 14}
  "tipo_aula": "continuidade | revisao | nova_unidade | extraordinaria | retroativa",
  "conteudo_planejado": [],
  "conteudo_realizado": [],
  "objetivos": [],
  "atividades": [],
  "materiais": [],
  "cronograma": [{"inicio_min": 0, "fim_min": 5, "titulo": "Acolhimento", "descricao": ""}],
  "rendimento": {"leitura": 3, "ritmo": 4},   // apenas o que o professor informou
  "avaliacao_qualitativa": "",
  "dificuldades": [],
  "conquistas": [],
  "observacoes": "",
  "tarefas": [],
  "proximo_passo": "",
  "repertorio_trabalhado": [],
  "habilidades_curriculares": ["EF15AR14"],   // somente códigos validados
  "fontes_utilizadas": [],                    // Seção 11.5
  "modo_ia": "essencial | gemini",
  "plano_origem": "planos/2026-08-01_a3f9.json"
}
```
- **Numeração "Aula N"** é derivada: posição da aula na lista ordenada por data (excluindo canceladas). Nunca armazenar, porque registro retroativo (§47) reordena.
- Data sugerida = hoje; sempre editável.

**Estado atual** (`estado_atual.json`) — atualizado após cada aula:
```json
{
  "schema_version": 1,
  "total_aulas": 14,
  "ultima_aula": "2026-08-28",
  "unidade_atual": "coordenação e leitura básica",
  "conteudos_consolidados": ["semínima", "mínima", "reconhecimento das notas"],
  "em_desenvolvimento": ["regularidade rítmica", "coordenação dedos 3 e 4"],
  "dificuldades_recorrentes": ["troca dedos 3 e 4", "acelera no final das frases"],
  "proximo_objetivo": "introdução de duas colcheias",
  "ultima_observacao": "tendência a acelerar no final das frases",
  "rendimento_recente": {"leitura": [3,3,4], "ritmo": [4,4,4]},
  "atualizado_em": "..."
}
```
Atualização é **determinística**: ao registrar a aula, o professor classifica cada conteúdo trabalhado como *consolidado / em desenvolvimento / dificuldade* (pré-preenchido com o estado anterior). Dificuldade citada em ≥2 aulas vira recorrente. Com Gemini, o modelo pode **propor** a classificação; o professor confirma.

**Resumo pedagógico** (`resumo_pedagogico.json`): texto curto (≤ 1500 caracteres) + lista dos últimos 5 encontros (data, conteúdo, situação, 1 linha). É o que vai ao prompt, nunca o histórico inteiro. Gerado por template no Modo Essencial; reescrito por Gemini no Modo Inteligente (o professor pode editar).

**Repertório** (`repertorio.json`): lista de `{obra, compositor, arranjo, nivel, estado: em_estudo|concluido|apresentacao|revisao, inicio, fim}`.

**Plano** (`planos/`): saída completa da Seção 8.4, com `status: gerado|realizado|descartado`. Quando a aula é registrada a partir de um plano, o plano recebe `realizado` e a aula aponta para ele.

### 4.4 Escrita atômica e backups
`storage/atomic.py`: escrever em `arquivo.json.tmp` → validar (parse + pydantic) → `os.replace` → manter `arquivo.json.bak` (1 cópia). Antes de qualquer migração de schema: cópia da pasta afetada em `backups/<timestamp>_<motivo>/`. Nunca dezenas de cópias.

### 4.5 Versionamento e migração
`configuracoes/versao.json` guarda a versão global; cada arquivo guarda a sua. `storage/migrations/v1_to_v2.py` etc. Ao detectar versão antiga: "Versão antiga detectada. Fazendo backup e atualizando seus dados…". Migração nunca perde campos: campos desconhecidos são preservados em `_extra`.

---

## 5. MÓDULO DE DOMÍNIO: MÚSICA

### 5.1 Adaptador de domínio
`domains/base.py` define `DomainAdapter` com o contrato usado pelo núcleo:
```
listar_especialidades()            -> instrumentos / áreas ("piano", "percepcao_musical"…)
perfil_especialidade(id)           -> perfil estruturado (Seção 5.2)
rubrica_padrao(especialidade, modalidade, idade)
progressao_sugerida(estado_atual, perfil, curriculo)   -> "próximo passo sugerido" + justificativa
vocabulario(especialidade)         -> termos para expansão de consultas (PT/EN)
gerar_material_deterministico(tipo, parametros)        -> ex.: MIDI de escala
validar_conteudo(texto)            -> checagens determinísticas (ex.: tonalidade via music21)
expandir_consulta(tema, especialidade, nivel)          -> lista de consultas PT/EN
```
O núcleo (aluno, turma, histórico, frequência, rendimento, currículo, biblioteca, pesquisa, aula, cronograma, relatório) **não importa nada de `domains/music`**. Toda referência a instrumento, tessitura, técnica, music21 fica no adaptador. Futuro: `domains/math`, `domains/portuguese`, `domains/science`, `domains/infantil`.

### 5.2 Perfis instrumentais (`domains/music/instrument_profiles/*.json`)
Um arquivo por instrumento/área da Seção 1.4. Campos:
```json
{
  "id": "flauta_doce", "nome": "Flauta doce", "familia": "sopro_madeira",
  "tessitura": {"inicial": ["G4","A4","B4"], "ampliada": "C4–D6"},
  "postura": [], "tecnicas_fundamentais": [], "pre_requisitos": {},
  "progressoes": {
    "pulsacao": ["pulsação corporal", "respiração", "ataques", "nota repetida", "Sol, Lá e Si", "frase curta"]
  },
  "dificuldades_frequentes": [], "vocabulario_pt": [], "vocabulario_en": [],
  "tipos_de_exercicios": {}, "criterios_avaliacao": ["sonoridade","respiracao","articulacao","ritmo","leitura","autonomia"],
  "consideracoes_etarias": {"6-8": [], "9-12": [], "13+": []},
  "editavel": true
}
```
Os perfis são **hipóteses pedagógicas editáveis**, não verdade absoluta. O professor pode ajustar no app (cópia salva em `Percurso/configuracoes/perfis/`; o original do repositório permanece). O instrumento é estrutural: altera pesquisa, metodologia, exercícios, objetivos, progressão, vocabulário, dificuldades esperadas, recursos e avaliação — nunca só uma palavra no prompt.

Exemplo obrigatório de diferenciação (tema "pulsação"): piano → corpo → nota única → cinco dedos → alternância de mãos → pequena estrutura; flauta doce → corpo → respiração → ataques → nota repetida → Sol-Lá-Si → frase curta; percussão → movimento → pulso → ostinato → subdivisão → coordenação entre grupos.

### 5.3 Rubricas
Flexíveis, desativáveis, escala 1–5 por padrão. Padrão para instrumento: leitura, ritmo, técnica, coordenação, percepção, autonomia. Variam por instrumento (do perfil), modalidade, idade. O professor pode criar critérios próprios. **IA nunca preenche rendimento não informado.**

### 5.4 Metodologias
Seleção múltipla: Dalcroze, Orff, Kodály, Gordon, Swanwick, abordagem própria, combinação, sem preferência. Nenhuma afirmação sobre esses autores sem fonte rastreável (biblioteca ou acadêmica).

### 5.5 music21 (`domains/music/theory.py`)
Funções determinísticas: notas, intervalos, acordes, escalas, tonalidades, compassos, transposição, análise por graus/números romanos, tessitura por instrumento, geração de exemplos (escala, arpejo, padrão rítmico) em **MIDI e MusicXML**. Sem renderização de imagem na V1 (D8). Sempre preferir cálculo a geração textual quando a pergunta for teórica.

---

## 6. INTERFACE (GRADIO)

### 6.1 Princípios
Blocks + Tabs; todo texto em `ui/texts.py` (PT-BR, uma fonte). Tema próprio em `ui/theme.py` (fonte legível, contraste, botões claros, sem excesso). Nenhuma mensagem técnica ao professor; erros viram frases claras + botão DIAGNÓSTICO opcional.

### 6.2 Tela inicial
```
PERCURSO — Plataforma de inteligência pedagógica
[ Modo Essencial ativo ]  ou  [ Modo Inteligente (Gemini) ativo ]

[ CONTINUAR ALUNO OU TURMA ]  [ NOVO REGISTRO ]  [ PLANEJAR AULA ]
[ PESQUISAR ]  [ MINHA BIBLIOTECA ]  [ RELATÓRIOS ]  [ CONFIGURAÇÕES ]
                                                   ♡ Apoiar o Percurso
```
Na primeira execução: onboarding (boas-vindas, Drive conectado ✓, estrutura criada ✓, perfil opcional). A cada sessão: "Deseja utilizar inteligência Gemini nesta sessão? [USAR GEMINI] [CONTINUAR SEM GEMINI]" — escolha nunca persistida.

### 6.3 Continuar aluno ou turma
Campo "Digite o código" → [CARREGAR] → painel de retorno (exemplo real de saída):
```
João · Piano · Aula 14 · Última aula: 28/08/2026
Conteúdos trabalhados: posição de cinco dedos · pulsação · semínima · mínima
Consolidado: ✓ reconhecimento das notas ✓ pulsação em exercícios simples
Em desenvolvimento: coordenação entre dedos 3 e 4
Última observação: tendência a acelerar no final das frases
Próximo passo sugerido: consolidar coordenação antes de ampliar a extensão
```
Botões: CONTINUAR DE ONDE PARAMOS · FAZER REVISÃO · CRIAR NOVA AULA (nova unidade) · AULA EXTRAORDINÁRIA · ALTERAR PLANEJAMENTO · VER HISTÓRICO · GERAR RELATÓRIO.
Se não há aulas: "Este registro ainda não possui aulas." → [CRIAR PRIMEIRA AULA] [REGISTRAR AULA JÁ REALIZADA].

### 6.4 Novo registro (fluxo)
tipo → identificação → instrumento/área → nível/idade → modalidade → agenda → currículo → conhecimentos prévios → objetivos → recursos → adaptações → metodologias → **Registro criado. Código: PCR-7K4M2Q. Guarde este código.** (+ QR do código).

### 6.5 Registrar aula
Formulário com os campos da entidade Aula (Seção 4.3). Data pré-preenchida com hoje; horário previsto pré-preenchido pela agenda com [MANTER] [ALTERAR]; frequência escolhida pelo professor (nunca inferida). Conteúdos trabalhados com classificação consolidado/em desenvolvimento/dificuldade. "Registrar aula já realizada" é o mesmo formulário com `tipo_aula = retroativa`.

### 6.6 Histórico
Lista Aula 01… N com data, conteúdo, situação, resumo; abrir qualquer encontro. Campo de busca no histórico: Modo Essencial = busca estruturada (conteúdo, dificuldade, período, situação); Modo Inteligente = pergunta livre interpretada pelo Gemini sobre o histórico (com pseudonimização).

### 6.7 Biblioteca, Pesquisa, Relatórios, Configurações
Descritas nas Seções 9, 11, 12, 14.5. Configurações inclui: perfil do professor, perfis instrumentais editáveis, rubricas, fuso horário, consentimento de envio de trechos à IA, exportar/excluir dados, diagnóstico.

---

## 7. MODOS DE OPERAÇÃO E GEMINI

### 7.1 Modo Essencial (sem Gemini) — obrigatório funcionar por completo
Registros, turmas, histórico, frequência, horários, rendimento, biblioteca, busca textual + BM25, pesquisa acadêmica, BNCC/CRMG, análise musical determinística (music21), geração de aula por modelos pedagógicos (templates + perfis), relatórios por template, gráficos, PDF, DOCX, QR Codes, Drive. Aviso discreto: "Modo Essencial ativo. Alguns recursos avançados de geração e síntese estarão indisponíveis nesta sessão."

### 7.2 Modo Inteligente (com Gemini) — acrescenta
Síntese de pesquisas, interpretação pedagógica do histórico, planejamento contextual, criação avançada de aulas e atividades, adaptação textual, relatórios narrativos, comparação de fontes, justificativa pedagógica, planejamento de progressão, busca semântica por embeddings, busca livre no histórico. O Modo Inteligente **acrescenta**; nunca repara função que deveria existir no Essencial.

### 7.3 Chave (`ai/gemini.py`)
Ordem: 1) `userdata.get("GEMINI_API_KEY")` (Colab Secrets); 2) campo "usar chave apenas nesta sessão" (memória). Nunca no notebook, GitHub, logs, exportações, nem enviada a outro serviço. Se "USAR GEMINI" e nenhuma chave: "Gemini ainda não está configurado. [APRENDER A CONFIGURAR] [CONTINUAR SEM GEMINI]". Chave inválida: "A chave informada não foi aceita pelo Google. Verifique e tente novamente, ou continue em Modo Essencial." Após validar a chave, fazer uma chamada mínima de teste.

### 7.4 Tutorial de configuração (`docs/TUTORIAL_GEMINI.md`, renderizado no app)
Linguagem para leitor de 10 anos, sem termos técnicos não explicados, com passos numerados: abrir Google AI Studio → entrar com conta Google → criar chave → copiar → voltar ao Colab → abrir "Segredos" (ícone da chave na barra lateral) → criar `GEMINI_API_KEY` → colar → ativar "acesso do notebook" → testar no Percurso. Nunca pedir para colar a chave no GitHub. Capturas de tela descritas em texto (sem imagens que envelheçam).

### 7.5 Saída estruturada e validação (`ai/schemas.py`, `ai/validate_loop.py`)
Toda geração usa `response_mime_type="application/json"` + `response_schema` pydantic. Ciclo:
```
Gemini gera → pydantic valida → cronograma somado (Seção 8.2) → habilidades verificadas (Seção 10)
→ fontes verificadas (Seção 11.5) → instrumento coerente com o perfil → apresentar
```
Falha em qualquer etapa → "A resposta não passou pela validação. Tentando corrigir…" → reenvio com o erro específico no prompt → máximo **3 tentativas** → fallback para template do Modo Essencial com aviso. Nunca aceitar silenciosamente resposta malformada. Nunca loop.

### 7.6 Regras de uso do modelo
- Pseudonimização (D7) em todo prompt; mapa código↔nome só em memória.
- Trechos da biblioteca só vão ao modelo com consentimento explícito na sessão: "Permitir que trechos da minha biblioteca sejam enviados à Gemini API para análise? [SIM] [NÃO]". Nunca documentos completos; só os trechos recuperados (máx. definido em `config/gemini.json`).
- Contexto mínimo: resumo pedagógico (não histórico inteiro), últimas 3–5 aulas, estado atual, perfil, trechos relevantes.
- Cache de respostas por hash(prompt) em memória de sessão; evitar reanálise repetida.
- Não usar IA para o que Python resolve: percentuais, somas, códigos BNCC, tonalidade.
- Proibido inventar: rendimento, frequência, autores, artigos, DOI, páginas, habilidades curriculares. Sem fonte: "Não foi localizada uma referência suficiente para sustentar esta afirmação."
- Falha de rede/API: "Gemini não respondeu. Você pode tentar novamente ou continuar em Modo Essencial."

---

## 8. PLANEJAMENTO DE AULA

### 8.1 Entradas
Aluno/turma (carregado do registro), instrumento, idade, nível, duração, objetivo, conteúdo atual, conhecimentos prévios, recursos disponíveis (checklist: quadro, caixa de som, instrumentos, projetor, celulares, impressão, nenhum, outro), contexto, currículo, metodologia, adaptações, observações, tipo (continuidade / revisão / nova unidade / extraordinária), "onde pesquisar" (Seção 11.1).

Fontes automáticas: perfil + estado atual + resumo + últimas aulas + dificuldades + consolidados + objetivos + currículo + biblioteca + perfil instrumental.

Se o professor não indica conteúdo: "O que devo trabalhar agora?" → sistema sugere **"Próximo passo sugerido"** com base em histórico, pré-requisitos, currículo, instrumento, dificuldades e fontes. Nunca como verdade absoluta.

### 8.2 Cronograma (`core/schedule.py`)
Lista de blocos contíguos: `inicio_min` do primeiro = 0; `fim_min` de cada = `inicio_min` do seguinte; `fim_min` do último = duração. Função `validar_cronograma(blocos, duracao)` retorna erro específico (ex.: "soma 57, esperado 50"). **Nenhum plano é apresentado sem passar.**

`adaptar_duracao(blocos, nova_duracao)`: redistribuição proporcional preservando a estrutura (acolhimento, introdução/atividade corporal, exploração, prática, aplicação, avaliação, fechamento), com mínimos por bloco (ex.: fechamento ≥ 2 min), arredondamento e ajuste do resíduo no bloco de prática. Nunca "cortar a última atividade".

### 8.3 Geração no Modo Essencial (`core/planner.py`)
Motor de templates:
1. conteúdo = escolha do professor, ou `proximo_objetivo`, ou próximo item da progressão do perfil instrumental não consolidado;
2. estrutura de cronograma = template por modalidade e duração (`config/defaults.json`);
3. atividades = `tipos_de_exercicios` do perfil para aquele conteúdo, filtradas por recursos e idade;
4. avaliação = rubrica ativa;
5. continuidade = próximo item da progressão;
6. referências = resultados da pesquisa (biblioteca/currículo/acadêmica), se solicitada.
O plano é rotulado "gerado por modelo pedagógico (sem IA)". É útil, não decorativo.

### 8.4 Plano completo (saída)
Tema · Contexto · Faixa etária · Nível · Instrumento · Duração · Objetivo geral · Objetivos específicos · Conhecimentos prévios · Conteúdos · Competências · Habilidades curriculares (validadas) · Recursos · Metodologia · Cronograma · Atividades · Intervenções do professor · Possíveis dificuldades · Adaptações · Avaliação · Critérios · Continuidade · Referências (com origem marcada) · **Justificativa pedagógica** ("Por que esta aula foi estruturada assim?" e "Por que este exercício é adequado ao instrumento e ao estágio?").

Aula extraordinária (ex.: apresentação em 3 semanas com música específica) adapta a sessão e registra `tipo_aula = extraordinaria`, sem alterar unidade/objetivo longitudinal. Nova unidade registra a mudança sem apagar histórico. Revisão prioriza dificuldades recorrentes, conteúdos instáveis, pré-requisitos não consolidados, repertório pendente.

### 8.5 Materiais gerados (sob demanda, nunca obrigatórios)
Folha do professor, folha do aluno, exercícios, rubrica, ficha, lista de repertório → PDF/DOCX; exemplos musicais → MIDI/MusicXML (music21); QR Code do registro. Salvos em `registros/<código>/materiais/`.

---

## 9. BIBLIOTECA DO PROFESSOR

### 9.1 Formatos V1
PDF, DOCX, TXT, MD. (EPUB/XLSX/CSV/PPTX: roadmap.)

### 9.2 Pipeline (`library/ingest.py`)
```
gr.File → validar formato → SHA-256 → duplicado? ("Este documento já está na sua biblioteca.")
→ copiar para biblioteca/arquivos/<sha>.<ext> → extrair texto (PyMuPDF; fallback pypdf; python-docx; leitura direta)
→ dividir em trechos (~500 tokens, sobreposição 80, com página quando houver)
→ salvar biblioteca/texto/<sha>.json → detectar metadados → indexar (incremental) → catálogo
```
PDF sem texto extraível: "Este PDF parece ser digitalizado como imagem. O conteúdo não pôde ser lido." (entra no catálogo marcado `sem_texto`; OCR é roadmap, sempre como fallback). Arquivo corrompido: "Não foi possível processar este arquivo. Os demais documentos continuam disponíveis."

### 9.3 Metadados (`catalogo.json`)
Título, autor, ano, categoria (pedagogia musical, teoria, percepção, harmonia, história, técnica instrumental, repertório, educação infantil, avaliação, currículo, inclusão, metodologia, outros), área, instrumento, nível, tipo de documento, observações, hash, nome original, data de inclusão, páginas, n_trechos, `sem_texto`. Detecção automática (metadados do PDF/DOCX + primeira página); professor corrige.

### 9.4 Interface
MINHA BIBLIOTECA: [ADICIONAR MATERIAL] [PESQUISAR] [VER BIBLIOTECA] [REMOVER MATERIAL]. Remoção pede confirmação e mostra o que será apagado (arquivo, texto, entradas do índice).

### 9.5 Busca (`library/search.py`)
- Textual exata (normalização de acentos, case-insensitive).
- BM25 (`rank_bm25`) sobre trechos, com **expansão de sinônimos pedagógicos** PT/EN vinda do adaptador de domínio (ex.: "desenvolvimento da pulsação" → pulso regular, senso de pulsação, beat perception, internalização métrica, movimento corporal e pulso).
- Semântica por embeddings da API Gemini (Modo Inteligente) — índice separado `indices/biblioteca_emb_gemini.json`, incremental.
- Opt-in local: `sentence-transformers` (multilingual-e5-small) instalado só se o professor pedir na sessão; fallback automático para BM25 se não carregar.
Resultado sempre mostra documento, página, trecho e origem 📚.

### 9.6 Cache de índice (`indices/*.json` + manifesto)
Manifesto: `{hash_por_documento, data_indexacao, metodo, versao_indice, n_trechos}`. Indexação incremental: só documentos novos/alterados. Mudança de versão do índice: "Seu índice precisa ser atualizado. [ATUALIZAR AGORA]". Nunca reprocessar tudo a cada sessão.

### 9.7 Copyright e privacidade
Documentos permanecem privados no Drive do professor; nunca redistribuídos; biblioteca de um professor nunca acessível a outro. Respostas preferem síntese, referência, paráfrase, trechos mínimos. NotebookLM: sem dependência de API não oficial; a mesma pasta pode alimentar o NotebookLM manualmente, se o professor quiser.

---

## 10. BASE CURRICULAR

### 10.1 Escopo V1
- **BNCC**: componente Arte (Música está inserida em Arte) — Ensino Fundamental, unidades temáticas, habilidades com código; Educação Infantil — campos de experiência e objetivos de aprendizagem relacionados a sons/música. Ensino Médio: habilidades de Linguagens relacionadas a Arte.
- **CRMG** (Currículo Referência de Minas Gerais): recorte equivalente (Arte/Música).
- Base **estruturada e validada** em `curriculum/data/bncc_arte.json`, `bncc_infantil.json`, `crmg_arte.json`, transcrita dos documentos oficiais vigentes (obter no momento da implementação), cada arquivo com `{documento, versao, fonte_oficial, url, data_obtencao}`. Nunca enviar BNCC/CRMG como texto livre ao modelo.

Formato de habilidade:
```json
{"codigo": "EF15AR14", "etapa": "EF", "anos": ["1","2","3","4","5"], "componente": "Arte",
 "unidade_tematica": "Música", "objeto": "...", "texto": "...", "musica": true}
```

### 10.2 Validação (`curriculum/validate.py`)
```
código existe? → etapa compatível com o registro? → componente = Arte? → relação com Música? → usar
```
Qualquer código gerado pela IA que falhe é removido do plano e registrado no log; o professor vê "1 habilidade sugerida não foi validada e foi removida".

### 10.3 Vínculo opcional
Referência curricular por registro: BNCC · BNCC + CRMG · Currículo próprio · Curso livre · Conservatório · Nenhuma. Aula instrumental não é obrigada a vincular habilidade. Roadmap: "ADICIONAR MEU DOCUMENTO CURRICULAR" (pasta `curriculo/`).

---

## 11. PESQUISA

### 11.1 Camadas
"Onde pesquisar?" ☑ Minha Biblioteca ☑ Base Curricular ☑ Pesquisa Acadêmica ☐ Pesquisa Externa (desativada na V1; provedor configurável no roadmap). O sistema funciona sem pesquisa web.

### 11.2 Provedores (`research/providers/`)
```
ResearchProvider (base: buscar(consulta) -> [Fonte]; disponivel() -> bool)
├── OpenAlexProvider       (obrigatório; sem chave; usar mailto do proprietário no "polite pool")
├── CrossrefProvider       (obrigatório; sem chave; DOI/metadados/periódicos)
├── GoogleBooksProvider    (obrigatório; sem chave; livros/ISBN/assuntos)
├── SemanticScholarProvider(opcional; ativa se houver chave em Colab Secrets SEMANTIC_SCHOLAR_API_KEY; sem chave, respeita rate limit público)
└── WebSearchProvider      (roadmap; interface definida, sem implementação obrigatória)
```
Falha de um provedor não derruba a pesquisa: "OpenAlex temporariamente indisponível. Continuando com outras fontes." Timeout, retry com `tenacity`, resultados deduplicados por DOI/título normalizado.

### 11.3 Expansão de consultas (`research/expand.py`)
A partir de tema + instrumento + nível, gerar consultas PT e EN via vocabulário do adaptador. Ex.: "flauta doce + articulação + iniciante" → recorder articulation pedagogy · beginner recorder tonguing · flauta doce articulação ensino · recorder teaching children. Todas as consultas realizadas são salvas no plano/aula (`consultas_realizadas`).

### 11.4 Cache (`pesquisas/cache/`)
Chave = hash(consulta normalizada + provedores). Guarda query, provedores, data, resultados. Validade: acadêmica 90 dias (antiga pode permanecer); curricular controlada por versão da base; biblioteca por manifesto do índice.

### 11.5 Rastreabilidade (`research/trace.py`)
Toda fonte apresentada carrega: título, autor, ano, fonte, URL, DOI, página (quando houver), data da consulta, tipo. Tipos marcados na interface: 📚 Minha Biblioteca · 🏛 Fonte curricular oficial · 🎓 Literatura acadêmica · 🌐 Fonte externa. Uma referência só entra num plano se existir em `fontes_utilizadas` com origem verificável (cache, catálogo ou base curricular). O validador (Seção 7.5) rejeita referências que não estejam nesse conjunto.

---

## 12. RELATÓRIOS E EXPORTAÇÃO

### 12.1 Tipos
Frequência · Rendimento · Pedagógico · Completo · Institucional · Para responsáveis. Todos por registro e por período (data inicial/final).

### 12.2 Frequência (`reports/attendance.py`, cálculo em Python, nunca IA)
Período, aulas previstas, realizadas, presenças, faltas, faltas justificadas, reposições, cancelamentos, frequência percentual (presenças + reposições + extras ÷ aulas previstas não canceladas pela instituição — regra documentada em DATA_MODEL.md), tempo total de aula. Tabela: Data | Dia | Previsto | Real | Situação | Duração. Para turmas com lista de alunos: frequência individual por aluno.

### 12.3 Rendimento
Somente dados registrados. Evolução por critério ao longo das aulas; linha por critério.

### 12.4 Pedagógico
Conteúdos trabalhados, conquistas, dificuldades, progressão, repertório trabalhado no período, participação, objetivos atuais, recomendações. Modo Essencial: template estruturado a partir de estado + aulas. Modo Inteligente: narrativa (pseudonimizada, nomes restaurados na saída), sempre marcada "gerado com apoio de IA".

### 12.5 Gráficos (`reports/charts.py`, matplotlib)
Evolução por critério, frequência no período, aulas por mês, desempenho por critério. Sem gráficos decorativos. PNG embutido nos exports.

### 12.6 Exportação
PDF (`reportlab`), DOCX (`python-docx`), Markdown, CSV quando tabular. Salvar em `relatorios/` ou `exportacoes/` e oferecer [BAIXAR] (via `gr.File` de saída) e [ABRIR PASTA] (link do Drive quando possível).

---

## 13. APOIO AO PROJETO (DOAÇÕES)

### 13.1 Regras
Gratuito, sem bloqueio, sem contagem de uso, sem paywall, sem dark patterns: nunca "você já usou 50 vezes", sem contagem regressiva, sem esconder o fechar, sem culpa, sem repetir no mesmo mês.

### 13.2 Mercado Pago
Somente **link público de contribuição** fornecido pelo proprietário (Seção 21), em `config/defaults.json`. Sem Access Token, sem segredo, sem API privada. QR Code gerado com `qrcode` + `Pillow`.

### 13.3 Botão permanente
"♡ Apoiar o Percurso", discreto, sempre visível, nunca interrompe. Abre painel: "Apoie o Percurso" · QR Code "Escaneie com seu celular" · [CONTRIBUIR PELO MERCADO PAGO] · finalidade ("Seu apoio ajuda a financiar: novos recursos · manutenção · expansão para outras áreas · melhoria da biblioteca pedagógica · evolução da plataforma").

### 13.4 Lembrete mensal (`support/donations.py`) — regra exata
Aparece **uma única vez por mês-calendário, na primeira abertura efetiva do Percurso naquele mês**, no fuso configurado (padrão `America/Sao_Paulo`, via `zoneinfo`).
```
abre 01/10 → aparece; abre 02/10 → não; abre 20/10 → não; primeira abertura em novembro (08/11) → aparece
não abriu em novembro → nenhum lembrete; volta em 15/12 → aparece em 15/12
```
Persistência: `configuracoes/apoio.json` = `{"ultimo_mes_lembrete_apoio": "2026-09"}`; comparar com `YYYY-MM` atual; gravar **antes** de exibir (evita repetir se a sessão cair). Texto:
> Ajude o Percurso a continuar crescendo.
> O Percurso é desenvolvido de forma independente e permanece gratuito. Se a ferramenta tem contribuído para seu trabalho, considere apoiar sua manutenção e o desenvolvimento de novos recursos.
> [QR CODE] [APOIAR PELO MERCADO PAGO] [CONTINUAR NO PERCURSO]
> Nenhuma função será bloqueada.

---

## 14. SEGURANÇA E LGPD

### 14.1 Transparência antes de conectar
"O Percurso utilizará uma pasta própria no seu Google Drive para armazenar seus dados pedagógicos e sua biblioteca. Nenhum arquivo fora dessa área será alterado automaticamente."

### 14.2 Escopo de acesso
Código opera exclusivamente em `MyDrive/Percurso/`. Nunca listar ou varrer o Drive fora dela.

### 14.3 Dados de menores — minimização
Identificação recomendada: primeiro nome, iniciais, código ou pseudônimo. Nunca exigir sobrenome. Idade opcional. Campo "adaptações" é texto livre do professor, sem inferência médica pelo sistema. Sem CPF/RG/endereço/dados bancários de ninguém.

### 14.4 Segredos
Chave Gemini: nunca em notebook, repositório, logs, exportações, backups, cache. Logs (`utils/logging.py`) filtram padrões de chave. Diagnóstico exportável nunca inclui segredos nem conteúdo de alunos.

### 14.5 Direitos (tela Configurações → Privacidade)
[EXPORTAR MEUS DADOS] (zip de `Percurso/` ou de um registro) · [EXCLUIR REGISTRO] · [EXCLUIR BIBLIOTECA] · [APAGAR DADOS LOCAIS] (limpa `/content` e memória de sessão). Antes de excluir: "Tem certeza?" + lista exata do que será removido. Exclusão de registro cria backup em `backups/` por 30 dias (documentado), depois pode ser removido pelo professor.

### 14.6 Envio à IA
Só com Gemini ativo na sessão; sempre pseudonimizado (D7); trechos da biblioteca só com consentimento da sessão (Seção 7.6); nunca documentos completos.

---

## 15. RESILIÊNCIA, LOGS, DESEMPENHO E CUSTOS

- Uma falha nunca destrói a sessão. Toda operação externa (Drive, APIs, Gemini, extração) tem try/except com mensagem PT-BR e caminho de continuidade.
- Logs técnicos em `/content/percurso.log` (runtime) e opcionalmente `Percurso/configuracoes/diagnostico.log` rotativo (≤ 1 MB); botão DIAGNÓSTICO mostra as últimas linhas. Sem chaves, sem conteúdo sensível.
- Desempenho: estado resumido em vez de histórico inteiro; cache por hash; indexação incremental; nunca reinstalar dependências já presentes; `pip install -q` só do que falta.
- Custos de IA: contexto mínimo, trechos e não documentos, cache de sessão, sem repetição de análise. "Modo econômico / completo" só se trouxer benefício real (decisão do agente, documentada).
- Timeouts: Gemini 60 s; APIs de pesquisa 15 s; retries com backoff (`tenacity`), máximo 3.

---

## 16. TESTES

### 16.1 Infraestrutura
`pytest`; `PERCURSO_BASE_PATH` aponta para `tmp_path`; `platform/local.py` substitui o Colab; `tests/mocks/gemini.py` (cliente falso com respostas válidas, inválidas e falha de rede); `tests/mocks/providers.py` (respostas gravadas em `fixtures/`); fixtures: 1 PDF com texto, 1 PDF só imagem, 1 PDF corrompido, 1 DOCX, 1 MD; registro de exemplo com 14 aulas; dados em schema v0 para migração.
Todos os testes rodam localmente sem rede (rede é mockada). Testes de integração com APIs reais ficam marcados `@pytest.mark.online` e são opcionais.

### 16.2 Casos obrigatórios (mapeados da v1 §118)
| # | Caso | Esperado |
|---|------|----------|
| 1 | Primeira abertura sem pasta Percurso | estrutura criada, versão gravada |
| 2 | Nova sessão com pasta existente | dados recuperados sem alteração |
| 3 | Gemini desativado | todas as funções do Modo Essencial operam |
| 4 | Gemini ativado com chave válida (mock) | funções inteligentes disponíveis |
| 5 | Gemini ativado sem chave | tutorial ou continuar sem Gemini |
| 6 | Chave inválida | erro amigável, sem traceback |
| 7 | Upload de PDF | extração, indexação, catálogo, persistência |
| 8 | Upload duplicado | não duplica, mensagem correta |
| 9 | Criar registro | código único, formato válido, sem colisão |
| 10 | Fechar e reabrir | código → histórico e estado recuperados |
| 11 | Gerar segunda aula | plano usa estado anterior (conteúdos consolidados não reaparecem como novos) |
| 12 | Frequência | percentuais corretos, incluindo canceladas e reposições |
| 13 | Cronograma | soma exata; adaptação de duração mantém estrutura |
| 14 | Relatório | PDF e DOCX abrem e contêm os dados |
| 15 | Lembrete de apoio | 1ª abertura do mês mostra; 2ª não; novo mês mostra; fuso respeitado |
| 16 | API acadêmica fora do ar | fallback para demais provedores |
| 17 | Arquivo corrompido | erro sem quebrar; demais documentos disponíveis |
| 18 | Histórico antigo | migração sem perda, backup criado |
| 19 | Pseudonimização | nenhum nome de aluno em prompt enviado ao mock |
| 20 | Validação de habilidade | código inexistente/etapa errada é rejeitado |
| 21 | Referência inventada pelo mock | plano rejeitado e reenviado; após 3 falhas, fallback |
| 22 | Numeração de aulas | registro retroativo reordena corretamente |

### 16.3 Testes manuais reais (no Colab, antes de cada entrega ao beta)
- **Piano**: aluno de 10 anos, semanal, 50 min, iniciante. Três aulas sequenciais com frequência, dificuldade, rendimento e continuidade. Fechar runtime, reabrir, recuperar pelo código, gerar a 4ª aula. Confirmar continuidade verdadeira.
- **Turma**: Percepção Musical, 16 alunos, 45 min, três encontros, relatório de frequência e pedagógico.
- **Biblioteca**: adicionar PDF e DOCX, pesquisar conceito, confirmar resultado + fonte + persistência após nova sessão.
- **Gemini**: comparar Modo Essencial × Modo Inteligente na mesma aula; o primeiro deve ser útil, o segundo deve acrescentar.

---

## 17. ORDEM DE ENTREGAS (V1)

Nenhuma funcionalidade da v1 é excluída; a ordem garante que cada entrega seja utilizável. Cada entrega termina com testes verdes, teste manual no Colab e relatório da Seção 19.4.

### E1 — Núcleo (Modo Essencial)
Bootstrap do notebook · platform colab/local · storage com escrita atômica · estrutura do Drive · onboarding e perfil do professor · registros e códigos (individual, dupla, turma) · registrar aula (inclusive retroativa) · frequência · rendimento com rubrica · estado atual e resumo (determinísticos) · histórico com busca estruturada · continuidade por template + perfis instrumentais de todos os instrumentos da Seção 1.4 · cronograma com validação e adaptação · aula extraordinária, revisão, nova unidade · repertório · botão de apoio, QR, lembrete mensal · LGPD (exportar/excluir) · migração base · README inicial.
**Aceite:** critérios 1–5, 7–17, 25–27 da Seção 19.3, sem Gemini. O beta pode começar aqui.

### E2 — Modo Inteligente
Chave via Secrets e sessão · tutorial · schemas pydantic · ciclo de validação · pseudonimização · consentimento de trechos · plano contextual · resumo narrativo · busca livre no histórico · proposta de classificação do estado.
**Aceite:** critérios 6 e 17 com Gemini; casos 4–6, 19, 21.

### E3 — Biblioteca
Upload PDF/DOCX/TXT/MD · hash e duplicidade · extração · trechos · metadados · catálogo · busca textual + BM25 com expansão · índice incremental e manifesto · embeddings Gemini (se E2) · opt-in sentence-transformers · remoção.
**Aceite:** critérios 18–19; casos 7, 8, 17.

### E4 — Currículo e pesquisa acadêmica
Bases BNCC (Arte + EI) e CRMG estruturadas · validação de habilidades · vínculo opcional · provedores OpenAlex, Crossref, Google Books (+ Semantic Scholar opcional) · expansão PT/EN · cache · rastreabilidade · "onde pesquisar" integrado ao planejamento.
**Aceite:** critérios 20–21; casos 16, 20.

### E5 — Relatórios, exportação e fechamento
Relatórios (6 tipos) · gráficos · PDF/DOCX/MD/CSV · materiais (folhas, fichas, MIDI/MusicXML) · diagnóstico · docs finais (ARCHITECTURE, DATA_MODEL, TESTING, TUTORIAL_PROFESSOR) · README completo · badge Open in Colab · relatório de entrega.
**Aceite:** critérios 22–24; casos 12–14; todos os 27 critérios verificados de ponta a ponta.

### 17.1 Roadmap pós-V1 (registrar em docs/ROADMAP.md, não implementar)
Imagem de partitura (verovio) · OCR fallback · EPUB/XLSX/PPTX · pesquisa web configurável · SQLite como cache · documento curricular próprio · frequência individual avançada em turma · aplicação web, login, banco remoto, múltiplos dispositivos · painel institucional · Google Calendar/Classroom · NotebookLM (se API oficial) · outros componentes curriculares (Matemática, Português, Ciências, História, Geografia, Educação Infantil) · versão para escolas · app móvel · assinatura · Mercado Pago automatizado · dashboards · acompanhamento de responsáveis.

### 17.2 Não fazer agora
Servidor obrigatório, SaaS, login central, banco central, paywall, cobrança, app Android/iOS, infraestrutura além de GitHub + Colab + Drive.

---

## 18. DEPENDÊNCIAS (V1)

Obrigatórias: `gradio`, `pydantic>=2`, `pandas`, `numpy`, `PyMuPDF`, `pypdf`, `python-docx`, `rank-bm25`, `music21`, `matplotlib`, `reportlab`, `qrcode`, `Pillow`, `httpx`, `tenacity`, `google-genai`.
Opcionais (instaladas sob demanda): `sentence-transformers`, `faiss-cpu`.
Excluídas da V1: `ipywidgets` (só o que o Colab já traz), `openpyxl`, `pretty_midi`, `librosa`, `pydub`.
Fixar versões em `requirements.txt` **somente após testar no Colab atual**; registrar a data do teste no README.

---

## 19. DOCUMENTAÇÃO E ENTREGA

### 19.1 Para professores
`docs/TUTORIAL_PROFESSOR.md` (também renderizado numa aba "Ajuda" do app): Primeiros passos · Cadastrar aluno · Continuar aula · Adicionar materiais · Pesquisar · Gemini · Frequência · Relatórios · Apoiar o projeto · Privacidade · Solução de problemas.

### 19.2 README
O que é o Percurso · badge Open in Colab (apontando para `Percurso.ipynb`) · requisitos · como conectar o Drive · como configurar Gemini · como usar sem Gemini · cadastrar aluno · recuperar por código · adicionar documentos · gerar aula · frequência · relatório · apoiar · privacidade · solução de problemas · data do último teste no Colab.

### 19.3 Critérios de aceitação final (proprietário)
1. abrir o GitHub · 2. clicar em Open in Colab · 3. inicializar · 4. conectar o Drive · 5. usar sem Gemini · 6. opcionalmente ativar Gemini · 7. criar aluno · 8. receber código · 9. elaborar aula · 10. registrar frequência · 11. registrar rendimento · 12. fechar · 13. abrir outro dia · 14. digitar o código · 15. receber imediatamente o resumo da última aula · 16. escolher continuar · 17. receber aula realmente baseada no histórico · 18. pesquisar meus PDFs · 19. adicionar novos documentos · 20. pesquisar fontes acadêmicas · 21. utilizar BNCC/CRMG corretamente · 22. gerar relatório · 23. exportar PDF/DOCX · 24. visualizar gráficos · 25. receber lembrete de apoio apenas uma vez por mês · 26. acessar QR Code do Mercado Pago · 27. fazer tudo isso sem editar Python.

### 19.4 Relatório de entrega (por entrega e ao final)
O que foi desenvolvido · como abrir · como testar · configuração do Drive · configuração do Gemini · biblioteca · cadastro de aluno · continuidade · relatórios · Mercado Pago · dependências · **limitações conhecidas** · testes realizados (com evidência) · melhorias recomendadas.

### 19.5 Documentação técnica
`docs/ARCHITECTURE.md`, `docs/DATA_MODEL.md` (inclui regras de cálculo de frequência e de estado), `docs/TESTING.md`, `docs/ROADMAP.md`. Segurança e pesquisa ficam como seções de ARCHITECTURE.md.

---

## 20. MELHORIAS PROPOSTAS PELO AGENTE (FORMATO)

```
MELHORIA PROPOSTA
Problema: ...
Mudança: ...
Benefício: ...
Impacto: ...
Compatível com os requisitos atuais? Sim/Não
```
Decisão interna de implementação → executar sem interromper. Remoção ou alteração de requisito → explicar primeiro e aguardar.

---

## 21. INFORMAÇÕES DO PROPRIETÁRIO (PREENCHER ANTES DE INICIAR)

| Item | Valor |
|------|-------|
| Conta/repositório GitHub | `github.com/________/Percurso` |
| Link público de contribuição Mercado Pago | `https://link.mercadopago.com.br/________` |
| Logotipo | ( ) não há — usar tipografia   ( ) anexo em `assets/` |
| E-mail/canal de contato exibido no app | `________` (opcional) |
| E-mail para o polite pool do OpenAlex | `________` |
| BNCC: usar versão oficial vigente | ( ) sim |
| CRMG: versão a usar | `________` (confirmar vigência) |
| Documentos de teste para a biblioteca | ( ) fornecerei PDFs/DOCX   ( ) usar fixtures próprias |
| Fuso horário padrão | `America/Sao_Paulo` |
| Chave Gemini | **não informar aqui** — Colab Secrets: `GEMINI_API_KEY` |

---

## 22. PRINCÍPIO PEDAGÓGICO FINAL

Ensinar não consiste em produzir aulas isoladas. Cada encontro pertence a uma trajetória. O sistema preserva memória, contexto, continuidade, adaptação, progressão, registro e reflexão. O histórico não é documentação: ele modifica o planejamento futuro.

O Percurso é um produto real cuja primeira interface de distribuição é o Google Colab — nunca "apenas um notebook".

O resultado esperado não é uma demonstração. É a primeira versão funcional do **Percurso — Plataforma de inteligência pedagógica**.
