"""Slot do modelo de linguagem — a interface que o agente usa, sem implementação.

O provedor (Anthropic direto, OpenAI, local via Ollama...) será plugado aqui
quando decidido. Enquanto não houver implementação de `LLM`, o grafo roda em
modo sem-LLM: a elegibilidade sem um `Caso` montado fica `INDETERMINADO` e as
respostas são compostas por template em `agente.resposta`.
"""

from __future__ import annotations

from typing import Protocol

from amparo.rules.elegibilidade import Caso


class LLM(Protocol):
    def extrair_caso(self, texto: str) -> Caso | None:
        """Extrai um `Caso` de elegibilidade da fala do usuário.

        Retorna `None` quando faltam dados essenciais (rota, idade, composição
        e renda do grupo familiar) — nesse caso o agente deve perguntar.
        """
        ...

    def responder(self, pergunta: str, trechos: list[dict]) -> str:
        """Redige a resposta em linguagem simples, fundamentada só nos `trechos`.

        Cada trecho traz `titulo`/`fonte`/`tag`. A resposta cita a fonte e nunca
        afirma nada que não esteja nos trechos.
        """
        ...
