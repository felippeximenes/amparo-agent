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

    # IDF do BM25, calculado na ingestão e aplicado à consulta (o modo local do
    # Qdrant não honra o Modifier.IDF).
    bm25_idf_path: str = "./bm25_idf.json"

    # LLM via endpoint compatível com OpenAI. Padrão: Ollama local.
    # Para a API da OpenAI: llm_base_url=https://api.openai.com/v1,
    # llm_api_key=sk-..., llm_model=gpt-4o-mini (ou outro).
    llm_base_url: str = "http://localhost:11434/v1"
    llm_model: str = "qwen2.5:7b"
    llm_api_key: str = "ollama"


settings = Settings()
