from __future__ import annotations

from .base import Context
from ..core.contacts import contact_stats_between_atom_sets

class InterfaceContactsPlugin:
    """
    Role-role interface contacts.
    Reads cfg.interface_pairs = (("antibody","antigen"), ("vh","antigen"), ...)
    Emits one row per pair into interfaces table.
    """
    name = "interface_contacts"
    prefix = "iface"
    table = "interfaces"

    def run(self, ctx: Context):
        cfg = ctx.data.get("cfg")
        pairs = getattr(cfg, "interface_pairs", (("antibody", "antigen"),)) if cfg is not None else (("antibody", "antigen"),)

        for left_role, right_role in pairs:
            left = ctx.roles.get(left_role)
            right = ctx.roles.get(right_role)
            if left is None or right is None:
                continue
            if len(left) == 0 or len(right) == 0:
                continue

            stats = contact_stats_between_atom_sets(
                left.coord,
                right.coord,
                contact_cutoff=5.0,
                clash_cutoff=1.0,
                cell_size=6.0,
            )

            yield {
                "path": ctx.path,
                "assembly_id": ctx.assembly_id,
                "pair": f"{left_role}__{right_role}",
                "role_left": str(left_role),
                "role_right": str(right_role),
                "contact_cutoff": 5.0,
                "clash_cutoff": 1.0,
                **stats,
            }
