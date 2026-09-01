"""REPL para experimentar o grafo do agente Amparo.

Uso:  uv run python scripts/chat.py

Usa o LLM de `config.llm_*` (padrão: Ollama local). Sem LLM no ar, roda em modo
template: elegibilidade sem dados montados fica INDETERMINADO. Requer o índice do
RAG: `uv run python scripts/ingest.py`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from amparo.agente import construir_grafo  # noqa: E402
from amparo.llm import criar_llm  # noqa: E402

BANNER = (
    "Amparo (protótipo) — orientação informativa sobre o BPC/LOAS.\n"
    "Não é canal oficial do INSS. Digite sua pergunta (ou 'sair').\n"
)


def main() -> None:
    grafo = construir_grafo(criar_llm())
    print(BANNER)
    while True:
        try:
            pergunta = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if pergunta.lower() in {"sair", "exit", "quit", ""}:
            return
        estado = grafo.invoke({"pergunta": pergunta})
        print("\n" + estado["resposta"] + "\n")


if __name__ == "__main__":
    main()
