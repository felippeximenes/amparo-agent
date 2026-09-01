"""Motor determinístico de elegibilidade ao BPC/LOAS.

Função pura: recebe um `Caso` + `Parametros` vigentes, devolve uma `Avaliacao`.
Escopo e limites em `docs/adr/0001-escopo-do-motor-de-elegibilidade.md` —
calcula idade e renda familiar per capita; nunca decide sobre deficiência.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum

IDADE_IDOSO = 65

_FONTE_IDADE = "LOAS (Lei 8.742/1993) art. 20; Estatuto da Pessoa Idosa art. 34"
_FONTE_RENDA = (
    "LOAS art. 20, §3º; Lei 14.176/2021; "
    "Portaria Conjunta MDS/INSS 34/2025 art. 8º e art. 11"
)
_FONTE_IMPEDIMENTO = "LOAS art. 20, §§2º e 10"
_FONTE_AVALIACAO = "LOAS art. 20, §6º; Portaria Conjunta MDS/INSS 34/2025 art. 13"


class Rota(Enum):
    IDADE = "idade"
    DEFICIENCIA = "deficiencia"


class Resultado(Enum):
    ATENDE = "atende"
    NAO_ATENDE = "nao_atende"
    DEPENDE_DE_AVALIACAO = "depende_de_avaliacao"
    INDETERMINADO = "indeterminado"  # produzido pelo eligibility_node quando faltam dados


class CategoriaDeducao(Enum):
    MEDICAMENTOS = "medicamentos"
    CONSULTAS = "consultas"
    FRALDAS = "fraldas"
    ALIMENTACAO_ESPECIAL = "alimentacao_especial"
    CENTRO_DIA = "centro_dia"


def _dec(v) -> Decimal:
    return v if isinstance(v, Decimal) else Decimal(str(v))


@dataclass(frozen=True)
class Membro:
    """Um membro do grupo familiar (a lista já vem filtrada pelo intake)."""

    idade_anos: int
    com_deficiencia: bool = False
    renda_trabalho: Decimal = Decimal(0)  # salário, informal, Bolsa Família, pró-labore...
    beneficios_previdenciarios: tuple[Decimal, ...] = ()
    renda_excluida: Decimal = Decimal(0)  # estágio, aprendizagem, barragens, auxílio-inclusão


@dataclass(frozen=True)
class Caso:
    rota: Rota
    requerente: Membro
    outros_membros: tuple[Membro, ...] = ()
    impedimento_min_2_anos: bool | None = None  # só rota DEFICIENCIA
    deducoes_saude: frozenset[CategoriaDeducao] = frozenset()


@dataclass(frozen=True)
class Parametros:
    vigencia: date
    salario_minimo: Decimal
    deducao_saude: Mapping[CategoriaDeducao, Decimal]


PARAMETROS_2025 = Parametros(
    vigencia=date(2025, 1, 1),
    salario_minimo=Decimal("1518.00"),
    deducao_saude={
        CategoriaDeducao.MEDICAMENTOS: Decimal("45.00"),
        CategoriaDeducao.CONSULTAS: Decimal("90.00"),
        CategoriaDeducao.FRALDAS: Decimal("99.00"),
        CategoriaDeducao.ALIMENTACAO_ESPECIAL: Decimal("121.00"),
        CategoriaDeducao.CENTRO_DIA: Decimal("32.00"),
    },
)


@dataclass(frozen=True)
class Avaliacao:
    resultado: Resultado
    motivo: str
    renda_per_capita: Decimal | None = None
    limite_renda: Decimal | None = None
    fontes: tuple[str, ...] = ()


def _contribuicao(membro: Membro, salario_minimo: Decimal) -> Decimal:
    beneficios = [_dec(b) for b in membro.beneficios_previdenciarios]
    total = _dec(membro.renda_trabalho) + sum(beneficios, Decimal(0))
    # Exclui 1 benefício de até 1 SM se o membro é idoso 65+ ou pessoa com deficiência
    # (Portaria 34/2025 art. 8º, I, "d" e "e", e §1º).
    if membro.idade_anos >= IDADE_IDOSO or membro.com_deficiencia:
        excluiveis = [b for b in beneficios if b <= salario_minimo]
        if excluiveis:
            total -= max(excluiveis)
    return total


def _renda_per_capita(caso: Caso, params: Parametros) -> Decimal:
    salario_minimo = _dec(params.salario_minimo)
    membros = (caso.requerente, *caso.outros_membros)
    bruta = sum((_contribuicao(m, salario_minimo) for m in membros), Decimal(0))
    deducoes = sum(
        (_dec(params.deducao_saude[c]) for c in caso.deducoes_saude), Decimal(0)
    )
    liquida = max(bruta - deducoes, Decimal(0))
    return liquida / Decimal(len(membros))


def avaliar(caso: Caso, params: Parametros = PARAMETROS_2025) -> Avaliacao:
    limite = _dec(params.salario_minimo) / Decimal(4)
    per_capita = _renda_per_capita(caso, params)
    renda_ok = per_capita <= limite

    if caso.rota == Rota.DEFICIENCIA and caso.impedimento_min_2_anos is False:
        return Avaliacao(
            Resultado.NAO_ATENDE,
            "O impedimento informado dura menos de 2 anos; o BPC exige impedimento "
            "de longo prazo (efeitos pelo prazo mínimo de 2 anos).",
            per_capita,
            limite,
            (_FONTE_IMPEDIMENTO,),
        )

    if caso.rota == Rota.IDADE and caso.requerente.idade_anos < IDADE_IDOSO:
        return Avaliacao(
            Resultado.NAO_ATENDE,
            f"O requerente tem {caso.requerente.idade_anos} anos; o BPC ao idoso "
            "exige 65 anos completos.",
            per_capita,
            limite,
            (_FONTE_IDADE,),
        )

    if not renda_ok:
        return Avaliacao(
            Resultado.NAO_ATENDE,
            f"A renda familiar per capita (R$ {per_capita:.2f}) supera o limite de "
            f"1/4 do salário mínimo (R$ {limite:.2f}).",
            per_capita,
            limite,
            (_FONTE_RENDA,),
        )

    if caso.rota == Rota.DEFICIENCIA:
        return Avaliacao(
            Resultado.DEPENDE_DE_AVALIACAO,
            "A renda está dentro do limite. O reconhecimento da deficiência para o "
            "BPC depende da avaliação biopsicossocial do INSS.",
            per_capita,
            limite,
            (_FONTE_RENDA, _FONTE_AVALIACAO),
        )

    return Avaliacao(
        Resultado.ATENDE,
        f"O requerente tem 65 anos ou mais e a renda familiar per capita "
        f"(R$ {per_capita:.2f}) está dentro do limite de 1/4 do salário mínimo "
        f"(R$ {limite:.2f}).",
        per_capita,
        limite,
        (_FONTE_IDADE, _FONTE_RENDA),
    )
