"""Grafo do agente Amparo (LangGraph).

Versão sem LLM: `intake` classifica a intenção por palavra-chave, `elegibilidade`
embrulha o motor de regras, `rag` embrulha a busca híbrida, `resposta` compõe o
texto final por template — sempre com citação de fonte e o disclaimer.

O parsing de texto livre para um `Caso` e o polimento da resposta entram depois,
quando um provedor de LLM for plugado.
"""

from __future__ import annotations

from enum import Enum
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from amparo import rag
from amparo.disclaimer import DISCLAIMER
from amparo.rules.elegibilidade import Avaliacao, Caso, Resultado, avaliar


class Intencao(str, Enum):
    ELEGIBILIDADE = "elegibilidade"
    CHECKLIST = "checklist"
    DUVIDA = "duvida"


class Estado(TypedDict, total=False):
    pergunta: str
    intencao: Intencao
    caso: Caso | None          # montado fora do grafo por enquanto
    avaliacao: Avaliacao | None
    trechos: list[dict]        # payloads do rag.search (com titulo/fonte/tag)
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


def intake(estado: Estado) -> dict:
    p = estado.get("pergunta", "").lower()
    if any(k in p for k in _ELEGIBILIDADE):
        intencao = Intencao.ELEGIBILIDADE
    elif any(k in p for k in _CHECKLIST):
        intencao = Intencao.CHECKLIST
    else:
        intencao = Intencao.DUVIDA
    return {"intencao": intencao}


def elegibilidade(estado: Estado) -> dict:
    caso = estado.get("caso")
    if caso is None:
        return {
            "avaliacao": Avaliacao(
                Resultado.INDETERMINADO,
                "Para verificar, preciso saber: se a análise é por idade ou por "
                "deficiência, a idade do requerente, quem mora na mesma casa "
                "(cônjuge, pais, filhos e irmãos solteiros) e a renda mensal de "
                "cada um.",
                fontes=("LOAS art. 20",),
            )
        }
    return {"avaliacao": avaliar(caso)}


def rag_node(estado: Estado) -> dict:
    pergunta = estado.get("pergunta", "")
    trechos = rag.search(rag.client(), pergunta, k=4) if pergunta else []
    return {"trechos": trechos}


def _linha_veredito(a: Avaliacao) -> str:
    if a.resultado is Resultado.ATENDE:
        return "Pelos dados informados, você parece atender aos critérios de idade e renda do BPC."
    if a.resultado is Resultado.DEPENDE_DE_AVALIACAO:
        return a.motivo
    if a.resultado is Resultado.INDETERMINADO:
        return a.motivo
    return f"Pelos dados informados, ainda não é atendido um dos critérios. {a.motivo}"


def resposta(estado: Estado) -> dict:
    partes: list[str] = []
    a = estado.get("avaliacao")
    if a is not None:
        partes.append(_linha_veredito(a))
        if a.renda_per_capita is not None and a.limite_renda is not None:
            partes.append(
                f"Renda por pessoa considerada: R$ {a.renda_per_capita:.2f}. "
                f"Limite (1/4 do salário mínimo): R$ {a.limite_renda:.2f}."
            )
        if a.fontes:
            partes.append("Base: " + "; ".join(a.fontes) + ".")

    trechos = estado.get("trechos") or []
    if trechos:
        partes.append("Segundo as fontes oficiais consultadas:")
        for t in trechos[:3]:
            corpo = t["texto"][:320].rstrip()
            partes.append(f"— {corpo}…\n  Fonte: {t['titulo']} — {t['fonte']}")
    elif a is None:
        partes.append(
            "Não encontrei essa informação nas fontes oficiais que consulto. "
            "Procure o INSS (telefone 135 ou Meu INSS) ou a Defensoria Pública."
        )

    partes.append(DISCLAIMER)
    return {"resposta": "\n\n".join(partes)}


def _rota(estado: Estado) -> str:
    return "elegibilidade" if estado.get("intencao") is Intencao.ELEGIBILIDADE else "rag"


def construir_grafo():
    g = StateGraph(Estado)
    g.add_node("intake", intake)
    g.add_node("elegibilidade", elegibilidade)
    g.add_node("rag", rag_node)
    g.add_node("resposta", resposta)
    g.add_edge(START, "intake")
    g.add_conditional_edges(
        "intake", _rota, {"elegibilidade": "elegibilidade", "rag": "rag"}
    )
    g.add_edge("elegibilidade", "resposta")
    g.add_edge("rag", "resposta")
    g.add_edge("resposta", END)
    return g.compile()
