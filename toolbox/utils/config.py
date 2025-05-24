from datetime import datetime
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field


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
    max_team_size: int = Field(..., alias="max-team-size", ge=1)
    registration_mode: Literal["internal", "external"] = Field(..., alias="registration-mode")


class Label(BaseModel):
    id: str
    name: str
    description: str


class LabelsConfig(YamlConfig, BaseModel):
    labels: list[Label]
