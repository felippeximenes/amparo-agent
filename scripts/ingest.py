"""Ingestão do corpus curado em `docs/sources/` para o Qdrant.

Uso:  uv run python scripts/ingest.py

Recria a coleção do zero a cada execução — o corpus é curado à mão e pequeno.
Requer Qdrant no ar (docker compose up -d) e credenciais AWS com acesso ao
Amazon Bedrock.
"""

import json
import sys
from pathlib import Path

import boto3
from qdrant_client import QdrantClient, models

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from amparo.config import settings  # noqa: E402
from amparo.corpus import chunk, parse_source  # noqa: E402

SOURCES = Path(__file__).resolve().parents[1] / "docs" / "sources"
_bedrock = boto3.client("bedrock-runtime", region_name=settings.aws_region)


def embed(text: str) -> list[float]:
    resp = _bedrock.invoke_model(
        modelId=settings.bedrock_embedding_model_id,
        body=json.dumps({"inputText": text}),
    )
    return json.loads(resp["body"].read())["embedding"]


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

    vectors = [embed(c["texto"]) for c in chunks]

    qc = QdrantClient(url=settings.qdrant_url)
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
    print(f"indexado em '{settings.qdrant_collection}' @ {settings.qdrant_url}")


if __name__ == "__main__":
    main()
