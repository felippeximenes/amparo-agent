"""Grafo do agente Amparo (LangGraph).

`construir_grafo(llm)` monta `intake → {elegibilidade | rag} → resposta`.

- `intake` classifica a intenção por palavra-chave.
- `elegibilidade` usa `llm.extrair_caso` para montar um `Caso` a partir da fala;
  sem `Caso` (ou sem LLM) devolve `INDETERMINADO` pedindo os dados.
- `rag` faz a busca híbrida.
- `resposta` compõe o texto: com LLM, `llm.responder` redige sobre os trechos;
  sem LLM, template. A parte de elegibilidade é sempre template (mantém os
  números e o veredito exatos). Disclaimer em toda resposta.

`fallback_node` (saída estruturada do modelo) entra quando fizer falta.
"""

from __future__ import annotations

from enum import Enum
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from amparo import rag
from amparo.disclaimer import DISCLAIMER
from amparo.llm import LLM
from amparo.rules.elegibilidade import Avaliacao, Caso, Resultado, avaliar


class Intencao(str, Enum):
    ELEGIBILIDADE = "elegibilidade"
    CHECKLIST = "checklist"
    DUVIDA = "duvida"


class Estado(TypedDict, total=False):
    pergunta: str
    intencao: Intencao
    caso: Caso | None          # se já vier montado, o LLM não é chamado
    avaliacao: Avaliacao | None
    trechos: list[dict]
    resposta: str


_ELEGIBILIDADE = (
    "tenho direito", "tem direito", "direito ao", "posso receber", "posso pedir",
    "posso solicitar", "consigo o", "consigo receber", "sou elegív", "me enquadro",
    "tenho chance", "quem pode receber", "quem tem direito",
)
_CHECKLIST = (
    "documento", "documentos", "o que preciso", "o que levar", "o que apresentar",
    "checklist", "lista de", "como solicito", "como solicitar", "como peço",
    "como pedir", "como dar entrada", "onde peço", "onde solicito", "passo a passo",
)


def classificar_intencao(pergunta: str) -> Intencao:
    p = pergunta.lower()
    if any(k in p for k in _ELEGIBILIDADE):
        return Intencao.ELEGIBILIDADE
    if any(k in p for k in _CHECKLIST):
        return Intencao.CHECKLIST
    return Intencao.DUVIDA


PEDIDO_DE_DADOS = Avaliacao(
    Resultado.INDETERMINADO,
    "Para verificar, preciso saber: se a análise é por idade ou por deficiência, "
    "a idade do requerente, quem mora na mesma casa (cônjuge, pais, filhos e "
    "irmãos solteiros) e a renda mensal de cada um.",
    fontes=("LOAS (Lei 8.742/1993) art. 20",),
)


def _linha_veredito(a: Avaliacao) -> str:
    if a.resultado is Resultado.ATENDE:
        return (
            "Pelos dados informados, você parece atender aos critérios de idade e "
            "renda do BPC."
        )
    if a.resultado in (Resultado.DEPENDE_DE_AVALIACAO, Resultado.INDETERMINADO):
        return a.motivo
    return f"Pelos dados informados, ainda não é atendido um dos critérios. {a.motivo}"


def compor_resposta(
    *,
    avaliacao: Avaliacao | None = None,
    trechos: list[dict] | tuple = (),
    texto_rag: str | None = None,
) -> str:
    partes: list[str] = []

    if avaliacao is not None:  # trilha de elegibilidade — sempre template exato
        partes.append(_linha_veredito(avaliacao))
        if avaliacao.renda_per_capita is not None and avaliacao.limite_renda is not None:
            partes.append(
                f"Renda por pessoa considerada: R$ {avaliacao.renda_per_capita:.2f}. "
                f"Limite (1/4 do salário mínimo): R$ {avaliacao.limite_renda:.2f}."
            )
        if avaliacao.fontes:
            partes.append("Base: " + "; ".join(avaliacao.fontes) + ".")
    elif texto_rag:  # trilha do RAG com LLM
        partes.append(texto_rag)
    elif trechos:  # trilha do RAG sem LLM
        partes.append("Segundo as fontes oficiais consultadas:")
        for t in list(trechos)[:3]:
            corpo = t["texto"][:320].rstrip()
            partes.append(f"— {corpo}…\n  Fonte: {t['titulo']} — {t['fonte']}")
    else:
        partes.append(
            "Não encontrei essa informação nas fontes oficiais que consulto. "
            "Procure o INSS (telefone 135 ou pelo Meu INSS) ou a Defensoria Pública."
        )

    partes.append(DISCLAIMER)
    return "\n\n".join(partes)


def construir_grafo(llm: LLM | None = None):
    def no_intake(estado: Estado) -> dict:
        return {"intencao": classificar_intencao(estado.get("pergunta", ""))}

    def no_elegibilidade(estado: Estado) -> dict:
        caso = estado.get("caso")
        if caso is None and llm is not None:
            caso = llm.extrair_caso(estado.get("pergunta", ""))
        return {"avaliacao": avaliar(caso) if caso is not None else PEDIDO_DE_DADOS}

    def no_rag(estado: Estado) -> dict:
        pergunta = estado.get("pergunta", "")
        trechos = rag.search(rag.client(), pergunta, k=4) if pergunta else []
        return {"trechos": trechos}

    def no_resposta(estado: Estado) -> dict:
        trechos = estado.get("trechos") or []
        texto_rag = None
        if llm is not None and trechos:
            texto_rag = llm.responder(estado.get("pergunta", ""), trechos) or None
        return {
            "resposta": compor_resposta(
                avaliacao=estado.get("avaliacao"),
                trechos=trechos,
                texto_rag=texto_rag,
            )
        }

    def _rota(estado: Estado) -> str:
        return (
            "elegibilidade"
            if estado.get("intencao") is Intencao.ELEGIBILIDADE
            else "rag"
        )

    g = StateGraph(Estado)
    g.add_node("intake", no_intake)
    g.add_node("elegibilidade", no_elegibilidade)
    g.add_node("rag", no_rag)
    g.add_node("resposta", no_resposta)
    g.add_edge(START, "intake")
    g.add_conditional_edges(
        "intake", _rota, {"elegibilidade": "elegibilidade", "rag": "rag"}
    )
    g.add_edge("elegibilidade", "resposta")
    g.add_edge("rag", "resposta")
    g.add_edge("resposta", END)
    return g.compile()
