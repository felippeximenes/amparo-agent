"""Ingestão do corpus curado em `docs/sources/` para o Qdrant.

Uso:  uv run python scripts/ingest.py

Roda 100% local: embeddings via fastembed (baixa o modelo na 1ª execução) e
Qdrant em modo arquivo (`settings.qdrant_path`). Recria a coleção do zero a
cada execução — o corpus é curado à mão e pequeno.
"""

import sys
from pathlib import Path

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

    model = TextEmbedding(model_name=settings.embedding_model)
    vectors = [v.tolist() for v in model.passage_embed([c["texto"] for c in chunks])]

    qc = QdrantClient(path=settings.qdrant_path)
    qc.recreate_collection(
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
    print(
        f"indexado: {len(chunks)} trechos em '{settings.qdrant_collection}' "
        f"({settings.qdrant_path})"
    )


if __name__ == "__main__":
    main()
