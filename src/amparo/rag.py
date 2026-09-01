"""Codificação e busca híbrida (densa + BM25) sobre o índice do RAG.

Compartilhado por `scripts/ingest.py`, `scripts/eval_retrieval.py` e, na Fase 2,
pelo `rag_node`. O caller controla o ciclo de vida do QdrantClient (modo local
não aceita dois processos).

BM25: os vetores dos trechos guardam só a frequência do termo (TF). O IDF é
calculado sobre o corpus na ingestão (`compute_idf` -> `settings.bm25_idf_path`)
e aplicado ao vetor da consulta em `search` — o modo local do Qdrant não honra
o `Modifier.IDF` do servidor.
"""

from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path

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


def encode_passages(
    texts: list[str],
) -> tuple[list[list[float]], list[models.SparseVector]]:
    dense, sparse = _encoders()
    d = [v.tolist() for v in dense.passage_embed(texts)]
    s = [_sparse(v) for v in sparse.passage_embed(texts)]
    return d, s


def compute_idf(sparse_vecs: list[models.SparseVector]) -> dict[str, float]:
    df: dict[int, int] = {}
    for sv in sparse_vecs:
        for idx in sv.indices:
            df[int(idx)] = df.get(int(idx), 0) + 1
    n = max(len(sparse_vecs), 1)
    return {str(t): math.log(1 + (n - d + 0.5) / (d + 0.5)) for t, d in df.items()}


@lru_cache(maxsize=1)
def _idf() -> dict[str, float]:
    p = Path(settings.bm25_idf_path)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def _query_sparse(query: str) -> models.SparseVector:
    _, sparse = _encoders()
    emb = next(iter(sparse.query_embed([query])))
    idf = _idf()
    idxs = emb.indices.tolist()
    vals = emb.values.tolist()
    return models.SparseVector(
        indices=idxs,
        values=[v * idf.get(str(i), 0.0) for i, v in zip(idxs, vals)],
    )


def search(client, query: str, k: int = 5, rrf_k: int = 60) -> list[dict]:
    """Busca híbrida: uma consulta densa + uma BM25, fundidas por RRF em Python.
    Retorna os payloads dos k melhores trechos, no máx. 2 por arquivo."""
    dense, _ = _encoders()
    dq = next(iter(dense.query_embed([query]))).tolist()
    sq = _query_sparse(query)
    n = 12 * k

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

    per_file, seen, out = 2, {}, []
    for i in sorted(scores, key=scores.get, reverse=True):
        arq = payloads[i].get("arquivo", "")
        if seen.get(arq, 0) >= per_file:
            continue
        seen[arq] = seen.get(arq, 0) + 1
        out.append(payloads[i])
        if len(out) == k:
            break
    return out
