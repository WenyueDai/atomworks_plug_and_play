from __future__ import annotations

from pathlib import Path
import pandas as pd

REQUIRED = {"pdb", "chain_id", "IMGT", "pred", "x", "y", "z"}

def load_paragraph_preds(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    missing = REQUIRED - set(df.columns)
    if missing:
        raise ValueError(f"Paragraph CSV missing columns: {sorted(missing)}")

    out = df.copy()
    out["pdb"] = out["pdb"].astype(str)
    out["chain_id"] = out["chain_id"].astype(str)
    out["IMGT"] = out["IMGT"].astype(str)
    out["pred"] = pd.to_numeric(out["pred"], errors="coerce")
    out["x"] = pd.to_numeric(out["x"], errors="coerce")
    out["y"] = pd.to_numeric(out["y"], errors="coerce")
    out["z"] = pd.to_numeric(out["z"], errors="coerce")
    return out
