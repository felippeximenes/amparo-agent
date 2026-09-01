"""Especificação do motor de elegibilidade ao BPC (seam: `avaliar`)."""

from datetime import date
from decimal import Decimal

from amparo.rules.elegibilidade import (
    PARAMETROS_2025,
    Caso,
    CategoriaDeducao,
    Membro,
    Parametros,
    Resultado,
    Rota,
    avaliar,
)

SM = Decimal("1518.00")
UM_QUARTO = Decimal("379.50")  # 1518 / 4


def idoso(**kw) -> Membro:
    kw.setdefault("idade_anos", 70)
    return Membro(**kw)


# --- rota idade: gate de idade ------------------------------------------------

def test_requerente_com_64_anos_nao_atende_pela_idade():
    r = avaliar(Caso(rota=Rota.IDADE, requerente=Membro(idade_anos=64)))
    assert r.resultado is Resultado.NAO_ATENDE
    assert "65" in r.motivo


def test_65_completos_com_renda_zero_atende():
    r = avaliar(Caso(rota=Rota.IDADE, requerente=Membro(idade_anos=65)))
    assert r.resultado is Resultado.ATENDE


# --- critério de renda: bordas ---------------------------------------------------

def test_renda_per_capita_exatamente_um_quarto_do_sm_atende():
    r = avaliar(Caso(rota=Rota.IDADE, requerente=idoso(renda_trabalho=UM_QUARTO)))
    assert r.resultado is Resultado.ATENDE
    assert r.renda_per_capita == UM_QUARTO
    assert r.limite_renda == UM_QUARTO


def test_um_centavo_acima_do_limite_nao_atende():
    r = avaliar(
        Caso(rota=Rota.IDADE, requerente=idoso(renda_trabalho=Decimal("379.51")))
    )
    assert r.resultado is Resultado.NAO_ATENDE
    assert "renda" in r.motivo.lower()


# --- divisor: número de membros do grupo familiar ------------------------------

def test_familia_de_uma_pessoa_divide_por_um():
    r = avaliar(Caso(rota=Rota.IDADE, requerente=idoso(renda_trabalho=Decimal("300"))))
    assert r.renda_per_capita == Decimal("300")


def test_renda_dividida_pelo_numero_de_membros():
    r = avaliar(
        Caso(
            rota=Rota.IDADE,
            requerente=idoso(renda_trabalho=Decimal("1200")),
            outros_membros=(
                Membro(idade_anos=40),
                Membro(idade_anos=15),
                Membro(idade_anos=10),
            ),
        )
    )
    assert r.renda_per_capita == Decimal("300")  # 1200 / 4
    assert r.resultado is Resultado.ATENDE


# --- exclusões de renda -------------------------------------------------------

def test_um_beneficio_previdenciario_de_1sm_do_idoso_nao_conta():
    r = avaliar(
        Caso(rota=Rota.IDADE, requerente=idoso(beneficios_previdenciarios=(SM,)))
    )
    assert r.renda_per_capita == Decimal("0")
    assert r.resultado is Resultado.ATENDE


def test_apenas_um_beneficio_de_1sm_e_excluido_por_membro():
    r = avaliar(
        Caso(rota=Rota.IDADE, requerente=idoso(beneficios_previdenciarios=(SM, SM)))
    )
    assert r.renda_per_capita == SM  # um excluído, o outro conta
    assert r.resultado is Resultado.NAO_ATENDE


def test_exclusao_nao_se_aplica_a_membro_jovem_sem_deficiencia():
    r = avaliar(
        Caso(
            rota=Rota.IDADE,
            requerente=idoso(),
            outros_membros=(
                Membro(idade_anos=30, beneficios_previdenciarios=(SM,)),
            ),
        )
    )
    assert r.renda_per_capita == SM / 2  # nada excluído, 2 membros


def test_estagio_aprendizagem_barragens_auxilio_inclusao_nao_contam():
    r = avaliar(
        Caso(rota=Rota.IDADE, requerente=idoso(renda_excluida=Decimal("5000")))
    )
    assert r.renda_per_capita == Decimal("0")


# --- deduções de saúde (Anexo I da Portaria 34/2025) --------------------------

def test_deducoes_de_saude_abatem_da_renda_bruta():
    r = avaliar(
        Caso(
            rota=Rota.IDADE,
            requerente=idoso(renda_trabalho=Decimal("500")),
            deducoes_saude=frozenset(
                {CategoriaDeducao.FRALDAS, CategoriaDeducao.MEDICAMENTOS}
            ),
        )
    )
    assert r.renda_per_capita == Decimal("356.00")  # 500 - 99 - 45
    assert r.resultado is Resultado.ATENDE


def test_deducao_maior_que_a_renda_nao_deixa_per_capita_negativa():
    r = avaliar(
        Caso(
            rota=Rota.IDADE,
            requerente=idoso(renda_trabalho=Decimal("50")),
            deducoes_saude=frozenset({CategoriaDeducao.ALIMENTACAO_ESPECIAL}),  # 121
        )
    )
    assert r.renda_per_capita == Decimal("0")
    assert r.resultado is Resultado.ATENDE


# --- rota deficiência -------------------------------------------------------------

def test_impedimento_menor_que_2_anos_nao_atende():
    r = avaliar(
        Caso(
            rota=Rota.DEFICIENCIA,
            requerente=Membro(idade_anos=30),
            impedimento_min_2_anos=False,
        )
    )
    assert r.resultado is Resultado.NAO_ATENDE
    assert "2 anos" in r.motivo


def test_deficiencia_com_renda_ok_depende_de_avaliacao_do_inss():
    r = avaliar(
        Caso(
            rota=Rota.DEFICIENCIA,
            requerente=Membro(idade_anos=30),
            impedimento_min_2_anos=True,
        )
    )
    assert r.resultado is Resultado.DEPENDE_DE_AVALIACAO
    assert "biopsicossocial" in r.motivo.lower()


def test_deficiencia_sem_duracao_informada_ainda_depende_de_avaliacao():
    r = avaliar(
        Caso(rota=Rota.DEFICIENCIA, requerente=Membro(idade_anos=30))
    )
    assert r.resultado is Resultado.DEPENDE_DE_AVALIACAO


def test_deficiencia_com_renda_acima_do_limite_nao_atende_por_renda():
    r = avaliar(
        Caso(
            rota=Rota.DEFICIENCIA,
            requerente=Membro(idade_anos=30, renda_trabalho=SM),
            impedimento_min_2_anos=True,
        )
    )
    assert r.resultado is Resultado.NAO_ATENDE
    assert "renda" in r.motivo.lower()


def test_jovem_com_deficiencia_nao_e_barrado_pela_idade():
    r = avaliar(
        Caso(
            rota=Rota.DEFICIENCIA,
            requerente=Membro(idade_anos=25),
            impedimento_min_2_anos=True,
        )
    )
    assert r.resultado is Resultado.DEPENDE_DE_AVALIACAO


# --- parâmetros vigentes configuráveis --------------------------------------------

def test_salario_minimo_diferente_muda_o_limite_de_renda():
    params = Parametros(
        vigencia=date(2026, 1, 1),
        salario_minimo=Decimal("1600.00"),
        deducao_saude=PARAMETROS_2025.deducao_saude,
    )
    r = avaliar(
        Caso(rota=Rota.IDADE, requerente=idoso(renda_trabalho=Decimal("400"))), params
    )
    assert r.limite_renda == Decimal("400")  # 1600 / 4
    assert r.resultado is Resultado.ATENDE  # 400 <= 400


def test_avaliacao_sempre_cita_fonte():
    for caso in (
        Caso(rota=Rota.IDADE, requerente=Membro(idade_anos=64)),
        Caso(rota=Rota.IDADE, requerente=Membro(idade_anos=70)),
        Caso(
            rota=Rota.DEFICIENCIA,
            requerente=Membro(idade_anos=30),
            impedimento_min_2_anos=True,
        ),
    ):
        assert avaliar(caso).fontes
