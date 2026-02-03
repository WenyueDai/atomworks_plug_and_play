from __future__ import annotations
import numpy as np
import biotite.structure as struc
from .base import Context

class ChainContinuityPlugin:
    name = "chain_continuity"
    prefix = "qc"
    table = "chains"

    def run(self, ctx: Context):
        for chain_id, arr in ctx.chains.items():
            if arr is None or len(arr) == 0:
                continue
            try:
                ok = struc.check_backbone_continuity(arr)
                if isinstance(ok, (bool, np.bool_)):
                    has_break = not bool(ok)
                    n_breaks = int(has_break)
                else:
                    ok = np.asarray(ok).astype(bool)
                    n_breaks = int(np.count_nonzero(~ok))
                    has_break = bool(n_breaks > 0)
            except Exception:
                has_break = True
                n_breaks = -1

            yield {
                "path": ctx.path,
                "assembly_id": ctx.assembly_id,
                "chain_id": str(chain_id),
                "has_break": bool(has_break),
                "n_breaks": int(n_breaks),
            }
