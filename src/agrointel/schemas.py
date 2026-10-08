"""Shared, strict request schema for REST and MCP callers."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .validation import validate

Finite = Annotated[float, Field(strict=True, allow_inf_nan=False)]


class PredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nitrogen: Annotated[
        Finite, Field(ge=0, description="Dataset benchmark scale, units unverified")
    ]
    phosphorus: Annotated[Finite, Field(ge=0)]
    potassium: Annotated[Finite, Field(ge=0)]
    temperature: Annotated[Finite, Field(ge=-50, le=65, description="Degrees Celsius")]
    humidity: Annotated[Finite, Field(ge=0, le=100, description="Relative humidity percent")]
    ph: Annotated[Finite, Field(ge=0, le=14)]
    rainfall: Annotated[
        Finite, Field(ge=0, description="Benchmark rainfall in mm; not today's rain")
    ]
    state: Annotated[str, Field(strict=True, min_length=1, max_length=120)]
    district: Annotated[str, Field(strict=True, min_length=1, max_length=120)]
    season: Annotated[str, Field(strict=True, min_length=1, max_length=120)]
    year: Annotated[int, Field(strict=True, ge=1900, le=2200)]
    area: Annotated[Finite, Field(gt=0, description="Cultivated area in hectares")]

    @model_validator(mode="after")
    def normalise_fields(self):
        cleaned = validate(self.model_dump())
        for field in ("state", "district", "season"):
            setattr(self, field, cleaned[field])
        return self
