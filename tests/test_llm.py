"""Construção de `Caso` a partir do JSON do modelo (`caso_de_dict`)."""

from decimal import Decimal

from amparo.llm import caso_de_dict
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
