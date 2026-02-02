from __future__ import annotations
import numpy as np

def select_chain_polymer_atoms(aa, chain_id: str):
    return aa[(aa.chain_id == chain_id) & aa.is_polymer]

def ensure_unit_id_annotation(aa):
    cats = set(aa.get_annotation_categories())
    if "pn_unit_id" in cats:
        return aa
    aa = aa.copy()
    aa.set_annotation("pn_unit_id", np.array([f"{c}_1" for c in aa.chain_id], dtype="<U16"))
    return aa
