from __future__ import annotations

import argparse
from pathlib import Path

from .config import MetadataConfig, RoleSpec
from .run import build_metadata

def _add_role_arg(ap: argparse.ArgumentParser):
    ap.add_argument(
        "--role",
        action="append",
        nargs="+",
        default=None,
        help=(
            "Define a role: --role <role_name> <chain_id1> <chain_id2> ... "
            "Example: --role antigen A D --role vh H --role antibody H L"
        ),
    )

def _add_interface_pair_arg(ap: argparse.ArgumentParser):
    ap.add_argument(
        "--iface_pair",
        action="append",
        nargs=2,
        default=None,
        metavar=("LEFT_ROLE", "RIGHT_ROLE"),
        help="Add an interface pair: --iface_pair antibody antigen (repeatable)",
    )

def main() -> None:
    ap = argparse.ArgumentParser("atw_pp (role + plugin based)")

    ap.add_argument("--cif_dir", required=True)
    ap.add_argument("--out_dir", default="atw_pp_out")

    ap.add_argument("--param_csv", nargs="*", default=None)
    ap.add_argument("--csv_mode", default="merge", choices=["merge", "append"])

    ap.add_argument("--assembly_id", default="1")

    # Quick role shortcuts
    ap.add_argument("--antigen_chains", nargs="*", default=None)
    ap.add_argument("--vh_chains", nargs="*", default=None)
    ap.add_argument("--vl_chains", nargs="*", default=None)

    _add_role_arg(ap)
    _add_interface_pair_arg(ap)

    # Paragraph ingest
    ap.add_argument("--paragraph_preds", default=None)
    ap.add_argument("--paragraph_cutoff", type=float, default=0.734)
    ap.add_argument("--paragraph_id_mode", default="stem", choices=["stem", "path"])

    # Role-level paratope summaries
    ap.add_argument(
        "--role_paratope_summaries",
        nargs="*",
        default=None,
        help="Which roles to emit role-level paragraph summaries for (default: vh vl antibody)",
    )

    ap.add_argument("--param_prefix", default="param__")
    ap.add_argument("--param_on_conflict", default="keep_row", choices=["keep_row", "overwrite"])

    ap.add_argument(
        "--plugins",
        nargs="*",
        default=list(MetadataConfig().plugins),
        help="Plugin names to run",
    )

    args = ap.parse_args()

    cfg = MetadataConfig(
        assembly_id=args.assembly_id,
        paragraph_cutoff=args.paragraph_cutoff,
        paragraph_id_mode=args.paragraph_id_mode,
        csv_mode=args.csv_mode,
        param_prefix=args.param_prefix,
        param_on_conflict=args.param_on_conflict,
        plugins=tuple(args.plugins),
    )

    # Apply role shortcuts
    roles = dict(cfg.roles)
    if args.antigen_chains is not None:
        roles["antigen"] = RoleSpec(tuple(args.antigen_chains))
    if args.vh_chains is not None:
        roles["vh"] = RoleSpec(tuple(args.vh_chains))
    if args.vl_chains is not None:
        roles["vl"] = RoleSpec(tuple(args.vl_chains))

    # Derived role antibody
    vh = roles.get("vh", RoleSpec(())).chain_ids
    vl = roles.get("vl", RoleSpec(())).chain_ids
    if vh or vl:
        roles["antibody"] = RoleSpec(tuple(dict.fromkeys(tuple(vh) + tuple(vl))))

    # Apply --role overrides
    if args.role:
        for items in args.role:
            if not items:
                continue
            role_name = items[0]
            chain_ids = tuple(items[1:]) if len(items) > 1 else ()
            roles[role_name] = RoleSpec(chain_ids)

    # Interface pairs
    iface_pairs = cfg.interface_pairs
    if args.iface_pair:
        iface_pairs = tuple((a, b) for a, b in args.iface_pair)

    # Role-level paratope summaries
    role_summ = cfg.role_paratope_summaries
    if args.role_paratope_summaries is not None:
        role_summ = tuple(args.role_paratope_summaries)

    # rebuild cfg with updated roles/pairs/summaries
    cfg = MetadataConfig(
        assembly_id=cfg.assembly_id,
        roles=roles,
        paragraph_cutoff=cfg.paragraph_cutoff,
        paragraph_id_mode=cfg.paragraph_id_mode,
        role_paratope_summaries=role_summ,
        interface_pairs=iface_pairs,
        csv_mode=cfg.csv_mode,
        param_prefix=cfg.param_prefix,
        param_on_conflict=cfg.param_on_conflict,
        plugins=cfg.plugins,
    )

    build_metadata(
        cif_dir=Path(args.cif_dir).resolve(),
        out_dir=Path(args.out_dir).resolve(),
        cfg=cfg,
        param_csvs=[Path(p).resolve() for p in args.param_csv] if args.param_csv else None,
        paragraph_preds=Path(args.paragraph_preds).resolve() if args.paragraph_preds else None,
    )

if __name__ == "__main__":
    main()
