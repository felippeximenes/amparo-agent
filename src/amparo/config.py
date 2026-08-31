from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Qdrant em modo local (arquivo) — sem servidor/Docker no dev.
    qdrant_path: str = "./qdrant_data"
    qdrant_collection: str = "amparo_bpc"

    # Embedding roda localmente (fastembed). O MESMO modelo precisa ser usado
    # na ingestão e na consulta do RAG. e5-large multilíngue: ~2.25 GB, baixado
    # uma vez para fastembed_cache. Alternativa leve para dev:
    # "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2".
    embedding_model: str = "intfloat/multilingual-e5-large"
    fastembed_cache: str = "./.fastembed_cache"


settings = Settings()
