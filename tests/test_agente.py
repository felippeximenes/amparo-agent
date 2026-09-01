"""Grafo do agente Amparo — nós isolados e fluxo ponta a ponta (sem LLM)."""

from decimal import Decimal

import pytest

from amparo.agente import (
    Intencao,
    construir_grafo,
    elegibilidade,
    intake,
    resposta,
)
from amparo.disclaimer import DISCLAIMER
from amparo.rules.elegibilidade import Caso, Membro, Resultado, Rota


# --- intake: classificação por palavra-chave -----------------------------------

@pytest.mark.parametrize(
    "pergunta,esperada",
    [
        ("Tenho direito ao BPC?", Intencao.ELEGIBILIDADE),
        ("Minha mãe posso pedir o benefício pra ela?", Intencao.ELEGIBILIDADE),
        ("Quais documentos preciso para dar entrada?", Intencao.CHECKLIST),
        ("Como solicitar o BPC pela internet?", Intencao.CHECKLIST),
        ("O que é a LOAS?", Intencao.DUVIDA),
    ],
)
def test_intake_classifica_intencao(pergunta, esperada):
    assert intake({"pergunta": pergunta})["intencao"] is esperada


# --- eligibility_node ---------------------------------------------------------

def test_elegibilidade_sem_caso_retorna_indeterminado_pedindo_dados():
    r = elegibilidade({"pergunta": "tenho direito?"})
    a = r["avaliacao"]
    assert a.resultado is Resultado.INDETERMINADO
    assert "idade" in a.motivo and "renda" in a.motivo


def test_elegibilidade_com_caso_roda_o_motor():
    caso = Caso(rota=Rota.IDADE, requerente=Membro(idade_anos=70, renda_trabalho=Decimal("0")))
    a = elegibilidade({"caso": caso})["avaliacao"]
    assert a.resultado is Resultado.ATENDE


# --- response_node ----------------------------------------------------------------

def test_resposta_sempre_traz_o_disclaimer():
    for estado in (
        {"avaliacao": elegibilidade({"caso": Caso(rota=Rota.IDADE, requerente=Membro(idade_anos=70))})["avaliacao"]},
        {"trechos": []},
        {},
    ):
        assert DISCLAIMER in resposta(estado)["resposta"]


def test_resposta_de_elegibilidade_cita_a_base_legal():
    caso = Caso(rota=Rota.IDADE, requerente=Membro(idade_anos=70))
    estado = {"avaliacao": elegibilidade({"caso": caso})["avaliacao"]}
    texto = resposta(estado)["resposta"]
    assert "Base:" in texto and "LOAS" in texto


# --- fluxo ponta a ponta --------------------------------------------------------

def test_fluxo_elegibilidade_com_caso_montado():
    grafo = construir_grafo()
    caso = Caso(rota=Rota.IDADE, requerente=Membro(idade_anos=70, renda_trabalho=Decimal("0")))
    final = grafo.invoke({"pergunta": "Tenho direito ao BPC?", "caso": caso})
    assert final["intencao"] is Intencao.ELEGIBILIDADE
    assert final["avaliacao"].resultado is Resultado.ATENDE
    assert DISCLAIMER in final["resposta"]


def test_fluxo_duvida_sem_indice_ainda_responde_com_disclaimer(monkeypatch):
    # sem índice do Qdrant, o rag_node deve degradar sem quebrar o fluxo
    from amparo import rag

    monkeypatch.setattr(rag, "client", lambda: None)
    monkeypatch.setattr(rag, "search", lambda *a, **k: [])
    grafo = construir_grafo()
    final = grafo.invoke({"pergunta": "O que é a LOAS?"})
    assert final["intencao"] is Intencao.DUVIDA
    assert DISCLAIMER in final["resposta"]
    assert "INSS" in final["resposta"] or "Defensoria" in final["resposta"]
