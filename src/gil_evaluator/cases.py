from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Callable


class CaseType(StrEnum):
    FUNCTIONAL = "functional"
    STRESS = "stress"
    PERF = "perf"


CaseFn = Callable[[], dict[str, Any] | None]


@dataclass(slots=True)
class Case:
    case_id: str
    case_type: CaseType
    run: CaseFn
