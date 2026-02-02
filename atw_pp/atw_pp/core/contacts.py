from __future__ import annotations

import numpy as np
import biotite.structure as struc
from scipy.spatial import cKDTree

def contact_stats_between_atom_sets(
    coord1: np.ndarray,
    coord2: np.ndarray,
    *,
    contact_cutoff: float = 5.0,
    clash_cutoff: float = 2.0,
    cell_size: float = 6.0,
) -> dict:
    v1 = ~np.isnan(coord1).any(axis=1)
    v2 = ~np.isnan(coord2).any(axis=1)
    c1 = coord1[v1]
    c2 = coord2[v2]

    if c1.size == 0 or c2.size == 0:
        return {"n_contact_atoms": 0, "n_clash_atoms": 0, "min_dist": float("inf")}

    cl = struc.CellList(c2, cell_size=cell_size)
    near_c = cl.get_atoms(c1, contact_cutoff, as_mask=True)
    near_x = cl.get_atoms(c1, clash_cutoff, as_mask=True)

    has_contact = np.any(near_c, axis=1)
    has_clash = np.any(near_x, axis=1)

    t2 = cKDTree(c2)
    d, _ = t2.query(c1, k=1)
    min_dist = float(np.min(d)) if len(d) else float("inf")

    return {
        "n_contact_atoms": int(np.count_nonzero(has_contact)),
        "n_clash_atoms": int(np.count_nonzero(has_clash)),
        "min_dist": min_dist,
    }
