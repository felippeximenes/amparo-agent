# Roadmap — Amparo

Fonte de verdade do progresso do projeto. Marque os itens conforme forem
concluídos — é esta lista que orienta qualquer sessão (humana ou do Claude
Code) que continuar o trabalho.

Legenda: `[x]` feito · `[~]` parcial · `[ ]` a fazer

---

## Onde estamos (revisão de 15/10/2026)

Último commit: 15/10/2026. **157 testes passando.**

| Fase | Situação |
|---|---|
| 0 — Fundação | ✅ concluída |
| 1 — Curadoria + RAG | ✅ concluída (recall@5 = 82%, 40 perguntas) — 1 fonte pendente |
| 2 — Núcleo do agente | 🟡 veredito errado em 2 de 3 rodadas — ver lacuna 5 |
| 3 — API HTTP | ⬜ não iniciada |
| 4 — Canal WhatsApp | ⬜ não iniciada |
| 5 — Demo web | ⬜ não iniciada |
| 6 — Qualidade, LGPD e deploy | ⬜ não iniciada |
| 7 — Portfólio | ⬜ não iniciada |

**O que já funciona hoje:** conversa multi-turno pelo CLI (`scripts/chat.py
--sessao NOME`, persistida entre execuções via checkpointer + SQLite) →
intenção por palavra-chave → RAG híbrido (denso + BM25 + RRF) **ou** motor de
elegibilidade determinístico, coletando o `Caso` aos poucos (um dado por vez,
confirmação vazia só na etapa certa) → resposta com fonte + disclaimer. O LLM
(Ollama ou OpenAI, via endpoint compatível) extrai só os campos NOVOS de cada
fala e redige a resposta do RAG. Um desvio de assunto no meio da coleta
("e quais documentos?") é respondido pelo RAG sem perder o que já foi
coletado — se a extração não avançar a etapa pendente, uma 2ª tentativa
focada (`llm.extrair_foco`) é feita antes de repetir a pergunta. Sessão
expira em 24h sem mensagem ou na hora com "apagar". A
intenção agora é classificada pelo LLM (6 categorias, saída estruturada:
elegibilidade/checklist/duvida/saudacao/fora_de_escopo/apagar), com a
palavra-chave como fallback; saudação, fora de escopo, mensagem
incompreensível e apagar passam pelo `fallback_node`.

**Principais lacunas encontradas na revisão:**

1. ~~**Cada mensagem é independente.**~~ Resolvido em 15/10/2026: conversa
   multi-turno (`src/amparo/coleta.py` + `Estado.caso_parcial`/`aguardando`
   em `agente.py`). O LLM não decide mais quando uma etapa está respondida —
   `coleta.marcar_etapas_respondidas` deriva isso da presença explícita dos
   dados; corrigido um bug real em que o modelo pulava a pergunta de
   "quem mora na casa" (regra 1 do CLAUDE.md).
2. ~~**Salário mínimo desatualizado.**~~ Resolvido em 15/10/2026:
   `PARAMETROS_2026` (SM R$ 1.621, limite R$ 405,25) + `parametros_vigentes(data)`.
   Anexo I (deduções de saúde) conferido — sem reajuste na Portaria 34/2025.
3. ~~**Documentação divergente do código.**~~ Resolvido em 15/10/2026:
   `CLAUDE.md` já não cita Bedrock.
4. **Qdrant em modo arquivo** só aceita um processo — serve para o CLI, não
   para um servidor web/webhook com vários workers.
5. **Extração por LLM ainda tem ruído run-a-run — Fase 2 não fecha por isso.**
   `eval_agente.py` agora separa duas métricas (antes misturadas num só
   "acerto"): **veredito errado** (motor chega a um resultado definitivo
   diferente do esperado — sempre bug, meta 0) e **conversa não concluída**
   (terminou pedindo dado — normalmente ruído de extração num turno, meta
   ≥ 90%). Com `coleta.deduplicar_renda` e a 2ª tentativa focada
   (`llm.extrair_foco`), "não concluída" ficou saudável (95%, 95%, 100% em
   3 rodadas com gpt-4o-mini). **Veredito errado não ficou em 0**: 1/20 em
   2 das 3 rodadas, sempre a mesma conversa
   (`bolsa-familia-conta-como-renda-nao-atende`) — o modelo às vezes
   reclassifica a renda do requerente de `renda_trabalho` para
   `beneficios_previdenciarios` numa fala que não é sobre renda, escapando
   do `deduplicar_renda` (que só zera duplicata, não a reclassificação
   pura). Com `gpt-4o` (só para comparação, LLM_MODEL na linha de comando,
   `.env` não alterado): 0 veredito errado, 100% concluídas nas 20
   conversas — mas o preço no `.env` ainda é o do gpt-4o-mini, então o
   custo impresso não vale para essa comparação (ver RESUMO FINAL da
   sessão de 15/10/2026 para a estimativa corrigida). Não troquei o modelo
   padrão — decisão de quem lê isto.
6. ~~**Intenção classificada só por palavra-chave e sem `fallback_node`.**~~
   Resolvido em 15/10/2026: classificação pelo LLM (6 categorias) com a
   palavra-chave como fallback; `fallback_node` trata saudação, fora de
   escopo, mensagem incompreensível e confirma o apagar.

---

## Fase 0 — Fundação ✅

- [x] Stack: Python 3.12 + LangGraph + Qdrant + `fastembed` (embeddings locais) + LLM via endpoint compatível com OpenAI (Ollama por padrão). *(Bedrock foi a escolha inicial e foi abandonada em 31/08 — RAG 100% local.)*
- [x] Estrutura de pastas (`src/amparo/`, `tests/`, `docs/sources/`)
- [x] Disclaimer legal — `src/amparo/disclaimer.py` (+ teste)
- [x] Ambiente local — `pyproject.toml`, `uv.lock`, `.env.example`, `docker-compose.yml` (Qdrant opcional)

## Fase 1 — Curadoria de conteúdo (RAG) ✅

- [x] 15 fontes oficiais selecionadas e validadas (`docs/research/bpc-loas-fontes-oficiais.md`)
- [x] Documentos estruturados em `docs/sources/` com metadata (título, fonte, tipo, tag, data de coleta)
- [x] Ingestão: chunk por dispositivo legal (Art./§/heading), payload pronto para citação — `scripts/ingest.py` + `src/amparo/corpus.py`
- [x] Avaliação da recuperação — `scripts/eval_retrieval.py`, 20 perguntas, **recall@5 = 85%** (busca híbrida densa + BM25 com IDF, fusão RRF, máx. 2 trechos/arquivo)
- [ ] Coletar a Portaria Conjunta MDS/MPS/INSS nº 33/2025 (reavaliação, art. 21 da LOAS) — texto integral do DOU de 07/08/2025
- [x] Ampliar o conjunto de avaliação para ~40 perguntas, incluindo perguntas **coloquiais** (como as pessoas escrevem no WhatsApp: sem acento, abreviado, "loas") — `scripts/eval_retrieval.py`, **recall@5 = 82% (33/40)**

## Fase 2 — Núcleo do agente (LangGraph) 🟡

Já feito:

- [x] Grafo `intake → {elegibilidade | rag} → resposta` — `src/amparo/agente.py`
- [x] Motor de elegibilidade determinístico — `src/amparo/rules/elegibilidade.py` (idade, renda per capita, exclusões e deduções do Anexo I da Portaria 34/2025; deficiência sempre `depende_de_avaliacao`), com testes de borda
- [x] Citação obrigatória de fonte + disclaimer em toda resposta
- [x] LLM plugado — `src/amparo/llm.py` (`ChatLLM`, Ollama ou OpenAI): extrai o `Caso` da fala (JSON) e redige a resposta do RAG; modo template quando não há LLM; contador de tokens/custo
- [x] **Atualizar parâmetros para 2026** — `PARAMETROS_2026` (SM R$ 1.621) e `parametros_vigentes(data)` escolhe o parâmetro pela data; `avaliar()` usa o vigente hoje por padrão. Testes de borda em R$ 405,25. Anexo I conferido (sem reajuste).
- [x] **Conversa multi-turno** — `src/amparo/coleta.py` (`PERGUNTAS`, `proximo_dado_faltante`, `fundir_caso_parcial`, `marcar_etapas_respondidas`, código puro e testado) + `Estado.caso_parcial`/`aguardando`/`opcoes` em `agente.py`. O agente pergunta *um dado por vez* (rota → idade/impedimento → quem mora na casa → renda de cada um → gastos de saúde) e só chama `avaliar()` quando o `Caso` está completo; atalho se a primeira fala já tiver tudo; desvio de assunto no meio responde pelo RAG sem perder o `caso_parcial`. Nenhuma etapa é dada como respondida por um marcador do LLM — só pela presença explícita dos dados no `caso_parcial` (corrige um bug em que o modelo pulava a pergunta sobre quem mora na casa). `scripts/chat.py` carrega o `Estado` entre turnos (em memória no processo — persistência é o P3). `opcoes` de cada pergunta já no formato de botões para o WhatsApp.
- [x] **Memória de sessão** — `src/amparo/sessao.py`: checkpointer do LangGraph (SQLite em dev, `./sessoes.db` gitignored; Postgres via `SESSION_DB_URL` reservado por configuração, não implementado) + `thread_id` = `session_id_de(identificador)` (HMAC-SHA256, nunca o telefone/CPF cru) + `limpar_sessoes_expiradas()` (sem mensagem há mais de `SESSION_TTL_HORAS`, padrão 24h, chamada a cada turno do `chat.py`) + comando "apagar"/"apagar meus dados"/"sair" apaga a thread na hora. Decisão registrada em `docs/adr/0002-memoria-de-sessao-e-lgpd.md`.
- [x] Fluxo completo via CLI — `scripts/chat.py --sessao NOME` retoma a conversa entre execuções
- [x] **Intenção via LLM** com saída estruturada (`llm.classificar_intencao` + `llm.interpretar_intencao`, 6 categorias) — mantém a palavra-chave como fallback quando o LLM está fora ou não dá para interpretar a saída. Em meio a uma coleta, só um desvio claro interrompe (checklist/dúvida/apagar vindos do LLM; só checklist se caiu na palavra-chave, que não é confiável para "dúvida").
- [x] **`fallback_node`** — saudação (boas-vindas + o que o Amparo faz), fora de escopo ("e o auxílio-doença?" → só cubro BPC/LOAS, encaminha INSS 135/Meu INSS/Defensoria), mensagem incompreensível → pede para reformular com exemplo. "Apagar" também passa por aqui (confirma o texto); quem apaga de fato é o canal, lendo `Estado["intencao"]`.
- [x] **Correções encontradas via `diagnosing-bugs` + `eval_agente.py`**: idade >= 65 na primeira fala infere `rota` deterministicamente (`coleta.inferir_rota_por_idade`) — o LLM extraía a idade mas não preenchia `rota` sozinho, e a coleta pedia a rota de novo; filho/enteado/irmão só entra no grupo familiar se solteiro (`coleta.filtrar_grupo_familiar`, LOAS art. 20 §1º); `fundir_caso_parcial` mescla `outros_membros` por posição (não substitui a lista inteira) — o LLM as vezes restabelece um membro só com o campo novo, perdendo parentesco/idade já sabidos; `coleta.deduplicar_renda` corrige o LLM repetir o mesmo valor de aposentadoria em `renda_trabalho` E `beneficios_previdenciarios`, o que bloquearia a exclusão de 1 SM do idoso/deficiente.
- [~] **Avaliação ponta a ponta** — `scripts/eval_agente.py` com 20 conversas-roteiro em `tests/fixtures/conversas/` (YAML). Duas métricas separadas: **veredito errado** (meta 0, sai 1 se > 0) e **conversa não concluída** (meta ≥ 90%); também checa disclaimer e nenhum valor em R$ fora do motor; relatório em `eval_agente.json` (gitignored). 3 rodadas com gpt-4o-mini: não concluídas 95%/95%/100% (saudável) mas **veredito errado 1/0/1** — não fecha a meta de 0. Mesma conversa falhando nas duas vezes (lacuna nº 5). `coleta.deduplicar_renda` e `llm.extrair_foco` (2ª tentativa de extração focada na etapa pendente) já implementados; falta eliminar essa reclassificação específica.
- [x] Alinhar `CLAUDE.md` e `README.md` com a stack real (sem Bedrock)

## Fase 3 — API HTTP do agente ⬜

Uma API única que os dois canais (WhatsApp e web) usam. Sem ela, cada canal
reimplementaria o agente.

- [ ] FastAPI: `POST /chat` `{session_id, mensagem}` → `{resposta, fontes, avaliacao?}`; `GET /health`
- [ ] Qdrant em **modo servidor** (Docker no dev; Qdrant Cloud free tier ou container junto da API em produção) — o modo arquivo não aceita vários processos
- [ ] Índice criado no build/deploy (ingestão como etapa, não manual)
- [ ] `Dockerfile` da API (com o modelo de embedding já baixado na imagem, para não baixar a cada cold start)
- [ ] Rate limit por sessão e timeout do LLM com resposta de contingência
- [ ] Observabilidade: log estruturado por requisição (latência, tokens, custo, rota do grafo) — **sem gravar o conteúdo das mensagens**; opcional: Langfuse/LangSmith com mascaramento
- [ ] Testes da API com `httpx`/`TestClient` usando o `FakeLLM` que já existe

## Fase 4 — Canal WhatsApp ⬜

**Por que antes da web:** o público do Amparo (idosos, pessoas de baixa renda,
cuidadores de pessoas com deficiência) usa WhatsApp, não apps. É o canal que
dá sentido ao projeto — e o diferencial do portfólio.

**Abordagem recomendada: WhatsApp Cloud API oficial da Meta + webhook próprio
na FastAPI.** Sem n8n no meio (a API já resolve; menos peças, código que
aparece no portfólio). Evitar bibliotecas não oficiais (Baileys, Evolution
API, "WhatsApp Web"): violam os termos, o número pode ser banido, e o projeto
lida com dados sensíveis de público vulnerável.

```
Pessoa no WhatsApp
      │ mensagem
      ▼
Meta (WhatsApp Cloud API) ──POST webhook──▶ FastAPI /webhook/whatsapp
                                              │ 1. valida assinatura (X-Hub-Signature-256)
                                              │ 2. responde 200 na hora
                                              │ 3. processa em background
                                              ▼
                                        grafo LangGraph (thread_id = hash do telefone)
                                              │
FastAPI ──POST /{phone_id}/messages──▶ Meta ──▶ resposta no WhatsApp
```

4.1 Preparação (sem código)
- [ ] Criar conta Meta for Developers + app do tipo "Business" + produto WhatsApp
- [ ] Usar o **número de teste** que a Meta fornece (envia só para até 5 números cadastrados — suficiente para desenvolver)
- [ ] Gerar token de acesso permanente (System User) — o token do painel expira em 24 h
- [ ] Expor a API local com `ngrok`/`cloudflared` para a Meta alcançar o webhook

4.2 Webhook mínimo ("eco")
- [ ] `GET /webhook/whatsapp` — verificação (`hub.mode`, `hub.verify_token`, devolver `hub.challenge`)
- [ ] `POST /webhook/whatsapp` — validar assinatura com o App Secret, extrair `from` + texto, responder 200 imediatamente
- [ ] Cliente de envio (`httpx` → Graph API `/messages`) — primeiro só devolve o texto recebido
- [ ] Idempotência: a Meta reenvia eventos; ignorar `message.id` já processado
- [ ] Ignorar eventos de status (entregue/lido) e mensagens de grupos

4.3 Ligar o agente
- [ ] Webhook chama o mesmo serviço do `POST /chat`; `session_id` = hash (SHA-256 + sal) do telefone — o número nunca vai para o estado nem para os logs
- [ ] Adaptar a resposta ao WhatsApp: limite de 4.096 caracteres (quebrar em partes), negrito com `*`, sem markdown de link
- [ ] Mensagem de boas-vindas na primeira interação com o **disclaimer completo** + aviso de privacidade; nas respostas seguintes, rodapé curto ("Orientação informativa · não é o INSS"). *(Decisão a registrar em ADR: adapta a regra nº 4 do `CLAUDE.md` ao formato do canal.)*
- [ ] Comando "apagar" / "sair" → apaga a sessão na hora (LGPD)

4.4 Experiência pensada para o público
- [ ] Botões de resposta (até 3) e listas (até 10) na coleta de dados — "Por idade / Por deficiência", "Quantas pessoas moram com você?"
- [ ] **Áudio**: transcrever mensagens de voz (Whisper local ou API) — boa parte do público prefere mandar áudio
- [ ] Indicador de "lendo…" (marcar como lida) enquanto o agente processa

4.5 Produção
- [ ] Número próprio (chip dedicado, não o pessoal) registrado na Cloud API + verificação do negócio, se for abrir para o público
- [ ] Custo: respostas dentro da janela de 24 h após a pessoa escrever são **gratuitas** na Cloud API; o Amparo só responde (não dispara mensagens), então o custo do WhatsApp tende a zero — o custo real é o LLM
- [ ] Política: em jan/2026 a Meta proibiu assistentes de IA **de uso geral** na Business API (o CADE suspendeu a regra para números +55). O Amparo é um bot de serviço específico, mas manter o escopo restrito ao BPC e acompanhar a regra

## Fase 5 — Demo web ⬜

Para quem avalia o portfólio conseguir testar sem cadastrar telefone.

- [ ] Chat web mínimo consumindo `POST /chat` (reaproveitar padrões de UI do `certara-agent`)
- [ ] Mostrar as fontes citadas como cartões clicáveis e o resultado da elegibilidade com o cálculo aberto (renda considerada × limite)
- [ ] Acessibilidade: teclado, ARIA, contraste AA, fonte grande, `prefers-reduced-motion`
- [ ] Disclaimer visível e permanente
- [ ] Limite de uso por IP (demo pública com LLM pago)

## Fase 6 — Qualidade, conformidade e deploy ⬜

- [ ] CI no GitHub Actions: `pytest` + `eval_retrieval` (falha se recall@5 < 0,8) + `eval_agente`
- [ ] E2E com Playwright na demo web; teste do webhook com payloads reais da Meta (fixtures)
- [ ] Revisão LGPD documentada (`docs/lgpd.md`): o que é coletado, por quanto tempo, como apagar; nada sensível fora da sessão; telefone só como hash
- [ ] Deploy: container da API (AWS Lambda com imagem de container via SAM, como no `certara-agent`, **ou** Fly.io/Render). Atenção: o modelo de embedding (~470 MB) pesa no cold start da Lambda — medir antes de decidir
- [ ] Segredos fora do código (token da Meta, App Secret, chave do LLM)
- [ ] Rotina para atualizar parâmetros anuais (salário mínimo de janeiro) e reindexar fontes quando a legislação mudar

## Fase 7 — Portfólio ⬜

- [ ] README reescrito como estudo de caso: problema → público → decisões de arquitetura → resultados
- [ ] Diagrama da arquitetura (grafo + RAG + canais)
- [ ] Vídeo/GIF de 60–90 s: conversa no WhatsApp do "oi" até o checklist de documentos
- [ ] Números que mostram rigor: recall@5 do RAG, acerto do motor de elegibilidade, nº de testes, latência média, custo por conversa
- [ ] Seção "Decisões que tomei e por quê" (ADRs): elegibilidade determinística em vez de LLM, RAG curado em vez de crawler, embeddings locais, API oficial do WhatsApp em vez de não oficial
- [ ] Post no LinkedIn / artigo curto contando o projeto

## Fase 8 — Extensão (pós-MVP) ⬜

- [ ] Projeto irmão (leitura assistida de documentos para acessibilidade) como módulo do Amparo — ex.: a pessoa manda foto de uma carta do INSS e o Amparo explica
- [ ] Outros benefícios (auxílio por incapacidade temporária, aposentadoria por incapacidade permanente)
- [ ] Busca de CRAS mais próximo para inscrição/atualização do CadÚnico
