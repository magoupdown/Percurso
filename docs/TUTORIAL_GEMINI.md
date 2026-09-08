# Como configurar o Gemini

**1. Obtenha sua chave.** Abra o [Google AI Studio](https://aistudio.google.com/api-keys), entre na sua conta Google e escolha criar uma chave de API. Se solicitado, selecione ou crie um projeto. Copie a chave gerada.

**2. Guarde no Colab.** Abra **Segredos**, no ícone de chave da barra lateral do Colab. Adicione um segredo com o nome **GEMINI_API_KEY** e cole a chave em **Valor**. Ative **Acesso do notebook**.

**3. Conecte.** Volte ao Percurso e clique em **Usar Gemini**. A mensagem de ativação confirma que a conexão funcionou.

**Alternativa para esta sessão:** se o segredo não for encontrado, aparece um campo de senha. Cole nele somente a chave e clique em **Usar Gemini**. Ela fica em memória e não é salva no Drive.

**Se houver erro:** confira o nome do segredo, a permissão de acesso do notebook e a situação da chave no AI Studio. Uma chave bloqueada precisa ser substituída. Você pode continuar sem Gemini.

Não compartilhe sua chave nem a inclua em capturas de tela. Disponibilidade, cotas e eventual cobrança são definidas pelo Google para seu projeto. [Orientação oficial sobre chaves](https://ai.google.dev/gemini-api/docs/api-key).
