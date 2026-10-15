"""Slot do modelo de linguagem.

`LLM` é a interface que o grafo usa. `ChatLLM` a implementa contra qualquer
endpoint compatível com a API da OpenAI — o padrão é o Ollama local
(`config.llm_*`); trocar para a API da OpenAI é só mudar `llm_base_url`,
`llm_api_key` e `llm_model`.

Sem LLM configurado (ou Ollama fora do ar), `criar_llm()` devolve `None` e o
grafo roda em modo template: a coleta de elegibilidade fica `INDETERMINADO` no
primeiro dado que falta (nada é extraído da fala) e as respostas do RAG são
compostas por template.
"""

from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from typing import Protocol

from amparo.coleta import filtrar_grupo_familiar
from amparo.rules.elegibilidade import (
    Caso,
    CategoriaDeducao,
    Membro,
    Rota,
)


class LLM(Protocol):
    def extrair_atualizacoes(self, mensagens: list[dict], caso_parcial: dict) -> dict:
        """A partir da conversa e do que já foi coletado (`caso_parcial`, no
        formato de `caso_de_dict`), devolve só os campos NOVOS entendidos na
        última fala do usuário. Não decide o que falta — isso é
        `coleta.proximo_dado_faltante`, código puro."""
        ...

    def classificar_intencao(self, pergunta: str) -> str | None:
        """Classifica a fala numa das 6 categorias ("elegibilidade",
        "checklist", "duvida", "saudacao", "fora_de_escopo", "apagar") ou
        "incompreensivel" quando a saída do modelo não dá para interpretar.
        `None` quando a chamada falha/está indisponível — quem chama cai na
        classificação por palavra-chave (`agente.classificar_intencao`)."""
        ...

    def responder(self, pergunta: str, trechos: list[dict]) -> str:
        """Redige a resposta em linguagem simples, fundamentada só nos `trechos`
        (cada um com `titulo`/`fonte`/`tag`), citando a fonte."""
        ...


# --- construção de Caso a partir do JSON do modelo (puro, testável) -----------

_CATEGORIAS = {c.value: c for c in CategoriaDeducao}


def _dec(v) -> Decimal:
    return Decimal(str(v)) if v not in (None, "") else Decimal(0)


def _membro_de_dict(d: dict) -> Membro:
    return Membro(
        idade_anos=int(d.get("idade_anos") or 0),
        com_deficiencia=bool(d.get("com_deficiencia", False)),
        renda_trabalho=_dec(d.get("renda_trabalho")),
        beneficios_previdenciarios=tuple(
            _dec(b) for b in (d.get("beneficios_previdenciarios") or [])
        ),
        renda_excluida=_dec(d.get("renda_excluida")),
    )


def caso_de_dict(d: dict) -> Caso | None:
    """Monta um `Caso` a partir do dicionário devolvido pelo modelo. `None`
    quando falta o essencial (rota válida; idade do requerente na rota idade)."""
    rota_raw = str(d.get("rota") or "").strip().lower()
    if rota_raw not in ("idade", "deficiencia"):
        return None
    rota = Rota(rota_raw)

    requerente_raw = d.get("requerente") or {}
    if rota is Rota.IDADE and not requerente_raw.get("idade_anos"):
        return None

    try:
        requerente = _membro_de_dict(requerente_raw)
        outros_raw = filtrar_grupo_familiar(d.get("outros_membros") or [])
        outros = tuple(_membro_de_dict(m) for m in outros_raw)
    except (TypeError, ValueError, InvalidOperation):
        return None

    imp = d.get("impedimento_min_2_anos")
    deducoes = frozenset(
        _CATEGORIAS[c] for c in (d.get("deducoes_saude") or []) if c in _CATEGORIAS
    )
    return Caso(
        rota=rota,
        requerente=requerente,
        outros_membros=outros,
        impedimento_min_2_anos=imp if isinstance(imp, bool) else None,
        deducoes_saude=deducoes,
    )


_MARCADORES_DE_ETAPA = ("membros_coletado", "renda_coletada", "saude_coletada")


def interpretar_atualizacoes(saida: str) -> dict:
    """Parsing puro da resposta do modelo para `extrair_atualizacoes`. JSON
    inválido ou que não é um objeto devolve `{}` (nenhuma atualização).
    Descarta qualquer marcador de etapa que o modelo devolva — quem decide
    se uma etapa foi respondida é `coleta.marcar_etapas_respondidas`, a
    partir da presença explícita dos dados, nunca da palavra do modelo."""
    if not saida:
        return {}
    try:
        dados = json.loads(saida)
    except json.JSONDecodeError:
        return {}
    if not isinstance(dados, dict):
        return {}
    for marcador in _MARCADORES_DE_ETAPA:
        dados.pop(marcador, None)
    return dados


_CATEGORIAS_INTENCAO = (
    "elegibilidade", "checklist", "duvida", "saudacao", "fora_de_escopo", "apagar",
)


def interpretar_intencao(saida: str) -> str | None:
    """Parsing puro da resposta do classificador de intenção. `None` quando o
    modelo não respondeu nada usável (chamada falhou/está indisponível) —
    nesse caso quem chama cai na classificação por palavra-chave. Uma
    resposta não vazia que não é uma das 6 categorias válidas devolve
    "incompreensivel": o modelo tentou e não deu para entender, o que é
    diferente de não ter respondido nada."""
    if not saida:
        return None
    try:
        dados = json.loads(saida)
    except json.JSONDecodeError:
        return "incompreensivel"
    categoria = dados.get("intencao") if isinstance(dados, dict) else None
    return categoria if categoria in _CATEGORIAS_INTENCAO else "incompreensivel"


# --- adaptador para endpoint compatível com OpenAI --------------------------------

_SEM_RESPOSTA = (
    "Não encontrei essa informação nas fontes oficiais que consulto. "
    "Procure o INSS (telefone 135 ou pelo Meu INSS) ou a Defensoria Pública."
)

_SYS_EXTRAIR_ATUALIZACOES = """Você ajuda a preencher, PASSO A PASSO, os dados para
verificar elegibilidade ao BPC/LOAS. Você recebe o que já foi coletado (JSON) e a
conversa até agora (amparo pergunta, a pessoa responde). Devolva SOMENTE um JSON com
os campos NOVOS que a ÚLTIMA fala da pessoa (a última linha da conversa) trouxe — não
repita o que já estava coletado, não invente o que a pessoa não disse. Campos
possíveis, no MESMO formato do que já foi coletado:
{
  "rota": "idade" | "deficiencia",
  "requerente": {"idade_anos": int, "com_deficiencia": bool, "renda_trabalho": number,
                 "beneficios_previdenciarios": [number], "renda_excluida": number},
  "outros_membros": [ {mesma forma do requerente, mais:
                 "parentesco": "conjuge"|"pai_mae"|"filho_enteado"|"irmao"|"tutelado"|"outro",
                 "solteiro": true|false} ],
  "impedimento_min_2_anos": true | false,
  "deducoes_saude": ["medicamentos","consultas","fraldas","alimentacao_especial","centro_dia"]
}
Em "outros_membros", preencha "parentesco" sempre que a fala der a relação com o
requerente. "solteiro" só importa para "filho_enteado" e "irmao" (só esses dois ficam
de fora do grupo familiar se forem casados) — preencha true/false quando a pessoa
disser o estado civil (ex.: "meu filho casado" → solteiro: false; "minha irmã
solteira" → solteiro: true); se não for dito, não inclua o campo. Para cônjuge, pais
ou tutelados, "solteiro" não é necessário. "outros_membros" e "deducoes_saude" são a
lista COMPLETA (não um item novo). Quando a
pessoa disser que mora só / ninguém mais mora na casa, devolva "outros_membros": []
— lista vazia, EXPLÍCITA, não omita o campo. Quando disser que não tem gastos de
saúde, devolva "deducoes_saude": [] — vazia, explícita. Quando disser que não tem
renda (da pessoa ou de algum membro da casa), devolva "renda_trabalho": 0
EXPLICITAMENTE para esse membro — não omita o campo. "renda_trabalho" soma salário,
trabalho informal, pró-labore e Bolsa Família. "beneficios_previdenciarios" são
aposentadorias/pensões/BPC. "renda_excluida" é estágio, aprendizagem, indenização de
barragem, auxílio-inclusão. Se a última fala não trouxer nada novo sobre um campo, não
o inclua no JSON. NÃO invente valores, e NÃO devolva nenhum campo além dos listados
acima. Responda só o JSON."""

_SYS_CLASSIFICAR_INTENCAO = """Você classifica a intenção de uma fala sobre o BPC/LOAS
(Benefício de Prestação Continuada). Devolva SOMENTE um JSON {"intencao": "<categoria>"}
com UMA destas categorias:
"elegibilidade" — quer saber se tem (ou alguém tem) direito ao BPC, ou está respondendo
  dados para essa verificação (idade, renda, quem mora na casa, deficiência, documentos
  pessoais da avaliação...).
"checklist" — quer saber quais documentos levar, como pedir, passo a passo, onde
  solicitar o BPC.
"duvida" — pergunta sobre regras do BPC/LOAS que não é elegibilidade nem checklist (ex.:
  o que é o BPC, quem pode receber em geral, valor do benefício, prazo do INSS).
"saudacao" — saudação, cumprimento ou pedido de ajuda genérico, sem conteúdo sobre o
  BPC (ex.: "oi", "bom dia", "pode me ajudar?").
"fora_de_escopo" — pergunta sobre outro benefício (auxílio-doença, aposentadoria,
  pensão por morte...) ou assunto não relacionado ao BPC/LOAS.
"apagar" — pede para apagar os dados da conversa, encerrar e excluir o que foi dito.
Responda só o JSON, sem comentários."""

_SYS_RESPONDER = """Você é o Amparo, uma ferramenta de orientação informativa e independente.
NÃO é o INSS nem o governo. Responda à pergunta APENAS com base nos trechos oficiais
fornecidos. Escreva em português claro e acolhedor, para uma pessoa com pouca
escolaridade. Ao afirmar uma regra, cite a fonte (o nome da norma). Se os trechos não
respondem à pergunta, diga que não encontrou e oriente procurar o INSS (135 / Meu INSS)
ou a Defensoria Pública. Não invente artigos, valores ou prazos."""


class ChatLLM:
    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str = "ollama",
        timeout: float = 120.0,
        preco_entrada: float = 0.0,
        preco_saida: float = 0.0,
    ) -> None:
        from openai import OpenAI

        self._client = OpenAI(base_url=base_url, api_key=api_key, timeout=timeout)
        self._model = model
        self._preco_entrada = preco_entrada
        self._preco_saida = preco_saida
        self.tokens_entrada = 0
        self.tokens_saida = 0

    def _chat(self, system: str, user: str, *, json_mode: bool = False) -> str:
        kwargs = dict(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0,
        )
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        try:
            r = self._client.chat.completions.create(**kwargs)
        except Exception:
            return ""
        uso = getattr(r, "usage", None)
        if uso is not None:
            self.tokens_entrada += getattr(uso, "prompt_tokens", 0) or 0
            self.tokens_saida += getattr(uso, "completion_tokens", 0) or 0
        return (r.choices[0].message.content or "").strip()

    def resumo_uso(self) -> str:
        total = self.tokens_entrada + self.tokens_saida
        linha = (
            f"tokens: {self.tokens_entrada} entrada + {self.tokens_saida} saída "
            f"= {total}"
        )
        if self._preco_entrada or self._preco_saida:
            custo = (
                self.tokens_entrada / 1_000_000 * self._preco_entrada
                + self.tokens_saida / 1_000_000 * self._preco_saida
            )
            linha += f"  |  custo estimado da sessão: US$ {custo:.4f}"
        return linha

    def extrair_atualizacoes(self, mensagens: list[dict], caso_parcial: dict) -> dict:
        transcricao = "\n".join(f"{m['role']}: {m['texto']}" for m in mensagens)
        contexto = json.dumps(caso_parcial, ensure_ascii=False)
        user = f"Já coletado até agora: {contexto}\n\nConversa:\n{transcricao}"
        saida = self._chat(_SYS_EXTRAIR_ATUALIZACOES, user, json_mode=True)
        return interpretar_atualizacoes(saida)

    def classificar_intencao(self, pergunta: str) -> str | None:
        saida = self._chat(_SYS_CLASSIFICAR_INTENCAO, pergunta, json_mode=True)
        return interpretar_intencao(saida)

    def responder(self, pergunta: str, trechos: list[dict]) -> str:
        if not trechos:
            return _SEM_RESPOSTA
        contexto = "\n\n".join(
            f"[{t.get('titulo', '')} — {t.get('fonte', '')}]\n{t.get('texto', '')}"
            for t in trechos
        )
        return (
            self._chat(
                _SYS_RESPONDER,
                f"Trechos oficiais:\n\n{contexto}\n\nPergunta: {pergunta}",
            )
            or _SEM_RESPOSTA
        )


def criar_llm(check: bool = True) -> LLM | None:
    """Constrói o `ChatLLM` a partir de `settings`. Se `check`, faz um ping
    rápido e devolve `None` (com aviso) quando o endpoint não responde."""
    from amparo.config import settings

    llm = ChatLLM(
        settings.llm_base_url,
        settings.llm_model,
        settings.llm_api_key,
        preco_entrada=settings.llm_preco_entrada,
        preco_saida=settings.llm_preco_saida,
    )
    if check:
        try:
            llm._client.models.list()
        except Exception:
            print(
                f"[amparo] LLM indisponível em {settings.llm_base_url} "
                f"(modelo {settings.llm_model}). Rodando em modo template."
            )
            return None
    return llm
