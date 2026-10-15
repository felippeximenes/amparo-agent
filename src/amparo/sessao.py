"""Memória de sessão: thread_id por conversa, persistido pelo checkpointer do
LangGraph. O que é guardado, por quanto tempo e como se apaga — ver
`docs/adr/0002-memoria-de-sessao-e-lgpd.md` e a regra 5 do CLAUDE.md.
"""

from __future__ import annotations

import hashlib
import hmac
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Protocol


def session_id_de(identificador: str, salt: str | None = None) -> str:
    """`thread_id` derivado por HMAC-SHA256 — nunca o telefone/CPF cru.
    Sem `salt`, usa `settings.session_salt`; falha se nenhum estiver
    configurado (um HMAC sem segredo não protege nada)."""
    if salt is None:
        from amparo.config import settings

        salt = settings.session_salt
    if not salt:
        raise ValueError(
            "SESSION_SALT não configurado — defina no .env antes de gerar "
            "um session_id (ver .env.example)."
        )
    return hmac.new(salt.encode("utf-8"), identificador.encode("utf-8"), hashlib.sha256).hexdigest()


class _CheckpointTupleLike(Protocol):
    config: dict
    checkpoint: dict


class Checkpointer(Protocol):
    def list(self, config: dict | None) -> object: ...
    def delete_thread(self, thread_id: str) -> None: ...


def limpar_sessoes_expiradas(checkpointer: Checkpointer, ttl_horas: float = 24.0) -> int:
    """Apaga toda sessão sem atividade há mais de `ttl_horas`. Devolve
    quantas threads foram apagadas."""
    corte = datetime.now(timezone.utc) - timedelta(hours=ttl_horas)
    ultima_atividade: dict[str, datetime] = {}
    # ponytail: varre todos os checkpoints a cada chamada — ok no volume de
    # um protótipo; trocar por consulta indexada por thread se crescer.
    for checkpoint_tuple in checkpointer.list(None):
        thread_id = checkpoint_tuple.config["configurable"]["thread_id"]
        ts = datetime.fromisoformat(checkpoint_tuple.checkpoint["ts"])
        if thread_id not in ultima_atividade or ts > ultima_atividade[thread_id]:
            ultima_atividade[thread_id] = ts

    expiradas = [tid for tid, ts in ultima_atividade.items() if ts < corte]
    for thread_id in expiradas:
        checkpointer.delete_thread(thread_id)
    return len(expiradas)


# Tipos do domínio guardados direto no Estado do grafo — sem isso, o
# checkpointer avisa (e numa versão futura vai bloquear) ao desserializar.
_TIPOS_DO_DOMINIO = [
    ("amparo.agente", "Intencao"),
    ("amparo.rules.elegibilidade", "Avaliacao"),
    ("amparo.rules.elegibilidade", "Caso"),
    ("amparo.rules.elegibilidade", "CategoriaDeducao"),
    ("amparo.rules.elegibilidade", "Membro"),
    ("amparo.rules.elegibilidade", "Resultado"),
    ("amparo.rules.elegibilidade", "Rota"),
]


@contextmanager
def abrir_checkpointer():
    """Checkpointer de dev/testes: SQLite num arquivo gitignored
    (`settings.session_sqlite_path`). A troca para Postgres (produção) é só
    configuração (`SESSION_DB_URL`) — a infra ainda não está implementada,
    ver ADR 0002."""
    from amparo.config import settings

    if settings.session_db_url:
        raise NotImplementedError(
            "SESSION_DB_URL configurado, mas o checkpointer de Postgres "
            "ainda não foi implementado — por enquanto, deixe essa variável "
            "vazia para usar o SQLite local."
        )
    import sqlite3

    from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
    from langgraph.checkpoint.sqlite import SqliteSaver

    serde = JsonPlusSerializer(allowed_msgpack_modules=_TIPOS_DO_DOMINIO)
    conn = sqlite3.connect(settings.session_sqlite_path, check_same_thread=False)
    try:
        yield SqliteSaver(conn, serde=serde)
    finally:
        conn.close()
