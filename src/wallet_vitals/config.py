from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Wallet Vitals"
    environment: str = "development"
    database_path: Path = Path("data/wallet_vitals.db")

    graph_api_key: SecretStr | None = None
    graph_subgraph_id: str = "Cd2gEDVeqnjBn1hSeqFMitw8Q1iiyV9FYUZkLNRcL87g"
    graph_gateway_url: str = "https://gateway.thegraph.com/api/subgraphs/id"
    graph_timeout_seconds: float = Field(default=18.0, gt=0, le=60)
    graph_max_age_seconds: int = Field(default=900, ge=60, le=7200)

    ethereum_rpc_url: str = "https://ethereum-rpc.publicnode.com"
    ethereum_rpc_timeout_seconds: float = Field(default=15.0, gt=0, le=60)

    openai_api_key: SecretStr | None = None
    openai_model: str = "gpt-5.6-luna"
    openai_timeout_seconds: float = Field(default=20.0, gt=0, le=60)

    report_ttl_hours: int = Field(default=24, ge=1, le=168)
    address_cooldown_seconds: int = Field(default=10, ge=0, le=300)
    max_concurrent_analyses: int = Field(default=4, ge=1, le=32)

    @property
    def graph_endpoint(self) -> str:
        return f"{self.graph_gateway_url.rstrip('/')}/{self.graph_subgraph_id}"
