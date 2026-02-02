from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

from .base import Context
from ..core.epitope import points_repr_from_points

class ParagraphParatopePlugin:
    name = "paragraph_paratope"
    prefix = "paragraph"
    table = "chains"

    def _subset_df(self, ctx: Context, df: pd.DataFrame) -> pd.DataFrame:
        cfg = ctx.data.get("cfg")
        mode = getattr(cfg, "paragraph_id_mode", "stem") if cfg is not None else "stem"
        if mode == "path":
            if "path" not in df.columns:
                return df.iloc[:0]
            return df[df["path"].astype(str) == str(ctx.path)]
        pdb_id = Path(ctx.path).stem
        return df[df["pdb"].astype(str) == str(pdb_id)]

    def _summarize(self, g: pd.DataFrame, cutoff: float, label_prefix: str, label_maker):
        g = g.copy()
        g["pred"] = pd.to_numeric(g["pred"], errors="coerce")
        g["x"] = pd.to_numeric(g["x"], errors="coerce")
        g["y"] = pd.to_numeric(g["y"], errors="coerce")
        g["z"] = pd.to_numeric(g["z"], errors="coerce")
        g = g.dropna(subset=["pred", "x", "y", "z", "IMGT", "chain_id"])
        if g.empty:
            return None

        n_scored = int(len(g))
        hit = g[g["pred"] >= cutoff].copy()

        base = {
            "cutoff": float(cutoff),
            "n_res_scored": n_scored,
            "score_mean_all_scored": float(g["pred"].mean()),
            "score_max": float(g["pred"].max()),
        }

        if hit.empty:
            return {
                **base,
                f"{label_prefix}_size": 0,
                f"{label_prefix}_labels": "",
                f"{label_prefix}_centroid_x": np.nan,
                f"{label_prefix}_centroid_y": np.nan,
                f"{label_prefix}_centroid_z": np.nan,
                f"{label_prefix}_rg": np.nan,
                f"{label_prefix}_score_mean": np.nan,
            }

        P = hit[["x", "y", "z"]].to_numpy(dtype=float)
        labels = [label_maker(r) for _, r in hit.iterrows()]
        reprd = points_repr_from_points(P, labels, label_prefix=label_prefix)

        return {
            **base,
            **reprd,
            f"{label_prefix}_score_mean": float(hit["pred"].mean()),
        }

    def run(self, ctx: Context):
        cfg = ctx.data.get("cfg")
        df: pd.DataFrame | None = ctx.data.get("paragraph_df")
        if cfg is None or df is None or df.empty:
            return

        cutoff = float(cfg.paragraph_cutoff)
        sub = self._subset_df(ctx, df)
        if sub.empty:
            return

        # ---- Chain-level outputs (chains table) ----
        for chain_id, grp in sub.groupby("chain_id", sort=False):
            if ctx.chains and str(chain_id) not in ctx.chains:
                continue

            s = self._summarize(
                grp,
                cutoff=cutoff,
                label_prefix="paratope",
                label_maker=lambda r: f"{r['chain_id']}:{r['IMGT']}",
            )
            if s is None:
                continue

            yield {
                "__table__": "chains",
                "path": ctx.path,
                "assembly_id": ctx.assembly_id,
                "chain_id": str(chain_id),
                **s,
            }

        # ---- Role-level outputs (roles table) ----
        role_names = tuple(getattr(cfg, "role_paratope_summaries", ()))
        if not role_names:
            return

        # role = union of chains in cfg.roles[role].chain_ids
        for role in role_names:
            spec = cfg.roles.get(role)
            if spec is None:
                continue
            chain_ids = set(map(str, spec.chain_ids))
            if not chain_ids:
                continue
            grp = sub[sub["chain_id"].astype(str).isin(chain_ids)]
            if grp.empty:
                continue

            s = self._summarize(
                grp,
                cutoff=cutoff,
                label_prefix="paratope",
                label_maker=lambda r: f"{r['chain_id']}:{r['IMGT']}",
            )
            if s is None:
                continue

            yield {
                "__table__": "roles",
                "path": ctx.path,
                "assembly_id": ctx.assembly_id,
                "role": str(role),
                **s,
            }
