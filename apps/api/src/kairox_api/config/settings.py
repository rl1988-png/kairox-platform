from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEV_JWT = "dev-jwt-secret-change-in-production-min-32-chars"
_DEV_CSRF = "dev-csrf-secret-change-in-production"
_MIN_SECRET_LENGTH = 32
_ALLOWED_AI_PROVIDERS = {"auto", "openai", "anthropic", "noop"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    web_url: str = "http://localhost:3000"
    api_url: str = "http://localhost:8000"

    jwt_secret: str = _DEV_JWT
    jwt_access_ttl_minutes: int = 30
    jwt_refresh_ttl_days: int = 7

    database_url: str = "postgresql+asyncpg://kairox:kairox_dev_password@localhost:5432/kairox"
    redis_url: str = "redis://localhost:6379/0"

    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60

    trongrid_api_key: str = ""
    tron_deposit_address: str = ""
    usdt_trc20_contract: str = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
    tron_min_confirmations: int = 19
    recharge_watcher_enabled: bool = True
    hot_wallet_balance: str = "45230.12"
    block_trial_withdraw: bool = True

    openai_api_key: str = ""
    anthropic_api_key: str = ""
    ai_default_provider: str = "auto"
    ai_request_timeout_sec: int = 30
    ai_max_tokens: int = 2048
    ai_enable_pii_mask: bool = True

    log_level: str = "INFO"
    log_json: bool = False

    csrf_secret: str = _DEV_CSRF
    cookie_secure: bool = False
    cors_origins: str = "http://localhost:3000"

    @model_validator(mode="after")
    def _validate_settings(self) -> "Settings":
        self.app_env = self.app_env.lower().strip()
        self.ai_default_provider = self.ai_default_provider.lower().strip()

        if self.ai_default_provider not in _ALLOWED_AI_PROVIDERS:
            raise ValueError(
                "AI_DEFAULT_PROVIDER must be one of: " + ", ".join(sorted(_ALLOWED_AI_PROVIDERS))
            )

        if self.app_env == "production":
            self._validate_production()
        return self

    def _validate_production(self) -> None:
        if self.jwt_secret == _DEV_JWT:
            raise ValueError(
                "JWT_SECRET must be set in production; "
                "current value is the insecure development default"
            )
        if len(self.jwt_secret) < _MIN_SECRET_LENGTH or self.jwt_secret.startswith("change-me"):
            raise ValueError("JWT_SECRET must be at least 32 random characters")

        if self.csrf_secret == _DEV_CSRF:
            raise ValueError(
                "CSRF_SECRET must be set in production; "
                "current value is the insecure development default"
            )
        if len(self.csrf_secret) < _MIN_SECRET_LENGTH or self.csrf_secret.startswith("change-me"):
            raise ValueError("CSRF_SECRET must be at least 32 random characters")

        if not self.cookie_secure:
            raise ValueError("COOKIE_SECURE must be true in production")
        if not self.web_url.startswith("https://"):
            raise ValueError("WEB_URL must use HTTPS in production")
        if not self.api_url.startswith("https://"):
            raise ValueError("API_URL must use HTTPS in production")
        if "localhost" in self.web_url or "localhost" in self.api_url:
            raise ValueError("WEB_URL and API_URL must not use localhost in production")
        if not self.cors_origin_list:
            raise ValueError("CORS_ORIGINS must contain at least one origin in production")
        if "*" in self.cors_origin_list:
            raise ValueError("CORS_ORIGINS must not contain '*' in production")
        if self.web_url not in self.cors_origin_list:
            raise ValueError("CORS_ORIGINS must include WEB_URL in production")
        if any(not origin.startswith("https://") for origin in self.cors_origin_list):
            raise ValueError("CORS_ORIGINS must use HTTPS origins in production")
        if not self.tron_deposit_address:
            raise ValueError("TRON_DEPOSIT_ADDRESS must be set in production")
        if not _is_tron_address(self.tron_deposit_address):
            raise ValueError("TRON_DEPOSIT_ADDRESS must be a TRON base58 address")
        if self.recharge_watcher_enabled and not self.trongrid_api_key:
            raise ValueError("TRONGRID_API_KEY must be set when recharge watcher is enabled")
        if not self.log_json:
            raise ValueError("LOG_JSON must be true in production")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


def _is_tron_address(value: str) -> bool:
    return len(value) == 34 and value.startswith("T")


settings = Settings()
