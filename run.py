from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from .config import MetadataConfig
from .io.cif import list_cifs, safe_parse_cif
from .io.params import load_param_map, attach_params
from .io.paragraph import load_paragraph_preds
from .core.annotations import ensure_unit_id_annotation
from .core.selection import build_chain_map, build_roles
from .plugins import BUILTIN_PLUGINS
from .plugins.base import Context
from .tables.wide import build_all_metadata_wide

IDENTITY_COLS = {
    "path", "assembly_id",
    "chain_id",
    "role",
    "pair",
    "role_left", "role_right",
    "contact_cutoff", "clash_cutoff",
}

def _prefix_row(row: dict[str, Any], prefix: str) -> dict[str, Any]:
    out = {}
    for k, v in row.items():
        if k == "__table__":
            continue
        if k in IDENTITY_COLS:
            out[k] = v
        else:
            out[f"{prefix}__{k}"] = v
    return out

def build_metadata(
    cif_dir: Path,
    out_dir: Path,
    *,
    cfg: MetadataConfig = MetadataConfig(),
    param_csvs: list[Path] | None = None,
    paragraph_preds: Path | None = None,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    cif_paths = list_cifs(cif_dir)
    print(f"Found {len(cif_paths)} CIF files under: {cif_dir}")

    param_map = load_param_map(param_csvs, mode=cfg.csv_mode)
    if param_map:
        print(f"Loaded param rows: {len(param_map)}")

    paragraph_df = None
    if paragraph_preds is not None:
        paragraph_df = load_paragraph_preds(paragraph_preds)
        print(f"Loaded Paragraph preds: {len(paragraph_df)} rows from {paragraph_preds}")

    # resolve plugins
    plugins = []
    for name in cfg.plugins:
        if name not in BUILTIN_PLUGINS:
            raise ValueError(f"Unknown plugin '{name}'. Available: {sorted(BUILTIN_PLUGINS)}")
        plugins.append(BUILTIN_PLUGINS[name])

    rows_struct: list[dict[str, Any]] = []
    rows_chain: list[dict[str, Any]] = []
    rows_role: list[dict[str, Any]] = []
    rows_iface: list[dict[str, Any]] = []
    bad_rows: list[dict[str, Any]] = []

    for path in cif_paths:
        abs_path = str(path.resolve())
        params_for_this = param_map.get(abs_path)

        aa = safe_parse_cif(path, assembly_id=cfg.assembly_id)
        if aa is None:
            bad_rows.append(
                attach_params(
                    {"path": abs_path, "error": "parse_failed"},
                    params_for_this,
                    prefix=cfg.param_prefix,
                    on_conflict=cfg.param_on_conflict,
                )
            )
            continue

        aa = ensure_unit_id_annotation(aa)

        ctx = Context(path=abs_path, assembly_id=cfg.assembly_id, aa=aa)
        ctx.data["cfg"] = cfg
        ctx.data["params"] = params_for_this
        if paragraph_df is not None:
            ctx.data["paragraph_df"] = paragraph_df

        ctx.chains = build_chain_map(aa)
        ctx.roles = build_roles(cfg, ctx.chains)

        for plg in plugins:
            for raw in plg.run(ctx):
                table = raw.get("__table__", plg.table)
                pref = _prefix_row(raw, plg.prefix)
                pref = attach_params(
                    pref,
                    params_for_this,
                    prefix=cfg.param_prefix,
                    on_conflict=cfg.param_on_conflict,
                )

                if table == "structures":
                    rows_struct.append(pref)
                elif table == "chains":
                    rows_chain.append(pref)
                elif table == "roles":
                    rows_role.append(pref)
                elif table == "interfaces":
                    rows_iface.append(pref)
                else:
                    raise ValueError(f"Plugin '{plg.name}' returned unknown table: {table}")

    df_struct = pd.DataFrame(rows_struct)
    df_chain = pd.DataFrame(rows_chain)
    df_role = pd.DataFrame(rows_role)
    df_iface = pd.DataFrame(rows_iface)
    df_bad = pd.DataFrame(bad_rows)

    df_struct.to_parquet(out_dir / "structures_metadata.parquet", index=False)
    df_chain.to_parquet(out_dir / "chains_metadata.parquet", index=False)
    df_role.to_parquet(out_dir / "roles_metadata.parquet", index=False)
    df_iface.to_parquet(out_dir / "interfaces_metadata.parquet", index=False)
    df_bad.to_csv(out_dir / "bad_files.csv", index=False)

    df_all = build_all_metadata_wide(df_struct, df_chain, df_role, df_iface)
    df_all.to_parquet(out_dir / "all_metadata.parquet", index=False)

    print("Saved:")
    print("  ", out_dir / "structures_metadata.parquet", "rows=", len(df_struct))
    print("  ", out_dir / "chains_metadata.parquet", "rows=", len(df_chain))
    print("  ", out_dir / "roles_metadata.parquet", "rows=", len(df_role))
    print("  ", out_dir / "interfaces_metadata.parquet", "rows=", len(df_iface))
    print("  ", out_dir / "all_metadata.parquet", "rows=", len(df_all))
    print("  ", out_dir / "bad_files.csv", "rows=", len(df_bad))
