"""Coleta progressiva do Caso de elegibilidade, um dado por vez.

`caso_parcial` é um dict no MESMO formato aceito por `llm.caso_de_dict` (o que
o modelo devolve), mais três marcadores que não existem no `Caso` final —
`membros_coletado`, `renda_coletada`, `saude_coletada` — porque para esses
passos uma resposta vazia é válida ("mora só", "nenhuma renda", "sem gastos")
e precisa ser distinguida de "ainda não foi perguntado".
"""

from __future__ import annotations

from collections.abc import Mapping

PERGUNTAS: dict[str, dict] = {
    "rota": {
        "texto": (
            "Para eu verificar certo: a pessoa tem 65 anos ou mais, ou a "
            "situação é por causa de uma deficiência?"
        ),
        "opcoes": ["Por idade (65 anos ou mais)", "Por deficiência"],
    },
    "idade": {
        "texto": "Qual a idade da pessoa que vai pedir o benefício?",
        "opcoes": [],
    },
    "impedimento": {
        "texto": (
            "Esse impedimento (físico, mental, intelectual ou sensorial) já "
            "dura, ou deve durar, pelo menos 2 anos?"
        ),
        "opcoes": ["Sim", "Não"],
    },
    "membros": {
        "texto": (
            "Quem mora na mesma casa com ela? Me diga a idade de cada pessoa "
            "(cônjuge, pais, filhos, irmãos solteiros) — ou \"mora só\", se "
            "for o caso."
        ),
        "opcoes": [],
    },
    "renda": {
        "texto": (
            "Qual a renda mensal de cada pessoa da casa (salário, trabalho "
            "informal, Bolsa Família, aposentadoria, pensão ou BPC)? Pode "
            "responder \"nenhuma\" se ninguém tiver renda."
        ),
        "opcoes": [],
    },
    "saude": {
        "texto": (
            "Tem gastos mensais com remédios, consultas, fraldas, "
            "alimentação especial ou centro-dia que não são cobertos pelo "
            "SUS/SUAS?"
        ),
        "opcoes": ["Sim", "Não"],
    },
}


def proximo_dado_faltante(caso_parcial: Mapping) -> str | None:
    """O próximo passo da coleta (chave de `PERGUNTAS`), ou `None` se o
    `Caso` já está completo para chamar `avaliar()`."""
    rota = caso_parcial.get("rota")
    if rota not in ("idade", "deficiencia"):
        return "rota"
    if rota == "idade" and not caso_parcial.get("requerente", {}).get("idade_anos"):
        return "idade"
    if rota == "deficiencia" and caso_parcial.get("impedimento_min_2_anos") is None:
        return "impedimento"
    if not caso_parcial.get("membros_coletado"):
        return "membros"
    if not caso_parcial.get("renda_coletada"):
        return "renda"
    if not caso_parcial.get("saude_coletada"):
        return "saude"
    return None


_CAMPOS_RENDA = ("renda_trabalho", "beneficios_previdenciarios", "renda_excluida")


def _membro_tem_renda_explicita(membro: Mapping) -> bool:
    return any(campo in membro for campo in _CAMPOS_RENDA)


def marcar_etapas_respondidas(caso_parcial: Mapping) -> dict:
    """Deriva `membros_coletado`/`renda_coletada`/`saude_coletada` da presença
    explícita dos dados em `caso_parcial` — NUNCA de um marcador que o LLM
    tenha devolvido (por isso sempre sobrescreve os três, mesmo que já
    existam). "Explícito" é a chave em si estar presente — uma lista vazia
    ("mora só", "sem gastos") ou renda zero contam, desde que a pessoa tenha
    respondido aquilo; a ausência da chave é "ainda não perguntado"."""
    resultado = dict(caso_parcial)

    resultado["membros_coletado"] = "outros_membros" in resultado

    if resultado["membros_coletado"]:
        membros = (resultado.get("requerente") or {}, *resultado.get("outros_membros", []))
        resultado["renda_coletada"] = all(_membro_tem_renda_explicita(m) for m in membros)
    else:
        resultado["renda_coletada"] = False

    resultado["saude_coletada"] = "deducoes_saude" in resultado
    return resultado


def fundir_caso_parcial(atual: Mapping, novo: Mapping) -> dict:
    """Funde os campos NOVOS (extraídos pelo LLM da última fala) no que já
    foi coletado. `requerente` é mesclado campo a campo; os demais campos —
    incluindo listas como `outros_membros` e `deducoes_saude` — são
    substituídos: o LLM sempre devolve o valor completo do campo, não um
    delta dele."""
    fundido = dict(atual)
    for chave, valor in novo.items():
        if chave == "requerente" and isinstance(valor, Mapping):
            fundido["requerente"] = {**fundido.get("requerente", {}), **valor}
        else:
            fundido[chave] = valor
    return fundido
