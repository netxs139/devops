"""DevOps 数据采集服务配置模块 (Pydantic V2 版)

采用 pydantic-settings 实现强类型配置管理，支持：
1. 从 config.ini 自动加载 (保持向下兼容)
2. 环境变量覆盖 (高优先级)
3. 自动类型转换与校验

使用方式:
    from devops_collector.config import settings
    print(settings.gitlab.url)
"""

import os
from typing import TYPE_CHECKING, Annotated, Any

import httpx
from pydantic import BaseModel, BeforeValidator, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _split_comma_separated(v: Any) -> list[str]:
    """Splits comma-separated strings into lists."""
    if isinstance(v, str):
        return [i.strip() for i in v.split(",") if i.strip()]
    return v  # type: ignore[no-any-return]


if TYPE_CHECKING:
    CommaSeparatedList = list[str]
else:
    CommaSeparatedList = Annotated[str | list[str], BeforeValidator(_split_comma_separated)]


class GitLabSettings(BaseModel):
    """GitLab connection settings.

    Attributes:
        url (str): The base URL of the GitLab instance.
        private_token (SecretStr): The private access token for authentication (System-level).
        client_id (str): OAuth2 Application ID.
        client_secret (SecretStr): OAuth2 Application Secret.
        redirect_uri (str): OAuth2 Callback URL (e.g., http://portal/auth/callback).
    """

    url: str = "https://gitlab.com"
    private_token: SecretStr
    client_id: str = ""
    client_secret: SecretStr
    redirect_uri: str = ""
    verify_ssl: bool = True


class DatabaseSettings(BaseModel):
    """Database connection and retention settings.

    Attributes:
        uri (SecretStr): The database connection URI.
        raw_data_retention_days (int): The number of days to retain raw data.
    """

    uri: SecretStr
    raw_data_retention_days: int = 30


class RabbitMQSettings(BaseModel):
    """RabbitMQ connection settings.

    Attributes:
        host (str): The RabbitMQ server host.
        queue (str): The default queue name.
        user (str): The username for authentication.
        password (SecretStr): The password for authentication.
    """

    host: str = "rabbitmq"
    queue: str = "gitlab_tasks"
    user: str = "user"
    password: SecretStr

    @property
    def url(self) -> str:
        """Constructs the AMQP URL from settings."""
        return f"amqp://{self.user}:{self.password.get_secret_value()}@{self.host}:5672/"


class AnalysisSettings(BaseModel):
    """Code analysis configuration."""

    enable_deep_analysis: bool = False
    ignored_file_patterns: CommaSeparatedList = ["*.lock", "*.min.js", "*.min.css", "node_modules/*", "dist/*"]
    production_env_mapping: CommaSeparatedList = ["prod", "production", "prd", "main"]
    incident_label_patterns: CommaSeparatedList = ["incident", "production-error", "P0", "P1"]
    change_failure_label_patterns: CommaSeparatedList = ["change-failure", "rollback"]


class RateLimitSettings(BaseModel):
    """Rate limiting configuration."""

    requests_per_second: int = 10


class ClientSettings(BaseModel):
    """HTTP client configuration."""

    timeout: int = 10
    per_page: int = 100
    max_retries: int = 5


class SchedulerSettings(BaseModel):
    """Task scheduler configuration."""

    sync_interval_minutes: int = 10


class LoggingSettings(BaseModel):
    """Logging configuration."""

    level: str = "INFO"


class SonarQubeSettings(BaseModel):
    """SonarQube integration settings."""

    url: str = ""
    token: SecretStr
    sync_interval_hours: int = 24
    sync_issues: bool = False


class NexusSettings(BaseModel):
    """Nexus integration settings."""

    url: str = ""
    user: str = ""
    password: SecretStr
    sync_interval_hours: int = 12
    repositories: CommaSeparatedList = Field(default_factory=list)


class JenkinsSettings(BaseModel):
    """Jenkins integration settings."""

    url: str = ""
    user: str = ""
    token: SecretStr
    sync_interval_hours: int = 12
    build_sync_limit: int = 100


class ZenTaoSettings(BaseModel):
    """ZenTao integration settings."""

    url: str = ""
    token: SecretStr
    account: str | None = None
    password: SecretStr | None = None
    sync_interval_hours: int = 12
    build_sync_limit: int = 100


class SMTPSettings(BaseModel):
    """SMTP email notification settings."""

    host: str = "smtp.example.com"
    port: int = 587
    username: str = "no-reply@example.com"
    password: SecretStr = Field(default_factory=lambda: SecretStr("dummy_password"))
    from_address: str = "no-reply@example.com"
    from_name: str = "DevOps Platform"
    use_tls: bool = True


class AISettings(BaseModel):
    """AI service configuration."""

    api_key: SecretStr
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o"


class SLASettings(BaseModel):
    """SLA threshold settings (in hours)."""

    p0: int = 8
    p1: int = 24
    p2: int = 73
    p3: int = 120
    p4: int = 240
    default: int = 48


class AuthSettings(BaseModel):
    """认证相关配置。"""

    allowed_domains: CommaSeparatedList = Field(default_factory=list, description="允许注册的邮箱域名列表")
    secret_key: SecretStr
    admin_api_token: SecretStr


class NotifiersSettings(BaseModel):
    """Webhook notifiers configuration."""

    wecom_webhook: str = ""
    feishu_webhook: str = ""
    dingtalk_webhook: str = ""


class PluginSettings(BaseModel):
    """Plugin system configuration."""

    enabled_plugins: CommaSeparatedList = ["gitlab", "sonarqube", "jenkins", "zentao"]


class StorageSettings(BaseModel):
    """Local storage configuration."""

    data_dir: str = "./data"

    @field_validator("data_dir")
    @classmethod
    def make_absolute(cls, v):
        """Make absolute."""
        if not os.path.isabs(v):
            return os.path.join(os.getcwd(), v)
        return v


class Settings(BaseSettings):
    """Global application configuration model."""

    gitlab: GitLabSettings
    database: DatabaseSettings
    rabbitmq: RabbitMQSettings
    analysis: AnalysisSettings = Field(default_factory=AnalysisSettings)
    ratelimit: RateLimitSettings = Field(default_factory=RateLimitSettings)
    client: ClientSettings = Field(default_factory=ClientSettings)
    scheduler: SchedulerSettings = Field(default_factory=SchedulerSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    sonarqube: SonarQubeSettings
    jenkins: JenkinsSettings
    zentao: ZenTaoSettings
    nexus: NexusSettings
    ai: AISettings
    smtp: SMTPSettings = Field(default_factory=SMTPSettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    plugin: PluginSettings = Field(default_factory=PluginSettings)
    sla: SLASettings = Field(default_factory=SLASettings)
    auth: AuthSettings
    notifiers: NotifiersSettings = Field(default_factory=NotifiersSettings)
    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="__", extra="ignore")


# 模块单例
settings = Settings()  # type: ignore[call-arg]
http_client: httpx.AsyncClient | None = None
