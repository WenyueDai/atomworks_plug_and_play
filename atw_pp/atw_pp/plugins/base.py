from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Protocol, Literal
import biotite.structure as struc

TableName = Literal["structures", "chains", "roles", "interfaces"]

@dataclass
class Context:
    path: str
    assembly_id: str
    aa: struc.AtomArray

    chains: dict[str, struc.AtomArray] = field(default_factory=dict)
    roles: dict[str, struc.AtomArray] = field(default_factory=dict)

    data: dict[str, Any] = field(default_factory=dict)
    cache: dict[str, Any] = field(default_factory=dict)

class Plugin(Protocol):
    name: str
    prefix: str
    table: TableName

    def run(self, ctx: Context) -> Iterable[dict]:
        ...
