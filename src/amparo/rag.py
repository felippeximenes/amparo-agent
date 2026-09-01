"""Codificação e busca híbrida (densa + BM25) sobre o índice do RAG.

Compartilhado por `scripts/ingest.py`, `scripts/eval_retrieval.py` e, na Fase 2,
pelo `rag_node`. O caller controla o ciclo de vida do QdrantClient (modo local
não aceita dois processos).
"""

from __future__ import annotations

from functools import lru_cache

from fastembed import SparseTextEmbedding, TextEmbedding
from qdrant_client import models

from amparo.config import settings

DENSE = "dense"
SPARSE = "bm25"


@lru_cache(maxsize=1)
def _encoders() -> tuple[TextEmbedding, SparseTextEmbedding]:
    dense = TextEmbedding(
        model_name=settings.embedding_model, cache_dir=settings.fastembed_cache
    )
    sparse = SparseTextEmbedding(
        model_name="Qdrant/bm25",
        cache_dir=settings.fastembed_cache,
        language="portuguese",
    )
    return dense, sparse


def _sparse(emb) -> models.SparseVector:
    return models.SparseVector(indices=emb.indices.tolist(), values=emb.values.tolist())


def encode_passages(texts: list[str]) -> tuple[list[list[float]], list[models.SparseVector]]:
    dense, sparse = _encoders()
    d = [v.tolist() for v in dense.passage_embed(texts)]
    s = [_sparse(v) for v in sparse.passage_embed(texts)]
    return d, s


def search(client, query: str, k: int = 5, rrf_k: int = 60) -> list[dict]:
    """Busca híbrida: uma consulta densa + uma BM25, fundidas por RRF em Python.

    Fusão manual (em vez de FusionQuery do Qdrant) para não depender de suporte
    do modo local a prefetch/fusão.
    """
    dense, sparse = _encoders()
    dq = next(iter(dense.query_embed([query]))).tolist()
    sq = _sparse(next(iter(sparse.query_embed([query]))))
    n = 6 * k

    ranked = [
        client.query_points(
            settings.qdrant_collection, query=dq, using=DENSE, limit=n, with_payload=True
        ).points,
        client.query_points(
            settings.qdrant_collection, query=sq, using=SPARSE, limit=n, with_payload=True
        ).points,
    ]

    scores: dict[int, float] = {}
    payloads: dict[int, dict] = {}
    for hits in ranked:
        for rank, h in enumerate(hits, start=1):
            scores[h.id] = scores.get(h.id, 0.0) + 1.0 / (rrf_k + rank)
            payloads[h.id] = h.payload

    ordered = sorted(scores, key=scores.get, reverse=True)

    # diversifica: no máximo `per_file` trechos do mesmo arquivo no top-k
    per_file = 2
    seen: dict[str, int] = {}
    out: list[dict] = []
    for i in ordered:
        arq = payloads[i].get("arquivo", "")
        if seen.get(arq, 0) >= per_file:
            continue
        seen[arq] = seen.get(arq, 0) + 1
        out.append(payloads[i])
        if len(out) == k:
            break
    return out
