# Percurso

**Plataforma de inteligência pedagógica.** *Cada aula começa de onde a anterior terminou.*

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/________/Percurso/blob/main/Percurso.ipynb)

O Percurso não é um gerador de planos de aula. É um sistema de **memória pedagógica longitudinal**: cada aula é registrada, o estado do aluno é atualizado, e o planejamento seguinte parte exatamente de onde o anterior terminou. Primeira especialização: Música (piano, violão, flauta doce, canto, coral, percussão, percepção musical e mais 15 áreas). Gratuito, sem paywall.

## Requisitos

- Uma conta Google (para o Colab e o Drive).
- Nada para instalar no computador. Funciona no celular, mas é mais confortável em tela maior.
- Opcional: uma chave gratuita do Gemini (veja abaixo).

## Como abrir

1. Clique no botão **Open in Colab** acima.
2. Execute a célula **▶ Inicializar Percurso** (uma vez por sessão).
3. Execute a célula **▶ Abrir Percurso**. O Colab pedirá permissão para acessar o Drive: aceite. O Percurso usa **apenas** a pasta `Meu Drive/Percurso`.
4. A interface aparece abaixo da célula.

Se a célula 1 falhar por rede, aguarde alguns segundos e execute de novo. Não é preciso usar Git ou terminal.

## Como conectar o Drive

O popup de autorização é do próprio Colab. Depois de autorizar, o Percurso cria a estrutura `Percurso/` (configurações, registros, biblioteca, índices, relatórios, exportações, backups) e mostra "Drive conectado ✓ · Estrutura criada ✓". Nas próximas vezes: "Seus dados foram recuperados ✓".

## Usar sem Gemini (Modo Essencial)

Tudo funciona sem IA: registros, turmas, histórico, frequência, rendimento por rubrica, estado pedagógico, planejamento por modelos pedagógicos (perfis instrumentais editáveis), cronograma validado, aula extraordinária/revisão/nova unidade, repertório, exportação de dados, lembrete de apoio. Os planos são rotulados "gerado por modelo pedagógico (sem IA)".

## Configurar o Gemini (opcional)

Passo a passo na aba **Ajuda → Configurar o Gemini** (ou [docs/TUTORIAL_GEMINI.md](docs/TUTORIAL_GEMINI.md)). Resumo: crie uma chave no Google AI Studio, guarde-a nos **Segredos** do Colab com o nome `GEMINI_API_KEY` e ative "Acesso do notebook". Nunca cole a chave no notebook nem no GitHub. Nomes de alunos nunca são enviados ao Gemini.

## Cadastrar aluno e recuperar por código

**Novo registro** → preencha identificação (só primeiro nome ou iniciais), instrumento, nível e agenda → **CRIAR REGISTRO** → guarde o código `PCR-XXXXXX` (há um QR Code). Em qualquer sessão: **Continuar** → digite o código → **CARREGAR** → o painel mostra onde o aluno parou e o próximo passo sugerido.

## Gerar aula, registrar frequência e rendimento

**Planejar aula** → (opcional) "O que devo trabalhar agora?" → **GERAR PLANO**. O plano traz objetivos, cronograma que fecha na duração exata, atividades do perfil do instrumento, avaliação, continuidade e justificativa pedagógica. **REGISTRAR AULA A PARTIR DESTE PLANO** pré-preenche o formulário. Em **Registrar aula**, marque a frequência (nunca inferida), classifique cada conteúdo como consolidado / em desenvolvimento / dificuldade e dê notas de 1 a 5 só no que observou.

## Adicionar documentos, pesquisar, relatórios

Entregas E3–E5 (biblioteca com PDF/DOCX/TXT/MD e busca BM25; pesquisa acadêmica OpenAlex/Crossref/Google Books; BNCC/CRMG; relatórios PDF/DOCX com gráficos). Consulte a seção **Estado das entregas** abaixo.

## Apoiar

Botão **♡ Apoiar o Percurso** com QR Code do Mercado Pago. Lembrete uma vez por mês, na primeira abertura do mês. Nenhuma função é bloqueada.

## Privacidade

- O código opera exclusivamente em `Meu Drive/Percurso/`.
- Identificação mínima de alunos; nunca CPF, RG, endereço, dados bancários.
- **Configurações → Privacidade**: exportar todos os dados (zip), excluir registro (backup por 30 dias), excluir biblioteca, apagar dados locais da sessão.
- Chave Gemini nunca gravada, logada, exportada ou enviada a outro serviço.

## Solução de problemas

Veja [docs/TUTORIAL_PROFESSOR.md](docs/TUTORIAL_PROFESSOR.md) → "Solução de problemas" e o botão **DIAGNÓSTICO** em Configurações.

## Para desenvolvedores

```bash
pip install -e ".[dev]"
pytest
```

Os testes rodam sem rede (`PERCURSO_BASE_PATH` → pasta temporária; Colab substituído por `platform/local.py`). Documentação técnica em `docs/` (ARCHITECTURE, DATA_MODEL, TESTING, ROADMAP). Especificação completa em [SPEC.md](SPEC.md).

## Estado das entregas

| Entrega | Escopo | Estado |
|---|---|---|
| E1 | Núcleo (Modo Essencial) | concluída · 59 testes verdes |
| E2 | Modo Inteligente (Gemini) | em desenvolvimento |
| E3 | Biblioteca | pendente |
| E4 | Currículo e pesquisa acadêmica | pendente |
| E5 | Relatórios, exportação e fechamento | pendente |

**Último teste no Colab:** ainda não realizado (versões de dependências não fixadas, conforme SPEC §18).
