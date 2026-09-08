# Percurso: revisão técnica e de experiência

Data: 08/09/2026. Referência solicitada: `93b098d`. Base de implementação: `e2b46b7`, revisão mais recente obtida do repositório. A versão posterior já contém ajustes de proxy do Colab e documentação de dependências; esses ajustes foram preservados. Esta revisão não representa homologação em produção.

## Parecer

O principal valor do Percurso é a continuidade pedagógica baseada no histórico. A separação entre núcleo determinístico, persistência, domínio musical, interface e IA é adequada à primeira versão individual no Colab. Não há razão técnica demonstrada para substituir esse conjunto por um SaaS ou mudar de linguagem nesta etapa.

A experiência original, porém, apresenta muitas ações com peso semelhante e coloca decisões auxiliares antes da tarefa principal. Além disso, testes do núcleo não detectavam falhas na passagem de contexto entre telas. O investimento prioritário deve ser tornar confiável o ciclo carregar aluno, planejar, registrar e recuperar. A aparência precisa expressar essa continuidade sem encobrir problemas de estado.

A análise examinou notebook, empacotamento, composição da aplicação, sessão, telas principais, armazenamento, anonimização, biblioteca semântica e testes. Não é uma auditoria exaustiva de segurança nem uma validação pedagógica de todos os perfis e fontes curriculares.

## Problemas e intervenções

| Prioridade | Evidência no código anterior | Consequência | Intervenção |
|---|---|---|---|
| Alta | `Sessao._montar_contexto` substituía contexto sem limpar plano e formulário | Plano do aluno anterior podia aparecer no registro seguinte | Limpeza de plano, formulário, mapa de pseudônimos e cache somente quando muda o código |
| Alta | Campos de avaliação e observações ausentes de `saidas_preencher` | Informações anteriores permaneciam no formulário | Reinicialização explícita desses campos e teste da correspondência entre componentes e retornos |
| Alta | Frequência individual iniciava em `presente`; turma era pré-selecionada inteira | Presença podia ser registrada sem escolha consciente | Frequência sem valor inicial, lista vazia e validação obrigatória antes de salvar |
| Alta | Dois callbacks independentes no botão de registrar a partir de um plano | Navegação podia antecipar o preenchimento; falha podia abrir outro formulário | Encadeamento por sucesso, seguido da atualização explícita do formulário |
| Alta | Mensagens e nome do aluno interpolados em HTML | Marcação fornecida podia ser interpretada | Escape de texto, regiões `status` e `alert`, testes com conteúdo de marcação |
| Alta | Identificador do perfil instrumental virava caminho sem validação | Entrada inadequada podia apontar fora da pasta prevista | Validação do identificador e do caminho resolvido |
| Média | Nome fixo de arquivo temporário na gravação atômica | Escritas concorrentes disputavam o mesmo `.tmp` | Arquivo temporário exclusivo no mesmo diretório, validação e substituição atômica preservadas |
| Média | Exportação percorria exportações anteriores | Crescimento cumulativo do ZIP | Exclusão da pasta de exportações e dos logs; dados pedagógicos preservados |
| Média | Desativar Gemini mantinha chave e consentimento na sessão | Desativação incompleta | Método único para limpar credenciais, consentimento e cache |
| Média | Dois caminhos distintos de pseudonimização | Nome próprio da turma não era coberto pelo método da sessão | Reutilização de `Pseudonimizador` existente |
| Média | Recuperação dependia de código ou lista extensa | Atrito para o professor com muitos alunos | Busca por nome, código e instrumento, independente de acentos e caixa |
| Média | Navegação por botão não atualizava explicitamente as telas de destino | Cabeçalhos e formulários podiam ficar desatualizados | Atualização encadeada nos atalhos principais |
| Média | `gradio>=4` aceitava versões incompatíveis com a API de lançamento usada | Instalação aparentemente válida podia falhar ao abrir | Faixa `>=6.26,<7` e constraints testadas pelo projeto no bootstrap |
| Média | `git pull` ignorava erro e instalação não aplicava requirements fixados | Abertura podia usar código antigo sem indicar o problema | Atualização fast-forward verificada e mensagem de falha mais precisa |
| Média | Exceção genérica era exibida com trecho da mensagem técnica | Dados ou detalhes internos podiam aparecer ao professor | `gr.Error` com mensagem de produto e log do tipo de exceção no wrapper compartilhado |

A fila usa um grupo de concorrência comum para os callbacks desta instância individual, reduzindo disputa entre troca de contexto e gravação. Isso não constitui suporte a múltiplos professores em um servidor compartilhado. O teste concorrente da escrita comprova integridade do JSON e ausência de colisão de temporários; não comprova transações entre múltiplos arquivos nem durabilidade adicional do Google Drive.

## Funcionalidades preservadas

Colab e Drive, Gradio, registros individuais e turmas, planejamento determinístico, Gemini opcional, classificação de conteúdos, frequência, rendimento, histórico, biblioteca, pesquisa, referências curriculares, relatórios, exportações, materiais musicais e apoio voluntário. Não foi alterada a fórmula pedagógica de progressão nem a base curricular.

## Direção de interface

A tela inicial passa a apresentar identidade, continuidade do trabalho, ferramentas auxiliares, Gemini opcional e primeiros passos. As três ações principais ficam próximas e com maior área de interação. A decisão de usar IA continua disponível em cada sessão, sem impedir o Modo Essencial. O lembrete mensal de apoio permanece funcional.

Sistema visual implementado: branco `#ffffff`, áreas de trabalho `#f7f9f8`, verde `#146c60`, texto `#203b35`, divisórias `#d5e1dd`. Georgia nos títulos e ações editoriais; Segoe UI/Arial nos formulários. A fonte não exige download externo. Controles com altura mínima de 44 px, foco visível, avisos com texto e semântica e respeito à preferência por movimento reduzido. No CSS, ações empilham abaixo de 720 px e tabelas admitem rolagem própria.

Essas escolhas foram implementadas, mas conformidade de acessibilidade e qualidade responsiva dependem de inspeção visual e navegação real, ainda pendentes. O conceito gerado é uma referência de design, não uma captura da aplicação funcionando.

## Verificação

- Linha de base: 103 testes aprovados, 1 teste online excluído pela configuração do projeto.
- Resultado final e ambiente: consultar `VALIDACAO_REVISAO.md`.
- Servidor real Gradio iniciado localmente; `/config` respondeu HTTP 200 no mesmo processo de teste.
- Nenhuma chave Gemini, conta de professor ou dado real de aluno foi utilizado.
- O navegador integrado rejeitou `http://127.0.0.1:7860` com `ERR_BLOCKED_BY_CLIENT`.
- A alternativa Playwright foi preparada; o navegador Chromium não estava instalado e seu download sofreu timeout. Não há captura renderizada para atestar fidelidade ao conceito, nem validação visual concluída.
- Drive/Colab autenticados, Gemini ao vivo e APIs acadêmicas não foram exercitados nesta revisão. Testes existentes usam mocks nesses pontos. A informação anterior do repositório sobre teste no Colab não é uma execução realizada aqui.

## Limites e próximos critérios de qualidade

1. Homologar no Colab real o fluxo de três aulas de piano e três encontros de turma, incluindo fechar runtime, recuperar e planejar novamente. O plano futuro precisa reagir às evidências anteriores.
2. Inspecionar o layout em 1504 × 1045, 1366 × 768 e 390 × 844, sem corte de botões, com navegação por teclado e retorno visível das ações. Comparar tipografia, hierarquia, espaçamento, cor e textos com o conceito.
3. Revisar armazenamento de rascunhos de formulários. Neste momento, campos não salvos não têm recuperação garantida após navegação ou encerramento do runtime.
4. Validar o significado do consentimento da busca semântica: a indexação remota atual envia todos os trechos indexáveis em lotes. O produto precisa distinguir esse envio da análise pontual de trechos recuperados. Não apresentar pseudonimização por nomes cadastrados como garantia de anonimização de qualquer texto livre.
5. Revisar sistematicamente os demais logs e limites de upload; a correção no wrapper compartilhado não equivale a auditoria de todas as mensagens e integrações.
6. Manter uso individual por instância. Uma versão compartilhada exigiria isolamento por usuário, autenticação e autorização de arquivos antes da disponibilização pública.
7. Fazer revisão pedagógica dos 22 perfis com professores dos instrumentos correspondentes. Validar progressões, tessituras e adequação etária com evidência, sem medir qualidade apenas pelo número de funcionalidades.
8. Acompanhar tempo até recuperar aluno, tempo para registrar uma aula, taxa de conclusão e incidentes de recuperação de dados. Coletar feedback dos professores antes de ampliar o escopo.

## MELHORIA PROPOSTA

Problema: a promessa de uma experiência excepcional não possui critérios mensuráveis de homologação.

Mudança: adotar os cenários de continuidade, integridade, acessibilidade e revisão pedagógica acima como critérios de liberação.

Benefício: qualidade verificável na rotina do professor.

Impacto: mantém a arquitetura atual e exige uma etapa explícita de avaliação antes da promoção desta revisão à versão principal.

Compatível com os requisitos atuais? Sim.

## Edição, reset e confirmação de chave (08/09/2026)

Nova aba **Editar e resetar** com edição de cadastro, nomes dos integrantes da turma,
aulas e planos ainda não realizados. Restaurar campos relê o item salvo; não remove
histórico. Reset permite remover aula/plano, zerar histórico preservando cadastro,
ou excluir o cadastro completo. Exige revisão, código digitado e seleção inalterada.
Cada mutação gera backup com identificador único. Alunos com frequência histórica
não podem ser removidos da lista da turma; seus nomes podem ser corrigidos mantendo
os IDs. Alterações invalidam os formulários da sessão ativa. Documentos previamente
exportados e resumos escritos pelo professor não são reescritos automaticamente.

Mudança de data da aula grava o novo arquivo antes de remover o anterior. Planos
realizados são corrigidos pela aula correspondente; remover a última aula vinculada
libera o plano novamente. Alterar duração de plano reajusta seu cronograma.

O retorno do Gemini permanece visível após conectar. O sucesso só é apresentado
após a chamada de teste ao Google. Informa se a chave está somente em memória ou
foi obtida da configuração de segredos do ambiente. O aplicativo não grava a chave.
No Colab, salve GEMINI_API_KEY nos Segredos e habilite acesso ao notebook para não
precisar colá-la em cada sessão. Há controles de trocar chave e desconectar.
