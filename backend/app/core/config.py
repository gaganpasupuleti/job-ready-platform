from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "job-ready-platform"
    app_env: str = "development"
    debug: bool = True

    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    api_v1_prefix: str = "/api/v1"

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "jobready"
    postgres_password: str = "jobready_dev"
    postgres_db: str = "jobready_db"
    database_url: str = (
        "postgresql+asyncpg://jobready:jobready_dev@localhost:5432/jobready_db"
    )

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_url: str = "redis://localhost:6379/0"

    judge0_url: str = "http://localhost:2358"
    judge0_api_key: str = ""
    judge0_enabled: bool = True
    judge0_timeout_seconds: int = 30

    max_source_code_length: int = 65536
    default_exam_duration_minutes: int = 30

    # SQL practice sandbox (isolated from application DB)
    # Admin: schema create/seed/drop only. Runner: read-only student queries only.
    sql_sandbox_admin_database_url: str = (
        "postgresql+asyncpg://jobready_sql_admin:jobready_sql_admin_dev@localhost:5433/jobready_sql_sandbox"
    )
    sql_sandbox_runner_database_url: str = (
        "postgresql+asyncpg://jobready_sql_runner:jobready_sql_dev@localhost:5433/jobready_sql_sandbox"
    )
    # Backward-compatible alias (treated as runner URL if runner URL unset)
    sql_sandbox_database_url: str = (
        "postgresql+asyncpg://jobready_sql_runner:jobready_sql_dev@localhost:5433/jobready_sql_sandbox"
    )
    sql_sandbox_runner_role: str = "jobready_sql_runner"
    sql_execution_enabled: bool = True
    sql_query_timeout_ms: int = 3000
    sql_max_rows: int = 500
    sql_submit_max_rows: int = 10000
    sql_max_query_length: int = 20000

    jwt_secret_key: str = "change-me-in-production-use-long-random-secret"
    jwt_access_token_expire_minutes: int = 60 * 24

    practice_catalog_cache_ttl_seconds: int = 300
    practice_catalog_cache_key: str = "practice:catalog"

    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


settings = Settings()
