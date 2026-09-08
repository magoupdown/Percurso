# Como ligar o Gemini no Percurso

O Percurso funciona por completo **sem** o Gemini (Modo Essencial). O Gemini é um ajudante extra: ele escreve resumos, sugere ideias de aula e responde perguntas sobre o histórico. Para usá-lo, você precisa de uma **chave** gratuita do Google. Uma chave é como uma senha comprida que diz ao Google que é você usando o serviço.

Siga os passos na ordem. Leva uns 5 minutos.

## Parte 1 — Pegar a chave no Google

1. Abra um site chamado **Google AI Studio**. O endereço é: `https://aistudio.google.com`
2. Entre com a sua **conta do Google** (o mesmo e-mail que você usa no Gmail).
3. Procure um botão escrito **"Get API key"** (em português pode aparecer **"Obter chave de API"**). Ele costuma ficar no canto da tela.
4. Clique em **"Create API key"** (**"Criar chave de API"**). Se ele perguntar sobre um projeto, escolha criar um novo.
5. Vai aparecer uma sequência longa de letras e números. Essa é a sua chave. Clique em **copiar**.

> Guarde essa chave como você guardaria uma senha. Não mande por mensagem, não coloque em documento público e **nunca cole no GitHub**.

## Parte 2 — Guardar a chave no Colab (só uma vez)

6. Volte para a aba do **Google Colab** onde o Percurso está aberto.
7. Olhe a **barra da esquerda**. Há um ícone de **chave** 🔑. Clique nele. Vai abrir um painel chamado **"Segredos"** (ou "Secrets").
8. Clique em **"Adicionar novo segredo"** (**"Add new secret"**).
9. No campo **Nome**, escreva exatamente assim, com letras maiúsculas e o sublinhado:

   ```
   GEMINI_API_KEY
   ```

10. No campo **Valor**, **cole** a chave que você copiou na Parte 1.
11. Ative a chavinha **"Acesso do notebook"** (**"Notebook access"**). Ela precisa ficar ligada para o Percurso conseguir ler o segredo.

Pronto. O Colab guarda esse segredo para você. Ele não fica no notebook nem no GitHub.

## Parte 3 — Testar no Percurso

12. Na tela inicial do Percurso, clique em **USAR GEMINI**.
13. Se estiver tudo certo, aparece **"Gemini ativado para esta sessão"** e o selo muda para **Modo Inteligente (Gemini) ativo**.

## Se não funcionar

- **"Gemini ainda não está configurado."** → o Percurso não achou o segredo. Confira se o nome é exatamente `GEMINI_API_KEY` e se a chavinha "Acesso do notebook" está ligada. Depois clique em USAR GEMINI de novo.
- **"A chave informada não foi aceita pelo Google."** → a chave foi copiada errada ou foi apagada no AI Studio. Copie de novo (Parte 1) e cole de novo (Parte 2).
- **"Gemini não respondeu."** → problema de internet ou serviço do Google. Você pode tentar mais tarde ou clicar em **CONTINUAR SEM GEMINI**. Nada do Percurso deixa de funcionar.

## Só por hoje (sem guardar no Colab)

Se preferir não guardar a chave, clique em USAR GEMINI e cole a chave no campo **"Chave para usar apenas nesta sessão"**. Ela fica somente na memória enquanto o Colab estiver aberto e some quando você fechar. Na próxima vez, será preciso colar de novo.

## O que o Percurso faz com a sua chave

- Usa só para falar com o Gemini durante a sessão.
- **Nunca** grava a chave no Drive, no notebook, nos relatórios, nos backups ou nos registros de diagnóstico.
- **Nunca** envia a chave para outro serviço.
- Os nomes dos alunos **nunca** são enviados ao Gemini: o Percurso troca os nomes pelo código do registro antes de perguntar qualquer coisa.
