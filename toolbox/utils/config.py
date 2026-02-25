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
    max_teams_per_org: int | None = Field(default=None, alias="max-teams-per-org", ge=1)

    @model_validator(mode="after")
    def check_max_teams_per_org_if_registration_external(self):
        if self.registration_mode == "external" and self.max_teams_per_org is None:
            raise PydanticCustomError(
                "missing_max_teams_per_org",
                "'max-teams-per-org' must be provided if registration-mode is external",
            )
        return self


class Label(BaseModel):
    id: str
    name: str
    description: str


class LabelsConfig(YamlConfig, BaseModel):
    labels: list[Label]
