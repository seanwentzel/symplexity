from dataclasses import dataclass
from typing import Literal

from dataclasses_json import dataclass_json

Outcome = Literal["YES", "NO"]


@dataclass_json
@dataclass
class Direction:
    id: str
    outcome: Outcome
