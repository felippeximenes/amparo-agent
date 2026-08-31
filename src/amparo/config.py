from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Qdrant em modo local (arquivo) — sem servidor/Docker no dev.
    qdrant_path: str = "./qdrant_data"
    qdrant_collection: str = "amparo_bpc"

    # Embedding roda localmente (fastembed). O MESMO modelo precisa ser usado
    # na ingestão e na consulta do RAG.
    embedding_model: str = "intfloat/multilingual-e5-large"


settings = Settings()
