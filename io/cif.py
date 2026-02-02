from __future__ import annotations

from pathlib import Path
from atomworks.io import parse

def safe_parse_cif(path: Path, assembly_id: str = "1"):
    try:
        out = parse(
            filename=str(path),
            build_assembly=(assembly_id,),
            add_missing_atoms=False,
            fix_formal_charges=False,
            add_id_and_entity_annotations=True,
        )
        return out["assemblies"][assembly_id][0]
    except Exception:
        return None

def list_cifs(cif_dir: Path) -> list[Path]:
    return sorted(p for p in cif_dir.rglob("*.cif") if p.is_file())
