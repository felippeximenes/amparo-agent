"""Coleta progressiva do Caso de elegibilidade (seam: `proximo_dado_faltante`,
`fundir_caso_parcial`)."""

from amparo.coleta import (
    PERGUNTAS,
    fundir_caso_parcial,
    marcar_etapas_respondidas,
    proximo_dado_faltante,
)


# --- proximo_dado_faltante: ordem da coleta -----------------------------------

def test_caso_vazio_pede_a_rota():
    assert proximo_dado_faltante({}) == "rota"


def test_rota_idade_sem_idade_pede_a_idade():
    assert proximo_dado_faltante({"rota": "idade"}) == "idade"


def test_rota_idade_com_idade_pede_membros():
    caso = {"rota": "idade", "requerente": {"idade_anos": 70}}
    assert proximo_dado_faltante(caso) == "membros"


def test_rota_deficiencia_sem_impedimento_pede_impedimento():
    assert proximo_dado_faltante({"rota": "deficiencia"}) == "impedimento"


def test_rota_deficiencia_com_impedimento_pede_membros():
    caso = {"rota": "deficiencia", "impedimento_min_2_anos": True}
    assert proximo_dado_faltante(caso) == "membros"


def test_membros_coletado_pede_renda():
    caso = {
        "rota": "idade",
        "requerente": {"idade_anos": 70},
        "membros_coletado": True,
    }
    assert proximo_dado_faltante(caso) == "renda"


def test_renda_coletada_pede_saude():
    caso = {
        "rota": "idade",
        "requerente": {"idade_anos": 70},
        "membros_coletado": True,
        "renda_coletada": True,
    }
    assert proximo_dado_faltante(caso) == "saude"


def test_tudo_coletado_nao_falta_nada():
    caso = {
        "rota": "idade",
        "requerente": {"idade_anos": 70},
        "membros_coletado": True,
        "renda_coletada": True,
        "saude_coletada": True,
    }
    assert proximo_dado_faltante(caso) is None


def test_todas_as_perguntas_tem_texto():
    for passo, pergunta in PERGUNTAS.items():
        assert pergunta["texto"]
        assert isinstance(pergunta["opcoes"], list)


# --- fundir_caso_parcial: fusão pura, sem decidir o que falta -----------------

def test_fundir_adiciona_campo_novo():
    assert fundir_caso_parcial({}, {"rota": "idade"}) == {"rota": "idade"}


def test_fundir_mescla_requerente_campo_a_campo():
    atual = {"requerente": {"idade_anos": 70}}
    novo = {"requerente": {"renda_trabalho": 300}}
    fundido = fundir_caso_parcial(atual, novo)
    assert fundido["requerente"] == {"idade_anos": 70, "renda_trabalho": 300}


def test_fundir_nao_apaga_campos_nao_mencionados():
    atual = {"rota": "idade", "requerente": {"idade_anos": 70}}
    fundido = fundir_caso_parcial(atual, {"membros_coletado": True})
    assert fundido["rota"] == "idade"
    assert fundido["requerente"] == {"idade_anos": 70}
    assert fundido["membros_coletado"] is True


def test_fundir_substitui_lista_completa_de_outros_membros():
    atual = {"outros_membros": [{"idade_anos": 10}]}
    novo = {"outros_membros": [{"idade_anos": 10}, {"idade_anos": 40}]}
    assert fundir_caso_parcial(atual, novo)["outros_membros"] == novo["outros_membros"]


# --- marcar_etapas_respondidas: deriva os marcadores da presença explícita ---
# dos dados em caso_parcial — nunca de um marcador que o LLM tenha devolvido.

def test_marca_membros_quando_outros_membros_presente_mesmo_vazio():
    assert marcar_etapas_respondidas({"outros_membros": []})["membros_coletado"] is True


def test_nao_marca_membros_sem_outros_membros():
    assert marcar_etapas_respondidas({})["membros_coletado"] is False


def test_marca_renda_quando_requerente_tem_renda_explicita_sem_outros_membros():
    caso = {"outros_membros": [], "requerente": {"renda_trabalho": 0}}
    assert marcar_etapas_respondidas(caso)["renda_coletada"] is True


def test_nao_marca_renda_sem_renda_do_requerente():
    caso = {"outros_membros": [], "requerente": {}}
    assert marcar_etapas_respondidas(caso)["renda_coletada"] is False


def test_nao_marca_renda_se_falta_renda_de_outro_membro():
    caso = {
        "outros_membros": [{"idade_anos": 40}],
        "requerente": {"renda_trabalho": 0},
    }
    assert marcar_etapas_respondidas(caso)["renda_coletada"] is False


def test_marca_renda_quando_todos_os_membros_tem_renda_explicita():
    caso = {
        "outros_membros": [{"idade_anos": 40, "renda_trabalho": 3000}],
        "requerente": {"renda_trabalho": 0},
    }
    assert marcar_etapas_respondidas(caso)["renda_coletada"] is True


def test_beneficio_ou_renda_excluida_tambem_contam_como_renda_explicita():
    caso = {"outros_membros": [], "requerente": {"beneficios_previdenciarios": [1518]}}
    assert marcar_etapas_respondidas(caso)["renda_coletada"] is True


def test_marca_saude_quando_deducoes_saude_presente_mesmo_vazia():
    assert marcar_etapas_respondidas({"deducoes_saude": []})["saude_coletada"] is True


def test_nao_marca_saude_sem_deducoes_saude():
    assert marcar_etapas_respondidas({})["saude_coletada"] is False


def test_marcador_vindo_do_llm_e_sobrescrito_pela_checagem_real():
    """Um `membros_coletado=True` (indevido, vindo do LLM ou de um estado
    anterior inconsistente) é sobrescrito pela checagem real dos dados."""
    caso = {"membros_coletado": True}
    assert marcar_etapas_respondidas(caso)["membros_coletado"] is False
