"""
https://github.com/DunbrackLab/IPSAE/blob/main/ipsae.py
https://github.com/adaptyvbio/nipah_ipsae_pipeline/blob/main/Boltz-IPSAE.ipynb

The ipsae.py can be run in commandline (sys.argv).
So I use subprocess.run(["python", ipsae.py, ...]) to call it,
It will generate *_15_15.txt along the structure files.
Plugin read the txt file and yield data into interfaces table.

This script assumes the PAE file is next to the structure file,
with names like pae_model_0.npz, model_0_pae.npz, pae.npz (fallback),
or AF3 style confidences.json.
If no PAE file found, skip without error.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable
import subprocess
import pandas as pd


@dataclass(frozen=True, slots=True)
class IpsaePlugin:
    name: str = "ipsae"
    table: str = "interfaces"
    prefix: str = "ipsae"

    ipsae_script: str = "../externals/ipsae/ipsae.py"
    pae_cutoff: float = 15.0
    dist_cutoff: float = 15.0

    emit_max: bool = True
    emit_min: bool = True

    def run(self, ctx) -> Iterable[Dict[str, Any]]:
        structure = Path(ctx.path)
        folder = structure.parent
        stem = structure.stem

        # 1) find pae file next to structure (Boltz-style default)
        pae_candidates = [
            folder / f"pae_{stem}.npz",
            folder / f"{stem}_pae.npz",
            folder / "pae.npz",
            folder / "confidences.json",  # AF3 style
        ]
        pae_path = next((p for p in pae_candidates if p.exists()), None)
        if pae_path is None:
            return

        # 2) run external script (creates *_15_15.txt next to structure)
        subprocess.run(
            ["python", self.ipsae_script, str(pae_path), str(structure),
             str(self.pae_cutoff), str(self.dist_cutoff)],
            check=True
        )

        pae_s = f"{int(self.pae_cutoff):02d}"
        dist_s = f"{int(self.dist_cutoff):02d}"
        out_txt = structure.with_suffix("").as_posix() + f"_{pae_s}_{dist_s}.txt"
        out_path = Path(out_txt)
        if not out_path.exists():
            return

        # 3) parse output (some versions are whitespace separated)
        df = pd.read_csv(out_path, sep=r"\s+", engine="python")

        # 4) choose score columns robustly
        id_cols = {"Chn1", "Chn2", "PAE", "Dist", "Type", "Model"}
        score_cols = [c for c in df.columns if c not in id_cols]

        # 5) emit max + min per chainpair, matching notebook logic
        max_rows = df[df["Type"] == "max"]
        for _, row_max in max_rows.iterrows():
            ch1, ch2 = row_max["Chn1"], row_max["Chn2"]
            pair = f"{ch1}-{ch2}"

            base = {
                "__table__": "interfaces",
                "path": ctx.path,
                "assembly_id": ctx.assembly_id,
                "pair": pair,
            }

            if self.emit_max:
                yield {
                    **base,
                    "agg": "max",
                    **{c: row_max.get(c) for c in score_cols},
                }

            if self.emit_min:
                mask = (df["Chn1"] == ch1) & (df["Chn2"] == ch2) & (df["Type"] != "max")
                if mask.any():
                    mins = df.loc[mask, score_cols].min(numeric_only=True)
                    yield {
                        **base,
                        "agg": "min",
                        **mins.to_dict(),
                    }
