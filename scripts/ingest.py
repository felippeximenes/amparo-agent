"""Ingestão do corpus curado em `docs/sources/` para o Qdrant.

Uso:  uv run python scripts/ingest.py

Roda 100% local: embeddings via fastembed (denso + BM25), Qdrant em modo
arquivo (`settings.qdrant_path`). Recria a coleção do zero a cada execução — o
corpus é curado à mão e pequeno.
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

from qdrant_client import QdrantClient, models  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from amparo import rag  # noqa: E402
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

    print("gerando embeddings (denso + BM25) ...")
    dense_vecs, sparse_vecs = rag.encode_passages([c["texto"] for c in chunks])

    qc = QdrantClient(path=settings.qdrant_path)
    if qc.collection_exists(settings.qdrant_collection):
        qc.delete_collection(settings.qdrant_collection)
    qc.create_collection(
        settings.qdrant_collection,
        vectors_config={
            rag.DENSE: models.VectorParams(
                size=len(dense_vecs[0]), distance=models.Distance.COSINE
            )
        },
        sparse_vectors_config={
            rag.SPARSE: models.SparseVectorParams(modifier=models.Modifier.IDF)
        },
    )
    qc.upsert(
        settings.qdrant_collection,
        points=[
            models.PointStruct(
                id=i,
                vector={rag.DENSE: dv, rag.SPARSE: sv},
                payload=c,
            )
            for i, (dv, sv, c) in enumerate(zip(dense_vecs, sparse_vecs, chunks))
        ],
    )
    total = qc.count(settings.qdrant_collection).count
    print(
        f"indexado: {total} trechos em '{settings.qdrant_collection}' "
        f"({settings.qdrant_path})"
    )


if __name__ == "__main__":
    main()
