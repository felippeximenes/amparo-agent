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
    de `extrair_atualizacoes`, um por chamada (fila vazia → `{}`, sem
    novidade). `intencoes`, se dado, é a fila de categorias que
    `classificar_intencao` devolve (uma por chamada); `None` (não dado) faz
    `classificar_intencao` sempre devolver `None` — cai na palavra-chave,
    igual a quando não há sinal nenhum do LLM para a intenção."""

    def __init__(
        self,
        atualizacoes: list[dict] | None = None,
        texto: str = "RESPOSTA DO MODELO",
        intencoes: list[str | None] | None = None,
    ):
        self._fila = list(atualizacoes or [])
        self._texto = texto
        self._fila_intencoes = list(intencoes) if intencoes is not None else None

    def extrair_atualizacoes(self, mensagens, caso_parcial):  # noqa: ARG002
        return self._fila.pop(0) if self._fila else {}

    def classificar_intencao(self, pergunta):  # noqa: ARG002
        if self._fila_intencoes is None:
            return None
        return self._fila_intencoes.pop(0) if self._fila_intencoes else None

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


# --- classificação de intenção pelo LLM: frases coloquiais reais -------------
# O FakeLLM simula a categoria que um modelo bem-instruído devolveria para
# cada fala — a palavra-chave (3 categorias) não distingue saudação, fora de
# escopo ou apagar, e é frágil a erro de digitação/sem acento.

@pytest.mark.parametrize(
    "fala,categoria,esperada",
    [
        ("oi", "saudacao", Intencao.SAUDACAO),
        ("boa tarde", "saudacao", Intencao.SAUDACAO),
        ("bom dia, preciso de ajuda", "saudacao", Intencao.SAUDACAO),
        ("oii, alguem pode me ajudar", "saudacao", Intencao.SAUDACAO),
        ("quanto é o auxílio-doença?", "fora_de_escopo", Intencao.FORA_DE_ESCOPO),
        (
            "e a aposentadoria por invalidez, dá pra pedir junto?",
            "fora_de_escopo",
            Intencao.FORA_DE_ESCOPO,
        ),
        ("quero apagar meus dados", "apagar", Intencao.APAGAR),
        ("pode apagar tudo que eu disse?", "apagar", Intencao.APAGAR),
        ("minha vo tem 68 anos ela pode pegar o loas", "elegibilidade", Intencao.ELEGIBILIDADE),
        ("quero saber se eu tenho direito", "elegibilidade", Intencao.ELEGIBILIDADE),
        (
            "beneficio da minha vó, quais documentos precisa?",
            "checklist",
            Intencao.CHECKLIST,
        ),
        ("como faço pra dar entrada no bpc", "checklist", Intencao.CHECKLIST),
        ("o que é o bpc?", "duvida", Intencao.DUVIDA),
        ("pra que serve a loas", "duvida", Intencao.DUVIDA),
        ("qnto ganha quem recebe o bpc", "duvida", Intencao.DUVIDA),
        ("asdkjh qwerty 123 blablabla", "incompreensivel", Intencao.INCOMPREENSIVEL),
    ],
)
def test_classificacao_llm_cobre_frases_coloquiais(monkeypatch, fala, categoria, esperada):
    from amparo import rag

    monkeypatch.setattr(rag, "client", lambda: None)
    monkeypatch.setattr(rag, "search", lambda *a, **k: [])
    grafo = construir_grafo(FakeLLM(intencoes=[categoria]))
    final = grafo.invoke({"pergunta": fala})
    assert final["intencao"] is esperada


# --- fallback_node: saudação, fora de escopo, incompreensível, apagar ------

def test_saudacao_tem_boas_vindas_disclaimer_e_nao_fala_de_elegibilidade():
    grafo = construir_grafo(FakeLLM(intencoes=["saudacao"]))
    final = grafo.invoke({"pergunta": "oi"})
    assert "BPC" in final["resposta"]
    assert DISCLAIMER in final["resposta"]
    assert final.get("avaliacao") is None


def test_fora_de_escopo_encaminha_para_inss_ou_defensoria():
    grafo = construir_grafo(FakeLLM(intencoes=["fora_de_escopo"]))
    final = grafo.invoke({"pergunta": "quanto é o auxílio-doença?"})
    assert "135" in final["resposta"] or "Defensoria" in final["resposta"]
    assert DISCLAIMER in final["resposta"]


def test_incompreensivel_pede_para_reformular_com_exemplo():
    grafo = construir_grafo(FakeLLM(intencoes=["incompreensivel"]))
    final = grafo.invoke({"pergunta": "asdkjh qwerty"})
    assert "reformular" in final["resposta"].lower()
    assert "?" in final["resposta"]  # traz um exemplo de pergunta


def test_apagar_fica_marcado_na_intencao_para_o_canal_apagar_a_sessao():
    """O grafo só confirma o texto — quem apaga de fato é o canal
    (scripts/chat.py), lendo `intencao` depois do invoke()."""
    grafo = construir_grafo(FakeLLM(intencoes=["apagar"]))
    final = grafo.invoke({"pergunta": "quero apagar meus dados"})
    assert final["intencao"] is Intencao.APAGAR
    assert "apagar" in final["resposta"].lower()


# --- desvio claro em meio à coleta: agora inclui dúvida explícita e apagar -

def test_duvida_explicita_via_llm_interrompe_a_coleta_e_depois_retoma(monkeypatch):
    from amparo import rag

    monkeypatch.setattr(rag, "client", lambda: None)
    monkeypatch.setattr(
        rag, "search", lambda *a, **k: [{"texto": "x", "titulo": "t", "fonte": "u"}]
    )
    grafo = construir_grafo(FakeLLM(atualizacoes=[{}], intencoes=[None, "duvida"]))
    estado = grafo.invoke({"pergunta": "Minha mãe tem direito ao BPC?"})
    assert estado["aguardando"] == "rota"

    estado = grafo.invoke({**estado, "pergunta": "o que é o bpc, afinal?"})
    assert estado["intencao"] is Intencao.DUVIDA
    assert estado["aguardando"] == "rota"  # não perdeu o que já tinha


def test_apagar_via_llm_interrompe_a_coleta():
    grafo = construir_grafo(FakeLLM(atualizacoes=[{}], intencoes=[None, "apagar"]))
    estado = grafo.invoke({"pergunta": "Minha mãe tem direito ao BPC?"})
    assert estado["aguardando"] == "rota"

    estado = grafo.invoke({**estado, "pergunta": "na verdade apaga meus dados"})
    assert estado["intencao"] is Intencao.APAGAR


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


def test_texto_fallback_tem_prioridade_sobre_avaliacao_e_rag():
    a = avaliar(Caso(rota=Rota.IDADE, requerente=Membro(idade_anos=70)))
    texto = compor_resposta(
        texto_fallback="Oi! Sou o Amparo.",
        avaliacao=a,
        trechos=[{"texto": "x", "titulo": "t", "fonte": "u"}],
        texto_rag="explicação do modelo",
    )
    assert "Oi! Sou o Amparo." in texto
    assert "Pelos dados informados" not in texto
    assert "explicação do modelo" not in texto
    assert DISCLAIMER in texto


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


def test_primeira_fala_completa_ainda_confirma_as_etapas_vazias():
    """Dados não vazios (rota, idade) da primeira fala são aproveitados de
    cara — mas confirmações vazias (mora só, sem renda) só valem quando
    respondem à pergunta certa: a coleta pede membros, renda e saúde de
    novo, uma por vez, mesmo já tendo sido "ditas" na primeira fala."""
    grafo = construir_grafo(
        FakeLLM(
            atualizacoes=[
                {"rota": "idade", "requerente": {"idade_anos": 70}, "outros_membros": []},
                {"outros_membros": []},
                {"requerente": {"renda_trabalho": 0}},
                {"deducoes_saude": []},
            ]
        )
    )
    estado: dict = {}
    falas = [
        "minha mãe tem 70 anos, mora sozinha e não tem renda, ela tem direito ao bpc?",
        "sim, mora só",
        "nenhuma renda",
        "não",
    ]
    estado = grafo.invoke({**estado, "pergunta": falas[0]})
    assert estado["aguardando"] == "membros"  # idade ficou; "mora sozinha" ainda não foi confirmado

    for fala in falas[1:]:
        estado = grafo.invoke({**estado, "pergunta": fala})

    assert estado["avaliacao"].resultado is Resultado.ATENDE
    assert estado["aguardando"] is None


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
                {"outros_membros": []},
                {"requerente": {"renda_trabalho": 0}},
                {"deducoes_saude": []},
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


# --- regressão: marcadores de etapa são do código, nunca do LLM -------------
# (bug real: gpt-4o-mini pulava a pergunta de "membros" devolvendo
# membros_coletado=true sem outros_membros — violava a regra 1 do CLAUDE.md)

def test_regressao_a_rota_e_idade_em_falas_separadas_ainda_pede_membros():
    grafo = construir_grafo(
        FakeLLM(atualizacoes=[{}, {"rota": "idade"}, {"requerente": {"idade_anos": 70}}])
    )
    estado: dict = {}
    for fala in ("Minha mãe tem direito ao BPC?", "Por idade", "Ela tem 70 anos"):
        estado = grafo.invoke({**estado, "pergunta": fala})
    assert estado["aguardando"] == "membros"


def test_regressao_marcador_de_etapa_do_llm_e_ignorado():
    grafo = construir_grafo(
        FakeLLM(
            atualizacoes=[
                {
                    "rota": "idade",
                    "requerente": {"idade_anos": 70},
                    "membros_coletado": True,  # o LLM não devolve mais isso; se devolver, é ignorado
                    "renda_coletada": True,
                    "saude_coletada": True,
                }
            ]
        )
    )
    final = grafo.invoke({"pergunta": "Minha mãe de 70 anos tem direito ao BPC?"})
    assert final["aguardando"] == "membros"


def test_regressao_irmao_com_renda_junto_derruba_para_nao_atende():
    grafo = construir_grafo(
        FakeLLM(
            atualizacoes=[
                {"rota": "idade", "requerente": {"idade_anos": 70}},
                {"outros_membros": [{"idade_anos": 40, "renda_trabalho": 3000}]},
                {"requerente": {"renda_trabalho": 0}},
                {"deducoes_saude": []},
            ]
        )
    )
    estado: dict = {}
    falas = [
        "Minha mãe de 70 anos tem direito ao BPC?",
        "mora com meu irmão de 40 anos que ganha 3000",
        "ela não tem renda",
        "sem gastos de saúde",
    ]
    for fala in falas:
        estado = grafo.invoke({**estado, "pergunta": fala})
    assert estado["avaliacao"].resultado is Resultado.NAO_ATENDE


# --- regressão (Passo 0): confirmação vazia exige a etapa certa -------------

def test_regressao_outros_membros_vazio_fora_da_etapa_membros_e_descartado():
    """Um LLM que devolve outros_membros=[] respondendo à pergunta de idade
    (bug/alucinação) não fecha a etapa de membros — ela é perguntada."""
    grafo = construir_grafo(
        FakeLLM(atualizacoes=[{}, {"rota": "idade"}, {"outros_membros": []}])
    )
    estado: dict = {}
    for fala in ("Minha mãe tem direito ao BPC?", "Por idade", "qualquer coisa"):
        estado = grafo.invoke({**estado, "pergunta": fala})
    assert estado["aguardando"] == "idade"


def test_regressao_renda_de_membro_mencionada_antes_da_hora_e_aproveitada():
    """Valor NÃO vazio (renda > 0 de um membro) é aproveitado mesmo chegando
    antes de a etapa de renda ser perguntada — só a confirmação vazia exige
    a etapa certa, não o dado real."""
    grafo = construir_grafo(
        FakeLLM(
            atualizacoes=[{"outros_membros": [{"idade_anos": 40, "renda_trabalho": 2000}]}]
        )
    )
    final = grafo.invoke(
        {"pergunta": "Minha mãe tem direito? Mora com o filho que ganha 2000"}
    )
    assert final["caso_parcial"]["outros_membros"] == [
        {"idade_anos": 40, "renda_trabalho": 2000}
    ]


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


# --- checkpointer: persiste por thread_id sem repassar o estado na mão ------

def test_com_checkpointer_a_conversa_persiste_por_thread_id():
    from langgraph.checkpoint.sqlite import SqliteSaver

    with SqliteSaver.from_conn_string(":memory:") as checkpointer:
        grafo = construir_grafo(
            FakeLLM(atualizacoes=[{}, {"rota": "idade"}]), checkpointer=checkpointer
        )
        config = {"configurable": {"thread_id": "t1"}}
        grafo.invoke({"pergunta": "Minha mãe tem direito ao BPC?"}, config)
        # não repasso o estado anterior — o checkpointer é quem carrega
        final = grafo.invoke({"pergunta": "Por idade"}, config)
        assert final["aguardando"] == "idade"  # "rota" só persistiu por causa do thread_id


def test_threads_diferentes_nao_compartilham_caso_parcial():
    from langgraph.checkpoint.sqlite import SqliteSaver

    with SqliteSaver.from_conn_string(":memory:") as checkpointer:
        grafo = construir_grafo(
            FakeLLM(atualizacoes=[{"rota": "idade"}, {}]), checkpointer=checkpointer
        )
        grafo.invoke(
            {"pergunta": "Minha mãe tem direito?"}, {"configurable": {"thread_id": "a"}}
        )
        outra_thread = grafo.invoke(
            {"pergunta": "Minha mãe tem direito?"}, {"configurable": {"thread_id": "b"}}
        )
        assert outra_thread["aguardando"] == "rota"  # não herdou o "rota" da thread "a"
