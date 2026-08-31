from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Qdrant em modo local (arquivo) — sem servidor/Docker no dev.
    qdrant_path: str = "./qdrant_data"
    qdrant_collection: str = "amparo_bpc"

    # Embedding roda localmente (fastembed). O MESMO modelo precisa ser usado
    # na ingestão e na consulta do RAG. MiniLM multilíngue: ~470 MB, roda em
    # CPU modesto. (e5-large dá recuperação melhor, mas trava a inferência
    # neste hardware.)
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    fastembed_cache: str = "./.fastembed_cache"


settings = Settings()
