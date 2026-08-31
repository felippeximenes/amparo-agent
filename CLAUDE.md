# Amparo — Agente de Benefícios Sociais (BPC/LOAS)

Leia este arquivo antes de escrever qualquer código neste repositório.

## O que é este projeto

Amparo é um agente de IA (LangGraph + RAG) que ajuda pessoas de baixa renda,
idosas ou com deficiência a entender e solicitar o **BPC/LOAS** (Benefício de
Prestação Continuada) junto ao INSS.

É o par social do projeto [`certara-agent`](https://github.com/felippeximenes/certara-agent)
(assistente de estudos para certificações AWS) — mesma arquitetura agentic,
público invertido: em vez de ajudar alguém a passar numa certificação técnica,
ajuda alguém a acessar um direito social que a burocracia esconde.

## Escopo do MVP

Cobre **apenas BPC/LOAS**. Não expandir para outros benefícios (auxílio-doença,
aposentadoria por invalidez etc.) nem para outros canais até o MVP estar
validado ponta a ponta — ver `ROADMAP.md`, Fase 5.

## Regras de domínio inegociáveis

1. **Elegibilidade é código determinístico, nunca decisão do LLM.** Idade,
   renda per capita e critério de deficiência são calculados por função pura
   testável (`rules/`), não geradas pelo modelo.
2. **Toda resposta que cita uma regra ou direito deve referenciar a fonte
   oficial** (lei, decreto, instrução normativa) usada no RAG. Nunca responder
   sobre elegibilidade ou processo sem citar de onde veio a informação.
3. **Nunca dar a entender que é um canal oficial do INSS ou do governo.** Nome,
   UI e respostas do agente devem deixar claro que é uma ferramenta de
   orientação independente.
4. **Disclaimer sempre visível**: "orientação informativa, não substitui
   atendimento no INSS ou na Defensoria Pública."
5. **LGPD**: não persistir dado sensível (renda declarada, condição de
   deficiência, CPF) além da sessão ativa. Sem tabela de usuários/perfis nesta
   fase do projeto — o que a pessoa contou só existe enquanto a conversa dura.

## Arquitetura

```
LangGraph:
  intake_node      → identifica a intenção (elegibilidade / checklist / dúvida geral)
  eligibility_node → regra determinística pura (idade, renda, deficiência)
  rag_node         → busca em Qdrant nos documentos curados em docs/sources/
  fallback_node    → modelo com saída estruturada, só quando a rota determinística não resolve
  response_node    → resposta final + citação de fonte + disclaimer
```

- **RAG**: Qdrant sobre corpus curado manualmente. Não usar crawler automático
  — neste domínio precisão importa mais que cobertura.
- **Modelo**: Amazon Bedrock, com fallback (mesmo padrão do `certara-agent`).
- **Estado de sessão**: Postgres (Neon), sem dado sensível persistido.
- **Deploy**: AWS SAM (mesmo padrão do `certara-agent`), quando o projeto
  chegar na fase de deploy.

## Convenções

- Documentos-fonte do RAG vivem em `docs/sources/`, sempre com metadata de
  origem e data de coleta no cabeçalho do arquivo.
- Toda mudança na lógica de elegibilidade exige teste unitário cobrindo o caso
  de borda correspondente (ex.: renda exatamente no limite).
- `ROADMAP.md` é a fonte de verdade do que já foi feito — atualize os
  checkboxes conforme o trabalho avança, não deixe a lista ficar desatualizada.

## Fora de escopo por enquanto

- Autenticação / contas de usuário
- Canal WhatsApp (Fase 5 do roadmap)
- Outros benefícios além de BPC/LOAS (Fase 5)
- Leitura assistida de documentos para acessibilidade — projeto irmão que
  entra como módulo do Amparo na Fase 5, não antes
