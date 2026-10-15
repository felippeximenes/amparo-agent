"""Coleta progressiva do Caso de elegibilidade (seam: `proximo_dado_faltante`,
`fundir_caso_parcial`)."""

from amparo.coleta import (
    PERGUNTAS,
    filtrar_atualizacoes_vazias,
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


# --- filtrar_atualizacoes_vazias: confirmação vazia exige a pergunta certa ---
# Resposta vazia (outros_membros=[], renda zero, deducoes_saude=[]) só vale
# quando responde à pergunta que foi de fato feita (`aguardando`); fora disso
# é descartada (a pergunta é repetida). Valor NÃO vazio vale a qualquer hora.

def test_outros_membros_vazio_e_descartado_fora_da_etapa_membros():
    atualizacoes = {"outros_membros": []}
    assert filtrar_atualizacoes_vazias(atualizacoes, "idade") == {}


def test_outros_membros_vazio_e_aceito_na_etapa_membros():
    atualizacoes = {"outros_membros": []}
    assert filtrar_atualizacoes_vazias(atualizacoes, "membros") == {"outros_membros": []}


def test_outros_membros_nao_vazio_e_aceito_a_qualquer_hora():
    atualizacoes = {"outros_membros": [{"idade_anos": 40, "renda_trabalho": 2000}]}
    assert filtrar_atualizacoes_vazias(atualizacoes, "rota") == atualizacoes


def test_deducoes_saude_vazia_e_descartada_fora_da_etapa_saude():
    assert filtrar_atualizacoes_vazias({"deducoes_saude": []}, "renda") == {}


def test_deducoes_saude_vazia_e_aceita_na_etapa_saude():
    atualizacoes = {"deducoes_saude": []}
    assert filtrar_atualizacoes_vazias(atualizacoes, "saude") == atualizacoes


def test_deducoes_saude_nao_vazia_e_aceita_a_qualquer_hora():
    atualizacoes = {"deducoes_saude": ["fraldas"]}
    assert filtrar_atualizacoes_vazias(atualizacoes, "rota") == atualizacoes


def test_renda_zero_do_requerente_e_descartada_fora_da_etapa_renda():
    atualizacoes = {"requerente": {"idade_anos": 70, "renda_trabalho": 0}}
    filtrado = filtrar_atualizacoes_vazias(atualizacoes, "membros")
    assert filtrado["requerente"] == {"idade_anos": 70}


def test_renda_zero_do_requerente_e_aceita_na_etapa_renda():
    atualizacoes = {"requerente": {"renda_trabalho": 0}}
    assert filtrar_atualizacoes_vazias(atualizacoes, "renda") == atualizacoes


def test_renda_maior_que_zero_do_requerente_e_aceita_a_qualquer_hora():
    atualizacoes = {"requerente": {"renda_trabalho": 800}}
    assert filtrar_atualizacoes_vazias(atualizacoes, "rota") == atualizacoes


def test_renda_zero_de_outro_membro_e_descartada_fora_da_etapa_renda():
    atualizacoes = {"outros_membros": [{"idade_anos": 40, "renda_trabalho": 0}]}
    filtrado = filtrar_atualizacoes_vazias(atualizacoes, "membros")
    assert filtrado["outros_membros"] == [{"idade_anos": 40}]


def test_renda_maior_que_zero_de_outro_membro_e_aceita_fora_da_etapa_renda():
    atualizacoes = {"outros_membros": [{"idade_anos": 40, "renda_trabalho": 2000}]}
    filtrado = filtrar_atualizacoes_vazias(atualizacoes, "membros")
    assert filtrado["outros_membros"] == atualizacoes["outros_membros"]
