from datetime import datetime
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field


class EventConfig(BaseModel):
    start_date: datetime = Field(..., alias="start-date")
    end_date: datetime = Field(..., alias="end-date")

    @staticmethod
    def from_file(config_directory: Path):
        config_directory = config_directory / "event.yaml"
        config = yaml.load(config_directory.read_text(), Loader=yaml.FullLoader)

        return EventConfig(**config)


class RegistrationConfig(BaseModel):
    start_date: datetime = Field(..., alias="start-date")
    end_date: datetime = Field(..., alias="end-date")
    max_team_size: int = Field(..., alias="max-team-size", ge=1)
    registration_mode: Literal["internal", "external"] = Field(..., alias="registration-mode")

    @staticmethod
    def from_file(config_directory: Path):
        config_directory = config_directory / "registration.yaml"
        config = yaml.load(config_directory.read_text(), Loader=yaml.FullLoader)

        return RegistrationConfig(**config)
