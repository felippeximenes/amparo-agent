try:
    # Em algumas máquinas (antivírus/rede corporativa) o tráfego HTTPS passa por
    # interceptação TLS com certificado que o certifi não reconhece, mas o
    # Windows confia. truststore usa o trust store do SO em vez do certifi —
    # sem efeito em máquinas sem esse cenário.
    import truststore

    truststore.inject_into_ssl()
except ImportError:
    pass

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

    # US$ por 1 milhão de tokens (da página de pricing do provedor). Se > 0,
    # o chat.py estima o custo da sessão.
    llm_preco_entrada: float = 0.0
    llm_preco_saida: float = 0.0

    # Memória de sessão (checkpointer do LangGraph) — ver docs/adr/0002.
    # Segredo do HMAC que vira o thread_id; nunca o telefone/CPF cru.
    session_salt: str = ""
    # Dev/testes: SQLite num arquivo gitignored. Produção troca para Postgres
    # (Neon) só preenchendo SESSION_DB_URL — a infra de Postgres não está
    # implementada ainda (ver ADR 0002).
    session_sqlite_path: str = "./sessoes.db"
    session_db_url: str = ""
    session_ttl_horas: float = 24.0


settings = Settings()
