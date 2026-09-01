"""Slot do modelo de linguagem.

`LLM` é a interface que o grafo usa. `ChatLLM` a implementa contra qualquer
endpoint compatível com a API da OpenAI — o padrão é o Ollama local
(`config.llm_*`); trocar para a API da OpenAI é só mudar `llm_base_url`,
`llm_api_key` e `llm_model`.

Sem LLM configurado (ou Ollama fora do ar), `criar_llm()` devolve `None` e o
grafo roda em modo template: elegibilidade sem `Caso` fica `INDETERMINADO` e as
respostas do RAG são compostas por template.
"""

from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from typing import Protocol

from amparo.rules.elegibilidade import (
    Caso,
    CategoriaDeducao,
    Membro,
    Rota,
)


class LLM(Protocol):
    def extrair_caso(self, texto: str) -> Caso | None:
        """Extrai um `Caso` de elegibilidade da fala do usuário; `None` se
        faltam dados essenciais (rota, idade na rota idade)."""
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
        outros = tuple(_membro_de_dict(m) for m in (d.get("outros_membros") or []))
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


# --- adaptador para endpoint compatível com OpenAI --------------------------------

_SEM_RESPOSTA = (
    "Não encontrei essa informação nas fontes oficiais que consulto. "
    "Procure o INSS (telefone 135 ou pelo Meu INSS) ou a Defensoria Pública."
)

_SYS_EXTRAIR = """Você extrai dados para uma verificação de elegibilidade ao BPC/LOAS.
Leia o texto do usuário e devolva SOMENTE um JSON com esta forma:
{
  "rota": "idade" | "deficiencia" | null,
  "requerente": {"idade_anos": int|null, "com_deficiencia": bool,
                 "renda_trabalho": number, "beneficios_previdenciarios": [number],
                 "renda_excluida": number},
  "outros_membros": [ {mesma forma do requerente} ],
  "impedimento_min_2_anos": true | false | null,
  "deducoes_saude": ["medicamentos","consultas","fraldas","alimentacao_especial","centro_dia"]
}
Regras: "rota" é "idade" se a pessoa tem ou está perto de 65 anos; "deficiencia" se
menciona deficiência/impedimento. "renda_trabalho" soma salário, trabalho informal,
pró-labore e Bolsa Família. "beneficios_previdenciarios" são aposentadorias/pensões/BPC.
"renda_excluida" é estágio, aprendizagem, indenização de barragem, auxílio-inclusão.
Se um dado não foi informado, use null (ou 0 para valores, [] para listas).
NÃO invente valores. Responda só o JSON."""

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

    def extrair_caso(self, texto: str) -> Caso | None:
        saida = self._chat(_SYS_EXTRAIR, texto, json_mode=True)
        if not saida:
            return None
        try:
            return caso_de_dict(json.loads(saida))
        except (json.JSONDecodeError, TypeError):
            return None

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
