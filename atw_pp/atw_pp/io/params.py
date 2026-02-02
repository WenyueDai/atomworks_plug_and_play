from __future__ import annotations

from pathlib import Path
from typing import Any
import pandas as pd

def attach_params(
    row: dict[str, Any],
    params: dict[str, Any] | None,
    *,
    prefix: str = "param__",
    on_conflict: str = "keep_row",
) -> dict[str, Any]:
    if not params:
        return dict(row)
    out = dict(row)
    for k, v in params.items():
        kk = f"{prefix}{k}" if prefix else str(k)
        if kk in out and on_conflict == "keep_row":
            continue
        out[kk] = v
    return out

def load_param_map(param_csvs: list[Path] | None, mode: str = "merge") -> dict[str, dict[str, Any]]:
    if not param_csvs:
        return {}

    dfs = [pd.read_csv(p) for p in param_csvs]
    for df in dfs:
        if "path" not in df:
            raise ValueError("Param CSV missing required column 'path'")
        df["path"] = df["path"].astype(str)

    if mode == "append":
        dfp = pd.concat(dfs, ignore_index=True).drop_duplicates("path", keep="last")
    elif mode == "merge":
        dfp = dfs[0]
        for df in dfs[1:]:
            dfp = dfp.merge(df, on="path", how="outer", suffixes=("", "_dup"))
    else:
        raise ValueError("mode must be 'append' or 'merge'")

    return dfp.set_index("path").to_dict(orient="index")

def param_map_to_df(param_map: dict[str, dict[str, Any]]) -> pd.DataFrame:
    if not param_map:
        return pd.DataFrame(columns=["path"])
    return pd.DataFrame.from_dict(param_map, orient="index").reset_index(names="path").drop_duplicates("path")
