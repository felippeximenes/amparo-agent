# Roadmap — Amparo

Checklist de execução do MVP (BPC/LOAS). Marque os itens conforme forem
concluídos; mantenha esta lista como fonte de verdade do progresso do
projeto — é ela que orienta qualquer sessão do Claude Code que continuar o
trabalho.

## Fase 0 — Fundação

- [ ] Confirmar stack final (Python + LangGraph + Qdrant + Bedrock + Postgres/Neon)
- [ ] Criar estrutura de pastas (`src/`, `docs/sources/`, `tests/`)
- [ ] Escrever o texto padrão do disclaimer legal (usado em toda resposta do agente)
- [ ] Configurar ambiente local (`.env.example`, dependências, `README` de setup)

## Fase 1 — Curadoria de conteúdo (RAG)

- [ ] Selecionar 15–20 fontes oficiais sobre BPC/LOAS:
  - Lei Orgânica da Assistência Social (Lei 8.742/93) e alterações
  - Decreto 6.214/2007 (regulamenta o BPC)
  - Instruções Normativas do INSS sobre BPC
  - Manuais oficiais do Meu INSS / gov.br/inss
- [ ] Estruturar os documentos em `docs/sources/` (texto limpo, com metadata de fonte e data de coleta)
- [ ] Escrever script de ingestão (chunking + embeddings) para o Qdrant
- [ ] Validar a recuperação (RAG) com um conjunto de perguntas de teste

## Fase 2 — Núcleo do agente (LangGraph)

- [ ] Modelar o grafo: `intake_node → eligibility_node → rag_node → fallback_node → response_node`
- [ ] Implementar `eligibility_node` como função determinística pura (idade, renda per capita, deficiência) com testes unitários cobrindo casos de borda
- [ ] Integrar Amazon Bedrock com fallback (mesmo padrão do `certara-agent`)
- [ ] Garantir citação obrigatória de fonte em toda resposta do `rag_node`
- [ ] Persistência de sessão (Postgres/Neon) sem dado sensível fora da sessão ativa
- [ ] Testar o fluxo completo via CLI/notebook com casos reais (idoso sem deficiência, PCD jovem, renda na borda do limite)

## Fase 3 — Interface

- [ ] Front-end web mínimo (chat), reaproveitando padrões de UI do `certara-agent`
- [ ] Acessibilidade: navegação por teclado, ARIA, contraste, `prefers-reduced-motion` (mesmo padrão do projeto `Caminhos`)
- [ ] Exibir o disclaimer de forma visível e permanente na interface

## Fase 4 — Qualidade, conformidade e deploy

- [ ] Cobertura E2E com Playwright dos fluxos principais
- [ ] Revisão de conformidade LGPD: nenhuma persistência de dado sensível fora da sessão ativa, política de retenção documentada
- [ ] Deploy serverless (AWS SAM, mesmo padrão do `certara-agent`)
- [ ] Documentar a arquitetura final no `README.md` com prints/vídeo de demonstração (para o portfólio)

## Fase 5 — Extensão (pós-MVP)

- [ ] Canal WhatsApp via n8n como alternativa de acesso para quem não usa apps
- [ ] Iniciar o projeto irmão (agente de acessibilidade documental) como módulo do Amparo
- [ ] Expandir cobertura para outros benefícios (auxílio-doença, aposentadoria por invalidez)
