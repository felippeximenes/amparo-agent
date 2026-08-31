"""Ingestão do corpus curado em `docs/sources/` para o Qdrant.

Uso:  uv run python scripts/ingest.py

Roda 100% local: embeddings via fastembed (baixa o modelo na 1ª execução, cache
em `settings.fastembed_cache`) e Qdrant em modo arquivo (`settings.qdrant_path`).
Recria a coleção do zero a cada execução — o corpus é curado à mão e pequeno.
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

from fastembed import TextEmbedding
from qdrant_client import QdrantClient, models

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from amparo.config import settings  # noqa: E402
from amparo.corpus import chunk, parse_source  # noqa: E402

SOURCES = Path(__file__).resolve().parents[1] / "docs" / "sources"


def main() -> None:
    files = sorted(SOURCES.glob("[0-9]*.md"))
    if not files:
        sys.exit(f"nenhuma fonte em {SOURCES}")

    chunks: list[dict] = []
    for f in files:
        meta, body = parse_source(f)
        c = chunk(meta, body, arquivo=f.name)
        chunks.extend(c)
        print(f"{f.name}: {len(c)} trechos")
    print(f"total: {len(chunks)} trechos")

    print(f"carregando modelo {settings.embedding_model} ...")
    model = TextEmbedding(
        model_name=settings.embedding_model, cache_dir=settings.fastembed_cache
    )

    print("gerando embeddings ...")
    vectors: list[list[float]] = []
    for i, v in enumerate(model.passage_embed([c["texto"] for c in chunks]), start=1):
        vectors.append(v.tolist())
        if i % 50 == 0 or i == len(chunks):
            print(f"  {i}/{len(chunks)}")

    qc = QdrantClient(path=settings.qdrant_path)
    if qc.collection_exists(settings.qdrant_collection):
        qc.delete_collection(settings.qdrant_collection)
    qc.create_collection(
        settings.qdrant_collection,
        vectors_config=models.VectorParams(
            size=len(vectors[0]), distance=models.Distance.COSINE
        ),
    )
    qc.upsert(
        settings.qdrant_collection,
        points=[
            models.PointStruct(id=i, vector=v, payload=c)
            for i, (v, c) in enumerate(zip(vectors, chunks))
        ],
    )
    total = qc.count(settings.qdrant_collection).count
    print(
        f"indexado: {total} trechos em '{settings.qdrant_collection}' "
        f"({settings.qdrant_path})"
    )


if __name__ == "__main__":
    main()
