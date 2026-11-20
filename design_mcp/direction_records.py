"""Schema and loading for reviewed design direction records."""

from functools import lru_cache
from pathlib import Path
import json
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator

from .models.visual_analyzer import contrast_ratio


Surface = Literal["landing", "dashboard", "mobile", "portfolio", "pricing", "editorial"]
Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=420)]
Slug = Annotated[str, StringConstraints(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=64)]
Hex = Annotated[str, StringConstraints(pattern=r"^#[0-9a-fA-F]{6}$")]
_DATA = Path(__file__).parent / "data" / "directions.json"


class _Record(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class TypeRoles(_Record):
    display: Text
    body: Text
    ratio: float = Field(ge=2.5, le=5)
    tracking: float = Field(ge=-0.04, le=-0.02)
    weight: int = Field(ge=200, le=900)
    license: Literal["OFL-1.1"]

    @model_validator(mode="after")
    def verify_roles(self):
        fonts = {family.casefold() for family in (self.display, self.body)}
        if len(fonts) != 2 or fonts & {"inter", "roboto", "space grotesk", "system-ui"}:
            raise ValueError("Display and workhorse need distinct approved font families")
        return self


class Palette(_Record):
    ink: Hex
    paper: Hex
    accent: Hex

    @model_validator(mode="after")
    def verify_roles(self):
        if len({self.ink.lower(), self.paper.lower(), self.accent.lower()}) != 3:
            raise ValueError("Ink, paper and accent must be distinct")
        if contrast_ratio(self.ink, self.paper) < 4.5:
            raise ValueError("Ink and paper must reach 4.5:1")
        if max(contrast_ratio(self.accent, self.ink), contrast_ratio(self.accent, self.paper)) < 4.5:
            raise ValueError("An accent surface needs an accessible foreground")
        return self


class Layout(_Record):
    skeleton: Text
    focus: Text
    desktop: Text
    mobile: Text
    rhythm: Text


class Imagery(_Record):
    subject: Text
    crop: Text
    fallback: Text


class Motion(_Record):
    trigger: Text
    effect: Text
    duration_ms: int = Field(ge=200, le=400)
    reduced: Text


class Action(_Record):
    instruction: Text
    label: Text


class Source(_Record):
    url: Annotated[str, StringConstraints(pattern=r"^https://[^\s]+$", max_length=480)]
    observation: Text
    strength: Literal["evidence", "hypothesis", "house target"]


class Direction(_Record):
    id: Slug
    surface: Surface
    title: Text
    summary: Text
    tags: list[Text] = Field(min_length=1, max_length=12)
    type: TypeRoles
    palette: Palette
    layout: Layout
    imagery: Imagery
    motion: Motion
    action: Action
    why: Text
    sources: list[Source] = Field(min_length=1, max_length=3)
    credit: Text

    @field_validator("sources")
    @classmethod
    def check_evidence(cls, sources):
        if not any(source.strength == "evidence" for source in sources):
            raise ValueError("A direction needs at least one observed reference")
        return sources


@lru_cache(maxsize=1)
def library() -> dict[str, Direction]:
    rows = [Direction.model_validate(item) for item in json.loads(_DATA.read_text(encoding="utf-8"))]
    result = {row.id: row for row in rows}
    if not rows or len(result) != len(rows):
        raise ValueError("The direction library needs unique IDs and at least one record")
    return result
