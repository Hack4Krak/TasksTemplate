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


class EventStage(BaseModel):
    name: str
    stage_type: Literal["event-start", "event-end", "informative"] = Field(alias="type")
    start_date: datetime = Field(..., alias="start-date")
    end_date: datetime | None = Field(default=None, alias="end-date")
    description: str | None = None

    @model_validator(mode="after")
    def check_stage_dates(self):
        if self.end_date is not None:
            try:
                if self.end_date <= self.start_date:
                    raise PydanticCustomError(
                        "invalid_stage_dates",
                        "'end-date' must be later than 'start-date'",
                    )
            except TypeError as exception:
                raise PydanticCustomError(
                    "invalid_stage_timezone",
                    "'start-date' and 'end-date' must use the same timezone format",
                ) from exception

        return self


class EventConfig(YamlConfig, BaseModel):
    id: str
    name: str | None = None
    stages: list[EventStage] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_stages(self):
        def get_single_stage(stage_type: Literal["event-start", "event-end"]) -> EventStage:
            matched_stages = [stage for stage in self.stages if stage.stage_type == stage_type]
            if len(matched_stages) != 1:
                raise PydanticCustomError(
                    "invalid_event_stage_count",
                    f"Exactly one {stage_type} stage is required",
                )

            return matched_stages[0]

        event_start_stage = get_single_stage("event-start")
        event_end_stage = get_single_stage("event-end")

        event_start = event_start_stage.start_date
        event_end = event_end_stage.start_date

        try:
            if event_end <= event_start:
                raise PydanticCustomError(
                    "invalid_event_boundaries",
                    "event-end stage must be later than event-start stage",
                )
        except TypeError as exception:
            raise PydanticCustomError(
                "invalid_event_boundaries_timezone",
                "event-start and event-end stages must use the same timezone format",
            ) from exception

        return self


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
