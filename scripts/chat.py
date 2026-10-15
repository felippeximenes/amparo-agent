"""REPL para experimentar o grafo do agente Amparo.

Uso:  uv run python scripts/chat.py [--sessao NOME]

Sem --sessao, a conversa é perdida ao sair (thread aleatória). Com
--sessao NOME, ela persiste entre execuções (SQLite local, `thread_id` =
`session_id_de(NOME)` — nunca NOME em claro; requer SESSION_SALT no .env).
Digite "apagar", "apagar meus dados" ou "sair" para apagar a sessão na hora.

Usa o LLM de `config.llm_*` (padrão: Ollama local). Sem LLM no ar, roda em modo
template: a coleta de elegibilidade fica INDETERMINADO. Requer o índice do
RAG: `uv run python scripts/ingest.py`.
"""

import argparse
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from amparo.agente import construir_grafo  # noqa: E402
from amparo.llm import criar_llm  # noqa: E402
from amparo.sessao import abrir_checkpointer, limpar_sessoes_expiradas, session_id_de  # noqa: E402

BANNER = (
    "Amparo (protótipo) — orientação informativa sobre o BPC/LOAS.\n"
    "Não é canal oficial do INSS. Digite sua pergunta (ou 'sair').\n"
)

_COMANDOS_APAGAR = {"apagar", "apagar meus dados", "sair"}
_COMANDOS_SAIR = {"exit", "quit", ""}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--sessao", help="nome da sessão a retomar/criar — persiste entre execuções"
    )
    args = parser.parse_args()

    thread_id = session_id_de(args.sessao) if args.sessao else str(uuid.uuid4())
    llm = criar_llm()
    print(BANNER)

    with abrir_checkpointer() as checkpointer:
        grafo = construir_grafo(llm, checkpointer=checkpointer)
        config = {"configurable": {"thread_id": thread_id}}
        try:
            while True:
                limpar_sessoes_expiradas(checkpointer)
                try:
                    pergunta = input("> ").strip()
                except (EOFError, KeyboardInterrupt):
                    print()
                    break
                comando = pergunta.lower()
                if comando in _COMANDOS_APAGAR:
                    checkpointer.delete_thread(thread_id)
                    print("\nOk, apaguei os dados desta conversa.\n")
                    break
                if comando in _COMANDOS_SAIR:
                    break
                estado = grafo.invoke({"pergunta": pergunta}, config)
                print("\n" + estado["resposta"] + "\n")
        finally:
            if hasattr(llm, "resumo_uso") and getattr(llm, "tokens_entrada", 0):
                print("[amparo] " + llm.resumo_uso())


if __name__ == "__main__":
    main()
