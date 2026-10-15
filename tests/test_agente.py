"""Grafo do agente Amparo — núcleo puro e fluxo ponta a ponta."""

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
    """Implementa o Protocol LLM sem rede. `atualizacoes` é a fila de retornos
    de `extrair_atualizacoes`, um por chamada (fila vazia → `{}`, sem novidade)."""

    def __init__(self, atualizacoes: list[dict] | None = None, texto: str = "RESPOSTA DO MODELO"):
        self._fila = list(atualizacoes or [])
        self._texto = texto

    def extrair_atualizacoes(self, mensagens, caso_parcial):  # noqa: ARG002
        return self._fila.pop(0) if self._fila else {}

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

def test_fluxo_elegibilidade_sem_llm_pede_a_rota():
    grafo = construir_grafo(llm=None)
    final = grafo.invoke({"pergunta": "tenho direito ao bpc?"})
    assert final["avaliacao"].resultado is Resultado.INDETERMINADO
    assert final["aguardando"] == "rota"
    assert "deficiência" in final["resposta"]


def test_atalho_quando_a_primeira_fala_ja_tem_tudo():
    """Se o LLM extrai o Caso completo numa só fala, avalia direto — sem
    perguntar mais nada (comportamento equivalente ao de antes do P2)."""
    tudo = {
        "rota": "idade",
        "requerente": {"idade_anos": 68, "renda_trabalho": 0},
        "membros_coletado": True,
        "outros_membros": [],
        "renda_coletada": True,
        "saude_coletada": True,
    }
    grafo = construir_grafo(FakeLLM(atualizacoes=[tudo]))
    final = grafo.invoke({"pergunta": "tenho 68 anos e não tenho renda, tenho direito?"})
    assert final["avaliacao"].resultado is Resultado.ATENDE
    assert final["aguardando"] is None
    assert final["caso"] is not None


def test_coleta_pergunta_um_dado_por_vez():
    grafo = construir_grafo(FakeLLM(atualizacoes=[{}]))  # fala não traz nada extraível
    final = grafo.invoke({"pergunta": "tenho direito ao bpc?"})
    assert final["avaliacao"].resultado is Resultado.INDETERMINADO
    assert final["aguardando"] == "rota"
    assert final["opcoes"] == ["Por idade (65 anos ou mais)", "Por deficiência"]


def test_conversa_multiturno_ate_o_veredito():
    """5 turnos: rota → idade → membros → renda → saúde, acumulando o
    caso_parcial entre eles, como o chat.py faz carregando o estado."""
    grafo = construir_grafo(
        FakeLLM(
            atualizacoes=[
                {"rota": "idade"},
                {"requerente": {"idade_anos": 70}},
                {"membros_coletado": True, "outros_membros": []},
                {"renda_coletada": True, "requerente": {"renda_trabalho": 0}},
                {"saude_coletada": True},
            ]
        )
    )
    estado: dict = {}
    falas = [
        "Minha mãe tem direito ao BPC?",
        "Ela tem 70 anos",
        "Mora só",
        "Não tem nenhuma renda",
        "Não tem gastos de saúde",
    ]
    for fala in falas:
        estado = grafo.invoke({**estado, "pergunta": fala})

    assert estado["avaliacao"].resultado is Resultado.ATENDE
    assert estado["aguardando"] is None
    assert estado["caso"].requerente.idade_anos == 70
    assert len(estado["mensagens"]) == 10  # 5 falas do usuário + 5 respostas do amparo


def test_desvio_no_meio_da_coleta_responde_pelo_rag_e_mantem_o_caso_parcial(monkeypatch):
    from amparo import rag

    monkeypatch.setattr(rag, "client", lambda: None)
    monkeypatch.setattr(
        rag, "search", lambda *a, **k: [{"texto": "...", "titulo": "t", "fonte": "u"}]
    )
    grafo = construir_grafo(
        FakeLLM(
            atualizacoes=[{"rota": "idade"}, {"requerente": {"idade_anos": 70}}],
            texto="Os documentos são X e Y.",
        )
    )
    estado = grafo.invoke({"pergunta": "Minha mãe tem direito ao BPC?"})
    assert estado["aguardando"] == "idade"
    caso_parcial_antes = dict(estado["caso_parcial"])

    estado = grafo.invoke({**estado, "pergunta": "e quais documentos preciso levar?"})
    assert estado["intencao"] is Intencao.CHECKLIST
    assert "Os documentos são X e Y." in estado["resposta"]
    assert estado["aguardando"] == "idade"  # não avançou nem perdeu o que já tinha
    assert estado["caso_parcial"] == caso_parcial_antes

    # a conversa retoma de onde parou
    estado = grafo.invoke({**estado, "pergunta": "70 anos"})
    assert estado["aguardando"] == "membros"


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
