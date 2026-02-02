from __future__ import annotations

from pathlib import Path
from atomworks.io import parse

def safe_parse_structure(path: Path, assembly_id: str = "1"):
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

def list_structures(input_dir: Path) -> list[Path]:
    exts = (".cif", ".mmcif", ".pdb", ".ent")
    return sorted(p for p in input_dir.rglob("*") if p.is_file() and p.suffix.lower() in exts)