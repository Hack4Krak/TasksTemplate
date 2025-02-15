from datetime import datetime
from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class EventConfig(BaseModel):
    start_date: datetime = Field(..., alias="start-date")
    end_date: datetime = Field(..., alias="end-date")
    max_team_size: int = Field(..., alias="max-team-size", ge=1)

    @staticmethod
    def from_file(config_directory: Path):
        config_directory = config_directory / "event.yaml"
        config = yaml.load(config_directory.read_text(), Loader=yaml.FullLoader)

        return EventConfig(**config)
