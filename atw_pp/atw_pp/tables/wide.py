from __future__ import annotations
import pandas as pd

def _pivot(df: pd.DataFrame, *, index: str, col: str, drop_cols: tuple[str, ...], prefix: str) -> pd.DataFrame:
    value_cols = [c for c in df.columns if c not in drop_cols]
    if not value_cols:
        return pd.DataFrame({index: df[index].drop_duplicates()})
    p = df.pivot_table(index=index, columns=col, values=value_cols, aggfunc="first")
    p.columns = [f"{prefix}_{cid}__{feat}" for feat, cid in p.columns]
    return p.reset_index()

def build_all_metadata_wide(
    df_struct: pd.DataFrame,
    df_chain: pd.DataFrame | None,
    df_role: pd.DataFrame | None,
    df_iface: pd.DataFrame | None,
) -> pd.DataFrame:
    base = df_struct[["path"]].drop_duplicates().copy()
    struct = df_struct.drop_duplicates("path")
    base = base.merge(struct, on="path", how="left")

    if df_chain is not None and not df_chain.empty and {"path", "chain_id"}.issubset(df_chain.columns):
        ch = _pivot(df_chain, index="path", col="chain_id", drop_cols=("path", "assembly_id", "chain_id"), prefix="chain")
        base = base.merge(ch, on="path", how="left")

    if df_role is not None and not df_role.empty and {"path", "role"}.issubset(df_role.columns):
        rl = _pivot(df_role, index="path", col="role", drop_cols=("path", "assembly_id", "role"), prefix="role")
        base = base.merge(rl, on="path", how="left")

    # interfaces: pivot by pair (role_left__role_right)
    if df_iface is not None and not df_iface.empty and {"path", "pair"}.issubset(df_iface.columns):
        iface = _pivot(df_iface, index="path", col="pair", drop_cols=("path", "assembly_id", "pair"), prefix="iface")
        base = base.merge(iface, on="path", how="left")

    return base
