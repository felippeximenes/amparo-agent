"""Construção de `Caso` a partir do JSON do modelo (`caso_de_dict`)."""

from decimal import Decimal

from amparo.llm import caso_de_dict, interpretar_atualizacoes, interpretar_intencao
from amparo.rules.elegibilidade import CategoriaDeducao, Resultado, Rota, avaliar


def test_dict_completo_vira_caso():
    d = {
        "rota": "idade",
        "requerente": {"idade_anos": 70, "renda_trabalho": 300},
        "outros_membros": [{"idade_anos": 40, "renda_trabalho": 900}],
        "deducoes_saude": ["fraldas"],
    }
    caso = caso_de_dict(d)
    assert caso is not None
    assert caso.rota is Rota.IDADE
    assert caso.requerente.idade_anos == 70
    assert caso.requerente.renda_trabalho == Decimal("300")
    assert len(caso.outros_membros) == 1
    assert CategoriaDeducao.FRALDAS in caso.deducoes_saude


def test_rota_ausente_ou_invalida_retorna_none():
    assert caso_de_dict({"requerente": {"idade_anos": 70}}) is None
    assert caso_de_dict({"rota": "aposentadoria", "requerente": {"idade_anos": 70}}) is None


def test_rota_idade_sem_idade_do_requerente_retorna_none():
    assert caso_de_dict({"rota": "idade", "requerente": {"renda_trabalho": 0}}) is None


def test_rota_deficiencia_aceita_sem_idade():
    caso = caso_de_dict(
        {"rota": "deficiencia", "requerente": {"com_deficiencia": True},
         "impedimento_min_2_anos": True}
    )
    assert caso is not None
    assert caso.impedimento_min_2_anos is True


def test_beneficios_e_deducoes_desconhecidas_sao_tratados():
    d = {
        "rota": "idade",
        "requerente": {
            "idade_anos": 66,
            "beneficios_previdenciarios": [1518, "1518.00"],
            "renda_excluida": 500,
        },
        "deducoes_saude": ["fraldas", "categoria_inexistente"],
    }
    caso = caso_de_dict(d)
    assert caso is not None
    assert caso.requerente.beneficios_previdenciarios == (Decimal("1518"), Decimal("1518.00"))
    assert caso.deducoes_saude == frozenset({CategoriaDeducao.FRALDAS})
    # e o Caso montado roda no motor
    assert avaliar(caso).resultado in set(Resultado)


# --- grupo familiar: filho/irmão casado não entra no Caso -------------------

def test_filho_casado_nao_entra_no_caso():
    d = {
        "rota": "idade",
        "requerente": {"idade_anos": 70},
        "outros_membros": [
            {
                "idade_anos": 40,
                "parentesco": "filho_enteado",
                "solteiro": False,
                "renda_trabalho": 3000,
            }
        ],
    }
    caso = caso_de_dict(d)
    assert caso is not None
    assert caso.outros_membros == ()


def test_filho_solteiro_entra_no_caso():
    d = {
        "rota": "idade",
        "requerente": {"idade_anos": 70},
        "outros_membros": [
            {"idade_anos": 40, "parentesco": "filho_enteado", "solteiro": True}
        ],
    }
    caso = caso_de_dict(d)
    assert caso is not None
    assert len(caso.outros_membros) == 1


# --- interpretar_atualizacoes (parsing puro da saída do modelo) --------------

def test_interpretar_atualizacoes_de_json_valido():
    assert interpretar_atualizacoes('{"rota": "idade"}') == {"rota": "idade"}


def test_interpretar_atualizacoes_vazia():
    assert interpretar_atualizacoes("") == {}


def test_interpretar_atualizacoes_de_json_invalido():
    assert interpretar_atualizacoes("não é json") == {}


def test_interpretar_atualizacoes_de_lista_json_e_ignorada():
    assert interpretar_atualizacoes('["idade"]') == {}


def test_interpretar_atualizacoes_descarta_marcadores_de_etapa_do_modelo():
    saida = (
        '{"rota": "idade", "membros_coletado": true, '
        '"renda_coletada": true, "saude_coletada": true}'
    )
    assert interpretar_atualizacoes(saida) == {"rota": "idade"}


# --- interpretar_intencao (parsing puro da classificação de intenção) -------

def test_interpretar_intencao_categoria_valida():
    assert interpretar_intencao('{"intencao": "saudacao"}') == "saudacao"


def test_interpretar_intencao_vazia_cai_para_none():
    """`None` sinaliza "o LLM não respondeu nada usável" — quem chama cai na
    classificação por palavra-chave, não no fallback de incompreensível."""
    assert interpretar_intencao("") is None


def test_interpretar_intencao_json_invalido_e_incompreensivel():
    """O modelo respondeu algo, só não dá para interpretar — diferente de
    não ter respondido nada."""
    assert interpretar_intencao("não é json") == "incompreensivel"


def test_interpretar_intencao_categoria_desconhecida_e_incompreensivel():
    assert interpretar_intencao('{"intencao": "sei_nao"}') == "incompreensivel"


def test_interpretar_intencao_sem_a_chave_intencao_e_incompreensivel():
    assert interpretar_intencao('{"outra_coisa": 1}') == "incompreensivel"


def test_interpretar_intencao_de_lista_json_e_incompreensivel():
    assert interpretar_intencao('["saudacao"]') == "incompreensivel"
