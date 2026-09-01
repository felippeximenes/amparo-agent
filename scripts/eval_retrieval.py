"""Validação da recuperação do RAG (busca híbrida denso + BM25).

Uso:  uv run python scripts/eval_retrieval.py [k]

Roda um conjunto de perguntas reais contra o índice do Qdrant e reporta, para
cada uma, se algum dos arquivos-fonte esperados aparece no top-k. Sai com
código != 0 se o recall@k ficar abaixo de 0.8.

Pré-requisito: `uv run python scripts/ingest.py` já executado.
"""

import sys
from pathlib import Path

from qdrant_client import QdrantClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from amparo import rag  # noqa: E402
from amparo.config import settings  # noqa: E402

# (pergunta, {prefixos de arquivo que respondem legitimamente})
CASOS: list[tuple[str, set[str]]] = [
    ("Tenho 64 anos, posso pedir o BPC como idoso?", {"02", "06"}),
    ("Qual é o limite de renda por pessoa da família para ter direito ao BPC?", {"02", "04", "08"}),
    ("Quem entra no grupo familiar para calcular a renda do BPC?", {"02", "08", "12"}),
    ("O Bolsa Família entra no cálculo da renda do BPC?", {"09"}),
    ("Minha mãe já recebe BPC; isso conta na renda para meu pai idoso pedir o dele?", {"05", "06"}),
    ("Como o INSS avalia se a pessoa tem deficiência para o BPC?", {"03", "02", "13"}),
    ("Preciso estar inscrito no CadÚnico para pedir o BPC?", {"02", "12", "10"}),
    ("De quanto em quanto tempo o BPC é revisto?", {"02", "08"}),
    ("Se eu começar a trabalhar de carteira assinada, perco o BPC?", {"02", "12"}),
    ("Pessoa com deficiência que abre um MEI perde o benefício?", {"02"}),
    ("O BPC paga 13º salário?", {"14", "15"}),
    ("Quem já é aposentado pode acumular a aposentadoria com o BPC?", {"02", "08"}),
    ("Como faço para solicitar o BPC pela internet, no Meu INSS?", {"14", "15", "12"}),
    ("Meu CadÚnico está desatualizado há mais de dois anos; o que acontece com o BPC?", {"02", "07"}),
    ("Posso abater os gastos com fralda e remédio no cálculo da renda?", {"04", "12", "02"}),
    ("Estrangeiro morando no Brasil tem direito ao BPC?", {"12", "14", "15"}),
    ("O que é impedimento de longo prazo para fins do BPC?", {"02", "03"}),
    ("Quanto tempo o INSS demora para responder o pedido de BPC?", {"14", "15"}),
    ("O BPC deixa pensão por morte para os herdeiros?", {"14", "15"}),
    ("Qual é a base na Constituição para o BPC?", {"01"}),
]

THRESHOLD = 0.8


def prefixo(arquivo: str) -> str:
    return arquivo.split("-", 1)[0]


def main() -> None:
    k = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    qc = QdrantClient(path=settings.qdrant_path)

    acertos = 0
    for pergunta, esperado in CASOS:
        vistos = [prefixo(p["arquivo"]) for p in rag.search(qc, pergunta, k)]
        rank = next((i + 1 for i, p in enumerate(vistos) if p in esperado), None)
        acertos += rank is not None
        tag = f"OK  r{rank}" if rank else "FALHA "
        print(
            f"[{tag}] {pergunta[:58]:<58} "
            f"top{k}: {','.join(vistos)}  esp: {','.join(sorted(esperado))}"
        )

    recall = acertos / len(CASOS)
    print(f"\nrecall@{k}: {acertos}/{len(CASOS)} ({recall:.0%})")
    sys.exit(0 if recall >= THRESHOLD else 1)


if __name__ == "__main__":
    main()
