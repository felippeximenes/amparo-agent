# Amparo

Agente de IA que ajuda pessoas de baixa renda, idosas ou com deficiência a
entender e solicitar o **BPC/LOAS** (Benefício de Prestação Continuada) junto
ao INSS.

> ⚠️ **Projeto em desenvolvimento.** Amparo é uma ferramenta de orientação
> informativa e independente — **não é um canal oficial do INSS ou do
> governo federal** e não substitui atendimento presencial no INSS ou na
> Defensoria Pública.

## O problema

O BPC/LOAS é um direito garantido por lei a idosos e pessoas com deficiência
em situação de baixa renda, mas o acesso a ele esbarra em burocracia,
linguagem jurídica difícil e falta de orientação — justamente para o público
que mais precisa. Amparo existe para reduzir essa barreira: explica regras,
verifica elegibilidade e monta o checklist de documentos em linguagem simples.

## Como funciona

Um agente construído com LangGraph identifica a intenção da pessoa, aplica as
regras de elegibilidade de forma determinística (não é o modelo de IA que
decide se alguém tem direito ao benefício) e usa RAG sobre uma base curada de
legislação e manuais oficiais para explicar o processo — sempre citando a
fonte usada.

## Stack

- **Python** + **LangGraph** — orquestração do agente
- **Amazon Bedrock** — modelo de linguagem, com fallback
- **Qdrant** — busca vetorial (RAG) sobre documentos oficiais curados
- **Postgres (Neon)** — estado de sessão, sem dado sensível persistido
- **AWS SAM** — deploy serverless

## Rodando localmente

Pré-requisitos: [uv](https://docs.astral.sh/uv/), Docker e credenciais AWS com
acesso ao Amazon Bedrock (`aws configure`).

```bash
uv sync                              # cria o .venv e instala as dependências
cp .env.example .env                 # ajuste se necessário
docker compose up -d                 # sobe o Qdrant em localhost:6333
uv run pytest                        # roda os testes
uv run python scripts/ingest.py      # indexa docs/sources/ no Qdrant (requer AWS/Bedrock)
```

Skills do Claude Code: a pasta `.claude/skills/` é gitignored — rode o script em
`.claude/SKILLS_NOTES.md` depois de clonar.

## Status

Consulte [`ROADMAP.md`](./ROADMAP.md) para o progresso atual do projeto.

## Projeto irmão

Amparo compartilha arquitetura com o
[`certara-agent`](https://github.com/felippeximenes/certara-agent), assistente
de estudos conversacional para certificações AWS — mesmo padrão agentic
(LangGraph + RAG + fallback), público invertido.
