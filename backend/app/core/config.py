from pydantic_settings import BaseSettings, SettingsConfigDict
import logging
import warnings

logger = logging.getLogger(__name__)

_UNSAFE_JWT_DEFAULT = "change-me-in-production-use-long-random-secret"
_EMAIL_PLACEHOLDER_KEY = "REPLACE_WITH_REAL_BREVO_API_KEY"
_EMAIL_PLACEHOLDER_ADDRESS = "notifications@example.com"
_STORAGE_PLACEHOLDERS = {
    "",
    "changeme",
    "placeholder",
    "your-access-key",
    "your-secret-key",
    "replace-me",
}


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
    # Prefer JUDGE0_AUTH_TOKEN; JUDGE0_API_KEY kept for backward compatibility
    judge0_api_key: str = ""
    judge0_auth_header: str = "X-Auth-Token"
    judge0_auth_token: str = ""
    # Stay false unless a private Judge0 host is intentionally configured.
    # A missing env var must not enable coding execution for the jobs-first pilot.
    judge0_enabled: bool = False
    judge0_timeout_seconds: int = 30
    judge0_poll_interval_ms: int = 500
    judge0_max_poll_seconds: int = 45
    judge0_max_cpu_time_seconds: float = 15.0
    judge0_max_wall_time_seconds: float = 20.0
    judge0_max_memory_kb: int = 256000
    judge0_health_cache_seconds: int = 30
    judge0_retry_count: int = 2
    judge0_batch_size: int = 20

    # Coding limits / rate control (aliases coding_max_source_chars → max_source_code_length)
    max_source_code_length: int = 65536
    coding_max_source_chars: int = 65536
    coding_max_stdin_chars: int = 100_000
    coding_runs_per_minute: int = 20
    coding_submits_per_minute: int = 10
    coding_max_concurrent_executions_per_user: int = 2

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
    # Used when deriving runner DSN from admin URL (Railway) and for role bootstrap
    sql_sandbox_runner_password: str = "jobready_sql_dev"
    sql_execution_enabled: bool = True
    sql_query_timeout_ms: int = 3000
    sql_max_rows: int = 500
    sql_submit_max_rows: int = 10000
    sql_max_query_length: int = 20000
    sql_runs_per_minute: int = 10
    sql_submits_per_minute: int = 5
    sql_max_concurrent_executions_per_user: int = 1

    # Read-only DSN for the Railway "Jobs server" catalog. Empty disables sync.
    # Never point this at the application database. Do not commit the password.
    jobs_source_database_url: str = ""

    jwt_secret_key: str = _UNSAFE_JWT_DEFAULT
    jwt_access_token_expire_minutes: int = 60 * 24

    # Login abuse controls (Redis-backed; process-local fallback if Redis unavailable)
    login_max_failures: int = 10
    login_failure_window_seconds: int = 300

    # Explicit admin bootstrap (never use hardcoded defaults in production)
    admin_bootstrap_email: str = ""
    admin_bootstrap_password: str = ""

    # In-app mail stays off until a verified Brevo sender and a real API key
    # replace the Railway placeholders. Reading these names does not send mail.
    email_provider: str = ""
    email_enabled: bool = False
    email_from_address: str = ""
    email_from_name: str = ""
    brevo_api_key: str = ""
    frontend_base_url: str = "http://localhost:5173"
    email_http_timeout_seconds: float = 10.0
    email_max_attempts: int = 5
    email_worker_batch_size: int = 20
    # Must stay longer than the HTTP timeout. A claim that outlives it is
    # ambiguous and is not resent.
    email_claim_timeout_seconds: int = 30

    # Private library PDFs. Empty values leave storage unconfigured and do not
    # contact Cloudflare. These are not printed.
    library_r2_account_id: str = ""
    library_r2_bucket: str = ""
    library_r2_access_key_id: str = ""
    library_r2_secret_access_key: str = ""

    practice_catalog_cache_ttl_seconds: int = 300
    practice_catalog_cache_key: str = "practice:catalog"

    prompt_max_chars: int = 20000
    prompt_max_cases: int = 40
    prompt_max_regex_length: int = 200
    prompt_evaluation_timeout_ms: int = 2000

    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    def validate_runtime_safety(self) -> None:
        """Fail on unsafe production configuration. Does not print secrets."""
        is_prod = self.app_env.lower() in {"production", "prod"}
        if not is_prod:
            return
        if self.jwt_secret_key in {_UNSAFE_JWT_DEFAULT, "", "secret", "changeme"}:
            raise RuntimeError(
                "Unsafe JWT_SECRET_KEY in production. Set a long random JWT_SECRET_KEY."
            )
        if not self.database_url:
            raise RuntimeError("DATABASE_URL is required in production.")
        if self.debug:
            warnings.warn("DEBUG=true in production is discouraged.", UserWarning, stacklevel=2)

    @property
    def email_can_send(self) -> bool:
        """True only when mail is explicitly enabled with a real Brevo sender and key."""
        provider = (self.email_provider or "").strip().lower()
        address = (self.email_from_address or "").strip().lower()
        key = (self.brevo_api_key or "").strip()
        return (
            self.email_enabled
            and provider == "brevo"
            and bool(address)
            and address != _EMAIL_PLACEHOLDER_ADDRESS
            and "@" in address
            and bool(key)
            and key != _EMAIL_PLACEHOLDER_KEY
        )

    @property
    def email_block_reason(self) -> str | None:
        """Why mail must not be sent, or None when email_can_send is true.

        Disabled sending and placeholder credentials are different reasons.
        Both suppress new outbox rows instead of leaving them queued.
        """
        if self.email_can_send:
            return None
        provider = (self.email_provider or "").strip().lower()
        address = (self.email_from_address or "").strip().lower()
        key = (self.brevo_api_key or "").strip()
        placeholder = (
            provider == "brevo"
            and (
                not address
                or "@" not in address
                or address == _EMAIL_PLACEHOLDER_ADDRESS
                or not key
                or key == _EMAIL_PLACEHOLDER_KEY
            )
        )
        if self.email_enabled and placeholder:
            return "placeholder_configuration"
        return "email_disabled"

    @property
    def library_storage_configured(self) -> bool:
        """True only when R2 account, bucket, and non-placeholder keys are set."""
        account = (self.library_r2_account_id or "").strip()
        bucket = (self.library_r2_bucket or "").strip()
        access = (self.library_r2_access_key_id or "").strip()
        secret = (self.library_r2_secret_access_key or "").strip()
        return all(
            value
            and value.lower() not in _STORAGE_PLACEHOLDERS
            for value in (account, bucket, access, secret)
        )

    @property
    def frontend_link_base(self) -> str | None:
        base = (self.frontend_base_url or "").strip().rstrip("/")
        if base.startswith("https://") or base.startswith("http://"):
            return base
        return None


settings = Settings()
settings.validate_runtime_safety()
