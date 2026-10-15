# Roteiro de prompts — Claude Code

Um prompt por etapa do `ROADMAP.md`. Para cada um:

1. Abra o terminal na pasta do projeto e rode `claude`.
2. Cole o prompt inteiro.
3. Quando terminar, ele roda os testes, marca o `ROADMAP.md` e faz o commit.
4. Volte na conversa com o Claude (claude.ai) e cole o **resumo final** que o
   Claude Code imprimir. Ajustamos o próximo prompt a partir dele.

Dicas:
- Um prompt por sessão (`/clear` entre um e outro) — o contexto fica limpo e o
  `CLAUDE.md` + `ROADMAP.md` dão a continuidade.
- Se ele pedir para usar uma ferramenta/comando, leia e aprove. Se travar ou
  fugir do escopo, interrompa com `Esc` e redirecione.
- Antes de colar um prompt grande, você pode pedir `use o plan mode` (ou
  `Shift+Tab`) para ele mostrar o plano antes de editar.
- Prompts marcados **[você]** têm passos manuais seus (contas, chaves, número).
- **Commits sem menção ao Claude**: a partir do P1 isso fica configurado
  (`attribution` no `.claude/settings.json` + regra no `CLAUDE.md`). Se algum
  commit sair com `Co-Authored-By: Claude`, peça: "refaça o último commit sem a
  linha Co-Authored-By".

---

## P0 — Sincronizar e conferir o ambiente

```
Contexto: estou retomando o projeto Amparo depois de ~6 semanas. Leia CLAUDE.md, ROADMAP.md e CONTEXT.md antes de tudo.

Tarefa:
1. Rode `git status` e `git fetch`. Existe uma branch remota `origin/docs/roadmap-revisao-2026-10` com o ROADMAP.md revisado. Se o ROADMAP.md local já tiver esse conteúdo (eu copiei à mão), não duplique: traga a branch para a main com merge fast-forward (ou, se houver conflito só no ROADMAP.md, fique com a versão da branch). Se houver diferenças só de quebra de linha (CRLF/LF), não as commite — configure `.gitattributes` com `* text=auto eol=lf` num commit separado.
2. Rode o script de sync das skills descrito em `.claude/SKILLS_NOTES.md` (a pasta `.claude/skills/` é gitignored).
3. `uv sync`, `uv run pytest`, `uv run python scripts/ingest.py` e `uv run python scripts/eval_retrieval.py`. Confirme que o recall@5 continua ≥ 0,80.
4. Verifique se há LLM disponível: Ollama rodando (`ollama list`) ou `.env` com OpenAI. Se nenhum, me diga como configurar e pare.
5. Rode `uv run python scripts/chat.py` com 2 perguntas de teste ("Quais documentos preciso para pedir o BPC?" e "Minha mãe tem 70 anos, mora sozinha e não tem renda. Ela tem direito?") e mostre as respostas.

Não altere código nesta etapa. No fim, faça push da main e imprima um RESUMO FINAL curto: estado dos testes, recall@5, LLM em uso, respostas das 2 perguntas, qualquer erro.
```

## P1 — Salário mínimo 2026 + documentação alinhada

**[você] antes de colar:** crie uma chave em platform.openai.com (API keys),
coloque alguns dólares de crédito e crie o `.env` na raiz do projeto:

```
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
LLM_API_KEY=sk-...sua-chave...
LLM_PRECO_ENTRADA=0.15
LLM_PRECO_SAIDA=0.60
```

(confira os preços atuais na página de pricing da OpenAI). O `.env` já está
no `.gitignore` — nunca cole a chave no chat do Claude Code.

```
Leia CLAUDE.md, ROADMAP.md (Fase 2, item "Atualizar parâmetros para 2026") e docs/adr/0001. Use a skill `tdd`.

Passo 0 — configuração do repositório (commit separado, tipo chore):
a) Commits deste projeto NÃO devem ter "Co-Authored-By: Claude" nem qualquer menção ao Claude. Crie/atualize `.claude/settings.json` (versionado) com a chave `attribution` vazia para commit e PR (consulte a documentação de settings do Claude Code para o formato exato) e adicione em CLAUDE.md, seção Convenções: "Commits e PRs sem trailer Co-Authored-By nem menção ao Claude; autor = configuração git local."
b) Na minha máquina há interceptação de TLS (antivírus/rede) e o Python não confia no certificado — no P0 foi preciso injetar `truststore` à mão. Torne isso permanente sem afetar outras máquinas: adicione a dependência `truststore` e chame `truststore.inject_into_ssl()` num único ponto de entrada (ex.: início de `amparo/config.py`), protegido por try/except. Confirme que `uv run python scripts/ingest.py` roda sem workaround.
c) O `.env` com a OpenAI já existe (não leia nem imprima a chave). Rode `uv run python scripts/chat.py` com as 2 perguntas do P0 e mostre as respostas e o custo estimado da sessão.

Problema: `src/amparo/rules/elegibilidade.py` usa PARAMETROS_2025 (salário mínimo R$ 1.518, limite R$ 379,50). Em 2026 o SM é R$ 1.621 (limite 1/4 = R$ 405,25), vigente desde 01/01/2026.

Tarefa:
1. Escreva primeiro os testes que falham: renda per capita exatamente R$ 405,25 → atende; R$ 405,26 → não atende; um caso com renda per capita entre R$ 379,51 e R$ 405,25 que hoje dá "não atende" e deve dar "atende" em 2026.
2. Crie PARAMETROS_2026 e uma função `parametros_vigentes(data: date) -> Parametros` que escolhe o parâmetro pela data (a lista de parâmetros fica num lugar só). `avaliar()` continua aceitando `params` explícito; o default passa a ser o vigente hoje.
3. Os valores do Anexo I (deduções de saúde) — mantenha os de 2025 em 2026, a menos que você encontre nos arquivos de docs/sources/ uma atualização; deixe um comentário dizendo que precisam ser conferidos a cada ano.
4. Corrija a documentação para a stack real: CLAUDE.md (seção Arquitetura cita Amazon Bedrock — o projeto usa fastembed local + LLM via endpoint compatível com OpenAI, Ollama por padrão) e README.md se necessário. Na seção "Fora de escopo" do CLAUDE.md, o canal WhatsApp agora está na Fase 4 do ROADMAP.

Critério de pronto: todos os testes passam; nenhum valor de SM espalhado fora do módulo de parâmetros (grep "1518" e "1.518" sem resultados fora do histórico).
Finalize: marque o item no ROADMAP.md, commits pequenos (feat/docs), push, e imprima um RESUMO FINAL.
```

## P2 — Conversa multi-turno (coleta de dados passo a passo)

```
Leia CLAUDE.md, CONTEXT.md, ROADMAP.md (Fase 2, "Conversa multi-turno") e src/amparo/agente.py e llm.py. Use as skills `domain-modeling` e `tdd`.

Problema: cada mensagem é independente. Para verificar elegibilidade a pessoa precisa mandar tudo numa mensagem; senão recebe INDETERMINADO.

Objetivo: o agente monta o Caso aos poucos, perguntando UM dado por vez, em linguagem simples, e só chama `avaliar()` quando o Caso está completo.

Requisitos:
- O Estado do grafo passa a ter: `mensagens` (histórico, com reducer `add_messages` ou lista própria), `caso_parcial` (dict com os campos já coletados) e `aguardando` (qual dado foi perguntado por último).
- Ordem da coleta: rota (idade ou deficiência) → idade do requerente (se rota idade) → impedimento ≥ 2 anos (se rota deficiência) → quem mora na mesma casa (membros do grupo familiar, CONTEXT.md) → renda de cada membro (trabalho, Bolsa Família, aposentadoria/pensão/BPC) → gastos de saúde do Anexo I.
- A extração do LLM recebe o histórico + o caso_parcial e devolve só os campos NOVOS; a fusão com o caso_parcial é código puro e testável (não é o LLM que decide o que está completo).
- Função pura `proximo_dado_faltante(caso_parcial) -> str | None` com testes. As perguntas ao usuário são textos fixos (template), cada uma com opções curtas — prepare-as num formato que depois vire botões do WhatsApp (ex.: `{"texto": ..., "opcoes": ["Por idade", "Por deficiência"]}`).
- Atalho: se a primeira mensagem já tiver tudo, avalia direto (comportamento atual).
- Se a pessoa mudar de assunto no meio ("e quais documentos?"), responde pelo RAG e mantém o caso_parcial.
- Regras inegociáveis do CLAUDE.md continuam valendo: veredito só do motor, fonte citada, disclaimer.
- Teste com FakeLLM uma conversa de 5–6 turnos ponta a ponta.
- Atualize scripts/chat.py para manter o estado entre as perguntas (por enquanto em memória no próprio processo — a persistência é o P3).

Finalize: testes passando, ROADMAP.md marcado, commits, push, RESUMO FINAL com um exemplo de conversa real pelo chat.py.
```

## P3 — Memória de sessão (checkpointer + expiração + "apagar")

```
Leia CLAUDE.md (regra 5, LGPD) e ROADMAP.md (Fase 2, "Memória de sessão"). Use `tdd` e `ponytail` (sem abstração especulativa).

Tarefa:
1. Use o checkpointer do LangGraph: `thread_id` por conversa. Dev/testes: SQLite (`langgraph-checkpoint-sqlite`) num arquivo gitignored. Deixe a troca para Postgres (`langgraph-checkpoint-postgres`, Neon) apenas por configuração (`SESSION_DB_URL`), sem implementar a infra agora.
2. Expiração: sessão sem mensagem há mais de `SESSION_TTL_HORAS` (default 24) é apagada. Implemente uma função `limpar_sessoes_expiradas()` + chamada oportunista no início de cada invocação (sem cron por enquanto).
3. Comando "apagar meus dados" / "apagar" / "sair" → apaga a thread imediatamente e confirma ao usuário.
4. Nada de dado sensível em log. Garanta que o thread_id NUNCA seja um telefone ou CPF cru: crie `session_id_de(identificador: str) -> str` = HMAC-SHA256 com segredo `SESSION_SALT` do .env.
5. chat.py passa a usar o checkpointer (`--sessao NOME` para retomar).
6. Documente em docs/adr/0002-memoria-de-sessao-e-lgpd.md (curto: o que é guardado, por quanto tempo, como apaga).

Finalize: testes, ROADMAP.md, .env.example atualizado, commits, push, RESUMO FINAL.
```

## P4 — Intenção via LLM + fallback_node

```
Leia CLAUDE.md, ROADMAP.md (Fase 2) e src/amparo/agente.py. Use `tdd`.

Tarefa:
1. Classificação de intenção pelo LLM com saída estruturada (JSON: elegibilidade | checklist | duvida | saudacao | fora_de_escopo | apagar). Se o LLM falhar ou não existir, cai na classificação por palavra-chave atual.
2. Crie o `fallback_node`: saudação → boas-vindas curtas + o que o Amparo faz + disclaimer; fora de escopo (outros benefícios, assuntos aleatórios) → explica que só cobre BPC/LOAS e encaminha (INSS 135 / Meu INSS / Defensoria); mensagem incompreensível → pede para reformular com exemplos.
3. Testes parametrizados com ~15 frases coloquiais reais (erros de digitação, sem acento, "loas", "beneficio da minha vó", "oi", "quanto é o auxílio-doença?").
4. Atualize o diagrama do grafo no CLAUDE.md.

Finalize: testes, ROADMAP.md, commits, push, RESUMO FINAL.
```

## P5 — Avaliação ponta a ponta + perguntas coloquiais no RAG

```
Leia ROADMAP.md (Fase 1, último item; Fase 2, "Avaliação ponta a ponta"), scripts/eval_retrieval.py.

Tarefa:
1. Amplie o conjunto do eval_retrieval para ~40 perguntas, metade coloquiais (como se escreve no WhatsApp). Rode e reporte o recall@5. Se cair abaixo de 0,80, investigue (skill `diagnosing-bugs`) e proponha ajuste — não mexa no corpus curado sem me perguntar.
2. Crie scripts/eval_agente.py com ~20 conversas-roteiro em YAML/JSON (tests/fixtures/conversas/): cada uma com as falas do usuário e o esperado (resultado de elegibilidade, ou fontes que devem aparecer). Checagens determinísticas: veredito correto; toda fonte citada existe nos trechos recuperados; nenhum valor em R$ que não venha do motor; disclaimer presente. Opcional: LLM-as-judge para "linguagem simples" (nota 1–5) com o mesmo LLM configurado.
3. Saída: tabela no terminal + arquivo eval_agente.json (gitignored). Falha (exit 1) se acerto de veredito < 95%.

Finalize: ROADMAP.md, commits, push, RESUMO FINAL com os números.
```

## P6 — API HTTP (FastAPI) + Qdrant servidor + Docker

```
Leia CLAUDE.md e ROADMAP.md (Fase 3 inteira). Use `tdd`.

Tarefa:
1. FastAPI em src/amparo/api.py: `POST /chat` {session_id, mensagem} → {resposta, fontes, avaliacao (opcional), opcoes (botões, se houver)}; `GET /health`. O session_id que chega é tratado com `session_id_de()`.
2. Qdrant: suporte a modo servidor via `QDRANT_URL` (+ `QDRANT_API_KEY`), mantendo o modo arquivo como default no dev. docker-compose.yml passa a subir `qdrant` + `api`.
3. Dockerfile da API (uv, multi-stage, modelo de embedding baixado no build para não baixar em cold start). Ingestão como comando (`docker compose run api python scripts/ingest.py`).
4. Timeout do LLM com resposta de contingência educada; rate limit simples por session_id (ex.: 20 msgs/min) em memória.
5. Log estruturado por requisição (JSON): latência, rota do grafo, tokens, custo estimado — SEM conteúdo das mensagens e SEM session_id cru.
6. Testes com TestClient + FakeLLM.
7. README: seção "Rodando a API".

Finalize: ROADMAP.md, commits, push, RESUMO FINAL com o comando para subir tudo e um curl de exemplo.
```

## P7 — [você] Preparar a conta do WhatsApp (sem código)

Passos manuais — faça antes do P8. Se travar em algum, me chame aqui.

1. Acesse developers.facebook.com, crie uma conta de desenvolvedor e um app do
   tipo **Business**.
2. No app, adicione o produto **WhatsApp**. A Meta cria uma conta de teste com
   um **número de teste** gratuito.
3. Em "Enviar e receber mensagens", cadastre o **seu celular** como
   destinatário (até 5 números) e mande a mensagem-modelo "hello_world" para
   confirmar que chega.
4. Anote: **Phone Number ID**, **WhatsApp Business Account ID**, **App Secret**
   (Configurações do app → Básico) e gere um **token permanente** (Business
   Settings → Usuários do sistema → criar usuário admin → gerar token com
   `whatsapp_business_messaging` e `whatsapp_business_management`).
5. Instale o `cloudflared` ou `ngrok` (para a Meta enxergar a API na sua máquina).
6. Coloque no `.env` (nunca no git): `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_ID`,
   `WHATSAPP_APP_SECRET`, `WHATSAPP_VERIFY_TOKEN` (uma senha que você inventa).

## P8 — Webhook do WhatsApp ("eco")

```
Leia CLAUDE.md e ROADMAP.md (Fase 4, itens 4.2). Use `tdd`. Já tenho no .env: WHATSAPP_TOKEN, WHATSAPP_PHONE_ID, WHATSAPP_APP_SECRET, WHATSAPP_VERIFY_TOKEN.

Tarefa: integração com a WhatsApp Cloud API oficial da Meta (Graph API), sem bibliotecas não oficiais e sem n8n.
1. src/amparo/canais/whatsapp.py + rotas na API:
   - GET /webhook/whatsapp: verificação (hub.mode == "subscribe", hub.verify_token confere → devolve hub.challenge; senão 403).
   - POST /webhook/whatsapp: valida X-Hub-Signature-256 (HMAC-SHA256 do corpo cru com o App Secret; inválida → 401). Responde 200 imediatamente e processa em background.
   - Extrai mensagens de texto (from, id, text.body). Ignora eventos de status, mensagens de grupo e tipos não suportados (responde "Por enquanto entendo só mensagens de texto").
   - Idempotência: ignora message.id já processado (cache com TTL).
2. Cliente de envio com httpx: POST https://graph.facebook.com/{versão}/{PHONE_ID}/messages (versão da Graph API configurável, `WHATSAPP_API_VERSION`). Nesta etapa só ecoa o texto recebido.
3. Testes com payloads reais da Meta como fixtures (tests/fixtures/whatsapp/) e o envio mockado.
4. Escreva docs/whatsapp.md com o passo a passo para eu testar: subir a API, abrir o túnel (cloudflared/ngrok), cadastrar a URL do webhook no painel da Meta, assinar o campo "messages", e mandar mensagem do meu celular.

Finalize: ROADMAP.md (4.1 e 4.2), commits, push, RESUMO FINAL com o passo a passo de teste.
```

## P9 — Ligar o agente ao WhatsApp

```
Leia CLAUDE.md, ROADMAP.md (Fase 4, item 4.3) e docs/whatsapp.md. O eco do WhatsApp já funciona.

Tarefa:
1. O webhook chama o mesmo serviço do POST /chat; session_id = session_id_de(telefone). O telefone nunca vai para estado nem log.
2. Formatação para WhatsApp: quebrar em partes de até 4.096 caracteres; markdown → negrito com *; links como texto puro; fontes no fim em lista curta.
3. Disclaimer: na primeira mensagem da sessão, boas-vindas + disclaimer completo + aviso de privacidade (o que guardamos, por 24 h, digite "apagar" para apagar). Nas demais, rodapé curto: "_Orientação informativa · não é o INSS_". Registre essa decisão em docs/adr/0003-disclaimer-no-whatsapp.md e ajuste a regra 4 do CLAUDE.md para referenciar o ADR.
4. Marcar a mensagem como lida assim que chegar (feedback de "recebido") enquanto o agente processa.
5. Comando "apagar" funciona pelo WhatsApp.
6. Testes ponta a ponta com payload de fixture → resposta enviada (mock).

Finalize: ROADMAP.md, commits, push, RESUMO FINAL. Vou testar no meu celular e volto com o resultado.
```

## P10 — Botões interativos + mensagens de voz

```
Leia ROADMAP.md (Fase 4, item 4.4) e o formato de `opcoes` criado no P2.

Tarefa:
1. Quando a resposta tem `opcoes`: até 3 → mensagem interativa com reply buttons (título ≤ 20 caracteres); 4 a 10 → list message. Ao clicar, o payload `interactive.button_reply`/`list_reply` vira a mensagem do usuário no grafo.
2. Áudio: mensagens do tipo audio → baixar a mídia pela Graph API (GET media_id → URL → download com o token), transcrever e seguir o fluxo normal. Transcrição atrás de uma interface (`Transcritor`), com implementação via faster-whisper local (modelo small, pt) e opção de API compatível com OpenAI (`/audio/transcriptions`) por config. Apagar o arquivo de áudio logo após transcrever. Responder "Ouvi: <transcrição>" antes da resposta, para a pessoa conferir.
3. Testes com fixtures e transcritor fake.

Finalize: ROADMAP.md, commits, push, RESUMO FINAL.
```

## P11 — Demo web

```
Leia CLAUDE.md e ROADMAP.md (Fase 5). Use as skills `frontend-design` e `impeccable`.

Tarefa: chat web mínimo que consome POST /chat, servido pela própria FastAPI (pasta web/, sem build complexo — HTML + JS ou Vite simples, você decide e justifica).
- Público: idosos e cuidadores. Fonte grande (≥ 18px), alto contraste AA, botões grandes, navegação por teclado, ARIA, prefers-reduced-motion.
- Disclaimer fixo e visível; nada que pareça site do governo (sem cores/brasão do gov.br).
- Fontes citadas como cartões clicáveis; resultado de elegibilidade com o cálculo aberto (renda considerada × limite).
- Opções da coleta como botões (mesmo formato do WhatsApp).
- Rate limit por IP para a demo pública.
- Teste E2E com Playwright de 2 fluxos (dúvida com fonte; elegibilidade completa por botões).

Finalize: ROADMAP.md, commits, push, RESUMO FINAL com print da tela.
```

## P12 — CI, LGPD e deploy

```
Leia CLAUDE.md e ROADMAP.md (Fase 6). Use `code-review` no projeto inteiro antes de começar e me mostre os achados principais.

Tarefa:
1. GitHub Actions: pytest + eval_retrieval (recall@5 ≥ 0,80) + eval_agente com FakeLLM determinístico + Playwright.
2. docs/lgpd.md: dados tratados, finalidade, retenção (24 h), hash do telefone, como apagar, terceiros envolvidos (Meta, provedor do LLM), o que nunca é guardado.
3. Deploy: compare AWS Lambda (imagem de container via SAM, padrão do certara-agent) × Fly.io/Render para esta API (modelo de embedding de ~470 MB, webhook que precisa responder rápido, Qdrant). Me mostre a comparação com custo estimado e PARE para eu escolher.
```

Depois da escolha, peça: "Siga com o deploy em <opção>: infra como código, segredos no gerenciador da plataforma, Qdrant Cloud ou container, URL pública do webhook atualizada no painel da Meta (me diga o passo manual)".

## P13 — Portfólio

```
Leia o projeto inteiro, ROADMAP.md e os ADRs. Escreva em português direto, primeira pessoa, sem jargão de marketing nem frases infladas.

Tarefa:
1. Reescreva o README.md como estudo de caso: problema (BPC/LOAS e a barreira de acesso) → público → demo (GIF/vídeo + link da demo web + como testar no WhatsApp) → arquitetura (diagrama Mermaid do grafo, RAG e canais) → decisões e por quê (links para os ADRs: elegibilidade determinística, RAG curado, embeddings locais, API oficial do WhatsApp, disclaimer, LGPD) → resultados em números (recall@5, acerto do eval_agente, nº de testes, latência média, custo por conversa) → como rodar → limitações honestas → próximos passos.
2. Gere a tabela de números rodando os evals de verdade, não invente.
3. Escreva docs/post-linkedin.md: rascunho de post contando o projeto (até 1.300 caracteres).
4. Liste para mim o roteiro do vídeo de 60–90 s (cena a cena) que eu vou gravar.

Finalize: ROADMAP.md (Fase 7), commit, push, RESUMO FINAL.
```

---

### Pendência manual (qualquer momento)

Portaria Conjunta MDS/MPS/INSS nº 33/2025 (DOU 07/08/2025, Seção 1): baixe o
texto em in.gov.br, salve como PDF na pasta do projeto e peça ao Claude Code:
"Estruture este PDF como docs/sources/16-portaria-conjunta-33-2025.md seguindo o
padrão do docs/sources/README.md, reindexe e rode o eval_retrieval".
