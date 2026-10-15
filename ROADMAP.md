# Roadmap — Amparo

Fonte de verdade do progresso do projeto. Marque os itens conforme forem
concluídos — é esta lista que orienta qualquer sessão (humana ou do Claude
Code) que continuar o trabalho.

Legenda: `[x]` feito · `[~]` parcial · `[ ]` a fazer

---

## Onde estamos (revisão de 15/10/2026)

Último commit: 15/10/2026. **65 testes passando.**

| Fase | Situação |
|---|---|
| 0 — Fundação | ✅ concluída |
| 1 — Curadoria + RAG | ✅ concluída (recall@5 = 85%) — 1 fonte pendente |
| 2 — Núcleo do agente | 🟡 ~75% — conversa multi-turno pronta, falta memória de sessão |
| 3 — API HTTP | ⬜ não iniciada |
| 4 — Canal WhatsApp | ⬜ não iniciada |
| 5 — Demo web | ⬜ não iniciada |
| 6 — Qualidade, LGPD e deploy | ⬜ não iniciada |
| 7 — Portfólio | ⬜ não iniciada |

**O que já funciona hoje:** conversa multi-turno pelo CLI (`scripts/chat.py`,
estado em memória no processo) → intenção por palavra-chave → RAG híbrido
(denso + BM25 + RRF) **ou** motor de elegibilidade determinístico, coletando
o `Caso` aos poucos (um dado por vez) → resposta com fonte + disclaimer. O LLM
(Ollama ou OpenAI, via endpoint compatível) extrai só os campos NOVOS de cada
fala e redige a resposta do RAG. Um desvio de assunto no meio da coleta
("e quais documentos?") é respondido pelo RAG sem perder o que já foi
coletado.

**Principais lacunas encontradas na revisão:**

1. ~~**Cada mensagem é independente.**~~ Resolvido em 15/10/2026: conversa
   multi-turno (`src/amparo/coleta.py` + `Estado.caso_parcial`/`aguardando`
   em `agente.py`). Ressalva: a extração por LLM às vezes infere um passo
   (ex.: "mora só") como coletado antes de perguntar explicitamente — a
   avaliação final continua correta (motor determinístico), mas o prompt de
   extração pode ser afinado depois.
2. ~~**Salário mínimo desatualizado.**~~ Resolvido em 15/10/2026:
   `PARAMETROS_2026` (SM R$ 1.621, limite R$ 405,25) + `parametros_vigentes(data)`.
   Anexo I (deduções de saúde) conferido — sem reajuste na Portaria 34/2025.
3. ~~**Documentação divergente do código.**~~ Resolvido em 15/10/2026:
   `CLAUDE.md` já não cita Bedrock.
4. **Qdrant em modo arquivo** só aceita um processo — serve para o CLI, não
   para um servidor web/webhook com vários workers.
5. Intenção classificada só por palavra-chave (frágil para fala coloquial) e
   sem `fallback_node`.

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
- [ ] Ampliar o conjunto de avaliação para ~40 perguntas, incluindo perguntas **coloquiais** (como as pessoas escrevem no WhatsApp: "minha mãe tem 66 anos e ganha pensão, ela pode pegar o loas?")

## Fase 2 — Núcleo do agente (LangGraph) 🟡

Já feito:

- [x] Grafo `intake → {elegibilidade | rag} → resposta` — `src/amparo/agente.py`
- [x] Motor de elegibilidade determinístico — `src/amparo/rules/elegibilidade.py` (idade, renda per capita, exclusões e deduções do Anexo I da Portaria 34/2025; deficiência sempre `depende_de_avaliacao`), com testes de borda
- [x] Citação obrigatória de fonte + disclaimer em toda resposta
- [x] LLM plugado — `src/amparo/llm.py` (`ChatLLM`, Ollama ou OpenAI): extrai o `Caso` da fala (JSON) e redige a resposta do RAG; modo template quando não há LLM; contador de tokens/custo
- [x] **Atualizar parâmetros para 2026** — `PARAMETROS_2026` (SM R$ 1.621) e `parametros_vigentes(data)` escolhe o parâmetro pela data; `avaliar()` usa o vigente hoje por padrão. Testes de borda em R$ 405,25. Anexo I conferido (sem reajuste).
- [x] **Conversa multi-turno** — `src/amparo/coleta.py` (`PERGUNTAS`, `proximo_dado_faltante`, `fundir_caso_parcial`, código puro e testado) + `Estado.caso_parcial`/`aguardando`/`opcoes` em `agente.py`. O agente pergunta *um dado por vez* (rota → idade/impedimento → quem mora na casa → renda de cada um → gastos de saúde) e só chama `avaliar()` quando o `Caso` está completo; atalho se a primeira fala já tiver tudo; desvio de assunto no meio responde pelo RAG sem perder o `caso_parcial`. `scripts/chat.py` carrega o `Estado` entre turnos (em memória no processo — persistência é o P3). `opcoes` de cada pergunta já no formato de botões para o WhatsApp.
- [~] Fluxo completo via CLI — funciona multi-turno em memória no processo (sem persistir entre execuções — isso é o P3)

A fazer (nesta ordem):

- [ ] **Memória de sessão** — checkpointer do LangGraph com `thread_id` por conversa. Dev: `MemorySaver`/SQLite; produção: Postgres (Neon). Expiração automática (ex.: 24 h sem mensagem → apaga o estado) — atende à regra de LGPD do `CLAUDE.md`.
- [ ] **Intenção via LLM** com saída estruturada, mantendo a palavra-chave como fallback quando o LLM está fora
- [ ] **`fallback_node`** — saudação, fora de escopo ("e o auxílio-doença?"), mensagem incompreensível → resposta educada + encaminhamento (INSS 135 / Defensoria)
- [ ] **Avaliação ponta a ponta** — `scripts/eval_agente.py` com ~20 conversas-roteiro: veredito correto, fonte citada existe nos trechos, sem valores inventados (LLM-as-judge + checagens determinísticas)
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
