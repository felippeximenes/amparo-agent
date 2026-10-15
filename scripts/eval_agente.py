"""Avaliação ponta a ponta do agente Amparo — grafo completo, LLM real.

Uso:  uv run python scripts/eval_agente.py

Roda as conversas-roteiro de tests/fixtures/conversas/*.yaml pelo grafo
completo (requer LLM configurado e índice do RAG já construído). Para cada
conversa, checa: veredito (ou intenção de fallback) correto; disclaimer
presente; nenhum valor em R$ fora do que o motor calculou (nas conversas de
elegibilidade — o template é sempre determinístico, então isso é um alarme
de regressão, não uma verificação opcional); nº de perguntas até o veredito.

Saída: tabela no terminal + eval_agente.json (gitignored, não comitar — tem
o texto das respostas). Sai com código 1 se o acerto de veredito/intenção
ficar abaixo de 0.95.
"""

import json
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from amparo.agente import Intencao, construir_grafo  # noqa: E402
from amparo.disclaimer import DISCLAIMER  # noqa: E402
from amparo.llm import criar_llm  # noqa: E402
from amparo.rules.elegibilidade import Resultado  # noqa: E402

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "conversas"
LIMIAR_ACERTO = 0.95
_RE_REAIS = re.compile(r"R\$\s*(\d+[.,]\d{2})")


def carregar_conversas() -> list[dict]:
    arquivos = sorted(FIXTURES_DIR.glob("*.yaml"))
    return [yaml.safe_load(a.read_text(encoding="utf-8")) for a in arquivos]


def _aceita(obtido, esperado) -> bool:
    if isinstance(esperado, list):
        return obtido in esperado
    return obtido == esperado


def _valores_em_reais(texto: str) -> set[str]:
    return set(_RE_REAIS.findall(texto))


def _valores_do_motor(avaliacao) -> set[str]:
    if avaliacao is None:
        return set()
    valores = set()
    if avaliacao.renda_per_capita is not None:
        valores.add(f"{avaliacao.renda_per_capita:.2f}".replace(".", ","))
        valores.add(f"{avaliacao.renda_per_capita:.2f}")
    if avaliacao.limite_renda is not None:
        valores.add(f"{avaliacao.limite_renda:.2f}".replace(".", ","))
        valores.add(f"{avaliacao.limite_renda:.2f}")
    return valores


def rodar_conversa(grafo, conversa: dict) -> dict:
    esperado = conversa["esperado"]
    estado: dict = {}
    perguntas_pendentes = 0
    for fala in conversa["falas"]:
        estado = grafo.invoke({**estado, "pergunta": fala})
        if estado.get("intencao") is Intencao.ELEGIBILIDADE:
            avaliacao = estado.get("avaliacao")
            if avaliacao is not None and avaliacao.resultado is Resultado.INDETERMINADO:
                perguntas_pendentes += 1

    is_elegibilidade = esperado["tipo"] == "elegibilidade"
    if is_elegibilidade:
        avaliacao = estado.get("avaliacao")
        obtido = avaliacao.resultado.value if avaliacao is not None else None
        veredito_ok = _aceita(obtido, esperado["resultado"])
    else:
        intencao = estado.get("intencao")
        obtido = intencao.value if intencao is not None else None
        veredito_ok = _aceita(obtido, esperado["intencao"])

    resposta = estado.get("resposta", "")
    disclaimer_ok = DISCLAIMER in resposta

    if is_elegibilidade:
        valores_ok = _valores_em_reais(resposta) <= _valores_do_motor(estado.get("avaliacao"))
    else:
        valores_ok = not _valores_em_reais(resposta)  # fallback não deveria citar R$ nenhum

    return {
        "id": conversa["id"],
        "tipo": esperado["tipo"],
        "esperado": esperado.get("resultado") or esperado.get("intencao"),
        "obtido": obtido,
        "veredito_ok": veredito_ok,
        "disclaimer_ok": disclaimer_ok,
        "valores_ok": valores_ok,
        "perguntas_pendentes": perguntas_pendentes,
        "resposta_final": resposta,
    }


def main() -> None:
    llm = criar_llm()
    if llm is None:
        print("[eval_agente] LLM indisponível — a avaliação ponta a ponta precisa do LLM real.")
        sys.exit(1)

    grafo = construir_grafo(llm)
    conversas = carregar_conversas()
    resultados = [rodar_conversa(grafo, c) for c in conversas]

    for r in resultados:
        tag = "OK   " if r["veredito_ok"] else "FALHA"
        avisos = []
        if not r["disclaimer_ok"]:
            avisos.append("sem disclaimer")
        if not r["valores_ok"]:
            avisos.append("valor em R$ fora do motor")
        aviso = f"  [{', '.join(avisos)}]" if avisos else ""
        print(
            f"[{tag}] {r['id']:<48} esperado={str(r['esperado']):<18} "
            f"obtido={str(r['obtido']):<18} perguntas={r['perguntas_pendentes']}{aviso}"
        )

    total = len(resultados)
    acertos = sum(r["veredito_ok"] for r in resultados)
    acerto = acertos / total if total else 0.0
    casos_elegibilidade = [r for r in resultados if r["tipo"] == "elegibilidade"]
    media_perguntas = (
        sum(r["perguntas_pendentes"] for r in casos_elegibilidade) / len(casos_elegibilidade)
        if casos_elegibilidade
        else 0.0
    )

    print(f"\nveredito/intenção: {acertos}/{total} ({acerto:.0%})")
    print(f"perguntas até o veredito (média, casos de elegibilidade): {media_perguntas:.1f}")
    custo_linha = llm.resumo_uso() if hasattr(llm, "resumo_uso") else None
    if custo_linha:
        print("[amparo] " + custo_linha)

    saida = {
        "acerto_veredito": acerto,
        "media_perguntas_ate_veredito": media_perguntas,
        "custo": custo_linha,
        "resultados": resultados,
    }
    Path("eval_agente.json").write_text(
        json.dumps(saida, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    sys.exit(0 if acerto >= LIMIAR_ACERTO else 1)


if __name__ == "__main__":
    main()
