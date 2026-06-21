import json
import os
from typing import Any

from pydantic.fields import FieldInfo
from pydantic_settings import BaseSettings, SettingsConfigDict, EnvSettingsSource, PydanticBaseSettingsSource


class CommaSeparatedEnvSource(EnvSettingsSource):
    def prepare_field_value(
        self, field_name: str, field: FieldInfo, value: Any, value_is_complex: bool
    ) -> Any:
        if field_name == 'api_keys' and isinstance(value, str):
            return [key.strip() for key in value.split(',')]
        return super().prepare_field_value(field_name, field, value, value_is_complex)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    api_keys: list[str]
    kimi_api_key: str
    kimi_model: str = "kimi-k2.6"
    vault_path: str = "/data/vault"
    database_path: str = "/data/clipper.db"
    log_level: str = "INFO"
    rate_limit_ip: str = "10/minute"
    rate_limit_global: str = "100/minute"
    max_retry: int = 3

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            CommaSeparatedEnvSource(settings_cls),
            dotenv_settings,
            file_secret_settings,
        )
