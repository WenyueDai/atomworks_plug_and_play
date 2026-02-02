from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Literal, Tuple, Dict, Optional

CsvMode = Literal["merge", "append"]
Conflict = Literal["keep_row", "overwrite"]

@dataclass(frozen=True, slots=True)
class RoleSpec:
    chain_ids: Tuple[str, ...] = ()

@dataclass(frozen=True, slots=True)
class MetadataConfig:
    assembly_id: str = "1"

    # ----- Roles -----
    roles: Dict[str, RoleSpec] = None  # type: ignore

    # ----- Paragraph ingest -----
    paragraph_cutoff: float = 0.734
    paragraph_id_mode: Literal["stem", "path"] = "stem"

    # Role-level paratope summaries (emit to roles table)
    # e.g. ("vh","vl","antibody") or ("antibody",) etc.
    role_paratope_summaries: Tuple[str, ...] = ("vh", "vl", "antibody")

    # ----- Interface role pairs -----
    # Each tuple is (left_role, right_role)
    interface_pairs: Tuple[Tuple[str, str], ...] = (("antibody", "antigen"),)

    # ----- param CSV behavior -----
    csv_mode: CsvMode = "merge"
    param_prefix: str = "param__"
    param_on_conflict: Conflict = "keep_row"

    # plugins to run (by name)
    plugins: tuple[str, ...] = (
        "identity",
        "chain_continuity",
        "paragraph_paratope",
        "interface_contacts",
    )

    def __post_init__(self):
        if self.roles is None:
            object.__setattr__(
                self,
                "roles",
                {
                    "antigen": RoleSpec(("A",)),
                    "vh": RoleSpec(("B",)),
                    "vl": RoleSpec(("C",)),
                    "antibody": RoleSpec(("B", "C")),
                },
            )

    def to_dict(self) -> dict:
        return asdict(self)
