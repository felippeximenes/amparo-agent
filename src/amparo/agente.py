"""Grafo do agente Amparo (LangGraph).

`construir_grafo(llm, checkpointer)` monta `intake → {elegibilidade | rag} →
resposta`. Com `checkpointer` (ver `amparo.sessao`), o `Estado` persiste por
`thread_id` entre chamadas de `grafo.invoke()` — a conversa segue de um
turno para o outro sem precisar repassar o estado manualmente (ver
`scripts/chat.py`). Sem `checkpointer` (como nos testes), cada `invoke()`
começa do zero — por isso os testes repassam o estado anterior na mão.

- `intake` classifica a intenção pelo LLM (saída estruturada: elegibilidade,
  checklist, duvida, saudacao, fora_de_escopo, apagar); sem LLM, ou se a
  saída não der para interpretar, cai na classificação por palavra-chave
  (`classificar_intencao`, só distingue elegibilidade/checklist/duvida). Em
  meio a uma coleta (`aguardando` setado), só um desvio claro interrompe —
  checklist/duvida/apagar vindos do LLM, ou só checklist se a classificação
  caiu na palavra-chave (ela não é confiável para distinguir uma resposta
  curta de uma dúvida de verdade).
- `elegibilidade` usa `llm.extrair_atualizacoes` + `coleta.fundir_caso_parcial`
  para ir montando o `caso_parcial` aos poucos; `coleta.proximo_dado_faltante`
  (código puro) decide se falta pergunta ou se já pode chamar `avaliar()`.
  Sem LLM, cada turno fica `INDETERMINADO` no primeiro dado que falta.
- `rag` faz a busca híbrida; um desvio no meio da coleta passa por aqui sem
  tocar no `caso_parcial`, que a conversa retoma depois.
- `fallback` trata saudação, fora de escopo (outro benefício/assunto) e
  mensagem incompreensível com texto fixo — nunca decide elegibilidade, só
  orienta ou encaminha. "apagar" também passa por aqui (confirma o texto);
  quem efetivamente apaga a sessão é o canal (`scripts/chat.py`), que lê
  `Estado["intencao"]` depois do `invoke()`.
- `resposta` compõe o texto: fallback tem prioridade; senão, com LLM,
  `llm.responder` redige sobre os trechos; sem LLM, template. A parte de
  elegibilidade é sempre template (mantém os números e o veredito exatos).
  Disclaimer em toda resposta.
"""

from __future__ import annotations

from enum import Enum
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from amparo import rag
from amparo.coleta import (
    PERGUNTAS,
    filtrar_atualizacoes_vazias,
    fundir_caso_parcial,
    inferir_rota_por_idade,
    marcar_etapas_respondidas,
    proximo_dado_faltante,
)
from amparo.disclaimer import DISCLAIMER
from amparo.llm import LLM, caso_de_dict
from amparo.rules.elegibilidade import Avaliacao, Caso, Resultado, avaliar


class Intencao(str, Enum):
    ELEGIBILIDADE = "elegibilidade"
    CHECKLIST = "checklist"
    DUVIDA = "duvida"
    SAUDACAO = "saudacao"
    FORA_DE_ESCOPO = "fora_de_escopo"
    APAGAR = "apagar"
    # Não faz parte do schema do LLM — é o que `agente` atribui quando a
    # saída do modelo não dá para interpretar (ver `llm.interpretar_intencao`).
    INCOMPREENSIVEL = "incompreensivel"


# Desvio que interrompe uma coleta em andamento. A palavra-chave só distingue
# elegibilidade/checklist/duvida e não dá para confiar nela para "duvida"
# (uma resposta curta tipo "70 anos" cairia em duvida por default) — por
# isso o conjunto é mais estrito quando a classificação vem da palavra-chave.
_DESVIO_CLARO_COM_LLM = frozenset({Intencao.CHECKLIST, Intencao.DUVIDA, Intencao.APAGAR})
_DESVIO_CLARO_PALAVRA_CHAVE = frozenset({Intencao.CHECKLIST})


class Estado(TypedDict, total=False):
    pergunta: str
    mensagens: list[dict]            # histórico [{"role": "usuario"|"amparo", "texto": str}]
    caso_parcial: dict               # campos de elegibilidade já coletados, passo a passo
    aguardando: str | None           # qual passo de `coleta.PERGUNTAS` foi perguntado por último
    opcoes: list[str] | None         # opções curtas da pergunta pendente (futuros botões)
    intencao: Intencao
    texto_fallback: str | None       # saudação / fora de escopo / incompreensível / apagar
    caso: Caso | None                # Caso completo, só quando a coleta termina
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


_FONTE_COLETA = ("LOAS (Lei 8.742/1993) art. 20",)


def _avaliacao_pendente(dado_faltante: str) -> Avaliacao:
    return Avaliacao(
        Resultado.INDETERMINADO, PERGUNTAS[dado_faltante]["texto"], fontes=_FONTE_COLETA
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


_BOAS_VINDAS = (
    "Oi! Eu sou o Amparo — ajudo a entender e verificar o direito ao BPC/LOAS "
    "(Benefício de Prestação Continuada), o benefício para pessoas idosas ou "
    "com deficiência de baixa renda. Posso checar se você (ou alguém da sua "
    "família) tem direito, e explicar os documentos e o passo a passo do "
    "pedido. Me conte sua situação quando quiser."
)
_FORA_DE_ESCOPO_TEXTO = (
    "Eu só ajudo com o BPC/LOAS — não tenho informação sobre outros "
    "benefícios (como auxílio-doença, aposentadoria ou pensão) nem sobre "
    "outros assuntos. Para isso, procure o INSS (telefone 135 ou pelo app/"
    "site Meu INSS) ou a Defensoria Pública."
)
_INCOMPREENSIVEL_TEXTO = (
    "Não entendi bem o que você quis dizer. Pode reformular? Por exemplo: "
    "\"minha mãe tem 70 anos, ela tem direito ao BPC?\" ou \"quais documentos "
    "preciso para pedir o BPC?\"."
)
_APAGAR_TEXTO = "Vou apagar os dados desta conversa agora."

_TEXTO_FALLBACK = {
    Intencao.SAUDACAO: _BOAS_VINDAS,
    Intencao.FORA_DE_ESCOPO: _FORA_DE_ESCOPO_TEXTO,
    Intencao.APAGAR: _APAGAR_TEXTO,
    Intencao.INCOMPREENSIVEL: _INCOMPREENSIVEL_TEXTO,
}


def compor_resposta(
    *,
    avaliacao: Avaliacao | None = None,
    trechos: list[dict] | tuple = (),
    texto_rag: str | None = None,
    opcoes: list[str] | None = None,
    texto_fallback: str | None = None,
) -> str:
    partes: list[str] = []

    if texto_fallback is not None:  # saudação / fora de escopo / incompreensível / apagar
        partes.append(texto_fallback)
    elif avaliacao is not None:  # trilha de elegibilidade — sempre template exato
        partes.append(_linha_veredito(avaliacao))
        if avaliacao.renda_per_capita is not None and avaliacao.limite_renda is not None:
            partes.append(
                f"Renda por pessoa considerada: R$ {avaliacao.renda_per_capita:.2f}. "
                f"Limite (1/4 do salário mínimo): R$ {avaliacao.limite_renda:.2f}."
            )
        if opcoes:
            partes.append("Responda: " + " ou ".join(opcoes) + ".")
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


def construir_grafo(llm: LLM | None = None, checkpointer=None):
    def no_intake(estado: Estado) -> dict:
        pergunta = estado.get("pergunta", "")
        mensagens = [*estado.get("mensagens", []), {"role": "usuario", "texto": pergunta}]

        categoria = llm.classificar_intencao(pergunta) if llm is not None else None
        if categoria is not None:
            intencao_da_fala = Intencao(categoria)
            desvio_claro = _DESVIO_CLARO_COM_LLM
        else:
            intencao_da_fala = classificar_intencao(pergunta)
            desvio_claro = _DESVIO_CLARO_PALAVRA_CHAVE

        # Em meio à coleta, só um desvio claro interrompe — tudo o mais (ex.:
        # "70 anos", "moro só", que a palavra-chave classificaria como DUVIDA
        # por default) continua respondendo a pergunta pendente.
        if estado.get("aguardando") and intencao_da_fala not in desvio_claro:
            intencao = Intencao.ELEGIBILIDADE
        else:
            intencao = intencao_da_fala
        return {"mensagens": mensagens, "intencao": intencao}

    def no_elegibilidade(estado: Estado) -> dict:
        caso_parcial = dict(estado.get("caso_parcial") or {})
        pergunta = estado.get("pergunta", "")
        if llm is not None and pergunta:
            atualizacoes = llm.extrair_atualizacoes(
                estado.get("mensagens", []), caso_parcial
            )
            # Uma confirmação vazia (outros_membros=[], renda zero,
            # deducoes_saude=[]) só vale se responde à etapa que foi de fato
            # perguntada — senão é descartada e a pergunta se repete.
            atualizacoes = filtrar_atualizacoes_vazias(atualizacoes, estado.get("aguardando"))
            caso_parcial = fundir_caso_parcial(caso_parcial, atualizacoes)
        # Nunca confia em marcador de etapa vindo do LLM — deriva da presença
        # explícita dos dados (regra 1 do CLAUDE.md: elegibilidade é código,
        # não decisão do modelo). Idem para a rota: se já se sabe a idade
        # (>= 65), a rota é "idade" por regra determinística, não precisa de
        # o LLM ter dito isso explicitamente.
        caso_parcial = inferir_rota_por_idade(caso_parcial)
        caso_parcial = marcar_etapas_respondidas(caso_parcial)

        dado_faltante = proximo_dado_faltante(caso_parcial)
        if dado_faltante is not None:
            return {
                "caso_parcial": caso_parcial,
                "aguardando": dado_faltante,
                "opcoes": PERGUNTAS[dado_faltante]["opcoes"],
                "avaliacao": _avaliacao_pendente(dado_faltante),
                "caso": None,
            }

        caso = caso_de_dict(caso_parcial)
        if caso is None:  # dados coletados ficaram inconsistentes — recomeça pela rota
            return {
                "caso_parcial": caso_parcial,
                "aguardando": "rota",
                "opcoes": PERGUNTAS["rota"]["opcoes"],
                "avaliacao": _avaliacao_pendente("rota"),
                "caso": None,
            }
        return {
            "caso_parcial": caso_parcial,
            "aguardando": None,
            "opcoes": None,
            "caso": caso,
            "avaliacao": avaliar(caso),
        }

    def no_rag(estado: Estado) -> dict:
        pergunta = estado.get("pergunta", "")
        trechos = rag.search(rag.client(), pergunta, k=4) if pergunta else []
        return {"trechos": trechos}

    def no_fallback(estado: Estado) -> dict:
        intencao = estado.get("intencao")
        return {"texto_fallback": _TEXTO_FALLBACK[intencao]}

    def no_resposta(estado: Estado) -> dict:
        intencao = estado.get("intencao")
        em_elegibilidade = intencao is Intencao.ELEGIBILIDADE
        avaliacao = estado.get("avaliacao") if em_elegibilidade else None
        opcoes = estado.get("opcoes") if em_elegibilidade else None
        texto_fallback = estado.get("texto_fallback")

        trechos = estado.get("trechos") or []
        texto_rag = None
        if llm is not None and trechos:
            texto_rag = llm.responder(estado.get("pergunta", ""), trechos) or None

        resposta = compor_resposta(
            avaliacao=avaliacao,
            trechos=trechos,
            texto_rag=texto_rag,
            opcoes=opcoes,
            texto_fallback=texto_fallback,
        )
        mensagens = [*estado.get("mensagens", []), {"role": "amparo", "texto": resposta}]
        return {"resposta": resposta, "mensagens": mensagens}

    def _rota(estado: Estado) -> str:
        intencao = estado.get("intencao")
        if intencao is Intencao.ELEGIBILIDADE:
            return "elegibilidade"
        if intencao in (Intencao.CHECKLIST, Intencao.DUVIDA):
            return "rag"
        return "fallback"

    g = StateGraph(Estado)
    g.add_node("intake", no_intake)
    g.add_node("elegibilidade", no_elegibilidade)
    g.add_node("fallback", no_fallback)
    g.add_node("rag", no_rag)
    g.add_node("resposta", no_resposta)
    g.add_edge(START, "intake")
    g.add_conditional_edges(
        "intake",
        _rota,
        {"elegibilidade": "elegibilidade", "rag": "rag", "fallback": "fallback"},
    )
    g.add_edge("elegibilidade", "resposta")
    g.add_edge("rag", "resposta")
    g.add_edge("fallback", "resposta")
    g.add_edge("resposta", END)
    return g.compile(checkpointer=checkpointer)
