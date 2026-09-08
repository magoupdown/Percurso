# Evidência de validação

Ambiente: Python 3.12; Gradio 6.26.0. Dados sintéticos em diretórios temporários. Testes online excluídos pelo próprio projeto. As dependências instaladas neste ambiente não representam nova homologação do arquivo de versões do Colab.

## Resultado automatizado

Comando: `python -m pytest -q`.

Resultado: **121 passed, 1 deselected**. Linha de base: **103 passed, 1 deselected**. Foram acrescentados 18 casos executados, incluindo parametrizações. Os testes cobrem troca de aluno, recarga do mesmo registro, falha de recuperação, revogação de Gemini, escape de HTML, busca textual, concorrência de temporários, falha de validação, exportações cumulativas, caminhos de perfis, nome de turma e limpeza do formulário com frequência explícita.

`git diff --check`: sem erro de espaços em branco. Notebook validado como JSON; células Python compiladas sem execução de acesso ao Drive.

## Verificação da aplicação

| Verificação | Resultado |
|---|---|
| Composição de todas as telas | Passou no teste de montagem |
| Inicialização do servidor Gradio | Passou |
| Resposta HTTP do servidor em `/config` | 200 |
| Fluxo do núcleo: criar, planejar, registrar, recuperar estado | Passou na suíte existente |
| Fluxo visual com cliques | Pendente |
| Console do navegador | Pendente |
| Captura desktop e mobile | Pendente |
| Comparação entre conceito e aplicação renderizada | Pendente |
| Colab e Drive autenticados | Não executado nesta revisão |
| Gemini e pesquisa acadêmica ao vivo | Não executado; mocks na suíte |

O navegador integrado estava disponível, mas rejeitou a URL local com `ERR_BLOCKED_BY_CLIENT`. O fallback Playwright encontrou ausência do executável Chromium; o download sofreu timeouts. Não foram usados capturas falsas, uma imagem como substituta da interface ou resultados simulados como evidência de funcionamento visual.

## Referência visual e registro de fidelidade

Conceito criado em `generated_images/exec-9545f26d-c1b1-4aab-b7fa-58ab81ecdbe0.png`, fora do pacote de código. Essa imagem foi exibida na conversa. Ela é uma proposta visual, não um screenshot do produto.

| Dimensão | Implementado no código | Estado da comparação renderizada |
|---|---|---|
| Hierarquia | Identidade, ações principais, utilidades, Gemini, primeiros passos | Pendente |
| Tipografia | Georgia editorial e fontes locais de interface | Pendente |
| Paleta | Branco, cinza claro, verde e texto escuro | Pendente |
| Espaçamento | Faixas abertas, áreas de ação amplas, divisórias discretas | Pendente |
| Controles | Botões nativos, foco visível, alturas mínimas | Pendente |
| Textos | Ações principais equivalentes ao conceito; rótulos existentes mantidos nas outras telas | Inspeção de código apenas |
| Responsividade | Empilhamento abaixo de 720 px; rolagem em tabelas | Pendente em 390 × 844 |

Diferenças intencionais: rótulos tradicionais das abas preservados onde o projeto já os define; lembrete mensal aparece quando devido, embora ausente do conceito; formulários usam fonte sans-serif para legibilidade; consentimento e campo de senha aparecem conforme a sessão. Não foi executado diff visual dos textos acima da dobra. Não há afirmação de fidelidade visual concluída.

## Como revisar no Colab

1. Abra `Percurso_Revisao.ipynb` na branch `melhoria/experiencia-e-integridade`, em uma sessão nova.
2. Execute as duas células. A instalação usa a branch de revisão em `/content/Percurso_Revisao`.
3. Continue sem Gemini, crie dois registros de teste e anote os códigos.
4. Gere um plano para o primeiro. Troque para o segundo e confirme que o plano e as observações anteriores não aparecem.
5. Gere o plano do segundo e escolha registrar a partir dele. O formulário deve receber os conteúdos corretos. Selecione a frequência explicitamente.
6. Salve, recupere pelo código, confira o histórico e gere a próxima aula.
7. Teste a busca digitando um nome sem acento e parte do instrumento.
8. Exporte os dados duas vezes e confirme que a segunda exportação não contém a primeira.
9. Avalie as telas com teclado, em notebook e celular, antes de integrar à branch principal.

A revisão usa a mesma pasta de dados do Drive. A branch separa o código, não cria uma cópia dos dados pedagógicos. Para testar sem afetar registros reais, crie registros fictícios.

## Ajuste de alinhamento e ajuda contextual

Após o feedback com a captura de tela: a orientação de identificação foi movida para abaixo da linha compartilhada com idade. Os dois campos ficam sem alturas diferentes de texto auxiliar. Foram acrescentados tutorial de cadastro, orientação Gemini junto à ativação e ao campo de senha, e configuração do link público Mercado Pago com tutorial, persistência e atualização do QR Code.

A API de imagem foi corrigida para o Gradio 6.26 (`buttons=[]`). Resultado desta atualização: **124 passed, 1 deselected**. Os três novos testes verificam persistência/validação do link, QR distinto ao trocar o endereço e atualização do callback da tela de apoio, incluindo remontagem com link já configurado. `git diff --check` passou.

A imagem fornecida foi inspecionada diretamente. O alinhamento foi corrigido no código com base nessa evidência; não há nova captura renderizada, pois permanece a limitação do navegador registrada acima. Os tutoriais apontam para as páginas oficiais do Google e Mercado Pago consultadas nesta atualização.
