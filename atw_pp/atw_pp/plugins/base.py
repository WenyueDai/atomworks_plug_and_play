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
    """
    Base protocol for plugins.
    Each plugin must have the following attributes and method:
    name: the name of the plugin
    prefix: used to prefix emitted row columns in the output
    table: the name of the table this plugin outputs rows for ("structures", "chains", "roles", "interfaces")
    yield {"path": ctx.path, "assembly_id": ctx.assembly_id, ...}
    """
    name: str
    prefix: str
    table: TableName

    def run(self, ctx: Context) -> Iterable[dict]:
        ...
