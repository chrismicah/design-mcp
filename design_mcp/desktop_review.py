"""Review minimal on-device evidence from an owned desktop application."""

import argparse
import json
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator


MAX_BYTES = 64 * 1024
Coordinate = Annotated[float, Field(ge=-100_000, le=100_000)]
Extent = Annotated[float, Field(gt=0, le=32_768)]
Role = Literal["button", "link", "toggle", "input", "slider", "selector"]


class Evidence(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)


class Region(Evidence):
    id: Annotated[str, Field(pattern=r"^r[1-9][0-9]{0,2}$")]
    role: Role
    bounds: tuple[Coordinate, Coordinate, Extent, Extent]
    hittable: bool


class Capture(Evidence):
    version: Literal[1]
    platform: Literal["swift", "electron"]
    viewport: tuple[Extent, Extent]
    regions: Annotated[list[Region], Field(max_length=80)]

    @model_validator(mode="after")
    def unique_ids(self):
        if len({region.id for region in self.regions}) != len(self.regions):
            raise ValueError("Region identifiers must be unique")
        return self


def review(capture: Capture) -> dict:
    viewport_width, viewport_height = capture.viewport
    findings = []
    for region in capture.regions:
        x, y, width, height = region.bounds
        if x < -1 or y < -1 or x + width > viewport_width + 1 or y + height > viewport_height + 1:
            findings.append({"code": "control-clipped", "region": region.id, "role": region.role,
                             "change": "Reveal the complete control in the visible window."})
        elif not region.hittable:
            findings.append({"code": "control-not-hittable", "region": region.id, "role": region.role,
                             "change": "Check hit testing and remove the overlapping surface if present."})
    return {"platform": capture.platform, "viewport": capture.viewport,
            "controls_reviewed": len(capture.regions), "findings": findings,
            "scope": "Visible control geometry and hit testing in the supplied capture"}


def main(args: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="design-mcp review-app", description=__doc__)
    parser.add_argument("capture", type=Path, help="An evidence JSON file from your local desktop app")
    options = parser.parse_args(args)
    try:
        with options.capture.open("rb") as file:
            contents = file.read(MAX_BYTES + 1)
        if len(contents) > MAX_BYTES:
            raise ValueError("An evidence file must be 64 KiB or less.")
        capture = Capture.model_validate_json(contents)
    except ValidationError:
        parser.error("Invalid desktop capture. Export a version 1 capture from the Swift or Electron adapter.")
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(review(capture), indent=2))
    return 0
