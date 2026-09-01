"""Grafo do agente Amparo — núcleo puro e fluxo ponta a ponta."""

from decimal import Decimal

import pytest

from amparo.agente import (
    Intencao,
    classificar_intencao,
    compor_resposta,
    construir_grafo,
)
from amparo.disclaimer import DISCLAIMER
from amparo.rules.elegibilidade import Caso, Membro, Resultado, Rota, avaliar


class FakeLLM:
    """Implementa o Protocol LLM sem rede."""

    def __init__(self, caso: Caso | None = None, texto: str = "RESPOSTA DO MODELO"):
        self._caso = caso
        self._texto = texto

    def extrair_caso(self, texto):  # noqa: ARG002
        return self._caso

    def responder(self, pergunta, trechos):  # noqa: ARG002
        return self._texto


# --- classificação de intenção -----------------------------------------------

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
def test_classificar_intencao(pergunta, esperada):
    assert classificar_intencao(pergunta) is esperada


# --- compor_resposta (puro) --------------------------------------------------

def test_resposta_sempre_traz_o_disclaimer():
    a = avaliar(Caso(rota=Rota.IDADE, requerente=Membro(idade_anos=70)))
    for kwargs in ({"avaliacao": a}, {"trechos": []}, {}):
        assert DISCLAIMER in compor_resposta(**kwargs)


def test_resposta_de_elegibilidade_cita_base_legal_e_ignora_texto_do_llm():
    a = avaliar(Caso(rota=Rota.IDADE, requerente=Membro(idade_anos=70)))
    texto = compor_resposta(avaliacao=a, texto_rag="qualquer coisa do modelo")
    assert "Base:" in texto and "LOAS" in texto
    assert "Pelos dados informados" in texto
    # a trilha de elegibilidade não passa pelo LLM — número e veredito exatos
    assert "qualquer coisa do modelo" not in texto


def test_resposta_do_rag_usa_o_texto_do_llm_quando_ha():
    texto = compor_resposta(trechos=[{"texto": "x", "titulo": "t", "fonte": "u"}],
                            texto_rag="explicação simples do modelo")
    assert "explicação simples do modelo" in texto
    assert "Segundo as fontes oficiais" not in texto  # template não é usado


def test_resposta_do_rag_sem_llm_cai_no_template_com_fonte():
    texto = compor_resposta(
        trechos=[{"texto": "conteúdo do trecho", "titulo": "LOAS", "fonte": "http://x"}]
    )
    assert "Segundo as fontes oficiais" in texto
    assert "Fonte: LOAS — http://x" in texto


# --- fluxo ponta a ponta ----------------------------------------------------------

def test_fluxo_elegibilidade_com_caso_ja_montado_nao_chama_o_llm():
    grafo = construir_grafo(FakeLLM(caso=None))  # extrair_caso devolveria None
    caso = Caso(rota=Rota.IDADE, requerente=Membro(idade_anos=70, renda_trabalho=Decimal("0")))
    final = grafo.invoke({"pergunta": "Tenho direito ao BPC?", "caso": caso})
    assert final["intencao"] is Intencao.ELEGIBILIDADE
    assert final["avaliacao"].resultado is Resultado.ATENDE
    assert DISCLAIMER in final["resposta"]


def test_fluxo_elegibilidade_llm_extrai_o_caso_da_pergunta():
    caso = Caso(rota=Rota.IDADE, requerente=Membro(idade_anos=68, renda_trabalho=Decimal("0")))
    grafo = construir_grafo(FakeLLM(caso=caso))
    final = grafo.invoke({"pergunta": "tenho 68 anos e não tenho renda, tenho direito?"})
    assert final["avaliacao"].resultado is Resultado.ATENDE


def test_fluxo_elegibilidade_sem_llm_pede_os_dados():
    grafo = construir_grafo(llm=None)
    final = grafo.invoke({"pergunta": "tenho direito ao bpc?"})
    assert final["avaliacao"].resultado is Resultado.INDETERMINADO
    assert "idade" in final["resposta"] and "renda" in final["resposta"]


def test_fluxo_duvida_sem_indice_ainda_responde_com_disclaimer(monkeypatch):
    from amparo import rag

    monkeypatch.setattr(rag, "client", lambda: None)
    monkeypatch.setattr(rag, "search", lambda *a, **k: [])
    grafo = construir_grafo(llm=None)
    final = grafo.invoke({"pergunta": "O que é a LOAS?"})
    assert final["intencao"] is Intencao.DUVIDA
    assert DISCLAIMER in final["resposta"]
    assert "INSS" in final["resposta"] or "Defensoria" in final["resposta"]


def test_fluxo_duvida_com_llm_usa_a_resposta_do_modelo(monkeypatch):
    from amparo import rag

    monkeypatch.setattr(rag, "client", lambda: None)
    monkeypatch.setattr(
        rag, "search", lambda *a, **k: [{"texto": "art. 20...", "titulo": "LOAS", "fonte": "http://x"}]
    )
    grafo = construir_grafo(FakeLLM(texto="A LOAS é a lei da assistência social."))
    final = grafo.invoke({"pergunta": "O que é a LOAS?"})
    assert "A LOAS é a lei da assistência social." in final["resposta"]
    assert DISCLAIMER in final["resposta"]
