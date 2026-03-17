from datetime import datetime
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, model_validator
from pydantic_core import PydanticCustomError


class YamlConfig:
    @classmethod
    def from_config_directory(cls, config_directory: Path):
        path = config_directory / f"{cls.__name__.replace('Config', '').lower()}.yaml"
        config = yaml.load(path.read_text(), Loader=yaml.FullLoader)
        if issubclass(cls, BaseModel):
            return cls.model_validate(config)

    @classmethod
    def from_path(cls, path: Path):
        config = yaml.load(path.read_text(), Loader=yaml.FullLoader)
        if issubclass(cls, BaseModel):
            return cls.model_validate(config)


class EventConfig(YamlConfig, BaseModel):
    id: str
    start_date: datetime = Field(..., alias="start-date")
    end_date: datetime = Field(..., alias="end-date")


class RegistrationConfig(YamlConfig, BaseModel):
    start_date: datetime = Field(..., alias="start-date")
    end_date: datetime = Field(..., alias="end-date")
    max_teams: int = Field(..., alias="max-teams", ge=1)
    max_team_size: int = Field(..., alias="max-team-size", ge=1)
    registration_mode: Literal["internal", "external"] = Field(..., alias="registration-mode")
    max_teams_per_organization: int | None = Field(default=None, alias="max-teams-per-organization", ge=1)

    @model_validator(mode="after")
    def check_max_teams_per_org_if_registration_external(self):
        if self.registration_mode == "external" and self.max_teams_per_organization is None:
            raise PydanticCustomError(
                "missing_max_teams_per_organization",
                "'max-teams-per-organization' must be provided if registration-mode is external",
            )
        return self


class Label(BaseModel):
    id: str
    name: str
    description: str


class LabelsConfig(YamlConfig, BaseModel):
    labels: list[Label]


class DeploymentTargetConfig(BaseModel):
    main_compose: str | None = Field(default=None, alias="main-compose")
    docker_context: str | None = Field(default=None, alias="docker-context")
    docker_host: str | None = Field(default=None, alias="docker-host")
    docker_tls: bool | None = Field(default=None, alias="docker-tls")
    docker_tls_verify: bool | None = Field(default=None, alias="docker-tls-verify")
    docker_tls_ca_cert: str | None = Field(default=None, alias="docker-tls-ca-cert")
    docker_tls_cert: str | None = Field(default=None, alias="docker-tls-cert")
    docker_tls_key: str | None = Field(default=None, alias="docker-tls-key")
    swarm_advertise_address: str | None = Field(default=None, alias="swarm-advertise-address")
    swarm_listen_address: str | None = Field(default=None, alias="swarm-listen-address")
    traefik_provider: Literal["docker", "swarm"] | None = Field(default=None, alias="traefik-provider")
    stack_network: str | None = Field(default=None, alias="stack-network")
    publish_mode: Literal["host", "ingress"] | None = Field(default=None, alias="publish-mode")
    docker_socket: str | None = Field(default=None, alias="docker-socket")
    with_registry_auth: bool = Field(default=False, alias="with-registry-auth")


class DeploymentsConfig(YamlConfig, BaseModel):
    default_target: str = Field(default="dev", alias="default-target")
    targets: dict[str, DeploymentTargetConfig] = Field(default_factory=lambda: {"dev": DeploymentTargetConfig()})

    @model_validator(mode="after")
    def check_default_target_exists(self):
        if self.default_target not in self.targets:
            raise PydanticCustomError(
                "invalid_default_target",
                "'default-target' must reference one of the configured deployment targets",
            )
        return self

    @classmethod
    def from_config_directory_optional(cls, config_directory: Path):
        path = config_directory / "deployments.yaml"
        if not path.exists():
            return cls()
        return cls.from_path(path)
