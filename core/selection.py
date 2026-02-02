from __future__ import annotations

from typing import Dict
import biotite.structure as struc

from .annotations import select_chain_polymer_atoms
from ..config import MetadataConfig

def build_chain_map(aa) -> dict[str, struc.AtomArray]:
    chain_ids = sorted(set(map(str, aa.chain_id)))
    return {cid: select_chain_polymer_atoms(aa, cid) for cid in chain_ids}

def _concat(arrs: list[struc.AtomArray], template: struc.AtomArray) -> struc.AtomArray:
    if not arrs:
        return template[:0]
    out = arrs[0]
    for a in arrs[1:]:
        out = struc.concatenate([out, a])
    return out

def build_roles(cfg: MetadataConfig, chain_map: dict[str, struc.AtomArray]) -> Dict[str, struc.AtomArray]:
    roles: Dict[str, struc.AtomArray] = {}
    template = next(iter(chain_map.values()))
    for role_name, spec in cfg.roles.items():
        picked = []
        for cid in spec.chain_ids:
            a = chain_map.get(cid)
            if a is not None and len(a) > 0:
                picked.append(a)
        roles[role_name] = _concat(picked, template=template)
    return roles
