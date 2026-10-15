"""Coleta progressiva do Caso de elegibilidade (seam: `proximo_dado_faltante`,
`fundir_caso_parcial`)."""

from amparo.coleta import (
    PERGUNTAS,
    deduplicar_renda,
    filtrar_atualizacoes_vazias,
    filtrar_grupo_familiar,
    fundir_caso_parcial,
    inferir_rota_por_idade,
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


def test_fundir_aceita_lista_maior_de_outros_membros():
    atual = {"outros_membros": [{"idade_anos": 10}]}
    novo = {"outros_membros": [{"idade_anos": 10}, {"idade_anos": 40}]}
    assert fundir_caso_parcial(atual, novo)["outros_membros"] == novo["outros_membros"]


def test_fundir_outros_membros_mescla_por_posicao_sem_perder_campo_antigo():
    """Regressão: o LLM às vezes restabelece 'outros_membros' só com o campo
    novo (ex.: renda), perdendo parentesco/idade já coletados antes — a
    fusão por posição preserva o que não foi restabelecido."""
    atual = {
        "outros_membros": [
            {"idade_anos": 65, "parentesco": "irmao", "solteiro": False}
        ]
    }
    novo = {"outros_membros": [{"renda_trabalho": 1621}]}
    fundido = fundir_caso_parcial(atual, novo)
    assert fundido["outros_membros"] == [
        {"idade_anos": 65, "parentesco": "irmao", "solteiro": False, "renda_trabalho": 1621}
    ]


def test_fundir_outros_membros_lista_vazia_explicita_zera_tudo():
    """"mora só" (lista vazia explícita) continua zerando, não é afetado
    pela fusão por posição."""
    atual = {"outros_membros": [{"idade_anos": 40}]}
    novo = {"outros_membros": []}
    assert fundir_caso_parcial(atual, novo)["outros_membros"] == []


def test_fundir_outros_membros_lista_menor_reflete_remocao():
    atual = {"outros_membros": [{"idade_anos": 10}, {"idade_anos": 40}]}
    novo = {"outros_membros": [{"idade_anos": 10}]}
    assert fundir_caso_parcial(atual, novo)["outros_membros"] == [{"idade_anos": 10}]


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


# --- inferir_rota_por_idade: regressão do P0 (idade >= 65 sem rota) ---------
# O LLM extrai idade_anos corretamente mas nem sempre preenche "rota" sozinho
# — sem essa regra determinística, proximo_dado_faltante pede "rota" de novo
# mesmo com a idade (>= 65) já coletada.

def test_infere_rota_idade_quando_idoso_e_rota_ausente():
    caso = {"requerente": {"idade_anos": 68}}
    assert inferir_rota_por_idade(caso)["rota"] == "idade"


def test_infere_rota_exatamente_nos_65_anos():
    caso = {"requerente": {"idade_anos": 65}}
    assert inferir_rota_por_idade(caso)["rota"] == "idade"


def test_nao_infere_rota_para_menor_de_65():
    caso = {"requerente": {"idade_anos": 40}}
    assert "rota" not in inferir_rota_por_idade(caso)


def test_nao_sobrescreve_rota_deficiencia_ja_informada():
    """Mesmo com idade >= 65, se a pessoa já disse que é pela deficiência,
    a inferência não pode sobrescrever a escolha dela."""
    caso = {"rota": "deficiencia", "requerente": {"idade_anos": 70}}
    assert inferir_rota_por_idade(caso)["rota"] == "deficiencia"


def test_nao_falha_sem_requerente_ainda():
    assert inferir_rota_por_idade({}) == {}


def test_regressao_idade_dada_na_primeira_fala_nao_pede_rota_de_novo():
    """Reproduz o bug: o LLM extrai só a idade (sem "rota") na primeira
    fala — a etapa seguinte não pode ser "rota" de novo."""
    caso_parcial = marcar_etapas_respondidas(
        inferir_rota_por_idade({"requerente": {"idade_anos": 68}})
    )
    assert proximo_dado_faltante(caso_parcial) != "rota"
    assert proximo_dado_faltante(caso_parcial) == "membros"


# --- filtrar_grupo_familiar: filho/irmão só entra se solteiro ---------------
# LOAS art. 20, §1º (CONTEXT.md, "Grupo familiar"): cônjuge/companheiro(a),
# pais, tutelados sempre contam; filhos, enteados e irmãos só se SOLTEIROS.

def test_filho_casado_fica_fora_do_grupo_familiar():
    membros = [{"idade_anos": 40, "parentesco": "filho_enteado", "solteiro": False}]
    assert filtrar_grupo_familiar(membros) == []


def test_filho_solteiro_continua_no_grupo_familiar():
    membros = [{"idade_anos": 40, "parentesco": "filho_enteado", "solteiro": True}]
    assert filtrar_grupo_familiar(membros) == membros


def test_irmao_casado_fica_fora_do_grupo_familiar():
    membros = [{"idade_anos": 30, "parentesco": "irmao", "solteiro": False}]
    assert filtrar_grupo_familiar(membros) == []


def test_conjuge_entra_mesmo_sem_campo_solteiro():
    membros = [{"idade_anos": 65, "parentesco": "conjuge"}]
    assert filtrar_grupo_familiar(membros) == membros


def test_estado_civil_desconhecido_nao_exclui():
    """Sem resposta sobre o estado civil, a pessoa continua no grupo —
    exclusão só quando se sabe explicitamente que é casado(a)."""
    membros = [{"idade_anos": 40, "parentesco": "filho_enteado"}]
    assert filtrar_grupo_familiar(membros) == membros


# --- deduplicar_renda: regressão real observada no eval_agente -------------
# O LLM às vezes repete o mesmo valor de aposentadoria/pensão em
# "renda_trabalho" E em "beneficios_previdenciarios" da mesma pessoa ao
# restabelecer "outros_membros" — isso contaria o benefício em dobro e
# bloquearia a exclusão de 1 SM do idoso/deficiente (que só vale para
# beneficios_previdenciarios).

def test_remove_renda_trabalho_duplicada_no_beneficio_do_requerente():
    caso = {"requerente": {"renda_trabalho": 1621, "beneficios_previdenciarios": [1621]}}
    assert deduplicar_renda(caso)["requerente"]["renda_trabalho"] == 0


def test_remove_renda_trabalho_duplicada_em_outro_membro():
    caso = {
        "outros_membros": [
            {"idade_anos": 65, "renda_trabalho": 1621, "beneficios_previdenciarios": [1621]}
        ]
    }
    assert deduplicar_renda(caso)["outros_membros"][0]["renda_trabalho"] == 0


def test_nao_remove_renda_trabalho_que_nao_e_duplicada():
    caso = {"requerente": {"renda_trabalho": 500, "beneficios_previdenciarios": [1621]}}
    assert deduplicar_renda(caso)["requerente"]["renda_trabalho"] == 500


def test_deduplicar_renda_sem_beneficios_nao_altera_nada():
    caso = {"requerente": {"renda_trabalho": 500}}
    assert deduplicar_renda(caso) == caso
