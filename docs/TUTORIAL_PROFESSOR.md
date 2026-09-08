# Tutorial do professor

O Percurso guarda a **memória pedagógica** de cada aluno ou turma: o que foi trabalhado, o que consolidou, o que ainda está em desenvolvimento e o que deve acontecer na próxima aula. Ele funciona dentro do Google Colab e grava tudo numa pasta própria no seu Google Drive chamada **Percurso**.

## Primeiros passos

1. Abra o notebook `Percurso.ipynb` no Colab (botão **Open in Colab** no GitHub).
2. Execute a célula **Inicializar Percurso**. Espere a mensagem "✓ Percurso pronto".
3. Execute a célula **Abrir Percurso**. O Colab pedirá permissão para acessar o seu Drive. Aceite.
4. A interface aparece logo abaixo da célula. Na primeira vez, ela pergunta se você quer usar o Gemini. Pode escolher **CONTINUAR SEM GEMINI**: tudo funciona.

Cada vez que você abre o Colab é uma nova sessão. Seus dados estão sempre no Drive; nada se perde ao fechar.

## Cadastrar aluno ou turma

1. Aba **Novo registro**.
2. Escolha o tipo (individual, dupla ou turma), a identificação (só o primeiro nome, iniciais ou um apelido), o instrumento ou área, o nível e a agenda.
3. Clique em **CRIAR REGISTRO**. Aparece um **código** como `PCR-7K4M2Q` e um QR Code.
4. **Guarde o código.** É com ele que você volta a esse aluno em qualquer sessão. O código não revela nome, idade nem instrumento.

## Continuar de onde parou

1. Aba **Continuar**. Digite o código (pode ser sem hífen e em minúsculas) e clique em **CARREGAR**.
2. O painel mostra onde o aluno estava: última aula, consolidado, em desenvolvimento, última observação e o **próximo passo sugerido**.
3. Escolha: **CONTINUAR DE ONDE PARAMOS**, **FAZER REVISÃO**, **CRIAR NOVA AULA (nova unidade)** ou **AULA EXTRAORDINÁRIA**. Todas levam à aba **Planejar aula** com o tipo já escolhido.

## Planejar uma aula

1. Aba **Planejar aula**. Se não souber o que trabalhar, clique em **O QUE DEVO TRABALHAR AGORA?**.
2. Ajuste duração, recursos disponíveis e observações. Clique em **GERAR PLANO**.
3. O plano traz objetivos, cronograma (que sempre fecha na duração exata), atividades do perfil do instrumento, avaliação, continuidade e a **justificativa pedagógica**.
4. Se a aula tiver outra duração, use **ADAPTAR DURAÇÃO**: o cronograma é redistribuído sem cortar a última atividade.
5. Para registrar a aula depois de dá-la, clique em **REGISTRAR AULA A PARTIR DESTE PLANO**.

Planos gerados sem Gemini são rotulados "gerado por modelo pedagógico (sem IA)".

## Registrar uma aula

1. Aba **Registrar aula**. A data vem como hoje e o horário vem da agenda (você pode manter ou alterar).
2. Marque a **frequência** (presente, falta, reposição, cancelada…). O Percurso nunca adivinha isso.
3. Escreva os **conteúdos trabalhados**, um por linha, e clique em **PREPARAR CLASSIFICAÇÃO**. Marque cada um como **consolidado**, **em desenvolvimento** ou **dificuldade**. É isso que atualiza o estado do aluno.
4. Dê notas de 1 a 5 só nos critérios que você observou. Deixe em branco o resto.
5. Anote dificuldades, conquistas, observações, tarefa e próximo passo. Clique em **SALVAR AULA**.

Para uma aula que já aconteceu em outra data, use o tipo **Registro retroativo**. A numeração das aulas é recalculada pela data.

## Histórico

A aba **Histórico** lista todas as aulas com data, situação e conteúdo. Abra qualquer uma para ver os detalhes. A busca filtra por conteúdo, dificuldade, período ou situação. Aqui também fica o **repertório** do aluno.

## Adicionar materiais e pesquisar

A aba **Minha biblioteca** aceita PDF, DOCX, TXT e MD. Os documentos ficam só no seu Drive. A busca encontra trechos por palavras e sinônimos pedagógicos e mostra documento, página e trecho. A aba **Pesquisar** consulta fontes acadêmicas e a base curricular. Toda fonte mostrada traz de onde veio: 📚 sua biblioteca, 🏛 currículo oficial, 🎓 literatura acadêmica.

## Gemini (opcional)

Veja a aba **Ajuda → Configurar o Gemini**. Com o Gemini ligado, o Percurso acrescenta resumos narrativos, planos contextuais e busca livre no histórico. Sem ele, nada deixa de funcionar.

## Frequência e relatórios

A aba **Relatórios** gera frequência, rendimento, pedagógico, completo, institucional e para responsáveis, por período, com gráficos e exportação em PDF/DOCX. Os percentuais são calculados pelo programa, nunca pela IA.

## Apoiar o projeto

O Percurso é gratuito. O botão **♡ Apoiar o Percurso** mostra um QR Code do Mercado Pago. Aparece um lembrete uma vez por mês, na primeira abertura do mês. Nenhuma função é bloqueada.

## Privacidade

- O Percurso só mexe na pasta `Meu Drive/Percurso`.
- Recomendamos identificar alunos só pelo primeiro nome, iniciais ou apelido. Nunca pedimos CPF, RG ou endereço.
- Em **Configurações → Privacidade** você pode exportar todos os dados (zip), excluir um registro (fica um backup por 30 dias) ou excluir a biblioteca.
- Nomes de alunos nunca são enviados ao Gemini; trechos da sua biblioteca só vão com a sua permissão na sessão.

## Solução de problemas

- **A célula 1 deu erro de rede** → espere alguns segundos e execute de novo.
- **Não achei o código** → confira se digitou as 6 letras/números certos. O código nunca tem 0, O, 1 ou I.
- **Algo não funcionou** → em **Configurações → Diagnóstico**, clique em DIAGNÓSTICO e envie o texto ao responsável pelo projeto. Ele não contém chaves nem dados de alunos.
- **Fechei o Colab sem querer** → nada se perde. Abra de novo, execute as duas células e carregue pelo código.
