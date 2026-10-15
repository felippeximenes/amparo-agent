# Memória de sessão e LGPD

Até aqui o Amparo não guardava nada entre execuções — cada `chat.py` começava
do zero. Isso quebra a conversa multi-turno sempre que o processo reinicia, o
que seria inviável no WhatsApp (Fase 4). Decidimos persistir o `Estado` do
grafo (histórico, `caso_parcial`, resultado) via checkpointer do LangGraph,
indexado por `thread_id`, com expiração automática — isto é, "a sessão ativa"
da regra 5 do CLAUDE.md passa a significar **dentro da janela de
`SESSION_TTL_HORAS` (padrão 24h)**, não só "enquanto o processo está de pé".

**O que é guardado:** o `Estado` inteiro da conversa (mensagens, `caso_parcial`
— idade, renda, composição familiar, gastos de saúde —, resultado da
avaliação). Isso inclui dado sensível por natureza do próprio domínio do
Amparo; não há como verificar elegibilidade sem ele. O que a regra 5 exige é
limitar o *tempo* de retenção e nunca expor o identificador da pessoa.

**Por quanto tempo:** até `SESSION_TTL_HORAS` (padrão 24h) sem mensagem nova —
`limpar_sessoes_expiradas()`, chamada oportunisticamente a cada turno do
`chat.py` (sem cron). Ou imediatamente, se a pessoa digitar "apagar", "apagar
meus dados" ou "sair".

**Como se identifica a sessão sem expor a pessoa:** `thread_id` nunca é o
telefone/CPF cru — é `session_id_de(identificador)`, HMAC-SHA256 com
`SESSION_SALT` (segredo só no `.env`). Sem o salto, não há como recuperar o
identificador original a partir do `thread_id` armazenado.

**Onde:** SQLite num arquivo local gitignorado (`sessoes.db`) em dev/testes.
Produção trocaria para Postgres (Neon) preenchendo `SESSION_DB_URL` — ainda
não implementado; a troca de backend é só configuração quando chegar a hora
(`amparo.sessao.abrir_checkpointer`).

**Como se apaga:** `checkpointer.delete_thread(thread_id)` — apaga todos os
checkpoints da conversa na hora. Acionado pelo comando "apagar"/"apagar meus
dados"/"sair" no `chat.py`, ou pela expiração automática.
